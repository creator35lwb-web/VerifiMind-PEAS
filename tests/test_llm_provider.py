"""
Unit tests for LLM Provider with comprehensive mocking.

Tests cover:
- Successful API responses
- Error handling for various exceptions
- Authentication errors
- Rate limiting
- Timeouts
- Invalid requests
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from src.llm.llm_provider import (
    OpenAIProvider,
    AnthropicProvider,
    LLMMessage,
    LLMResponse,
    LLMProviderError,
    LLMAPIError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMInvalidRequestError,
)


# ============================================================================
# OpenAI Provider Tests
# ============================================================================

class TestOpenAIProvider:
    """Test suite for OpenAI provider"""

    @pytest.mark.asyncio
    async def test_openai_success(self):
        """Test successful OpenAI API call with mocked response"""

        # Create mock response object that matches OpenAI's structure
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test response from OpenAI."
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 8
        mock_response.usage.total_tokens = 18

        # Mock the AsyncOpenAI client (patch where it's imported, not where it's defined)
        with patch('openai.AsyncOpenAI') as mock_client_class:
            # Configure the mock
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            # Create provider and test
            provider = OpenAIProvider(api_key="test-key", model="gpt-4")
            messages = [
                LLMMessage(role="system", content="You are a helpful assistant."),
                LLMMessage(role="user", content="Hello!")
            ]

            # Call the method
            result = await provider.generate(messages)

            # Assertions
            assert isinstance(result, LLMResponse)
            assert result.content == "This is a test response from OpenAI."
            assert result.model == "gpt-4"
            assert result.finish_reason == "stop"
            assert result.usage["prompt_tokens"] == 10
            assert result.usage["completion_tokens"] == 8
            assert result.usage["total_tokens"] == 18

            # Verify the API was called with correct parameters
            mock_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["model"] == "gpt-4"
            assert len(call_kwargs["messages"]) == 2

    @pytest.mark.asyncio
    async def test_openai_api_error(self):
        """Test OpenAI API error handling"""

        # Import the actual exception class
        from openai import APIError

        # Mock the AsyncOpenAI client to raise APIError
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Create a proper APIError with required arguments
            mock_request = Mock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=APIError(
                    message="API connection failed",
                    request=mock_request,
                    body=None
                )
            )

            # Create provider
            provider = OpenAIProvider(api_key="test-key", model="gpt-4")
            messages = [LLMMessage(role="user", content="Hello!")]

            # Should raise our custom exception
            with pytest.raises(LLMAPIError) as exc_info:
                await provider.generate(messages)

            # Verify the exception details
            assert "OpenAI API error" in str(exc_info.value.message)
            assert exc_info.value.provider == "OpenAI"
            assert isinstance(exc_info.value.original_error, APIError)

    @pytest.mark.asyncio
    async def test_openai_authentication_error(self):
        """Test OpenAI authentication error handling"""

        from openai import AuthenticationError

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Create AuthenticationError with just message and response
            mock_response = Mock()
            mock_response.status_code = 401
            mock_client.chat.completions.create = AsyncMock(
                side_effect=AuthenticationError(
                    message="Invalid API key",
                    response=mock_response,
                    body=None
                )
            )

            provider = OpenAIProvider(api_key="invalid-key", model="gpt-4")
            messages = [LLMMessage(role="user", content="Hello!")]

            with pytest.raises(LLMAuthenticationError) as exc_info:
                await provider.generate(messages)

            assert "authentication failed" in str(exc_info.value.message).lower()
            assert exc_info.value.provider == "OpenAI"

    @pytest.mark.asyncio
    async def test_openai_rate_limit_error(self):
        """Test OpenAI rate limit error handling"""

        from openai import RateLimitError

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Create RateLimitError with just message and response
            mock_response = Mock()
            mock_response.status_code = 429
            mock_client.chat.completions.create = AsyncMock(
                side_effect=RateLimitError(
                    message="Rate limit exceeded",
                    response=mock_response,
                    body=None
                )
            )

            provider = OpenAIProvider(api_key="test-key", model="gpt-4")
            messages = [LLMMessage(role="user", content="Hello!")]

            with pytest.raises(LLMRateLimitError) as exc_info:
                await provider.generate(messages)

            assert "rate limit exceeded" in str(exc_info.value.message).lower()
            assert exc_info.value.provider == "OpenAI"

    @pytest.mark.asyncio
    async def test_openai_timeout_error(self):
        """Test OpenAI timeout error handling"""

        from openai import APITimeoutError

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_request = Mock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=APITimeoutError(request=mock_request)
            )

            provider = OpenAIProvider(api_key="test-key", model="gpt-4")
            messages = [LLMMessage(role="user", content="Hello!")]

            with pytest.raises(LLMTimeoutError) as exc_info:
                await provider.generate(messages)

            assert "timed out" in str(exc_info.value.message).lower()
            assert exc_info.value.provider == "OpenAI"

    @pytest.mark.asyncio
    async def test_openai_connection_error(self):
        """Test OpenAI connection error handling"""

        from openai import APIConnectionError

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_request = Mock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=APIConnectionError(request=mock_request)
            )

            provider = OpenAIProvider(api_key="test-key", model="gpt-4")
            messages = [LLMMessage(role="user", content="Hello!")]

            with pytest.raises(LLMAPIError) as exc_info:
                await provider.generate(messages)

            assert "connect" in str(exc_info.value.message).lower()
            assert exc_info.value.provider == "OpenAI"

    @pytest.mark.asyncio
    async def test_openai_invalid_request_error(self):
        """Test OpenAI invalid request error handling"""

        from openai import BadRequestError

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Create BadRequestError with just message and response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_client.chat.completions.create = AsyncMock(
                side_effect=BadRequestError(
                    message="Invalid model parameter",
                    response=mock_response,
                    body=None
                )
            )

            provider = OpenAIProvider(api_key="test-key", model="invalid-model")
            messages = [LLMMessage(role="user", content="Hello!")]

            with pytest.raises(LLMInvalidRequestError) as exc_info:
                await provider.generate(messages)

            assert "invalid request" in str(exc_info.value.message).lower()
            assert exc_info.value.provider == "OpenAI"

    @pytest.mark.asyncio
    async def test_openai_no_api_key(self):
        """Test OpenAI provider without API key"""

        provider = OpenAIProvider(api_key=None, model="gpt-4")
        messages = [LLMMessage(role="user", content="Hello!")]

        with pytest.raises(LLMAuthenticationError) as exc_info:
            await provider.generate(messages)

        assert "api key not provided" in str(exc_info.value.message).lower()
        assert exc_info.value.provider == "OpenAI"

    @pytest.mark.asyncio
    async def test_openai_response_parsing_error(self):
        """Test handling of malformed API response"""

        # Create a mock response with missing attributes
        mock_response = Mock()
        mock_response.choices = []  # Empty choices list will cause IndexError

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            provider = OpenAIProvider(api_key="test-key", model="gpt-4")
            messages = [LLMMessage(role="user", content="Hello!")]

            with pytest.raises(LLMAPIError) as exc_info:
                await provider.generate(messages)

            assert "failed to parse" in str(exc_info.value.message).lower()
            assert exc_info.value.provider == "OpenAI"


# ============================================================================
# Anthropic Provider Tests
# ============================================================================

class TestAnthropicProvider:
    """Test suite for Anthropic provider"""

    @pytest.mark.asyncio
    async def test_anthropic_success(self):
        """Test successful Anthropic API call with mocked response"""

        # Create mock response object that matches Anthropic's structure
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "This is a test response from Claude."
        mock_response.model = "claude-3-sonnet-20240229"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 10

        with patch('anthropic.AsyncAnthropic') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            provider = AnthropicProvider(api_key="test-key", model="claude-3-sonnet-20240229")
            messages = [
                LLMMessage(role="system", content="You are a helpful assistant."),
                LLMMessage(role="user", content="Hello!")
            ]

            result = await provider.generate(messages)

            assert isinstance(result, LLMResponse)
            assert result.content == "This is a test response from Claude."
            assert result.model == "claude-3-sonnet-20240229"
            assert result.finish_reason == "end_turn"
            assert result.usage["prompt_tokens"] == 15
            assert result.usage["completion_tokens"] == 10
            assert result.usage["total_tokens"] == 25

            # Verify system message was extracted correctly
            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["system"] == "You are a helpful assistant."
            assert len(call_kwargs["messages"]) == 1  # Only user message

    @pytest.mark.asyncio
    async def test_anthropic_api_error(self):
        """Test Anthropic API error handling"""

        from anthropic import APIError

        with patch('anthropic.AsyncAnthropic') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_client.messages.create = AsyncMock(
                side_effect=APIError(
                    message="API connection failed",
                    request=Mock(),
                    body=None
                )
            )

            provider = AnthropicProvider(api_key="test-key")
            messages = [LLMMessage(role="user", content="Hello!")]

            with pytest.raises(LLMAPIError) as exc_info:
                await provider.generate(messages)

            assert "anthropic api error" in str(exc_info.value.message).lower()
            assert exc_info.value.provider == "Anthropic"

    @pytest.mark.asyncio
    async def test_anthropic_authentication_error(self):
        """Test Anthropic authentication error handling"""

        from anthropic import AuthenticationError

        with patch('anthropic.AsyncAnthropic') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Create AuthenticationError with just message and response
            mock_response = Mock()
            mock_response.status_code = 401
            mock_client.messages.create = AsyncMock(
                side_effect=AuthenticationError(
                    message="Invalid API key",
                    response=mock_response,
                    body=None
                )
            )

            provider = AnthropicProvider(api_key="invalid-key")
            messages = [LLMMessage(role="user", content="Hello!")]

            with pytest.raises(LLMAuthenticationError) as exc_info:
                await provider.generate(messages)

            assert "authentication failed" in str(exc_info.value.message).lower()
            assert exc_info.value.provider == "Anthropic"

    @pytest.mark.asyncio
    async def test_anthropic_no_api_key(self):
        """Test Anthropic provider without API key"""

        provider = AnthropicProvider(api_key=None)
        messages = [LLMMessage(role="user", content="Hello!")]

        with pytest.raises(LLMAuthenticationError) as exc_info:
            await provider.generate(messages)

        assert "api key not provided" in str(exc_info.value.message).lower()
        assert exc_info.value.provider == "Anthropic"


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================

class TestLLMProviderEdgeCases:
    """Test edge cases and special scenarios"""

    @pytest.mark.asyncio
    async def test_empty_messages_list(self):
        """Test behavior with empty messages list"""

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage = Mock(prompt_tokens=0, completion_tokens=1, total_tokens=1)

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            provider = OpenAIProvider(api_key="test-key")
            messages = []  # Empty list

            result = await provider.generate(messages)

            # Should still work, just with empty messages
            assert isinstance(result, LLMResponse)
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_multiple_system_messages(self):
        """Test handling of multiple system messages with Anthropic"""

        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.model = "claude-3-sonnet-20240229"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock(input_tokens=10, output_tokens=5)

        with patch('anthropic.AsyncAnthropic') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            provider = AnthropicProvider(api_key="test-key")
            messages = [
                LLMMessage(role="system", content="First system message"),
                LLMMessage(role="system", content="Second system message"),
                LLMMessage(role="user", content="Hello!")
            ]

            result = await provider.generate(messages)

            # Should use the last system message
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["system"] == "Second system message"

    @pytest.mark.asyncio
    async def test_custom_temperature_and_max_tokens(self):
        """Test that custom parameters are passed correctly"""

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            provider = OpenAIProvider(api_key="test-key")
            messages = [LLMMessage(role="user", content="Hello!")]

            await provider.generate(messages, temperature=0.5, max_tokens=500)

            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["temperature"] == 0.5
            assert call_kwargs["max_tokens"] == 500


# ============================================================================
# Test Utilities
# ============================================================================

def test_llm_message_creation():
    """Test LLMMessage dataclass creation"""
    message = LLMMessage(role="user", content="Hello!")
    assert message.role == "user"
    assert message.content == "Hello!"


def test_llm_response_creation():
    """Test LLMResponse dataclass creation"""
    response = LLMResponse(
        content="Test response",
        model="gpt-4",
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        finish_reason="stop",
        raw_response={}
    )
    assert response.content == "Test response"
    assert response.model == "gpt-4"
    assert response.usage["total_tokens"] == 15
    assert response.finish_reason == "stop"
