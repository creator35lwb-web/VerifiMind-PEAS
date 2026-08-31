"""OAuth 2.1 spine contract — core, stores, and HTTP endpoints (Design v2).

Covers the T S152/S153 acceptance receipts that live in this layer:
hash-at-rest storage, PKCE-bound single-use codes, refresh rotation with
reuse-detection lineage revocation, RFC 7009 revoke, bounded DCR, the
enumeration-safe verification ceremony, issuance limits, and the full
authorize→token→validate walk through the real HTTP app.
"""

import re
from unittest.mock import patch

import pytest

from verifimind_mcp.oauth import core, stores
from verifimind_mcp.oauth.stores import StoreUnavailable

from .oauth_fakes import FakeFirestore

SUBJECT = "018f6b2a-aaaa-7abc-8def-0123456789ab"


@pytest.fixture()
def db():
    fake = FakeFirestore()
    stores.clear_caches()
    with patch("verifimind_mcp.registration._get_firestore", return_value=fake):
        yield fake
    stores.clear_caches()


def _register_client(redirect="https://client.example/callback"):
    return stores.register_client(
        client_name="Test MCP Client",
        redirect_uris=[redirect],
        registration_path="dcr",
    )


class TestStores:
    def test_secrets_never_stored_in_plaintext(self, db):
        minted = stores.issue_token(kind=core.ACCESS, subject_uuid=SUBJECT, client_id="c")
        stored = db.data["oauth_tokens"][minted.token_id]
        secret = minted.token.split(".")[2]
        assert secret not in str(stored)
        assert stored["secret_hash"] == core.sha256_hex(secret)

    def test_validate_round_trip_and_kind_binding(self, db):
        minted = stores.issue_token(kind=core.ACCESS, subject_uuid=SUBJECT, client_id="c")
        record = stores.validate_token(minted.token)
        assert record and record.subject_uuid == SUBJECT
        assert stores.validate_token(minted.token, expected_kind=core.REFRESH) is None

    def test_validate_rejects_wrong_secret(self, db):
        minted = stores.issue_token(kind=core.ACCESS, subject_uuid=SUBJECT, client_id="c")
        forged = minted.token[:-4] + "XXXX"
        assert stores.validate_token(forged) is None

    def test_revoked_token_fails_within_cache_ttl_locally(self, db):
        minted = stores.issue_token(kind=core.ACCESS, subject_uuid=SUBJECT, client_id="c")
        assert stores.validate_token(minted.token) is not None
        assert stores.revoke_token(minted.token) is True
        # Local revoke purges the cache immediately.
        assert stores.validate_token(minted.token) is None

    def test_expired_token_rejected(self, db):
        minted = stores.issue_token(kind=core.ACCESS, subject_uuid=SUBJECT, client_id="c")
        db.data["oauth_tokens"][minted.token_id]["expires_at"] = 1.0
        assert stores.validate_token(minted.token) is None

    def test_outage_raises_store_unavailable_never_passes(self):
        stores.clear_caches()
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            with pytest.raises(StoreUnavailable):
                stores.validate_token("vmat.x.y")

    def test_refresh_rotation_and_reuse_detection(self, db):
        refresh = stores.issue_token(kind=core.REFRESH, subject_uuid=SUBJECT, client_id="c")
        first = stores.rotate_refresh_token(refresh.token)
        assert first is not None
        # Reusing the ROTATED (old) refresh token is a theft signal: the
        # subject's live credentials are revoked wholesale.
        assert stores.rotate_refresh_token(refresh.token) is None
        assert stores.validate_token(first["access"].token) is None

    def test_revoke_all_for_subject_tombstones_everything(self, db):
        a = stores.issue_token(kind=core.ACCESS, subject_uuid=SUBJECT, client_id="c1")
        b = stores.issue_token(kind=core.PAT, subject_uuid=SUBJECT, client_id=None)
        other = stores.issue_token(kind=core.ACCESS, subject_uuid="other", client_id="c2")
        revoked = stores.revoke_all_for_subject(SUBJECT)
        assert revoked == 2
        assert stores.validate_token(a.token) is None
        assert stores.validate_token(b.token, expected_kind=core.PAT) is None
        assert stores.validate_token(other.token) is not None

    def test_authorization_code_single_use_and_hashing(self, db):
        code = stores.issue_code(
            client_id="c", subject_uuid=SUBJECT,
            redirect_uri="https://client.example/callback",
            code_challenge="ch", scope="mcp",
        )
        secret = code.split(".")[2]
        assert secret not in str(db.data["oauth_codes"])
        first = stores.consume_code(code)
        assert first and first["subject_uuid"] == SUBJECT
        assert stores.consume_code(code) is None  # single-use

    def test_verification_attempt_cap_and_consume(self, db):
        stores.put_verification(email="a@b.co", code="12345678", purpose="authorize")
        for _ in range(stores.VERIFICATION_MAX_ATTEMPTS):
            assert stores.check_verification(email="a@b.co", code="00000000") is False
        # Cap reached: even the right code no longer verifies.
        assert stores.check_verification(email="a@b.co", code="12345678") is False
        stores.put_verification(email="c@d.co", code="87654321", purpose="authorize")
        assert stores.check_verification(email="c@d.co", code="87654321") is True
        # Consumed on success.
        assert stores.check_verification(email="c@d.co", code="87654321") is False

    def test_verification_stores_email_hash_only(self, db):
        stores.put_verification(email="Person@Example.com", code="11112222", purpose="x")
        blob = str(db.data["oauth_email_verifications"])
        assert "person@example.com" not in blob.lower().replace(
            core.sha256_hex("person@example.com"), ""
        )


