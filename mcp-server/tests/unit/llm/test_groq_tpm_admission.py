"""
Groq 8k TPM admission regression coverage.

S114 found that PR #311's input-aware repair still rejected the measured
orchestrated CS prompt it claimed to fix. These tests pin the provider-measured
Z/CS prompt shapes and exercise the production GroqProvider.generate body.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from verifimind_mcp.llm.provider import (
    GROQ_8K_TPM_COMPLETION_CAP,
    GROQ_8K_TPM_LIMIT,
    GROQ_MIN_COMPLETION_TOKENS,
    GROQ_TPM_SAFETY_MARGIN,
    GroqProvider,
    _estimate_groq_input_tokens,
    _groq_8k_tpm_max_tokens,
)


MEASURED_AGENT_PROMPTS = [
    ("Z standalone", 11183, 2935),
    ("Z orchestrated", 17013, 3886),
    ("CS standalone", 12571, 3072),
    ("CS orchestrated", 23017, 4794),
]


def _messages(char_count: int):
    return [{"role": "user", "content": "x" * char_count}]


def _groq_response(text: str, prompt_tokens: int = 10, completion_tokens: int = 5):
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = text
    response.usage.prompt_tokens = prompt_tokens
    response.usage.completion_tokens = completion_tokens
    response.usage.total_tokens = prompt_tokens + completion_tokens
    return response


def test_measured_z_cs_prompt_shapes_are_admitted_and_under_real_limit():
    for name, chars, provider_measured_input_tokens in MEASURED_AGENT_PROMPTS:
        budget = _groq_8k_tpm_max_tokens("openai/gpt-oss-120b", _messages(chars), 4096)

        assert budget >= GROQ_MIN_COMPLETION_TOKENS, name
        assert budget <= GROQ_8K_TPM_COMPLETION_CAP, name
        assert provider_measured_input_tokens + budget <= GROQ_8K_TPM_LIMIT, name


def test_orchestrated_cs_shape_gets_useful_completion_budget():
    budget = _groq_8k_tpm_max_tokens("openai/gpt-oss-120b", _messages(23017), 4096)

    assert GROQ_MIN_COMPLETION_TOKENS <= budget < GROQ_8K_TPM_COMPLETION_CAP


def test_pr311_divisor_regression_would_reject_measured_cs_shape():
    pr311_estimated_input = (23017 // 3) + 1
    pr311_available = GROQ_8K_TPM_LIMIT - pr311_estimated_input - 256

    assert pr311_available < GROQ_MIN_COMPLETION_TOKENS
    repaired_budget = _groq_8k_tpm_max_tokens(
        "openai/gpt-oss-120b",
        _messages(23017),
        4096,
    )
    assert repaired_budget >= GROQ_MIN_COMPLETION_TOKENS


def test_groq_8k_tpm_fails_closed_when_useful_output_cannot_fit():
    with pytest.raises(ValueError, match="not admissible"):
        _groq_8k_tpm_max_tokens("openai/gpt-oss-120b", _messages(30000), 4096)


def test_non_8k_groq_model_keeps_requested_budget():
    budget = _groq_8k_tpm_max_tokens(
        "meta-llama/llama-4-scout-17b-16e-instruct",
        _messages(30000),
        8192,
    )

    assert budget == 8192


@pytest.mark.asyncio
async def test_groq_generate_admits_measured_cs_orchestrated_shape(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    provider = GroqProvider(model="openai/gpt-oss-120b")
    provider.client = MagicMock()
    captured = {}

    async def fake_create(**kwargs):
        captured.update(kwargs)
        return _groq_response('{"ok": true}', prompt_tokens=4794, completion_tokens=42)

    provider.client.chat.completions.create = AsyncMock(side_effect=fake_create)

    result = await provider.generate("x" * 23017, max_tokens=4096)

    assert result["content"]["ok"] is True
    assert GROQ_MIN_COMPLETION_TOKENS <= captured["max_tokens"] < GROQ_8K_TPM_COMPLETION_CAP
    assert 4794 + captured["max_tokens"] <= GROQ_8K_TPM_LIMIT


def test_budget_keeps_safety_margin_against_local_estimate():
    chars = 17013
    messages = _messages(chars)
    budget = _groq_8k_tpm_max_tokens("openai/gpt-oss-120b", messages, 4096)
    estimated_input = _estimate_groq_input_tokens(messages)

    assert estimated_input + budget + GROQ_TPM_SAFETY_MARGIN <= GROQ_8K_TPM_LIMIT
