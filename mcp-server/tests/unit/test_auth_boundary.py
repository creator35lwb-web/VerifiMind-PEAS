"""HTTP OAuth boundary contract (Design v2, D-153-5).

Dark parity, the 401 + WWW-Authenticate challenge (with the RFC 9728
resource-metadata pointer OAuth clients need to start the flow), fail-closed
503 on token-store outage, subject/actor contextvar binding, and
execution-mode body peek + replay integrity.
"""

import json
from unittest.mock import patch

import pytest

from verifimind_mcp.middleware.mcp_auth_boundary import McpAuthBoundary
from verifimind_mcp.middleware.registration_gate import (
    AUTH_ACTOR_CLASS,
    AUTH_SUBJECT_UUID,
)
from verifimind_mcp.oauth import core, stores

from .oauth_fakes import FakeFirestore

SUBJECT = "018f6b2a-bbbb-7abc-8def-0123456789ab"


def _scope(path="/mcp/", method="POST", headers=None):
    return {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [
            (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
        ],
    }


def _receive_for(body: bytes):
    sent = {"done": False}

    async def receive():
        if sent["done"]:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent["done"] = True
        return {"type": "http.request", "body": body, "more_body": False}

    return receive


class _Sink:
    def __init__(self):
        self.status = None
        self.headers = {}
        self.body = b""

    async def __call__(self, message):
        if message["type"] == "http.response.start":
            self.status = message["status"]
            self.headers = {
                k.decode(): v.decode() for k, v in message.get("headers", [])
            }
        elif message["type"] == "http.response.body":
            self.body += message.get("body", b"")


class _InnerApp:
    """Records what reached the app: contextvars and the replayed body."""

    def __init__(self):
        self.called = False
        self.subject = "unset"
        self.actor = "unset"
        self.body = b""

    async def __call__(self, scope, receive, send):
        self.called = True
        self.subject = AUTH_SUBJECT_UUID.get()
        self.actor = AUTH_ACTOR_CLASS.get()
        while True:
            message = await receive()
            self.body += message.get("body", b"")
            if not message.get("more_body", False):
                break
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})


@pytest.fixture()
def db():
    fake = FakeFirestore()
    stores.clear_caches()
    with patch("verifimind_mcp.registration._get_firestore", return_value=fake):
        yield fake
    stores.clear_caches()


def _run(boundary, scope, receive):
    import asyncio
    sink = _Sink()
    asyncio.get_event_loop_policy().new_event_loop()
    asyncio.run(boundary(scope, receive, sink))
    return sink


class TestDarkParity:
    def test_disabled_gate_passes_everything(self, monkeypatch):
        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)
        inner = _InnerApp()
        sink = _run(
            McpAuthBoundary(inner), _scope(), _receive_for(b'{"method":"x"}')
        )
        assert inner.called and sink.status == 200
        assert inner.subject is None

    def test_non_mcp_paths_never_challenged(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        inner = _InnerApp()
        sink = _run(
            McpAuthBoundary(inner), _scope(path="/health", method="GET"),
            _receive_for(b""),
        )
        assert inner.called and sink.status == 200


class TestConnectionMode:
    def test_missing_token_gets_401_with_resource_metadata(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setenv("AUTH_BOUNDARY_MODE", "connection")
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(b"{}"))
        assert not inner.called
        assert sink.status == 401
        challenge = sink.headers["www-authenticate"]
        assert challenge.startswith("Bearer ")
        assert "/.well-known/oauth-protected-resource" in challenge
        assert json.loads(sink.body)["error"] == "invalid_token"

    def test_invalid_token_gets_401(self, monkeypatch, db):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        inner = _InnerApp()
        sink = _run(
            McpAuthBoundary(inner),
            _scope(headers={"authorization": "Bearer vmat.fake.fake"}),
            _receive_for(b"{}"),
        )
        assert not inner.called and sink.status == 401

    def test_valid_token_passes_and_binds_identity(self, monkeypatch, db):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        minted = stores.issue_token(
            kind=core.ACCESS, subject_uuid=SUBJECT, client_id="c",
            actor_class="external",
        )
        inner = _InnerApp()
        sink = _run(
            McpAuthBoundary(inner),
            _scope(headers={"authorization": f"Bearer {minted.token}"}),
            _receive_for(b'{"method":"tools/list"}'),
        )
        assert inner.called and sink.status == 200
        assert inner.subject == SUBJECT
        assert inner.actor == "external"
        # Contextvars reset after the request.
        assert AUTH_SUBJECT_UUID.get() is None

    def test_store_outage_is_503_never_open(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        stores.clear_caches()
        inner = _InnerApp()
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            sink = _run(
                McpAuthBoundary(inner),
                _scope(headers={"authorization": "Bearer vmat.some.token"}),
                _receive_for(b"{}"),
            )
        assert not inner.called
        assert sink.status == 503
        assert sink.headers.get("retry-after") == "120"

    def test_revoked_token_rejected_at_boundary(self, monkeypatch, db):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        minted = stores.issue_token(kind=core.ACCESS, subject_uuid=SUBJECT, client_id="c")
        stores.revoke_token(minted.token)
        inner = _InnerApp()
        sink = _run(
            McpAuthBoundary(inner),
            _scope(headers={"authorization": f"Bearer {minted.token}"}),
            _receive_for(b"{}"),
        )
        assert not inner.called and sink.status == 401

    def test_legacy_uuid_header_confers_nothing(self, monkeypatch, db):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        inner = _InnerApp()
        sink = _run(
            McpAuthBoundary(inner),
            _scope(headers={"x-verifimind-uuid": SUBJECT}),
            _receive_for(b"{}"),
        )
        assert not inner.called and sink.status == 401


class TestExecutionMode:
    def test_discovery_passes_anonymously_with_body_replayed(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setenv("AUTH_BOUNDARY_MODE", "execution")
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode()
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(body))
        assert inner.called and sink.status == 200
        assert inner.body == body  # replay integrity — nothing consumed

    def test_gated_tools_call_requires_token(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setenv("AUTH_BOUNDARY_MODE", "execution")
        body = json.dumps({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": "run_full_trinity", "arguments": {}},
        }).encode()
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(body))
        assert not inner.called and sink.status == 401

    def test_ungated_tools_call_passes(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setenv("AUTH_BOUNDARY_MODE", "execution")
        body = json.dumps({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "list_prompt_templates", "arguments": {}},
        }).encode()
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(body))
        assert inner.called and sink.status == 200
        assert inner.body == body

    def test_unparseable_body_fails_toward_authentication(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setenv("AUTH_BOUNDARY_MODE", "execution")
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(b"\xff\xfe not json"))
        assert not inner.called and sink.status == 401


class TestFullAppDarkParity:
    def test_mcp_post_without_gate_is_not_challenged(self, monkeypatch):
        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)
        import http_server
        from starlette.testclient import TestClient
        with TestClient(http_server.app) as tc:
            response = tc.post("/mcp/", json={"jsonrpc": "2.0", "id": 1,
                                              "method": "tools/list"})
        assert response.status_code != 401
        assert "www-authenticate" not in {k.lower() for k in response.headers}
