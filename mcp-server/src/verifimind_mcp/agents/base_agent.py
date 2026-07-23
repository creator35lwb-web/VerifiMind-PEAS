"""
Base Agent class for VerifiMind-PEAS MCP Server.

This module provides the foundational agent class that all
specialized agents (X, Z, CS) inherit from. It implements
Chain of Thought reasoning and LLM interaction.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Type

from pydantic import BaseModel

from ..models import (
    Concept,
    AgentConfig,
    ChainOfThought,
    PriorReasoning,
    get_agent_config
)
from ..llm import LLMProvider, get_provider

try:
    from ..utils.metrics import AgentMetrics
except ImportError:
    AgentMetrics = None

logger = logging.getLogger(__name__)

# Groq free-tier carries a tighter total-request budget (~12K tokens input+output)
# than large-context providers. Agent configs request 8192 output tokens so verbose
# models (Claude, GPT) don't truncate mid-JSON; for Groq we clamp output back to a
# safe ceiling so the full request stays under the budget. Large-context providers
# (Anthropic, OpenAI, Gemini, Mistral, Cerebras) use the configured value unchanged.
GROQ_SAFE_MAX_OUTPUT_TOKENS = 4096


class BaseAgent(ABC):
    """
    Abstract base class for all VerifiMind agents.
    
    Provides common functionality for:
    - LLM interaction
    - Chain of Thought reasoning
    - Prior reasoning integration
    - Structured output parsing
    """
    
    # Subclasses must define these
    AGENT_ID: str = ""
    OUTPUT_MODEL: Type[BaseModel] = None
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        llm_provider: Optional[LLMProvider] = None
    ):
        """
        Initialize the agent.
        
        Args:
            config: Agent configuration (uses default if not provided)
            llm_provider: LLM provider instance (creates default if not provided)
        """
        if not self.AGENT_ID:
            raise ValueError("AGENT_ID must be defined in subclass")
        
        self.config = config or get_agent_config(self.AGENT_ID)
        self.llm = llm_provider or get_provider()
        
        logger.info(f"Initialized {self.config.name} agent with {self.llm.get_model_name()}")
    
    def build_prompt(
        self,
        concept: Concept,
        prior_reasoning: Optional[PriorReasoning] = None
    ) -> str:
        """
        Build the analysis prompt for the LLM.
        
        Args:
            concept: The concept to analyze
            prior_reasoning: Optional reasoning from previous agents
            
        Returns:
            Complete prompt string
        """
        # Format prior reasoning if available
        prior_context = ""
        if prior_reasoning and prior_reasoning.chains:
            prior_context = prior_reasoning.format_for_prompt()
        
        # Build prompt from template
        prompt = self.config.prompt_template.format(
            concept_name=concept.name,
            concept_description=concept.description,
            context=concept.context or "No additional context provided.",
            prior_reasoning=prior_context
        )

        # v0.5.43: anchor the model to the real current date. Without this, agents
        # default to their training-cutoff year (research prompts said "2024") and
        # Z's "upcoming deadline" reasoning silently rots as regulations take effect.
        from datetime import date
        today = date.today()
        date_header = (
            f"CURRENT DATE: {today.isoformat()} ({today.strftime('%B %d, %Y')}). "
            "Treat this as today when assessing market timing, recency, and whether "
            "any cited regulatory deadline is upcoming or already in effect.\n\n"
        )

        return date_header + prompt

    def _effective_max_tokens(self) -> int:
        """
        Resolve the output-token budget for the active provider.

        Configs request 8192 so verbose models don't truncate; Groq's tighter
        total-request budget is honored by clamping to a safe ceiling. Detected
        by provider class name to avoid importing every provider type here.
        """
        configured = self.config.max_tokens
        provider_name = type(self.llm).__name__.lower()
        if "groq" in provider_name:
            return min(configured, GROQ_SAFE_MAX_OUTPUT_TOKENS)
        return configured

    async def analyze(
        self,
        concept: Concept,
        prior_reasoning: Optional[PriorReasoning] = None,
        metrics: Optional[Any] = None
    ) -> BaseModel:
        """
        Analyze a concept with Chain of Thought reasoning.
        
        Args:
            concept: The concept to analyze
            prior_reasoning: Optional reasoning from previous agents
            metrics: Optional metrics object to track performance
            
        Returns:
            Structured analysis result (specific to agent type)
        """
        if self.OUTPUT_MODEL is None:
            raise ValueError("OUTPUT_MODEL must be defined in subclass")
        
        # Initialize metrics if provided
        if metrics and AgentMetrics:
            metrics.agent_type = self.AGENT_ID.lower()
            metrics.model_name = self.llm.get_model_name()
        
        # Build prompt
        prompt = self.build_prompt(concept, prior_reasoning)
        
        logger.debug(f"{self.config.name} analyzing concept: {concept.name}")
        
        # Get output schema
        output_schema = self.OUTPUT_MODEL.model_json_schema()
        
        # Call LLM — through the WP-B failover executor. For unmarked
        # providers (all BYOK/Ollama/override/mock) or with the runtime flag
        # off, this is a plain delegated provider.generate() call.
        from ..llm.failover import generate_with_failover
        try:
            response = await generate_with_failover(
                self.llm,
                prompt=prompt,
                output_schema=output_schema,
                temperature=self.config.temperature,
                max_tokens=self._effective_max_tokens()
            )
            
            # Extract content, usage, and inference quality from response
            if isinstance(response, dict) and "content" in response:
                content = response["content"]
                usage = response.get("usage", {})
                inference_quality = response.get("_inference_quality", "unknown")
            else:
                # Backward compatibility: response is content directly
                content = response
                usage = {}
                inference_quality = "unknown"

            # Parse response into model
            result = self.OUTPUT_MODEL.model_validate(content)

            # v0.4.3.1 C-S-P State: attach inference quality marker to result
            result._inference_quality = inference_quality

            # WP-B: attempt disclosure (present only when the failover
            # executor ran for a marked hosted provider; absent otherwise).
            # The quality marker above is the FINAL provider's true stamp —
            # a hop never upgrades it.
            if isinstance(response, dict) and "_provider_attempts" in response:
                result._provider_attempts = response["_provider_attempts"]
                result._failover_occurred = response.get("_failover_occurred", False)

            # v0.5.46 (P2-2 repair): expose API-reported output tokens on the result so
            # the Z-Agent token-ceiling monitor (server.py) reads a real count. Previously
            # `_output_tokens` was never populated → the monitor always saw 0 and never
            # fired, masking truncation since v0.5.3.
            result._output_tokens = usage.get("output_tokens", 0) if usage else 0

            # Update metrics if provided
            if metrics:
                if usage:
                    metrics.input_tokens = usage.get("input_tokens", 0)
                    metrics.output_tokens = usage.get("output_tokens", 0)
                    metrics.total_tokens = usage.get("total_tokens", 0)
                    metrics.calculate_cost()
                metrics.success = True
                metrics.finish()

            logger.info(f"{self.config.name} completed analysis with confidence: {result.confidence} (quality: {inference_quality})")

            return result
            
        except Exception as e:
            logger.error(f"{self.config.name} analysis failed: {e}")
            if metrics:
                metrics.error_count += 1
                metrics.error_message = str(e)
                metrics.finish()
            raise
    
    async def analyze_with_cot(
        self,
        concept: Concept,
        prior_reasoning: Optional[PriorReasoning] = None
    ) -> ChainOfThought:
        """
        Analyze and return as ChainOfThought for passing to next agent.
        
        Args:
            concept: The concept to analyze
            prior_reasoning: Optional reasoning from previous agents
            
        Returns:
            ChainOfThought that can be passed to next agent
        """
        result = await self.analyze(concept, prior_reasoning)
        
        # Convert to ChainOfThought
        return result.to_chain_of_thought(concept.name)
    
    def to_dict(self, result: BaseModel) -> Dict[str, Any]:
        """Convert result to dictionary for MCP tool response."""
        return result.model_dump()
    
    @abstractmethod
    def get_focus_summary(self) -> str:
        """Return a brief summary of this agent's focus areas."""
        pass


