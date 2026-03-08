"""
Chain of Thought reasoning models for VerifiMind-PEAS MCP Server.

These models define the structures for transparent reasoning,
enabling agents to share their thought processes with each other
and with humans for full auditability.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ReasoningStep(BaseModel):
    """
    A single step in a Chain of Thought reasoning process.
    
    Each step represents one logical thought in the agent's
    reasoning chain, with optional evidence and confidence.
    """
    step_number: int = Field(..., ge=1, description="Sequential step number")
    thought: str = Field(..., description="The reasoning thought at this step")
    evidence: Optional[str] = Field(None, description="Evidence supporting this thought")
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence in this reasoning step (0.0 to 1.0)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "step_number": 1,
                "thought": "This concept involves AI automation of code review, which is a growing market.",
                "evidence": "GitHub Copilot and similar tools have seen 40% YoY growth.",
                "confidence": 0.85
            }
        }


class ChainOfThought(BaseModel):
    """
    A complete Chain of Thought from an agent's analysis.
    
    This captures the full reasoning process, making it transparent
    and auditable for both other agents and human reviewers.
    """
    agent_id: str = Field(..., description="Agent identifier (X, Z, or CS)")
    agent_name: str = Field(..., description="Full agent name")
    concept_name: str = Field(..., description="Name of the concept being analyzed")
    reasoning_steps: List[ReasoningStep] = Field(
        ...,
        min_length=1,
        description="Sequential reasoning steps"
    )
    final_conclusion: str = Field(..., description="Final conclusion from the analysis")
    overall_confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the analysis"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def format_for_next_agent(self) -> str:
        """
        Format this Chain of Thought for consumption by the next agent.
        
        Returns a human-readable summary that the next agent can
        reference in their own analysis.
        """
        lines = [
            f"\n## Prior Analysis from {self.agent_name} ({self.agent_id})\n",
            f"**Concept**: {self.concept_name}\n",
            "**Reasoning Chain**:\n"
        ]
        
        for step in self.reasoning_steps:
            confidence_pct = int(step.confidence * 100)
            lines.append(f"- Step {step.step_number} ({confidence_pct}% confidence): {step.thought}")
            if step.evidence:
                lines.append(f"  - Evidence: {step.evidence}")
        
        lines.append(f"\n**Conclusion**: {self.final_conclusion}")
        lines.append(f"**Overall Confidence**: {int(self.overall_confidence * 100)}%\n")
        
        return "\n".join(lines)
    
    def to_summary(self) -> str:
        """Return a brief summary of the analysis."""
        return f"{self.agent_name}: {self.final_conclusion} (Confidence: {int(self.overall_confidence * 100)}%)"


class XAgentAnalysis(BaseModel):
    """
    Complete analysis output from X Intelligent agent — v4.1 with competitive intelligence.
    """
    agent: str = Field(default="X Intelligent")
    reasoning_steps: List[ReasoningStep]
    innovation_score: float = Field(..., ge=0.0, le=10.0, description="Innovation potential score")
    strategic_value: float = Field(..., ge=0.0, le=10.0, description="Strategic value score")
    opportunities: List[str] = Field(..., description="Identified opportunities")
    risks: List[str] = Field(..., description="Identified risks")
    recommendation: str = Field(..., description="Final recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    # v4.1 addition
    competitive_position: Optional[float] = Field(None, ge=0.0, le=10.0, description="Competitive position score vs LangChain/CrewAI/AutoGen (10=unique moat, 5=parity, 0=dominated)")
    # v4.2 Sentinel-Verified addition
    competitive_analysis: Optional[dict] = Field(None, description="Explicit competitive positioning vs LangChain/CrewAI/AutoGen/OpenAI Swarm with unique moat")
    
    def to_chain_of_thought(self, concept_name: str) -> ChainOfThought:
        """Convert to ChainOfThought for passing to next agent."""
        return ChainOfThought(
            agent_id="X",
            agent_name=self.agent,
            concept_name=concept_name,
            reasoning_steps=self.reasoning_steps,
            final_conclusion=self.recommendation,
            overall_confidence=self.confidence
        )


class ZAgentAnalysis(BaseModel):
    """
    Complete analysis output from Z Guardian agent — Z-Protocol v1.1 "Sentinel".
    """
    agent: str = Field(default="Z Guardian")
    reasoning_steps: List[ReasoningStep]
    ethics_score: float = Field(..., ge=0.0, le=10.0, description="Ethics compliance score (weighted 5-dimension composite)")
    z_protocol_compliance: bool = Field(..., description="Whether Z-Protocol v1.1 is satisfied")
    ethical_concerns: List[str] = Field(..., description="Identified ethical concerns")
    mitigation_measures: List[str] = Field(..., description="Recommended mitigations")
    recommendation: str = Field(..., description="Final recommendation")
    veto_triggered: bool = Field(
        default=False,
        description="True if ethical red line crossed - concept should not proceed"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    # v4.1 Sentinel additions
    veto_reason: Optional[str] = Field(None, description="Which red line triggered the veto, if any")
    jurisdiction_detected: Optional[List[str]] = Field(None, description="Target markets detected (EU, US, ASEAN, Global)")
    compliance_timeline: Optional[List[str]] = Field(None, description="Upcoming compliance deadlines relevant to this concept")
    # v4.2 Sentinel-Verified additions
    scoring_breakdown: Optional[dict] = Field(None, description="Per-dimension scores: ethical_alignment, regulatory_compliance, transparency_disclosure, data_governance, multi_agent_safety — each with score, weight, frameworks")
    applicable_frameworks: Optional[dict] = Field(None, description="Applicable frameworks by tier: tier_1_international, tier_2_eu, tier_3_us, tier_4_asean")
    total_frameworks_evaluated: Optional[int] = Field(None, description="Count of unique frameworks evaluated across all applicable tiers")
    
    def to_chain_of_thought(self, concept_name: str) -> ChainOfThought:
        """Convert to ChainOfThought for passing to next agent."""
        conclusion = self.recommendation
        if self.veto_triggered:
            conclusion = f"VETO TRIGGERED: {self.recommendation}"
        
        return ChainOfThought(
            agent_id="Z",
            agent_name=self.agent,
            concept_name=concept_name,
            reasoning_steps=self.reasoning_steps,
            final_conclusion=conclusion,
            overall_confidence=self.confidence
        )


class CSAgentAnalysis(BaseModel):
    """
    Complete analysis output from CS Security agent — v1.1 "Sentinel" (6-stage, 12-dimension).
    """
    agent: str = Field(default="CS Security")
    reasoning_steps: List[ReasoningStep]
    security_score: float = Field(..., ge=0.0, le=10.0, description="Security assessment score")
    vulnerabilities: List[str] = Field(..., description="Traditional web security vulnerabilities (Stage 1, dimensions 1-6)")
    attack_vectors: List[str] = Field(..., description="Potential attack vectors")
    security_recommendations: List[str] = Field(..., description="Security recommendations")
    socratic_questions: List[str] = Field(
        ...,
        description="Socratic questions — minimum 5, across 4 categories: Assumption Challenge, Boundary Probe, Cascade Scenario, Human Override"
    )
    recommendation: str = Field(..., description="Final recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence")
    # v4.1 Sentinel additions
    threat_level: Optional[str] = Field(None, description="Overall threat level: Low Risk / Medium Risk / High Risk / Critical Threat")
    agentic_threats: Optional[List[str]] = Field(None, description="Agentic-specific threats from Stage 2 OWASP ASI01-ASI10 assessment")
    reasoning_layer_findings: Optional[List[str]] = Field(None, description="Tool poisoning/shadowing/rugpull findings from Stage 5 Reasoning-Layer Audit")
    # v4.2 Sentinel-Verified additions
    stages_completed: Optional[List[dict]] = Field(None, description="All 6 stages completed with name and findings count")
    dimensions_evaluated: Optional[dict] = Field(None, description="All 12 dimensions: 6 traditional + 6 agentic, each with findings or 'Not applicable'")
    macp_security_assessment: Optional[dict] = Field(None, description="6 MACP v2.0 security properties: git_audit_trail, human_gated_execution, platform_isolation, credential_separation, artifact_integrity, transport_security")
    standards_referenced: Optional[List[str]] = Field(None, description="All security standards actually evaluated in this analysis")
    
    def to_chain_of_thought(self, concept_name: str) -> ChainOfThought:
        """Convert to ChainOfThought for passing to next agent."""
        return ChainOfThought(
            agent_id="CS",
            agent_name=self.agent,
            concept_name=concept_name,
            reasoning_steps=self.reasoning_steps,
            final_conclusion=self.recommendation,
            overall_confidence=self.confidence
        )


class PriorReasoning(BaseModel):
    """
    Container for prior reasoning from previous agents.
    
    Used to pass reasoning context between agents in the
    X → Z → CS validation flow.
    """
    chains: List[ChainOfThought] = Field(
        default_factory=list,
        description="List of prior reasoning chains"
    )
    
    def add(self, chain: ChainOfThought) -> None:
        """Add a new reasoning chain."""
        self.chains.append(chain)
    
    def format_for_prompt(self) -> str:
        """Format all prior reasoning for inclusion in a prompt."""
        if not self.chains:
            return ""
        
        lines = ["\n# PRIOR AGENT REASONING\n"]
        lines.append("Consider the following analysis from previous agents:\n")
        
        for chain in self.chains:
            lines.append(chain.format_for_next_agent())
        
        lines.append("\nBuild upon this prior reasoning in your analysis.\n")
        
        return "\n".join(lines)
    
    def get_agent_ids(self) -> List[str]:
        """Get list of agent IDs that have contributed reasoning."""
        return [chain.agent_id for chain in self.chains]
