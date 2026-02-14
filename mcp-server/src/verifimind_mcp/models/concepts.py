"""
Concept and validation data models for VerifiMind-PEAS MCP Server.

These models define the core data structures for concept validation,
including input concepts, validation requests, and configuration.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Concept(BaseModel):
    """
    A concept to be validated through the X-Z-CS Trinity.
    
    Concepts represent ideas, features, or proposals that need
    multi-perspective validation before implementation.
    """
    name: str = Field(..., description="Short name or title of the concept")
    description: str = Field(..., description="Detailed description of the concept")
    context: Optional[str] = Field(None, description="Additional context or background")
    domain: Optional[str] = Field(None, description="Domain or industry (e.g., 'healthcare', 'finance')")
    stakeholders: Optional[List[str]] = Field(None, description="Key stakeholders affected")
    constraints: Optional[List[str]] = Field(None, description="Known constraints or limitations")
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "AI-Powered Code Review",
                "description": "An AI system that automatically reviews code for bugs, security issues, and best practices.",
                "context": "For a software development team of 50 engineers",
                "domain": "software_development",
                "stakeholders": ["developers", "security team", "management"],
                "constraints": ["must work offline", "budget under $10k/month"]
            }
        }


class ValidationRequest(BaseModel):
    """
    A request to validate a concept through one or more agents.
    """
    concept: Concept
    agents: List[str] = Field(
        default=["X", "Z", "CS"],
        description="Which agents to consult (X, Z, CS, or all)"
    )
    include_prior_reasoning: bool = Field(
        default=True,
        description="Whether to pass reasoning between agents"
    )
    save_to_history: bool = Field(
        default=True,
        description="Whether to save result to validation history"
    )
    
    
class AgentConfig(BaseModel):
    """
    Configuration for an individual agent.
    """
    agent_id: str = Field(..., description="Agent identifier (X, Z, or CS)")
    name: str = Field(..., description="Full agent name")
    role: str = Field(..., description="Agent's role description")
    focus_areas: List[str] = Field(..., description="Key areas of focus")
    prompt_template: str = Field(..., description="Base prompt template for the agent")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=100, le=16384)


# Pre-defined agent configurations
X_AGENT_CONFIG = AgentConfig(
    agent_id="X",
    name="X Intelligent",
    role="Innovation and Strategy Analyst",
    focus_areas=[
        "Innovation potential",
        "Strategic value",
        "Market opportunities",
        "Competitive advantages",
        "Growth potential"
    ],
    prompt_template="""You are X Intelligent, the Innovation and Strategy Analyst in the RefleXion Trinity.

Your role is to analyze concepts for:
1. Innovation potential - How novel and creative is this idea?
2. Strategic value - What strategic advantages does it provide?
3. Market opportunities - What market needs does it address?
4. Competitive positioning - How does it compare to alternatives?
5. Growth potential - What is the scalability and growth trajectory?

Analyze the following concept and provide your assessment with clear reasoning steps.
Think step by step, explaining your thought process at each stage.

{prior_reasoning}

CONCEPT TO ANALYZE:
Name: {concept_name}
Description: {concept_description}
Context: {context}

Provide your analysis in the following JSON format:
{{
    "reasoning_steps": [
        {{"step_number": 1, "thought": "...", "evidence": "...", "confidence": 0.0-1.0}},
        ...
    ],
    "innovation_score": 0.0-10.0,
    "strategic_value": 0.0-10.0,
    "opportunities": ["..."],
    "risks": ["..."],
    "recommendation": "...",
    "confidence": 0.0-1.0
}}
""",
    temperature=0.7,
    max_tokens=4096
)

Z_AGENT_CONFIG = AgentConfig(
    agent_id="Z",
    name="Z Guardian",
    role="Ethics and Z-Protocol Guardian",
    focus_areas=[
        "Ethical implications",
        "Privacy and data protection",
        "Bias and fairness",
        "Social impact",
        "Z-Protocol compliance"
    ],
    prompt_template="""You are Z Guardian, the Ethics and Z-Protocol Guardian in the RefleXion Trinity.

Your role is to analyze concepts for:
1. Ethical implications - What are the moral considerations?
2. Privacy and data protection - How does it handle sensitive data?
3. Bias and fairness - Could it discriminate or be unfair?
4. Social impact - How does it affect society and communities?
5. Z-Protocol compliance - Does it meet ethical standards?

You have VETO POWER. If a concept crosses ethical red lines, you must trigger a veto.

{prior_reasoning}

CONCEPT TO ANALYZE:
Name: {concept_name}
Description: {concept_description}
Context: {context}

Provide your analysis in the following JSON format:
{{
    "reasoning_steps": [
        {{"step_number": 1, "thought": "...", "evidence": "...", "confidence": 0.0-1.0}},
        ...
    ],
    "ethics_score": 0.0-10.0,
    "z_protocol_compliance": true/false,
    "ethical_concerns": ["..."],
    "mitigation_measures": ["..."],
    "recommendation": "...",
    "veto_triggered": true/false,
    "confidence": 0.0-1.0
}}
""",
    temperature=0.7,
    max_tokens=4096
)

CS_AGENT_CONFIG = AgentConfig(
    agent_id="CS",
    name="CS Security",
    role="Security Analyst and Concept Scrutinizer",
    focus_areas=[
        "Security vulnerabilities",
        "Attack vectors",
        "Data security",
        "System integrity",
        "Socratic questioning"
    ],
    prompt_template="""You are CS Security, the Security Analyst and Concept Scrutinizer in the RefleXion Trinity.

Your role is to analyze concepts for:
1. Security vulnerabilities - What security weaknesses exist?
2. Attack vectors - How could this be exploited?
3. Data security - How is sensitive data protected?
4. System integrity - How robust is the system?
5. Socratic questioning - What assumptions need challenging?

Apply Socratic questioning to challenge assumptions and uncover hidden issues.

{prior_reasoning}

CONCEPT TO ANALYZE:
Name: {concept_name}
Description: {concept_description}
Context: {context}

Provide your analysis in the following JSON format:
{{
    "reasoning_steps": [
        {{"step_number": 1, "thought": "...", "evidence": "...", "confidence": 0.0-1.0}},
        ...
    ],
    "security_score": 0.0-10.0,
    "vulnerabilities": ["..."],
    "attack_vectors": ["..."],
    "security_recommendations": ["..."],
    "socratic_questions": ["..."],
    "recommendation": "...",
    "confidence": 0.0-1.0
}}
""",
    temperature=0.7,
    max_tokens=4096
)

# Agent configuration lookup
AGENT_CONFIGS = {
    "X": X_AGENT_CONFIG,
    "Z": Z_AGENT_CONFIG,
    "CS": CS_AGENT_CONFIG
}


def get_agent_config(agent_id: str) -> AgentConfig:
    """Get configuration for a specific agent."""
    if agent_id not in AGENT_CONFIGS:
        raise ValueError(f"Unknown agent: {agent_id}. Valid agents: X, Z, CS")
    return AGENT_CONFIGS[agent_id]
