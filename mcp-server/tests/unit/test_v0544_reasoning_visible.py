"""
v0.5.44 "Reasoning Visible" — regression tests for the reasoning-exposure layer.

Covers:
- detail normalization (invalid → standard; case-insensitive)
- consult_steps: legacy "step" key; evidence only at full
- build_reasoning_block: structure, "n" step key, evidence/heavy fields only at full,
  inference.warning passthrough
- markdown report: inference_warning callout + ethics scoring breakdown render
"""

from datetime import datetime
from types import SimpleNamespace

import pytest

from verifimind_mcp.utils.reasoning_view import (
    normalize_detail,
    consult_steps,
    build_reasoning_block,
    DEFAULT_DETAIL,
)


# ---------- detail normalization ----------

@pytest.mark.parametrize("raw,expected", [
    ("summary", "summary"),
    ("standard", "standard"),
    ("full", "full"),
    ("FULL", "full"),
    ("  Standard  ", "standard"),
    ("bogus", "standard"),
    ("", "standard"),
    (None, "standard"),
])
def test_normalize_detail(raw, expected):
    assert normalize_detail(raw) == expected


def test_default_detail_is_standard():
    assert DEFAULT_DETAIL == "standard"


# ---------- consult_steps ----------

def _steps():
    return [
        SimpleNamespace(step_number=1, thought="t1", evidence="e1", confidence=0.9),
        SimpleNamespace(step_number=2, thought="t2", evidence=None, confidence=0.8),
    ]


def test_consult_steps_legacy_key_and_no_evidence_at_standard():
    out = consult_steps(_steps(), "standard")
    assert out[0] == {"step": 1, "thought": "t1", "confidence": 0.9}
    assert "evidence" not in out[0]


def test_consult_steps_evidence_only_at_full():
    out = consult_steps(_steps(), "full")
    assert out[0]["evidence"] == "e1"
    # step 2 had no evidence → key omitted, not null
    assert "evidence" not in out[1]


# ---------- build_reasoning_block ----------

def _x():
    return SimpleNamespace(
        reasoning_steps=_steps(), opportunities=["o1"], risks=["r1"],
        next_steps=["n1"], market_competition={"m": 1}, competitive_analysis={"c": 1},
    )


def _z():
    return SimpleNamespace(
        reasoning_steps=_steps(), scoring_breakdown={"ethical_alignment": {"score": 8}},
        jurisdiction_detected=["EU"], applicable_frameworks={"tier_1_international": ["UNESCO"]},
        compliance_timeline=["EU Art50: Aug 2026"], ethical_concerns=["ec1"],
        mitigation_measures=["m1"], total_frameworks_evaluated=5,
    )


def _cs():
    return SimpleNamespace(
        reasoning_steps=_steps(), threat_level="Medium Risk",
        socratic_questions=["[Assumption Challenge]: q1"], attack_vectors=["av1"],
        agentic_threats=["ASI01: x"], reasoning_layer_findings=["rl1"],
        security_recommendations=["sr1"], dimensions_evaluated={"traditional": {}},
        stages_completed=[{"stage": 1}], macp_security_assessment={"git_audit_trail": "N/A"},
        standards_referenced=["OWASP"],
    )


def _chain():
    return {"x_agent": "real", "z_agent": "real", "cs_agent": "real"}


def test_reasoning_block_structure_and_step_key():
    b = build_reasoning_block(_x(), _z(), _cs(), _chain(), "full", None, "standard")
    assert set(b.keys()) == {"detail", "x", "z", "cs", "inference"}
    # Trinity block uses "n" (not "step")
    assert b["x"]["steps"][0]["n"] == 1
    assert "step" not in b["x"]["steps"][0]


