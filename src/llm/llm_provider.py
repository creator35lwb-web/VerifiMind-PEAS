"""
LLM Provider Abstraction Layer
Supports multiple LLM providers: OpenAI, Anthropic, Local models

Enhanced with comprehensive error handling and logging.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================

class LLMProviderError(Exception):
    """Base exception for LLM provider errors"""
    def __init__(self, message: str, provider: str, original_error: Optional[Exception] = None):
        self.message = message
        self.provider = provider
        self.original_error = original_error
        super().__init__(self.message)


class LLMAPIError(LLMProviderError):
    """API-related errors (authentication, connection, etc.)"""
    pass


class LLMRateLimitError(LLMProviderError):
    """Rate limit exceeded errors"""
    pass


class LLMAuthenticationError(LLMProviderError):
    """Authentication/API key errors"""
    pass


class LLMTimeoutError(LLMProviderError):
    """Request timeout errors"""
    pass


class LLMInvalidRequestError(LLMProviderError):
    """Invalid request parameters errors"""
    pass


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class LLMMessage:
    """Standardized message format across providers"""
    role: str  # system, user, assistant
    content: str


@dataclass
class LLMResponse:
    """Standardized response format"""
    content: str
    model: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    finish_reason: str
    raw_response: Any


# ============================================================================
# Base Provider
# ============================================================================

class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.default_temperature = 0.7
        self.default_max_tokens = 2000
        self.provider_name = self.__class__.__name__

    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion from messages"""
        pass

    @abstractmethod
    async def stream_generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Stream completion from messages"""
        pass


# ============================================================================
# OpenAI Provider
# ============================================================================

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider with comprehensive error handling"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"), model)
        self.api_base = "https://api.openai.com/v1"

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using OpenAI API with comprehensive error handling"""

        # Validate API key
        if not self.api_key:
            error_msg = "OpenAI API key not provided. Set OPENAI_API_KEY environment variable."
            logger.error(f"ERROR: {error_msg}")
            raise LLMAuthenticationError(error_msg, provider="OpenAI")

        try:
            # Import OpenAI SDK
            try:
                from openai import AsyncOpenAI, APIError, RateLimitError, AuthenticationError, APIConnectionError, APITimeoutError, BadRequestError
            except ImportError as e:
                logger.error(f"ERROR: OpenAI SDK not installed: {e}")
                logger.info("Falling back to mock response for demo purposes")
                return await self._mock_generate(messages)

            # Create client
            client = AsyncOpenAI(api_key=self.api_key)

            # Format messages
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            logger.info(f"Sending request to OpenAI API (model: {self.model})")

            # Make API call
            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    temperature=temperature or self.default_temperature,
                    max_tokens=max_tokens or self.default_max_tokens,
                    **kwargs
                )
            except AuthenticationError as e:
                error_msg = f"OpenAI authentication failed. Check your API key: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMAuthenticationError(error_msg, provider="OpenAI", original_error=e)

            except RateLimitError as e:
                error_msg = f"OpenAI rate limit exceeded: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMRateLimitError(error_msg, provider="OpenAI", original_error=e)

            except APITimeoutError as e:
                error_msg = f"OpenAI API request timed out: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMTimeoutError(error_msg, provider="OpenAI", original_error=e)

            except APIConnectionError as e:
                error_msg = f"Failed to connect to OpenAI API: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMAPIError(error_msg, provider="OpenAI", original_error=e)

            except BadRequestError as e:
                error_msg = f"Invalid request to OpenAI API: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMInvalidRequestError(error_msg, provider="OpenAI", original_error=e)

            except APIError as e:
                error_msg = f"OpenAI API error: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMAPIError(error_msg, provider="OpenAI", original_error=e)

            # Parse response
            try:
                llm_response = LLMResponse(
                    content=response.choices[0].message.content,
                    model=response.model,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    finish_reason=response.choices[0].finish_reason,
                    raw_response=response
                )
                logger.info(f"OpenAI API call successful (tokens: {llm_response.usage['total_tokens']})")
                return llm_response

            except (AttributeError, IndexError, KeyError) as e:
                error_msg = f"Failed to parse OpenAI response: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMAPIError(error_msg, provider="OpenAI", original_error=e)

        except LLMProviderError:
            # Re-raise our custom errors
            raise

        except Exception as e:
            # Catch-all for unexpected errors
            error_msg = f"Unexpected error in OpenAI provider: {str(e)}"
            logger.error(f"ERROR: {error_msg}")
            logger.exception("Full traceback:")
            raise LLMProviderError(error_msg, provider="OpenAI", original_error=e)

    async def stream_generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Stream completion using OpenAI API with error handling"""

        if not self.api_key:
            error_msg = "OpenAI API key not provided"
            logger.error(f"ERROR: {error_msg}")
            raise LLMAuthenticationError(error_msg, provider="OpenAI")

        try:
            from openai import AsyncOpenAI, APIError, RateLimitError, AuthenticationError, APIConnectionError, APITimeoutError
        except ImportError as e:
            logger.error(f"ERROR: OpenAI SDK not installed: {e}")
            logger.info("Falling back to mock streaming response")
            yield "Mock streaming response (OpenAI SDK not available)"
            return

        try:
            client = AsyncOpenAI(api_key=self.api_key)

            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            logger.info(f"Starting OpenAI streaming request (model: {self.model})")

            try:
                stream = await client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    temperature=temperature or self.default_temperature,
                    max_tokens=max_tokens or self.default_max_tokens,
                    stream=True,
                    **kwargs
                )

                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

                logger.info("OpenAI streaming completed successfully")

            except (AuthenticationError, RateLimitError, APITimeoutError, APIConnectionError, APIError) as e:
                error_msg = f"OpenAI streaming error: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                yield f"\n[ERROR: {error_msg}]"

        except Exception as e:
            error_msg = f"Unexpected error in OpenAI streaming: {str(e)}"
            logger.error(f"ERROR: {error_msg}")
            logger.exception("Full traceback:")
            yield f"\n[ERROR: {error_msg}]"

    async def _mock_generate(self, messages: List[LLMMessage]) -> LLMResponse:
        """Mock response for demo/testing"""
        logger.warning("Using mock response (OpenAI API not available)")
        await asyncio.sleep(0.1)  # Simulate API latency

        # Generate contextual mock response based on last message
        last_message = messages[-1].content.lower()

        if "market" in last_message or "business" in last_message:
            mock_content = """
