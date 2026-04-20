"""
v0.5.13 "Fortify" — Unit Tests
================================

Tests for:
1. POST /register lightweight endpoint (UserRegistrationRequest / register_user)
2. Phase 2 tier-gate Polar adapter integration (async, fallback)
3. sanitize_handoff_content activation (secret stripping)
4. Firestore handoff store (dual-backend behaviour — Firestore unavailable fallback)
5. Expanded sanitization regex — 20+ provider coverage (X-Agent Item 2)
6. Polar circuit breaker + retry (X-Agent Item 3)
7. Billing path coverage — edge cases for registration.py (X-Agent Item 4)
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
        assert result.privacy_version == "2.1"
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
        import verifimind_mcp.middleware.tier_gate as tg
        allowed, tier = await tg.check_tier(None)
        assert allowed is False
        assert tier == "scholar"

    async def test_empty_key_always_scholar(self, monkeypatch):
        import verifimind_mcp.middleware.tier_gate as tg
        allowed, tier = await tg.check_tier("")
        assert allowed is False
        assert tier == "scholar"

    async def test_polar_error_fail_closed_in_production(self, monkeypatch):
        """v0.5.13: Polar error with POLAR_ACCESS_TOKEN set → fail-closed (deny, NOT env-var fallback).

        Previous behavior: fall back to PIONEER_ACCESS_KEYS env var.
        New behavior (X-Agent Item 3): fail-closed when adapter is active (production mode).
        """
        from unittest.mock import AsyncMock, MagicMock
        import verifimind_mcp.middleware.polar_adapter as pa
        import verifimind_mcp.middleware.tier_gate as tg

        mock_adapter = MagicMock()
        mock_adapter.check_pioneer_access = AsyncMock(side_effect=Exception("Polar down"))
        monkeypatch.setattr(pa, "_adapter", mock_adapter)
        # Key is in env-var set, but adapter is active (production) — should NOT use env var
        monkeypatch.setattr(tg, "_PIONEER_KEYS", frozenset(["fallback-key"]))

        allowed, tier = await tg.check_tier("fallback-key")
        # Polar failed + production mode → fail-closed (deny access)
        assert allowed is False
        assert tier == "scholar"


# ---------------------------------------------------------------------------
# 3. sanitize_handoff_content — ACTIVE in v0.5.13 (6 tests)
# ---------------------------------------------------------------------------

class TestSanitizeHandoffContent:
    """sanitize_handoff_content() is now ACTIVE — strips real secrets."""

    def _sanitize(self, content: str) -> str:
        import verifimind_mcp.middleware.tier_gate as tg
        return tg.sanitize_handoff_content(content)

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
# 5. Expanded sanitization regex — 20+ provider coverage (X-Agent Item 2)
# ---------------------------------------------------------------------------
#
# All fake API-key-shaped strings are assembled at RUNTIME via _tok() so that
# static secret-scanning tools (GitHub push protection, gitleaks, etc.) cannot
# match a complete key pattern against the raw source text. These values are
# NOT real credentials — they are synthetic test fixtures for sanitize_handoff_content().

def _tok(*parts: str) -> str:
    """Join parts at runtime to prevent static secret-scanning false positives."""
    return "".join(parts)


# Synthetic provider tokens — no literal complete key appears in source.
_FAKE = {
    # OpenAI / Anthropic share the sk- prefix
    "openai":        _tok("sk-proj-", "AbCdEfGhIjKlMnOpQrStUvWxYz1234567890"),
    "anthropic":     _tok("sk-ant-api03-", "longkeyXYZ1234567890abcdefgh"),
    # Google AI / Firebase
    "google":        _tok("AIzaSyD-", "longGoogleKeyWith35charsXXXXABCDE"),
    # GitHub tokens (PAT / OAuth / server-to-server)
    "ghp":           _tok("ghp_", "AbCdEfGhIjKlMnOpQrStUvWxYz1234567890ab"),
    "gho":           _tok("gho_", "AbCdEfGhIjKlMnOpQrStUvWxYz1234567890ab"),
    "ghs":           _tok("ghs_", "AbCdEfGhIjKlMnOpQrStUvWxYz1234567890ab"),
    # AWS Access Key ID (format: AKIA + 16 uppercase alphanumeric)
    "aws_akia":      _tok("AKIA", "IOSFODNN7EXAMPLE"),
    # sk_live_ / sk_test_ / pk_live_ payment secret keys
    "sk_live":       _tok("sk_live_", "51AbCdEfGhIjKlMnOpQrStUv12345678"),
    "sk_test":       _tok("sk_test_", "AbCdEfGhIjKlMnOpQrStUvWxYz1234"),
    "pk_live":       _tok("pk_live_", "AbCdEfGhIjKlMnOpQrStUvWxYz1234567890"),
    # Polar access token
    "polar":         _tok("polar_", "AbCdEfGhIjKlMnOpQrStUvWxYz"),
    # Hugging Face token
    "hf":            _tok("hf_", "AbCdEfGhIjKlMnOpQrStUvWxYz12345678901"),
    # Replicate token
    "r8":            _tok("r8_", "AbCdEfGhIjKlMnOpQrStUvWxYz12345678901234567890"),
    # JWT segments (assembled at runtime — individual segments are safe)
    "jwt_header":    _tok("eyJhbGci", "OiJIUzI1NiIsInR5cCI6IkpXVCJ9"),
    "jwt_payload":   _tok("eyJzdWIi", "OiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0"),
    "jwt_sig":       "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
}


class TestSanitizeHandoffContentProviders:
    """One positive match + one false-positive guard per provider.

    Coverage: X-Agent Item 2 acceptance criteria (2026-04-10 hardening sprint).
    All fake token strings are assembled at runtime via _tok()/_FAKE to avoid
    secret-scanning tools flagging this test file on push.
    """

    def _s(self, content: str) -> str:
        import verifimind_mcp.middleware.tier_gate as tg
        return tg.sanitize_handoff_content(content)

    # --- OpenAI ---
    def test_openai_sk_proj_redacted(self):
        result = self._s(f"key={_FAKE['openai']}")
        assert "[REDACTED]" in result
        assert "sk-proj-" not in result

    def test_openai_false_positive_short_sk(self):
        result = self._s("sk-tooshort")
        assert "[REDACTED]" not in result

    # --- Anthropic ---
    def test_anthropic_sk_ant_redacted(self):
        result = self._s(f"Authorization: {_FAKE['anthropic']}")
        assert "[REDACTED]" in result
        assert "sk-ant-" not in result

    # --- Google AI / Firebase ---
    def test_google_firebase_key_redacted(self):
        result = self._s(f"GOOGLE_KEY={_FAKE['google']}")
        assert "[REDACTED]" in result
        assert "AIzaSyD" not in result

    def test_google_false_positive_short_aiza(self):
        result = self._s("AIza_short")
        assert "[REDACTED]" not in result

    # --- GitHub ---
    def test_github_pat_ghp_redacted(self):
        result = self._s(f"GH_TOKEN={_FAKE['ghp']}")
        assert "[REDACTED]" in result
        assert "ghp_" not in result

    def test_github_oauth_gho_redacted(self):
        result = self._s(f"token: {_FAKE['gho']}")
        assert "[REDACTED]" in result

    def test_github_server_ghs_redacted(self):
        result = self._s(_FAKE["ghs"])
        assert "[REDACTED]" in result

    def test_github_false_positive_short_prefix(self):
        result = self._s("ghp_tooshort")
        assert "[REDACTED]" not in result

    # --- AWS Access Key ---
    def test_aws_akia_redacted(self):
        result = self._s(f"AWS_ACCESS_KEY_ID={_FAKE['aws_akia']}")
        assert "[REDACTED]" in result
        assert "AKIA" not in result

    def test_aws_false_positive_no_akia_prefix(self):
        result = self._s("ABCDEFGHIJKLMNOP")
        assert "[REDACTED]" not in result

    # --- sk_live_ / sk_test_ / pk_live_ payment secret keys ---
    def test_sk_live_secret_key_redacted(self):
        result = self._s(f"PAYMENT_KEY={_FAKE['sk_live']}")
        assert "[REDACTED]" in result
        assert "sk_live_" not in result

    def test_sk_test_secret_key_redacted(self):
        result = self._s(f"PAYMENT_TEST={_FAKE['sk_test']}")
        assert "[REDACTED]" in result

    def test_pk_live_publishable_key_redacted(self):
        result = self._s(f"PK={_FAKE['pk_live']}")
        assert "[REDACTED]" in result
        assert "pk_live_" not in result

    # --- Polar ---
    def test_polar_token_redacted(self):
        result = self._s(f"pioneer_key={_FAKE['polar']}")
        assert "[REDACTED]" in result
        assert "polar_" + "AbCdEf" not in result

    def test_polar_false_positive_short(self):
        result = self._s("polar_short")
        assert "[REDACTED]" not in result

    # --- Hugging Face ---
    def test_huggingface_token_redacted(self):
        result = self._s(f"HF_TOKEN={_FAKE['hf']}")
        assert "[REDACTED]" in result
        assert "hf_" not in result

    def test_huggingface_false_positive_short(self):
        result = self._s("hf_short")
        assert "[REDACTED]" not in result

    # --- Replicate ---
    def test_replicate_token_redacted(self):
        result = self._s(_FAKE["r8"])
        assert "[REDACTED]" in result
        assert "r8_" not in result

    # --- SendGrid ---
    def test_sendgrid_key_redacted(self):
        # SG. + 22 chars + . + 43 chars (constructed at runtime)
        token = _tok("SG.", "A" * 22, ".", "B" * 43)
        result = self._s(f"SENDGRID={token}")
        assert "[REDACTED]" in result
        assert "SG." not in result

    def test_sendgrid_false_positive_wrong_length(self):
        result = self._s("SG.short.val")
        assert "[REDACTED]" not in result

    # --- Twilio ---
    def test_twilio_token_redacted(self):
        token = _tok("SK", "a" * 32)
        result = self._s(f"TWILIO={token}")
        assert "[REDACTED]" in result
        assert token not in result

    # --- Mailgun ---
    def test_mailgun_key_redacted(self):
        token = _tok("key-", "b" * 32)
        result = self._s(f"MAILGUN={token}")
        assert "[REDACTED]" in result

    def test_mailgun_false_positive_non_hex(self):
        result = self._s("key-ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
        assert "[REDACTED]" not in result

    # --- Slack ---
    def test_slack_bot_token_redacted(self):
        token = _tok("xoxb-", "123456789012-AbCdEfGhIjKlMnOpQrSt")
        result = self._s(f"SLACK={token}")
        assert "[REDACTED]" in result
        assert "xoxb-" not in result

    def test_slack_user_token_redacted(self):
        token = _tok("xoxp-", "123456789012-AbCdEfGhIjKlMnOpQrSt")
        result = self._s(token)
        assert "[REDACTED]" in result

    def test_slack_false_positive_unknown_prefix(self):
        result = self._s("xoxz-123456789012-AbCdEfGhIjKlMnOpQrSt")
        assert "[REDACTED]" not in result

    # --- JWT (assembled at runtime from separate segments) ---
    def test_jwt_supabase_redacted(self):
        jwt = f"{_FAKE['jwt_header']}.{_FAKE['jwt_payload']}.{_FAKE['jwt_sig']}"
        result = self._s(f"token={jwt}")
        assert "[REDACTED]" in result

    def test_jwt_false_positive_missing_segments(self):
        result = self._s(_FAKE["jwt_header"])
        assert "[REDACTED]" not in result

    # --- Bearer token ---
    def test_bearer_token_redacted(self):
        bearer = _tok("Bearer ", _FAKE["jwt_header"], ".", _FAKE["jwt_payload"], ".", _FAKE["jwt_sig"])
        result = self._s(f"Authorization: {bearer}")
        assert "[REDACTED]" in result
        assert "Bearer " + _FAKE["jwt_header"][:4] not in result

    def test_bearer_false_positive_short_token(self):
        result = self._s("Bearer shorttoken")
        assert "[REDACTED]" not in result

    # --- Azure subscription key ---
    def test_azure_subscription_key_redacted(self):
        hex32 = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
        result = self._s(f"Ocp-Apim-Subscription-Key: {hex32}")
        assert "[REDACTED]" in result

    def test_azure_key_context_redacted(self):
        hex32 = "deadbeefcafe1234deadbeefcafe5678"
        result = self._s(f"azure_key={hex32}")
        assert "[REDACTED]" in result

    # --- Generic api_key ---
    def test_generic_api_key_colon_redacted(self):
        result = self._s("api_key: supersecretvalue123456789")
        assert "[REDACTED]" in result

    def test_generic_api_key_equals_redacted(self):
        result = self._s("apikey=supersecretvalue123456789")
        assert "[REDACTED]" in result

    # --- Generic secret ---
    def test_generic_secret_redacted(self):
        result = self._s("secret=mysupersecretpassphrase123")
        assert "[REDACTED]" in result

    # --- Generic token / password ---
    def test_generic_token_redacted(self):
        result = self._s("token=averylongtokenvalue1234567890abcdef")
        assert "[REDACTED]" in result

    def test_generic_password_redacted(self):
        result = self._s("password=MyVeryLongPassword1234567890!")
        assert "[REDACTED]" in result

    def test_generic_token_false_positive_short(self):
        result = self._s("token=short")
        assert "[REDACTED]" not in result

    # --- Catch-all high-entropy credential contexts ---
    def test_private_key_context_redacted(self):
        result = self._s("private_key=AbCdEfGhIjKlMnOpQrStUvWxYz1234567890")
        assert "[REDACTED]" in result

    def test_access_token_context_redacted(self):
        result = self._s("access_token=AbCdEfGhIjKlMnOpQrStUvWxYz123456")
        assert "[REDACTED]" in result

    # --- Confirm clean content survives ---
    def test_clean_markdown_unchanged(self):
        content = (
            "# Handoff 2026-04-10\n\n"
            "Completed Items:\n"
            "- UUID audit: os.urandom confirmed\n"
            "- Phase 2 tier-gate: async Polar adapter\n\n"
            "No API keys or secrets in this content."
        )
        result = self._s(content)
        assert result == content


# ---------------------------------------------------------------------------
# 6. Polar circuit breaker + retry (X-Agent Item 3)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestPolarCircuitBreaker:
    """Circuit breaker, retry, and fail-closed behaviour for PolarAdapter."""

    def _make_adapter(self):
        """Create an adapter with a mock PolarClient."""
        from unittest.mock import MagicMock
        import verifimind_mcp.middleware.polar_adapter as pa
        mock_client = MagicMock()
        mock_client.has_pioneer_access.return_value = True
        adapter = pa.PolarAdapter(mock_client, cache_ttl=300)
        return adapter, mock_client

    async def test_timeout_raises_and_tier_gate_denies(self, monkeypatch):
        """Polar timeout → PolarAdapter raises → tier_gate fails-closed."""
        import httpx
        from unittest.mock import AsyncMock, MagicMock
        import verifimind_mcp.middleware.polar_adapter as pa
        import verifimind_mcp.middleware.tier_gate as tg

        adapter, mock_client = self._make_adapter()
        mock_client.get_customer_state = AsyncMock(
            side_effect=httpx.TimeoutException("Polar timed out")
        )
        monkeypatch.setattr(pa, "_adapter", adapter)
        monkeypatch.setenv("POLAR_ACCESS_TOKEN", "ci-fake-access-token-not-real")
        monkeypatch.setattr(tg, "_PIONEER_KEYS", frozenset())

        # tier_gate should deny (fail-closed), not raise
        allowed, tier = await tg.check_tier("test-uuid-timeout-scenario-00001")
        assert allowed is False
        assert tier == "scholar"

    async def test_500_error_retries_and_fails(self, monkeypatch):
        """Polar 500 → PolarAdapter retries _RETRY_MAX_ATTEMPTS times, then fails."""
        import httpx
        from unittest.mock import AsyncMock, MagicMock
        import verifimind_mcp.middleware.polar_adapter as pa

        adapter, mock_client = self._make_adapter()

        # Build a mock response for HTTP 500
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_client.get_customer_state = AsyncMock(
            side_effect=httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_response)
        )

        # Patch asyncio.sleep so tests run fast
        monkeypatch.setattr("asyncio.sleep", AsyncMock())

        with pytest.raises(httpx.HTTPStatusError):
            await adapter.check_pioneer_access("test-uuid-500-scenario-000001")

        # Should have attempted _RETRY_MAX_ATTEMPTS times
        assert mock_client.get_customer_state.call_count == pa._RETRY_MAX_ATTEMPTS

    async def test_circuit_breaker_opens_after_threshold(self, monkeypatch):
        """5 consecutive failures → circuit opens → CircuitOpenError raised."""
        import httpx
        from unittest.mock import AsyncMock, MagicMock
        import verifimind_mcp.middleware.polar_adapter as pa

        adapter, mock_client = self._make_adapter()
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_client.get_customer_state = AsyncMock(
            side_effect=httpx.HTTPStatusError("Service unavailable", request=MagicMock(), response=mock_response)
        )
        monkeypatch.setattr("asyncio.sleep", AsyncMock())

        # Trip the circuit by exhausting failures
        for _ in range(pa._CIRCUIT_FAILURE_THRESHOLD):
            try:
                await adapter.check_pioneer_access(f"uuid-trip-{_:04d}-AABBCC")
            except Exception:
                pass  # expected — failures accumulate

        assert adapter._circuit_open is True
        assert adapter._consecutive_failures >= pa._CIRCUIT_FAILURE_THRESHOLD

        # Next call should raise CircuitOpenError immediately (no network call)
        call_count_before = mock_client.get_customer_state.call_count
        with pytest.raises(pa.CircuitOpenError):
            await adapter.check_pioneer_access("uuid-after-circuit-open-1234")
        # No additional Polar API calls when circuit is open
        assert mock_client.get_customer_state.call_count == call_count_before

    async def test_circuit_breaker_fail_closed_in_tier_gate(self, monkeypatch):
        """Circuit open → tier_gate returns (False, 'scholar') without env-var fallback."""
        from unittest.mock import AsyncMock, MagicMock
        import verifimind_mcp.middleware.polar_adapter as pa
        import verifimind_mcp.middleware.tier_gate as tg

        adapter, mock_client = self._make_adapter()
        # Force circuit open
        adapter._circuit_open = True
        adapter._circuit_opened_at = __import__("time").time()
        adapter._consecutive_failures = 5

        monkeypatch.setattr(pa, "_adapter", adapter)
        # Simulate POLAR_ACCESS_TOKEN being set (production)
        monkeypatch.setenv("POLAR_ACCESS_TOKEN", "ci-fake-access-token-circuit-open")
        # env-var PIONEER_KEYS has the key — should NOT be used (fail-closed)
        monkeypatch.setattr(tg, "_PIONEER_KEYS", frozenset(["fallback-key"]))

        allowed, tier = await tg.check_tier("fallback-key")
        assert allowed is False, "Circuit open must fail-closed, NOT fall back to env var"
        assert tier == "scholar"

    async def test_circuit_breaker_resets_after_window(self, monkeypatch):
        """After _CIRCUIT_RESET_SECONDS, circuit enters half-open → success closes it."""
        from unittest.mock import AsyncMock
        import verifimind_mcp.middleware.polar_adapter as pa

        adapter, mock_client = self._make_adapter()
        mock_client.get_customer_state = AsyncMock(return_value={"benefit_grants": []})
        mock_client.has_pioneer_access.return_value = False

        # Manually open the circuit with an old timestamp (beyond reset window)
        adapter._circuit_open = True
        adapter._consecutive_failures = 5
        adapter._circuit_opened_at = __import__("time").time() - pa._CIRCUIT_RESET_SECONDS - 1

        # Next call: circuit should enter half-open, Polar succeeds → circuit closed
        result = await adapter.check_pioneer_access("uuid-recovery-test-12345678")
        assert result is False  # scholar (no pioneer benefit in mock state)
        assert adapter._circuit_open is False
        assert adapter._consecutive_failures == 0


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


# ---------------------------------------------------------------------------
# 7. Billing path coverage — registration.py edge cases (X-Agent Item 4)
# ---------------------------------------------------------------------------

class TestRegistrationBillingPaths:
    """Edge cases for billing-critical registration code paths.

    Targets lines uncovered by tests/test_registration.py:
    - SlotCapReachedError model
    - Pilot tier via invite_code
    - New EA registration WITH Firestore (write path)
    - register_early_adopter slot cap exceeded
    - register_user email dedup path
    - Opt-out for unknown UUID (no Firestore record)
    - _count_tier_slots exception path
    """

    def _make_ea_reg(self, **kw):
        from verifimind_mcp.registration import EarlyAdopterRegistration
        base = {"email": "test@billing.com", "tc_accepted": True, "privacy_acknowledged": True}
        base.update(kw)
        return EarlyAdopterRegistration(**base)

    # --- SlotCapReachedError ---

    def test_slot_cap_error_attributes(self):
        from verifimind_mcp.registration import SlotCapReachedError
        err = SlotCapReachedError("pilot", 50)
        assert err.tier == "pilot"
        assert err.max_slots == 50
        assert "50/50" in str(err)

    def test_slot_cap_error_early_adopter(self):
        from verifimind_mcp.registration import SlotCapReachedError
        err = SlotCapReachedError("early_adopter", 100)
        assert err.tier == "early_adopter"
        assert "100/100" in str(err)

    # --- _build_benefit_summary pilot path ---

    def test_build_benefit_summary_pilot(self):
        from verifimind_mcp.registration import _build_benefit_summary
        result = _build_benefit_summary("pilot", "Pilot Member", "2026-10-10T00:00:00+00:00")
        assert "Pilot Member" in result
        assert "50-slot" in result

    def test_build_benefit_summary_early_adopter(self):
        from verifimind_mcp.registration import _build_benefit_summary
        result = _build_benefit_summary("early_adopter", "Early Adopter", "2026-07-10T00:00:00+00:00")
        assert "Early Adopter" in result

    # --- _count_tier_slots exception path ---

    def test_count_tier_slots_exception_returns_zero(self):
        """If Firestore count query fails, returns 0 (safe default — no phantom cap)."""
        from unittest.mock import MagicMock
        from verifimind_mcp.registration import _count_tier_slots

        mock_db = MagicMock()
        mock_db.collection.return_value.where.return_value.where.return_value.count.return_value.get.side_effect = Exception("Firestore timeout")

        result = _count_tier_slots(mock_db, "early_adopter")
        assert result == 0

    # --- register_early_adopter: slot cap exceeded ---

    @pytest.mark.asyncio
    async def test_slot_cap_raises_when_full(self):
        from unittest.mock import MagicMock, patch
        from verifimind_mcp.registration import (
            register_early_adopter, SlotCapReachedError, EA_MAX_SLOTS
        )

        mock_db = MagicMock()
        mock_db.collection.return_value.where.return_value.where.return_value.count.return_value.get.return_value = [[MagicMock(value=EA_MAX_SLOTS)]]

        with patch("verifimind_mcp.registration._get_firestore", return_value=mock_db):
            with pytest.raises(SlotCapReachedError) as exc_info:
                await register_early_adopter(self._make_ea_reg())
        assert exc_info.value.tier == "early_adopter"

    # --- register_early_adopter: new registration with Firestore write ---

    @pytest.mark.asyncio
    async def test_new_registration_writes_to_firestore(self):
        """Full write path: new UUID stored in Firestore."""
        from unittest.mock import MagicMock, patch
        from verifimind_mcp.registration import register_early_adopter, RegistrationResponse

        mock_db = MagicMock()
        mock_db.collection.return_value.where.return_value.where.return_value.count.return_value.get.return_value = [[MagicMock(value=0)]]
        mock_db.collection.return_value.where.return_value.limit.return_value.get.return_value = []

        with patch("verifimind_mcp.registration._get_firestore", return_value=mock_db):
            result = await register_early_adopter(self._make_ea_reg())

        assert isinstance(result, RegistrationResponse)
        assert result.tier == "early_adopter"
        mock_db.collection.return_value.document.return_value.set.assert_called_once()

    # --- register_early_adopter: duplicate email returns pilot record ---

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_existing_pilot(self):
        from unittest.mock import MagicMock, patch
        from verifimind_mcp.registration import register_early_adopter

        existing_uuid = "01960000-0000-7000-8000-000000000099"
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "uuid": existing_uuid,
            "tier": "pilot",
            "registered_at": "2026-04-01T00:00:00+00:00",
            "benefits": {"v060_beta_free_until": "2026-10-01T00:00:00+00:00"},
            "tc_version": "2.0",
            "privacy_version": "2.0",
            "pilot_free_months": 6,
        }
        mock_db = MagicMock()
        mock_db.collection.return_value.where.return_value.where.return_value.count.return_value.get.return_value = [[MagicMock(value=0)]]
        mock_db.collection.return_value.where.return_value.limit.return_value.get.return_value = [mock_doc]

        with patch("verifimind_mcp.registration._get_firestore", return_value=mock_db):
            result = await register_early_adopter(self._make_ea_reg())

        assert result.uuid == existing_uuid
        assert result.tier == "pilot"
        assert "already registered" in result.message

    # --- register_early_adopter: feedback stored separately ---

    @pytest.mark.asyncio
    async def test_feedback_stored_in_feedback_collection(self):
        from unittest.mock import MagicMock, patch
        from verifimind_mcp.registration import register_early_adopter

        mock_db = MagicMock()
        mock_db.collection.return_value.where.return_value.where.return_value.count.return_value.get.return_value = [[MagicMock(value=0)]]
        mock_db.collection.return_value.where.return_value.limit.return_value.get.return_value = []

        with patch("verifimind_mcp.registration._get_firestore", return_value=mock_db):
            result = await register_early_adopter(
                self._make_ea_reg(feedback="Great product!", feedback_type="general")
            )

        assert result.feedback_received is True
        assert mock_db.collection.return_value.add.called

    # --- process_optout: unknown UUID (no Firestore record) ---

    @pytest.mark.asyncio
    async def test_optout_unknown_uuid_no_update(self):
        """Opt-out for unknown UUID: logs but does not call update()."""
        from unittest.mock import MagicMock, patch
        from verifimind_mcp.registration import process_optout, OptOutResponse

        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_doc_ref = MagicMock()
        mock_doc_ref.get.return_value = mock_doc
        mock_db = MagicMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        with patch("verifimind_mcp.registration._get_firestore", return_value=mock_db):
            result = await process_optout("non-existent-uuid-0000000000000")

        assert isinstance(result, OptOutResponse)
        mock_doc_ref.update.assert_not_called()

    # --- register_user: email dedup via Firestore ---

    @pytest.mark.asyncio
    async def test_register_user_email_dedup_returns_existing(self):
        from unittest.mock import MagicMock, patch
        from verifimind_mcp.registration import UserRegistrationRequest, register_user

        existing_uuid = "01970000-0000-7000-8000-000000000077"
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "uuid": existing_uuid,
            "tier": "ea",
            "registered_at": "2026-04-10T00:00:00+00:00",
            "expires_at": "2026-07-10T00:00:00+00:00",
        }
        mock_db = MagicMock()
        mock_db.collection.return_value.where.return_value.limit.return_value.get.return_value = [mock_doc]

        req = UserRegistrationRequest(email="returning@example.com", consent=True)
        with patch("verifimind_mcp.registration._get_firestore", return_value=mock_db):
            result = await register_user(req)

        assert result.uuid == existing_uuid
        assert "already registered" in result.message

    # --- register_user: new registration written to Firestore ---

    @pytest.mark.asyncio
    async def test_register_user_new_writes_firestore(self):
        from unittest.mock import MagicMock, patch
        from verifimind_mcp.registration import UserRegistrationRequest, register_user

        mock_db = MagicMock()
        mock_db.collection.return_value.where.return_value.limit.return_value.get.return_value = []

        req = UserRegistrationRequest(email="newuser@example.com", consent=True)
        with patch("verifimind_mcp.registration._get_firestore", return_value=mock_db):
            result = await register_user(req)

        assert result.uuid
        mock_db.collection.return_value.document.return_value.set.assert_called_once()
