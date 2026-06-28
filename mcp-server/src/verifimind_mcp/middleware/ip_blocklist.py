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
    # Credential / Secret Enumeration Scanner — 788 req single burst on May 12; probed .env variants,
    # .git/* tree, .terraform.*, .stripe/, .s3cfg, .wp-config.php.swp, ?phpinfo=1, ?pp=env&pp=env,
    # CI configs (.gitlab-ci, .github/workflows), Next.js/SharePoint paths. Static Chrome/131 UA.
    # 611/788 (77%) caught by rate limiter as 429; 4 served 200 (safe root/register, zero leak).
    ("195.178.110.199", "SECRET_SCANNER", "2026-05-13", "RNA_CSO"),
    # CMS Webshell Scanner — Azure/Microsoft range; null UA on every request; ~310 req/7d in 2 bursts
    # (2026-05-21 + 2026-05-26 14:40-14:42 UTC); WordPress + PHP webshell dictionary (wp-login.php,
    # xmlrpc.php, wp-admin/alfa.php, wp-content/uploads/goods.php, wso.php, gecko.php, chosen.php,
    # lock360.php, god4m.php, ~140 PHP webshell names incl. mixed-case randkeyword.PhP7 evasion);
    # 50% redirected (Layer 3), 37% rate-limited (429), 13% 404; zero 200; no VerifiMind handler hit.
    ("4.228.83.111", "CMS_WEBSHELL_SCANNER", "2026-05-29", "RNA_CSO"),
    # Secret / Credential Scanner — IPv6; single 15-second burst 2026-05-25 19:13:03-19:13:18 UTC;
    # 65 req @ ~4.3 req/s; rotating UA across 18+ distinct browser/OS strings per request (Windows/
    # Chrome v145-147, Edge v146-147, macOS/Safari, Linux/Firefox v149-150, iOS/Safari — botnet/
    # distributed-proxy pattern); 3-phase probe: (1) GCP service-account JSON files (serviceAccount
    # Key.json was the first probe — GCP-aware attacker), (2) .env variant tree across 28 paths
    # incl. .env.production.*/.env.local.* backup variants, (3) .git internals (HEAD/config/
    # logs/HEAD/refs/heads/main/master); 60% rate-limited, 34% 404, 3x 200 ALL on public root /;
    # zero leak. Same SECRET_SCANNER class as 195.178.110.199 (2026-05-13). Address-only block —
    # /48 prefix scan returned only the base address, no multi-host rotation observed.
    ("2602:fb54:99a::", "SECRET_SCANNER", "2026-05-29", "RNA_CSO"),
    # AISEC Registry Scanner — UA `aisec-registry/0.2 (+https://sec.sqrx.io)` on 100% of 400 requests;
    # 5-day cron-like persistence (May 23-27, ~80 req/day); MCP/OAuth surface enumeration: 89× POST /mcp +
    # 89× GET /mcp/.well-known/oauth-{authorization-server,protected-resource,mcp}; HTTP 200 = 0 (never
    # reached a real handler), 268× 429 (rate-limited), 88× 404 (OAuth discovery failures); not a builder,
    # not a Scholar conversion candidate, no /register intent. AY+AZ forensics 2026-05-30 (see
    # .macp/handoffs/20260530_AY_to_RNA_block_ip10_3_137_30_179.md). Same non-user automated-probe class as
    # 4.228.83.111 / 2602:fb54:99a:: but with higher volume persistence; address-only block.
    ("3.137.30.179", "AISEC_REGISTRY_SCANNER", "2026-06-01", "RNA_CSO"),
    # AgentSure MCP Scanner — UA `Mozilla/5.0 (compatible; AgentSure-MCPScan/0.1; +https://agentsure.tech)`;
    # primary IP 152.55.176.35 = 20×200 POST /mcp/ Jun 5-10 with a 39,779s (~11h) engagement window on
    # Jun 5 alone (daily cron ~21:37 UTC) — polluted ~11h of "flying hours" as if verified engagement.
    # 8 rotating Azure-range IPs share the same UA (low individual duration, but WAU/endpoint inflation).
    # Not a builder, zero /register intent. AY+AZ forensics 2026-06-12 (honest-metrics gate held Report 097).
    ("152.55.176.35", "AGENTSURE_MCP_SCANNER", "2026-06-16", "RNA_CSO"),
    ("20.119.41.196", "AGENTSURE_MCP_SCANNER", "2026-06-16", "RNA_CSO"),
    ("64.236.140.200", "AGENTSURE_MCP_SCANNER", "2026-06-16", "RNA_CSO"),
    ("52.233.87.81", "AGENTSURE_MCP_SCANNER", "2026-06-16", "RNA_CSO"),
    ("152.55.176.88", "AGENTSURE_MCP_SCANNER", "2026-06-16", "RNA_CSO"),
    ("172.172.87.67", "AGENTSURE_MCP_SCANNER", "2026-06-16", "RNA_CSO"),
    ("48.211.211.35", "AGENTSURE_MCP_SCANNER", "2026-06-16", "RNA_CSO"),
    ("52.234.42.34", "AGENTSURE_MCP_SCANNER", "2026-06-16", "RNA_CSO"),
    ("52.159.245.161", "AGENTSURE_MCP_SCANNER", "2026-06-16", "RNA_CSO"),
    # LeakIX l9scan — UA `l9scan/2.0 (+https://leakix.net)`; internet background path-enumeration scanner.
    # Jun 9 burst: 28 reqs sweeping /console/, /server-status, /about and similar (all 302/legacy). Block
    # for metrics cleanliness (minimal hour impact). AY+AZ forensics 2026-06-12.
    ("146.190.242.161", "LEAKIX_L9SCAN", "2026-06-16", "RNA_CSO"),
    ("64.23.218.208", "LEAKIX_L9SCAN", "2026-06-16", "RNA_CSO"),
    # MCP Endpoint Scanner — UA `MCP-Inspector/1.8.0 (security-scan)` on 100% of 330 req; single 100-second
    # burst 2026-06-15 12:22:34-12:24:14 UTC @ ~3.3 req/s; systematic 23-path MCP transport dictionary sweep
    # (/mcp, /sse, /stream, /events, /jsonrpc, /rpc, /api/sse, /api/mcp, /messages, /v1/mcp, /mcp/v1/sse,
    # /.well-known/mcp, /.well-known/oauth-authorization-server, nested variants) with embedded JSON-RPC
    # capability-enum payloads (initialize, tools/list, resources/list, prompts/list); AS45820 TATAIDC
    # Bengaluru IN; 86% rate-limited (429), 8% 404, 6% redirects; ZERO 200; zero leak; no /register intent.
    # Alton-flagged 2026-06-16; Sentinel investigation confirmed BLOCK.
    ("14.194.11.238", "MCP_ENDPOINT_SCANNER", "2026-06-16", "RNA_CSO"),
    # Config/Secret Scanner #23 — spoofed Chrome UA (81/81 identical); 81 hits/14d; CI/CD + cloud-config +
    # credential enumeration sweep (/.firebase/hosting.json, /firebase.json, /amplify.yml, /vite.config.js,
    # /.gitlab-ci.yml, /Jenkinsfile, /.github/workflows/*, /.vscode/settings.json, /.pypirc, /composer.json);
    # 59x429, 20x404, 2x200 (root / only); ZERO sensitive 200s, ZERO /mcp success, ZERO /register, 0 flying
    # hours. Alton-flagged during adoption review; AY+AZ GCP forensics 2026-06-18 (D-45-3). Hygiene block.
    ("45.148.10.15", "CONFIG_SECRET_SCANNER", "2026-06-18", "AY_AZ_COO_CPO"),
    # Config/Secret Scanner #24 (45.148.10.0/24) — rotating browser UA per request (Chrome/macOS/Linux/Win +
    # Firefox = botnet/spoof); weekly cron (Jun 5/10/17/27 ~16:00 UTC), 4 rounds x ~30 req/session; probed
    # .git/config (high-value), .env tree (18+ variants incl. admin/.env, backend/.env), wp-config.php, phpinfo.php,
    # aws.config.js; 80x404 (67%), 36x429 (30%), 4x200 all on public root / ; ZERO sensitive 200s. Same /24 as #23
    # (45.148.10.15, 2026-06-18) and #25 (45.148.10.67, this batch). AY+AZ flagged, Sentinel-verified 2026-06-28.
    ("45.148.10.62", "CONFIG_SECRET_SCANNER", "2026-06-28", "RNA_CSO"),  # NOSONAR
    # Config/Secret Scanner #25 (45.148.10.0/24) — UA TLM-Audit-Scanner/1.0 (self-identifying, 100% static); single
    # extreme-velocity burst 2026-06-27 02:43:36-53 UTC (~59 req/s, 17s, 1000+ req); multi-tech credential dictionary:
    # Stripe (stripe-credentials.json/keys.json/.env), Terraform (.tfvars/.tfstate(.backup)), AWS Lambda (var/task/
    # amplify.yml, docker-compose, serverless.yaml, next.config.*), WordPress (wp-config.php*, wp-json/gravitysmtp,
    # wp-content/mysql.sql), .env tree (v1/v2/v3/staging/src/srv/shop/services/website), Webmin CGI; 635x302
    # (HTTP->HTTPS), 364x429 (36%), 4x200 (/, /register, /?phpinfo=1, /?pp=env&pp=env — all public-safe); ZERO
    # sensitive 200s. UA `TLM-Audit-Scanner` added to BLOCKED_UA_PATTERNS for rotation-proof /24 coverage.
    ("45.148.10.67", "CONFIG_SECRET_SCANNER", "2026-06-28", "RNA_CSO"),  # NOSONAR
    # Config/RCE Scanner #26 (NEW class) — primary UA Firefox/47.0 (2016-era static); secondary Chrome/Win10 + empty
    # UA at overlapping timestamps = proxy cluster / multi-tool orchestration; single 6-min burst 2026-06-24
    # 04:41-47 UTC, 180 req @ ~0.5 req/s; probed .aws/credentials (high-value), swagger.json, backend/config/
    # default.yml, storage/logs/laravel.log, config.js + .env tree (10+ variants incl. crm/.env, core/.env,
    # application/.env), phpinfo.php, server-info.php, apis/controllers/users.js, admin/controllers/merchant.js;
    # ESCALATION: embedded Node.js child_process.execSync RCE probe via query param (?param=test?cmd=<base64:echo
    # VULN_TEST>) — returned 200 root page (Python/FastAPI ignores query params; zero execution, zero leak);
    # 108x404 (60%), 64x429 (36%), 5x200 (root + ignored-query paths), 3x302; ZERO sensitive 200s. Sentinel 2026-06-28.
    ("93.123.109.103", "CONFIG_RCE_SCANNER", "2026-06-28", "RNA_CSO"),  # NOSONAR
]

# Blocked User-Agent substrings (case-insensitive substring match)
BLOCKED_UA_PATTERNS: list[str] = [
    "YellowMCP-SecurityScanner",
    "AgentSure-MCPScan",   # AgentSure MCP scanner — rotation-proof block across its Azure IP family
    "l9scan",              # LeakIX internet background scanner
    "(security-scan)",     # self-declared scanner suffix (e.g. MCP-Inspector/1.8.0 (security-scan)); surgical — does not collide with standard MCP Inspector usage
    "TLM-Audit-Scanner",   # TLM-Audit-Scanner/1.0 — self-identifying commercial scanner; rotation-proof coverage for 45.148.10.67 (#25, 2026-06-28) and any /24 successor IPs
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
