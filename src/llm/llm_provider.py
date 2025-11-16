"""
LLM Provider Abstraction Layer
Supports multiple LLM providers: OpenAI, Anthropic, Local models
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio


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


class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.default_temperature = 0.7
        self.default_max_tokens = 2000

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


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""

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
        """Generate completion using OpenAI API"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)

            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            response = await client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                **kwargs
            )

            return LLMResponse(
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
        except ImportError:
            # Fallback to mock for demo purposes
            return await self._mock_generate(messages)
        except Exception as e:
            print(f"[WARNING] OpenAI API call failed: {e}. Using mock response.")
            return await self._mock_generate(messages)

    async def stream_generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Stream completion using OpenAI API"""
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)

            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

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
        except Exception as e:
            print(f"[WARNING] OpenAI streaming failed: {e}")
            yield "Mock streaming response"

    async def _mock_generate(self, messages: List[LLMMessage]) -> LLMResponse:
        """Mock response for demo/testing"""
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


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider"""

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
        """Generate completion using Anthropic API"""
        try:
            import anthropic
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

            response = await client.messages.create(
                model=self.model,
                system=system_message,
                messages=conversation_messages,
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                **kwargs
            )

            return LLMResponse(
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
        except ImportError:
            return await self._mock_generate(messages)
        except Exception as e:
            print(f"[WARNING] Anthropic API call failed: {e}. Using mock response.")
            return await self._mock_generate(messages)

    async def stream_generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Stream completion using Anthropic API"""
        try:
            import anthropic
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
        except Exception as e:
            print(f"[WARNING] Anthropic streaming failed: {e}")
            yield "Mock streaming response"

    async def _mock_generate(self, messages: List[LLMMessage]) -> LLMResponse:
        """Mock response - same as OpenAI mock"""
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


class LocalModelProvider(BaseLLMProvider):
    """Local model provider (Ollama, LM Studio, etc.)"""

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
        """Generate completion using local model"""
        try:
            import aiohttp

            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/api/chat",
                    json={
                        "model": self.model,
                        "messages": formatted_messages,
                        "temperature": temperature or self.default_temperature,
                        "stream": False
                    }
                ) as response:
                    result = await response.json()

                    return LLMResponse(
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
        except Exception as e:
            print(f"[WARNING] Local model call failed: {e}. Using mock response.")
            return await self._mock_generate(messages)

    async def stream_generate(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Stream completion using local model"""
        try:
            import aiohttp

            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/api/chat",
                    json={
                        "model": self.model,
                        "messages": formatted_messages,
                        "temperature": temperature or self.default_temperature,
                        "stream": True
                    }
                ) as response:
                    async for line in response.content:
                        if line:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
        except Exception as e:
            print(f"[WARNING] Local model streaming failed: {e}")
            yield "Mock streaming response"

    async def _mock_generate(self, messages: List[LLMMessage]) -> LLMResponse:
        """Mock response"""
        await asyncio.sleep(0.1)
        return LLMResponse(
            content="Local model analysis complete. The concept shows promise.",
            model=self.model,
            usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            finish_reason="stop",
            raw_response={}
        )


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
            raise ValueError(f"Unknown provider type: {provider_type}")


# Convenience function for quick usage
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


# Example usage
if __name__ == "__main__":
    async def test_providers():
        """Test different providers"""

        # Test OpenAI
        print("Testing OpenAI provider...")
        openai_provider = LLMProviderFactory.create_provider("openai", model="gpt-4")
        messages = [
            LLMMessage(role="system", content="You are a business analyst."),
            LLMMessage(role="user", content="Analyze the market potential for a meditation app.")
        ]
        response = await openai_provider.generate(messages)
        print(f"OpenAI response: {response.content[:200]}...")

        # Test Anthropic
        print("\nTesting Anthropic provider...")
        anthropic_provider = LLMProviderFactory.create_provider("anthropic", model="claude-3-5-sonnet-20241022")
        response = await anthropic_provider.generate(messages)
        print(f"Anthropic response: {response.content[:200]}...")

        # Test convenience function
        print("\nTesting convenience function...")
        result = await generate_completion(
            prompt="What are the key security considerations for a web app?",
            system_prompt="You are a security expert.",
            provider_type="openai",
            temperature=0.5
        )
        print(f"Result: {result[:200]}...")

    asyncio.run(test_providers())
