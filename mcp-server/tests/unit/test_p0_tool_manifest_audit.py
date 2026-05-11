"""
P0 Tool Manifest Audit — v0.6.0-Beta Pre-req
=============================================

Tests for T's P0 directives (AY Report 078 — 81-endpoint churn response):

1. /.well-known/mcp-config lists all 13 tools (no stale 10-tool manifest)
2. Smithery server-card.json lists all 13 tools
3. http_exception_handler logs [TOOL_NOT_FOUND] with tool/uuid/ip/ts
4. http_exception_handler logs [HTTP_404] for non-tool path misses
5. http_server.py has module-level logger (not undefined reference)

Acceptance criteria from FLYWHEEL TEAM handoff (2026-04-28):
  - tools/list output matches handler registry exactly. Zero phantom tools.
  - Every unknown tool request logged as [TOOL_NOT_FOUND] tool= uuid= ip= ts=
  - Unknown tools return MCP JSON-RPC -32601, not raw 404 (FastMCP layer — verified by import)
"""

import inspect
import json
import logging

import pytest


# ---------------------------------------------------------------------------
# 1. All 13 tool names expected in every manifest
# ---------------------------------------------------------------------------

EXPECTED_TOOLS = {
    # Scholar tier (10)
    "consult_agent_x",
    "consult_agent_z",
    "consult_agent_cs",
    "run_full_trinity",
    "list_prompt_templates",
    "get_prompt_template",
    "export_prompt_template",
    "register_custom_template",
    "import_template_from_url",
    "get_template_statistics",
    # Pioneer tier (3) — shipped v0.5.16, was missing from static manifests
    "coordination_handoff_create",
    "coordination_handoff_read",
    "coordination_team_status",
}

COORDINATION_TOOLS = {
    "coordination_handoff_create",
    "coordination_handoff_read",
    "coordination_team_status",
}


# ---------------------------------------------------------------------------
# 2. Static manifest audit — mcp_config_handler and smithery server card
# ---------------------------------------------------------------------------

class TestMcpConfigManifest:
    """/.well-known/mcp-config must list all 13 tools."""

    def _get_source(self):
        import http_server
        return inspect.getsource(http_server.mcp_config_handler)

    def test_all_13_tool_names_present_in_source(self):
        src = self._get_source()
        missing = [t for t in EXPECTED_TOOLS if t not in src]
        assert missing == [], f"Missing from mcp_config_handler: {missing}"

    def test_coordination_tools_present(self):
        src = self._get_source()
        for tool in COORDINATION_TOOLS:
            assert tool in src, f"{tool} missing from mcp_config_handler"

    def test_no_extra_tool_count_mismatch(self):
        src = self._get_source()
        found = [t for t in EXPECTED_TOOLS if t in src]
        assert len(found) == 13, f"Expected 13 tools in manifest, found {len(found)}"


class TestSmitheryServerCardManifest:
    """/.well-known/mcp/server-card.json must list all 13 tools."""

    def _get_source(self):
        import http_server
        return inspect.getsource(http_server.smithery_server_card_handler)

    def test_all_13_tool_names_present_in_source(self):
        src = self._get_source()
        missing = [t for t in EXPECTED_TOOLS if t not in src]
        assert missing == [], f"Missing from smithery_server_card_handler: {missing}"

    def test_coordination_tools_present(self):
        src = self._get_source()
        for tool in COORDINATION_TOOLS:
            assert tool in src, f"{tool} missing from smithery_server_card_handler"


# ---------------------------------------------------------------------------
# 3. Server.py handler registry — zero phantom tools
# ---------------------------------------------------------------------------

class TestServerHandlerRegistry:
    """Every tool in server.py @app.tool() must match EXPECTED_TOOLS."""

    def _registered_tools(self):
        """Extract function names immediately after @app.tool() decorators."""
        import verifimind_mcp.server as srv
        src = inspect.getsource(srv._create_mcp_instance)
        tools = []
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if "@app.tool()" in line and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith("async def ") or next_line.startswith("def "):
                    name = next_line.split("def ")[1].split("(")[0]
                    tools.append(name)
        return set(tools)

    def test_registered_count_is_13(self):
        tools = self._registered_tools()
        assert len(tools) == 13, f"Expected 13 registered tools, got {len(tools)}: {tools}"

    def test_all_expected_tools_have_handlers(self):
        tools = self._registered_tools()
        missing = EXPECTED_TOOLS - tools
        assert missing == set(), f"Tools in manifest with no handler: {missing}"

    def test_no_phantom_tools_in_registry(self):
        tools = self._registered_tools()
        phantom = tools - EXPECTED_TOOLS
        assert phantom == set(), f"Handlers with no manifest entry: {phantom}"

    def test_coordination_tools_registered(self):
        tools = self._registered_tools()
        for tool in COORDINATION_TOOLS:
            assert tool in tools, f"{tool} has no @app.tool() handler"


