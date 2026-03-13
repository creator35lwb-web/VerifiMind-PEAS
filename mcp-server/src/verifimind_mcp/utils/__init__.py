"""
Utility module for VerifiMind-PEAS MCP Server.

Provides helper functions for synthesis, prompt building, and input sanitization.
"""

from .synthesis import (
    calculate_overall_score,
    determine_recommendation,
    synthesize_strengths,
    synthesize_concerns,
    synthesize_recommendations,
    create_synthesis,
    create_trinity_result
)

from .token_monitor import (
    check_z_agent_response,
    is_z_response_safe,
    Z_AGENT_CEILING,
)

from .sanitization import (
    sanitize_concept_name,
    sanitize_description,
    sanitize_category,
    sanitize_context,
    sanitize_concept_input,
    detect_prompt_injection,
    is_safe_input,
    SanitizationResult,
    SanitizationError
)

__all__ = [
    # Token monitor
    "check_z_agent_response",
    "is_z_response_safe",
    "Z_AGENT_CEILING",
    # Synthesis functions
    "calculate_overall_score",
    "determine_recommendation",
    "synthesize_strengths",
    "synthesize_concerns",
    "synthesize_recommendations",
    "create_synthesis",
    "create_trinity_result",
    # Sanitization functions
    "sanitize_concept_name",
    "sanitize_description",
    "sanitize_category",
    "sanitize_context",
    "sanitize_concept_input",
    "detect_prompt_injection",
    "is_safe_input",
    "SanitizationResult",
    "SanitizationError"
]
