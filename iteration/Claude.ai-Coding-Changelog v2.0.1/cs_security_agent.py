"""
VerifiMind PEAS - CS Security Agent v1.2
Corrected Version - December 2025

The 'Concept Scrutinizer' & Security Architect Agent.
Combines Socratic validation with cybersecurity threat modeling.

Fixes Applied:
- Consistent LLMMessage format throughout
- Validation of scrutinizer results before security scan
- Explicit score clamping and validation
- Improved error handling with detailed fallbacks
- Type-safe output formatting
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import asdict
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.core.concept_scrutinizer import (
    ConceptScrutinizer, 
    ScrutinyResult, 
    FeasibilityAnalysis,
    ScrutinyError
)
from src.llm.llm_provider import LLMMessage
from src.core.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# Type Definitions
# =============================================================================

class SecurityScanResult:
    """Structured security scan output."""
    
    def __init__(
        self,
        threats: List[str] = None,
        mitigations: List[str] = None,
        compliance_gaps: List[str] = None,
        owasp_relevant: List[str] = None,
        scan_status: str = "success",
        error_message: str = None
    ):
        self.threats = threats or []
        self.mitigations = mitigations or []
        self.compliance_gaps = compliance_gaps or []
        self.owasp_relevant = owasp_relevant or []
        self.scan_status = scan_status
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "threats": self.threats,
            "mitigations": self.mitigations,
            "compliance_gaps": self.compliance_gaps,
            "owasp_relevant": self.owasp_relevant,
            "scan_status": self.scan_status,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityScanResult':
        """Safe construction from parsed JSON."""
        return cls(
            threats=list(data.get('threats', [])),
            mitigations=list(data.get('mitigations', [])),
            compliance_gaps=list(data.get('compliance_gaps', [])),
            owasp_relevant=list(data.get('owasp_relevant', [])),
            scan_status=str(data.get('scan_status', 'success')),
            error_message=data.get('error_message')
        )
    
    @classmethod
    def error_result(cls, message: str) -> 'SecurityScanResult':
        """Create an error result."""
        return cls(
            threats=["Unable to complete threat analysis"],
            mitigations=["Manual security review required"],
            scan_status="error",
            error_message=message
        )


# =============================================================================
# Main Agent Class
# =============================================================================

class CSSecurityAgent(BaseAgent):
    """
    CS Security Agent v1.2 - The 'Concept Scrutinizer' & Security Architect.
    
    Upgraded to use the dedicated Socratic Validation Engine (ConceptScrutinizer)
    with robust error handling and parallel security scanning.
    
    Validation Flow:
    1. Socratic Scrutiny (4-step process via ConceptScrutinizer)
    2. Parallel Cybersecurity Threat Modeling (OWASP Top 10)
    3. Synthesis of both analyses into unified output
    """

    # Configuration
    SECURITY_SCAN_TIMEOUT = 45  # seconds
    
    def __init__(self, agent_id: str, llm_provider, config: Dict[str, Any] = None):
        super().__init__(agent_id, llm_provider, config or {})
        self.role = "Security & Socratic Validator"
        
        # Initialize the dedicated Socratic engine with shared config
        self.scrutinizer = ConceptScrutinizer(llm_provider, config)
        
        logger.info(f"CS Security Agent {agent_id} initialized with Socratic Engine")

    async def analyze(self, concept_input: Any) -> Dict[str, Any]:
        """
        Main analysis entry point.
        Delegates deep analysis to the ConceptScrutinizer engine.
        
        Args:
            concept_input: Either a ConceptInput object, dict, or string description
            
        Returns:
            Standardized agent response dictionary
        """
        logger.info(f"CS Agent {self.agent_id} starting Socratic analysis...")
        start_time = datetime.utcnow()
        
        # 1. Extract description safely
        description, context = self._extract_input(concept_input)
        
        if not description:
            return self._create_fallback_response("Empty or invalid concept input")

        try:
            # 2. Run the rigorous Socratic Scrutiny Engine
            scrutiny_result: ScrutinyResult = await self.scrutinizer.scrutinize(
                concept_description=description,
                context=context
            )
            
            # 3. Validate scrutiny results before security scan
            scrutiny_valid = self._validate_scrutiny_result(scrutiny_result)
            
            # 4. Perform specific Cybersecurity Scan (Parallel Task)
            # Pass degraded flag if scrutiny had issues
            tech_security_scan = await self._scan_technical_risks(
                description, 
                scrutiny_result,
                degraded_context=not scrutiny_valid
            )

            # 5. Synthesize Results
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            return self._format_output(scrutiny_result, tech_security_scan, elapsed)

        except ScrutinyError as e:
            logger.error(f"Scrutiny engine error: {e}", exc_info=True)
            return self._create_fallback_response(f"Scrutiny error: {e}")
        except Exception as e:
            logger.error(f"CS Analysis failed: {e}", exc_info=True)
            return self._create_fallback_response(str(e))

    # =========================================================================
    # Input Handling
    # =========================================================================

    def _extract_input(self, concept_input: Any) -> tuple[str, Dict[str, Any]]:
        """
        Safely extract description and context from various input types.
        
        Returns:
            Tuple of (description string, context dict)
        """
        description = ""
        context = {}
        
        if isinstance(concept_input, str):
            description = concept_input
        elif isinstance(concept_input, dict):
            description = concept_input.get('description', concept_input.get('content', ''))
            context = concept_input.get('user_context', concept_input.get('context', {}))
        elif hasattr(concept_input, 'description'):
            # Object with description attribute (e.g., ConceptInput dataclass)
            description = getattr(concept_input, 'description', '')
            context = getattr(concept_input, 'user_context', {})
            if context is None:
                context = {}
        else:
            # Last resort: convert to string
            description = str(concept_input)
        
        return description.strip(), context

    def _validate_scrutiny_result(self, result: ScrutinyResult) -> bool:
        """
        Validate that scrutiny results are usable for security scan context.
        
        Returns:
            True if results are valid, False if degraded
        """
        issues = []
        
        # Check Step 1 clarification
        if not result.step_1_clarification or len(result.step_1_clarification) < 20:
            issues.append("Clarification is empty or too short")
        
        # Check Step 2 feasibility (all scores at default = likely parsing failure)
        feasibility = result.step_2_feasibility
        if (feasibility.innovation_score == 50 and 
            feasibility.tech_feasibility_score == 50 and
            feasibility.market_score == 50 and
            feasibility.risk_score == 50):
            if not feasibility.innovation_analysis:
                issues.append("Feasibility analysis appears to have failed (all defaults)")
        
        # Check for recorded errors
        if result.has_errors:
            issues.extend(result.errors)
        
        if issues:
            logger.warning(f"Scrutiny validation issues: {issues}")
            return False
        
        return True

    # =========================================================================
    # Security Scanning
    # =========================================================================

    async def _scan_technical_risks(
        self, 
        description: str, 
        scrutiny: ScrutinyResult,
        degraded_context: bool = False
    ) -> SecurityScanResult:
        """
        Secondary layer: Specific Cyber-Security Threat Modeling.
        Focuses on OWASP Top 10 relative to the proposed architecture.
        
        Args:
            description: Original concept description
            scrutiny: Results from Socratic scrutiny
            degraded_context: If True, scrutiny context may be unreliable
        """
        # Build context from scrutiny results
        if degraded_context:
            context_section = f"""
