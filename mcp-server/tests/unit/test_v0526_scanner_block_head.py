"""
Tests for v0.5.26 — Scanner block + HEAD /mcp/ handler

Coverage:
  - 54.67.34.241 present in BLOCKED_IPS
  - BLOCKED_IPS entry has correct format (ip, reason, date, agent)
  - mcp_head_handler returns 200 Response
  - mcp_head_handler includes X-Server-Version header
  - mcp_head_handler includes Content-Type header
  - Server version is 0.5.26
"""

import pytest


class TestScannerIPBlock:

    def test_scanner_ip_in_blocklist(self):
        from verifimind_mcp.middleware.ip_blocklist import BLOCKED_IPS
        blocked = [ip for ip, *_ in BLOCKED_IPS]
        assert "54.67.34.241" in blocked

    def test_scanner_ip_reason_is_unauthorized_scanner(self):
        from verifimind_mcp.middleware.ip_blocklist import BLOCKED_IPS
        entry = next((e for e in BLOCKED_IPS if e[0] == "54.67.34.241"), None)
        assert entry is not None
        assert entry[1] == "UNAUTHORIZED_SCANNER"

    def test_scanner_ip_date_added(self):
        from verifimind_mcp.middleware.ip_blocklist import BLOCKED_IPS
        entry = next((e for e in BLOCKED_IPS if e[0] == "54.67.34.241"), None)
        assert entry[2] == "2026-05-06"

    def test_blocked_ip_set_includes_scanner(self):
        from verifimind_mcp.middleware.ip_blocklist import _BLOCKED_IP_SET
        assert "54.67.34.241" in _BLOCKED_IP_SET

    def test_total_blocked_ips_is_four(self):
        from verifimind_mcp.middleware.ip_blocklist import BLOCKED_IPS
        assert len(BLOCKED_IPS) >= 4

    def test_ssrf_scanner_ip_in_blocklist(self):
        from verifimind_mcp.middleware.ip_blocklist import BLOCKED_IPS
        blocked = [ip for ip, *_ in BLOCKED_IPS]
        assert "195.178.110.157" in blocked

    def test_ssrf_scanner_ip_reason(self):
        from verifimind_mcp.middleware.ip_blocklist import BLOCKED_IPS
        entry = next((e for e in BLOCKED_IPS if e[0] == "195.178.110.157"), None)
        assert entry is not None
        assert entry[1] == "SSRF_SCANNER"

    def test_ssrf_scanner_ip_in_blocked_set(self):
        from verifimind_mcp.middleware.ip_blocklist import _BLOCKED_IP_SET
        assert "195.178.110.157" in _BLOCKED_IP_SET


class TestMcpHeadHandler:

    def test_mcp_head_handler_exists(self):
        import http_server
        assert hasattr(http_server, "mcp_head_handler")

    @pytest.mark.asyncio
    async def test_mcp_head_handler_returns_200(self):
        import http_server
        from unittest.mock import MagicMock
        mock_request = MagicMock()
        response = await http_server.mcp_head_handler(mock_request)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_mcp_head_handler_has_content_type(self):
        import http_server
        from unittest.mock import MagicMock
        mock_request = MagicMock()
        response = await http_server.mcp_head_handler(mock_request)
        assert "content-type" in {k.lower() for k in response.headers.keys()}

    @pytest.mark.asyncio
    async def test_mcp_head_handler_has_server_version_header(self):
        import http_server
        from unittest.mock import MagicMock
        mock_request = MagicMock()
        response = await http_server.mcp_head_handler(mock_request)
        assert "x-server-version" in {k.lower() for k in response.headers.keys()}


class TestServerVersion:

    def test_server_version_is_0526(self):
        import http_server
        assert http_server.SERVER_VERSION == "0.5.42"
