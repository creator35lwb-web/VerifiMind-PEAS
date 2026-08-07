"""
Synthesis utilities for VerifiMind-PEAS MCP Server.

This module provides functions for synthesizing results from
multiple agent analyses into a unified Trinity result.
"""

import uuid
from datetime import datetime
from itertools import islice
from typing import Dict, List, Optional, Set

from ..models import (
    XAgentAnalysis,
    ZAgentAnalysis,
    CSAgentAnalysis,
    TrinitySynthesis,
    TrinityResult
)


REAL_INFERENCE_QUALITY = "real"


def _is_degraded_quality(quality: str) -> bool:
    """Every required stage must be explicitly real to clear the gate."""
    return quality != REAL_INFERENCE_QUALITY


def _degraded_agent_ids(quality_by_agent: Dict[str, str]) -> Set[str]:
    return {
        agent_id
        for agent_id, quality in quality_by_agent.items()
        if _is_degraded_quality(quality)
    }


def calculate_overall_score(
    x_result: XAgentAnalysis,
    z_result: ZAgentAnalysis,
    cs_result: CSAgentAnalysis,
    z_quality: str = "real",
    x_quality: str = "real",
    cs_quality: str = "real",
) -> float:
    """
    Calculate overall score from individual agent scores.

    Weights:
    - Innovation (X): 30%
    - Ethics (Z): 40% (higher weight for ethical considerations)
    - Security (CS): 30%

    If a real Z stage triggers veto, overall score is capped at 3.0.
    If any required agent inference was not explicitly real, one or more scores
    may be synthesized defaults. Cap the overall out of every auto-pass band.
    """
    # Base weighted average
    innovation_weight = 0.30
    ethics_weight = 0.40
    security_weight = 0.30

    # Average X scores
    x_score = (x_result.innovation_score + x_result.strategic_value) / 2

    weighted_score = (
        x_score * innovation_weight +
        z_result.ethics_score * ethics_weight +
        cs_result.security_score * security_weight
    )

    # A veto can influence the score only when it came from a real Z stage.
    if z_quality == REAL_INFERENCE_QUALITY and z_result.veto_triggered:
        weighted_score = min(weighted_score, 3.0)

    # Fail-safe symmetry: no required X/Z/CS stage may be absent, partial,
    # fallback, mock, unavailable, or unknown and still clear a concept.
    if any(
        _is_degraded_quality(quality)
        for quality in (x_quality, z_quality, cs_quality)
    ):
        weighted_score = min(weighted_score, 4.0)

    return round(weighted_score, 1)


def determine_recommendation(
    overall_score: float,
    z_result: ZAgentAnalysis,
    cs_result: CSAgentAnalysis,
    z_quality: str = "real",
    x_quality: str = "real",
    cs_quality: str = "real",
) -> str:
    """
    Determine overall recommendation based on scores and flags.

    Returns one of: "proceed", "proceed_with_caution", "revise", "reject"

    Fail-safe polarity (v0.5.56): a decision is complete only when every required
    X/Z/CS stage is explicitly real. No degraded result may be more permissive
    than REVISE, while a veto from a real Z stage remains a decisive REJECT.
    """
    # A trusted Z veto remains decisive even if another stage is degraded.
    if z_quality == REAL_INFERENCE_QUALITY and z_result.veto_triggered:
        return "reject"

    if any(
        _is_degraded_quality(quality)
        for quality in (x_quality, z_quality, cs_quality)
    ):
        return "revise"

    # High security vulnerabilities require revision
    if cs_result.security_score < 4.0:
        return "revise"

    # Score-based recommendations
    if overall_score >= 7.5:
        return "proceed"
    elif overall_score >= 5.5:
        return "proceed_with_caution"
    elif overall_score >= 4.0:
        return "revise"
    else:
        return "reject"


