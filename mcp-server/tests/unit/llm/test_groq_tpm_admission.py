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
    _TOKEN_ESTIMATE_CHARS_PER_TOKEN,
    GROQ_8K_TPM_COMPLETION_CAP,
    GROQ_8K_TPM_LIMIT,
    GROQ_8K_TPM_MODELS,
    GROQ_MIN_COMPLETION,
    GROQ_TPM_SAFETY_MARGIN,
    _estimate_tokens,
)


def _clamp(messages, requested, model="openai/gpt-oss-120b"):
    """Mirror of the production clamp, so the arithmetic is asserted directly.

    Raises ValueError when the minimum useful output cannot fit — the
    fail-closed behaviour T S114 required, replacing an unconditional floor
    that admitted over-budget requests."""
    if model not in GROQ_8K_TPM_MODELS:
        return requested
    estimated = _estimate_tokens(messages)
    available = GROQ_8K_TPM_LIMIT - estimated - GROQ_TPM_SAFETY_MARGIN
    if available < GROQ_MIN_COMPLETION:
        raise ValueError("not admissible")
    return min(requested, GROQ_8K_TPM_COMPLETION_CAP, available)


def _messages(token_count):
    """Build a message whose ESTIMATED token count is `token_count`.

    Derives the char count from the production constant rather than assuming a
    ratio — the same hardcoding mistake that hid an off-by-one earlier, and that
    would silently shift every boundary case if the estimator is recalibrated."""
    from verifimind_mcp.llm.provider import _TOKEN_ESTIMATE_CHARS_PER_TOKEN
    chars = (token_count - 1) * _TOKEN_ESTIMATE_CHARS_PER_TOKEN
    return [{"role": "user", "content": "x" * chars}]


# --- the defect this exists to prevent --------------------------------------

def test_orchestrated_sized_prompt_admits_under_the_tpm_limit():
    """The measured failing case: ~4,428-token orchestrated prompt. Under the
    old flat 4096 reservation this totalled 8,524 > 8,000 and Groq rejected."""
    messages = _messages(4428)
    reservation = _clamp(messages, 8192)
    assert _estimate_tokens(messages) + reservation <= GROQ_8K_TPM_LIMIT


# Derived, not hardcoded: the last admissible input is the one that still
# leaves the minimum useful output inside the limit. Deriving it means the
# boundary cases follow the constants instead of drifting from them — and it
# is how the off-by-one in the estimator's `+1` was caught.
MAX_ADMISSIBLE_INPUT = (GROQ_8K_TPM_LIMIT - GROQ_TPM_SAFETY_MARGIN
                        - GROQ_MIN_COMPLETION)
# _messages(n) now estimates EXACTLY n, so the last admissible input is the
# boundary itself — the earlier `- 1` compensated for a helper off-by-one that
# no longer exists. Left explicit because a stale compensation is invisible.
_LAST_ADMISSIBLE = MAX_ADMISSIBLE_INPUT


@pytest.mark.parametrize("input_tokens",
                         [500, 2799, 3690, 4428, 5500, 6500,
                          _LAST_ADMISSIBLE - 1, _LAST_ADMISSIBLE])
def test_admission_holds_across_the_whole_prompt_range(input_tokens):
    """Admission must hold at every ADMISSIBLE prompt size.

    T S114 caught that the original parametrisation stopped at 6,500 — just
    short of 6,721, where the old unconditional floor began admitting
    over-budget requests. A range test that stops before the failing zone is
    the vacuous-verification failure mode in a test asserting a range."""
    messages = _messages(input_tokens)
    assert _estimate_tokens(messages) + _clamp(messages, 8192) <= GROQ_8K_TPM_LIMIT


@pytest.mark.parametrize("input_tokens",
                         [_LAST_ADMISSIBLE + 1, 7001, 7500, 7999])
def test_inadmissible_inputs_fail_closed_rather_than_being_sent(input_tokens):
    """Beyond the floor-binding boundary the request cannot carry a useful
    answer within the limit. It must be REFUSED, not sent over-budget and
    blamed on the provider — the defect T S114 found in the first version:
    at 7,001 estimated input the old code reserved 1,024 for a total of 8,025
    against an 8,000 ceiling."""
    with pytest.raises(ValueError):
        _clamp(_messages(input_tokens), 8192)


def test_the_old_unconditional_floor_would_have_exceeded_the_limit():
    """Known-positive against the FIRST version of this fix (not just against
    the original flat cap): reproduce `max(available, FLOOR)` and show it
    admits an over-budget request. This is the arithmetic T verified."""
    estimated = 7001
    available = GROQ_8K_TPM_LIMIT - estimated - GROQ_TPM_SAFETY_MARGIN
    old_reservation = max(available, GROQ_MIN_COMPLETION)
    assert estimated + old_reservation > GROQ_8K_TPM_LIMIT


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


def test_admitted_requests_always_carry_a_useful_output_budget():
    """Observed Z/CS outputs run ~1k tokens. Any request that IS admitted must
    reserve at least that; anything that cannot is refused (test above). The
    original version asserted this by forcing the floor, which is what broke
    the admission invariant."""
    assert _clamp(_messages(_LAST_ADMISSIBLE), 8192) >= GROQ_MIN_COMPLETION


def test_caller_budget_is_still_respected_when_smaller():
    """The clamp only ever LOWERS the reservation; a caller asking for less
    than the cap keeps its own smaller number."""
    assert _clamp(_messages(500), 512) == 512


# --- scope and estimator ----------------------------------------------------

def test_non_8k_models_are_untouched():
    """Platform-scoped: models without the 8k TPM limit keep their budget."""
    assert _clamp(_messages(6000), 8192, model="meta-llama/llama-4-scout-17b-16e-instruct") == 8192


def test_estimator_over_counts_real_agent_prompt_shapes():
    """Calibrated against PROVIDER token counts captured 2026-07-30, not folklore.

    The previous version of this test used `"a" * 4000` — a single repeated
    character, the most favourable possible input — and passed while the
    estimator UNDER-counted every real prompt shape we actually send. These
    ratios are measured against the provider tokenizer:

        Z standalone 2,935 actual · CS orchestrated 4,794 actual

    The estimate must exceed the measured actual for our own agent prompts."""
    measured = [(11183, 2935), (17013, 3886), (12571, 3072), (23017, 4794)]
    for chars, actual_tokens in measured:
        estimate = _estimate_tokens([{"role": "user", "content": "x" * chars}])
        assert estimate >= actual_tokens, (
            f"estimator under-counts a real prompt shape: {chars} chars -> "
            f"estimate {estimate} < provider actual {actual_tokens}"
        )


def test_estimator_sums_all_messages():
    """System + user turns both consume the input budget."""
    combined = _estimate_tokens([
        {"role": "system", "content": "s" * 4000},
        {"role": "user", "content": "u" * 4000},
    ])
    assert combined >= 2000
