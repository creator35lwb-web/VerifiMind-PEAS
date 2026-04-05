"""
Z Guardian Agent for VerifiMind-PEAS MCP Server.

Z Guardian is the Ethics and Z-Protocol Guardian in the RefleXion Trinity.
It focuses on ethical implications, privacy, bias, and has VETO power.
"""

import logging
from typing import Optional

from ..models import (
    Concept,
    AgentConfig,
    ZAgentAnalysis,
    Z_AGENT_CONFIG
)
from ..llm import LLMProvider
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Code-enforced veto threshold — ethics_score below this MUST trigger veto
# regardless of LLM output. Guards against prompt dilution regression.
_VETO_SCORE_THRESHOLD = 4.0


class ZAgent(BaseAgent):
    """
    Z Guardian - Ethics and Z-Protocol Guardian.
    
    Specializes in:
    - Ethical implications assessment
    - Privacy and data protection review
    - Bias and fairness analysis
    - Social impact evaluation
    - Z-Protocol compliance verification
    
    Has VETO POWER for concepts that cross ethical red lines.
    """
    
    AGENT_ID = "Z"
    OUTPUT_MODEL = ZAgentAnalysis
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        llm_provider: Optional[LLMProvider] = None
    ):
        """
        Initialize Z Guardian agent.
        
        Args:
            config: Agent configuration (uses Z_AGENT_CONFIG if not provided)
            llm_provider: LLM provider instance
        """
        super().__init__(
            config=config or Z_AGENT_CONFIG,
            llm_provider=llm_provider
        )
    
    def get_focus_summary(self) -> str:
        """Return a brief summary of Z Guardian's focus areas."""
        return (
            "Z Guardian analyzes concepts for ethical implications, "
            "privacy concerns, bias, and social impact. "
            "Has VETO power for concepts crossing ethical red lines. "
            "Focus: Is this concept ethical and does it protect users?"
        )
    
    async def analyze(self, concept, prior_reasoning=None, metrics=None):
        """Analyze with post-LLM code-enforced veto threshold.

        Z Guardian has VETO POWER. If the LLM assigns ethics_score < 4.0
        but does not set veto_triggered=True, this method enforces it
        programmatically. This guards against prompt dilution regressions
        (e.g. Z-Protocol v1.1's expanded 21-framework prompt reducing
        sensitivity of the veto trigger).
        """
        result = await super().analyze(concept, prior_reasoning)

        # Code-enforced veto: score < 4.0 is the "Concerning → Non-Compliant"
        # boundary on the Z scale. Any concept scoring this low MUST be vetoed.
        if result.ethics_score < _VETO_SCORE_THRESHOLD and not result.veto_triggered:
            logger.warning(
                f"Z Guardian auto-veto enforced: score={result.ethics_score} "
                f"< threshold={_VETO_SCORE_THRESHOLD} but LLM did not trigger veto. "
                f"concept='{concept.name}'"
            )
            result.veto_triggered = True
            if not result.veto_reason:
                result.veto_reason = (
                    f"Auto-enforced: ethics_score {result.ethics_score:.1f}/10 "
                    f"is below the {_VETO_SCORE_THRESHOLD} safety threshold. "
                    f"Review concept for red line violations."
                )

        return result

    async def check_veto_status(self, concept: Concept) -> dict:
        """
        Quick check if a concept would trigger a veto.
        
        Returns veto status without full analysis.
        Useful for early screening of concepts.
        """
        result = await self.analyze(concept)
        
        return {
            "agent": "Z Guardian",
            "concept": concept.name,
            "veto_triggered": result.veto_triggered,
            "z_protocol_compliance": result.z_protocol_compliance,
            "ethics_score": result.ethics_score,
            "top_concern": result.ethical_concerns[0] if result.ethical_concerns else None,
            "recommendation": result.recommendation
        }
    
    def get_ethical_red_lines(self) -> list:
        """Return the ethical red lines that trigger veto."""
        return [
            {
                "red_line": "Deception",
                "description": "Intentionally misleading or deceiving users",
                "severity": "critical"
            },
            {
                "red_line": "Privacy Violation",
                "description": "Unauthorized collection or sharing of personal data",
                "severity": "critical"
            },
            {
                "red_line": "Discrimination",
                "description": "Systematic bias against protected groups",
                "severity": "critical"
            },
            {
                "red_line": "Harm Facilitation",
                "description": "Enabling physical, psychological, or financial harm",
                "severity": "critical"
            },
            {
                "red_line": "Autonomy Violation",
                "description": "Removing user agency or informed consent",
                "severity": "high"
            },
            {
                "red_line": "Exploitation",
                "description": "Taking unfair advantage of vulnerable populations",
                "severity": "high"
            }
        ]
    
    def get_z_protocol_principles(self) -> list:
        """Return the core principles of the Z-Protocol."""
        return [
            {
                "principle": "Transparency",
                "description": "Clear disclosure of AI involvement and data usage"
            },
            {
                "principle": "Consent",
                "description": "Informed user consent for data collection and processing"
            },
            {
                "principle": "Fairness",
                "description": "Equitable treatment across all user groups"
            },
            {
                "principle": "Privacy",
                "description": "Minimal data collection and strong protection"
            },
            {
                "principle": "Accountability",
                "description": "Clear responsibility for AI decisions and outcomes"
            },
            {
                "principle": "Beneficence",
                "description": "Active promotion of user and societal well-being"
            }
        ]