LIMITED CONTEXT (prior analysis had issues):
- Concept: {description}
- Note: Feasibility analysis may be incomplete. Focus on general threat patterns.
"""
        else:
            feasibility_summary = {
                "tech_score": scrutiny.step_2_feasibility.tech_feasibility_score,
                "tech_analysis": scrutiny.step_2_feasibility.tech_analysis,
                "risk_score": scrutiny.step_2_feasibility.risk_score,
                "risk_analysis": scrutiny.step_2_feasibility.risk_analysis
            }
            context_section = f"""
CONCEPT: {description}

FEASIBILITY CONTEXT:
{json.dumps(feasibility_summary, indent=2)}

CHALLENGES IDENTIFIED:
{json.dumps(scrutiny.step_3_challenges, indent=2)}
"""

        prompt = f"""
ROLE: You are CS Security v1.0 (Cybersecurity Specialist) for VerifiMind PEAS.
TASK: Perform Threat Modeling for the following concept.

{context_section}

ANALYZE:
1. Top 3 Attack Vectors specific to this concept (e.g., Prompt Injection, IDOR, SSRF, Data Exfiltration).
2. Specific mitigation strategies for each identified threat.
3. Compliance technical gaps (Encryption at rest/transit, Access Control, Audit Logging).
4. Relevant OWASP Top 10 categories that apply.

