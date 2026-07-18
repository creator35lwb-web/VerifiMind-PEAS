"""
v0.5.50 Robustness Pass — synthesis decision-boundary contract
==============================================================

Foundation Inspection pass 1, batch 2 (Hub #81, T scoping: "synthesis decision
tests around score-to-verdict behavior, caps, inference_warning, and the M3/M4
synthesis bottleneck").

Pins the EXACT decision surface of utils/synthesis.py so any M4 recalibration
(threshold shift, SGDV) must consciously change these tests — the boundaries
become a versioned contract instead of an implicit constant:

  weights 30/40/30 (X-avg / Z / CS) · veto -> cap 3.0 + reject
  degraded-Z (partial|fallback) -> cap 4.0 + revise ("mock" excluded by design)
  CS < 4.0 -> revise · thresholds: >=7.5 proceed / >=5.5 caution / >=4.0 revise

The 5.5-7.4 band IS the M3-identified "REVISE-hedge" territory; M4's SGDV/
recalibration work targets exactly these constants.
"""

import pytest

from verifimind_mcp.models.reasoning import (
    XAgentAnalysis,
    ZAgentAnalysis,
    CSAgentAnalysis,
    ReasoningStep,
)
from verifimind_mcp.utils.synthesis import (
    calculate_overall_score,
    determine_recommendation,
)


def _step():
    return [ReasoningStep(step_number=1, thought="t", confidence=0.9)]


def x(innov: float, strat: float | None = None) -> XAgentAnalysis:
    return XAgentAnalysis(
        reasoning_steps=_step(), innovation_score=innov,
        strategic_value=strat if strat is not None else innov,
        opportunities=[], risks=[], recommendation="r", confidence=0.9,
    )


def z(score: float, veto: bool = False) -> ZAgentAnalysis:
    return ZAgentAnalysis(
        reasoning_steps=_step(), ethics_score=score, z_protocol_compliance=not veto,
        ethical_concerns=[], mitigation_measures=[], recommendation="r",
        veto_triggered=veto, confidence=0.9,
    )


def cs(score: float) -> CSAgentAnalysis:
    return CSAgentAnalysis(
        reasoning_steps=_step(), security_score=score, vulnerabilities=[],
        attack_vectors=[], security_recommendations=[], socratic_questions=[],
        recommendation="r", confidence=0.9,
    )


def uniform(v: float):
    """X-avg == Z == CS == v  ->  overall == v exactly (30/40/30 weights)."""
    return x(v), z(v), cs(v)


# ---------------------------------------------------------------------------
# Weighting math
# ---------------------------------------------------------------------------

def test_weights_30_40_30():
    # X-avg=6 (0.3*6=1.8) + Z=8 (0.4*8=3.2) + CS=5 (0.3*5=1.5) = 6.5
    assert calculate_overall_score(x(4, 8), z(8), cs(5)) == 6.5


def test_x_score_is_mean_of_innovation_and_strategic():
    assert calculate_overall_score(x(10, 0), z(5), cs(5)) == \
           calculate_overall_score(x(5, 5), z(5), cs(5))


def test_uniform_scores_pass_through():
    for v in (0.0, 4.0, 5.5, 7.5, 10.0):
        xa, za, ca = uniform(v)
        assert calculate_overall_score(xa, za, ca) == v


# ---------------------------------------------------------------------------
# Verdict thresholds — exact boundaries (the M4 target constants)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("overall,expected", [
    (7.5, "proceed"),               # boundary: >= 7.5
    (7.4, "proceed_with_caution"),
    (5.5, "proceed_with_caution"),  # boundary: >= 5.5
    (5.4, "revise"),
    (4.0, "revise"),                # boundary: >= 4.0
])
def test_verdict_thresholds_exact(overall, expected):
    xa, za, ca = uniform(overall)
    score = calculate_overall_score(xa, za, ca)
    assert score == overall
    assert determine_recommendation(score, za, ca) == expected


def test_reject_branch_requires_cs_at_least_4():
    """CONTRACT DISCOVERY (this suite's first run): the CS gate (<4.0 -> revise)
    sits ABOVE the score ladder, so a uniformly-low concept (CS<4) reads
    'revise', never 'reject'. The reject branch is reachable only when CS>=4.0
    but the weighted total still falls under 4.0 (X-avg and Z very low)."""
    # uniform 3.9: CS gate intercepts -> revise (NOT reject)
    xa, za, ca = uniform(3.9)
    assert determine_recommendation(3.9, za, ca) == "revise"
    # CS=4.0, X=0, Z=0 -> overall = 0*0.3 + 0*0.4 + 4.0*0.3 = 1.2 -> reject
    za0, ca4 = z(0.0), cs(4.0)
    score = calculate_overall_score(x(0.0), za0, ca4)
    assert score == 1.2
    assert determine_recommendation(score, za0, ca4) == "reject"


def test_revise_hedge_band_is_5_5_to_7_4():
    """The M3-identified hedge band: uniform seat scores of 6 and 7 both land
    in proceed_with_caution — the discrimination-collapse zone M4 targets."""
    for v in (6.0, 7.0):
        xa, za, ca = uniform(v)
        assert determine_recommendation(v, za, ca) == "proceed_with_caution"


# ---------------------------------------------------------------------------
# Veto: cap 3.0 + unconditional reject (beats everything)
# ---------------------------------------------------------------------------

def test_veto_caps_score_at_3():
    assert calculate_overall_score(x(10), z(10, veto=True), cs(10)) == 3.0


def test_veto_forces_reject_even_with_high_scores():
    za = z(10, veto=True)
    assert determine_recommendation(10.0, za, cs(10)) == "reject"


def test_veto_beats_degraded_z():
    za = z(10, veto=True)
    assert determine_recommendation(10.0, za, cs(10), z_quality="fallback") == "reject"


# ---------------------------------------------------------------------------
# Degraded-Z fail-safe (v0.5.43): partial/fallback -> cap 4.0 + revise
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("quality", ["partial", "fallback"])
def test_degraded_z_caps_score_at_4(quality):
    assert calculate_overall_score(x(10), z(10), cs(10), z_quality=quality) == 4.0


@pytest.mark.parametrize("quality", ["partial", "fallback"])
def test_degraded_z_forces_revise_even_at_perfect_scores(quality):
    assert determine_recommendation(10.0, z(10), cs(10), z_quality=quality) == "revise"


def test_mock_quality_is_excluded_from_the_fail_safe():
    """'mock' is test-mode with its own synthetic warning — by design it does
    NOT trigger the degraded cap (documented exclusion, v0.5.43)."""
    assert calculate_overall_score(x(10), z(10), cs(10), z_quality="mock") == 10.0
    assert determine_recommendation(10.0, z(10), cs(10), z_quality="mock") == "proceed"


# ---------------------------------------------------------------------------
# CS security gate: < 4.0 forces revise regardless of overall
# ---------------------------------------------------------------------------

def test_low_security_forces_revise_despite_high_overall():
    ca = cs(3.9)
    assert determine_recommendation(9.0, z(10), ca) == "revise"


def test_security_gate_boundary_4_0_does_not_trip():
    ca = cs(4.0)
    assert determine_recommendation(9.0, z(10), ca) == "proceed"
