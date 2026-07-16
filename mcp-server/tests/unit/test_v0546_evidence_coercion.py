"""
v0.5.46 — BYOK evidence/thought coercion (provider output-format robustness).

Reproduces the M2 P3 failure: mistral-small returned CS per-step `evidence` as a
nested dict, crashing CSAgentAnalysis validation. The ReasoningStep `before` validator
now coerces dict/list → JSON string so any BYOK provider's structured reasoning is
preserved instead of failing validation.
"""

import json

from verifimind_mcp.models.reasoning import ReasoningStep, CSAgentAnalysis


def test_dict_evidence_coerced_to_json_string():
    step = ReasoningStep(step_number=1, thought="t", evidence={"prove": "a", "disprove": "b"}, confidence=0.9)
    assert isinstance(step.evidence, str)
    assert json.loads(step.evidence) == {"prove": "a", "disprove": "b"}


def test_list_evidence_coerced():
    step = ReasoningStep(step_number=1, thought="t", evidence=["x", "y"], confidence=0.8)
    assert isinstance(step.evidence, str)
    assert json.loads(step.evidence) == ["x", "y"]


def test_string_evidence_unchanged():
    step = ReasoningStep(step_number=1, thought="t", evidence="plain string", confidence=0.8)
    assert step.evidence == "plain string"


def test_none_evidence_stays_none():
    step = ReasoningStep(step_number=1, thought="t", evidence=None, confidence=0.8)
    assert step.evidence is None


def test_dict_thought_coerced():
    step = ReasoningStep(step_number=1, thought={"FOR": ["a"], "AGAINST": ["b"]}, confidence=0.8)
    assert isinstance(step.thought, str)
    assert json.loads(step.thought) == {"FOR": ["a"], "AGAINST": ["b"]}


def test_cs_agent_analysis_with_dict_evidence_validates():
    """The exact M2 P3 repro: a CS reasoning step with dict evidence must now validate."""
    cs = CSAgentAnalysis(
        reasoning_steps=[
            ReasoningStep(step_number=1, thought="stage 1", evidence="ok", confidence=0.9),
            ReasoningStep(step_number=2, thought="stage 2",
                          evidence={"disprove": "false-positive scenario", "prove": "exploit scenario"},
                          confidence=0.85),
        ],
        security_score=7.0,
        vulnerabilities=["v1"],
        attack_vectors=["av1"],
        security_recommendations=["sr1"],
        socratic_questions=["[Assumption Challenge]: q1", "[Boundary Probe]: q2"],
        recommendation="proceed after hardening",
        confidence=0.85,
    )
    assert isinstance(cs.reasoning_steps[1].evidence, str)
    assert "disprove" in cs.reasoning_steps[1].evidence