Based on market analysis:
- Total Addressable Market (TAM): $50B
- Target market shows 35% annual growth
- Competitive landscape: 5 major players, room for innovation
- User pain points: Validated through research
- Monetization potential: Strong, multiple revenue streams possible
"""
        elif "compliance" in last_message or "regulation" in last_message:
            mock_content = """
Compliance Assessment:
- GDPR: Requires data protection measures
- COPPA: Parental consent needed for children under 13
- Accessibility: WCAG 2.1 AA compliance recommended
- Data retention: Implement clear policies
- Privacy: Transparent data handling required
"""
        elif "security" in last_message or "threat" in last_message:
            mock_content = """
Security Analysis:
- Authentication: JWT with secure token handling needed
- Data validation: Input sanitization required
- SQL Injection: Use parameterized queries
- XSS Protection: Output encoding essential
- Rate Limiting: Prevent abuse and DoS attacks
"""
        else:
            mock_content = "Detailed analysis shows the concept is technically viable and presents good market opportunity."

        return LLMResponse(
            content=mock_content,
            model=self.model,
            usage={"prompt_tokens": 100, "completion_tokens": 150, "total_tokens": 250},
            finish_reason="stop",
            raw_response={}
        )


# ============================================================================
# Anthropic Provider
# ============================================================================

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider with comprehensive error handling"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        super().__init__(api_key or os.getenv("ANTHROPIC_API_KEY"), model)
        self.api_base = "https://api.anthropic.com/v1"

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using Anthropic API with comprehensive error handling"""

        # Validate API key
        if not self.api_key:
            error_msg = "Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable."
            logger.error(f"ERROR: {error_msg}")
            raise LLMAuthenticationError(error_msg, provider="Anthropic")

        try:
            # Import Anthropic SDK
            try:
                import anthropic
                from anthropic import APIError, RateLimitError, AuthenticationError, APIConnectionError, APITimeoutError, BadRequestError
            except ImportError as e:
                logger.error(f"ERROR: Anthropic SDK not installed: {e}")
                logger.info("Falling back to mock response for demo purposes")
                return await self._mock_generate(messages)

            # Create client
            client = anthropic.AsyncAnthropic(api_key=self.api_key)

            # Separate system message from conversation
            system_message = None
            conversation_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    conversation_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            logger.info(f"Sending request to Anthropic API (model: {self.model})")

            # Make API call
            try:
                response = await client.messages.create(
                    model=self.model,
                    system=system_message,
                    messages=conversation_messages,
                    temperature=temperature or self.default_temperature,
                    max_tokens=max_tokens or self.default_max_tokens,
                    **kwargs
                )
            except AuthenticationError as e:
                error_msg = f"Anthropic authentication failed. Check your API key: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMAuthenticationError(error_msg, provider="Anthropic", original_error=e)

            except RateLimitError as e:
                error_msg = f"Anthropic rate limit exceeded: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMRateLimitError(error_msg, provider="Anthropic", original_error=e)

            except APITimeoutError as e:
                error_msg = f"Anthropic API request timed out: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMTimeoutError(error_msg, provider="Anthropic", original_error=e)

            except APIConnectionError as e:
                error_msg = f"Failed to connect to Anthropic API: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMAPIError(error_msg, provider="Anthropic", original_error=e)

            except BadRequestError as e:
                error_msg = f"Invalid request to Anthropic API: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMInvalidRequestError(error_msg, provider="Anthropic", original_error=e)

            except APIError as e:
                error_msg = f"Anthropic API error: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMAPIError(error_msg, provider="Anthropic", original_error=e)

            # Parse response
            try:
                llm_response = LLMResponse(
                    content=response.content[0].text,
                    model=response.model,
                    usage={
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                    },
                    finish_reason=response.stop_reason,
                    raw_response=response
                )
                logger.info(f"Anthropic API call successful (tokens: {llm_response.usage['total_tokens']})")
                return llm_response

            except (AttributeError, IndexError, KeyError) as e:
                error_msg = f"Failed to parse Anthropic response: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMAPIError(error_msg, provider="Anthropic", original_error=e)

        except LLMProviderError:
            # Re-raise our custom errors
            raise

        except Exception as e:
            # Catch-all for unexpected errors
            error_msg = f"Unexpected error in Anthropic provider: {str(e)}"
            logger.error(f"ERROR: {error_msg}")
            logger.exception("Full traceback:")
            raise LLMProviderError(error_msg, provider="Anthropic", original_error=e)

    async def stream_generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Stream completion using Anthropic API with error handling"""

        if not self.api_key:
            error_msg = "Anthropic API key not provided"
            logger.error(f"ERROR: {error_msg}")
            raise LLMAuthenticationError(error_msg, provider="Anthropic")

        try:
            import anthropic
            from anthropic import APIError, RateLimitError, AuthenticationError, APIConnectionError, APITimeoutError
        except ImportError as e:
            logger.error(f"ERROR: Anthropic SDK not installed: {e}")
            logger.info("Falling back to mock streaming response")
            yield "Mock streaming response (Anthropic SDK not available)"
            return

        try:
            client = anthropic.AsyncAnthropic(api_key=self.api_key)

            system_message = None
            conversation_messages = []

            for msg in messages:
                if msg.role == "system":
                    system_message = msg.content
                else:
                    conversation_messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

            logger.info(f"Starting Anthropic streaming request (model: {self.model})")

            try:
                async with client.messages.stream(
                    model=self.model,
                    system=system_message,
                    messages=conversation_messages,
                    temperature=temperature or self.default_temperature,
                    max_tokens=max_tokens or self.default_max_tokens,
                    **kwargs
                ) as stream:
                    async for text in stream.text_stream:
                        yield text

                logger.info("Anthropic streaming completed successfully")

            except (AuthenticationError, RateLimitError, APITimeoutError, APIConnectionError, APIError) as e:
                error_msg = f"Anthropic streaming error: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                yield f"\n[ERROR: {error_msg}]"

        except Exception as e:
            error_msg = f"Unexpected error in Anthropic streaming: {str(e)}"
            logger.error(f"ERROR: {error_msg}")
            logger.exception("Full traceback:")
            yield f"\n[ERROR: {error_msg}]"

    async def _mock_generate(self, messages: List[LLMMessage]) -> LLMResponse:
        """Mock response - same as OpenAI mock"""
        logger.warning("Using mock response (Anthropic API not available)")
        await asyncio.sleep(0.1)

        last_message = messages[-1].content.lower()

        if "market" in last_message or "business" in last_message:
            mock_content = """