def test_standard_omits_evidence_and_heavy_fields():
    b = build_reasoning_block(_x(), _z(), _cs(), _chain(), "full", None, "standard")
    assert "evidence" not in b["z"]["steps"][0]
    # heavy/full-only fields absent at standard
    assert "market_competition" not in b["x"]
    assert "dimensions_evaluated" not in b["cs"]
    assert "total_frameworks_evaluated" not in b["z"]
    # but citations/breakdown present at standard (the differentiator)
    assert b["z"]["scoring_breakdown"] == {"ethical_alignment": {"score": 8}}
    assert b["z"]["jurisdiction_detected"] == ["EU"]
    assert b["cs"]["socratic_questions"] == ["[Assumption Challenge]: q1"]
    assert b["cs"]["threat_level"] == "Medium Risk"


def test_full_adds_evidence_and_heavy_fields():
    b = build_reasoning_block(_x(), _z(), _cs(), _chain(), "full", None, "full")
    assert b["z"]["steps"][0]["evidence"] == "e1"
    assert b["x"]["market_competition"] == {"m": 1}
    assert b["cs"]["dimensions_evaluated"] == {"traditional": {}}
    assert b["cs"]["macp_security_assessment"] == {"git_audit_trail": "N/A"}
    assert b["z"]["total_frameworks_evaluated"] == 5


def test_inference_block_passthrough():
    b = build_reasoning_block(_x(), _z(), _cs(), _chain(), "degraded",
                              "Ethics inference degraded — review required", "standard")
    assert b["inference"]["x"] == "real"
    assert b["inference"]["overall"] == "degraded"
    assert b["inference"]["warning"] == "Ethics inference degraded — review required"


# ---------- markdown report renders the new structured fields ----------

def test_markdown_renders_inference_warning_and_breakdown():
    from verifimind_mcp.models.reasoning import (
        ReasoningStep, XAgentAnalysis, ZAgentAnalysis, CSAgentAnalysis,
    )
    from verifimind_mcp.models.results import TrinityResult, TrinitySynthesis
    from verifimind_mcp.reporting.markdown_reporter import generate_markdown_report

    steps = [ReasoningStep(step_number=1, thought="t", evidence="e", confidence=0.8)]
    x = XAgentAnalysis(reasoning_steps=steps, innovation_score=7.0, strategic_value=7.0,
                       opportunities=["o"], risks=["r"], recommendation="ok", confidence=0.8)
    z = ZAgentAnalysis(reasoning_steps=steps, ethics_score=8.0, z_protocol_compliance=True,
                       ethical_concerns=["ec"], mitigation_measures=["m"], recommendation="ok",
                       veto_triggered=False, confidence=0.8,
                       jurisdiction_detected=["EU", "US"],
                       scoring_breakdown={"ethical_alignment": {"score": 8.0, "weight": 0.25, "frameworks": ["UNESCO-AI"]}})
    cs = CSAgentAnalysis(reasoning_steps=steps, security_score=7.0, vulnerabilities=["v"],
                         attack_vectors=["av"], security_recommendations=["sr"],
                         socratic_questions=["[Assumption Challenge]: q"], recommendation="ok",
                         confidence=0.8, threat_level="Medium Risk")
    synthesis = TrinitySynthesis(
        summary="s", innovation_score=7.0, ethics_score=8.0, security_score=7.0,
        overall_score=4.0, strengths=["st"], concerns=["c"], recommendations=["rec"],
        recommendation="revise", confidence=0.8,
        inference_warning="Ethics (Z) inference quality was 'fallback' — human review required.",
    )
    result = TrinityResult(
        validation_id="abc123", concept_name="C", concept_description="D",
        x_analysis=x, z_analysis=z, cs_analysis=cs, synthesis=synthesis,
        started_at=datetime.now(), completed_at=datetime.now(),
    )
    md = generate_markdown_report(result)
    assert "DEGRADED INFERENCE" in md
    assert "human review required" in md
    assert "Ethics Scoring Breakdown" in md
    assert "UNESCO-AI" in md
    assert "Jurisdictions detected" in md
    assert "Medium Risk" in md
    # generator stamp is the live version, not the stale 0.4.1
    assert "verifimind-peas/0.4.1" not in md