def synthesize_strengths(
    x_result: XAgentAnalysis,
    z_result: ZAgentAnalysis,
    cs_result: CSAgentAnalysis,
    degraded_agents: Optional[Set[str]] = None,
) -> List[str]:
    """Extract and synthesize key strengths from all analyses."""
    degraded_agents = degraded_agents or set()
    strengths = []
    
    # From X: High innovation or strategic value
    if "X" not in degraded_agents and x_result.innovation_score >= 7.0:
        strengths.append(f"High innovation potential (score: {x_result.innovation_score}/10)")
    if "X" not in degraded_agents and x_result.strategic_value >= 7.0:
        strengths.append(f"Strong strategic value (score: {x_result.strategic_value}/10)")
    
    # Add top opportunities from X
    if "X" not in degraded_agents:
        for opp in x_result.opportunities[:2]:
            strengths.append(f"Opportunity: {opp}")
    
    # From Z: Good ethics compliance
    if "Z" not in degraded_agents and z_result.z_protocol_compliance:
        strengths.append("Z-Protocol compliant")
    if "Z" not in degraded_agents and z_result.ethics_score >= 7.0:
        strengths.append(f"Strong ethical foundation (score: {z_result.ethics_score}/10)")
    
    # From CS: Good security
    if "CS" not in degraded_agents and cs_result.security_score >= 7.0:
        strengths.append(f"Solid security posture (score: {cs_result.security_score}/10)")
    
    return list(islice(strengths, 5))


def synthesize_concerns(
    x_result: XAgentAnalysis,
    z_result: ZAgentAnalysis,
    cs_result: CSAgentAnalysis,
    degraded_agents: Optional[Set[str]] = None,
) -> List[str]:
    """Extract and synthesize key concerns from all analyses."""
    degraded_agents = degraded_agents or set()
    concerns = []
    
    # From X: Risks
    if "X" not in degraded_agents:
        for risk in x_result.risks[:2]:
            concerns.append(f"Risk: {risk}")
    
    # From Z: Ethical concerns
    if "Z" not in degraded_agents:
        for concern in z_result.ethical_concerns[:2]:
            concerns.append(f"Ethical: {concern}")
    
    # Veto is a major concern
    if "Z" not in degraded_agents and z_result.veto_triggered:
        concerns.insert(0, "VETO TRIGGERED: Ethical red line crossed")
    
    # From CS: Vulnerabilities
    if "CS" not in degraded_agents:
        for vuln in cs_result.vulnerabilities[:2]:
            concerns.append(f"Security: {vuln}")

    for agent_id in sorted(degraded_agents):
        concerns.insert(0, f"{agent_id} analysis incomplete — human review required")
    
    return concerns[:5]  # Limit to top 5


def synthesize_recommendations(
    x_result: XAgentAnalysis,
    z_result: ZAgentAnalysis,
    cs_result: CSAgentAnalysis,
    degraded_agents: Optional[Set[str]] = None,
) -> List[str]:
    """Synthesize actionable recommendations from all analyses."""
    degraded_agents = degraded_agents or set()
    recommendations = []
    
    # Add agent recommendations
    if "X" not in degraded_agents:
        recommendations.append(f"X Intelligent: {x_result.recommendation}")
    if "Z" not in degraded_agents:
        recommendations.append(f"Z Guardian: {z_result.recommendation}")
    if "CS" not in degraded_agents:
        recommendations.append(f"CS Security: {cs_result.recommendation}")
    
    # Add specific mitigations from Z
    if "Z" not in degraded_agents:
        for mitigation in z_result.mitigation_measures[:2]:
            recommendations.append(f"Mitigation: {mitigation}")
    
    # Add security recommendations from CS
    if "CS" not in degraded_agents:
        for sec_rec in cs_result.security_recommendations[:2]:
            recommendations.append(f"Security: {sec_rec}")

    if degraded_agents:
        recommendations.insert(
            0,
            "Repeat the incomplete agent checks before making an implementation decision.",
        )
    
    return list(islice(recommendations, 7))


