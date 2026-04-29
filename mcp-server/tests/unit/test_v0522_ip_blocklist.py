"""
IP Blocklist Middleware — v0.5.22 Security Layer
=================================================

Tests for T Security Directive (2026-04-27):
  - 3 rogue IPs blocked at application level (403 Forbidden)
  - YellowMCP-SecurityScanner UA blocked
  - Legitimate traffic unaffected
  - Structured audit logging: [IP_BLOCKED] / [UA_BLOCKED]
  - ALL X-Forwarded-For chain IPs checked (GFE proxy-aware)
"""

import logging
import pytest
from unittest.mock import AsyncMock, MagicMock

from verifimind_mcp.middleware.ip_blocklist import (
    IPBlocklistMiddleware,
    BLOCKED_IPS,
    BLOCKED_UA_PATTERNS,
    _BLOCKED_IP_SET,
    _check_ip,
    _check_ua,
    _get_all_ips,
)


# ---------------------------------------------------------------------------
# Helper — build minimal mock Request
# ---------------------------------------------------------------------------

def _make_request(
    xff: str = "",
    ua: str = "python-httpx/0.27.0",
    client_host: str = "203.0.113.1",
    path: str = "/mcp/",
):
    req = MagicMock()
    req.url.path = path
    req.client = MagicMock()
    req.client.host = client_host
    headers = {}
    if xff:
        headers["x-forwarded-for"] = xff
    headers["user-agent"] = ua
    req.headers = headers
    return req


# ---------------------------------------------------------------------------
# 1. BLOCKED_IPS list — structure and completeness
# ---------------------------------------------------------------------------

class TestBlockedIpsConstants:

    def test_three_blocked_ips_defined(self):
        assert len(BLOCKED_IPS) == 3

    def test_erratic_bot_ipv6_present(self):
        ips = {ip for ip, *_ in BLOCKED_IPS}
        assert "2600:1f18:5a5b:3400:2f1e:c9d2:567b:76bc" in ips

    def test_content_scraper_ipv4_present(self):
        ips = {ip for ip, *_ in BLOCKED_IPS}
        assert "35.161.55.221" in ips

    def test_unauthorized_scanner_ipv6_present(self):
        ips = {ip for ip, *_ in BLOCKED_IPS}
        assert "2a02:4780:4:2ad9::1" in ips

    def test_all_entries_have_four_fields(self):
        for entry in BLOCKED_IPS:
            assert len(entry) == 4, f"Entry {entry} missing fields"

    def test_blocked_ua_yellowmcp_present(self):
        assert any("YellowMCP" in p for p in BLOCKED_UA_PATTERNS)


# ---------------------------------------------------------------------------
# 2. _check_ip — exact match and XFF chain traversal
# ---------------------------------------------------------------------------

class TestCheckIp:

    def test_blocked_ipv4_direct_xff(self):
        req = _make_request(xff="35.161.55.221")
        blocked, ip, reason = _check_ip(req)
        assert blocked is True
        assert "35.161.55.221" in ip
        assert reason == "CONTENT_SCRAPER"

    def test_blocked_ipv6_direct_xff(self):
        req = _make_request(xff="2600:1f18:5a5b:3400:2f1e:c9d2:567b:76bc")
        blocked, ip, reason = _check_ip(req)
        assert blocked is True
        assert reason == "ERRATIC_BOT"

    def test_blocked_ipv6_scanner(self):
        req = _make_request(xff="2a02:4780:4:2ad9::1")
        blocked, ip, reason = _check_ip(req)
        assert blocked is True
        assert reason == "UNAUTHORIZED_SCANNER"

    def test_blocked_ip_in_xff_chain(self):
        # GFE appends its own IP — blocked IP is earlier in the chain
        req = _make_request(xff="35.161.55.221, 130.211.0.1")
        blocked, _, reason = _check_ip(req)
        assert blocked is True
        assert reason == "CONTENT_SCRAPER"

    def test_blocked_ip_as_second_hop(self):
        req = _make_request(xff="203.0.113.5, 35.161.55.221, 130.211.0.1")
        blocked, _, _ = _check_ip(req)
        assert blocked is True

    def test_legitimate_ip_not_blocked(self):
        req = _make_request(xff="8.8.8.8")
        blocked, _, _ = _check_ip(req)
        assert blocked is False

    def test_empty_xff_checks_client_host(self):
        req = _make_request(xff="", client_host="35.161.55.221")
        blocked, _, reason = _check_ip(req)
        assert blocked is True
        assert reason == "CONTENT_SCRAPER"

    def test_legitimate_client_host_not_blocked(self):
        req = _make_request(xff="", client_host="192.0.2.100")
        blocked, _, _ = _check_ip(req)
        assert blocked is False

    def test_ip_matching_is_case_insensitive_ipv6(self):
        # IPv6 can be upper or lower case
        req = _make_request(xff="2600:1F18:5A5B:3400:2F1E:C9D2:567B:76BC")
        blocked, _, reason = _check_ip(req)
        assert blocked is True
        assert reason == "ERRATIC_BOT"


# ---------------------------------------------------------------------------
# 3. _check_ua — User-Agent substring blocking
# ---------------------------------------------------------------------------