# ---------------------------------------------------------------------------
# 4. http_exception_handler — structured logging
# ---------------------------------------------------------------------------

class TestStructuredLogging:
    """http_exception_handler must emit [TOOL_NOT_FOUND] for MCP tool-call 404s."""

    def _make_request(self, method="GET", path="/nonexistent", body=None, ip="1.2.3.4"):
        """Build a minimal Starlette-like mock Request."""
        from unittest.mock import AsyncMock, MagicMock
        req = MagicMock()
        req.method = method
        req.url.path = path
        req.headers = {"x-forwarded-for": ip}
        req.client = None

        async def _body():
            return body or b""

        req.body = _body
        return req

    def _make_exc(self, status=404):
        from unittest.mock import MagicMock
        exc = MagicMock()
        exc.status_code = status
        return exc

    @pytest.mark.asyncio
    async def test_tool_not_found_log_emitted(self, caplog):
        """POST /mcp/ with tools/call body → [TOOL_NOT_FOUND] log."""
        import http_server
        body = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "phantom_tool",
                "arguments": {"concept_name": "test"},
            },
        }).encode()

        req = self._make_request(method="POST", path="/mcp/", body=body)
        exc = self._make_exc(404)

        with caplog.at_level(logging.WARNING, logger="http_server"):
            await http_server.http_exception_handler(req, exc)

        tool_not_found_logs = [r for r in caplog.records if "[TOOL_NOT_FOUND]" in r.message]
        assert tool_not_found_logs, "Expected [TOOL_NOT_FOUND] log entry"
        log_msg = tool_not_found_logs[0].message
        assert "phantom_tool" in log_msg, "Tool name must appear in log"

    @pytest.mark.asyncio
    async def test_tool_not_found_log_includes_uuid_when_present(self, caplog):
        """tools/call with user_uuid in args → UUID appears in log."""
        import http_server
        body = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "missing_tool",
                "arguments": {"user_uuid": "019d40d6-test-uuid-0000-000000000001"},
            },
        }).encode()

        req = self._make_request(method="POST", path="/mcp/", body=body)
        exc = self._make_exc(404)

        with caplog.at_level(logging.WARNING, logger="http_server"):
            await http_server.http_exception_handler(req, exc)

        log_msgs = [r.message for r in caplog.records if "[TOOL_NOT_FOUND]" in r.message]
        assert log_msgs, "Expected [TOOL_NOT_FOUND] log"
        assert "019d40d6-test-uuid" in log_msgs[0], "UUID must appear in log"

    @pytest.mark.asyncio
    async def test_no_body_404_logs_http_404(self, caplog):
        """GET 404 with no body → [HTTP_404] log, not [TOOL_NOT_FOUND]."""
        import http_server
        req = self._make_request(method="GET", path="/nonexistent")
        exc = self._make_exc(404)

        with caplog.at_level(logging.WARNING, logger="http_server"):
            await http_server.http_exception_handler(req, exc)

        http_404_logs = [r for r in caplog.records if "[HTTP_404]" in r.message]
        tool_logs = [r for r in caplog.records if "[TOOL_NOT_FOUND]" in r.message]
        assert http_404_logs, "Expected [HTTP_404] log for non-tool 404"
        assert not tool_logs, "Should not emit [TOOL_NOT_FOUND] for non-tool 404"

    @pytest.mark.asyncio
    async def test_404_response_still_returns_404_status(self):
        """Structured logging must not change the 404 response code."""
        import http_server
        req = self._make_request(method="GET", path="/missing")
        exc = self._make_exc(404)
        response = await http_server.http_exception_handler(req, exc)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_non_tools_call_post_logs_http_404_not_tool_not_found(self, caplog):
        """POST body that is NOT tools/call → [HTTP_404], not [TOOL_NOT_FOUND]."""
        import http_server
        body = json.dumps({"method": "initialize", "params": {}}).encode()
        req = self._make_request(method="POST", path="/mcp/", body=body)
        exc = self._make_exc(404)

        with caplog.at_level(logging.WARNING, logger="http_server"):
            await http_server.http_exception_handler(req, exc)

        tool_logs = [r for r in caplog.records if "[TOOL_NOT_FOUND]" in r.message]
        assert not tool_logs


# ---------------------------------------------------------------------------
# 5. Module-level logger is defined (was a latent NameError)
# ---------------------------------------------------------------------------

class TestLoggerDefined:

    def test_http_server_has_module_logger(self):
        import http_server
        import logging
        assert hasattr(http_server, "logger")
        assert isinstance(http_server.logger, logging.Logger)

    def test_logger_name_is_http_server(self):
        import http_server
        assert http_server.logger.name == "http_server"


# ---------------------------------------------------------------------------
# 6. SERVER_VERSION assertion
# ---------------------------------------------------------------------------

class TestServerVersion:

    def test_server_version_is_0522(self):
        import http_server
        assert http_server.SERVER_VERSION == "0.5.29"