def build_founder_summary(
    overall_score: float,
    recommendation: str,
    x_result: XAgentAnalysis,
    z_result: ZAgentAnalysis,
    cs_result: CSAgentAnalysis,
    degraded_agents: Optional[Set[str]] = None,
    trusted_veto: Optional[bool] = None,
) -> dict:
    """
    Build a plain-language founder summary — no jargon, actionable guidance.

    Translates Trinity scores and findings into language a non-technical
    founder or first-time entrepreneur can read and act on immediately.
    """
    degraded_agents = degraded_agents or set()
    if trusted_veto is None:
        trusted_veto = (
            "Z" not in degraded_agents and bool(z_result.veto_triggered)
        )

    # Verdict line
    verdict_map = {
        "proceed": "Your idea looks solid. The main risk is execution — go build it.",
        "proceed_with_caution": "Your idea has real potential, but there are a few things to address before you go all in.",
        "revise": "The core idea has merit, but in its current form there are significant issues to work through first.",
        "reject": "As described, this concept has critical problems that would need to be fundamentally rethought.",
    }
    if trusted_veto:
        verdict_line = f"STOPPED: {z_result.ethical_concerns[0] if z_result.ethical_concerns else 'This concept crosses an ethical red line and cannot proceed as described.'}"
    else:
        verdict_line = verdict_map.get(recommendation, "See full analysis for details.")

    # What's working (plain language)
    whats_working = []
    if "X" not in degraded_agents:
        for opp in x_result.opportunities[:2]:
            whats_working.append(opp)
    if "Z" not in degraded_agents and z_result.ethics_score >= 7.0:
        if z_result.ethical_concerns:
            whats_working.append(
                "No Z-Protocol veto was triggered; review the listed ethical "
                "concerns and mitigations."
            )
        else:
            whats_working.append(
                "No major ethical or legal concerns were identified in this review."
            )
    if "CS" not in degraded_agents and cs_result.security_score >= 7.0:
        if cs_result.vulnerabilities:
            whats_working.append(
                "No critical security blocker was identified; review the listed "
                "vulnerabilities and recommendations."
            )
        else:
            whats_working.append(
                "No significant security risks were identified in this review."
            )

    # Things to think about (plain language, merged from all agents)
    things_to_address = []
    if "X" not in degraded_agents:
        for risk in x_result.risks[:2]:
            things_to_address.append(risk)
    if "Z" not in degraded_agents:
        for concern in z_result.ethical_concerns[:1]:
            things_to_address.append(concern)
    if "CS" not in degraded_agents:
        for vuln in cs_result.vulnerabilities[:1]:
            things_to_address.append(vuln)
    for agent_id in sorted(degraded_agents):
        things_to_address.insert(
            0, f"{agent_id} did not complete a trustworthy analysis."
        )

    # Next steps (from X if available, else synthesized)
    next_steps = (
        getattr(x_result, 'next_steps', None) or []
        if "X" not in degraded_agents
        else []
    )
    if not next_steps and "X" not in degraded_agents:
        next_steps = [r for r in x_result.risks[:2]]  # fallback
    if degraded_agents:
        next_steps.insert(0, "Repeat the incomplete Trinity checks before proceeding.")

    # Research continuation — Perplexity/Grok queries from X Agent
    research_prompts = (
        getattr(x_result, 'research_prompts', None) or []
        if "X" not in degraded_agents
        else []
    )
    research_continuation = None
    if research_prompts:
        research_continuation = {
            "message": (
                "Your validation is based on what's been described. To go deeper, "
                "paste these queries into Perplexity.ai or Grok for real-time market intelligence:"
            ),
            "queries": research_prompts[:3],
        }

    return {
        "verdict": verdict_line,
        "score_plain": f"{overall_score}/10",
        "what_works": whats_working[:3],
        "things_to_address": things_to_address[:3],
        "next_steps": next_steps[:3],
        "research_continuation": research_continuation,
    }


