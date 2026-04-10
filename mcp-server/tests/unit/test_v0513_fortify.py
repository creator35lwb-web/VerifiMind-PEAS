"""
v0.5.13 "Fortify" — Unit Tests
================================

Tests for:
1. POST /register lightweight endpoint (UserRegistrationRequest / register_user)
2. Phase 2 tier-gate Polar adapter integration (async, fallback)
3. sanitize_handoff_content activation (secret stripping)
4. Firestore handoff store (dual-backend behaviour — Firestore unavailable fallback)
"""

import pytest


# ---------------------------------------------------------------------------
# 1. Lightweight /register endpoint (10 tests)
# ---------------------------------------------------------------------------

class TestUserRegistrationRequest:
    """Pydantic model validation for the lightweight /register input."""

    def test_consent_only_is_valid(self):
        from verifimind_mcp.registration import UserRegistrationRequest
        req = UserRegistrationRequest(consent=True)
        assert req.consent is True
        assert req.email is None
        assert req.display_name is None

    def test_full_payload_valid(self):
        from verifimind_mcp.registration import UserRegistrationRequest
        req = UserRegistrationRequest(
            email="test@example.com",
            display_name="Alice",
            consent=True,
        )
        assert str(req.email) == "test@example.com"
        assert req.display_name == "Alice"

    def test_consent_false_raises(self):
        from verifimind_mcp.registration import UserRegistrationRequest
        import pydantic
        with pytest.raises((ValueError, pydantic.ValidationError)):
            UserRegistrationRequest(consent=False)

    def test_consent_missing_raises(self):
        from verifimind_mcp.registration import UserRegistrationRequest
        import pydantic
        with pytest.raises((TypeError, pydantic.ValidationError)):
            UserRegistrationRequest()

    def test_invalid_email_raises(self):
        from verifimind_mcp.registration import UserRegistrationRequest
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            UserRegistrationRequest(email="not-an-email", consent=True)

    def test_display_name_max_length(self):
        from verifimind_mcp.registration import UserRegistrationRequest
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            UserRegistrationRequest(display_name="x" * 101, consent=True)

    def test_display_name_100_chars_ok(self):
        from verifimind_mcp.registration import UserRegistrationRequest
        req = UserRegistrationRequest(display_name="x" * 100, consent=True)
        assert len(req.display_name) == 100


@pytest.mark.asyncio
class TestRegisterUser:
    """register_user() function — Firestore unavailable (unit test safe)."""

    async def test_returns_uuid_consent_only(self):
        from verifimind_mcp.registration import UserRegistrationRequest, register_user
        req = UserRegistrationRequest(consent=True)
        result = await register_user(req)
        assert result.uuid
        assert len(result.uuid) > 10
        assert result.tier == "ea"

    async def test_returns_pioneer_checkout_url(self):
        from verifimind_mcp.registration import UserRegistrationRequest, register_user
        req = UserRegistrationRequest(consent=True)
        result = await register_user(req)
        assert "polar.sh" in result.pioneer_checkout or "polar" in result.pioneer_checkout.lower()
        assert result.uuid in result.pioneer_checkout

    async def test_uuid_in_opt_out_url(self):
        from verifimind_mcp.registration import UserRegistrationRequest, register_user
        req = UserRegistrationRequest(consent=True)
        result = await register_user(req)
        assert result.uuid in result.opt_out_url

    async def test_expires_at_is_future(self):
        from verifimind_mcp.registration import UserRegistrationRequest, register_user
        from datetime import datetime, timezone
        req = UserRegistrationRequest(consent=True)
        result = await register_user(req)
        expires = datetime.fromisoformat(result.expires_at.replace("Z", "+00:00"))
        assert expires > datetime.now(timezone.utc)

    async def test_policy_versions_returned(self):
        from verifimind_mcp.registration import UserRegistrationRequest, register_user
        req = UserRegistrationRequest(consent=True)
        result = await register_user(req)
        assert result.privacy_version == "2.0"
        assert result.tc_version == "2.0"

    async def test_different_calls_return_different_uuids(self):
        from verifimind_mcp.registration import UserRegistrationRequest, register_user
        r1 = await register_user(UserRegistrationRequest(consent=True))
        r2 = await register_user(UserRegistrationRequest(consent=True))
        assert r1.uuid != r2.uuid


