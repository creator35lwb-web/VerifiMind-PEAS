"""
v0.5.46 — BYOK robustness bundle (Step 1 of the M2 unified path).

Covers three production-hardening fixes surfaced by GCP logs + M2 P3 runs:

1. Provider-format normalization (D-AZ-0618-1): a June-17 prod user passed
   `anthropic/claude-opus-4-8` and was rejected as "Invalid provider". We now
   accept the `provider/model` shorthand, split it server-side, honor the model,
   and give an actionable error otherwise.
2. Per-provider max_tokens clamp: configs request 8192 (verbose models like
   Claude truncated at 4096); Groq's tighter total-request budget is clamped
   back to a safe ceiling.
3. Token-monitor repair (P2-2): `_output_tokens` is now populated on agent
   results so the Z-Agent token-ceiling monitor reads a real count instead of 0.
"""

import pytest

from verifimind_mcp.config_helper import create_ephemeral_provider
from verifimind_mcp.agents.base_agent import GROQ_SAFE_MAX_OUTPUT_TOKENS
from verifimind_mcp.agents import XAgent
from verifimind_mcp.llm import MockProvider, GroqProvider, AnthropicProvider


# --- 1. Provider-format normalization (D-AZ-0618-1) -------------------------

def test_provider_model_shorthand_splits_and_honors_model():
    """`anthropic/claude-opus-4-8` resolves to AnthropicProvider with that model."""
    p = create_ephemeral_provider(llm_provider="anthropic/claude-opus-4-8", api_key="sk-ant-test")
    assert isinstance(p, AnthropicProvider)
    # the model part is honored on the provider; get_model_name() renders provider/model
    assert p.model == "claude-opus-4-8"
    assert p.get_model_name() == "anthropic/claude-opus-4-8"


def test_bare_provider_still_works():
    p = create_ephemeral_provider(llm_provider="mock")
    assert isinstance(p, MockProvider)


def test_invalid_provider_raises_actionable_error():
    with pytest.raises(ValueError) as exc:
        create_ephemeral_provider(llm_provider="claude-opus-4-8", api_key="sk-ant-test")
    msg = str(exc.value)
    assert "Invalid provider" in msg
    # actionable guidance: tell the user how to pass a model
    assert "provider/model" in msg or "separately" in msg


def test_shorthand_without_model_part_is_bare_provider():
    """Trailing slash / empty model part falls back to provider default model."""
    p = create_ephemeral_provider(llm_provider="anthropic/", api_key="sk-ant-test")
    assert isinstance(p, AnthropicProvider)


# --- 2. Per-provider max_tokens clamp ---------------------------------------

def test_large_context_provider_uses_full_config():
    """X config requests 8192; a non-Groq provider keeps it."""
    agent = XAgent(llm_provider=MockProvider())
    assert agent.config.max_tokens == 8192
    assert agent._effective_max_tokens() == 8192


def test_groq_provider_clamped_to_safe_ceiling():
    agent = XAgent(llm_provider=GroqProvider(api_key="gsk_test"))
    assert agent._effective_max_tokens() == GROQ_SAFE_MAX_OUTPUT_TOKENS
    assert agent._effective_max_tokens() <= agent.config.max_tokens


# --- 3. Token-monitor repair (P2-2) -----------------------------------------

def test_output_tokens_default_zero_is_safe():
    """server.py reads getattr(result, '_output_tokens', 0); the monitor handles 0."""
    from verifimind_mcp.utils.token_monitor import check_z_agent_response
    m = check_z_agent_response(0)
    assert m["token_count"] == 0
    assert m["risk_level"] == "LOW"
    assert m["truncated"] is False


def test_monitor_flags_truncation_at_ceiling():
    from verifimind_mcp.utils.token_monitor import check_z_agent_response
    m = check_z_agent_response(8192)
    assert m["risk_level"] == "CRITICAL"
    assert m["truncated"] is True
