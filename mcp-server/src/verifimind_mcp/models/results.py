"""
Result models for VerifiMind-PEAS MCP Server.

These models define the output structures for validation results,
including individual agent results and full Trinity synthesis.
"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, computed_field

from .reasoning import (
    XAgentAnalysis,
    ZAgentAnalysis,
    CSAgentAnalysis,
    ChainOfThought
)


class TrinitySynthesis(BaseModel):
    """
    Synthesis of all three agent analyses into a unified assessment.
    """
    summary: str = Field(..., description="Executive summary of the validation")
    
    # Aggregated scores
    innovation_score: Optional[float] = Field(..., ge=0.0, le=10.0)
    ethics_score: Optional[float] = Field(..., ge=0.0, le=10.0)
    security_score: Optional[float] = Field(..., ge=0.0, le=10.0)
    overall_score: Optional[float] = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Null when the complete Trinity quality gate did not pass",
    )
    
    # Key findings
    strengths: List[str] = Field(..., description="Key strengths identified")
    concerns: List[str] = Field(..., description="Key concerns identified")
    recommendations: List[str] = Field(..., description="Actionable recommendations")
    
    # Decision support
    recommendation: Literal["proceed", "proceed_with_caution", "revise", "reject"] = Field(
        ...,
        description="Overall recommendation"
    )
    confidence: Optional[float] = Field(
        ...,
        ge=0.0,
        le=1.0,
        description=(
            "Aggregate decision confidence. Null when any required Trinity stage "
            "did not complete with real inference."
        ),
    )
    confidence_valid: bool = Field(
        default=True,
        description="False when aggregate confidence is withheld by the quality gate",
    )
    analysis_incomplete: bool = Field(
        default=False,
        description="True when one or more required Trinity stages was degraded",
    )
    degraded_agents: List[str] = Field(
        default_factory=list,
        description="Required agent IDs whose inference quality was not real",
    )
    quality_gate: dict = Field(
        default_factory=dict,
        description="Machine-readable per-agent quality gate used for the decision",
    )
    
    # Veto status
    veto_triggered: Optional[bool] = Field(
        default=False,
        description=(
            "True if a real Z analysis triggered ethical veto; null when Z "
            "inference was degraded"
        ),
    )
    veto_reason: Optional[str] = Field(
        None,
        description="Reason for veto if triggered"
    )

    # v0.5.4 — plain-language founder layer
    founder_summary: Optional[dict] = Field(
        None,
        description="Plain-language summary for non-technical founders: verdict, score_plain, what_works, things_to_address, next_steps, research_continuation"
    )

    # v0.5.43 — fail-safe transparency: set when an agent's inference was degraded
    # (partial/fallback/synthetic). Surfaces that the verdict rests on synthesized
    # defaults so a caller never reads a clean PROCEED off untrustworthy ethics data.
    inference_warning: Optional[str] = Field(
        None,
        description="Non-null when Trinity inference was degraded; explains why the recommendation was capped and human review is required"
    )


class TrinityResult(BaseModel):
    """
    Complete result from a full Trinity validation (X → Z → CS).
    
    This is the primary output of the run_full_trinity tool,
    containing all agent analyses and the synthesized result.
    """
    # Metadata
    validation_id: str = Field(..., description="Unique validation identifier")
    concept_name: str = Field(..., description="Name of the validated concept")
    concept_description: str = Field(..., description="Description of the concept")
    
    # Individual agent analyses
    x_analysis: XAgentAnalysis = Field(..., description="X Intelligent analysis")
    z_analysis: ZAgentAnalysis = Field(..., description="Z Guardian analysis")
    cs_analysis: CSAgentAnalysis = Field(..., description="CS Security analysis")
    
    # Synthesis
    synthesis: TrinitySynthesis = Field(..., description="Synthesized result")
    
    # Human-at-Center
    human_decision_required: bool = Field(
        default=True,
        description="Always True - human makes final decision"
    )
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    @computed_field
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate validation duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def get_reasoning_chains(self) -> List[ChainOfThought]:
        """Get all reasoning chains for review."""
        return [
            self.x_analysis.to_chain_of_thought(self.concept_name),
            self.z_analysis.to_chain_of_thought(self.concept_name),
            self.cs_analysis.to_chain_of_thought(self.concept_name)
        ]
    
    def to_summary(self) -> str:
        """Generate a human-readable summary."""
        def _score(value: Optional[float]) -> str:
            return f"{value:.1f}/10" if value is not None else "unavailable"

        lines = [
            f"# Trinity Validation Result: {self.concept_name}",
            f"\n## Overall Assessment",
            f"- **Recommendation**: {self.synthesis.recommendation.upper()}",
            f"- **Overall Score**: {_score(self.synthesis.overall_score)}",
            (
                f"- **Confidence**: {int(self.synthesis.confidence * 100)}%"
                if self.synthesis.confidence is not None
                else "- **Confidence**: unavailable (degraded inference)"
            ),
        ]
        
        if self.synthesis.veto_triggered:
            lines.append(f"\n⚠️ **VETO TRIGGERED**: {self.synthesis.veto_reason}")
        
        lines.extend([
            f"\n## Individual Scores",
            f"- Innovation (X): {_score(self.synthesis.innovation_score)}",
            f"- Ethics (Z): {_score(self.synthesis.ethics_score)}",
            f"- Security (CS): {_score(self.synthesis.security_score)}",
            f"\n## Key Strengths",
        ])
        
        for strength in self.synthesis.strengths[:3]:
            lines.append(f"- {strength}")
        
        lines.append("\n## Key Concerns")
        for concern in self.synthesis.concerns[:3]:
            lines.append(f"- {concern}")
        
        lines.append("\n## Recommendations")
        for rec in self.synthesis.recommendations[:3]:
            lines.append(f"- {rec}")
        
        lines.extend([
            f"\n---",
            f"*Validation ID: {self.validation_id}*",
            f"*Human decision required: {self.human_decision_required}*"
        ])
        
        return "\n".join(lines)


class ValidationHistoryEntry(BaseModel):
    """
    A single entry in the validation history.
    
    Stores a summary of past validations for retrieval and learning.
    """
    validation_id: str
    concept_name: str
    concept_description: str
    recommendation: str
    overall_score: Optional[float]
    veto_triggered: Optional[bool]
    timestamp: datetime
    
    # Optional full result (may be omitted for storage efficiency)
    full_result: Optional[TrinityResult] = None
    
    @classmethod
    def from_trinity_result(cls, result: TrinityResult) -> "ValidationHistoryEntry":
        """Create history entry from a TrinityResult."""
        return cls(
            validation_id=result.validation_id,
            concept_name=result.concept_name,
            concept_description=result.concept_description,
            recommendation=result.synthesis.recommendation,
            overall_score=result.synthesis.overall_score,
            veto_triggered=result.synthesis.veto_triggered,
            timestamp=result.started_at,
            full_result=result
        )


class ValidationHistory(BaseModel):
    """
    Container for validation history.
    """
    entries: List[ValidationHistoryEntry] = Field(default_factory=list)
    
    def add(self, result: TrinityResult) -> None:
        """Add a new validation result to history."""
        entry = ValidationHistoryEntry.from_trinity_result(result)
        self.entries.insert(0, entry)  # Most recent first
    
    def get_latest(self, n: int = 10) -> List[ValidationHistoryEntry]:
        """Get the n most recent validations."""
        return self.entries[:n]
    
    def find_by_concept(self, concept_name: str) -> List[ValidationHistoryEntry]:
        """Find all validations for a specific concept."""
        return [e for e in self.entries if e.concept_name == concept_name]
    
    def get_statistics(self) -> dict:
        """Get statistics about validation history."""
        if not self.entries:
            return {
                "total_validations": 0,
                "average_score": 0.0,
                "veto_rate": 0.0,
                "scored_validations": 0,
                "trusted_veto_validations": 0,
                "recommendation_distribution": {}
            }
        
        total = len(self.entries)
        scored_entries = [
            e.overall_score for e in self.entries if e.overall_score is not None
        ]
        trusted_veto_entries = [
            e.veto_triggered for e in self.entries if e.veto_triggered is not None
        ]
        avg_score = (
            sum(scored_entries) / len(scored_entries)
            if scored_entries else None
        )
        veto_rate = (
            sum(1 for veto in trusted_veto_entries if veto)
            / len(trusted_veto_entries)
            if trusted_veto_entries else None
        )
        
        rec_dist = {}
        for e in self.entries:
            rec_dist[e.recommendation] = rec_dist.get(e.recommendation, 0) + 1
        
        return {
            "total_validations": total,
            "average_score": round(avg_score, 2) if avg_score is not None else None,
            "veto_rate": round(veto_rate, 2) if veto_rate is not None else None,
            "scored_validations": len(scored_entries),
            "trusted_veto_validations": len(trusted_veto_entries),
            "recommendation_distribution": rec_dist
        }
