"""Registration bridge repair contract (RNA S152).

The lightweight POST /register lane wrote to ``ea_registrations`` while every
reader consulted only ``early_adopters`` — a lightweight registrant was
invisible to /whoami, tier resolution, and any authorization check.
``resolve_registration`` closes the bridge on the READER side (no write
migration: EA slot caps and pioneer-tier mapping are untouched), is
status-aware (revocation revokes), and fails closed on outage.
"""

from unittest.mock import MagicMock, patch

import pytest

from verifimind_mcp import registration_lookup
from verifimind_mcp.registration_lookup import (
    NOT_REGISTERED,
    REGISTERED,
    UNAVAILABLE,
    resolve_registration,
)

UUID_A = "018f6b2a-aaaa-7abc-8def-0123456789ab"


@pytest.fixture(autouse=True)
def _fresh_cache():
    registration_lookup._clear_cache()
    yield
    registration_lookup._clear_cache()


def _doc(exists, data=None):
    doc = MagicMock()
    doc.exists = exists
    doc.to_dict.return_value = data or {}
    return doc


def _db(by_collection):
    """Fake Firestore routing document lookups by collection name."""
    db = MagicMock()

    def collection(name):
        coll = MagicMock()
        coll.document.return_value.get.return_value = by_collection.get(
            name, _doc(False)
        )
        return coll

    db.collection.side_effect = collection
    return db


def _patched(db):
    return patch(
        "verifimind_mcp.registration._get_firestore", return_value=db
    )


class TestResolveRegistration:
    def test_active_early_adopter_is_registered(self):
        db = _db({"early_adopters": _doc(True, {"status": "active", "tier": "pilot"})})
        with _patched(db):
            state = resolve_registration(UUID_A)
        assert state.state == REGISTERED
        assert state.source == "early_adopters"
        assert state.tier == "pilot"

    def test_active_lightweight_registration_is_registered(self):
        # THE bridge: ea_registrations identities now verify.
        db = _db({"ea_registrations": _doc(True, {"status": "active", "tier": "ea"})})
        with _patched(db):
            state = resolve_registration(UUID_A)
        assert state.state == REGISTERED
        assert state.source == "ea_registrations"

    def test_deletion_requested_account_is_revoked(self):
        # doc.exists alone must never authorize: opt-out actually revokes.
        db = _db({
            "early_adopters": _doc(True, {"status": "deletion_requested"}),
        })
        with _patched(db):
            state = resolve_registration(UUID_A)
        assert state.state == NOT_REGISTERED

    def test_unknown_uuid_is_not_registered(self):
        with _patched(_db({})):
            assert resolve_registration(UUID_A).state == NOT_REGISTERED

    def test_firestore_none_is_unavailable_not_a_pass(self):
        with _patched(None):
            assert resolve_registration(UUID_A).state == UNAVAILABLE

    def test_lookup_exception_is_unavailable_not_a_pass(self):
        db = MagicMock()
        db.collection.side_effect = RuntimeError("backend down")
        with _patched(db):
            assert resolve_registration(UUID_A).state == UNAVAILABLE

    def test_positive_results_are_cached_across_backend_blips(self):
        db = _db({"early_adopters": _doc(True, {"status": "active"})})
        with _patched(db):
            assert resolve_registration(UUID_A).state == REGISTERED
        with _patched(None):  # backend gone — cache rides through
            assert resolve_registration(UUID_A).state == REGISTERED

    def test_negative_results_are_never_cached(self):
        with _patched(_db({})):
            assert resolve_registration(UUID_A).state == NOT_REGISTERED
        db = _db({"ea_registrations": _doc(True, {"status": "active"})})
        with _patched(db):
            # A registration made right after a failed check is visible
            # immediately: NOT_REGISTERED was not cached.
            assert resolve_registration(UUID_A).state == REGISTERED

    def test_unavailable_results_are_never_cached(self):
        with _patched(None):
            assert resolve_registration(UUID_A).state == UNAVAILABLE
        db = _db({"early_adopters": _doc(True, {"status": "active"})})
        with _patched(db):
            assert resolve_registration(UUID_A).state == REGISTERED


