"""
Performance Monitoring and Metrics Collection

Tracks latency, token usage, cost, and error rates for all validations
to ensure consistent performance and identify issues early.

Author: VerifiMind PEAS Team
Date: December 21, 2025
Version: 1.0.0
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import json

from verifimind_mcp.config.standard_config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Metrics for a single agent execution."""
    
    agent_type: str  # x, z, or cs
    model_name: str
    
    # Timing
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    latency: Optional[float] = None  # seconds
    
    # Token Usage
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    # Cost (USD)
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    
    # Reliability
    retry_count: int = 0
    error_count: int = 0
    success: bool = False
    error_message: Optional[str] = None
    
    def finish(self):
        """Mark agent execution as finished and calculate latency."""
        self.end_time = time.time()
        self.latency = self.end_time - self.start_time
    
    def calculate_cost(self, provider: Optional[str] = None):
        """Calculate cost based on token usage and provider pricing."""
        # Pricing per 1M tokens (as of Dec 2025)
        pricing = {
            "openai": {
                "gpt-4-0613": {
                    "input": 30.0,  # $30 per 1M input tokens
                    "output": 60.0,  # $60 per 1M output tokens
                },
                "gpt-4-turbo": {
                    "input": 10.0,  # $10 per 1M input tokens
                    "output": 30.0,  # $30 per 1M output tokens
                },
            },
            "anthropic": {
                "claude-3-haiku-20240307": {
                    "input": 0.25,  # $0.25 per 1M input tokens
                    "output": 1.25,  # $1.25 per 1M output tokens
                },
                "claude-3-5-sonnet": {
                    "input": 3.0,
                    "output": 15.0,
                },
            },
            "gemini": {
                "gemini-2.5-flash": {
                    "input": 0.0,  # FREE (within limits)
                    "output": 0.0,  # FREE (within limits)
                },
                "gemini-1.5-pro": {
                    "input": 1.25,  # $1.25 per 1M input tokens
                    "output": 5.0,  # $5.00 per 1M output tokens
                },
                "gemini-1.5-flash": {
                    "input": 0.075,  # $0.075 per 1M input tokens
                    "output": 0.30,  # $0.30 per 1M output tokens
                },
            },
        }
        
        # Extract provider and model from model_name
        if "/" in self.model_name:
            provider_name, model = self.model_name.split("/", 1)
        elif provider:
            provider_name = provider
            model = self.model_name
        else:
            # Auto-detect provider from model name
            if "gpt" in self.model_name.lower():
                provider_name = "openai"
            elif "claude" in self.model_name.lower():
                provider_name = "anthropic"
            elif "gemini" in self.model_name.lower():
                provider_name = "gemini"
            else:
                logger.warning(f"Cannot detect provider for model: {self.model_name}")
                return
            model = self.model_name
        
        # Get pricing for this model
        model_pricing = None
        if provider_name in pricing:
            for model_key, prices in pricing[provider_name].items():
                if model_key in model:
                    model_pricing = prices
                    break
        
        if model_pricing:
            self.input_cost = (self.input_tokens / 1_000_000) * model_pricing["input"]
            self.output_cost = (self.output_tokens / 1_000_000) * model_pricing["output"]
            self.total_cost = self.input_cost + self.output_cost
        else:
            logger.warning(f"Unknown model pricing for {self.model_name}, cost not calculated")


