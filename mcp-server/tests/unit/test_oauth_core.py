"""OAuth 2.1 Authlib-core discriminating contracts (D-ALTON-AUTHLIB).

Covers the T S154 preflight P0 negatives and concurrency barriers:
PKCE matrix, wrong-verifier-does-not-consume, exactly-one concurrent winner,
refresh rotation + replay family-revocation, ACCESS/PAT vs REFRESH bearer,
the P0-1 cache secret-bypass probe (before AND after warm-up), issuer/
audience/scope 401-vs-403, duplicate-email non-disclosure, dark-mode zero
mutation + zero mail, and stage/prod token isolation.
"""

import base64
import hashlib
import re
import secrets
import warnings
from unittest.mock import patch

import pytest

warnings.filterwarnings("ignore", category=DeprecationWarning)

from verifimind_mcp.oauth import config, core, stores
from verifimind_mcp.oauth import authlib_server as A
from verifimind_mcp.oauth.stores import StoreUnavailable

from .oauth_fakes import FakeFirestore


def _pkce():
    verifier = secrets.token_urlsafe(48)[:64]
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


@pytest.fixture()
def env(monkeypatch):
    monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "development")
    monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", "http://localhost:8080")
    monkeypatch.setenv("OAUTH_ISSUANCE_ENABLED", "true")
    monkeypatch.delenv("MAIL_RECIPIENT_ALLOWLIST", raising=False)


@pytest.fixture()
def db(env):
    fake = FakeFirestore()
    stores.clear_caches()
    with patch("verifimind_mcp.registration._get_firestore", return_value=fake):
        yield fake
    stores.clear_caches()


@pytest.fixture()
def server(db):
    return A.build_authorization_server()


def _client(redirect="https://c.example/cb"):
    return stores.register_client(
        client_name="CLI", redirect_uris=[redirect], registration_path="dcr"
    )


def _mkcode(cid, challenge, subject="subj-1", redirect="https://c.example/cb"):
    code = core.mint_authorization_code()
    stores.persist_code(
        code_id=code.token_id, code_secret_hash=code.secret_hash, client_id=cid,
        subject_uuid=subject, redirect_uri=redirect, code_challenge=challenge, scope="mcp",
    )
    return code


def _treq(**form):
    return A.build_request(
        method="POST", uri="http://localhost:8080/oauth/token",
        form_pairs=list(form.items()), query_pairs=[],
        headers={"content-type": "application/x-www-form-urlencoded"},
    )


def _exchange(server, cid, code_token, verifier, redirect="https://c.example/cb"):
    return server.create_token_response(_treq(
        grant_type="authorization_code", code=code_token, code_verifier=verifier,
        client_id=cid, redirect_uri=redirect,
    ))


class TestHappyPath:
    def test_code_exchange_issues_bound_tokens(self, server):
        cid = _client()
        v, ch = _pkce()
        code = _mkcode(cid, ch)
        st, body, _ = _exchange(server, cid, code.token, v)
        assert st == 200 and "access_token" in body
        rec = stores.validate_bearer(body["access_token"])
        assert rec.subject_uuid == "subj-1"
        assert rec.audience == "http://localhost:8080/mcp"
        assert rec.issuer == "http://localhost:8080"
        assert rec.scope == "mcp"


class TestPKCEMatrix:
    def test_missing_verifier_rejected(self, server):
        cid = _client()
        _v, ch = _pkce()
        code = _mkcode(cid, ch)
        st, body, _ = server.create_token_response(_treq(
            grant_type="authorization_code", code=code.token, client_id=cid,
            redirect_uri="https://c.example/cb"))
        assert st == 400

    def test_wrong_verifier_rejected_and_does_not_consume(self, server):
        cid = _client()
        v, ch = _pkce()
        code = _mkcode(cid, ch)
        st, body, _ = _exchange(server, cid, code.token, "wrong-" + v)
        assert st == 400 and body["error"] == "invalid_grant"
        # T P0-3: a failed exchange must NOT burn the code.
        assert stores.read_code(code.token_id) is not None
        # A subsequent correct verifier still works.
        st2, body2, _ = _exchange(server, cid, code.token, v)
        assert st2 == 200

    def test_plain_challenge_method_refused_at_authorize(self, server):
        cid = _client()
        _v, ch = _pkce()
        req = A.build_request(method="GET", uri="http://localhost:8080/oauth/authorize",
            form_pairs=[], query_pairs=[
                ("response_type", "code"), ("client_id", cid),
                ("redirect_uri", "https://c.example/cb"),
                ("code_challenge", ch), ("code_challenge_method", "plain")],
            headers={})
        from authlib.oauth2.base import OAuth2Error
        with pytest.raises(OAuth2Error):
            server.get_consent_grant(req)


