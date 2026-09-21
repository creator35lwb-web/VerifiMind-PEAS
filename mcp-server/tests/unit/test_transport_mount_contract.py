"""Transport mount contracts for the #346 candidate-SDK lane (T S175 re-entry).

Two properties are pinned here, both of which broke or would silently regress:

1.  `ToolResult` is imported from the DECLARED PUBLIC surface `fastmcp.tools`, not from
    `fastmcp.tools.tool`. FastMCP 4.x deletes that module, so the old path raises
    ModuleNotFoundError before the app is constructed; `fastmcp.tools` resolves on both the
    pinned 3.4.7 and the candidate 4.0.3, which is what lets this import be version-agnostic.
    `fastmcp.tools.base` also works but is the implementation module, not the public API.

2.  The MCP app is mounted with `stateless_http=True`. With the sessionful default, an
    `initialize` on one instance mints a session id that a request landing on another
    instance cannot resolve. The cross-instance test below is paired with a known-negative
    that builds a SESSIONFUL app and requires it to 404, so a green result cannot come from
    the probe simply not exercising an instance switch.

The modern 2026-07-28 era is sessionless regardless of this flag and is covered by a
version-gated test: it SKIPS on an SDK whose LATEST_PROTOCOL_VERSION predates that era, and a
skip is not a pass. Under the pinned manifest it will skip; under the candidate pair it runs.
"""
import importlib.util
import pathlib
import re

import pytest
from starlette.testclient import TestClient

from mcp.types import LATEST_PROTOCOL_VERSION

MODERN_ERA = "2026-07-28"
LEGACY_ERA = "2025-11-25"
HDR = {"accept": "application/json, text/event-stream", "content-type": "application/json"}
MODERN_META = {
    "io.modelcontextprotocol/protocolVersion": MODERN_ERA,
    "io.modelcontextprotocol/clientCapabilities": {},
}

# The four method classes, with the string each successful response must carry.
CALLS = [
    ("tools/list", {}, None, "list_prompt_templates"),
    ("resources/list", {}, None, "genesis://state/project_info"),
    ("resources/read", {"uri": "genesis://state/project_info"}, "genesis://state/project_info", None),
    ("tools/call", {"name": "list_prompt_templates", "arguments": {}}, "list_prompt_templates", None),
]


def _server_root() -> pathlib.Path:
    import http_server

    return pathlib.Path(http_server.__file__).resolve().parent


def _load_app(name, force_stateless=None):
    """Load http_server.py under a distinct module name, so two apps are independent.

    Each load also gets fresh module-level state, which keeps per-app rate limiting from
    leaking between the instances in one test.
    """
    import sys

    path = _server_root() / "http_server.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)

    if force_stateless is None:
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module.app

    from fastmcp import FastMCP

    original = FastMCP.http_app

    def patched(self, *args, **kwargs):
        kwargs["stateless_http"] = force_stateless
        return original(self, *args, **kwargs)

    FastMCP.http_app = patched
    try:
        sys.modules[name] = module
        spec.loader.exec_module(module)
    finally:
        FastMCP.http_app = original
    return module.app


def _cross_instance(client_a, client_b, era):
    """Initialize on A, then run every method class on B. Returns {method: (status, ok)}."""
    init = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": era, "capabilities": {},
                   "clientInfo": {"name": "mount-contract", "version": "0"}},
    }
    response = client_a.post("/mcp/", headers=HDR, json=init)
    session = response.headers.get("mcp-session-id")
    headers = {**HDR, "mcp-protocol-version": era}
    if session:
        headers["mcp-session-id"] = session

    results = {}
    for index, (method, params, _name, expected) in enumerate(CALLS, start=2):
        reply = client_b.post("/mcp/", headers=headers,
                              json={"jsonrpc": "2.0", "id": index, "method": method, "params": params})
        ok = expected in reply.text if expected else '"error"' not in reply.text
        results[method] = (reply.status_code, ok)
    return results