@pytest.fixture()
def client(db, monkeypatch):
    import http_server
    from starlette.testclient import TestClient
    from verifimind_mcp.middleware import rate_limiter
    from verifimind_mcp.oauth.endpoints import issuance_limiter

    # Keep the shared-process rate buckets out of these walks: fresh store
    # per test so batch order can never manufacture a 429.
    monkeypatch.setattr(
        rate_limiter, "_rate_limit_store", rate_limiter.RateLimitStore()
    )
    monkeypatch.setitem(rate_limiter.TIER_LIMITS, "anonymous", 10_000)
    monkeypatch.setattr(rate_limiter, "RATE_LIMIT_GLOBAL", 100_000)
    monkeypatch.setenv("MAILER_BACKEND", "console")
    monkeypatch.delenv("K_SERVICE", raising=False)
    issuance_limiter.reset()
    with TestClient(http_server.app) as tc:
        yield tc
    issuance_limiter.reset()


class TestMetadata:
    def test_protected_resource_metadata(self, client):
        body = client.get("/.well-known/oauth-protected-resource").json()
        assert body["resource"].endswith("/mcp")
        assert body["authorization_servers"] == ["https://verifimind.ysenseai.org"]

    def test_authorization_server_metadata(self, client):
        body = client.get("/.well-known/oauth-authorization-server").json()
        assert body["code_challenge_methods_supported"] == ["S256"]
        assert body["token_endpoint_auth_methods_supported"] == ["none"]
        assert body["grant_types_supported"] == [
            "authorization_code", "refresh_token",
        ]


class TestDcr:
    def test_register_accepts_https_and_loopback(self, client):
        response = client.post("/oauth/register", json={
            "client_name": "CLI",
            "redirect_uris": ["http://127.0.0.1:33418/callback"],
        })
        assert response.status_code == 201
        assert response.json()["client_id"].startswith("vmc_")

    def test_register_rejects_plain_http_remote(self, client):
        response = client.post("/oauth/register", json={
            "redirect_uris": ["http://evil.example/cb"],
        })
        assert response.status_code == 400