class TestCheckUa:

    def test_yellowmcp_scanner_blocked(self):
        req = _make_request(ua="YellowMCP-SecurityScanner/1.0 (yellowmcp.com)")
        blocked, pattern = _check_ua(req)
        assert blocked is True
        assert "yellowmcp" in pattern.lower()

    def test_yellowmcp_case_insensitive(self):
        req = _make_request(ua="yellowmcp-securityscanner/2.0")
        blocked, _ = _check_ua(req)
        assert blocked is True

    def test_legitimate_python_ua_not_blocked(self):
        req = _make_request(ua="python-httpx/0.27.0")
        blocked, _ = _check_ua(req)
        assert blocked is False

    def test_legitimate_node_ua_not_blocked(self):
        # The "node" UA is generic — only specific IPs are blocked, not all node UAs
        req = _make_request(ua="node/20.11.0")
        blocked, _ = _check_ua(req)
        assert blocked is False

    def test_mcp_client_ua_not_blocked(self):
        req = _make_request(ua="mcp-remote/0.1.0 (claude-code)")
        blocked, _ = _check_ua(req)
        assert blocked is False

    def test_missing_ua_header_not_blocked(self):
        req = MagicMock()
        req.url.path = "/mcp/"
        req.client = MagicMock()
        req.client.host = "203.0.113.1"
        req.headers = {}
        blocked, _ = _check_ua(req)
        assert blocked is False


# ---------------------------------------------------------------------------
# 4. IPBlocklistMiddleware.dispatch — integration
# ---------------------------------------------------------------------------

class TestIPBlocklistMiddlewareDispatch:

    def _middleware(self):
        app_mock = AsyncMock()
        return IPBlocklistMiddleware(app_mock)

    def _call_next_200(self):
        from starlette.responses import JSONResponse
        async def _call_next(req):
            return JSONResponse({"ok": True}, status_code=200)
        return _call_next

    @pytest.mark.asyncio
    async def test_blocked_ipv4_returns_403(self):
        mw = self._middleware()
        req = _make_request(xff="35.161.55.221")
        resp = await mw.dispatch(req, self._call_next_200())
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_blocked_ipv6_returns_403(self):
        mw = self._middleware()
        req = _make_request(xff="2600:1f18:5a5b:3400:2f1e:c9d2:567b:76bc")
        resp = await mw.dispatch(req, self._call_next_200())
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_blocked_scanner_ipv6_returns_403(self):
        mw = self._middleware()
        req = _make_request(xff="2a02:4780:4:2ad9::1")
        resp = await mw.dispatch(req, self._call_next_200())
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_blocked_ua_returns_403(self):
        mw = self._middleware()
        req = _make_request(ua="YellowMCP-SecurityScanner/1.0")
        resp = await mw.dispatch(req, self._call_next_200())
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_legitimate_request_passes_through(self):
        mw = self._middleware()
        req = _make_request(xff="8.8.8.8", ua="python-httpx/0.27.0")
        resp = await mw.dispatch(req, self._call_next_200())
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_403_response_body_format(self):
        import json
        mw = self._middleware()
        req = _make_request(xff="35.161.55.221")
        resp = await mw.dispatch(req, self._call_next_200())
        assert resp.status_code == 403
        body = json.loads(resp.body)
        assert body["error"] == "Forbidden"
        assert body["code"] == 403
        assert "message" in body
        # Must NOT reveal specific reason or blocklist mechanism
        assert "CONTENT_SCRAPER" not in body["message"]
        assert "blocklist" not in body["message"].lower()

    @pytest.mark.asyncio
    async def test_blocked_ip_in_chain_returns_403(self):
        mw = self._middleware()
        req = _make_request(xff="203.0.113.1, 35.161.55.221, 130.211.0.1")
        resp = await mw.dispatch(req, self._call_next_200())
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 5. Audit logging
# ---------------------------------------------------------------------------

class TestAuditLogging:

    def _middleware(self):
        app_mock = AsyncMock()
        return IPBlocklistMiddleware(app_mock)

    def _call_next_200(self):
        from starlette.responses import JSONResponse
        async def _call_next(req):
            return JSONResponse({"ok": True}, status_code=200)
        return _call_next

    @pytest.mark.asyncio
    async def test_ip_blocked_log_emitted(self, caplog):
        mw = self._middleware()
        req = _make_request(xff="35.161.55.221")
        with caplog.at_level(logging.WARNING, logger="verifimind_mcp.middleware.ip_blocklist"):
            await mw.dispatch(req, self._call_next_200())
        logs = [r for r in caplog.records if "[IP_BLOCKED]" in r.message]
        assert logs, "Expected [IP_BLOCKED] log entry"

    @pytest.mark.asyncio
    async def test_ip_blocked_log_contains_ip_and_reason(self, caplog):
        mw = self._middleware()
        req = _make_request(xff="35.161.55.221")
        with caplog.at_level(logging.WARNING, logger="verifimind_mcp.middleware.ip_blocklist"):
            await mw.dispatch(req, self._call_next_200())
        log_msg = caplog.records[-1].message
        assert "35.161.55.221" in log_msg
        assert "CONTENT_SCRAPER" in log_msg

    @pytest.mark.asyncio
    async def test_ua_blocked_log_emitted(self, caplog):
        mw = self._middleware()
        req = _make_request(ua="YellowMCP-SecurityScanner/1.0")
        with caplog.at_level(logging.WARNING, logger="verifimind_mcp.middleware.ip_blocklist"):
            await mw.dispatch(req, self._call_next_200())
        logs = [r for r in caplog.records if "[UA_BLOCKED]" in r.message]
        assert logs, "Expected [UA_BLOCKED] log entry"

    @pytest.mark.asyncio
    async def test_legitimate_request_no_block_log(self, caplog):
        mw = self._middleware()
        req = _make_request(xff="8.8.8.8", ua="python-httpx/0.27.0")
        with caplog.at_level(logging.WARNING, logger="verifimind_mcp.middleware.ip_blocklist"):
            await mw.dispatch(req, self._call_next_200())
        logs = [r for r in caplog.records if "[IP_BLOCKED]" in r.message or "[UA_BLOCKED]" in r.message]
        assert not logs, "No block logs should be emitted for legitimate request"
