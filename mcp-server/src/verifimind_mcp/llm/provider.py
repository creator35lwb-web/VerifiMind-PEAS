"""
LLM Provider abstraction for VerifiMind-PEAS MCP Server.

BYOK v0.3.0 - Multi-Provider Support with Fallback

This module provides a unified interface for interacting with
different LLM providers, enabling users to bring their own API keys
(BYOK) for any supported provider.

Supported Providers:
- Gemini (FREE tier available)
- Groq (FREE tier available)
- OpenAI
- Anthropic
- Mistral
- Ollama (local, FREE)
- Mock (testing)

Environment Variables:
- LLM_PROVIDER: Primary provider (default: mock)
- LLM_FALLBACK_PROVIDER: Fallback if primary fails (default: mock)
- LLM_MODEL: Override default model
- LLM_TEMPERATURE: Override temperature (default: 0.7)
- LLM_MAX_TOKENS: Override max tokens (default: 4096)
- {PROVIDER}_API_KEY: API key for each provider
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def strip_markdown_code_fences(text: str) -> str:
    """
    Strip markdown code fences from LLM responses.

    Many LLMs wrap JSON output in markdown code blocks like:
    ```json
    {...}
    ```

    This function removes those fences to get clean JSON.
    Handles cases where text appears before/after the code fence.
    """
    import re
    text = text.strip()

    # Method 1: Extract content from ANY code fence in the text (not just at start)
    # This handles "Here is the analysis:\n```json\n{...}\n```"
    fence_pattern = r'```(?:json|JSON)?\s*\n([\s\S]*?)\n```'
    fence_match = re.search(fence_pattern, text)
    if fence_match:
        return fence_match.group(1).strip()

    # Method 2: Full fence pattern (strict match — text IS the fence)
    pattern = r'^```(?:json|JSON)?\s*\n?([\s\S]*?)\n?```\s*$'
    match = re.match(pattern, text)
    if match:
        return match.group(1).strip()

    # Method 3: Remove leading fence and trailing fence separately
    if text.startswith('```'):
        first_newline = text.find('\n')
        if first_newline != -1:
            text = text[first_newline + 1:]
        else:
            text = re.sub(r'^```(?:json|JSON)?\s*', '', text)

    if text.rstrip().endswith('```'):
        text = re.sub(r'\n?```\s*$', '', text)

    return text.strip()


# ============================================================================
# PROVIDER CONFIGURATION (BYOK v0.3.0)
# ============================================================================

PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
    "gemini": {
        "name": "Google Gemini",
        "default_model": "gemini-2.5-flash",
        "models": ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash"],
        "api_key_env": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "free_tier": True,
        "rate_limit": 15,  # requests per minute on free tier
    },
    "openai": {
        "name": "OpenAI",
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "free_tier": False,
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "default_model": "claude-3-5-sonnet-20241022",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        "api_key_env": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1",
        "free_tier": False,
    },
    "groq": {
        "name": "Groq",
        "default_model": "llama-3.3-70b-versatile",
        "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
        "api_key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "free_tier": True,
        "rate_limit": 30,
    },
    "mistral": {
        "name": "Mistral AI",
        "default_model": "mistral-small-latest",
        "models": ["mistral-small-latest", "mistral-large-latest"],
        "api_key_env": "MISTRAL_API_KEY",
        "base_url": "https://api.mistral.ai/v1",
        "free_tier": False,
    },
    "ollama": {
        "name": "Ollama (Local)",
        "default_model": "llama3.2",
        "models": [],  # Dynamic based on local installation
        "api_key_env": None,  # No API key needed
        "base_url": "http://localhost:11434/v1",
        "free_tier": True,
    },
    "mock": {
        "name": "Mock Provider",
        "default_model": "mock-v1",
        "models": ["mock-v1"],
        "api_key_env": None,
        "base_url": None,
        "free_tier": True,
    },
}


@dataclass
class LLMResponse:
    """Structured response from LLM provider."""
    content: str
    model: str
    provider: str
    tokens_used: int
    latency_ms: float
    raw_response: Optional[Dict[str, Any]] = None


def get_provider_info(provider_name: str) -> Dict[str, Any]:
    """Get configuration info for a provider."""
    return PROVIDER_CONFIGS.get(provider_name.lower(), {})


def list_providers() -> List[Dict[str, Any]]:
    """List all available providers with their configurations."""
    return [
        {"id": name, **config}
        for name, config in PROVIDER_CONFIGS.items()
    ]


def list_free_tier_providers() -> List[str]:
    """List providers with free tier available."""
    return [
        name for name, config in PROVIDER_CONFIGS.items()
        if config.get("free_tier", False)
    ]


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

    Supports Gemini 2.5 Flash, Gemini 2.0 Flash, and other Gemini models.
    Uses prompt engineering for structured JSON output.

    Default: gemini-2.5-flash (FREE tier, reliable, fast)
    Note: Gemini 1.5 models retired in 2026
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
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
    
    def _build_response_schema(self, output_schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a JSON Schema (from Pydantic) to Gemini's response_schema format.

        Gemini structured output requires a subset of OpenAPI 3.0 schema.
        We strip unsupported fields (title, default, etc.), resolve $ref/$defs
        references inline, and return a clean schema suitable for the API.
        """
        # Extract $defs for $ref resolution
        defs = output_schema.get("$defs", {})

        def _resolve_ref(ref_str: str) -> dict:
            """Resolve a $ref like '#/$defs/ReasoningStep' to the actual definition."""
            parts = ref_str.lstrip("#/").split("/")
            node = output_schema
            for part in parts:
                node = node.get(part, {})
            return node

        def _clean(node):
            if not isinstance(node, dict):
                return node
            # Resolve $ref first
            if "$ref" in node:
                resolved = _resolve_ref(node["$ref"])
                return _clean(resolved)
            cleaned = {}
            # Fields supported by Gemini response_schema
            for key in ("type", "properties", "required", "items", "enum", "description"):
                if key in node:
                    val = node[key]
                    if key == "properties" and isinstance(val, dict):
                        cleaned[key] = {k: _clean(v) for k, v in val.items()}
                    elif key == "items" and isinstance(val, dict):
                        cleaned[key] = _clean(val)
                    else:
                        cleaned[key] = val
            # Handle anyOf with null (Optional fields) — pick the non-null type
            if "anyOf" in node:
                non_null = [s for s in node["anyOf"] if s.get("type") != "null"]
                if non_null:
                    cleaned.update(_clean(non_null[0]))
                elif node["anyOf"]:
                    cleaned.update(_clean(node["anyOf"][0]))
            return cleaned

        try:
            return _clean(output_schema)
        except Exception as e:
            logger.warning(f"Failed to build Gemini response schema: {e}")
            return None

    @staticmethod
    def _extract_best_json(text: str, expected_fields: list) -> Optional[dict]:
        """Extract the JSON object that best matches expected schema fields.

        Uses json.JSONDecoder.raw_decode() to find all valid JSON objects
        in the text (handles nested braces in strings correctly), scores
        each by field overlap, and returns the best match.
        """
        decoder = json.JSONDecoder()
        candidates = []
        idx = 0
        while idx < len(text):
            # Find next '{' character
            brace_pos = text.find('{', idx)
            if brace_pos == -1:
                break
            try:
                obj, end_idx = decoder.raw_decode(text, brace_pos)
                if isinstance(obj, dict):
                    score = sum(1 for f in expected_fields if f in obj)
                    candidates.append((score, obj))
                idx = end_idx
            except json.JSONDecodeError:
                idx = brace_pos + 1

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_obj = candidates[0]
            logger.info(
                f"extract_best_json: {len(candidates)} candidates, "
                f"best has {best_score}/{len(expected_fields)} fields, "
                f"keys={list(best_obj.keys())[:5]}"
            )
            return best_obj if best_score > 0 else None
        logger.warning("extract_best_json: no JSON objects found in text")
        return None

    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using Gemini API with structured output when schema provided."""

        try:
            # Build generation config
            gen_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            # v0.4.3.1: Stronger prompt guidance for structured output.
            # Gemini's native structured output mode was tested but produces
            # single sub-objects. Instead we guide via prompt + extract best JSON.
            if output_schema:
                required = output_schema.get("required", [])
                properties = output_schema.get("properties", {})
                # Build compact schema hint showing field names and types
                field_hints = []
                for field_name in required:
                    prop = properties.get(field_name, {})
                    field_type = prop.get("type", "any")
                    if "items" in prop:
                        field_type = f"array of {prop['items'].get('type', 'objects')}"
                    elif "$ref" in prop or "allOf" in prop:
                        field_type = "object"
                    field_hints.append(f'  "{field_name}": <{field_type}>')
                schema_example = "{\n" + ",\n".join(field_hints) + "\n}"
                prompt += (
                    f"\n\nIMPORTANT: You MUST respond with EXACTLY ONE JSON object. "
                    f"The JSON object must have ALL of these top-level fields:\n"
                    f"{schema_example}\n\n"
                    f"Do NOT output multiple separate JSON objects. "
                    f"Do NOT output reasoning steps as individual JSON objects. "
                    f"Include reasoning_steps as an ARRAY inside the single JSON object.\n"
                    f"Respond ONLY with the JSON object, no other text.\n\nJSON:"
                )

            # Create model instance
            model = self.genai.GenerativeModel(self.model)

            # Generate response
            response = model.generate_content(
                prompt,
                generation_config=gen_config
            )

            content = response.text

            # Extract token usage
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            }

            # Parse JSON response
            expected_fields = []
            if output_schema and "required" in output_schema:
                expected_fields = output_schema["required"]
            elif output_schema and "properties" in output_schema:
                expected_fields = list(output_schema["properties"].keys())

            clean_content = strip_markdown_code_fences(content)
            logger.debug(f"Cleaned content (first 300): {clean_content[:300]}...")

            # v0.4.3.1 C-S-P Compression: Use robust best-match extraction.
            # raw_decode() finds all valid JSON objects and scores by field overlap
            # to pick the full model object, not a sub-object (reasoning step).
            inference_quality = "real"
            if expected_fields:
                parsed_content = self._extract_best_json(clean_content, expected_fields)
                if parsed_content is not None:
                    overlap = sum(1 for f in expected_fields if f in parsed_content)
                    if overlap < len(expected_fields) * 0.5:
                        inference_quality = "partial"
                        logger.warning(f"Low field overlap: {overlap}/{len(expected_fields)}")
                else:
                    logger.warning(
                        f"Best-match extraction found nothing; "
                        f"content_len={len(clean_content)}, "
                        f"first_200={clean_content[:200]!r}"
                    )
                    inference_quality = "fallback"
                    try:
                        parsed_content = json.loads(clean_content)
                    except json.JSONDecodeError:
                        parsed_content = {"raw_response": content[:500], "parse_error": "No valid JSON found"}
            else:
                # No schema — simple parse (backward compatible)
                try:
                    if clean_content.strip().startswith("{"):
                        parsed_content = json.loads(clean_content)
                    else:
                        import re
                        json_match = re.search(r'\{[\s\S]*\}', clean_content)
                        if json_match:
                            parsed_content = json.loads(json_match.group())
                        else:
                            parsed_content = {"raw_response": content}
                            inference_quality = "fallback"
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON: {e}")
                    parsed_content = {"raw_response": content, "parse_error": str(e)}
                    inference_quality = "fallback"

            # Return content, usage, and inference quality marker
            return {
                "content": parsed_content,
                "usage": usage,
                "_inference_quality": inference_quality
            }

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    def get_model_name(self) -> str:
        return f"gemini/{self.model}"


class GroqProvider(LLMProvider):
    """
    Groq provider implementation.
    
    Supports Llama 3.1, Mixtral, and other models.
    FREE tier available with generous rate limits!
    """
    
    def __init__(
        self,
        model: str = "llama-3.1-70b-versatile",
        api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("Groq API key not provided. Set GROQ_API_KEY environment variable.")
        
        try:
            from groq import AsyncGroq
            self.client = AsyncGroq(api_key=self.api_key)
        except ImportError:
            raise ImportError("groq package not installed. Run: pip install groq")
    
    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using Groq API."""
        
        messages = [{"role": "user", "content": prompt}]
        
        # Add JSON instruction if schema provided
        if output_schema:
            messages[0]["content"] += f"\n\nRespond with valid JSON only, matching this schema:\n{json.dumps(output_schema, indent=2)}\n\nJSON Response:"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
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
                if content.strip().startswith("{"):
                    parsed_content = json.loads(content)
                else:
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        parsed_content = json.loads(json_match.group())
                    else:
                        parsed_content = {"raw_response": content}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                parsed_content = {"raw_response": content, "parse_error": str(e)}
            
            return {
                "content": parsed_content,
                "usage": usage
            }
                
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
    
    def get_model_name(self) -> str:
        return f"groq/{self.model}"


