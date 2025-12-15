"""
CS Security Agent for VerifiMind-PEAS MCP Server.

CS Security is the Security Analyst and Concept Scrutinizer in the RefleXion Trinity.
It focuses on security vulnerabilities, attack vectors, and Socratic questioning.
"""

from typing import Optional

from ..models import (
    Concept,
    AgentConfig,
    CSAgentAnalysis,
    PriorReasoning,
    CS_AGENT_CONFIG
)
from ..llm import LLMProvider
from .base_agent import BaseAgent


class CSAgent(BaseAgent):
    """
    CS Security - Security Analyst and Concept Scrutinizer.
    
    Specializes in:
    - Security vulnerability assessment
    - Attack vector identification
    - Data security review
    - System integrity analysis
    - Socratic questioning (challenging assumptions)
    """
    
    AGENT_ID = "CS"
    OUTPUT_MODEL = CSAgentAnalysis
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        llm_provider: Optional[LLMProvider] = None
    ):
        """
        Initialize CS Security agent.
        
        Args:
            config: Agent configuration (uses CS_AGENT_CONFIG if not provided)
            llm_provider: LLM provider instance
        """
        super().__init__(
            config=config or CS_AGENT_CONFIG,
            llm_provider=llm_provider
        )
    
    def get_focus_summary(self) -> str:
        """Return a brief summary of CS Security's focus areas."""
        return (
            "CS Security analyzes concepts for security vulnerabilities, "
            "attack vectors, and applies Socratic questioning to challenge assumptions. "
            "Focus: What could go wrong and what are we not seeing?"
        )
    
    async def security_scan(self, concept: Concept) -> dict:
        """
        Perform a quick security scan.
        
        Returns key security findings without full analysis.
        Useful for initial security screening.
        """
        result = await self.analyze(concept)
        
        return {
            "agent": "CS Security",
            "concept": concept.name,
            "security_score": result.security_score,
            "vulnerability_count": len(result.vulnerabilities),
            "attack_vector_count": len(result.attack_vectors),
            "top_vulnerability": result.vulnerabilities[0] if result.vulnerabilities else None,
            "top_question": result.socratic_questions[0] if result.socratic_questions else None,
            "recommendation": result.recommendation
        }
    
    def get_security_categories(self) -> list:
        """Return the security categories assessed."""
        return [
            {
                "category": "Authentication",
                "description": "Identity verification and access control",
                "weight": 0.20
            },
            {
                "category": "Authorization",
                "description": "Permission management and privilege escalation",
                "weight": 0.15
            },
            {
                "category": "Data Protection",
                "description": "Encryption, storage, and transmission security",
                "weight": 0.20
            },
            {
                "category": "Input Validation",
                "description": "Protection against injection and malformed input",
                "weight": 0.15
            },
            {
                "category": "Error Handling",
                "description": "Secure error handling and information disclosure",
                "weight": 0.10
            },
            {
                "category": "Logging & Monitoring",
                "description": "Audit trails and anomaly detection",
                "weight": 0.10
            },
            {
                "category": "Third-Party Risk",
                "description": "Dependencies, APIs, and supply chain security",
                "weight": 0.10
            }
        ]
    
    def get_socratic_question_types(self) -> list:
        """Return the types of Socratic questions used."""
        return [
            {
                "type": "Clarification",
                "purpose": "What exactly do you mean by...?",
                "example": "What specific data will be collected from users?"
            },
            {
                "type": "Assumption Probing",
                "purpose": "What are you assuming here?",
                "example": "Are you assuming users will always have internet access?"
            },
            {
                "type": "Evidence Seeking",
                "purpose": "What evidence supports this?",
                "example": "What data shows this approach is more secure?"
            },
            {
                "type": "Perspective Exploration",
                "purpose": "How might others see this?",
                "example": "How would a malicious actor view this feature?"
            },
            {
                "type": "Consequence Analysis",
                "purpose": "What are the implications?",
                "example": "What happens if this system fails during peak usage?"
            },
            {
                "type": "Meta-Questioning",
                "purpose": "Why is this question important?",
                "example": "Why haven't we considered offline functionality?"
            }
        ]
