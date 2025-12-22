import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from src.llm.llm_provider import LLMProvider, LLMMessage
from src.core.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class ScrutinyResult:
    """Structured output from the Socratic validation process"""
    step_1_clarification: str
    step_2_feasibility: Dict[str, Any]
    step_3_challenges: List[str]
    step_4_strategy: Dict[str, Any]
    final_verdict: str
    score: int
    timestamp: str = datetime.utcnow().isoformat()

class ConceptScrutinizer:
    """
    Implementation of the 'Concept Scrutinizer' (概念审思者) Methodology.
    Executes the 4-Step Socratic Validation Process used by VerifiMind PEAS.
    
    Ref: 概念审思者.pdf
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def scrutinize(self, concept_description: str, context: Optional[Dict] = None) -> ScrutinyResult:
        """
        Main entry point for the 4-step validation cycle.
        """
        logger.info(f"Starting Socratic Scrutiny for concept: {concept_description[:50]}...")
        
        # Context building
        context_str = json.dumps(context) if context else "No additional context."

        # Execute 4 Steps Sequentially (The Logic Chain)
        
        # Step 1: Clarification & Definition [cite: 1109]
        clarification = await self._step_1_clarify(concept_description)
        
        # Step 2: Multi-Dimensional Analysis [cite: 1112]
        feasibility = await self._step_2_analyze(concept_description, clarification)
        
        # Step 3: Socratic Challenge 
        challenges = await self._step_3_challenge(concept_description, feasibility)
        
        # Step 4: Strategic Recommendations [cite: 1122]
        strategy = await self._step_4_recommend(concept_description, feasibility, challenges)

        # Calculate Score & Verdict
        score = self._calculate_score(feasibility)
        
        return ScrutinyResult(
            step_1_clarification=clarification,
            step_2_feasibility=feasibility,
            step_3_challenges=challenges,
            step_4_strategy=strategy,
            final_verdict=strategy.get('verdict', 'Needs Refinement'),
            score=score
        )

    async def _step_1_clarify(self, concept: str) -> str:
        """Step 1: Clarification & Definition - Identify core assumptions."""
        prompt = f"""
        ROLE: You are the Concept Scrutinizer (概念审思者).
        TASK: Perform Step 1 (Clarification) on this concept: "{concept}"
        
        REQUIREMENTS:
        1. Restate the core concept clearly.
        2. Identify the target user and core pain point.
        3. List the top 3 hidden assumptions the user is making.
        
        Return the response as a clear, concise text summary.
        """
        response = await self.llm.generate([LLMMessage(role="user", content=prompt)])
        return response.content

    async def _step_2_analyze(self, concept: str, clarification: str) -> Dict:
        """Step 2: Multi-Dimensional Feasibility Analysis (Innovation, Tech, Market, Risk)."""
        prompt = f"""
        ROLE: You are the Concept Scrutinizer.
        TASK: Perform Step 2 (Deep Feasibility Analysis) on: "{concept}"
        CONTEXT: {clarification}
        
        ANALYZE THESE 4 DIMENSIONS:
        1. Innovation (Disruptive vs Incremental? Differentiation?)
        2. Technical Feasibility (Bottlenecks? Maturity?)
        3. Market Potential (Market size? Real pain point?)
        4. Risks (Execution, Ethical, Regulatory?)

        RETURN ONLY JSON FORMAT:
        {{
            "innovation_score": (0-100),
            "innovation_analysis": "...",
            "tech_feasibility_score": (0-100),
            "tech_analysis": "...",
            "market_score": (0-100),
            "market_analysis": "...",
            "risk_score": (0-100), // Higher is riskier
            "risk_analysis": "..."
        }}
        """
        response = await self.llm.generate([LLMMessage(role="user", content=prompt)], temperature=0.2)
        return self._parse_json(response.content)

    async def _step_3_challenge(self, concept: str, analysis: Dict) -> List[str]:
        """Step 3: Socratic Challenge - The 'Devil's Advocate'."""
        prompt = f"""
        ROLE: You are the Concept Scrutinizer.
        TASK: Perform Step 3 (Socratic Challenge). Be the Devil's Advocate.
        CONCEPT: {concept}
        ANALYSIS: {json.dumps(analysis)}
        
        REQUIREMENTS:
        1. Challenge the strongest assumption identified in Step 1.
        2. Find a specific 'Extreme Scenario' where this concept fails.
        3. Identify a likely cognitive bias in the founder's thinking (e.g., Optimism Bias).
        
        Return a list of 3-5 sharp, Socratic questions/challenges.
        """
        response = await self.llm.generate([LLMMessage(role="user", content=prompt)], temperature=0.7)
        # Simple split by newline for list format
        return [line.strip() for line in response.content.split('\n') if line.strip().startswith(('-', '*', '1.', '2.', '3.'))]

    async def _step_4_recommend(self, concept: str, analysis: Dict, challenges: List[str]) -> Dict:
        """Step 4: Strategic Recommendations & Roadmap."""
        prompt = f"""
        ROLE: You are the Concept Scrutinizer.
        TASK: Perform Step 4 (Strategic Synthesis).
        CONCEPT: {concept}
        CHALLENGES: {json.dumps(challenges)}
        
        REQUIREMENTS:
        1. Provide a Final Verdict (Go / Pivot / No-Go).
        2. Propose 3 executable Strategic Options.
        3. Define a high-level Roadmap (MVP timeline).
        
        RETURN ONLY JSON FORMAT:
        {{
            "verdict": "Go/Pivot/No-Go",
            "verdict_reason": "...",
            "strategic_options": ["Option A...", "Option B...", "Option C..."],
            "roadmap_milestones": ["Month 1...", "Month 3...", "Month 6..."]
        }}
        """
        response = await self.llm.generate([LLMMessage(role="user", content=prompt)])
        return self._parse_json(response.content)

    def _calculate_score(self, feasibility: Dict) -> int:
        """Weighted scoring algorithm based on Step 2 Analysis."""
        try:
            innovation = feasibility.get('innovation_score', 50)
            tech = feasibility.get('tech_feasibility_score', 50)
            market = feasibility.get('market_score', 50)
            risk = feasibility.get('risk_score', 50)
            
            # Formula: (Inn + Tech + Market) - (Risk * 0.5)
            raw_score = (innovation + tech + market) / 3
            risk_penalty = risk * 0.2
            final_score = max(0, min(100, raw_score - risk_penalty + 10)) # +10 base curve
            return int(final_score)
        except Exception:
            return 50

    def _parse_json(self, content: str) -> Dict:
        """Helper to safely parse LLM JSON responses."""
        try:
            # Strip markdown code blocks if present
            clean_content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_content)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from LLM: {content[:100]}...")
            return {}