class TestAuthorizeCeremonyEndToEnd:
    def _pkce(self):
        import base64
        import hashlib
        import secrets as s
        verifier = s.token_urlsafe(48)[:64]
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).rstrip(b"=").decode()
        return verifier, challenge

    def test_full_flow_register_verify_consent_token(self, client, db, capsys):
        client_id = _register_client()
        verifier, challenge = self._pkce()
        page = client.get("/oauth/authorize", params={
            "client_id": client_id,
            "redirect_uri": "https://client.example/callback",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "xyz",
        })
        assert page.status_code == 200
        sid = re.search(r"name='sid' value='([^']+)'", page.text).group(1)

        sent = client.post("/oauth/authorize", data={
            "sid": sid, "action": "send_code", "email": "new@example.com",
        })
        assert sent.status_code == 200
        code = re.search(
            r"verification code for authorize: (\d{8})", capsys.readouterr().err
        ).group(1)

        verified = client.post("/oauth/authorize", data={
            "sid": sid, "action": "verify_code",
            "email": "new@example.com", "code": code,
        })
        assert "Authorize access" in verified.text

        consent = client.post("/oauth/authorize", data={
            "sid": sid, "action": "consent", "decision": "allow", "agree": "on",
        }, follow_redirects=False)
        assert consent.status_code == 302
        location = consent.headers["location"]
        assert location.startswith("https://client.example/callback?")
        auth_code = re.search(r"code=([^&]+)", location).group(1)
        assert "state=xyz" in location

        token = client.post("/oauth/token", data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "code_verifier": verifier,
            "client_id": client_id,
            "redirect_uri": "https://client.example/callback",
        })
        assert token.status_code == 200
        body = token.json()
        assert body["token_type"] == "Bearer"
        record = stores.validate_token(body["access_token"])
        assert record is not None
        # The ceremony created the account with a verified mailbox.
        account = db.data["ea_registrations"][record.subject_uuid]
        assert account["email_verified"] is True
        assert account["registration_path"] == "oauth_ceremony_v2"

        # Refresh rotation works end-to-end.
        refreshed = client.post("/oauth/token", data={
            "grant_type": "refresh_token",
            "refresh_token": body["refresh_token"],
        })
        assert refreshed.status_code == 200

        # PAT issuance from a live access token.
        pat = client.post("/oauth/pat", headers={
            "Authorization": f"Bearer {refreshed.json()['access_token']}",
        })
        assert pat.status_code == 200
        assert pat.json()["personal_access_token"].startswith("vmpat.")

    def test_duplicate_email_answer_is_uniform(self, client, db, capsys):
        client_id = _register_client()
        _verifier, challenge = self._pkce()
        db.data.setdefault("ea_registrations", {})["existing-uuid"] = {
            "uuid": "existing-uuid", "email": "known@example.com",
            "status": "active", "tier": "ea",
        }

        def _send(email):
            page = client.get("/oauth/authorize", params={
                "client_id": client_id,
                "redirect_uri": "https://client.example/callback",
                "response_type": "code",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "state": "s",
            })
            sid = re.search(r"name='sid' value='([^']+)'", page.text).group(1)
            return client.post("/oauth/authorize", data={
                "sid": sid, "action": "send_code", "email": email,
            })

        known = _send("known@example.com")
        fresh = _send("fresh@example.com")
        # Same page, same copy — account existence is never disclosed and
        # no UUID or credential appears for either path (T P0 #1).
        assert known.status_code == fresh.status_code == 200
        for response in (known, fresh):
            assert "existing-uuid" not in response.text
            assert "already registered" not in response.text.lower()

    def test_unknown_client_never_redirects(self, client):
        response = client.get("/oauth/authorize", params={
            "client_id": "vmc_forged",
            "redirect_uri": "https://attacker.example/steal",
            "response_type": "code",
            "code_challenge": "x",
            "code_challenge_method": "S256",
        }, follow_redirects=False)
        assert response.status_code == 400  # open-redirect guard

    def test_wrong_pkce_verifier_is_invalid_grant(self, client, db, capsys):
        client_id = _register_client()
        verifier, challenge = self._pkce()
        page = client.get("/oauth/authorize", params={
            "client_id": client_id,
            "redirect_uri": "https://client.example/callback",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": "s",
        })
        sid = re.search(r"name='sid' value='([^']+)'", page.text).group(1)
        client.post("/oauth/authorize", data={
            "sid": sid, "action": "send_code", "email": "p@example.com",
        })
        code = re.search(
            r"verification code for authorize: (\d{8})", capsys.readouterr().err
        ).group(1)
        client.post("/oauth/authorize", data={
            "sid": sid, "action": "verify_code",
            "email": "p@example.com", "code": code,
        })
        consent = client.post("/oauth/authorize", data={
            "sid": sid, "action": "consent", "decision": "allow", "agree": "on",
        }, follow_redirects=False)
        auth_code = re.search(r"code=([^&]+)", consent.headers["location"]).group(1)
        token = client.post("/oauth/token", data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "code_verifier": verifier + "tampered",
            "client_id": client_id,
            "redirect_uri": "https://client.example/callback",
        })
        assert token.status_code == 400
        assert token.json()["error"] == "invalid_grant"

    def test_revoked_account_email_never_resolves(self, client, db, capsys):
        client_id = _register_client()
        _v, challenge = self._pkce()
        db.data.setdefault("ea_registrations", {})["gone-uuid"] = {
            "uuid": "gone-uuid", "email": "gone@example.com",
            "status": "deletion_requested", "tier": "ea",
        }
        page = client.get("/oauth/authorize", params={
            "client_id": client_id,
            "redirect_uri": "https://client.example/callback",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        })
        sid = re.search(r"name='sid' value='([^']+)'", page.text).group(1)
        client.post("/oauth/authorize", data={
            "sid": sid, "action": "send_code", "email": "gone@example.com",
        })
        code = re.search(
            r"verification code for authorize: (\d{8})", capsys.readouterr().err
        ).group(1)
        client.post("/oauth/authorize", data={
            "sid": sid, "action": "verify_code",
            "email": "gone@example.com", "code": code,
        })
        consent = client.post("/oauth/authorize", data={
            "sid": sid, "action": "consent", "decision": "allow", "agree": "on",
        }, follow_redirects=False)
        # A deletion-requested identity cannot re-authenticate through the
        # ceremony: no code is issued for it.
        assert consent.status_code == 503