@dataclass
class ValidationMetrics:
    """Metrics for a complete validation (X + Z + CS)."""
    
    validation_id: str
    concept_name: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Agent Metrics
    x_agent: Optional[AgentMetrics] = None
    z_agent: Optional[AgentMetrics] = None
    cs_agent: Optional[AgentMetrics] = None
    
    # Overall Timing
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_duration: Optional[float] = None  # seconds
    
    # Overall Token Usage
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    
    # Overall Cost
    total_cost: float = 0.0
    
    # Overall Reliability
    total_retry_count: int = 0
    total_error_count: int = 0
    success: bool = False
    
    # Results
    overall_score: Optional[float] = None
    verdict: Optional[str] = None
    
    def finish(self):
        """Mark validation as finished and aggregate metrics."""
        self.end_time = time.time()
        self.total_duration = self.end_time - self.start_time
        
        # Aggregate metrics from all agents
        for agent in [self.x_agent, self.z_agent, self.cs_agent]:
            if agent:
                self.total_input_tokens += agent.input_tokens
                self.total_output_tokens += agent.output_tokens
                self.total_tokens += agent.total_tokens
                self.total_cost += agent.total_cost
                self.total_retry_count += agent.retry_count
                self.total_error_count += agent.error_count
        
        # Mark success if all agents succeeded
        self.success = all(
            agent.success if agent else False
            for agent in [self.x_agent, self.z_agent, self.cs_agent]
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        
        # Convert nested dataclasses
        for key in ["x_agent", "z_agent", "cs_agent"]:
            if data[key]:
                data[key] = asdict(data[key])
        
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def save(self, filepath: str):
        """Save metrics to file."""
        with open(filepath, "w") as f:
            f.write(self.to_json())
        logger.info(f"Metrics saved to {filepath}")


class MetricsCollector:
    """Collects and aggregates metrics across multiple validations."""
    
    def __init__(self):
        self.validations: list[ValidationMetrics] = []
        self.enabled = DEFAULT_CONFIG.monitoring.track_metrics
    
    def add_validation(self, metrics: ValidationMetrics):
        """Add validation metrics to collection."""
        if self.enabled:
            self.validations.append(metrics)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics across all validations."""
        if not self.validations:
            return {"error": "No validations collected"}
        
        total_validations = len(self.validations)
        successful_validations = sum(1 for v in self.validations if v.success)
        
        # Calculate averages
        avg_duration = sum(v.total_duration or 0 for v in self.validations) / total_validations
        avg_tokens = sum(v.total_tokens for v in self.validations) / total_validations
        avg_cost = sum(v.total_cost for v in self.validations) / total_validations
        total_cost = sum(v.total_cost for v in self.validations)
        
        # Calculate error rate
        total_errors = sum(v.total_error_count for v in self.validations)
        total_retries = sum(v.total_retry_count for v in self.validations)
        error_rate = total_errors / total_validations if total_validations > 0 else 0
        
        # Calculate latency by agent
        agent_latencies = {
            "x_agent": [],
            "z_agent": [],
            "cs_agent": [],
        }
        
        for v in self.validations:
            if v.x_agent and v.x_agent.latency:
                agent_latencies["x_agent"].append(v.x_agent.latency)
            if v.z_agent and v.z_agent.latency:
                agent_latencies["z_agent"].append(v.z_agent.latency)
            if v.cs_agent and v.cs_agent.latency:
                agent_latencies["cs_agent"].append(v.cs_agent.latency)
        
        avg_latencies = {
            agent: sum(latencies) / len(latencies) if latencies else 0
            for agent, latencies in agent_latencies.items()
        }
        
        return {
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "success_rate": successful_validations / total_validations,
            "error_rate": error_rate,
            "total_errors": total_errors,
            "total_retries": total_retries,
            "avg_duration": avg_duration,
            "avg_tokens": avg_tokens,
            "avg_cost": avg_cost,
            "total_cost": total_cost,
            "avg_latencies": avg_latencies,
        }
    
    def save_summary(self, filepath: str):
        """Save summary statistics to file."""
        summary = self.get_summary()
        with open(filepath, "w") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Summary saved to {filepath}")
    
    def save_all(self, filepath: str):
        """Save all validation metrics to file."""
        data = {
            "summary": self.get_summary(),
            "validations": [v.to_dict() for v in self.validations],
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"All metrics saved to {filepath}")


# Global metrics collector
METRICS_COLLECTOR = MetricsCollector()
