"""
Data models for VerifiMind-PEAS MCP Server.

This module exports all data models used by the MCP server,
including concepts, reasoning chains, and validation results.
"""

from .concepts import (
    Concept,
    ValidationRequest,
    AgentConfig,
    X_AGENT_CONFIG,
    Z_AGENT_CONFIG,
    CS_AGENT_CONFIG,
    AGENT_CONFIGS,
    get_agent_config
)

from .reasoning import (
    ReasoningStep,
    ChainOfThought,
    XAgentAnalysis,
    ZAgentAnalysis,
    CSAgentAnalysis,
    PriorReasoning
)

from .results import (
    TrinitySynthesis,
    TrinityResult,
    ValidationHistoryEntry,
    ValidationHistory
)

__all__ = [
    # Concepts
    "Concept",
    "ValidationRequest",
    "AgentConfig",
    "X_AGENT_CONFIG",
    "Z_AGENT_CONFIG",
    "CS_AGENT_CONFIG",
    "AGENT_CONFIGS",
    "get_agent_config",
    
    # Reasoning
    "ReasoningStep",
    "ChainOfThought",
    "XAgentAnalysis",
    "ZAgentAnalysis",
    "CSAgentAnalysis",
    "PriorReasoning",
    
    # Results
    "TrinitySynthesis",
    "TrinityResult",
    "ValidationHistoryEntry",
    "ValidationHistory"
]
