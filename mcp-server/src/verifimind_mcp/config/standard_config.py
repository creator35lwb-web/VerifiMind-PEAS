"""
VerifiMind PEAS Standard Configuration v1.0

This module defines the standard configuration for LLM parameters,
API reliability settings, and performance monitoring to ensure
consistent, reproducible, and reliable validation results.

Author: VerifiMind PEAS Team
Date: December 21, 2025
Version: 1.0.0
"""

from typing import Dict, Any, List
from dataclasses import dataclass
import random


@dataclass
class LLMConfig:
    """Standard LLM configuration for consistent results."""
    
    # Model Selection (Pinned Versions)
    x_agent_model: str = "gemini-2.5-flash"  # Google Gemini 2.5 Flash (creative, free tier)
    z_agent_model: str = "claude-3-haiku-20240307"  # Anthropic Claude Haiku (pinned)
    cs_agent_model: str = "claude-3-haiku-20240307"  # Anthropic Claude Haiku (pinned)
    
    # Temperature Settings
    # 0.0 = Deterministic (too rigid)
    # 1.0 = Creative (too random)
    # 0.7 = Sweet spot for analytical reasoning
    temperature: float = 0.7
    
    # Token Limits
    max_tokens_x: int = 2000  # X Agent (Innovation)
    max_tokens_z: int = 2000  # Z Agent (Ethics)
    max_tokens_cs: int = 2000  # CS Agent (Security)
    
    # Sampling Parameters
    top_p: float = 0.9  # Nucleus sampling
    frequency_penalty: float = 0.0  # No penalty for repetition
    presence_penalty: float = 0.0  # No penalty for new topics
    
    # Reproducibility
    use_seed: bool = True
    seed: int = 42  # Default seed for deterministic results
    
    # Chain of Thought
    cot_steps: int = 5  # Fixed number of reasoning steps
    cot_confidence_decay: float = 0.05  # 5% decay per step (90% → 70%)
    
    # Prompt Versioning
    prompt_version: str = "1.0.0"
    
    def to_openai_params(self, agent_type: str) -> Dict[str, Any]:
        """Convert to OpenAI API parameters."""
        max_tokens = {
            "x": self.max_tokens_x,
            "z": self.max_tokens_z,
            "cs": self.max_tokens_cs,
        }.get(agent_type, 2000)
        
        params = {
            "temperature": self.temperature,
            "max_tokens": max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }
        
        if self.use_seed:
            params["seed"] = self.seed
        
        return params
    
    def to_anthropic_params(self, agent_type: str) -> Dict[str, Any]:
        """Convert to Anthropic API parameters."""
        max_tokens = {
            "x": self.max_tokens_x,
            "z": self.max_tokens_z,
            "cs": self.max_tokens_cs,
        }.get(agent_type, 2000)
        
        return {
            "temperature": self.temperature,
            "max_tokens": max_tokens,
            "top_p": self.top_p,
        }


@dataclass
class RetryConfig:
    """Retry configuration for API reliability."""
    
    max_retries: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0  # 1s → 2s → 4s → 8s
    jitter: bool = True  # Add randomness to prevent thundering herd
    
    # HTTP status codes to retry on
    retry_on_errors: List[int] = None
    
    def __post_init__(self):
        if self.retry_on_errors is None:
            self.retry_on_errors = [
                429,  # Rate limit
                500,  # Internal server error
                502,  # Bad gateway
                503,  # Service unavailable
                529,  # Overloaded (Anthropic)
            ]
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff and jitter."""
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add 50-150% randomness to prevent thundering herd
            delay *= (0.5 + random.random())
        
        return delay


@dataclass
class RateLimitConfig:
    """Rate limiting configuration to prevent API overloads."""
    
    # OpenAI Limits
    openai_requests_per_minute: int = 60  # Conservative limit
    openai_tokens_per_minute: int = 90000  # GPT-4 limit
    
    # Anthropic Limits
    anthropic_requests_per_minute: int = 50  # Conservative limit
    anthropic_tokens_per_minute: int = 100000  # Claude limit


@dataclass
class MonitoringConfig:
    """Performance monitoring configuration."""
    
    track_metrics: bool = True
    log_level: str = "INFO"
    
    # Metrics to track
    track_latency: bool = True
    track_token_usage: bool = True
    track_cost: bool = True
    track_error_rate: bool = True
    track_retry_count: bool = True
    
    # Quality Benchmarks
    min_reasoning_steps: int = 5
    min_confidence: float = 0.70
    min_explanation_length: int = 100  # characters
    
    # Alerts
    alert_on_high_latency: bool = True
    high_latency_threshold: float = 5.0  # seconds
    
    alert_on_high_error_rate: bool = True
    high_error_rate_threshold: float = 0.10  # 10%


@dataclass
class StandardConfig:
    """Complete standard configuration for VerifiMind PEAS."""
    
    llm: LLMConfig = None
    retry: RetryConfig = None
    rate_limit: RateLimitConfig = None
    monitoring: MonitoringConfig = None
    
    def __post_init__(self):
        if self.llm is None:
            self.llm = LLMConfig()
        if self.retry is None:
            self.retry = RetryConfig()
        if self.rate_limit is None:
            self.rate_limit = RateLimitConfig()
        if self.monitoring is None:
            self.monitoring = MonitoringConfig()
    
    @classmethod
    def load_default(cls) -> "StandardConfig":
        """Load default standard configuration."""
        return cls()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "llm": {
                "x_agent_model": self.llm.x_agent_model,
                "z_agent_model": self.llm.z_agent_model,
                "cs_agent_model": self.llm.cs_agent_model,
                "temperature": self.llm.temperature,
                "max_tokens_x": self.llm.max_tokens_x,
                "max_tokens_z": self.llm.max_tokens_z,
                "max_tokens_cs": self.llm.max_tokens_cs,
                "top_p": self.llm.top_p,
                "use_seed": self.llm.use_seed,
                "seed": self.llm.seed,
                "prompt_version": self.llm.prompt_version,
            },
            "retry": {
                "max_retries": self.retry.max_retries,
                "initial_delay": self.retry.initial_delay,
                "max_delay": self.retry.max_delay,
                "exponential_base": self.retry.exponential_base,
                "jitter": self.retry.jitter,
                "retry_on_errors": self.retry.retry_on_errors,
            },
            "rate_limit": {
                "openai_requests_per_minute": self.rate_limit.openai_requests_per_minute,
                "openai_tokens_per_minute": self.rate_limit.openai_tokens_per_minute,
                "anthropic_requests_per_minute": self.rate_limit.anthropic_requests_per_minute,
                "anthropic_tokens_per_minute": self.rate_limit.anthropic_tokens_per_minute,
            },
            "monitoring": {
                "track_metrics": self.monitoring.track_metrics,
                "min_confidence": self.monitoring.min_confidence,
                "high_latency_threshold": self.monitoring.high_latency_threshold,
                "high_error_rate_threshold": self.monitoring.high_error_rate_threshold,
            },
        }


# Global default configuration
DEFAULT_CONFIG = StandardConfig.load_default()