class TestIssuanceLimits:
    def test_send_code_limited_per_ip(self, client, db):
        from verifimind_mcp.oauth.endpoints import issuance_limiter
        client_id = _register_client()
        page = client.get("/oauth/authorize", params={
            "client_id": client_id,
            "redirect_uri": "https://client.example/callback",
            "response_type": "code",
            "code_challenge": "c" * 43,
            "code_challenge_method": "S256",
        })
        sid = re.search(r"name='sid' value='([^']+)'", page.text).group(1)
        limit, _window = issuance_limiter.LIMITS["send_code"]
        for i in range(limit):
            assert issuance_limiter.allow("send_code", "testclient")
        response = client.post("/oauth/authorize", data={
            "sid": sid, "action": "send_code", "email": "x@example.com",
        })
        assert "Too many codes" in response.text

    def test_mailer_fail_closed_in_production(self, client, db, monkeypatch):
        # Cloud Run + console backend must refuse: verification codes may
        # never leak into production logs, and the ceremony answers 503.
        monkeypatch.setenv("K_SERVICE", "verifimind-mcp-server")
        client_id = _register_client()
        page = client.get("/oauth/authorize", params={
            "client_id": client_id,
            "redirect_uri": "https://client.example/callback",
            "response_type": "code",
            "code_challenge": "c" * 43,
            "code_challenge_method": "S256",
        })
        sid = re.search(r"name='sid' value='([^']+)'", page.text).group(1)
        response = client.post("/oauth/authorize", data={
            "sid": sid, "action": "send_code", "email": "y@example.com",
        })
        assert response.status_code == 503
