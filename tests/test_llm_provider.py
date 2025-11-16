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
from unittest.mock import Mock, AsyncMock, patch
from llm.llm_provider import (
    LLMMessage,
    LLMResponse,
    OpenAIProvider,
    AnthropicProvider,
    LLMProviderError,
    LLMAPIError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMInvalidRequestError,
)


class TestOpenAIProvider:
    """Tests for OpenAI provider"""

    @pytest.mark.asyncio
    async def test_openai_success(self):
        """Test successful OpenAI API call"""
        # Create mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test response from OpenAI"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
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
                LLMMessage(role="user", content="Hello, world!")
            ]

            response = await provider.generate(messages)

            # Assertions
            assert response.content == "This is a test response from OpenAI"
            assert response.model == "gpt-4"
            assert response.usage["total_tokens"] == 18
            assert response.finish_reason == "stop"

            # Verify the API was called with correct parameters
            mock_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["model"] == "gpt-4"
            assert len(call_kwargs["messages"]) == 2

    @pytest.mark.asyncio
    async def test_openai_api_error(self):
        """Test OpenAI API error handling"""
        from openai import APIError

        # Mock the AsyncOpenAI client to raise APIError
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_request = Mock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=APIError(
                    message="API Error occurred",
                    request=mock_request,
                    body=None
                )
            )

            provider = OpenAIProvider(api_key="test-key", model="gpt-4")
            messages = [LLMMessage(role="user", content="Test")]

            # Should raise our custom LLMAPIError
            with pytest.raises(LLMAPIError) as exc_info:
                await provider.generate(messages)

            assert "OpenAI API error" in str(exc_info.value.message)
            assert exc_info.value.provider == "OpenAI"

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
            messages = [LLMMessage(role="user", content="Test")]

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
            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(LLMRateLimitError) as exc_info:
                await provider.generate(messages)

            assert "rate limit" in str(exc_info.value.message).lower()
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
            messages = [LLMMessage(role="user", content="Test")]

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
            messages = [LLMMessage(role="user", content="Test")]

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
            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(LLMInvalidRequestError) as exc_info:
                await provider.generate(messages)

            assert "invalid request" in str(exc_info.value.message).lower()
            assert exc_info.value.provider == "OpenAI"

    @pytest.mark.asyncio
    async def test_openai_no_api_key(self):
        """Test OpenAI provider with no API key"""
        provider = OpenAIProvider(api_key=None, model="gpt-4")
        messages = [LLMMessage(role="user", content="Test")]

        with pytest.raises(LLMAuthenticationError) as exc_info:
            await provider.generate(messages)

        assert "API key not provided" in str(exc_info.value.message)
        assert exc_info.value.provider == "OpenAI"

    @pytest.mark.asyncio
    async def test_openai_response_parsing_error(self):
        """Test handling of malformed OpenAI response"""
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Create a response with missing fields
            mock_response = Mock()
            mock_response.choices = []  # Empty choices should cause parsing error
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            provider = OpenAIProvider(api_key="test-key", model="gpt-4")
            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(LLMAPIError) as exc_info:
                await provider.generate(messages)

            assert "parse" in str(exc_info.value.message).lower()


class TestAnthropicProvider:
    """Tests for Anthropic provider"""

    @pytest.mark.asyncio
    async def test_anthropic_success(self):
        """Test successful Anthropic API call"""
        # Create mock response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "This is a test response from Claude"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 15
        mock_response.usage.output_tokens = 12

        with patch('anthropic.AsyncAnthropic') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            provider = AnthropicProvider(api_key="test-key", model="claude-3-5-sonnet-20241022")
            messages = [
                LLMMessage(role="system", content="You are a helpful assistant."),
                LLMMessage(role="user", content="Hello, Claude!")
            ]

            response = await provider.generate(messages)

            assert response.content == "This is a test response from Claude"
            assert response.model == "claude-3-5-sonnet-20241022"
            assert response.usage["total_tokens"] == 27
            assert response.finish_reason == "end_turn"

    @pytest.mark.asyncio
    async def test_anthropic_api_error(self):
        """Test Anthropic API error handling"""
        from anthropic import APIError

        with patch('anthropic.AsyncAnthropic') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            mock_request = Mock()
            mock_client.messages.create = AsyncMock(
                side_effect=APIError(
                    message="API Error occurred",
                    request=mock_request,
                    body=None
                )
            )

            provider = AnthropicProvider(api_key="test-key")
            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(LLMAPIError) as exc_info:
                await provider.generate(messages)

            assert "Anthropic API error" in str(exc_info.value.message)
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
            messages = [LLMMessage(role="user", content="Test")]

            with pytest.raises(LLMAuthenticationError) as exc_info:
                await provider.generate(messages)

            assert "authentication failed" in str(exc_info.value.message).lower()
            assert exc_info.value.provider == "Anthropic"

    @pytest.mark.asyncio
    async def test_anthropic_no_api_key(self):
        """Test Anthropic provider with no API key"""
        provider = AnthropicProvider(api_key=None)
        messages = [LLMMessage(role="user", content="Test")]

        with pytest.raises(LLMAuthenticationError) as exc_info:
            await provider.generate(messages)

        assert "API key not provided" in str(exc_info.value.message)
        assert exc_info.value.provider == "Anthropic"


class TestEdgeCases:
    """Tests for edge cases and special scenarios"""

    @pytest.mark.asyncio
    async def test_empty_messages_list(self):
        """Test handling of empty messages list"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 0
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 5

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            provider = OpenAIProvider(api_key="test-key", model="gpt-4")
            response = await provider.generate([])

            # Should still work with empty messages
            assert response.content == "Response"

    @pytest.mark.asyncio
    async def test_multiple_system_messages(self):
        """Test handling of multiple system messages"""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Response"
        mock_response.model = "claude-3-5-sonnet-20241022"
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with patch('anthropic.AsyncAnthropic') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            provider = AnthropicProvider(api_key="test-key")
            messages = [
                LLMMessage(role="system", content="You are helpful."),
                LLMMessage(role="system", content="You are concise."),
                LLMMessage(role="user", content="Hello")
            ]

            response = await provider.generate(messages)
            assert response.content == "Response"

    @pytest.mark.asyncio
    async def test_custom_temperature_and_max_tokens(self):
        """Test custom temperature and max_tokens parameters"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Creative response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 3
        mock_response.usage.total_tokens = 8

        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            provider = OpenAIProvider(api_key="test-key", model="gpt-4")
            messages = [LLMMessage(role="user", content="Be creative")]

            response = await provider.generate(messages, temperature=1.5, max_tokens=500)

            # Verify custom parameters were passed
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
            assert call_kwargs["temperature"] == 1.5
            assert call_kwargs["max_tokens"] == 500


class TestDataClasses:
    """Tests for data classes"""

    def test_llm_message_creation(self):
        """Test LLMMessage creation"""
        message = LLMMessage(role="user", content="Hello, world!")
        assert message.role == "user"
        assert message.content == "Hello, world!"

    def test_llm_response_creation(self):
        """Test LLMResponse creation"""
        response = LLMResponse(
            content="Test response",
            model="gpt-4",
            usage={"total_tokens": 100},
            finish_reason="stop",
            raw_response={"test": "data"}
        )
        assert response.content == "Test response"
        assert response.model == "gpt-4"
        assert response.usage["total_tokens"] == 100
        assert response.finish_reason == "stop"
