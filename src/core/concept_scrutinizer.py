"""
VerifiMind PEAS - Concept Scrutinizer (概念审思者)
Corrected v2.0.1 - December 2025

4-Step Socratic Validation Process:
1. Clarification & Definition
2. Multi-Dimensional Feasibility Analysis
3. Socratic Challenge (Devil's Advocate)
4. Strategic Recommendations

Fixes Applied:
- Robust JSON parsing with multiple fallback strategies
- Retry logic with exponential backoff for LLM calls
- Custom exception hierarchy for better error handling
- Consistent challenge extraction via JSON format
- Improved score calculation with validation
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

# Third-party imports (add tenacity to requirements.txt)
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False

from src.llm.llm_provider import LLMProvider, LLMMessage
from src.core.logging_config import get_logger

logger = get_logger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================

class ScrutinyError(Exception):
    """Base exception for Concept Scrutinizer errors."""
    pass


class LLMParsingError(ScrutinyError):
    """Raised when LLM response cannot be parsed."""
    def __init__(self, step_name: str, raw_content: str, original_error: Exception = None):
        self.step_name = step_name
        self.raw_content = raw_content
        self.original_error = original_error
        super().__init__(f"Failed to parse LLM response at {step_name}")


class LLMTimeoutError(ScrutinyError):
    """Raised when LLM call times out after retries."""
    pass


class ValidationError(ScrutinyError):
    """Raised when validation logic fails."""
    pass


# =============================================================================
# Data Classes
# =============================================================================

class Verdict(Enum):
    """Strategic verdict options."""
    GO = "Go"
    PIVOT = "Pivot"
    NO_GO = "No-Go"
    UNKNOWN = "Unknown"


@dataclass
class FeasibilityAnalysis:
    """Structured feasibility analysis from Step 2."""
    innovation_score: int = 50
    innovation_analysis: str = ""
    tech_feasibility_score: int = 50
    tech_analysis: str = ""
    market_score: int = 50
    market_analysis: str = ""
    risk_score: int = 50  # Higher = riskier
    risk_analysis: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeasibilityAnalysis':
        """Safe construction from dict with defaults."""
        return cls(
            innovation_score=int(data.get('innovation_score', 50)),
            innovation_analysis=str(data.get('innovation_analysis', '')),
            tech_feasibility_score=int(data.get('tech_feasibility_score', 50)),
            tech_analysis=str(data.get('tech_analysis', '')),
            market_score=int(data.get('market_score', 50)),
            market_analysis=str(data.get('market_analysis', '')),
            risk_score=int(data.get('risk_score', 50)),
            risk_analysis=str(data.get('risk_analysis', ''))
        )


@dataclass
class StrategicRecommendation:
    """Structured strategic output from Step 4."""
    verdict: Verdict = Verdict.UNKNOWN
    verdict_reason: str = ""
    strategic_options: List[str] = field(default_factory=list)
    roadmap_milestones: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'verdict': self.verdict.value,
            'verdict_reason': self.verdict_reason,
            'strategic_options': self.strategic_options,
            'roadmap_milestones': self.roadmap_milestones
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategicRecommendation':
        """Safe construction from dict with defaults."""
        verdict_str = str(data.get('verdict', 'Unknown'))
        try:
            verdict = Verdict(verdict_str)
        except ValueError:
            # Handle variations like "go", "GO", "Go!"
            verdict_lower = verdict_str.lower().strip().rstrip('!')
            if 'go' in verdict_lower and 'no' not in verdict_lower:
                verdict = Verdict.GO
            elif 'pivot' in verdict_lower:
                verdict = Verdict.PIVOT
            elif 'no' in verdict_lower:
                verdict = Verdict.NO_GO
            else:
                verdict = Verdict.UNKNOWN
        
        return cls(
            verdict=verdict,
            verdict_reason=str(data.get('verdict_reason', '')),
            strategic_options=list(data.get('strategic_options', [])),
            roadmap_milestones=list(data.get('roadmap_milestones', []))
        )


@dataclass
class ScrutinyResult:
    """Structured output from the Socratic validation process."""
    step_1_clarification: str
    step_2_feasibility: FeasibilityAnalysis
    step_3_challenges: List[str]
    step_4_strategy: StrategicRecommendation
    final_verdict: str
    score: int
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'step_1_clarification': self.step_1_clarification,
            'step_2_feasibility': self.step_2_feasibility.to_dict(),
            'step_3_challenges': self.step_3_challenges,
            'step_4_strategy': self.step_4_strategy.to_dict(),
            'final_verdict': self.final_verdict,
            'score': self.score,
            'timestamp': self.timestamp,
            'errors': self.errors
        }
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0


# =============================================================================
# Main Class
# =============================================================================

class ConceptScrutinizer:
    """
    Implementation of the 'Concept Scrutinizer' (概念审思者) Methodology.
    Executes the 4-Step Socratic Validation Process used by VerifiMind PEAS.
    
    Ref: 概念审思者.pdf
    
    Features:
    - Robust JSON parsing with multiple fallback strategies
    - Retry logic with exponential backoff
    - Structured data classes for type safety
    - Comprehensive error tracking
    """

    # Configuration
    DEFAULT_TIMEOUT = 60  # seconds
    MAX_RETRIES = 3
    
    def __init__(self, llm_provider: LLMProvider, config: Optional[Dict[str, Any]] = None):
        self.llm = llm_provider
        self.config = config or {}
        self.timeout = self.config.get('llm_timeout', self.DEFAULT_TIMEOUT)
        self._errors: List[str] = []

    async def scrutinize(
        self, 
        concept_description: str, 
        context: Optional[Dict] = None
    ) -> ScrutinyResult:
        """
        Main entry point for the 4-step validation cycle.
        
        Args:
            concept_description: The concept/idea to validate
            context: Optional additional context (user profile, industry, etc.)
            
        Returns:
            ScrutinyResult with all validation steps completed
        """
        logger.info(f"Starting Socratic Scrutiny for concept: {concept_description[:50]}...")
        self._errors = []  # Reset errors for this run
        
        # Context building
        context_str = json.dumps(context) if context else "No additional context."

        # Execute 4 Steps Sequentially (The Logic Chain)
        
        # Step 1: Clarification & Definition
        clarification = await self._step_1_clarify(concept_description)
        
        # Step 2: Multi-Dimensional Analysis
        feasibility = await self._step_2_analyze(concept_description, clarification)
        
        # Step 3: Socratic Challenge 
        challenges = await self._step_3_challenge(concept_description, feasibility)
        
        # Step 4: Strategic Recommendations
        strategy = await self._step_4_recommend(concept_description, feasibility, challenges)

        # Calculate Score & Verdict
        score = self._calculate_score(feasibility)
        
        result = ScrutinyResult(
            step_1_clarification=clarification,
            step_2_feasibility=feasibility,
            step_3_challenges=challenges,
            step_4_strategy=strategy,
            final_verdict=strategy.verdict.value,
            score=score,
            errors=self._errors.copy()
        )
        
        if result.has_errors:
            logger.warning(f"Scrutiny completed with {len(result.errors)} errors")
        else:
            logger.info(f"Scrutiny completed successfully. Score: {score}, Verdict: {strategy.verdict.value}")
        
        return result

    # =========================================================================
    # Step Implementations
    # =========================================================================

    async def _step_1_clarify(self, concept: str) -> str:
        """Step 1: Clarification & Definition - Identify core assumptions."""
        prompt = f"""