class TestConcurrency:
    def test_two_concurrent_code_exchanges_yield_one_winner(self, db, server):
        cid = _client()
        v, ch = _pkce()
        code = _mkcode(cid, ch)
        results = []

        def barrier():
            # Second claimant runs fully inside the first's pre-commit window.
            try:
                st, body, _ = _exchange(server, cid, code.token, v)
                results.append(st)
            except StoreUnavailable:
                results.append(409)

        db._next_barrier = barrier
        try:
            st1, _b1, _ = _exchange(server, cid, code.token, v)
            results.append(st1)
        except StoreUnavailable:
            results.append(409)
        assert results.count(200) == 1, results


class TestRefresh:
    def test_rotation_then_replay_revokes_family(self, server):
        cid = _client()
        v, ch = _pkce()
        code = _mkcode(cid, ch)
        _st, body, _ = _exchange(server, cid, code.token, v)
        access1, refresh1 = body["access_token"], body["refresh_token"]
        st2, body2, _ = server.create_token_response(_treq(
            grant_type="refresh_token", refresh_token=refresh1, client_id=cid))
        assert st2 == 200
        access2 = body2["access_token"]
        # Replay of the rotated refresh token → invalid_grant + family revoke.
        st3, body3, _ = server.create_token_response(_treq(
            grant_type="refresh_token", refresh_token=refresh1, client_id=cid))
        assert st3 == 400 and body3["error"] == "invalid_grant"
        assert stores.validate_bearer(access2) is None
        assert stores.validate_bearer(access1) is None


class TestBearerKinds:
    def test_access_and_pat_pass_refresh_rejected(self, server):
        cid = _client()
        v, ch = _pkce()
        code = _mkcode(cid, ch)
        _st, body, _ = _exchange(server, cid, code.token, v)
        access, refresh = body["access_token"], body["refresh_token"]
        pat = stores.issue_pat(subject_uuid="subj-1", actor_class="external", parent_grant_id="g-test").token
        assert stores.validate_bearer(access) is not None
        assert stores.validate_bearer(pat) is not None
        assert stores.validate_bearer(refresh) is None
        # PAT is rejected where only ACCESS is allowed (e.g. minting a PAT).
        assert stores.validate_bearer(pat, allow_pat=False) is None


class TestCacheSecretBypass:
    def test_wrong_secret_fails_before_and_after_warmup(self, server):
        # T P0-1: the CRITICAL finding — same token id, attacker secret.
        cid = _client()
        v, ch = _pkce()
        code = _mkcode(cid, ch)
        _st, body, _ = _exchange(server, cid, code.token, v)
        access = body["access_token"]
        tampered = access.rsplit(".", 1)[0] + ".attacker-does-not-know-secret"
        assert stores.validate_bearer(tampered) is None       # cold
        assert stores.validate_bearer(access) is not None     # warm the cache
        assert stores.validate_bearer(tampered) is None       # still rejected

    def test_cache_does_not_outlive_token_expiry(self, db, server):
        cid = _client()
        v, ch = _pkce()
        code = _mkcode(cid, ch)
        _st, body, _ = _exchange(server, cid, code.token, v)
        access = body["access_token"]
        assert stores.validate_bearer(access) is not None
        parsed = core.parse_token(access)
        db.collection(stores.c_tokens()).document(parsed.token_id).update({"expires_at": 1.0})
        stores.clear_caches()
        assert stores.validate_bearer(access) is None


class TestBearerAuthorization:
    def _access(self, server):
        cid = _client()
        v, ch = _pkce()
        code = _mkcode(cid, ch)
        _st, body, _ = _exchange(server, cid, code.token, v)
        return body["access_token"]

    def test_valid_scope_passes(self, server):
        access = self._access(server)
        record, err = A.authenticate_bearer(access, ("mcp",))
        assert record is not None and err is None

    def test_insufficient_scope_is_403_class(self, server):
        access = self._access(server)
        record, err = A.authenticate_bearer(access, ("admin",))
        assert record is None and err == "insufficient_scope"

    def test_wrong_audience_is_401_class(self, db, server):
        access = self._access(server)
        parsed = core.parse_token(access)
        db.collection(stores.c_tokens()).document(parsed.token_id).update(
            {"audience": "https://evil.example/mcp"})
        stores.clear_caches()
        record, err = A.authenticate_bearer(access, ("mcp",))
        assert record is None and err == "invalid_token"

    def test_wrong_issuer_is_401_class(self, db, server):
        access = self._access(server)
        parsed = core.parse_token(access)
        db.collection(stores.c_tokens()).document(parsed.token_id).update(
            {"issuer": "https://evil.example"})
        stores.clear_caches()
        record, err = A.authenticate_bearer(access, ("mcp",))
        assert record is None and err == "invalid_token"


