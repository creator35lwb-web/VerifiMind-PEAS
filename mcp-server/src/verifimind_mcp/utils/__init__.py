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
