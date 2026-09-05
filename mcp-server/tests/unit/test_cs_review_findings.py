"""Regressions for the four CS independent-review BOUNDED-HOLD findings.

Each test reproduces the reviewer's exact attack against SHA 2f44433 and
asserts the repair. Mapped 1:1 to the CS report so re-review can confirm.
"""

import warnings
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

warnings.filterwarnings("ignore", category=DeprecationWarning)

from .oauth_fakes import FakeFirestore


# ── Finding 1: dark issuance must block the legacy registration writes ───────

class TestFinding1DarkRegistration:
    def _req(self):
        async def _json():
            return {"consent": True, "email": "x@example.com",
                    "tc_accepted": True, "privacy_acknowledged": True}
        return SimpleNamespace(json=_json, headers={})

    @pytest.mark.asyncio
    async def test_lightweight_register_blocked_and_writes_nothing_when_dark(
        self, monkeypatch
    ):
        import http_server
        monkeypatch.delenv("OAUTH_ISSUANCE_ENABLED", raising=False)
        register = AsyncMock()
        with patch("http_server.register_user", new=register):
            resp = await http_server.register_handler(self._req())
        assert resp.status_code == 503
        register.assert_not_awaited()  # zero Firestore write

    @pytest.mark.asyncio
    async def test_ea_register_blocked_and_writes_nothing_when_dark(
        self, monkeypatch
    ):
        import http_server
        monkeypatch.delenv("OAUTH_ISSUANCE_ENABLED", raising=False)
        register = AsyncMock()
        with patch("http_server.register_early_adopter", new=register):
            resp = await http_server.ea_register_handler(self._req())
        assert resp.status_code == 503
        register.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_register_runs_when_issuance_enabled(self, monkeypatch):
        import http_server
        monkeypatch.setenv("OAUTH_ISSUANCE_ENABLED", "true")
        register = AsyncMock(return_value=MagicMock(
            model_dump=lambda: {"uuid": ""}, persisted=True))
        with patch("http_server.register_user", new=register):
            await http_server.register_handler(self._req())
        register.assert_awaited()  # not dark → proceeds


# ── Finding 2: anonymous (email-absent) registration must return its UUID ────

class TestFinding2AnonymousNotOrphaned:
    @pytest.mark.asyncio
    async def test_anonymous_registration_returns_uuid(self):
        from verifimind_mcp.registration import UserRegistrationRequest, register_user
        db = MagicMock()
        db.collection.return_value.where.return_value.limit.return_value.get.return_value = []
        with patch("verifimind_mcp.registration._get_firestore", return_value=db):
            result = await register_user(UserRegistrationRequest(consent=True))
        # No email → no oracle/hijack surface → the UUID is the user's only
        # handle and MUST be returned (else the account is orphaned at birth).
        assert result.uuid and result.uuid != ""
        assert result.opt_out_url.endswith(result.uuid)

    @pytest.mark.asyncio
    async def test_email_registration_still_withholds_uuid(self):
        from verifimind_mcp.registration import UserRegistrationRequest, register_user
        db = MagicMock()
        db.collection.return_value.where.return_value.limit.return_value.get.return_value = []
        with patch("verifimind_mcp.registration._get_firestore", return_value=db):
            result = await register_user(
                UserRegistrationRequest(consent=True, email="new@example.com"))
        assert result.uuid == ""  # email present → oracle-safe withhold


# ── Finding 3: the ceremony must not adopt attacker-injected profile data ────

class TestFinding3NoInjectedDataAdoption:
    @pytest.mark.asyncio
    async def test_unverified_record_fields_are_wiped_on_verification(self, monkeypatch):
        monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "production")
        monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", "https://verifimind.ysenseai.org")
        from verifimind_mcp.oauth.endpoints import _resolve_or_create_subject
        fake = FakeFirestore()
        # Attacker planted the victim's email with an injected display_name.
        fake.collection("ea_registrations").document("victim-uuid").set({
            "uuid": "victim-uuid", "email": "victim@example.com",
            "status": "active", "email_verified": False,
            "display_name": "ATTACKER-INJECTED", "registration_feedback": "profane",
            "name": "attacker", "feedback_type": "general",
        })
        with patch("verifimind_mcp.registration._get_firestore", return_value=fake):
            uuid = _resolve_or_create_subject("victim@example.com")
        assert uuid == "victim-uuid"  # UUID adopted for continuity
        record = fake.data["ea_registrations"]["victim-uuid"]
        assert record["email_verified"] is True
        # Every caller-injectable field is wiped — no attacker data survives.
        assert record["display_name"] is None
        assert record["name"] is None
        assert record["registration_feedback"] is None
        assert record["feedback_type"] is None


# ── Finding 4: the in-band gate denial must be environment-bound ─────────────

class TestFinding4EnvBoundDenial:
    def test_staging_denial_never_points_at_production(self, monkeypatch):
        monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "staging")
        monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", "https://staging.example")
        from verifimind_mcp.middleware.registration_gate import (
            DENIAL_AUTHENTICATION_REQUIRED, _denial_payload,
        )
        payload = _denial_payload("run_full_trinity", DENIAL_AUTHENTICATION_REQUIRED)
        blob = str(payload)
        assert "verifimind.ysenseai.org" not in blob  # no production leak
        assert payload["resource_metadata"] == (
            "https://staging.example/.well-known/oauth-protected-resource")
        assert payload["register_url"] == "https://staging.example/register"

    def test_production_denial_points_at_production(self, monkeypatch):
        monkeypatch.setenv("VERIFIMIND_ENVIRONMENT", "production")
        monkeypatch.setenv("VERIFIMIND_PUBLIC_ORIGIN", "https://verifimind.ysenseai.org")
        from verifimind_mcp.middleware.registration_gate import (
            DENIAL_AUTHENTICATION_REQUIRED, _denial_payload,
        )
        payload = _denial_payload("run_full_trinity", DENIAL_AUTHENTICATION_REQUIRED)
        assert payload["resource_metadata"] == (
            "https://verifimind.ysenseai.org/.well-known/oauth-protected-resource")