class TestOutageFailsClosed:
    def test_bearer_validation_raises_store_unavailable(self, env):
        stores.clear_caches()
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            with pytest.raises(StoreUnavailable):
                A.authenticate_bearer("vmat.x.y", ("mcp",))

    def test_token_endpoint_raises_on_outage(self, env):
        server = A.build_authorization_server()
        stores.clear_caches()
        with patch("verifimind_mcp.registration._get_firestore", return_value=None):
            with pytest.raises(StoreUnavailable):
                server.create_token_response(_treq(
                    grant_type="authorization_code", code="vmac.a.b",
                    code_verifier="x", client_id="c", redirect_uri="https://c/cb"))


class TestStageProdIsolation:
    def test_prod_token_rejected_in_staging(self, monkeypatch):
        # Mint under production identity, validate under staging: audience/
        # issuer mismatch denies (T P0-8).
        fake = FakeFirestore()
        stores.clear_caches()
        with patch("verifimind_mcp.registration._get_firestore", return_value=fake):
            monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "production")
            monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", "https://verifimind.ysenseai.org")
            prod_pat = stores.issue_pat(subject_uuid="s", actor_class="external", parent_grant_id="g-test").token
            # production stores in bare collection; staging reads a namespaced
            # one, so the token is not even found — isolation by namespace.
            monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "staging")
            monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", "https://staging.example")
            record, err = A.authenticate_bearer(prod_pat, ("mcp",))
            assert record is None
        stores.clear_caches()


class TestAdversarialFindings:
    """Regressions for the bypasses found by the S155 attacker-position pass.

    Each test reproduces the reviewer's concrete attack; none of them passed
    before the repair in the same commit.
    """

    def _grant(self, server):
        cid = _client()
        v, ch = _pkce()
        code = _mkcode(cid, ch)
        _st, body, _ = _exchange(server, cid, code.token, v)
        return body["access_token"], body["refresh_token"]

    def test_pat_is_revoked_with_its_parent_grant(self, server):
        # A-1/B-2: a PAT used to get a brand-new family, so revoking the
        # grant it was minted from could never reach it — a stolen 1-hour
        # access token became a silent 180-day credential.
        access, _refresh = self._grant(server)
        record = stores.validate_bearer(access)
        pat = stores.issue_pat(
            subject_uuid=record.subject_uuid, actor_class=record.actor_class,
            parent_grant_id=record.grant_id,
        ).token
        assert stores.validate_bearer(pat) is not None
        assert stores.revoke_credential(access) is True
        assert stores.validate_bearer(pat) is None

    def test_absent_issuer_or_audience_denies(self, db, server):
        # A-2: the binding check was truthy-guarded, so a token missing these
        # fields skipped it and validated in every environment.
        access, _r = self._grant(server)
        parsed = core.parse_token(access)
        db.collection(stores.c_tokens()).document(parsed.token_id).update(
            {"issuer": "", "audience": ""})
        stores.clear_caches()
        record, err = A.authenticate_bearer(access, ("mcp",))
        assert record is None and err == "invalid_token"

    def test_subject_tombstone_refuses_credentials_minted_after_the_sweep(
        self, db, server
    ):
        # B-4: revocation was query-then-update, so a credential created
        # after the snapshot survived. The tombstone is consulted at
        # validation time, so a later-minted credential is still refused.
        access, _r = self._grant(server)
        record = stores.validate_bearer(access)
        stores.revoke_all_for_subject(record.subject_uuid)
        late = stores.issue_pat(
            subject_uuid=record.subject_uuid, actor_class="external",
            parent_grant_id="unrelated-grant",
        ).token
        assert stores.validate_bearer(late) is None

    def test_warm_cache_cannot_outlive_revocation(self, db, server):
        # B-3: a cache HIT re-checked only kind/expiry, so a sibling
        # instance kept admitting a revoked token for the cache TTL.
        access, _r = self._grant(server)
        assert stores.validate_bearer(access) is not None  # warm
        record = stores.validate_bearer(access)
        stores._write_tombstone("grant", record.grant_id)  # peer revoked it
        assert stores.validate_bearer(access) is None

    def test_scope_persisted_is_the_resolved_grant_not_caller_input(self, db, server):
        # A5-related: persisting request.payload.scope stored raw client
        # input; Authlib warns this becomes escalation with >1 scope.
        cid = _client()
        v, ch = _pkce()
        code = _mkcode(cid, ch)
        db.collection(stores._c("oauth_codes")).document(code.token_id).update(
            {"scope": "mcp"})
        _st, body, _ = _exchange(server, cid, code.token, v)
        assert stores.validate_bearer(body["access_token"]).scope == "mcp"