# ---------------------------------------------------------------------------
# 2. Phase 2 Tier-Gate — Polar adapter async (5 tests)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestTierGatePhase2:
    """Phase 2 tier-gate: Polar adapter path + env-var fallback."""

    async def test_no_polar_token_falls_back_to_env_var(self, monkeypatch):
        monkeypatch.delenv("POLAR_ACCESS_TOKEN", raising=False)
        monkeypatch.setenv("PIONEER_ACCESS_KEYS", "my-test-key")
        import importlib
        import verifimind_mcp.middleware.tier_gate as tg
        import verifimind_mcp.middleware.polar_adapter as pa
        importlib.reload(pa)
        importlib.reload(tg)
        allowed, tier = await tg.check_tier("my-test-key")
        assert allowed is True
        assert tier == "pioneer"

    async def test_no_polar_token_invalid_key_blocked(self, monkeypatch):
        monkeypatch.delenv("POLAR_ACCESS_TOKEN", raising=False)
        monkeypatch.setenv("PIONEER_ACCESS_KEYS", "real-key")
        import importlib
        import verifimind_mcp.middleware.tier_gate as tg
        import verifimind_mcp.middleware.polar_adapter as pa
        importlib.reload(pa)
        importlib.reload(tg)
        allowed, tier = await tg.check_tier("wrong-key")
        assert allowed is False
        assert tier == "scholar"

    async def test_none_key_always_scholar(self, monkeypatch):
        from verifimind_mcp.middleware.tier_gate import check_tier
        allowed, tier = await check_tier(None)
        assert allowed is False
        assert tier == "scholar"

    async def test_empty_key_always_scholar(self, monkeypatch):
        from verifimind_mcp.middleware.tier_gate import check_tier
        allowed, tier = await check_tier("")
        assert allowed is False
        assert tier == "scholar"

    async def test_polar_adapter_error_falls_back(self, monkeypatch):
        """If Polar API raises an exception, fall back to env-var check."""
        from unittest.mock import AsyncMock, MagicMock
        import verifimind_mcp.middleware.polar_adapter as pa
        import verifimind_mcp.middleware.tier_gate as tg

        # Patch the adapter singleton at polar_adapter module level
        mock_adapter = MagicMock()
        mock_adapter.check_pioneer_access = AsyncMock(side_effect=Exception("Polar down"))
        monkeypatch.setattr(pa, "_adapter", mock_adapter)
        monkeypatch.setattr(tg, "_PIONEER_KEYS", frozenset(["fallback-key"]))

        allowed, tier = await tg.check_tier("fallback-key")
        # Polar raised → fell back to env var → key in frozenset → granted
        assert allowed is True


# ---------------------------------------------------------------------------
# 3. sanitize_handoff_content — ACTIVE in v0.5.13 (6 tests)
# ---------------------------------------------------------------------------

class TestSanitizeHandoffContent:
    """sanitize_handoff_content() is now ACTIVE — strips real secrets."""

    def _sanitize(self, content: str) -> str:
        from verifimind_mcp.middleware.tier_gate import sanitize_handoff_content
        return sanitize_handoff_content(content)

    def test_openai_key_redacted(self):
        result = self._sanitize("key: sk-abc123def456ghi789jkl012345678901234567890")
        assert "[REDACTED]" in result
        assert "sk-abc123" not in result

    def test_anthropic_key_redacted(self):
        result = self._sanitize("anthropic: sk-ant-api03-xyz789abc123longkeyvalue1234")
        assert "[REDACTED]" in result

    def test_google_api_key_redacted(self):
        result = self._sanitize("AIzaSyD-longGoogleKeyStringWith35chars1234")
        assert "[REDACTED]" in result

    def test_github_pat_redacted(self):
        # GitHub PAT pattern: ghp_ followed by exactly 36 alphanumeric chars
        result = self._sanitize("token: ghp_AbCdEfGhIjKlMnOpQrStUvWxYz1234567890ab")
        assert "[REDACTED]" in result

    def test_clean_content_unchanged(self):
        content = "# Handoff\n\nCompleted: feature X\nPending: review Y\nNo secrets here."
        result = self._sanitize(content)
        assert result == content

    def test_multiple_secrets_all_redacted(self):
        content = "key1=sk-abc123longkeyvalue1234567890xyz and key2=ghp_AbCdEfGhIjKlMnOpQrStUvWxYz1234567890ab"
        result = self._sanitize(content)
        assert result.count("[REDACTED]") >= 2


# ---------------------------------------------------------------------------
# 4. Firestore Handoff Store — dual-backend (4 tests)
# ---------------------------------------------------------------------------

class TestHandoffStoreDualBackend:
    """HandoffStore: Firestore write attempt + in-memory fallback."""

    def test_add_succeeds_without_firestore(self):
        """In-memory fallback works when Firestore is unavailable."""
        from verifimind_mcp.coordination.handoff_store import HandoffStore, build_handoff_record
        store = HandoffStore()
        record = build_handoff_record("RNA", "test", ["done"], [], [], [], [], None)
        store.add("test-key", record)
        assert store.count("test-key") == 1

    def test_add_persists_all_fields(self):
        from verifimind_mcp.coordination.handoff_store import HandoffStore, build_handoff_record
        store = HandoffStore()
        record = build_handoff_record("XV", "research", ["item1"], ["dec1"], ["art.py"], ["todo1"], ["blocker1"], "T")
        store.add("key", record)
        stored = store.get("key")[0]
        assert stored["agent_id"] == "XV"
        assert "item1" in stored["completed"]
        assert "blocker1" in stored["blockers"]

    def test_firestore_failure_does_not_raise(self, monkeypatch):
        """If Firestore write fails, in-memory store still works."""
        from verifimind_mcp.coordination import handoff_store as hs
        # Force _get_firestore_client to raise
        monkeypatch.setattr(hs, "_get_firestore_client", lambda: (_ for _ in ()).throw(Exception("no firestore")))
        store = hs.HandoffStore()
        record = hs.build_handoff_record("RNA", "test", [], [], [], [], [], None)
        store.add("k", record)  # must not raise
        assert store.count("k") == 1

    def test_collection_name_constant(self):
        from verifimind_mcp.coordination.handoff_store import COLLECTION_HANDOFFS
        assert COLLECTION_HANDOFFS == "coordination_handoffs"