ROLE: You are the Concept Scrutinizer (概念审思者).
TASK: Perform Step 1 (Clarification) on this concept: "{concept}"

REQUIREMENTS:
1. Restate the core concept clearly in 1-2 sentences.
2. Identify the target user and core pain point they experience.
3. List the top 3 hidden assumptions the founder is making.

FORMAT: Return as clear, structured text with headers for each section.
"""
        try:
            response = await self._llm_call_with_retry(
                [LLMMessage(role="user", content=prompt)],
                temperature=0.3
            )
            return response.content.strip()
        except Exception as e:
            error_msg = f"Step 1 failed: {str(e)}"
            self._errors.append(error_msg)
            logger.error(error_msg)
            return f"[Clarification unavailable due to error: {str(e)}]"

    async def _step_2_analyze(self, concept: str, clarification: str) -> FeasibilityAnalysis:
        """Step 2: Multi-Dimensional Feasibility Analysis (Innovation, Tech, Market, Risk)."""
        prompt = f"""
ROLE: You are the Concept Scrutinizer.
TASK: Perform Step 2 (Deep Feasibility Analysis) on: "{concept}"
CONTEXT FROM STEP 1: {clarification}

ANALYZE THESE 4 DIMENSIONS:
1. Innovation (Disruptive vs Incremental? Differentiation from existing solutions?)
2. Technical Feasibility (Implementation bottlenecks? Technology maturity?)
3. Market Potential (Addressable market size? Is the pain point real and urgent?)
4. Risks (Execution risk, Ethical concerns, Regulatory barriers?)