class TestLightweightRegisterHonesty:
    @pytest.mark.asyncio
    async def test_db_none_reports_not_saved(self):
        from verifimind_mcp.registration import (
            UserRegistrationRequest,
            register_user,
        )
        with _patched(None):
            response = await register_user(
                UserRegistrationRequest(consent=True)
            )
        assert response.persisted is False
        assert "NOT saved" in response.message
        assert "successful" not in response.message.lower()

    @pytest.mark.asyncio
    async def test_persisted_registration_reports_success(self):
        from verifimind_mcp.registration import (
            UserRegistrationRequest,
            register_user,
        )
        db = MagicMock()
        db.collection.return_value.where.return_value.limit.return_value.get.return_value = []
        with _patched(db):
            response = await register_user(
                UserRegistrationRequest(consent=True)
            )
        assert response.persisted is True
        assert db.collection.return_value.document.return_value.set.called


class TestHttpSurfaces:
    """First HTTP-level coverage for POST /register and /whoami."""

    @pytest.fixture
    def client(self, monkeypatch):
        import http_server
        from starlette.testclient import TestClient
        from verifimind_mcp.middleware import rate_limiter
        # Fresh rate-limit store per test: /register POSTs are deliberately
        # rate-limited now (minting bound), and batch accumulation from
        # other suites must not manufacture a 429 here.
        monkeypatch.setattr(
            rate_limiter, "_rate_limit_store", rate_limiter.RateLimitStore()
        )
        with TestClient(http_server.app) as tc:
            yield tc

    def test_post_register_completes_end_to_end(self, client):
        db = MagicMock()
        db.collection.return_value.where.return_value.limit.return_value.get.return_value = []
        with _patched(db):
            response = client.post("/register", json={"consent": True})
        assert response.status_code == 200
        body = response.json()
        assert body["persisted"] is True
        # The cohort record is written...
        db.collection.return_value.document.return_value.set.assert_called_once()
        # ...but no subject identifier is handed out on an unverified path:
        # the identifier comes only from the verified Connect ceremony
        # (T P0-2 + adversarial B-3/B-6 pre-registration hijack).
        assert body["uuid"] == ""
        assert body["opt_out_url"] == ""
        assert "Connect flow" in body["message"]

    def test_post_register_without_consent_is_422(self, client):
        response = client.post("/register", json={"consent": False})
        assert response.status_code == 422

    def test_post_register_during_outage_says_not_saved(self, client):
        with _patched(None):
            response = client.post("/register", json={"consent": True})
        assert response.status_code == 200
        body = response.json()
        assert body["persisted"] is False
        assert "NOT saved" in body["message"]

    def test_whoami_sees_lightweight_registration(self, client):
        db = _db({"ea_registrations": _doc(True, {"status": "active", "tier": "ea"})})
        registration_lookup._clear_cache()
        with _patched(db):
            response = client.get("/whoami", params={"uuid": UUID_A})
        body = response.json()
        assert body["status"] == "active"
        assert body["registration_source"] == "ea_registrations"

    def test_whoami_reports_outage_honestly(self, client):
        registration_lookup._clear_cache()
        with _patched(None):
            response = client.get("/whoami", params={"uuid": UUID_A})
        assert response.json()["status"] == "status_check_unavailable"

    def test_whoami_unregistered_shape_unchanged(self, client):
        registration_lookup._clear_cache()
        with _patched(_db({})):
            response = client.get("/whoami", params={"uuid": UUID_A})
        body = response.json()
        assert body["status"] == "unregistered"
        assert body["register_url"].endswith("/register")


class TestMintingRateExemption:
    def test_identity_minting_posts_are_rate_limited(self):
        from verifimind_mcp.middleware.rate_limiter import (
            _is_rate_limit_exempt,
        )
        # Page views stay exempt; the minting POSTs do not.
        assert _is_rate_limit_exempt("/register", "GET") is True
        assert _is_rate_limit_exempt("/register", "POST") is False
        assert _is_rate_limit_exempt("/early-adopters/register", "POST") is False
        assert _is_rate_limit_exempt("/whoami", "GET") is True
        assert _is_rate_limit_exempt("/mcp/", "POST") is False
