"""
Rate Limiting Middleware for VerifiMind MCP Server.

v0.5.19 - UUID Tier-Aware Rate Limiting (P0-A)

Tiers (per 60s window):
  Anonymous  — no valid UUID header → 10 req/60s per IP
  Scholar    — valid UUID, not in ea_registrations → 30 req/60s per UUID
  EA/Pioneer — valid UUID, in ea_registrations → 100 req/60s per UUID

UUID is read from the X-VerifiMind-UUID header (auto-sent by mcp-remote
after v0.5.17 mcp_config header fix). Falls back to IP-based limit when
header is absent or UUID is invalid.

Tier resolution uses a 5-minute in-memory cache to avoid per-request
Firestore reads. Firestore unavailable → Scholar limit (fail-open, generous).
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
RATE_LIMIT_PER_IP = int(os.getenv("RATE_LIMIT_PER_IP", "10"))
RATE_LIMIT_GLOBAL = int(os.getenv("RATE_LIMIT_GLOBAL", "100"))
RATE_LIMIT_BURST_MULTIPLIER = float(os.getenv("RATE_LIMIT_BURST", "2.0"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_CLEANUP_INTERVAL = int(os.getenv("RATE_LIMIT_CLEANUP", "300"))

# Tier rate limits (requests per RATE_LIMIT_WINDOW)
TIER_LIMITS: Dict[str, int] = {
    "anonymous": RATE_LIMIT_PER_IP,   # 10/60s — IP-based
    "scholar":   30,                   # 30/60s — UUID-based
    "pioneer":   100,                  # 100/60s — UUID-based (EA + Pioneer)
}

# UUID → tier cache: {uuid: (tier, expires_at)}
_uuid_tier_cache: Dict[str, Tuple[str, float]] = {}
UUID_TIER_CACHE_TTL = 300  # 5 minutes — matches Firestore session TTL

# Exempt paths from rate limiting
EXEMPT_PATHS = {"/health", "/", "/.well-known/mcp-config", "/setup", "/register", "/optout", "/privacy", "/terms", "/robots.txt", "/favicon.ico", "/early-adopters/register"}


def _resolve_uuid_tier(uuid: str) -> str:
    """Return tier for a valid UUID. Cached for UUID_TIER_CACHE_TTL seconds.

    Checks ea_registrations Firestore collection:
      - found → "pioneer"  (EA + Pioneer both get 100/60s)
      - not found → "scholar" (valid UUID, free tier, 30/60s)
      - Firestore unavailable → "scholar" (fail-open, generous)
    """
    now = time.time()
    cached = _uuid_tier_cache.get(uuid)
    if cached and now < cached[1]:
        return cached[0]
    try:
        from verifimind_mcp.registration import _get_firestore, COLLECTION_REGISTRATIONS
        db = _get_firestore()
        if db is not None:
            doc = db.collection(COLLECTION_REGISTRATIONS).document(uuid).get()
            tier = "pioneer" if doc.exists else "scholar"
        else:
            tier = "scholar"
    except Exception:
        tier = "scholar"
    _uuid_tier_cache[uuid] = (tier, now + UUID_TIER_CACHE_TTL)
    return tier


class RateLimitStore:
    """In-memory rate limit tracking with automatic cleanup. Sliding window."""

    def __init__(self):
        self.ip_requests: Dict[str, list] = defaultdict(list)
        self.uuid_requests: Dict[str, list] = defaultdict(list)
        self.global_requests: list = []
        self.last_cleanup = time.time()

    def _cleanup_old_entries(self, entries: list, window: int) -> list:
        cutoff = time.time() - window
        return [e for e in entries if e[0] > cutoff]

    def _maybe_global_cleanup(self):
        now = time.time()
        if now - self.last_cleanup > RATE_LIMIT_CLEANUP_INTERVAL:
            for bucket in (self.ip_requests, self.uuid_requests):
                dead = [k for k, v in bucket.items()
                        if not self._cleanup_old_entries(v, RATE_LIMIT_WINDOW)]
                for k in dead:
                    del bucket[k]
                for k in list(bucket):
                    bucket[k] = self._cleanup_old_entries(bucket[k], RATE_LIMIT_WINDOW)
            self.global_requests = self._cleanup_old_entries(
                self.global_requests, RATE_LIMIT_WINDOW
            )
            self.last_cleanup = now
            logger.debug("Rate limiter cleanup: %d IPs, %d UUIDs tracked",
                         len(self.ip_requests), len(self.uuid_requests))

    def _check_bucket(self, bucket: dict, key: str, limit: int,
                      label: str) -> Tuple[bool, Optional[int], str]:
        """Sliding-window check on a named bucket. Records on pass."""
        now = time.time()
        bucket[key] = self._cleanup_old_entries(bucket[key], RATE_LIMIT_WINDOW)
        count = len(bucket[key])
        effective_limit = int(limit * RATE_LIMIT_BURST_MULTIPLIER)
        if count >= effective_limit:
            oldest = min(e[0] for e in bucket[key])
            retry_after = int(RATE_LIMIT_WINDOW - (now - oldest)) + 1
            logger.warning("Rate limit exceeded [%s=%s]: %d/%d", label, key[:8], count, effective_limit)
            return False, retry_after, label
        bucket[key].append((now, 1))
        return True, None, "ok"

    def check_and_record(self, ip: str) -> Tuple[bool, Optional[int], str]:
        """Anonymous path: IP-based, RATE_LIMIT_PER_IP limit."""
        self._maybe_global_cleanup()
        # Global guard
        self.global_requests = self._cleanup_old_entries(self.global_requests, RATE_LIMIT_WINDOW)
        global_limit = int(RATE_LIMIT_GLOBAL * RATE_LIMIT_BURST_MULTIPLIER)
        if len(self.global_requests) >= global_limit:
            oldest = min(e[0] for e in self.global_requests)
            retry_after = int(RATE_LIMIT_WINDOW - (time.time() - oldest)) + 1
            return False, retry_after, "global"
        allowed, retry_after, limit_type = self._check_bucket(
            self.ip_requests, ip, RATE_LIMIT_PER_IP, "ip"
        )
        if allowed:
            self.global_requests.append((time.time(), 1))
        return allowed, retry_after, limit_type

    def check_and_record_uuid(self, uuid: str, limit: int) -> Tuple[bool, Optional[int], str]:
        """Scholar/Pioneer path: UUID-based with tier limit."""
        self._maybe_global_cleanup()
        # Global guard
        self.global_requests = self._cleanup_old_entries(self.global_requests, RATE_LIMIT_WINDOW)
        global_limit = int(RATE_LIMIT_GLOBAL * RATE_LIMIT_BURST_MULTIPLIER)
        if len(self.global_requests) >= global_limit:
            oldest = min(e[0] for e in self.global_requests)
            retry_after = int(RATE_LIMIT_WINDOW - (time.time() - oldest)) + 1
            return False, retry_after, "global"
        allowed, retry_after, limit_type = self._check_bucket(
            self.uuid_requests, uuid, limit, "uuid"
        )
        if allowed:
            self.global_requests.append((time.time(), 1))
        return allowed, retry_after, limit_type

    def get_stats(self) -> Dict:
        now = time.time()
        active_ips = sum(
            1 for entries in self.ip_requests.values()
            if any(e[0] > now - RATE_LIMIT_WINDOW for e in entries)
        )
        active_uuids = sum(
            1 for entries in self.uuid_requests.values()
            if any(e[0] > now - RATE_LIMIT_WINDOW for e in entries)
        )
        global_count = len([e for e in self.global_requests if e[0] > now - RATE_LIMIT_WINDOW])
        return {
            "active_ips": active_ips,
            "active_uuids": active_uuids,
            "global_requests_in_window": global_count,
            "global_limit": RATE_LIMIT_GLOBAL,
            "ip_limit": RATE_LIMIT_PER_IP,
            "window_seconds": RATE_LIMIT_WINDOW,
            "burst_multiplier": RATE_LIMIT_BURST_MULTIPLIER,
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
    """UUID tier-aware rate limiting. Anonymous→IP, Scholar/Pioneer→UUID."""

    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        if request.method == "OPTIONS":
            return await call_next(request)

        client_ip = get_client_ip(request)

        # Resolve tier from X-VerifiMind-UUID header
        uuid_header = request.headers.get("x-verifimind-uuid", "").strip()
        tier = "anonymous"
        active_limit = TIER_LIMITS["anonymous"]

        if uuid_header:
            try:
                from verifimind_mcp.utils.uuid_tracer import is_valid_uuid
                if is_valid_uuid(uuid_header):
                    tier = _resolve_uuid_tier(uuid_header)
                    active_limit = TIER_LIMITS[tier]
            except Exception:
                pass  # invalid header → fall back to anonymous

        if tier == "anonymous":
            allowed, retry_after, limit_type = _rate_limit_store.check_and_record(client_ip)
        else:
            allowed, retry_after, limit_type = _rate_limit_store.check_and_record_uuid(
                uuid_header, active_limit
            )

        if not allowed:
            logger.warning(
                "Rate limited: tier=%s key=%s type=%s path=%s retry_after=%ss",
                tier, (uuid_header[:8] if uuid_header else client_ip), limit_type,
                request.url.path, retry_after,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    "tier": tier,
                    "limit": active_limit,
                    "limit_type": limit_type,
                    "retry_after": retry_after,
                    "upgrade_hint": (
                        "Register at verifimind.ysenseai.org/register for Scholar tier (30 req/60s). "
                        "Pioneer tier: 100 req/60s."
                    ) if tier == "anonymous" else None,
                    "documentation": "https://github.com/creator35lwb-web/VerifiMind-PEAS#rate-limits",
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(active_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after),
                    "X-RateLimit-Tier": tier,
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(active_limit)
        response.headers["X-RateLimit-Window"] = str(RATE_LIMIT_WINDOW)
        response.headers["X-RateLimit-Tier"] = tier
        return response


def get_rate_limit_stats() -> Dict:
    """Get current rate limiting statistics (for monitoring)."""
    return _rate_limit_store.get_stats()