CRITICAL: Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
    "innovation_score": <0-100>,
    "innovation_analysis": "<2-3 sentences>",
    "tech_feasibility_score": <0-100>,
    "tech_analysis": "<2-3 sentences>",
    "market_score": <0-100>,
    "market_analysis": "<2-3 sentences>",
    "risk_score": <0-100>,
    "risk_analysis": "<2-3 sentences>"
}}

Note: risk_score where 0=very safe, 100=extremely risky.
"""
        try:
            response = await self._llm_call_with_retry(
                [LLMMessage(role="user", content=prompt)],
                temperature=0.2  # Lower temperature for structured output
            )
            parsed = self._parse_json(response.content, "Step 2 - Feasibility")
            return FeasibilityAnalysis.from_dict(parsed)
        except LLMParsingError as e:
            self._errors.append(str(e))
            logger.error(f"Step 2 parsing failed, using defaults: {e}")
            return FeasibilityAnalysis()
        except Exception as e:
            error_msg = f"Step 2 failed: {str(e)}"
            self._errors.append(error_msg)
            logger.error(error_msg)
            return FeasibilityAnalysis()

    async def _step_3_challenge(self, concept: str, analysis: FeasibilityAnalysis) -> List[str]:
        """Step 3: Socratic Challenge - The 'Devil's Advocate'."""
        prompt = f"""
ROLE: You are the Concept Scrutinizer acting as Devil's Advocate.
TASK: Perform Step 3 (Socratic Challenge) on this concept.

CONCEPT: {concept}
FEASIBILITY ANALYSIS: {json.dumps(analysis.to_dict())}

REQUIREMENTS:
1. Challenge the strongest assumption identified.
2. Identify a specific 'Extreme Scenario' where this concept fails.
3. Name a likely cognitive bias in the founder's thinking (e.g., Optimism Bias, Survivorship Bias).
4. Ask probing questions that expose weaknesses.

CRITICAL: Return ONLY a JSON array of 3-5 challenge strings (no markdown, no explanation):
["Challenge/Question 1...", "Challenge/Question 2...", "Challenge/Question 3..."]
"""
        try:
            response = await self._llm_call_with_retry(
                [LLMMessage(role="user", content=prompt)],
                temperature=0.7  # Higher temperature for creative challenges
            )
            challenges = self._parse_challenges(response.content)
            
            if not challenges:
                self._errors.append("Step 3: No challenges extracted, using fallback")
                return ["Manual review required: Unable to generate Socratic challenges automatically."]
            
            return challenges
        except Exception as e:
            error_msg = f"Step 3 failed: {str(e)}"
            self._errors.append(error_msg)
            logger.error(error_msg)
            return ["Manual review required due to processing error."]

    async def _step_4_recommend(
        self, 
        concept: str, 
        analysis: FeasibilityAnalysis, 
        challenges: List[str]
    ) -> StrategicRecommendation:
        """Step 4: Strategic Recommendations & Roadmap."""
        prompt = f"""
ROLE: You are the Concept Scrutinizer.
TASK: Perform Step 4 (Strategic Synthesis) based on all prior analysis.

CONCEPT: {concept}
FEASIBILITY SCORES: Innovation={analysis.innovation_score}, Tech={analysis.tech_feasibility_score}, Market={analysis.market_score}, Risk={analysis.risk_score}
CHALLENGES IDENTIFIED: {json.dumps(challenges)}

REQUIREMENTS:
1. Provide a Final Verdict: "Go" (proceed), "Pivot" (modify significantly), or "No-Go" (abandon).
2. Explain the verdict reasoning in 2-3 sentences.
3. Propose 3 executable Strategic Options regardless of verdict.
4. Define a high-level Roadmap with 3 milestones.

CRITICAL: Return ONLY valid JSON (no markdown, no explanation):
{{
    "verdict": "Go/Pivot/No-Go",
    "verdict_reason": "<2-3 sentences explaining why>",
    "strategic_options": ["Option A description", "Option B description", "Option C description"],
    "roadmap_milestones": ["Month 1-2: ...", "Month 3-4: ...", "Month 5-6: ..."]
}}
"""
        try:
            response = await self._llm_call_with_retry(
                [LLMMessage(role="user", content=prompt)],
                temperature=0.4
            )
            parsed = self._parse_json(response.content, "Step 4 - Strategy")
            return StrategicRecommendation.from_dict(parsed)
        except LLMParsingError as e:
            self._errors.append(str(e))
            logger.error(f"Step 4 parsing failed, using defaults: {e}")
            return StrategicRecommendation()
        except Exception as e:
            error_msg = f"Step 4 failed: {str(e)}"
            self._errors.append(error_msg)
            logger.error(error_msg)
            return StrategicRecommendation()

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _llm_call_with_retry(
        self, 
        messages: List[LLMMessage], 
        temperature: float = 0.5
    ):
        """
        Make LLM call with retry logic and timeout.
        
        Uses tenacity if available, otherwise simple retry loop.
        """
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                # Add timeout wrapper
                response = await asyncio.wait_for(
                    self.llm.generate(messages, temperature=temperature),
                    timeout=self.timeout
                )
                return response
            except asyncio.TimeoutError:
                last_error = LLMTimeoutError(f"LLM call timed out after {self.timeout}s")
                logger.warning(f"LLM timeout on attempt {attempt + 1}/{self.MAX_RETRIES}")
            except Exception as e:
                last_error = e
                logger.warning(f"LLM error on attempt {attempt + 1}/{self.MAX_RETRIES}: {e}")
            
            # Exponential backoff
            if attempt < self.MAX_RETRIES - 1:
                wait_time = (2 ** attempt) + 1
                await asyncio.sleep(wait_time)
        
        raise last_error or ScrutinyError("LLM call failed after all retries")

    def _parse_json(self, content: str, step_name: str = "unknown") -> Dict[str, Any]:
        """
        Robust JSON parsing with multiple fallback strategies.
        
        Strategies:
        1. Direct parse
        2. Strip markdown code blocks
        3. Extract JSON object using regex
        4. Try to fix common issues (trailing commas, etc.)
        """
        original_content = content
        
        # Strategy 1: Direct parse
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Strip markdown code blocks (various formats)
        cleaned = content
        for pattern in ["```json", "```JSON", "```"]:
            cleaned = cleaned.replace(pattern, "")
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Extract JSON object using regex
        # Look for content between first { and last }
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: Try to fix common LLM JSON issues
        fixed = cleaned
        # Remove trailing commas before } or ]
        fixed = re.sub(r',\s*([}\]])', r'\1', fixed)
        # Fix unquoted keys (simple cases)
        fixed = re.sub(r'(\{|,)\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', fixed)
        
        try:
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            raise LLMParsingError(step_name, original_content[:500], e)

    def _parse_challenges(self, content: str) -> List[str]:
        """
        Parse challenges from LLM response.
        
        Tries JSON array first, then falls back to line-based extraction.
        """
        # Try JSON array parse first
        try:
            cleaned = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned)
            if isinstance(result, list):
                return [str(c).strip() for c in result if c and len(str(c).strip()) > 10]
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Fallback: Extract from various list formats
        lines = content.split('\n')
        challenges = []
        
        # Patterns that indicate a list item
        list_patterns = [
            r'^[-*•◦▪▸►]\s*(.+)',           # Bullet points
            r'^[1-9][0-9]?[.)]\s*(.+)',      # Numbered: 1. 1) 
            r'^[a-zA-Z][.)]\s*(.+)',          # Lettered: a. A)
            r'^Q:\s*(.+)',                    # Q: format
            r'^Challenge:\s*(.+)',            # Challenge: format
            r'^\*\*(.+)\*\*',                 # Bold markdown
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            for pattern in list_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    challenge = match.group(1).strip()
                    if len(challenge) > 20:  # Minimum meaningful length
                        challenges.append(challenge)
                    break
            else:
                # No pattern matched - check if it's a substantial standalone line
                if len(line) > 50 and '?' in line:
                    challenges.append(line)
        
        # Deduplicate while preserving order
        seen = set()
        unique_challenges = []
        for c in challenges:
            c_lower = c.lower()
            if c_lower not in seen:
                seen.add(c_lower)
                unique_challenges.append(c)
        
        return unique_challenges[:5]  # Cap at 5 challenges

    def _calculate_score(self, feasibility: FeasibilityAnalysis) -> int:
        """
        Weighted scoring algorithm based on Step 2 Analysis.
        
        Formula: ((Innovation + Tech + Market) / 3) - (Risk * 0.2) + 10 base curve
        
        Returns: Score clamped to 0-100 range
        """
        try:
            # Validate inputs are in expected range
            innovation = max(0, min(100, feasibility.innovation_score))
            tech = max(0, min(100, feasibility.tech_feasibility_score))
            market = max(0, min(100, feasibility.market_score))
            risk = max(0, min(100, feasibility.risk_score))
            
            # Calculate weighted average of positive factors
            positive_avg = (innovation + tech + market) / 3
            
            # Risk penalty (20% weight)
            risk_penalty = risk * 0.2
            
            # Base curve of +10 to avoid overly harsh scores
            raw_score = positive_avg - risk_penalty + 10
            
            # Clamp to valid range
            final_score = int(max(0, min(100, raw_score)))
            
            logger.debug(
                f"Score calculation: Inn={innovation}, Tech={tech}, Market={market}, "
                f"Risk={risk} -> Raw={raw_score:.1f} -> Final={final_score}"
            )
            
            return final_score
            
        except Exception as e:
            logger.error(f"Score calculation error: {e}")
            self._errors.append(f"Score calculation failed: {e}")
            return 50  # Neutral fallback


# =============================================================================
# Convenience Functions
# =============================================================================

async def quick_scrutinize(
    concept: str, 
    llm_provider: LLMProvider,
    context: Optional[Dict] = None
) -> ScrutinyResult:
    """
    Convenience function for one-off scrutiny without instantiating the class.
    
    Usage:
        result = await quick_scrutinize("AI-powered pet food delivery", llm)
    """
    scrutinizer = ConceptScrutinizer(llm_provider)
    return await scrutinizer.scrutinize(concept, context)
