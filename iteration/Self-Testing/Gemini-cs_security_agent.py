import json
from typing import Dict, Any, List, Optional
from dataclasses import asdict

from src.agents.base_agent import BaseAgent
from src.core.concept_scrutinizer import ConceptScrutinizer, ScrutinyResult
from src.core.logging_config import get_logger

logger = get_logger(__name__)

class CSSecurityAgent(BaseAgent):
    """
    CS Security Agent v1.1 - The 'Concept Scrutinizer' & Security Architect.
    
    Upgraded to use the dedicated Socratic Validation Engine (ConceptScrutinizer)
    instead of raw prompts. This ensures rigorous 4-step validation:
    1. Clarification -> 2. Analysis -> 3. Challenge -> 4. Strategy.
    """

    def __init__(self, agent_id: str, llm_provider, config: Dict[str, Any]):
        super().__init__(agent_id, llm_provider, config)
        self.role = "Security & Socratic Validator"
        # Initialize the dedicated engine
        self.scrutinizer = ConceptScrutinizer(llm_provider)

    async def analyze(self, concept_input: Any) -> Dict[str, Any]:
        """
        Main analysis entry point. 
        Delegates deep analysis to the ConceptScrutinizer engine.
        """
        logger.info(f"CS Agent {self.agent_id} starting Socratic analysis...")
        
        # 1. Extract description safely
        description = getattr(concept_input, 'description', str(concept_input))
        context = getattr(concept_input, 'user_context', {})

        # 2. Run the rigorous Socratic Scrutiny Engine
        # This replaces the old "single prompt" approach
        try:
            scrutiny_result: ScrutinyResult = await self.scrutinizer.scrutinize(
                concept_description=description,
                context=context
            )
            
            # 3. Perform specific Cybersecurity Scan (Parallel Task)
            # While the Scrutinizer handles logic/feasibility, we still need 
            # a raw technical security scan (SQLi, XSS, etc) for the specific tech stack.
            tech_security_scan = await self._scan_technical_risks(description, scrutiny_result)

            # 4. Synthesize Results
            return self._format_output(scrutiny_result, tech_security_scan)

        except Exception as e:
            logger.error(f"CS Analysis failed: {e}", exc_info=True)
            return self._create_fallback_response(str(e))

    async def _scan_technical_risks(self, description: str, scrutiny: ScrutinyResult) -> Dict:
        """
        Secondary layer: Specific Cyber-Security Threat Modeling.
        Focuses on OWASP Top 10 relative to the proposed architecture.
        """
        prompt = f"""
        ROLE: You are CS Security v1.0 (Cybersecurity Specialist).
        TASK: Threat Modeling for the following concept.
        
        CONCEPT: {description}
        FEASIBILITY: {json.dumps(scrutiny.step_2_feasibility)}
        
        IDENTIFY:
        1. Top 3 Attack Vectors (e.g., Prompt Injection, IDOR, SSRF).
        2. Specific mitigation strategies for this stack.
        3. Compliance technical gaps (Encryption, Access Control).
        
        Return JSON: {{ "threats": [], "mitigations": [], "compliance_gaps": [] }}
        """
        # Note: Using the base LLM direct call for this specific sub-task
        response = await self.llm.generate([{"role": "user", "content": prompt}])
        try:
            # Basic cleanup and parse
            content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except:
            return {"threats": ["Parsing Error"], "mitigations": ["Manual Review"]}

    def _format_output(self, scrutiny: ScrutinyResult, tech_scan: Dict) -> Dict:
        """
        Format the complex data into the standard Agent response structure
        expected by the Orchestrator.
        """
        # Convert dataclass to dict
        scrutiny_data = asdict(scrutiny)
        
        return {
            "agent_type": "CS",
            "status": "success" if scrutiny.score > 60 else "warning",
            "risk_score": 100 - scrutiny.score, # Inverting for risk
            "validation_score": scrutiny.score,
            "verdict": scrutiny.final_verdict,
            
            # The Deep Insights
            "socratic_analysis": {
                "clarification": scrutiny.step_1_clarification,
                "challenges": scrutiny.step_3_challenges,
                "strategy": scrutiny.step_4_strategy
            },
            
            # The Security Specifics
            "security_scan": tech_scan,
            
            # For the Orchestrator's summary
            "analysis": f"Verdict: {scrutiny.final_verdict}. "
                        f"Top Challenge: {scrutiny.step_3_challenges[0] if scrutiny.step_3_challenges else 'None'}",
            "recommendations": scrutiny.step_4_strategy.get('strategic_options', [])
        }

    def _create_fallback_response(self, error_msg: str) -> Dict:
        return {
            "agent_type": "CS",
            "status": "error",
            "risk_score": 100,
            "analysis": f"Analysis failed: {error_msg}",
            "recommendations": ["System error - manual review required"]
        }