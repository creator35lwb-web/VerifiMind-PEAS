"""
IP Blocklist Middleware — VerifiMind-PEAS Security Layer

T Security Directive (2026-04-27): block 3 rogue IPs identified by AY forensic scan.
Runs as the outermost middleware layer — blocks before rate limiting or CORS processing.

Block criteria:
  1. Exact IP match (IPv4 or IPv6) against BLOCKED_IPS
  2. User-Agent substring match against BLOCKED_UA_PATTERNS
  3. ALL IPs in X-Forwarded-For chain are checked (GFE proxy-aware)

Audit log format:
  [IP_BLOCKED] ip=<ip> reason=<code> path=<path> ua=<ua> ts=<iso>
  [UA_BLOCKED] pattern=<pat> ip=<ip> path=<path> ua=<ua> ts=<iso>
"""

import datetime
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Blocked IPs — updated by T (CTO) + AY (COO) forensic scans
# Format: (ip_address, reason_code, date_added, added_by)
BLOCKED_IPS: list[tuple[str, str, str, str]] = [
    # Erratic Node Bot — 454 req/day, 63% error rate, AWS us-east-1 (IPv6)
    ("2600:1f18:5a5b:3400:2f1e:c9d2:567b:76bc", "ERRATIC_BOT", "2026-04-27", "T_CTO"),
    # Content Scraper — 2,007 AbuseIPDB reports, VirusTotal flagged, AWS us-west-2
    ("35.161.55.221", "CONTENT_SCRAPER", "2026-04-27", "T_CTO"),
    # Unauthorized MCP Scanner — YellowMCP, no consent given, Hostinger NL (IPv6)
    ("2a02:4780:4:2ad9::1", "UNAUTHORIZED_SCANNER", "2026-04-27", "T_CTO"),
    # Unauthorized MCP Prober — AWS EC2 us-west-1, no UA, 35-min interval HEAD/POST scan (2d, 96 hits)
    ("54.67.34.241", "UNAUTHORIZED_SCANNER", "2026-05-06", "RNA_CSO"),
    # SSRF Scanner — AS48090 Techoff SRV Ltd; 90-req automated scan, 18 SSRF probes targeting cloud IMDS
    ("195.178.110.157", "SSRF_SCANNER", "2026-05-07", "RNA_CSO"),
    # Config / Secret Enumeration Scanner — ~25 req/sec on May 11; probed /api/env, /firebase-config.json,
    # /swagger.json, /openapi.json, /.well-known/jwks.json, /api/v1/config, /api/account, /__env.js, etc.
    # Rotating User-Agents (different browser/OS per request — botnet pattern). Mostly 429-rate-limited.
    ("85.121.126.250", "CONFIG_SCANNER", "2026-05-12", "RNA_CSO"),
]

# Blocked User-Agent substrings (case-insensitive substring match)
BLOCKED_UA_PATTERNS: list[str] = [
    "YellowMCP-SecurityScanner",
]

# Pre-computed lookup structures (module-level, built once at import)
_BLOCKED_IP_SET: frozenset[str] = frozenset(ip.lower() for ip, *_ in BLOCKED_IPS)
_BLOCKED_IP_REASONS: dict[str, str] = {ip.lower(): reason for ip, reason, *_ in BLOCKED_IPS}
_BLOCKED_UA_LOWER: list[str] = [p.lower() for p in BLOCKED_UA_PATTERNS]

# Minimal 403 response — no implementation details disclosed
_FORBIDDEN_BODY = {
    "error": "Forbidden",
    "code": 403,
    "message": "Access denied by security policy.",
}


def _get_all_ips(request: Request) -> list[str]:
    """Return all IPs from X-Forwarded-For chain plus direct client (lowercase)."""
    ips: list[str] = []
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        ips.extend(part.strip().lower() for part in forwarded.split(",") if part.strip())
    if request.client and request.client.host:
        ips.append(request.client.host.lower())
    return ips


def _check_ip(request: Request) -> tuple[bool, str, str]:
    """Return (blocked, matched_ip, reason_code). Checks full XFF chain."""
    for ip in _get_all_ips(request):
        if ip in _BLOCKED_IP_SET:
            return True, ip, _BLOCKED_IP_REASONS[ip]
    return False, "", ""


def _check_ua(request: Request) -> tuple[bool, str]:
    """Return (blocked, matched_pattern). Case-insensitive substring match."""
    ua_lower = request.headers.get("user-agent", "").lower()
    for pattern in _BLOCKED_UA_LOWER:
        if pattern in ua_lower:
            return True, pattern
    return False, ""


class IPBlocklistMiddleware(BaseHTTPMiddleware):
    """Block rogue IPs and unauthorized scanners before any route processing."""

    async def dispatch(self, request: Request, call_next):
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        ua = request.headers.get("user-agent", "")[:200]

        # 1. IP check — covers all XFF hops
        blocked, matched_ip, reason = _check_ip(request)
        if blocked:
            logger.warning(
                "[IP_BLOCKED] ip=%s reason=%s path=%s ua=%s ts=%s",
                matched_ip, reason, request.url.path, ua, ts,
            )
            return JSONResponse(_FORBIDDEN_BODY, status_code=403)

        # 2. User-Agent check — catches scanner tools regardless of IP rotation
        ua_blocked, matched_pattern = _check_ua(request)
        if ua_blocked:
            xff = request.headers.get("x-forwarded-for", "")
            client_ip = xff.split(",")[0].strip() if xff else (
                request.client.host if request.client else "unknown"
            )
            logger.warning(
                "[UA_BLOCKED] pattern=%s ip=%s path=%s ua=%s ts=%s",
                matched_pattern, client_ip, request.url.path, ua, ts,
            )
            return JSONResponse(_FORBIDDEN_BODY, status_code=403)

        return await call_next(request)