Market Analysis Results:
- Strong product-market fit indicators
- Growing user demand in target segment
- Competitive advantages identified
- Clear monetization pathways
- Scalability considerations addressed
"""
        elif "compliance" in last_message or "regulation" in last_message:
            mock_content = """
Regulatory Compliance Review:
- Data protection: GDPR and regional laws
- User privacy: Comprehensive policies needed
- Accessibility: Standards compliance required
- Industry-specific: Sector regulations identified
- Risk mitigation: Strategies recommended
"""
        elif "security" in last_message or "threat" in last_message:
            mock_content = """
Security Threat Assessment:
- Injection vulnerabilities: Mitigations required
- Authentication: Strong methods recommended
- Authorization: Proper access controls needed
- Data encryption: At rest and in transit
- Security monitoring: Logging and alerts
"""
        else:
            mock_content = "Comprehensive analysis indicates the concept is well-structured with appropriate safeguards."

        return LLMResponse(
            content=mock_content,
            model=self.model,
            usage={"prompt_tokens": 100, "completion_tokens": 150, "total_tokens": 250},
            finish_reason="end_turn",
            raw_response={}
        )


# ============================================================================
# Local Model Provider
# ============================================================================

class LocalModelProvider(BaseLLMProvider):
    """Local model provider (Ollama, LM Studio, etc.) with error handling"""

    def __init__(self, api_key: Optional[str] = None, model: str = "llama2", api_base: str = "http://localhost:11434"):
        super().__init__(api_key, model)
        self.api_base = api_base

    async def generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate completion using local model with error handling"""

        try:
            import aiohttp
        except ImportError as e:
            error_msg = f"aiohttp not installed: {e}"
            logger.error(f"ERROR: {error_msg}")
            logger.info("Falling back to mock response")
            return await self._mock_generate(messages)

        try:
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            logger.info(f"Sending request to local model at {self.api_base}")

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_base}/api/chat",
                        json={
                            "model": self.model,
                            "messages": formatted_messages,
                            "temperature": temperature or self.default_temperature,
                            "stream": False
                        },
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status != 200:
                            error_msg = f"Local model returned status {response.status}"
                            logger.error(f"ERROR: {error_msg}")
                            raise LLMAPIError(error_msg, provider="LocalModel")

                        result = await response.json()

                        llm_response = LLMResponse(
                            content=result.get("message", {}).get("content", ""),
                            model=self.model,
                            usage={
                                "prompt_tokens": result.get("prompt_eval_count", 0),
                                "completion_tokens": result.get("eval_count", 0),
                                "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                            },
                            finish_reason="stop",
                            raw_response=result
                        )
                        logger.info(f"Local model call successful")
                        return llm_response

            except aiohttp.ClientConnectorError as e:
                error_msg = f"Cannot connect to local model at {self.api_base}: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMAPIError(error_msg, provider="LocalModel", original_error=e)

            except aiohttp.ClientTimeout as e:
                error_msg = f"Local model request timed out: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMTimeoutError(error_msg, provider="LocalModel", original_error=e)

            except aiohttp.ClientError as e:
                error_msg = f"HTTP client error: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                raise LLMAPIError(error_msg, provider="LocalModel", original_error=e)

        except LLMProviderError:
            raise

        except Exception as e:
            error_msg = f"Unexpected error in local model provider: {str(e)}"
            logger.error(f"ERROR: {error_msg}")
            logger.exception("Full traceback:")
            raise LLMProviderError(error_msg, provider="LocalModel", original_error=e)

    async def stream_generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Stream completion using local model with error handling"""

        try:
            import aiohttp
        except ImportError as e:
            logger.error(f"ERROR: aiohttp not installed: {e}")
            yield "Mock streaming response (aiohttp not available)"
            return

        try:
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            logger.info(f"Starting local model streaming at {self.api_base}")

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_base}/api/chat",
                        json={
                            "model": self.model,
                            "messages": formatted_messages,
                            "temperature": temperature or self.default_temperature,
                            "stream": True
                        },
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        if response.status != 200:
                            error_msg = f"Local model returned status {response.status}"
                            logger.error(f"ERROR: {error_msg}")
                            yield f"\n[ERROR: {error_msg}]"
                            return

                        async for line in response.content:
                            if line:
                                try:
                                    data = json.loads(line)
                                    if "message" in data and "content" in data["message"]:
                                        yield data["message"]["content"]
                                except json.JSONDecodeError:
                                    continue

                        logger.info("Local model streaming completed")

            except (aiohttp.ClientConnectorError, aiohttp.ClientTimeout, aiohttp.ClientError) as e:
                error_msg = f"Local model streaming error: {str(e)}"
                logger.error(f"ERROR: {error_msg}")
                yield f"\n[ERROR: {error_msg}]"

        except Exception as e:
            error_msg = f"Unexpected error in local model streaming: {str(e)}"
            logger.error(f"ERROR: {error_msg}")
            logger.exception("Full traceback:")
            yield f"\n[ERROR: {error_msg}]"

    async def _mock_generate(self, messages: List[LLMMessage]) -> LLMResponse:
        """Mock response"""
        logger.warning("Using mock response (local model not available)")
        await asyncio.sleep(0.1)
        return LLMResponse(
            content="Local model analysis complete. The concept shows promise.",
            model=self.model,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            finish_reason="stop",
            raw_response={}
        )


# ============================================================================
# Factory
# ============================================================================

class LLMProviderFactory:
    """Factory for creating LLM providers"""

    @staticmethod
    def create_provider(
        provider_type: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """
        Create LLM provider instance

        Args:
            provider_type: "openai", "anthropic", or "local"
            api_key: API key (optional, will use env var if not provided)
            model: Model name (optional, will use default)
            **kwargs: Additional provider-specific arguments

        Raises:
            ValueError: If provider_type is unknown
        """
        provider_type = provider_type.lower()

        if provider_type == "openai":
            return OpenAIProvider(api_key=api_key, model=model or "gpt-4")
        elif provider_type == "anthropic":
            return AnthropicProvider(api_key=api_key, model=model or "claude-3-sonnet-20240229")
        elif provider_type == "local":
            return LocalModelProvider(
                api_key=api_key,
                model=model or "llama2",
                api_base=kwargs.get("api_base", "http://localhost:11434")
            )
        else:
            raise ValueError(f"Unknown provider type: {provider_type}. Supported types: openai, anthropic, local")


# ============================================================================
# Convenience Functions
# ============================================================================

async def generate_completion(
    prompt: str,
    system_prompt: Optional[str] = None,
    provider_type: str = "openai",
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    **kwargs
) -> str:
    """
    Quick helper function to generate completion

    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        provider_type: "openai", "anthropic", or "local"
        model: Model name
        temperature: Temperature (0.0-1.0)
        max_tokens: Maximum tokens to generate

    Returns:
        Generated text

    Raises:
        LLMProviderError: If generation fails
    """
    provider = LLMProviderFactory.create_provider(
        provider_type=provider_type,
        model=model,
        **kwargs
    )

    messages = []
    if system_prompt:
        messages.append(LLMMessage(role="system", content=system_prompt))
    messages.append(LLMMessage(role="user", content=prompt))

    response = await provider.generate(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return response.content


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    async def test_providers():
        """Test different providers with error handling"""

        # Test OpenAI
        print("Testing OpenAI provider...")
        try:
            openai_provider = LLMProviderFactory.create_provider("openai", model="gpt-4")
            messages = [
                LLMMessage(role="system", content="You are a business analyst."),
                LLMMessage(role="user", content="Analyze the market potential for a meditation app.")
            ]
            response = await openai_provider.generate(messages)
            print(f"OpenAI response: {response.content[:200]}...")
        except LLMProviderError as e:
            print(f"OpenAI error: {e.message}")

        # Test Anthropic
        print("\nTesting Anthropic provider...")
        try:
            anthropic_provider = LLMProviderFactory.create_provider("anthropic", model="claude-3-5-sonnet-20241022")
            response = await anthropic_provider.generate(messages)
            print(f"Anthropic response: {response.content[:200]}...")
        except LLMProviderError as e:
            print(f"Anthropic error: {e.message}")

        # Test convenience function
        print("\nTesting convenience function...")
        try:
            result = await generate_completion(
                prompt="What are the key security considerations for a web app?",
                system_prompt="You are a security expert.",
                provider_type="openai",
                temperature=0.5
            )
            print(f"Result: {result[:200]}...")
        except LLMProviderError as e:
            print(f"Error: {e.message}")

    asyncio.run(test_providers())
