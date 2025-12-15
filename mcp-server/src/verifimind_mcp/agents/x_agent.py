"""
X Intelligent Agent for VerifiMind-PEAS MCP Server.

X Intelligent is the Innovation and Strategy Analyst in the RefleXion Trinity.
It focuses on innovation potential, strategic value, and market opportunities.
"""

from typing import Optional

from ..models import (
    Concept,
    AgentConfig,
    XAgentAnalysis,
    PriorReasoning,
    X_AGENT_CONFIG
)
from ..llm import LLMProvider
from .base_agent import BaseAgent


class XAgent(BaseAgent):
    """
    X Intelligent - Innovation and Strategy Analyst.
    
    Specializes in:
    - Innovation potential assessment
    - Strategic value analysis
    - Market opportunity identification
    - Competitive positioning
    - Growth potential evaluation
    """
    
    AGENT_ID = "X"
    OUTPUT_MODEL = XAgentAnalysis
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        llm_provider: Optional[LLMProvider] = None
    ):
        """
        Initialize X Intelligent agent.
        
        Args:
            config: Agent configuration (uses X_AGENT_CONFIG if not provided)
            llm_provider: LLM provider instance
        """
        super().__init__(
            config=config or X_AGENT_CONFIG,
            llm_provider=llm_provider
        )
    
    def get_focus_summary(self) -> str:
        """Return a brief summary of X Intelligent's focus areas."""
        return (
            "X Intelligent analyzes concepts for innovation potential, "
            "strategic value, market opportunities, and growth trajectory. "
            "Focus: What makes this idea valuable and how can it succeed?"
        )
    
    async def quick_assessment(self, concept: Concept) -> dict:
        """
        Perform a quick innovation assessment.
        
        Returns a simplified assessment without full Chain of Thought.
        Useful for initial screening of concepts.
        """
        result = await self.analyze(concept)
        
        return {
            "agent": "X Intelligent",
            "concept": concept.name,
            "innovation_score": result.innovation_score,
            "strategic_value": result.strategic_value,
            "top_opportunity": result.opportunities[0] if result.opportunities else None,
            "top_risk": result.risks[0] if result.risks else None,
            "recommendation": result.recommendation,
            "confidence": result.confidence
        }
    
    def get_innovation_criteria(self) -> list:
        """Return the criteria used for innovation assessment."""
        return [
            {
                "criterion": "Novelty",
                "description": "How new and unique is this idea?",
                "weight": 0.25
            },
            {
                "criterion": "Market Fit",
                "description": "How well does it address market needs?",
                "weight": 0.25
            },
            {
                "criterion": "Scalability",
                "description": "Can it grow and scale effectively?",
                "weight": 0.20
            },
            {
                "criterion": "Competitive Advantage",
                "description": "What sustainable advantages does it provide?",
                "weight": 0.15
            },
            {
                "criterion": "Feasibility",
                "description": "Is it technically and economically feasible?",
                "weight": 0.15
            }
        ]
