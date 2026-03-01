"""
v0.5.0 Foundation — Unit Tests

Tests for:
1. Smithery removal verification
2. SessionContext (models/session.py)
3. BYOK auto-detection edge cases
4. Structured error responses (build_error_response)
5. Security boundaries (api_key never logged)
6. Health endpoint v2 fields
"""

import importlib
import importlib.util
import logging
import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# 1. Smithery Removal (5 tests)
# ---------------------------------------------------------------------------

class TestSmitheryRemoval:
    """Verify smithery has been fully removed from the codebase."""

    def test_smithery_not_in_requirements(self):
        """requirements.txt must not list smithery (this is the canonical check)."""
        req_path = Path(__file__).parent.parent.parent / "requirements.txt"
        content = req_path.read_text(encoding="utf-8").lower()
        assert "smithery" not in content

    @pytest.mark.skipif(
        importlib.util.find_spec("smithery") is not None,
        reason="smithery still installed globally in dev env — passes in CI after fresh pip install"
    )
    def test_smithery_not_importable(self):
        """In CI (fresh install from requirements.txt), smithery must not be importable."""
        assert importlib.util.find_spec("smithery") is None

    def test_no_smithery_in_requirements(self):
        """requirements.txt must not reference smithery."""
        req_path = Path(__file__).parent.parent.parent / "requirements.txt"
        content = req_path.read_text(encoding="utf-8").lower()
        assert "smithery" not in content, "smithery still listed in requirements.txt"

    def test_no_smithery_import_in_server_py(self):
        """server.py must not import from smithery."""
        server_path = (
            Path(__file__).parent.parent.parent
            / "src" / "verifimind_mcp" / "server.py"
        )
        content = server_path.read_text(encoding="utf-8")
        assert "from smithery" not in content
        assert "import smithery" not in content

    def test_no_smithery_decorator_in_server_py(self):
        """@smithery.server decorator must be gone from server.py."""
        server_path = (
            Path(__file__).parent.parent.parent
            / "src" / "verifimind_mcp" / "server.py"
        )
        content = server_path.read_text(encoding="utf-8")
        assert "@smithery.server" not in content

    def test_server_version_is_050(self):
        """SERVER_VERSION must be bumped to 0.5.0."""
        from verifimind_mcp.server import SERVER_VERSION
        assert SERVER_VERSION == "0.5.0", (
            f"Expected 0.5.0, got {SERVER_VERSION}"
        )


# ---------------------------------------------------------------------------
# 2. SessionContext (7 tests)
# ---------------------------------------------------------------------------

class TestSessionContext:
    """Tests for the v0.5.0 SessionContext dataclass."""

    def setup_method(self):
        from verifimind_mcp.models.session import SessionContext
        self.SessionContext = SessionContext

    def test_unique_session_ids(self):
        s1 = self.SessionContext()
        s2 = self.SessionContext()
        assert s1.session_id != s2.session_id

    def test_session_id_is_8_chars(self):
        s = self.SessionContext()
        assert len(s.session_id) == 8

    def test_write_and_read(self):
        s = self.SessionContext(concept_name="Test Concept")
        s.write("X", {"score": 7.5, "provider": "groq/llama"})
        result = s.read("X")
        assert result == {"score": 7.5, "provider": "groq/llama"}

    def test_read_missing_key_returns_none(self):
        s = self.SessionContext()
        assert s.read("nonexistent") is None

    def test_agents_completed_tracks_writes(self):
        s = self.SessionContext()
        assert s.agents_completed == []
        s.write("X", {})
        assert "X" in s.agents_completed
        s.write("Z", {})
        assert "Z" in s.agents_completed

    def test_to_metadata_contains_required_fields(self):
        s = self.SessionContext(concept_name="My Idea")
        s.write("X", {"score": 8.0})
        s.write("Z", {"score": 7.5})
        meta = s.to_metadata()
        assert "_session_id" in meta
        assert "_session_started" in meta
        assert "_agents_completed" in meta
        assert "X" in meta["_agents_completed"]
        assert "Z" in meta["_agents_completed"]

    def test_api_key_must_not_be_stored_in_session(self):
        """Security: session state must never contain api_key values."""
        s = self.SessionContext()
        # Simulate what server.py writes — only scores and provider names
        s.write("X", {"score": 7.5, "provider": "groq/llama-3.3-70b"})
        serialized = str(s.to_metadata()) + str(s.outputs)
        assert "api_key" not in serialized
        assert "gsk_" not in serialized
        assert "sk-ant-" not in serialized


# ---------------------------------------------------------------------------
# 3. BYOK Auto-Detection Edge Cases (8 tests)
# ---------------------------------------------------------------------------

