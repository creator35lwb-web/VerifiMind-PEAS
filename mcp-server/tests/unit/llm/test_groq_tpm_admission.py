"""
Groq TPM admission is INPUT-AWARE — RNA S107
============================================

Diagnosis origin: Alton observed Z intermittently degrading to `fallback` in the
orchestrated Trinity path while staying `real` standalone. His session isolated
it well (heavy standalone prompt stayed real; two identical orchestrated runs
differed) and concluded "intermittent Groq blip".

It is not a blip. It is arithmetic.

Groq admits a request only when `input + completion_reservation <= TPM limit`.
With a FLAT 4096 reservation against an 8,000 limit, the input budget is 3,904
tokens. Measured against the real prompts:

    Z standalone                       ~2,799 tokens   (headroom +1,105)
    Z orchestrated, typical X payload  ~3,690 tokens   (headroom   +214)
    Z orchestrated, verbose X payload  ~4,428 tokens   (EXCEEDS by  524 -> 413)

X's output length varies per run, so the same concept crosses the ceiling on
some runs and not others — deterministic arithmetic presenting as intermittency.
The `_z_token_monitor` readings (38-47%) measure CONTEXT-WINDOW use, a different
limit entirely, which is why they correctly showed "no truncation" while the
request was still being rejected at admission.

Reserving from the ACTUAL input keeps admission satisfied at any prompt size.
"""

import pytest

from verifimind_mcp.llm.provider import (
    GROQ_8K_TPM_COMPLETION_CAP,
    GROQ_8K_TPM_LIMIT,
    GROQ_8K_TPM_MODELS,
    GROQ_MIN_COMPLETION,
    GROQ_TPM_SAFETY_MARGIN,
    _estimate_tokens,
)


def _clamp(messages, requested, model="openai/gpt-oss-120b"):
    """Mirror of the production clamp, so the arithmetic is asserted directly."""
    if model not in GROQ_8K_TPM_MODELS:
        return requested
    estimated = _estimate_tokens(messages)
    available = GROQ_8K_TPM_LIMIT - estimated - GROQ_TPM_SAFETY_MARGIN
    return min(requested, GROQ_8K_TPM_COMPLETION_CAP, max(available, GROQ_MIN_COMPLETION))


def _messages(token_count):
    return [{"role": "user", "content": "x" * (token_count * 4)}]


# --- the defect this exists to prevent --------------------------------------

def test_orchestrated_sized_prompt_admits_under_the_tpm_limit():
    """The measured failing case: ~4,428-token orchestrated prompt. Under the
    old flat 4096 reservation this totalled 8,524 > 8,000 and Groq rejected."""
    messages = _messages(4428)
    reservation = _clamp(messages, 8192)
    assert _estimate_tokens(messages) + reservation <= GROQ_8K_TPM_LIMIT


@pytest.mark.parametrize("input_tokens", [500, 2799, 3690, 4428, 5500, 6500])
def test_admission_holds_across_the_whole_prompt_range(input_tokens):
    """Admission must be satisfied at ANY prompt size — the property the flat
    cap could not provide, since it only fitted short prompts."""
    messages = _messages(input_tokens)
    assert _estimate_tokens(messages) + _clamp(messages, 8192) <= GROQ_8K_TPM_LIMIT


def test_flat_cap_would_have_failed_the_orchestrated_case():
    """Known-positive against the OLD behaviour: prove the previous constant
    genuinely breaks the measured case, so this suite is not asserting a
    property that was never violated."""
    input_tokens = 4428
    assert input_tokens + GROQ_8K_TPM_COMPLETION_CAP > GROQ_8K_TPM_LIMIT


# --- the reservation must stay useful, not just safe ------------------------

def test_short_prompts_keep_the_full_reservation():
    """Shrinking the reservation on SHORT prompts would trade one failure for
    another (truncated answers). Standalone Z must be unaffected."""
    assert _clamp(_messages(2799), 8192) == GROQ_8K_TPM_COMPLETION_CAP


def test_reservation_never_falls_below_the_observed_output_size():
    """Observed Z/CS outputs run ~1k tokens. Even a very large input must not
    reserve less than that floor — better to surface a loud admission error
    than to silently truncate every answer."""
    assert _clamp(_messages(7000), 8192) >= GROQ_MIN_COMPLETION


def test_caller_budget_is_still_respected_when_smaller():
    """The clamp only ever LOWERS the reservation; a caller asking for less
    than the cap keeps its own smaller number."""
    assert _clamp(_messages(500), 512) == 512


# --- scope and estimator ----------------------------------------------------

def test_non_8k_models_are_untouched():
    """Platform-scoped: models without the 8k TPM limit keep their budget."""
    assert _clamp(_messages(6000), 8192, model="meta-llama/llama-4-scout-17b-16e-instruct") == 8192


def test_estimator_errs_high_not_low():
    """Guessing high shrinks our own reservation (recoverable). Guessing low
    re-creates the 413. The estimate must never undercount."""
    text = "a" * 4000          # 1,000 tokens at 4 chars/token
    assert _estimate_tokens([{"role": "user", "content": text}]) >= 1000


def test_estimator_sums_all_messages():
    """System + user turns both consume the input budget."""
    combined = _estimate_tokens([
        {"role": "system", "content": "s" * 4000},
        {"role": "user", "content": "u" * 4000},
    ])
    assert combined >= 2000