class AgentRegistry:
    """
    Registry for managing agent instances.
    
    Provides singleton-like access to agent instances,
    ensuring consistent configuration across the MCP server.
    """
    
    _instances: Dict[str, BaseAgent] = {}
    _llm_provider: Optional[LLMProvider] = None
    
    @classmethod
    def set_llm_provider(cls, provider: LLMProvider) -> None:
        """Set the LLM provider for all agents."""
        cls._llm_provider = provider
        # Clear existing instances to recreate with new provider
        cls._instances.clear()
    
    @classmethod
    def get_agent(cls, agent_id: str) -> BaseAgent:
        """
        Get an agent instance by ID.
        
        Args:
            agent_id: Agent identifier (X, Z, or CS)
            
        Returns:
            Agent instance
        """
        if agent_id not in cls._instances:
            # Import here to avoid circular imports
            from .x_agent import XAgent
            from .z_agent import ZAgent
            from .cs_agent import CSAgent
            
            agent_classes = {
                "X": XAgent,
                "Z": ZAgent,
                "CS": CSAgent
            }
            
            if agent_id not in agent_classes:
                raise ValueError(f"Unknown agent: {agent_id}")
            
            cls._instances[agent_id] = agent_classes[agent_id](
                llm_provider=cls._llm_provider
            )
        
        return cls._instances[agent_id]
    
    @classmethod
    def get_all_agents(cls) -> Dict[str, BaseAgent]:
        """Get all agent instances."""
        for agent_id in ["X", "Z", "CS"]:
            cls.get_agent(agent_id)
        return cls._instances.copy()
    
    @classmethod
    def clear(cls) -> None:
        """Clear all agent instances."""
        cls._instances.clear()
        cls._llm_provider = None