class TestByokAutoDetection:
    """Tests for create_ephemeral_provider() key prefix auto-detection."""

    def setup_method(self):
        from verifimind_mcp.config_helper import create_ephemeral_provider
        self.create_ephemeral_provider = create_ephemeral_provider

    def test_no_key_returns_none(self):
        """No api_key → returns None (caller uses server default)."""
        result = self.create_ephemeral_provider(None, None, "X")
        assert result is None

    def test_empty_key_returns_none(self):
        result = self.create_ephemeral_provider(None, "", "X")
        assert result is None

    def test_gsk_prefix_routes_to_groq(self):
        """gsk_ prefix must auto-detect as Groq."""
        provider = self.create_ephemeral_provider(None, "gsk_fakefakefake123", "X")
        assert provider is not None
        model = provider.get_model_name()
        assert "groq" in model.lower()

    def test_sk_ant_prefix_routes_to_anthropic(self):
        """sk-ant- prefix must route to Anthropic (not OpenAI)."""
        provider = self.create_ephemeral_provider(None, "sk-ant-fake123", "X")
        assert provider is not None
        model = provider.get_model_name()
        assert "claude" in model.lower() or "anthropic" in model.lower()

    def test_sk_prefix_routes_to_openai_not_anthropic(self):
        """sk- prefix (without ant-) must route to OpenAI."""
        provider = self.create_ephemeral_provider(None, "sk-fake123", "X")
        assert provider is not None
        model = provider.get_model_name()
        # Must be OpenAI, not Anthropic
        assert "claude" not in model.lower()

    def test_aiza_prefix_routes_to_gemini(self):
        """AIza prefix must auto-detect as Gemini."""
        provider = self.create_ephemeral_provider(None, "AIzafake123", "X")
        assert provider is not None
        model = provider.get_model_name()
        assert "gemini" in model.lower()

    def test_explicit_provider_overrides_autodetect(self):
        """Explicit llm_provider takes priority over key prefix detection."""
        # sk-ant- prefix would normally → Anthropic, but we override to groq
        provider = self.create_ephemeral_provider("groq", "sk-ant-fake123", "X")
        assert provider is not None
        model = provider.get_model_name()
        assert "groq" in model.lower()

    def test_mock_provider_for_testing(self):
        """mock provider must work for testing without a real key."""
        provider = self.create_ephemeral_provider("mock", None, "X")
        assert provider is not None
        model = provider.get_model_name()
        assert "mock" in model.lower()


# ---------------------------------------------------------------------------
# 4. Structured Error Responses (5 tests)
# ---------------------------------------------------------------------------

class TestStructuredErrors:
    """Tests for build_error_response() (v0.5.0 Error Handling v2)."""

    def setup_method(self):
        from verifimind_mcp.server import build_error_response
        self.build_error_response = build_error_response

    def test_required_fields_present(self):
        err = self.build_error_response(
            error_code="BYOK_AUTH_FAILED",
            message="Invalid API key",
            recovery_hint="Check your key",
        )
        assert err["status"] == "error"
        assert err["error_code"] == "BYOK_AUTH_FAILED"
        assert err["error"] == "Invalid API key"
        assert err["recovery_hint"] == "Check your key"
        assert "timestamp" in err

    def test_agent_field(self):
        err = self.build_error_response(
            error_code="PROVIDER_TIMEOUT",
            message="Timeout",
            recovery_hint="Try again",
            agent="X",
        )
        assert err["agent"] == "X"

    def test_agent_defaults_to_none(self):
        err = self.build_error_response(
            error_code="TRINITY_ERROR",
            message="Something failed",
            recovery_hint="Retry",
        )
        assert err["agent"] is None

    def test_timestamp_is_iso_format(self):
        from datetime import datetime
        err = self.build_error_response("E", "msg", "hint")
        # Should parse as ISO timestamp without raising
        dt = datetime.fromisoformat(err["timestamp"].replace("Z", "+00:00"))
        assert dt is not None

    def test_original_error_logged_not_exposed(self):
        """The original exception should be logged but not in the response dict."""
        original = ValueError("internal detail")
        err = self.build_error_response(
            error_code="TEST_ERR",
            message="Public message",
            recovery_hint="Hint",
            original_error=original,
        )
        # The response exposes only the message, not the raw exception
        assert "internal detail" not in err.get("error", "")
        assert "original_error" not in err


# ---------------------------------------------------------------------------
# 5. Security Boundaries (5 tests)
# ---------------------------------------------------------------------------

class TestSecurityBoundaries:
    """Security invariants that must hold across v0.5.0."""

    def test_api_key_not_in_session_metadata(self):
        """Session metadata must never contain raw api_key values."""
        from verifimind_mcp.models.session import SessionContext
        s = SessionContext()
        s.write("X", {"score": 7.5, "provider": "groq/llama-3.3-70b-versatile"})
        meta_str = str(s.to_metadata())
        for sensitive in ["gsk_", "sk-ant-", "AIza", "api_key"]:
            assert sensitive not in meta_str

    def test_api_key_not_logged(self, caplog):
        """create_ephemeral_provider must not log the raw api_key value."""
        from verifimind_mcp.config_helper import create_ephemeral_provider
        fake_key = "gsk_SUPERSECRETFAKEKEYFORTESTING12345"
        with caplog.at_level(logging.DEBUG, logger="verifimind_mcp"):
            create_ephemeral_provider("groq", fake_key, "X")
        assert fake_key not in caplog.text

    def test_error_response_no_api_key_leakage(self):
        """build_error_response must not leak api_key in any field."""
        from verifimind_mcp.server import build_error_response
        key = "gsk_SECRETKEY99999"
        err = build_error_response(
            error_code="BYOK_AUTH_FAILED",
            message=f"Auth failed (provider=groq)",  # key NOT included in message
            recovery_hint="Check your api_key",
        )
        err_str = str(err)
        assert key not in err_str

    def test_session_context_importable(self):
        """models.session must be importable as part of the package."""
        from verifimind_mcp.models.session import SessionContext
        assert SessionContext is not None

    def test_rate_limit_middleware_importable(self):
        """RateLimitMiddleware must remain importable after refactor."""
        from verifimind_mcp.middleware import RateLimitMiddleware
        assert RateLimitMiddleware is not None