class TestToolResultImportIsPublicAndVersionAgnostic:
    def test_public_surface_exports_tool_result(self):
        import fastmcp.tools

        assert "ToolResult" in getattr(fastmcp.tools, "__all__", ()), (
            "fastmcp.tools must declare ToolResult as public API"
        )
        from fastmcp.tools import ToolResult  # noqa: F401

    def test_no_source_file_imports_the_removed_private_module(self):
        # Claim shape, not a bare word: an import statement naming the deleted module.
        pattern = re.compile(r"^\s*(?:from\s+fastmcp\.tools\.tool\s+import|import\s+fastmcp\.tools\.tool)\b", re.M)
        offenders = []
        for path in (_server_root() / "src").rglob("*.py"):
            if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                offenders.append(str(path.relative_to(_server_root())))
        assert offenders == [], f"fastmcp.tools.tool is removed in FastMCP 4.x: {offenders}"

        # Known-negative: the pattern must actually match the shape it forbids.
        assert pattern.search("from fastmcp.tools.tool import ToolResult\n")
        assert not pattern.search("from fastmcp.tools import ToolResult\n")


class TestMountIsExplicitlyStateless:
    def test_http_app_call_passes_stateless_http_true(self):
        import ast

        source = (_server_root() / "http_server.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "http_app"
        ]
        assert len(calls) == 1, f"expected exactly one http_app mount, found {len(calls)}"
        keywords = {kw.arg: kw.value for kw in calls[0].keywords}
        assert "stateless_http" in keywords, "the mount must state its session mode explicitly"
        value = keywords["stateless_http"]
        assert isinstance(value, ast.Constant) and value.value is True, (
            "stateless_http must be a literal True, so the mode is readable without tracing a variable"
        )


class TestCrossInstanceTransport:
    def test_legacy_era_survives_an_instance_switch(self, monkeypatch):
        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)
        app_a = _load_app("http_server_stateless_a")
        app_b = _load_app("http_server_stateless_b")
        with TestClient(app_a) as a, TestClient(app_b) as b:
            results = _cross_instance(a, b, LEGACY_ERA)
        for method, (status, ok) in results.items():
            assert status == 200, f"{method} returned {status} on a second instance"
            assert ok, f"{method} returned 200 but not the expected payload"

    def test_known_negative_a_sessionful_mount_fails_the_same_probe(self, monkeypatch):
        # Without this, the test above could pass on a build that never switches instances.
        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)
        app_a = _load_app("http_server_sessionful_a", force_stateless=False)
        app_b = _load_app("http_server_sessionful_b", force_stateless=False)
        with TestClient(app_a) as a, TestClient(app_b) as b:
            results = _cross_instance(a, b, LEGACY_ERA)
        assert all(status == 404 for status, _ in results.values()), (
            f"a sessionful mount must lose the session across instances; got {results}"
        )


@pytest.mark.skipif(
    LATEST_PROTOCOL_VERSION < MODERN_ERA,
    reason=(
        f"installed SDK speaks up to {LATEST_PROTOCOL_VERSION}; the {MODERN_ERA} era needs a "
        "newer mcp package. This test SKIPS rather than passes - a skip is not evidence."
    ),
)
class TestModernEraNeedsNoSession:
    def test_fresh_instance_serves_without_initialize(self, monkeypatch):
        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)
        app = _load_app("http_server_modern_fresh")
        with TestClient(app) as client:
            for index, (method, params, name, expected) in enumerate(CALLS, start=20):
                headers = {**HDR, "mcp-protocol-version": MODERN_ERA, "mcp-method": method}
                if name:
                    headers["mcp-name"] = name
                reply = client.post(
                    "/mcp/", headers=headers,
                    json={"jsonrpc": "2.0", "id": index, "method": method,
                          "params": {**params, "_meta": MODERN_META}},
                )
                assert reply.status_code == 200, f"{method} returned {reply.status_code} with no initialize"
                ok = expected in reply.text if expected else '"error"' not in reply.text
                assert ok, f"{method} returned 200 but not the expected payload"

    def test_known_negative_mismatched_target_name_is_refused(self, monkeypatch):
        # First request of a fresh app, so the app's own rate limiter cannot mask the refusal
        # with a 429 - which is exactly how an earlier version of this control was invalidated.
        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)
        app = _load_app("http_server_modern_negative")
        with TestClient(app) as client:
            headers = {**HDR, "mcp-protocol-version": MODERN_ERA,
                       "mcp-method": "tools/call", "mcp-name": "WRONG_NAME"}
            reply = client.post(
                "/mcp/", headers=headers,
                json={"jsonrpc": "2.0", "id": 99, "method": "tools/call",
                      "params": {"name": "list_prompt_templates", "arguments": {},
                                 "_meta": MODERN_META}},
            )
        assert reply.status_code == 400, f"a mismatched mcp-name must be refused, got {reply.status_code}"
        assert "-32020" in reply.text
