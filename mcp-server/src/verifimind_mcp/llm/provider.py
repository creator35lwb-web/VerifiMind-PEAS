"""
LLM Provider abstraction for VerifiMind-PEAS MCP Server.

This module provides a unified interface for interacting with
different LLM providers (OpenAI, Anthropic, etc.), enabling
the MCP server to work with any supported LLM.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers must implement the generate() method,
    which takes a prompt and returns a structured response.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The input prompt
            output_schema: Optional JSON schema for structured output
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Parsed JSON response as a dictionary
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name being used."""
        pass


class OpenAIProvider(LLMProvider):
    """
    OpenAI GPT provider implementation.
    
    Supports GPT-4, GPT-4 Turbo, and GPT-3.5 Turbo models.
    Uses JSON mode for structured output when schema is provided.
    """
    
    def __init__(
        self,
        model: str = "gpt-4-turbo-preview",
        api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        # Import here to avoid requiring openai if not used
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using OpenAI API."""
        
        messages = [{"role": "user", "content": prompt}]
        
        # Use JSON mode if schema provided
        response_format = None
        if output_schema:
            response_format = {"type": "json_object"}
            # Add schema hint to prompt
            messages[0]["content"] += f"\n\nRespond with valid JSON matching this schema:\n{json.dumps(output_schema, indent=2)}"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format
            )
            
            content = response.choices[0].message.content
            
            # Extract token usage
            usage = {
                "input_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                "output_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
            # Parse JSON response
            try:
                parsed_content = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Raw response: {content}")
                # Return raw content wrapped in dict
                parsed_content = {"raw_response": content, "parse_error": str(e)}
            
            # Return both content and usage
            return {
                "content": parsed_content,
                "usage": usage
            }
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def get_model_name(self) -> str:
        return f"openai/{self.model}"


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude provider implementation.
    
    Supports Claude 3.5 Sonnet, Claude 3 Opus, and other Claude models.
    Uses prompt engineering for structured output.
    """
    
    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable.")
        
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using Anthropic API."""
        
        # Add JSON instruction if schema provided
        if output_schema:
            prompt += f"\n\nRespond with valid JSON only, matching this schema:\n{json.dumps(output_schema, indent=2)}\n\nJSON Response:"
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            
            # Extract token usage
            usage = {
                "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else 0,
                "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else 0,
                "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if hasattr(response, 'usage') else 0
            }
            
            # Parse JSON response
            try:
                # Try to extract JSON from response
                if content.strip().startswith("{"):
                    parsed_content = json.loads(content)
                else:
                    # Try to find JSON in response
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        parsed_content = json.loads(json_match.group())
                    else:
                        parsed_content = {"raw_response": content}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                parsed_content = {"raw_response": content, "parse_error": str(e)}
            
            # Return both content and usage
            return {
                "content": parsed_content,
                "usage": usage
            }
                
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    def get_model_name(self) -> str:
        return f"anthropic/{self.model}"


class GeminiProvider(LLMProvider):
    """
    Google Gemini provider implementation.
    
    Supports Gemini 2.0 Flash, Gemini 1.5 Pro, and other Gemini models.
    Uses prompt engineering for structured JSON output.
    """
    
    def __init__(
        self,
        model: str = "gemini-2.0-flash-exp",
        api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY environment variable.")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
    
    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using Gemini API."""
        
        # Add JSON instruction if schema provided
        if output_schema:
            prompt += f"\n\nRespond with valid JSON only, matching this schema:\n{json.dumps(output_schema, indent=2)}\n\nJSON Response:"
        
        try:
            # Create model instance
            model = self.genai.GenerativeModel(self.model)
            
            # Generate response (synchronous call)
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )
            
            content = response.text
            
            # Extract token usage
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            }
            
            # Parse JSON response
            try:
                # Try to extract JSON from response
                if content.strip().startswith("{"):
                    parsed_content = json.loads(content)
                else:
                    # Try to find JSON in response
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        parsed_content = json.loads(json_match.group())
                    else:
                        parsed_content = {"raw_response": content}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                parsed_content = {"raw_response": content, "parse_error": str(e)}
            
            # Return both content and usage
            return {
                "content": parsed_content,
                "usage": usage
            }
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def get_model_name(self) -> str:
        return f"gemini/{self.model}"


