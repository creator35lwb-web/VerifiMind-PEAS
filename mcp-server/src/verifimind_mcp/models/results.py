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
    innovation_score: float = Field(..., ge=0.0, le=10.0)
    ethics_score: float = Field(..., ge=0.0, le=10.0)
    security_score: float = Field(..., ge=0.0, le=10.0)
    overall_score: float = Field(..., ge=0.0, le=10.0)
    
    # Key findings
    strengths: List[str] = Field(..., description="Key strengths identified")
    concerns: List[str] = Field(..., description="Key concerns identified")
    recommendations: List[str] = Field(..., description="Actionable recommendations")
    
    # Decision support
    recommendation: Literal["proceed", "proceed_with_caution", "revise", "reject"] = Field(
        ...,
        description="Overall recommendation"
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    
    # Veto status
    veto_triggered: bool = Field(
        default=False,
        description="True if Z Guardian triggered ethical veto"
    )
    veto_reason: Optional[str] = Field(
        None,
        description="Reason for veto if triggered"
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
        lines = [
            f"# Trinity Validation Result: {self.concept_name}",
            f"\n## Overall Assessment",
            f"- **Recommendation**: {self.synthesis.recommendation.upper()}",
            f"- **Overall Score**: {self.synthesis.overall_score:.1f}/10",
            f"- **Confidence**: {int(self.synthesis.confidence * 100)}%",
        ]
        
        if self.synthesis.veto_triggered:
            lines.append(f"\n⚠️ **VETO TRIGGERED**: {self.synthesis.veto_reason}")
        
        lines.extend([
            f"\n## Individual Scores",
            f"- Innovation (X): {self.synthesis.innovation_score:.1f}/10",
            f"- Ethics (Z): {self.synthesis.ethics_score:.1f}/10",
            f"- Security (CS): {self.synthesis.security_score:.1f}/10",
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
    overall_score: float
    veto_triggered: bool
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
                "recommendation_distribution": {}
            }
        
        total = len(self.entries)
        avg_score = sum(e.overall_score for e in self.entries) / total
        veto_count = sum(1 for e in self.entries if e.veto_triggered)
        
        rec_dist = {}
        for e in self.entries:
            rec_dist[e.recommendation] = rec_dist.get(e.recommendation, 0) + 1
        
        return {
            "total_validations": total,
            "average_score": round(avg_score, 2),
            "veto_rate": round(veto_count / total, 2),
            "recommendation_distribution": rec_dist
        }
