"""
Synthesis utilities for VerifiMind-PEAS MCP Server.

This module provides functions for synthesizing results from
multiple agent analyses into a unified Trinity result.
"""

import uuid
from datetime import datetime
from typing import List

from ..models import (
    XAgentAnalysis,
    ZAgentAnalysis,
    CSAgentAnalysis,
    TrinitySynthesis,
    TrinityResult
)


def calculate_overall_score(
    x_result: XAgentAnalysis,
    z_result: ZAgentAnalysis,
    cs_result: CSAgentAnalysis
) -> float:
    """
    Calculate overall score from individual agent scores.
    
    Weights:
    - Innovation (X): 30%
    - Ethics (Z): 40% (higher weight for ethical considerations)
    - Security (CS): 30%
    
    If Z triggers veto, overall score is capped at 3.0.
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
    
    # Cap score if veto triggered
    if z_result.veto_triggered:
        weighted_score = min(weighted_score, 3.0)
    
    return round(weighted_score, 1)


def determine_recommendation(
    overall_score: float,
    z_result: ZAgentAnalysis,
    cs_result: CSAgentAnalysis
) -> str:
    """
    Determine overall recommendation based on scores and flags.
    
    Returns one of: "proceed", "proceed_with_caution", "revise", "reject"
    """
    # Veto always results in reject
    if z_result.veto_triggered:
        return "reject"
    
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
    cs_result: CSAgentAnalysis
) -> List[str]:
    """Extract and synthesize key strengths from all analyses."""
    strengths = []
    
    # From X: High innovation or strategic value
    if x_result.innovation_score >= 7.0:
        strengths.append(f"High innovation potential (score: {x_result.innovation_score}/10)")
    if x_result.strategic_value >= 7.0:
        strengths.append(f"Strong strategic value (score: {x_result.strategic_value}/10)")
    
    # Add top opportunities from X
    for opp in x_result.opportunities[:2]:
        strengths.append(f"Opportunity: {opp}")
    
    # From Z: Good ethics compliance
    if z_result.z_protocol_compliance:
        strengths.append("Z-Protocol compliant")
    if z_result.ethics_score >= 7.0:
        strengths.append(f"Strong ethical foundation (score: {z_result.ethics_score}/10)")
    
    # From CS: Good security
    if cs_result.security_score >= 7.0:
        strengths.append(f"Solid security posture (score: {cs_result.security_score}/10)")
    
    return strengths[:5]  # Limit to top 5


def synthesize_concerns(
    x_result: XAgentAnalysis,
    z_result: ZAgentAnalysis,
    cs_result: CSAgentAnalysis
) -> List[str]:
    """Extract and synthesize key concerns from all analyses."""
    concerns = []
    
    # From X: Risks
    for risk in x_result.risks[:2]:
        concerns.append(f"Risk: {risk}")
    
    # From Z: Ethical concerns
    for concern in z_result.ethical_concerns[:2]:
        concerns.append(f"Ethical: {concern}")
    
    # Veto is a major concern
    if z_result.veto_triggered:
        concerns.insert(0, "VETO TRIGGERED: Ethical red line crossed")
    
    # From CS: Vulnerabilities
    for vuln in cs_result.vulnerabilities[:2]:
        concerns.append(f"Security: {vuln}")
    
    return concerns[:5]  # Limit to top 5


def synthesize_recommendations(
    x_result: XAgentAnalysis,
    z_result: ZAgentAnalysis,
    cs_result: CSAgentAnalysis
) -> List[str]:
    """Synthesize actionable recommendations from all analyses."""
    recommendations = []
    
    # Add agent recommendations
    recommendations.append(f"X Intelligent: {x_result.recommendation}")
    recommendations.append(f"Z Guardian: {z_result.recommendation}")
    recommendations.append(f"CS Security: {cs_result.recommendation}")
    
    # Add specific mitigations from Z
    for mitigation in z_result.mitigation_measures[:2]:
        recommendations.append(f"Mitigation: {mitigation}")
    
    # Add security recommendations from CS
    for sec_rec in cs_result.security_recommendations[:2]:
        recommendations.append(f"Security: {sec_rec}")
    
    return recommendations[:7]  # Limit to top 7


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
    overall_score = calculate_overall_score(x_result, z_result, cs_result)
    recommendation = determine_recommendation(overall_score, z_result, cs_result)
    
    # Build summary
    summary_parts = []
    
    if z_result.veto_triggered:
        summary_parts.append("VETO TRIGGERED by Z Guardian.")
        summary_parts.append(f"Reason: {z_result.ethical_concerns[0] if z_result.ethical_concerns else 'Ethical red line crossed'}")
    else:
        summary_parts.append(f"Overall assessment: {recommendation.upper()}")
    
    summary_parts.append(f"Innovation: {x_result.innovation_score}/10")
    summary_parts.append(f"Ethics: {z_result.ethics_score}/10")
    summary_parts.append(f"Security: {cs_result.security_score}/10")
    
    summary = " | ".join(summary_parts)
    
    # Calculate average confidence
    avg_confidence = (
        x_result.confidence +
        z_result.confidence +
        cs_result.confidence
    ) / 3
    
    return TrinitySynthesis(
        summary=summary,
        innovation_score=x_result.innovation_score,
        ethics_score=z_result.ethics_score,
        security_score=cs_result.security_score,
        overall_score=overall_score,
        strengths=synthesize_strengths(x_result, z_result, cs_result),
        concerns=synthesize_concerns(x_result, z_result, cs_result),
        recommendations=synthesize_recommendations(x_result, z_result, cs_result),
        recommendation=recommendation,
        confidence=round(avg_confidence, 2),
        veto_triggered=z_result.veto_triggered,
        veto_reason=z_result.ethical_concerns[0] if z_result.veto_triggered and z_result.ethical_concerns else None
    )


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
