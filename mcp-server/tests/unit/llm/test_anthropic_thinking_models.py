"""
Anthropic BYOK on extended-thinking models (Claude 5 family) — RNA S106
=======================================================================

Both defects below were found by DOGFOODING: running a real Z Guardian
privacy/legal assessment through the production BYOK path on `claude-opus-5`.
Neither was reachable by the existing suite, because every Anthropic test used
a mock whose response shape was copied from a NON-thinking model — the mock
encoded the assumption that was wrong.

Defect 1 — `'ThinkingBlock' object has no attribute 'text'`
    Anthropic returns a LIST of typed content blocks. Extended-thinking models
    emit a `thinking` block FIRST, so `response.content[0].text` raised and
    BYOK failed for every Claude 5 model. Fix: select by TYPE, not POSITION.

Defect 2 — silent truncation blamed on the model
    Thinking tokens are drawn from the SAME `max_tokens` budget as the answer.
    Measured: 5,437 thinking tokens on one real call. At the agents' 8,192
    budget the JSON answer was cut mid-object, and the parser reported it as
    the model returning malformed output — our accounting error, attributed to
    the model. Fix: add a thinking allowance, and fail LOUD on
    `stop_reason == "max_tokens"` instead of parsing a partial response.
"""

import pytest

from verifimind_mcp.llm.provider import (
    PROVIDER_CONFIGS,
    _first_text_block,
    _thinking_aware_max_tokens,
)


class _Block:
    """Minimal stand-in for an Anthropic content block."""

    def __init__(self, type_, text=None):
        self.type = type_
        if text is not None:
            self.text = text


# --- Defect 1: block selection by type, not position ------------------------

def test_thinking_block_first_does_not_break_extraction():
    """The exact production failure shape: thinking block at index 0."""
    blocks = [_Block("thinking"), _Block("text", "ANSWER")]
    assert _first_text_block(blocks) == "ANSWER"


def test_legacy_text_first_still_works():
    """Non-thinking models (the 4.x line) must be unaffected."""
    assert _first_text_block([_Block("text", "ANSWER")]) == "ANSWER"


def test_thinking_content_never_leaks_as_the_answer():
    """A thinking block carrying text is a scratchpad, not the response. It
    must never be returned to a caller as if it were the model's answer."""
    thinking = _Block("thinking", "SCRATCHPAD — do not surface")
    blocks = [thinking, _Block("text", "REAL ANSWER")]
    assert _first_text_block(blocks) == "REAL ANSWER"


def test_multiple_text_blocks_are_concatenated_in_order():
    blocks = [_Block("thinking"), _Block("text", "part one "), _Block("text", "part two")]
    assert _first_text_block(blocks) == "part one part two"


def test_no_text_block_fails_loud_rather_than_returning_empty():
    """Returning "" would surface downstream as a malformed model answer,
    hiding the real cause. The error must name the block types seen."""
    with pytest.raises(ValueError) as exc:
        _first_text_block([_Block("thinking")])
    assert "thinking" in str(exc.value)


# --- Defect 2: thinking-aware token budget ----------------------------------

@pytest.mark.parametrize("model", ["claude-opus-5", "claude-sonnet-5", "claude-fable-5"])
def test_thinking_models_receive_an_allowance_above_the_requested_budget(model):
    """Callers size max_tokens for the ANSWER. On a thinking model the budget
    must additionally cover the scratchpad, or the answer is truncated."""
    assert _thinking_aware_max_tokens(model, 8192) > 8192


@pytest.mark.parametrize("model", ["claude-sonnet-4-6", "claude-opus-4-8",
                                   "claude-haiku-4-5-20251001"])
def test_non_thinking_models_budget_is_unchanged(model):
    """Platform-scoped: the allowance must not silently inflate spend on
    models that do not emit thinking blocks."""
    assert _thinking_aware_max_tokens(model, 8192) == 8192


def test_allowance_covers_the_measured_real_world_thinking_usage():
    """Known-positive against a MEASURED value: a real Z-agent assessment
    consumed 5,437 thinking tokens. The allowance must exceed it, or the
    fix does not actually fix the case that produced it."""
    measured_thinking_tokens = 5437
    headroom = _thinking_aware_max_tokens("claude-opus-5", 8192) - 8192
    assert headroom > measured_thinking_tokens


# --- Model currency ---------------------------------------------------------

@pytest.mark.parametrize("model_id", ["claude-opus-5", "claude-sonnet-5", "claude-fable-5"])
def test_claude_5_family_is_offered_for_byok(model_id):
    """Live-verified available on a real key 2026-07-29. Absent from the list,
    the BYOK contract advertises a generation-stale model set."""
    assert model_id in PROVIDER_CONFIGS["anthropic"]["models"]


def test_default_model_change_stays_a_deliberate_decision():
    """Adding IDs to the offered list must not silently move the DEFAULT — a
    default change alters cost and behaviour for every non-BYOK caller and
    belongs to a reviewed version bump, not to a currency refresh."""
    assert PROVIDER_CONFIGS["anthropic"]["default_model"] == "claude-sonnet-4-6"
