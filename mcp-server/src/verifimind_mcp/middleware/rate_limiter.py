"""
Rate Limiting Middleware for VerifiMind MCP Server.

v0.3.1 - EDoS Protection (Economic Denial of Sustainability)

Provides IP-based and global rate limiting to prevent:
- DDoS attacks causing auto-scale cost explosion
- API abuse from single users
- Wallet drain attacks

Design Considerations for Cloud Run:
- In-memory storage (no external dependencies like Redis)
- Works per-instance (with max 3 instances, worst case is 3x limit)
- Automatic cleanup of old entries to prevent memory leak
- Configurable via environment variables

Rate Limits:
- Per IP: 10 requests/minute (configurable)
- Global: 100 requests/minute per instance (configurable)
- Burst: Allow short bursts up to 2x limit
"""

import os
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Configuration from environment variables
RATE_LIMIT_PER_IP = int(os.getenv("RATE_LIMIT_PER_IP", "10"))  # requests per minute
RATE_LIMIT_GLOBAL = int(os.getenv("RATE_LIMIT_GLOBAL", "100"))  # requests per minute per instance
RATE_LIMIT_BURST_MULTIPLIER = float(os.getenv("RATE_LIMIT_BURST", "2.0"))  # allow 2x burst
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds (1 minute)
RATE_LIMIT_CLEANUP_INTERVAL = int(os.getenv("RATE_LIMIT_CLEANUP", "300"))  # cleanup every 5 minutes

# Exempt paths from rate limiting
EXEMPT_PATHS = {"/health", "/", "/.well-known/mcp-config", "/setup"}


class RateLimitStore:
    """
    In-memory rate limit tracking with automatic cleanup.

    Uses sliding window algorithm for fair rate limiting.
    """

    def __init__(self):
        # {ip: [(timestamp, count), ...]}
        self.ip_requests: Dict[str, list] = defaultdict(list)
        self.global_requests: list = []
        self.last_cleanup = time.time()

    def _cleanup_old_entries(self, entries: list, window: int) -> list:
        """Remove entries older than the window."""
        cutoff = time.time() - window
        return [e for e in entries if e[0] > cutoff]

    def _maybe_global_cleanup(self):
        """Periodically clean up all old entries to prevent memory leak."""
        now = time.time()
        if now - self.last_cleanup > RATE_LIMIT_CLEANUP_INTERVAL:
            # Clean up IP entries
            ips_to_remove = []
            for ip, entries in self.ip_requests.items():
                self.ip_requests[ip] = self._cleanup_old_entries(entries, RATE_LIMIT_WINDOW)
                if not self.ip_requests[ip]:
                    ips_to_remove.append(ip)

            for ip in ips_to_remove:
                del self.ip_requests[ip]

            # Clean up global entries
            self.global_requests = self._cleanup_old_entries(self.global_requests, RATE_LIMIT_WINDOW)

            self.last_cleanup = now
            logger.debug(f"Rate limiter cleanup: {len(self.ip_requests)} IPs tracked")

    def check_and_record(self, ip: str) -> Tuple[bool, Optional[int], str]:
        """
        Check if request is allowed and record it.

        Returns:
            Tuple of (allowed, retry_after_seconds, limit_type)
        """
        now = time.time()
        self._maybe_global_cleanup()

        # Clean current IP's entries
        self.ip_requests[ip] = self._cleanup_old_entries(
            self.ip_requests[ip], RATE_LIMIT_WINDOW
        )

        # Clean global entries
        self.global_requests = self._cleanup_old_entries(
            self.global_requests, RATE_LIMIT_WINDOW
        )

        # Count requests in current window
        ip_count = len(self.ip_requests[ip])
        global_count = len(self.global_requests)

        # Check IP limit (with burst allowance)
        ip_limit = int(RATE_LIMIT_PER_IP * RATE_LIMIT_BURST_MULTIPLIER)
        if ip_count >= ip_limit:
            # Calculate retry after
            oldest = min(e[0] for e in self.ip_requests[ip])
            retry_after = int(RATE_LIMIT_WINDOW - (now - oldest)) + 1
            logger.warning(f"Rate limit exceeded for IP {ip}: {ip_count}/{ip_limit}")
            return False, retry_after, "ip"

        # Check global limit (with burst allowance)
        global_limit = int(RATE_LIMIT_GLOBAL * RATE_LIMIT_BURST_MULTIPLIER)
        if global_count >= global_limit:
            oldest = min(e[0] for e in self.global_requests)
            retry_after = int(RATE_LIMIT_WINDOW - (now - oldest)) + 1
            logger.warning(f"Global rate limit exceeded: {global_count}/{global_limit}")
            return False, retry_after, "global"

        # Record request
        self.ip_requests[ip].append((now, 1))
        self.global_requests.append((now, 1))

        return True, None, "ok"

    def get_stats(self) -> Dict:
        """Get current rate limiting statistics."""
        now = time.time()

        # Count active requests in window
        active_ips = sum(
            1 for entries in self.ip_requests.values()
            if any(e[0] > now - RATE_LIMIT_WINDOW for e in entries)
        )

        global_count = len([
            e for e in self.global_requests
            if e[0] > now - RATE_LIMIT_WINDOW
        ])

        return {
            "active_ips": active_ips,
            "global_requests_in_window": global_count,
            "global_limit": RATE_LIMIT_GLOBAL,
            "ip_limit": RATE_LIMIT_PER_IP,
            "window_seconds": RATE_LIMIT_WINDOW,
            "burst_multiplier": RATE_LIMIT_BURST_MULTIPLIER
        }


# Global store instance
_rate_limit_store = RateLimitStore()


def get_client_ip(request: Request) -> str:
    """
    Extract client IP from request, handling proxies.

    Cloud Run sets X-Forwarded-For header.
    """
    # Check X-Forwarded-For (set by Cloud Run and other proxies)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(",")[0].strip()

    # Check X-Real-IP
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    # Fallback to direct client
    if request.client:
        return request.client.host

    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for Starlette/FastAPI.

    Protects against:
    - EDoS (Economic Denial of Sustainability)
    - API abuse
    - Wallet drain attacks on auto-scaling infrastructure
    """

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Skip OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get client IP
        client_ip = get_client_ip(request)

        # Check rate limit
        allowed, retry_after, limit_type = _rate_limit_store.check_and_record(client_ip)

        if not allowed:
            logger.warning(
                f"Rate limited: IP={client_ip}, type={limit_type}, "
                f"path={request.url.path}, retry_after={retry_after}s"
            )

            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    "limit_type": limit_type,
                    "retry_after": retry_after,
                    "documentation": "https://github.com/creator35lwb-web/VerifiMind-PEAS#rate-limits"
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(RATE_LIMIT_PER_IP),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after)
                }
            )

        # Add rate limit headers to response
        response = await call_next(request)

        # Add informational headers
        _rate_limit_store.get_stats()
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_PER_IP)
        response.headers["X-RateLimit-Window"] = str(RATE_LIMIT_WINDOW)

        return response


def get_rate_limit_stats() -> Dict:
    """Get current rate limiting statistics (for monitoring)."""
    return _rate_limit_store.get_stats()