def create_synthesis(
    x_result: XAgentAnalysis,
    z_result: ZAgentAnalysis,
    cs_result: CSAgentAnalysis
) -> TrinitySynthesis:
    """
    Create a complete synthesis from all three agent analyses.

    This is the core synthesis function that combines all perspectives
    into a unified assessment.
    """
    quality_by_agent = {
        "X": getattr(x_result, "_inference_quality", "unknown"),
        "Z": getattr(z_result, "_inference_quality", "unknown"),
        "CS": getattr(cs_result, "_inference_quality", "unknown"),
    }
    degraded_agents = _degraded_agent_ids(quality_by_agent)

    calculated_score = calculate_overall_score(
        x_result,
        z_result,
        cs_result,
        z_quality=quality_by_agent["Z"],
        x_quality=quality_by_agent["X"],
        cs_quality=quality_by_agent["CS"],
    )
    recommendation = determine_recommendation(
        calculated_score,
        z_result,
        cs_result,
        z_quality=quality_by_agent["Z"],
        x_quality=quality_by_agent["X"],
        cs_quality=quality_by_agent["CS"],
    )

    inference_warning = None
    if degraded_agents:
        quality_details = ", ".join(
            f"{agent_id}='{quality_by_agent[agent_id]}'"
            for agent_id in sorted(degraded_agents)
        )
        inference_warning = (
            f"Required Trinity inference was degraded ({quality_details}). Scores or "
            "findings from those stages may be synthesized defaults rather than genuine "
            "analysis. Recommendation is restricted to REVISE, or REJECT when a real Z "
            "veto is present; aggregate confidence has been withheld and a human must "
            "review before this concept proceeds."
        )

    # Build summary
    summary_parts = []

    if inference_warning:
        summary_parts.append("⚠️ DEGRADED TRINITY INFERENCE — human review required")

    trusted_veto = "Z" not in degraded_agents and z_result.veto_triggered
    if trusted_veto:
        summary_parts.append("VETO TRIGGERED by Z Guardian.")
        summary_parts.append(f"Reason: {z_result.ethical_concerns[0] if z_result.ethical_concerns else 'Ethical red line crossed'}")
    else:
        summary_parts.append(f"Overall assessment: {recommendation.upper()}")

    summary_parts.append(
        "Innovation: unavailable"
        if "X" in degraded_agents
        else f"Innovation: {x_result.innovation_score}/10"
    )
    summary_parts.append(
        "Ethics: unavailable"
        if "Z" in degraded_agents
        else f"Ethics: {z_result.ethics_score}/10"
    )
    summary_parts.append(
        "Security: unavailable"
        if "CS" in degraded_agents
        else f"Security: {cs_result.security_score}/10"
    )

    summary = " | ".join(summary_parts)

    # Calculate average confidence
    avg_confidence = None
    if not degraded_agents:
        avg_confidence = round((
            x_result.confidence +
            z_result.confidence +
            cs_result.confidence
        ) / 3, 2)

    founder_summary = build_founder_summary(
        calculated_score,
        recommendation,
        x_result,
        z_result,
        cs_result,
        degraded_agents,
        trusted_veto=trusted_veto,
    )
    # Surface the degraded-inference caveat at the top of the founder verdict too
    if inference_warning and isinstance(founder_summary, dict):
        founder_summary["verdict"] = (
            "NEEDS HUMAN REVIEW: one or more required Trinity checks did not "
            "complete cleanly, so this result is not trustworthy on its own. "
            + founder_summary.get("verdict", "")
        ).strip()

    synthesis = TrinitySynthesis(
        summary=summary,
        innovation_score=(
            x_result.innovation_score if "X" not in degraded_agents else None
        ),
        ethics_score=(
            z_result.ethics_score if "Z" not in degraded_agents else None
        ),
        security_score=(
            cs_result.security_score if "CS" not in degraded_agents else None
        ),
        overall_score=(calculated_score if not degraded_agents else None),
        strengths=synthesize_strengths(
            x_result, z_result, cs_result, degraded_agents
        ),
        concerns=synthesize_concerns(
            x_result, z_result, cs_result, degraded_agents
        ),
        recommendations=synthesize_recommendations(
            x_result, z_result, cs_result, degraded_agents
        ),
        recommendation=recommendation,
        confidence=avg_confidence,
        confidence_valid=not degraded_agents,
        analysis_incomplete=bool(degraded_agents),
        degraded_agents=sorted(degraded_agents),
        quality_gate={
            "passed": not degraded_agents,
            "required_quality": REAL_INFERENCE_QUALITY,
            "agents": quality_by_agent,
            "degraded_agents": sorted(degraded_agents),
        },
        veto_triggered=(z_result.veto_triggered if "Z" not in degraded_agents else None),
        veto_reason=(
            z_result.ethical_concerns[0]
            if trusted_veto and z_result.ethical_concerns
            else None
        ),
        founder_summary=founder_summary,
        inference_warning=inference_warning,
    )

    return synthesis


def create_trinity_result(
    concept_name: str,
    concept_description: str,
    x_result: XAgentAnalysis,
    z_result: ZAgentAnalysis,
    cs_result: CSAgentAnalysis
) -> TrinityResult:
    """
    Create a complete Trinity validation result.
    
    This is the main function called by run_full_trinity to
    package all results into a single response.
    """
    synthesis = create_synthesis(x_result, z_result, cs_result)
    
    return TrinityResult(
        validation_id=str(uuid.uuid4())[:8],
        concept_name=concept_name,
        concept_description=concept_description,
        x_analysis=x_result,
        z_analysis=z_result,
        cs_analysis=cs_result,
        synthesis=synthesis,
        human_decision_required=True,
        started_at=datetime.now(),
        completed_at=datetime.now()
    )
