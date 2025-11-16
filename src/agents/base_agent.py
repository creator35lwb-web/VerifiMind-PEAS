"""
Base Agent Class for VerifiMind AI Agents
Provides common functionality for X, Z, and CS agents
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Standard response format for all agents"""
    agent_id: str
    agent_type: str  # 'X', 'Z', 'CS'
    status: str  # 'success', 'warning', 'error'
    analysis: Dict[str, Any]
    recommendations: List[str]
    risk_score: float  # 0-100
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class ConceptInput:
    """Input concept for analysis"""
    id: str
    description: str
    category: Optional[str]
    user_context: Dict[str, Any]
    session_id: str


class BaseAgent(ABC):
    """Abstract base class for all VerifiMind agents"""

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        llm_provider: Any,
        config: Dict[str, Any]
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.llm_provider = llm_provider
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{agent_type}")

    @abstractmethod
    async def analyze(self, concept: ConceptInput) -> AgentResponse:
        """
        Main analysis method - must be implemented by each agent
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Returns the agent's system prompt
        """
        pass

    def validate_input(self, concept: ConceptInput) -> bool:
        """
        Validates the input concept
        """
        if not concept.description or len(concept.description.strip()) < 10:
            raise ValueError("Concept description is too short (minimum 10 characters)")
        return True

    async def log_analysis(self, concept: ConceptInput, response: AgentResponse):
        """
        Logs the analysis for audit trail
        """
        self.logger.info(
            f"Analysis completed",
            extra={
                "agent_type": self.agent_type,
                "concept_id": concept.id,
                "status": response.status,
                "risk_score": response.risk_score
            }
        )

    def calculate_risk_score(self, factors: Dict[str, float]) -> float:
        """
        Calculates weighted risk score from multiple factors
        """
        if not factors:
            return 0.0

        total_weight = sum(factors.values())
        if total_weight == 0:
            return 0.0

        return min(100.0, max(0.0, total_weight))


class AgentOrchestrator:
    """
    Coordinates multiple agents for collaborative analysis
    """

    def __init__(
        self,
        x_agent: 'XIntelligentAgent',
        z_agent: 'ZGuardianAgent',
        cs_agent: 'CSSecurityAgent'
    ):
        self.x_agent = x_agent
        self.z_agent = z_agent
        self.cs_agent = cs_agent
        self.logger = logging.getLogger(__name__)

    async def run_full_analysis(self, concept: ConceptInput) -> Dict[str, AgentResponse]:
        """
        Runs all three agents in parallel and returns combined results
        """
        self.logger.info(f"Starting full analysis for concept {concept.id}")

        # Run agents in parallel
        import asyncio
        results = await asyncio.gather(
            self.x_agent.analyze(concept),
            self.z_agent.analyze(concept),
            self.cs_agent.analyze(concept),
            return_exceptions=True
        )

        x_result, z_result, cs_result = results

        # Handle any errors
        response_dict = {}
        for agent_name, result in [('X', x_result), ('Z', z_result), ('CS', cs_result)]:
            if isinstance(result, Exception):
                self.logger.error(f"{agent_name} agent failed: {str(result)}")
                response_dict[agent_name] = self._create_error_response(agent_name, result)
            else:
                response_dict[agent_name] = result

        return response_dict

    def _create_error_response(self, agent_type: str, error: Exception) -> AgentResponse:
        """Creates an error response when an agent fails"""
        return AgentResponse(
            agent_id=f"{agent_type.lower()}-agent",
            agent_type=agent_type,
            status='error',
            analysis={'error': str(error)},
            recommendations=[f"Agent {agent_type} encountered an error. Please retry."],
            risk_score=100.0,
            metadata={'error_type': type(error).__name__},
            timestamp=datetime.utcnow()
        )

    def resolve_conflicts(self, responses: Dict[str, AgentResponse]) -> Dict[str, Any]:
        """
        Resolves conflicts between agent recommendations
        Priority: CS Security > Z Guardian > X Intelligent
        """
        # Check for critical security issues first
        cs_response = responses.get('CS')
        if cs_response and cs_response.risk_score >= 80:
            return {
                'decision': 'reject',
                'reason': 'Critical security risk detected',
                'priority_agent': 'CS',
                'details': cs_response.analysis
            }

        # Check for compliance violations
        z_response = responses.get('Z')
        if z_response and z_response.risk_score >= 70:
            return {
                'decision': 'needs_revision',
                'reason': 'Compliance or ethical concerns',
                'priority_agent': 'Z',
                'details': z_response.analysis
            }

        # Evaluate business viability
        x_response = responses.get('X')
        if x_response and x_response.risk_score <= 40:
            return {
                'decision': 'approve',
                'reason': 'All checks passed with acceptable risk',
                'priority_agent': 'X',
                'details': {
                    'x_score': x_response.risk_score,
                    'z_score': z_response.risk_score if z_response else None,
                    'cs_score': cs_response.risk_score if cs_response else None
                }
            }

        return {
            'decision': 'review_required',
            'reason': 'Mixed signals from agents',
            'priority_agent': None,
            'details': {
                'x_score': x_response.risk_score if x_response else None,
                'z_score': z_response.risk_score if z_response else None,
                'cs_score': cs_response.risk_score if cs_response else None
            }
        }
