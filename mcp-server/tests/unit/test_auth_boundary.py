"""HTTP OAuth boundary contract (Design v2, T P0-4/P0-5/P0-7).

Dark parity, the 401 + WWW-Authenticate challenge, 403 insufficient_scope,
fail-closed 503 on token-store outage, ACCESS/PAT accept + REFRESH reject,
subject/actor contextvar binding, execution-mode body peek + replay, and the
default-off issuance gate (dark issuance produces no writes/mail).
"""

import base64
import hashlib
import json
import secrets
import warnings
from unittest.mock import patch

import pytest

warnings.filterwarnings("ignore", category=DeprecationWarning)

from verifimind_mcp.middleware.mcp_auth_boundary import McpAuthBoundary
from verifimind_mcp.middleware.registration_gate import (
    AUTH_ACTOR_CLASS,
    AUTH_SUBJECT_UUID,
)
from verifimind_mcp.oauth import authlib_server as A
from verifimind_mcp.oauth import core, stores

from .oauth_fakes import FakeFirestore


@pytest.fixture()
def env(monkeypatch):
    monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "development")
    monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", "http://localhost:8080")
    monkeypatch.setenv("OAUTH_ISSUANCE_ENABLED", "true")
    monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")


@pytest.fixture()
def db(env):
    fake = FakeFirestore()
    stores.clear_caches()
    with patch("verifimind_mcp.registration._get_firestore", return_value=fake):
        yield fake
    stores.clear_caches()


def _issue_access(db, subject="subj-1"):
    cid = stores.register_client(client_name="CLI", redirect_uris=["https://c/cb"], registration_path="dcr")
    v = secrets.token_urlsafe(48)[:64]
    ch = base64.urlsafe_b64encode(hashlib.sha256(v.encode()).digest()).rstrip(b"=").decode()
    code = core.mint_authorization_code()
    stores.persist_code(code_id=code.token_id, code_secret_hash=code.secret_hash, client_id=cid,
                        subject_uuid=subject, redirect_uri="https://c/cb", code_challenge=ch, scope="mcp")
    server = A.build_authorization_server()
    _st, body, _ = server.create_token_response(A.build_request(
        method="POST", uri="http://localhost:8080/oauth/token",
        form_pairs=[("grant_type", "authorization_code"), ("code", code.token),
                    ("code_verifier", v), ("client_id", cid), ("redirect_uri", "https://c/cb")],
        query_pairs=[], headers={}))
    return body["access_token"], body["refresh_token"]


def _scope(path="/mcp/", method="POST", headers=None):
    return {"type": "http", "method": method, "path": path,
            "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]}


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
            self.headers = {k.decode(): v.decode() for k, v in message.get("headers", [])}
        elif message["type"] == "http.response.body":
            self.body += message.get("body", b"")


class _InnerApp:
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


def _run(boundary, scope, receive):
    import asyncio
    sink = _Sink()
    asyncio.run(boundary(scope, receive, sink))
    return sink


class TestDarkParity:
    def test_disabled_gate_passes_everything(self, monkeypatch):
        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(b'{"method":"x"}'))
        assert inner.called and sink.status == 200 and inner.subject is None

    def test_non_mcp_paths_never_challenged(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(path="/health", method="GET"), _receive_for(b""))
        assert inner.called and sink.status == 200