CRITICAL: Return ONLY valid JSON (no markdown, no explanation):
{{
    "threats": ["Threat 1: description...", "Threat 2: description...", "Threat 3: description..."],
    "mitigations": ["Mitigation 1...", "Mitigation 2...", "Mitigation 3..."],
    "compliance_gaps": ["Gap 1...", "Gap 2..."],
    "owasp_relevant": ["A01:2021 - Broken Access Control", "A03:2021 - Injection", ...]
}}
"""
        try:
            # Use consistent LLMMessage format (FIX from original)
            response = await asyncio.wait_for(
                self.llm.generate(
                    [LLMMessage(role="user", content=prompt)],
                    temperature=0.3
                ),
                timeout=self.SECURITY_SCAN_TIMEOUT
            )
            
            # Parse response
            parsed = self._parse_security_json(response.content)
            return SecurityScanResult.from_dict(parsed)
            
        except asyncio.TimeoutError:
            logger.error("Security scan timed out")
            return SecurityScanResult.error_result("Security scan timed out")
        except Exception as e:
            logger.error(f"Security scan failed: {e}")
            return SecurityScanResult.error_result(str(e))

    def _parse_security_json(self, content: str) -> Dict[str, Any]:
        """Parse security scan JSON response with fallbacks."""
        import re
        
        # Strip markdown
        cleaned = content
        for marker in ["```json", "```JSON", "```"]:
            cleaned = cleaned.replace(marker, "")
        cleaned = cleaned.strip()
        
        # Try direct parse
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Try regex extraction
        json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Return minimal valid structure
        logger.warning("Could not parse security scan JSON, using defaults")
        return {
            "threats": ["Parsing failed - manual review required"],
            "mitigations": ["Manual security assessment recommended"],
            "compliance_gaps": [],
            "owasp_relevant": []
        }

    # =========================================================================
    # Output Formatting
    # =========================================================================

    def _format_output(
        self, 
        scrutiny: ScrutinyResult, 
        tech_scan: SecurityScanResult,
        elapsed_seconds: float
    ) -> Dict[str, Any]:
        """
        Format the complex data into the standard Agent response structure
        expected by the Orchestrator.
        
        Returns a flat dictionary that works whether accessed as dict or object.
        """
        # Calculate scores with explicit validation (FIX from original)
        validation_score = max(0, min(100, scrutiny.score))
        risk_score = 100 - validation_score
        
        # Determine status based on score thresholds
        if validation_score >= 70:
            status = "success"
        elif validation_score >= 50:
            status = "warning"
        else:
            status = "critical"
        
        # Adjust status if there were errors
        if scrutiny.has_errors or tech_scan.scan_status == "error":
            status = "warning" if status == "success" else status
        
        # Build analysis summary
        top_challenge = (
            scrutiny.step_3_challenges[0] 
            if scrutiny.step_3_challenges 
            else "No challenges identified"
        )
        top_threat = (
            tech_scan.threats[0] 
            if tech_scan.threats 
            else "No threats identified"
        )
        
        analysis_summary = (
            f"Verdict: {scrutiny.final_verdict}. "
            f"Top Challenge: {top_challenge[:100]}. "
            f"Top Threat: {top_threat[:100]}."
        )
        
        # Get recommendations
        recommendations = []
        if hasattr(scrutiny.step_4_strategy, 'strategic_options'):
            recommendations.extend(scrutiny.step_4_strategy.strategic_options)
        recommendations.extend(tech_scan.mitigations[:3])
        
        return {
            # Standard agent fields
            "agent_type": "CS",
            "agent_id": self.agent_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "elapsed_seconds": round(elapsed_seconds, 2),
            
            # Scores (with explicit clamping)
            "risk_score": risk_score,
            "validation_score": validation_score,
            "verdict": scrutiny.final_verdict,
            
            # Socratic Analysis (nested structure)
            "socratic_analysis": {
                "clarification": scrutiny.step_1_clarification,
                "feasibility": scrutiny.step_2_feasibility.to_dict(),
                "challenges": scrutiny.step_3_challenges,
                "strategy": scrutiny.step_4_strategy.to_dict()
            },
            
            # Security Scan Results
            "security_scan": tech_scan.to_dict(),
            
            # Flattened summary for orchestrator
            "analysis": analysis_summary,
            "recommendations": recommendations[:6],  # Cap at 6
            
            # Error tracking
            "errors": scrutiny.errors + ([tech_scan.error_message] if tech_scan.error_message else []),
            "has_errors": scrutiny.has_errors or tech_scan.scan_status == "error"
        }

    def _create_fallback_response(self, error_msg: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "agent_type": "CS",
            "agent_id": self.agent_id,
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "risk_score": 100,
            "validation_score": 0,
            "verdict": "Error",
            "analysis": f"Analysis failed: {error_msg}",
            "recommendations": [
                "System error occurred - manual review required",
                "Check logs for detailed error information",
                "Retry analysis after resolving underlying issue"
            ],
            "socratic_analysis": {
                "clarification": "Not available due to error",
                "feasibility": {},
                "challenges": [],
                "strategy": {}
            },
            "security_scan": SecurityScanResult.error_result(error_msg).to_dict(),
            "errors": [error_msg],
            "has_errors": True
        }


# =============================================================================
# Utility Functions
# =============================================================================

async def run_security_analysis(
    concept: Union[str, Dict, Any],
    llm_provider,
    config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Convenience function to run CS Security analysis without agent setup.
    
    Usage:
        result = await run_security_analysis("My AI startup idea", llm)
    """
    agent = CSSecurityAgent("cs-standalone", llm_provider, config or {})
    return await agent.analyze(concept)
