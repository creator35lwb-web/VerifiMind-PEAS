"""
v0.5.50 Robustness Pass — BYOK admission contract (config_helper)
=================================================================

Foundation Inspection pass 1, batch 3 (Hub #81; T scoping: "BYOK/provider
admission contract: resolved model IDs, fallback behavior, and clear
user-facing errors"). config_helper.py sat at 27% — the admission decisions
(shorthand split, key-prefix auto-detect, fallbacks, rejections) were dark.
"""

import pytest

from verifimind_mcp.config_helper import create_ephemeral_provider, VALID_BYOK_PROVIDERS
from verifimind_mcp.llm.provider import MockProvider, GroqProvider, AnthropicProvider


# ---------------------------------------------------------------------------
# Server-default fallbacks (return None = "use server provider")
# ---------------------------------------------------------------------------

def test_no_params_returns_none_server_default():
    assert create_ephemeral_provider(None, None) is None


def test_provider_without_key_falls_back_to_server_default():
    """Real-provider name with no key must NOT raise — fall back (the server
    may hold the env key)."""
    assert create_ephemeral_provider("groq", None) is None


def test_mock_needs_no_key():
    p = create_ephemeral_provider("mock", None)
    assert isinstance(p, MockProvider)


# ---------------------------------------------------------------------------
# provider/model shorthand (D-AZ-0618-1 — the June-17 prod rejection fix)
# ---------------------------------------------------------------------------

def test_shorthand_splits_provider_and_carries_model():
    p = create_ephemeral_provider("groq/qwen/qwen3.6-27b", "gsk_test123")
    assert isinstance(p, GroqProvider)
    # partition on the FIRST slash: model part keeps its own namespace slash
    assert p.model == "qwen/qwen3.6-27b"


def test_shorthand_anthropic_model_carried():
    p = create_ephemeral_provider("anthropic/claude-opus-4-8", "sk-ant-test")
    assert isinstance(p, AnthropicProvider)
    assert p.model == "claude-opus-4-8"


# ---------------------------------------------------------------------------
# Key-prefix auto-detection (order matters: sk-ant- before sk-)
# ---------------------------------------------------------------------------

def test_sk_ant_prefix_detects_anthropic_not_openai():
    p = create_ephemeral_provider(None, "sk-ant-abc123")
    assert isinstance(p, AnthropicProvider)


def test_gsk_prefix_detects_groq():
    p = create_ephemeral_provider(None, "gsk_abc123")
    assert isinstance(p, GroqProvider)


def test_unknown_prefix_raises_clear_error():
    with pytest.raises(ValueError) as e:
        create_ephemeral_provider(None, "zz-unknownkey")
    assert "auto-detect" in str(e.value)


# ---------------------------------------------------------------------------
# Rejections — user-facing error contract
# ---------------------------------------------------------------------------

def test_invalid_provider_rejected_with_shorthand_hint():
    with pytest.raises(ValueError) as e:
        create_ephemeral_provider("perplexity", "pplx-key")
    msg = str(e.value)
    assert "Invalid provider" in msg
    assert "shorthand" in msg  # the D-AZ-0618-1 hint must be user-visible


def test_valid_provider_set_is_the_documented_eight():
    assert VALID_BYOK_PROVIDERS == {
        "openai", "anthropic", "gemini", "groq",
        "cerebras", "mistral", "ollama", "mock",
    }


def test_provider_name_case_insensitive():
    p = create_ephemeral_provider("GROQ", "gsk_test123")
    assert isinstance(p, GroqProvider)