class TestConnectionMode:
    def test_missing_token_401_with_resource_metadata(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setenv("AUTH_BOUNDARY_MODE", "connection")
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(b"{}"))
        assert not inner.called and sink.status == 401
        challenge = sink.headers["www-authenticate"]
        assert challenge.startswith("Bearer ") and "oauth-protected-resource" in challenge

    def test_invalid_token_401(self, monkeypatch, db):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner),
                    _scope(headers={"authorization": "Bearer vmat.fake.fake"}), _receive_for(b"{}"))
        assert not inner.called and sink.status == 401

    def test_valid_access_binds_identity(self, monkeypatch, db):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        access, _refresh = _issue_access(db)
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner),
                    _scope(headers={"authorization": f"Bearer {access}"}),
                    _receive_for(b'{"method":"tools/list"}'))
        assert inner.called and sink.status == 200
        assert inner.subject == "subj-1" and inner.actor == "external"
        assert AUTH_SUBJECT_UUID.get() is None  # reset after request

    def test_pat_accepted_refresh_rejected(self, monkeypatch, db):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        _access, refresh = _issue_access(db)
        pat = stores.issue_pat(subject_uuid="subj-1", actor_class="external", parent_grant_id="g-test").token
        inner_pat = _InnerApp()
        sink_pat = _run(McpAuthBoundary(inner_pat),
                        _scope(headers={"authorization": f"Bearer {pat}"}), _receive_for(b"{}"))
        assert inner_pat.called and sink_pat.status == 200
        inner_ref = _InnerApp()
        sink_ref = _run(McpAuthBoundary(inner_ref),
                        _scope(headers={"authorization": f"Bearer {refresh}"}), _receive_for(b"{}"))
        assert not inner_ref.called and sink_ref.status == 401

    def test_insufficient_scope_403(self, monkeypatch, db):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        access, _r = _issue_access(db)
        # Strip the token's scope so the required 'mcp' is missing.
        parsed = core.parse_token(access)
        db.collection(stores.c_tokens()).document(parsed.token_id).update({"scope": "other"})
        stores.clear_caches()
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(headers={"authorization": f"Bearer {access}"}), _receive_for(b"{}"))
        assert not inner.called and sink.status == 403
        assert "insufficient_scope" in sink.headers["www-authenticate"]

    def test_store_outage_is_503(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        stores.clear_caches()
        inner = _InnerApp()
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            sink = _run(McpAuthBoundary(inner),
                        _scope(headers={"authorization": "Bearer vmat.some.token"}), _receive_for(b"{}"))
        assert not inner.called and sink.status == 503 and sink.headers.get("retry-after") == "120"

    def test_revoked_token_rejected(self, monkeypatch, db):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        access, _r = _issue_access(db)
        stores.revoke_credential(access)
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(headers={"authorization": f"Bearer {access}"}), _receive_for(b"{}"))
        assert not inner.called and sink.status == 401

    def test_legacy_uuid_header_confers_nothing(self, monkeypatch, db):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(headers={"x-verifimind-uuid": "subj-1"}), _receive_for(b"{}"))
        assert not inner.called and sink.status == 401


class TestExecutionMode:
    def test_discovery_passes_with_body_replayed(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setenv("AUTH_BOUNDARY_MODE", "execution")
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode()
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(body))
        assert inner.called and sink.status == 200 and inner.body == body

    def test_gated_tools_call_requires_token(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setenv("AUTH_BOUNDARY_MODE", "execution")
        body = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                           "params": {"name": "run_full_trinity", "arguments": {}}}).encode()
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(body))
        assert not inner.called and sink.status == 401

    def test_unparseable_body_fails_toward_authentication(self, monkeypatch):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setenv("AUTH_BOUNDARY_MODE", "execution")
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(b"\xff\xfe not json"))
        assert not inner.called and sink.status == 401


class TestFullAppDarkParity:
    def test_mcp_post_without_gate_not_challenged(self, monkeypatch):
        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)
        import http_server
        from starlette.testclient import TestClient
        with TestClient(http_server.app) as tc:
            response = tc.post("/mcp/", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        assert response.status_code != 401


class TestAdversarialFindings:
    """Regressions for S155 attacker-position findings outside the token core."""

    def test_array_params_do_not_crash_the_boundary(self, monkeypatch):
        # JSON-RPC permits array params; `.get()` on a list raised
        # AttributeError and escaped as an unhandled 500 for any anonymous
        # caller in execution mode.
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setenv("AUTH_BOUNDARY_MODE", "execution")
        body = json.dumps({"jsonrpc": "2.0", "id": 1,
                           "method": "tools/call", "params": [1, 2]}).encode()
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(body))
        assert not inner.called and sink.status == 401  # protected, not 500

    def test_misconfigured_env_never_challenges_toward_production(self, monkeypatch):
        # A broken staging service used to fall back to the hardcoded
        # production PRM, handing clients the production authorization server.
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "staging")
        monkeypatch.delenv("VERIFIMIND_PUBLIC_ORIGIN", raising=False)
        inner = _InnerApp()
        sink = _run(McpAuthBoundary(inner), _scope(), _receive_for(b"{}"))
        assert not inner.called and sink.status == 401
        assert "verifimind.ysenseai.org" not in sink.headers["www-authenticate"]

    def test_mailer_refuses_recipient_lists(self):
        # One request delivered the OTP to an off-allowlist address because
        # the allowlist read only the last @-segment while smtplib derived
        # BOTH envelope recipients from the To: header.
        from verifimind_mcp.oauth.mailer import MailerUnavailable, send_verification_email
        with pytest.raises(MailerUnavailable):
            send_verification_email(
                to_email="attacker@evil.com, ok@ysenseai.org",
                code="12345678", purpose="authorize",
            )

    def test_non_production_service_must_declare_its_environment(self, monkeypatch):
        # A staging revision that merely omitted one env var silently became
        # production: bare collections and production-audience tokens.
        from verifimind_mcp.oauth import config
        monkeypatch.delenv("VERIFIMIND_ENVIRONMENT", raising=False)
        monkeypatch.setenv("K_SERVICE", "verifimind-mcp-staging")
        with pytest.raises(config.EnvironmentMisconfigured):
            config.current_environment()
        monkeypatch.setenv("K_SERVICE", config.PRODUCTION_SERVICE_NAME)
        assert config.current_environment().name == "production"
