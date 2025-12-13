"""
Agent Orchestrator - X-Z-CS Trinity Collaboration
Orchestrates parallel execution and conflict resolution for the three agents.

Enhanced with:
- Parallel async execution
- Conflict resolution with Z veto power
- Error aggregation and recovery
- Timeout handling
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ConceptInput:
    """Input for concept validation."""
    id: str
    description: str
    category: Optional[str] = None
    user_context: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentResult:
    """Standardized result from any agent."""
    agent_id: str
    agent_name: str  # X, Z, or CS
    status: str  # success, warning, error, blocked
    decision: str  # approve, reject, pivot
    score: float  # 0-100
    reasoning: str
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0


@dataclass
class OrchestrationDecision:
    """Final decision from orchestrator after conflict resolution."""
    decision: str  # approve, reject, pivot
    confidence: float  # 0-100
    reason: str
    agent_votes: Dict[str, str]  # {agent_name: decision}
    conflicts_detected: List[str]
    resolution_strategy: str  # consensus, z_veto, cs_critical, majority
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# Agent Orchestrator
# =============================================================================

class AgentOrchestrator:
    """
    Orchestrates X-Z-CS Trinity collaboration with conflict resolution.

    Key Features:
    - Parallel async execution of all three agents
    - Z Guardian has veto power for ethical violations
    - CS Security can flag critical vulnerabilities (hard stop)
    - Conflict resolution with multiple strategies
    - Graceful error handling and partial failure recovery
    """

    def __init__(self, x_agent, z_agent, cs_agent, timeout: int = 180):
        """
        Initialize orchestrator with three agents.

        Args:
            x_agent: X Intelligent Agent (Innovation)
            z_agent: Z Guardian Agent (Ethics)
            cs_agent: CS Security Agent (Security)
            timeout: Max time for agent execution (seconds)
        """
        self.x_agent = x_agent
        self.z_agent = z_agent
        self.cs_agent = cs_agent
        self.timeout = timeout

    async def run_full_analysis(
        self,
        concept: ConceptInput,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Run all three agents (X, Z, CS) in parallel and collect results.

        Args:
            concept: Concept input to analyze
            parallel: If True, run agents in parallel (default), else sequential

        Returns:
            Dict with keys: 'X', 'Z', 'CS' containing agent results
        """
        logger.info(f"Starting full analysis for concept: {concept.id}")

        start_time = datetime.utcnow()

        try:
            if parallel:
                # Parallel execution with timeout
                results = await self._run_agents_parallel(concept)
            else:
                # Sequential execution (useful for debugging)
                results = await self._run_agents_sequential(concept)

            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Full analysis completed in {execution_time:.2f}s")

            # Add metadata
            results['metadata'] = {
                'concept_id': concept.id,
                'execution_time_s': execution_time,
                'parallel': parallel,
                'timestamp': datetime.utcnow().isoformat()
            }

            return results

        except Exception as e:
            logger.error(f"Full analysis failed: {e}", exc_info=True)
            raise

    async def _run_agents_parallel(self, concept: ConceptInput) -> Dict[str, Any]:
        """Run all three agents in parallel with timeout."""
        logger.info("Executing X, Z, CS agents in parallel...")

        # Create tasks
        tasks = {
            'X': self._run_agent_safe(self.x_agent, concept, 'X'),
            'Z': self._run_agent_safe(self.z_agent, concept, 'Z'),
            'CS': self._run_agent_safe(self.cs_agent, concept, 'CS')
        }

        # Wait for all tasks with timeout
        try:
            results = await asyncio.wait_for(
                self._gather_agent_results(tasks),
                timeout=self.timeout
            )
            return results
        except asyncio.TimeoutError:
            logger.error(f"Agent execution timed out after {self.timeout}s")
            # Return partial results
            return await self._handle_timeout(tasks)

    async def _run_agents_sequential(self, concept: ConceptInput) -> Dict[str, Any]:
        """Run agents sequentially (for debugging)."""
        logger.info("Executing agents sequentially...")

        results = {}

        # Run X first (Innovation)
        results['X'] = await self._run_agent_safe(self.x_agent, concept, 'X')

        # Run Z second (Ethics) - can veto based on X analysis
        results['Z'] = await self._run_agent_safe(self.z_agent, concept, 'Z')

        # Run CS last (Security) - validates X recommendations
        results['CS'] = await self._run_agent_safe(self.cs_agent, concept, 'CS')

        return results

    async def _run_agent_safe(
        self,
        agent,
        concept: ConceptInput,
        agent_name: str
    ) -> Any:
        """
        Run single agent with error handling.

        Args:
            agent: Agent instance to run
            concept: Concept input
            agent_name: Name of agent (X, Z, CS)

        Returns:
            Agent result or error object
        """
        start_time = datetime.utcnow()

        try:
            logger.info(f"{agent_name} Agent: Starting analysis...")

            # Run agent's analyze method
            result = await agent.analyze(concept)

            execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.info(f"{agent_name} Agent: Completed in {execution_time_ms:.0f}ms")

            # Add execution time to result if it's a dict
            if isinstance(result, dict):
                result['execution_time_ms'] = execution_time_ms

            return result

        except Exception as e:
            execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"{agent_name} Agent: Failed after {execution_time_ms:.0f}ms: {e}", exc_info=True)

            # Return error result
            return {
                'agent_name': agent_name,
                'status': 'error',
                'decision': 'reject',
                'score': 0,
                'reasoning': f"Agent execution failed: {str(e)}",
                'errors': [str(e)],
                'execution_time_ms': execution_time_ms
            }

    async def _gather_agent_results(self, tasks: Dict[str, asyncio.Task]) -> Dict[str, Any]:
        """Gather results from all agent tasks."""
        results = {}

        for agent_name, task in tasks.items():
            try:
                results[agent_name] = await task
            except Exception as e:
                logger.error(f"Failed to gather {agent_name} result: {e}")
                results[agent_name] = {
                    'agent_name': agent_name,
                    'status': 'error',
                    'decision': 'reject',
                    'score': 0,
                    'reasoning': f"Failed to gather result: {str(e)}",
                    'errors': [str(e)]
                }

        return results

    async def _handle_timeout(self, tasks: Dict[str, asyncio.Task]) -> Dict[str, Any]:
        """Handle timeout by collecting partial results."""
        logger.warning("Collecting partial results after timeout...")

        results = {}

        for agent_name, task in tasks.items():
            if task.done():
                try:
                    results[agent_name] = task.result()
                    logger.info(f"{agent_name}: Completed before timeout")
                except Exception as e:
                    logger.error(f"{agent_name}: Failed: {e}")
                    results[agent_name] = self._create_error_result(agent_name, str(e))
            else:
                logger.warning(f"{agent_name}: Timed out, cancelling...")
                task.cancel()
                results[agent_name] = self._create_error_result(agent_name, "Execution timed out")

        return results

    def _create_error_result(self, agent_name: str, error_message: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            'agent_name': agent_name,
            'status': 'error',
            'decision': 'reject',
            'score': 0,
            'reasoning': error_message,
            'errors': [error_message]
        }

    # =========================================================================
    # Conflict Resolution
    # =========================================================================

    def resolve_conflicts(
        self,
        agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve conflicts between agent recommendations.

        Resolution Rules:
        1. Z Guardian has VETO power (ethical violations)
        2. CS Security can flag CRITICAL vulnerabilities (hard stop)
        3. If no veto/critical: Majority vote (2/3 agents)
        4. If tied: Default to 'pivot' (refine concept)

        Args:
            agent_results: Dict with 'X', 'Z', 'CS' results

        Returns:
            OrchestrationDecision object as dict
        """
        logger.info("Starting conflict resolution...")

        # Extract decisions
        x_result = agent_results.get('X', {})
        z_result = agent_results.get('Z', {})
        cs_result = agent_results.get('CS', {})

        x_decision = self._extract_decision(x_result)
        z_decision = self._extract_decision(z_result)
        cs_decision = self._extract_decision(cs_result)

        agent_votes = {
            'X': x_decision,
            'Z': z_decision,
            'CS': cs_decision
        }

        logger.info(f"Agent votes: X={x_decision}, Z={z_decision}, CS={cs_decision}")

        conflicts_detected = []

        # RULE 1: Z Guardian Veto (Ethical)
        if z_decision == 'reject':
            z_reasoning = z_result.get('reasoning', 'Ethical violation detected')
            logger.warning(f"Z Guardian VETO: {z_reasoning}")
            conflicts_detected.append(f"Z Guardian veto: {z_reasoning}")

            return self._create_decision(
                decision='reject',
                confidence=100.0,
                reason=f"Z Guardian ethical veto: {z_reasoning}",
                agent_votes=agent_votes,
                conflicts=conflicts_detected,
                strategy='z_veto'
            )

        # RULE 2: CS Security Critical Flag
        cs_status = cs_result.get('status', 'unknown')
        cs_critical = cs_status == 'critical' or cs_decision == 'reject'

        if cs_critical:
            cs_reasoning = cs_result.get('reasoning', 'Critical security vulnerability detected')
            logger.warning(f"CS Security CRITICAL: {cs_reasoning}")
            conflicts_detected.append(f"CS critical vulnerability: {cs_reasoning}")

            return self._create_decision(
                decision='reject',
                confidence=95.0,
                reason=f"CS Security critical flag: {cs_reasoning}",
                agent_votes=agent_votes,
                conflicts=conflicts_detected,
                strategy='cs_critical'
            )

        # RULE 3: Majority Vote
        vote_counts = {
            'approve': sum(1 for d in agent_votes.values() if d == 'approve'),
            'reject': sum(1 for d in agent_votes.values() if d == 'reject'),
            'pivot': sum(1 for d in agent_votes.values() if d == 'pivot')
        }

        logger.info(f"Vote counts: {vote_counts}")

        # Check for majority (2/3 or 3/3)
        if vote_counts['approve'] >= 2:
            # Majority approval
            avg_score = self._calculate_average_score(agent_results)
            confidence = min(avg_score, 85.0)  # Cap at 85% for safety

            # Check for warnings from minority
            warnings = self._collect_warnings(agent_results)
            if warnings:
                conflicts_detected.extend(warnings)

            return self._create_decision(
                decision='approve',
                confidence=confidence,
                reason=f"Majority approval ({vote_counts['approve']}/3 agents)",
                agent_votes=agent_votes,
                conflicts=conflicts_detected,
                strategy='majority'
            )

        elif vote_counts['reject'] >= 2:
            # Majority rejection
            reasons = self._collect_rejection_reasons(agent_results)

            return self._create_decision(
                decision='reject',
                confidence=80.0,
                reason=f"Majority rejection ({vote_counts['reject']}/3 agents): {'; '.join(reasons)}",
                agent_votes=agent_votes,
                conflicts=conflicts_detected,
                strategy='majority'
            )

        # RULE 4: No Majority - Default to Pivot
        else:
            logger.info("No majority, defaulting to pivot (concept refinement needed)")
            conflicts_detected.append("No clear majority, concept needs refinement")

            pivot_reasons = []
            for agent_name, result in agent_results.items():
                if result.get('decision') == 'pivot':
                    pivot_reasons.append(result.get('reasoning', 'Refinement needed'))

            return self._create_decision(
                decision='pivot',
                confidence=60.0,
                reason=f"Split decision, refinement recommended: {'; '.join(pivot_reasons) if pivot_reasons else 'Conflicting agent assessments'}",
                agent_votes=agent_votes,
                conflicts=conflicts_detected,
                strategy='no_majority'
            )

    def _extract_decision(self, agent_result: Any) -> str:
        """Extract decision from agent result (handles dict or object)."""
        if agent_result is None:
            return 'reject'

        if isinstance(agent_result, dict):
            return agent_result.get('decision', 'reject')
        else:
            return getattr(agent_result, 'decision', 'reject')

    def _calculate_average_score(self, agent_results: Dict[str, Any]) -> float:
        """Calculate average score from all agents."""
        scores = []

        for result in agent_results.values():
            if isinstance(result, dict):
                score = result.get('score', 0)
            else:
                score = getattr(result, 'score', 0)

            if isinstance(score, (int, float)):
                scores.append(score)

        return sum(scores) / len(scores) if scores else 0.0

    def _collect_warnings(self, agent_results: Dict[str, Any]) -> List[str]:
        """Collect warnings from all agents."""
        warnings = []

        for agent_name, result in agent_results.items():
            if isinstance(result, dict):
                agent_warnings = result.get('warnings', [])
            else:
                agent_warnings = getattr(result, 'warnings', [])

            if agent_warnings:
                warnings.extend([f"{agent_name}: {w}" for w in agent_warnings])

        return warnings

    def _collect_rejection_reasons(self, agent_results: Dict[str, Any]) -> List[str]:
        """Collect rejection reasons from agents that rejected."""
        reasons = []

        for agent_name, result in agent_results.items():
            decision = self._extract_decision(result)

            if decision == 'reject':
                if isinstance(result, dict):
                    reasoning = result.get('reasoning', 'No reason provided')
                else:
                    reasoning = getattr(result, 'reasoning', 'No reason provided')

                reasons.append(f"{agent_name}: {reasoning}")

        return reasons

    def _create_decision(
        self,
        decision: str,
        confidence: float,
        reason: str,
        agent_votes: Dict[str, str],
        conflicts: List[str],
        strategy: str
    ) -> Dict[str, Any]:
        """Create standardized orchestration decision."""
        return {
            'decision': decision,
            'confidence': confidence,
            'reason': reason,
            'agent_votes': agent_votes,
            'conflicts_detected': conflicts,
            'resolution_strategy': strategy,
            'timestamp': datetime.utcnow().isoformat()
        }