class MistralProvider(LLMProvider):
    """
    Mistral AI provider implementation.

    Supports Mistral Small, Large, and other models.
    """

    def __init__(
        self,
        model: str = "mistral-small-latest",
        api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")

        if not self.api_key:
            raise ValueError("Mistral API key not provided. Set MISTRAL_API_KEY environment variable.")

        try:
            from mistralai import Mistral
            self.client = Mistral(api_key=self.api_key)
        except ImportError:
            raise ImportError("mistralai package not installed. Run: pip install mistralai")

    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using Mistral API."""

        messages = [{"role": "user", "content": prompt}]

        # Add JSON instruction if schema provided
        if output_schema:
            messages[0]["content"] += f"\n\nRespond with valid JSON only, matching this schema:\n{json.dumps(output_schema, indent=2)}\n\nJSON Response:"

        try:
            response = await self.client.chat.complete_async(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
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
                if content.strip().startswith("{"):
                    parsed_content = json.loads(content)
                else:
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        parsed_content = json.loads(json_match.group())
                    else:
                        parsed_content = {"raw_response": content}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                parsed_content = {"raw_response": content, "parse_error": str(e)}

            return {
                "content": parsed_content,
                "usage": usage
            }

        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            raise

    def get_model_name(self) -> str:
        return f"mistral/{self.model}"


class OllamaProvider(LLMProvider):
    """
    Ollama provider implementation for local LLM inference.

    Supports any model installed locally via Ollama.
    FREE - runs entirely on your local machine.

    Requires Ollama to be running: https://ollama.ai
    """

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434"
    ):
        self.model = model
        self.base_url = base_url

    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using Ollama local API."""
        import httpx

        # Add JSON instruction if schema provided
        if output_schema:
            prompt += f"\n\nRespond with valid JSON only, matching this schema:\n{json.dumps(output_schema, indent=2)}\n\nJSON Response:"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()

            content = data.get("response", "")

            # Extract token usage (Ollama provides eval_count and prompt_eval_count)
            usage = {
                "input_tokens": data.get("prompt_eval_count", 0),
                "output_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
            }

            # Parse JSON response
            try:
                if content.strip().startswith("{"):
                    parsed_content = json.loads(content)
                else:
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', content)
                    if json_match:
                        parsed_content = json.loads(json_match.group())
                    else:
                        parsed_content = {"raw_response": content}
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                parsed_content = {"raw_response": content, "parse_error": str(e)}

            return {
                "content": parsed_content,
                "usage": usage
            }

        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

    def get_model_name(self) -> str:
        return f"ollama/{self.model}"


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


# ============================================================================
# PROVIDER REGISTRY (BYOK v0.3.0)
# ============================================================================

_PROVIDERS: Dict[str, Type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "mistral": MistralProvider,
    "ollama": OllamaProvider,
    "mock": MockProvider
}


def get_provider(
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Get an LLM provider instance.

    BYOK v0.3.0: Supports multiple environment variable formats for compatibility.

    Args:
        provider_name: Provider name (gemini, openai, anthropic, groq, mistral, ollama, mock)
                      Defaults to LLM_PROVIDER env var or "mock"
        model: Model name to use
               Defaults to LLM_MODEL env var or provider default
        api_key: API key (optional, falls back to provider-specific env var)
        **kwargs: Additional arguments passed to provider constructor

    Returns:
        Configured LLMProvider instance

    Environment Variables:
        LLM_PROVIDER: Primary provider to use (gemini, openai, anthropic, groq, mistral, ollama, mock)
        LLM_MODEL: Override default model for the provider
        {PROVIDER}_API_KEY: API key for each provider (e.g., GEMINI_API_KEY)
    """
    # Get provider name from env if not specified (support both new and legacy env vars)
    if provider_name is None:
        provider_name = os.getenv("LLM_PROVIDER") or os.getenv("VERIFIMIND_LLM_PROVIDER", "mock")

    provider_name = provider_name.lower()

    if provider_name not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available providers: {list(_PROVIDERS.keys())}"
        )

    # Get API key from env if not specified
    if api_key is None:
        config = PROVIDER_CONFIGS.get(provider_name, {})
        api_key_env = config.get("api_key_env")
        if api_key_env:
            api_key = os.getenv(api_key_env)

    # Get model from env if not specified (support both new and legacy env vars)
    if model is None:
        model = os.getenv("LLM_MODEL") or os.getenv("VERIFIMIND_LLM_MODEL")

    # Build kwargs
    if model:
        kwargs["model"] = model
    if api_key and provider_name not in ["mock", "ollama"]:
        kwargs["api_key"] = api_key

    return _PROVIDERS[provider_name](**kwargs)


async def get_provider_with_fallback(
    provider_name: Optional[str] = None,
    fallback_provider: Optional[str] = None
) -> LLMProvider:
    """
    Get LLM provider with automatic fallback support.

    BYOK v0.3.0: If the primary provider fails to initialize or validate,
    automatically falls back to the configured fallback provider.

    Args:
        provider_name: Primary provider (defaults to LLM_PROVIDER env var)
        fallback_provider: Fallback provider (defaults to LLM_FALLBACK_PROVIDER env var or "mock")

    Returns:
        Configured LLMProvider instance (primary or fallback)

    Environment Variables:
        LLM_PROVIDER: Primary provider to use
        LLM_FALLBACK_PROVIDER: Fallback provider if primary fails (default: mock)
    """
    # Get provider names from env if not specified
    if provider_name is None:
        provider_name = os.getenv("LLM_PROVIDER") or os.getenv("VERIFIMIND_LLM_PROVIDER", "mock")
    if fallback_provider is None:
        fallback_provider = os.getenv("LLM_FALLBACK_PROVIDER", "mock")

    # Try primary provider
    try:
        provider = get_provider(provider_name)
        logger.info(f"Using primary provider: {provider_name}")
        return provider
    except Exception as e:
        logger.warning(f"Primary provider {provider_name} failed: {e}")

    # Try fallback provider
    if fallback_provider != provider_name:
        try:
            provider = get_provider(fallback_provider)
            logger.info(f"Using fallback provider: {fallback_provider}")
            return provider
        except Exception as e:
            logger.warning(f"Fallback provider {fallback_provider} failed: {e}")

    # Last resort: mock provider
    logger.info("Using mock provider as last resort")
    return get_provider("mock")


def register_provider(name: str, provider_class: Type[LLMProvider]) -> None:
    """
    Register a custom LLM provider.

    Args:
        name: Provider name for lookup
        provider_class: Provider class implementing LLMProvider
    """
    _PROVIDERS[name.lower()] = provider_class


def validate_provider_config(provider_name: str) -> Dict[str, Any]:
    """
    Validate that a provider is properly configured.

    Args:
        provider_name: Provider to validate

    Returns:
        Dict with validation status and details
    """
    provider_name = provider_name.lower()

    if provider_name not in _PROVIDERS:
        return {
            "valid": False,
            "provider": provider_name,
            "error": f"Unknown provider. Available: {list(_PROVIDERS.keys())}"
        }

    config = PROVIDER_CONFIGS.get(provider_name, {})
    api_key_env = config.get("api_key_env")

    # Check if API key is configured (if required)
    if api_key_env:
        api_key = os.getenv(api_key_env)
        if not api_key:
            return {
                "valid": False,
                "provider": provider_name,
                "error": f"API key not set. Set {api_key_env} environment variable.",
                "free_tier": config.get("free_tier", False)
            }

    return {
        "valid": True,
        "provider": provider_name,
        "name": config.get("name", provider_name),
        "default_model": config.get("default_model"),
        "free_tier": config.get("free_tier", False)
    }
