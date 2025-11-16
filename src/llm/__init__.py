"""
VerifiMind LLM Provider Module

Abstraction layer for multiple LLM providers (OpenAI, Anthropic, etc.)
Enhanced with comprehensive error handling.
"""

from .llm_provider import (
    # Core classes
    LLMMessage,
    LLMResponse,
    BaseLLMProvider,
    OpenAIProvider,
    AnthropicProvider,
    LocalModelProvider,
    LLMProviderFactory,
    # Custom exceptions
    LLMProviderError,
    LLMAPIError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMTimeoutError,
    LLMInvalidRequestError,
    # Convenience functions
    generate_completion,
)

__all__ = [
    # Core classes
    'LLMMessage',
    'LLMResponse',
    'BaseLLMProvider',
    'OpenAIProvider',
    'AnthropicProvider',
    'LocalModelProvider',
    'LLMProviderFactory',
    # Exceptions
    'LLMProviderError',
    'LLMAPIError',
    'LLMRateLimitError',
    'LLMAuthenticationError',
    'LLMTimeoutError',
    'LLMInvalidRequestError',
    # Functions
    'generate_completion',
]