class MockProvider(LLMProvider):
    """
    Mock LLM provider for testing.
    
    Returns predefined responses without making API calls.
    Useful for development and testing.
    """
    
    def __init__(self, responses: Optional[Dict[str, Dict]] = None):
        self.responses = responses or {}
        self.call_count = 0
    
    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Return mock response based on schema type."""
        self.call_count += 1
        
        # Check for predefined response
        for key, response in self.responses.items():
            if key in prompt:
                return response
        
        # Determine agent type from schema
        schema_title = output_schema.get("title", "") if output_schema else ""
        
        # Base reasoning steps for all agents
        reasoning_steps = [
            {
                "step_number": 1,
                "thought": "Analyzing the concept from my specialized perspective.",
                "evidence": "Based on the provided description and context.",
                "confidence": 0.85
            },
            {
                "step_number": 2,
                "thought": "Evaluating key factors and potential implications.",
                "evidence": "Industry best practices and standards.",
                "confidence": 0.80
            }
        ]
        
        # Return agent-specific mock response
        if "ZAgentAnalysis" in schema_title:
            return {
                "reasoning_steps": reasoning_steps,
                "ethics_score": 7.5,
                "z_protocol_compliance": True,
                "ethical_concerns": ["Data privacy considerations", "Potential for misuse"],
                "mitigation_measures": ["Implement access controls", "Add audit logging"],
                "recommendation": "Proceed with ethical safeguards in place.",
                "veto_triggered": False,
                "confidence": 0.82
            }
        elif "CSAgentAnalysis" in schema_title:
            return {
                "reasoning_steps": reasoning_steps,
                "security_score": 6.5,
                "vulnerabilities": ["Input validation needed", "Authentication gaps"],
                "attack_vectors": ["Injection attacks", "Unauthorized access"],
                "security_recommendations": ["Add input sanitization", "Implement MFA"],
                "socratic_questions": ["What happens if the API key is compromised?", "How do we handle malicious inputs?"],
                "recommendation": "Address security concerns before deployment.",
                "confidence": 0.78
            }
        else:
            # Default to X Agent response
            return {
                "reasoning_steps": reasoning_steps,
                "innovation_score": 7.5,
                "strategic_value": 8.0,
                "opportunities": ["Market differentiation", "Efficiency gains", "Scalability potential"],
                "risks": ["Competition", "Technical complexity"],
                "recommendation": "Strong innovation potential with manageable risks.",
                "confidence": 0.85
            }
    
    def get_model_name(self) -> str:
        return "mock/test-model"


# Provider registry
_PROVIDERS: Dict[str, Type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "mock": MockProvider
}


def get_provider(
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Get an LLM provider instance.
    
    Args:
        provider_name: Provider name (openai, anthropic, mock)
                      Defaults to VERIFIMIND_LLM_PROVIDER env var or "openai"
        model: Model name to use
               Defaults to VERIFIMIND_LLM_MODEL env var or provider default
        **kwargs: Additional arguments passed to provider constructor
        
    Returns:
        Configured LLMProvider instance
    """
    # Get provider name from env if not specified
    if provider_name is None:
        provider_name = os.getenv("VERIFIMIND_LLM_PROVIDER", "openai")
    
    provider_name = provider_name.lower()
    
    if provider_name not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available providers: {list(_PROVIDERS.keys())}"
        )
    
    # Get model from env if not specified
    if model is None:
        model = os.getenv("VERIFIMIND_LLM_MODEL")
    
    # Build kwargs
    if model:
        kwargs["model"] = model
    
    return _PROVIDERS[provider_name](**kwargs)


def register_provider(name: str, provider_class: Type[LLMProvider]) -> None:
    """
    Register a custom LLM provider.
    
    Args:
        name: Provider name for lookup
        provider_class: Provider class implementing LLMProvider
    """
    _PROVIDERS[name.lower()] = provider_class
