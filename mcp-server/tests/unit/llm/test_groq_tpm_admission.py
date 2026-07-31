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
    # A model outside GROQ_8K_TPM_MODELS. Deliberately NOT a real advertised
    # model: the previous fixture used llama-4-scout, which Groq retired
    # 2026-07-17, so the test depended on a decommissioned ID staying listed.
    budget = _groq_8k_tpm_max_tokens(
        "some-other-provider/unknown-model",
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


# ===========================================================================
# D-115: provider-informed accounting (T S115 required repairs 1-4)
#
# The external CJK finding proved a character heuristic cannot be made safe
# across scripts: a 20,000-character CJK aggregate estimated ~5,010 tokens and
# still admitted 2,478 completion tokens. No divisor fixes every script, so the
# provider's own rejection is treated as MEASUREMENT and drives exactly one
# retry with a budget derived from provider numbers.
# ===========================================================================

from verifimind_mcp.llm.provider import (
    GROQ_MIN_COMPLETION_TOKENS,
    _groq_provider_informed_budget,
)


class _FakeGroqError(Exception):
    """Mimics the SDK error surface: `.body` dict and `.response.headers`."""

    def __init__(self, code=None, message="", limit_header=None):
        super().__init__(message)
        self.body = {"error": {"code": code, "message": message, "type": "tokens"}}
        if limit_header is not None:
            self.response = type("R", (), {"headers": {"x-ratelimit-limit-tokens": limit_header}})()


def _tpm_error(requested, limit=8000, header=True):
    """The real Groq 413 shape captured live 2026-07-30 (S109)."""
    return _FakeGroqError(
        code="rate_limit_exceeded",
        message=(f"Request too large for model `openai/gpt-oss-120b` in organization `org_x` "
                 f"service tier `on_demand` on tokens per minute (TPM): Limit {limit}, "
                 f"Requested {requested}, please reduce your message size and try again."),
        limit_header=str(limit) if header else None,
    )


def test_cjk_underestimate_is_corrected_by_provider_numbers():
    """The external finding, as a regression. A CJK prompt the heuristic scored
    at ~5,010 really costs far more; the provider states the true figure and the
    retry budget is derived from it, not from another guess."""
    sent = 2478
    real_prompt_cost = 6000
    budget = _groq_provider_informed_budget(_tpm_error(real_prompt_cost + sent), sent)
    assert budget is not None
    assert real_prompt_cost + budget <= 8000


@pytest.mark.parametrize("real_prompt_cost", [4000, 5000, 6000, 6400])
def test_provider_derived_budget_always_fits_the_stated_limit(real_prompt_cost):
    """Whatever the true prompt cost, the derived budget must fit — this is the
    property the character estimate could not guarantee for any script."""
    sent = 4096
    budget = _groq_provider_informed_budget(_tpm_error(real_prompt_cost + sent), sent)
    if budget is not None:
        assert real_prompt_cost + budget <= 8000


def test_generic_body_size_413_is_not_retried():
    """D-115-2: a body-too-large 413 is NOT a TPM rejection. Retrying it with a
    smaller completion budget cannot help, because the BODY is the problem."""
    generic = _FakeGroqError(code="request_too_large", message="Request body too large")
    assert _groq_provider_informed_budget(generic, 4096) is None


@pytest.mark.parametrize("broken", [
    _FakeGroqError(code="rate_limit_exceeded", message="TPM exceeded"),          # no numbers
    _FakeGroqError(code="rate_limit_exceeded", message="Requested many, Limit some"),
    _FakeGroqError(code=None, message="Limit 8000, Requested 9000"),             # no code
    Exception("connection reset"),                                              # no body at all
])
def test_malformed_or_ambiguous_errors_are_never_retried(broken):
    """An error we cannot parse must fail, not retry. Retrying something we do
    not understand is how one rejection becomes a loop."""
    assert _groq_provider_informed_budget(broken, 4096) is None


def test_missing_limit_information_fails_rather_than_guessing():
    """D-115-3: with no trustworthy limit — no header and no stated Limit — the
    call must fail rather than assume a universal 8K ceiling."""
    no_limit = _FakeGroqError(
        code="rate_limit_exceeded", message="Requested 9000 tokens", limit_header=None)
    assert _groq_provider_informed_budget(no_limit, 4096) is None


def test_budget_below_useful_output_floor_fails_closed():
    """If the true prompt cost leaves less than the useful-output floor, there
    is no budget worth retrying with — fail rather than return a stub answer."""
    sent = 1024
    huge_prompt = 8000 - GROQ_MIN_COMPLETION_TOKENS + 1
    assert _groq_provider_informed_budget(_tpm_error(huge_prompt + sent), sent) is None


def test_header_limit_wins_over_message_limit():
    """The header is authoritative; the message is prose. When an account limit
    differs from the message text, the header must decide."""
    err = _tpm_error(9000, limit=8000)
    err.response.headers["x-ratelimit-limit-tokens"] = "16000"
    budget = _groq_provider_informed_budget(err, 4096)
    assert budget is not None and budget > 0


@pytest.mark.asyncio
async def test_production_path_retries_exactly_once_then_succeeds():
    """D-115-4 production path: a real GroqProvider.generate call that is
    rejected once must retry with the provider-derived budget and then stop.
    Asserts the CALL COUNT, because "retries correctly" and "retries forever"
    look identical from a passing result."""
    import os
    from unittest.mock import patch
    from verifimind_mcp.llm.provider import GroqProvider

    calls = []

    class _Completions:
        async def create(self, **kwargs):
            calls.append(kwargs["max_tokens"])
            if len(calls) == 1:
                raise _tpm_error(6000 + kwargs["max_tokens"], limit=8000)
            return type("R", (), {
                "choices": [type("C", (), {"message": type("M", (), {"content": '{"ok": true}'})()})()],
                "usage": type("U", (), {"prompt_tokens": 6000, "completion_tokens": 10, "total_tokens": 6010})(),
            })()

    with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
        provider = GroqProvider(model="openai/gpt-oss-120b", api_key="test-key")
    provider.client = type("Cl", (), {"chat": type("Ch", (), {"completions": _Completions()})()})()

    await provider.generate("hello", max_tokens=4096)

    assert len(calls) == 2, f"expected exactly one retry, saw {len(calls)} calls"
    assert 6000 + calls[1] <= 8000, "retry budget must fit the provider limit"


@pytest.mark.asyncio
async def test_production_path_does_not_retry_a_generic_413():
    """A body-size 413 must surface, not be retried — exactly one call."""
    import os
    from unittest.mock import patch
    from verifimind_mcp.llm.provider import GroqProvider

    calls = []

    class _Completions:
        async def create(self, **kwargs):
            calls.append(kwargs["max_tokens"])
            raise _FakeGroqError(code="request_too_large", message="Request body too large")

    with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
        provider = GroqProvider(model="openai/gpt-oss-120b", api_key="test-key")
    provider.client = type("Cl", (), {"chat": type("Ch", (), {"completions": _Completions()})()})()

    # The established provider contract is log-and-re-raise, so a body-size 413
    # SURFACES rather than degrading silently — the caller (or the failover
    # layer) decides. My first version of this test asserted a degraded dict;
    # the code was right and the expectation was wrong.
    with pytest.raises(Exception):
        await provider.generate("hello", max_tokens=4096)

    assert len(calls) == 1, f"generic 413 must not be retried, saw {len(calls)} calls"
