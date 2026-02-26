"""
Unit tests for LLM Providers - BYOK v0.3.0

Tests the multi-provider support and fallback functionality.
"""

import os
import pytest
from unittest.mock import patch

# Import from the package
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src'))

from verifimind_mcp.llm.provider import (
    get_provider,
    get_provider_with_fallback,
    validate_provider_config,
    list_providers,
    list_free_tier_providers,
    get_provider_info,
    MockProvider,
    PROVIDER_CONFIGS,
)


class TestProviderConfiguration:
    """Test provider configuration and metadata."""

    def test_provider_configs_has_all_providers(self):
        """Verify all expected providers are configured."""
        expected_providers = ['gemini', 'openai', 'anthropic', 'groq', 'mistral', 'ollama', 'mock']
        for provider in expected_providers:
            assert provider in PROVIDER_CONFIGS, f"Missing provider: {provider}"

    def test_free_tier_providers(self):
        """Verify free tier providers are correctly identified."""
        free_providers = list_free_tier_providers()
        assert 'gemini' in free_providers
        assert 'groq' in free_providers
        assert 'ollama' in free_providers
        assert 'mock' in free_providers
        assert 'openai' not in free_providers
        assert 'anthropic' not in free_providers

    def test_provider_info(self):
        """Test get_provider_info returns correct metadata."""
        gemini_info = get_provider_info('gemini')
        assert gemini_info['name'] == 'Google Gemini'
        assert gemini_info['free_tier'] is True
        assert 'gemini-2.5-flash' in gemini_info['models']

    def test_list_providers_returns_all(self):
        """Test list_providers returns all configured providers."""
        providers = list_providers()
        assert len(providers) == 7
        provider_ids = [p['id'] for p in providers]
        assert 'gemini' in provider_ids
        assert 'mock' in provider_ids


class TestMockProvider:
    """Test MockProvider functionality."""

    def test_mock_provider_creation(self):
        """Test MockProvider can be created without API key."""
        provider = MockProvider()
        assert provider.get_model_name() == "mock/test-model"

    @pytest.mark.asyncio
    async def test_mock_provider_generate(self):
        """Test MockProvider generates mock responses."""
        provider = MockProvider()
        response = await provider.generate("Test prompt")
        assert "content" in response or "reasoning_steps" in response

    def test_mock_provider_call_count(self):
        """Test MockProvider tracks call count."""
        provider = MockProvider()
        assert provider.call_count == 0


class TestGetProvider:
    """Test get_provider factory function."""

    def test_get_mock_provider(self):
        """Test getting mock provider."""
        provider = get_provider("mock")
        assert provider.get_model_name() == "mock/test-model"

    def test_unknown_provider_raises(self):
        """Test unknown provider raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            get_provider("unknown_provider")
        assert "Unknown provider" in str(excinfo.value)

    @patch.dict(os.environ, {'LLM_PROVIDER': 'mock'})
    def test_provider_from_env(self):
        """Test provider is read from environment variable."""
        provider = get_provider()
        assert provider.get_model_name() == "mock/test-model"

    @patch.dict(os.environ, {'VERIFIMIND_LLM_PROVIDER': 'mock'}, clear=True)
    def test_legacy_env_var_support(self):
        """Test legacy VERIFIMIND_LLM_PROVIDER env var is supported."""
        # Clear LLM_PROVIDER to test fallback
        if 'LLM_PROVIDER' in os.environ:
            del os.environ['LLM_PROVIDER']
        provider = get_provider()
        assert provider.get_model_name() == "mock/test-model"


class TestValidateProviderConfig:
    """Test provider configuration validation."""

    def test_validate_mock_provider(self):
        """Test validating mock provider (no API key needed)."""
        result = validate_provider_config('mock')
        assert result['valid'] is True
        assert result['provider'] == 'mock'

    def test_validate_unknown_provider(self):
        """Test validating unknown provider."""
        result = validate_provider_config('unknown')
        assert result['valid'] is False
        assert 'Unknown provider' in result['error']

    @patch.dict(os.environ, {}, clear=True)
    def test_validate_gemini_without_key(self):
        """Test validating Gemini without API key."""
        # Ensure no API key is set
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']
        result = validate_provider_config('gemini')
        assert result['valid'] is False
        assert 'GEMINI_API_KEY' in result['error']

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'})
    def test_validate_gemini_with_key(self):
        """Test validating Gemini with API key."""
        result = validate_provider_config('gemini')
        assert result['valid'] is True
        assert result['free_tier'] is True


class TestGetProviderWithFallback:
    """Test get_provider_with_fallback function."""

    @pytest.mark.asyncio
    async def test_fallback_to_mock(self):
        """Test fallback to mock provider when primary fails."""
        # Use a provider that will fail (no API key)
        with patch.dict(os.environ, {'LLM_PROVIDER': 'gemini', 'LLM_FALLBACK_PROVIDER': 'mock'}, clear=True):
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']
            provider = await get_provider_with_fallback()
            assert provider.get_model_name() == "mock/test-model"

    @pytest.mark.asyncio
    async def test_mock_primary_no_fallback_needed(self):
        """Test mock as primary doesn't need fallback."""
        with patch.dict(os.environ, {'LLM_PROVIDER': 'mock'}):
            provider = await get_provider_with_fallback()
            assert provider.get_model_name() == "mock/test-model"


class TestProviderClasses:
    """Test individual provider class properties."""

    def test_gemini_provider_requires_key(self):
        """Test GeminiProvider requires API key."""
        from verifimind_mcp.llm.provider import GeminiProvider
        with patch.dict(os.environ, {}, clear=True):
            if 'GEMINI_API_KEY' in os.environ:
                del os.environ['GEMINI_API_KEY']
            with pytest.raises(ValueError) as excinfo:
                GeminiProvider()
            assert 'GEMINI_API_KEY' in str(excinfo.value)

    def test_groq_provider_requires_key(self):
        """Test GroqProvider requires API key."""
        from verifimind_mcp.llm.provider import GroqProvider
        with patch.dict(os.environ, {}, clear=True):
            if 'GROQ_API_KEY' in os.environ:
                del os.environ['GROQ_API_KEY']
            with pytest.raises(ValueError) as excinfo:
                GroqProvider()
            assert 'GROQ_API_KEY' in str(excinfo.value)

    def test_mistral_provider_requires_key(self):
        """Test MistralProvider requires API key."""
        from verifimind_mcp.llm.provider import MistralProvider
        with patch.dict(os.environ, {}, clear=True):
            if 'MISTRAL_API_KEY' in os.environ:
                del os.environ['MISTRAL_API_KEY']
            with pytest.raises(ValueError) as excinfo:
                MistralProvider()
            assert 'MISTRAL_API_KEY' in str(excinfo.value)

    def test_ollama_provider_no_key_needed(self):
        """Test OllamaProvider doesn't require API key."""
        from verifimind_mcp.llm.provider import OllamaProvider
        provider = OllamaProvider()
        assert provider.get_model_name() == "ollama/llama3.2"

    def test_groq_default_model(self):
        """Test GroqProvider uses llama-3.3-70b-versatile by default."""
        from verifimind_mcp.llm.provider import GroqProvider
        with patch.dict(os.environ, {'GROQ_API_KEY': 'test-key'}):
            try:
                provider = GroqProvider()
                assert provider.model == "llama-3.3-70b-versatile"
                assert provider.get_model_name() == "groq/llama-3.3-70b-versatile"
            except ImportError:
                pytest.skip("groq package not installed")


class TestJsonExtraction:
    """Test JSON extraction and schema defaults methods (v0.4.3.1+)."""

    def test_extract_best_json_single_object(self):
        """Test extracting a single well-formed JSON object."""
        from verifimind_mcp.llm.provider import GeminiProvider
        text = '{"innovation_score": 8.5, "confidence": 0.9}'
        result = GeminiProvider._extract_best_json(text, ["innovation_score", "confidence"])
        assert result is not None
        assert result["innovation_score"] == 8.5
        assert result["confidence"] == 0.9

    def test_extract_best_json_multiple_objects(self):
        """Test extracting best match from multiple JSON objects."""
        from verifimind_mcp.llm.provider import GeminiProvider
        text = '{"step_number": 1, "thought": "test"} {"innovation_score": 8.5, "confidence": 0.9, "recommendation": "go"}'
        result = GeminiProvider._extract_best_json(text, ["innovation_score", "confidence", "recommendation"])
        assert result is not None
        assert result["innovation_score"] == 8.5
        assert "recommendation" in result

    def test_extract_best_json_no_match(self):
        """Test extraction returns None when no JSON found."""
        from verifimind_mcp.llm.provider import GeminiProvider
        result = GeminiProvider._extract_best_json("no json here", ["field1"])
        assert result is None

    def test_merge_json_objects_with_reasoning_steps(self):
        """Test merging scattered reasoning steps into one object."""
        from verifimind_mcp.llm.provider import GeminiProvider
        text = '{"step_number": 1, "thought": "first"} {"step_number": 2, "thought": "second"} {"recommendation": "proceed"}'
        result = GeminiProvider._merge_json_objects(text, ["reasoning_steps", "recommendation"])
        assert result is not None
        assert "reasoning_steps" in result
        assert len(result["reasoning_steps"]) == 2
        assert result["recommendation"] == "proceed"

    def test_fill_schema_defaults_number_fields(self):
        """Test filling missing number fields with midpoint defaults."""
        from verifimind_mcp.llm.provider import GeminiProvider
        schema = {
            "required": ["score", "confidence"],
            "properties": {
                "score": {"type": "number", "minimum": 0, "maximum": 10},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            }
        }
        data = {}
        result = GeminiProvider._fill_schema_defaults(data, schema)
        assert result["score"] == 5.0
        assert result["confidence"] == 0.5

    def test_fill_schema_defaults_preserves_existing(self):
        """Test that existing fields are not overwritten."""
        from verifimind_mcp.llm.provider import GeminiProvider
        schema = {
            "required": ["score", "name"],
            "properties": {
                "score": {"type": "number", "minimum": 0, "maximum": 10},
                "name": {"type": "string"},
            }
        }
        data = {"score": 8.5}
        result = GeminiProvider._fill_schema_defaults(data, schema)
        assert result["score"] == 8.5  # preserved
        assert "name" in result  # filled

    def test_fill_schema_defaults_boolean_and_array(self):
        """Test filling boolean and array defaults."""
        from verifimind_mcp.llm.provider import GeminiProvider
        schema = {
            "required": ["active", "items", "reasoning_steps"],
            "properties": {
                "active": {"type": "boolean"},
                "items": {"type": "array"},
                "reasoning_steps": {"type": "array"},
            }
        }
        data = {}
        result = GeminiProvider._fill_schema_defaults(data, schema)
        assert result["active"] is False
        assert isinstance(result["items"], list)
        assert isinstance(result["reasoning_steps"], list)
        assert len(result["reasoning_steps"]) == 1
        assert result["reasoning_steps"][0]["step_number"] == 1


class TestStripMarkdownCodeFences:
    """Test markdown code fence stripping."""

    def test_strip_json_fence(self):
        """Test stripping ```json fences."""
        from verifimind_mcp.llm.provider import strip_markdown_code_fences
        text = '```json\n{"key": "value"}\n```'
        assert strip_markdown_code_fences(text) == '{"key": "value"}'

    def test_strip_fence_with_preamble(self):
        """Test stripping fences with text before them."""
        from verifimind_mcp.llm.provider import strip_markdown_code_fences
        text = 'Here is the analysis:\n```json\n{"key": "value"}\n```'
        assert strip_markdown_code_fences(text) == '{"key": "value"}'

    def test_no_fence(self):
        """Test text without fences is returned as-is."""
        from verifimind_mcp.llm.provider import strip_markdown_code_fences
        text = '{"key": "value"}'
        assert strip_markdown_code_fences(text) == '{"key": "value"}'


# Integration tests (skipped if no API keys)
class TestIntegration:
    """Integration tests that require real API keys."""

    @pytest.mark.skipif(not os.getenv("GEMINI_API_KEY"), reason="No Gemini API key")
    @pytest.mark.asyncio
    async def test_gemini_integration(self):
        """Test real Gemini API call."""
        provider = get_provider("gemini")
        response = await provider.generate("Say hello in one word")
        assert response["content"]
        assert "usage" in response

    @pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="No Groq API key")
    @pytest.mark.asyncio
    async def test_groq_integration(self):
        """Test real Groq API call."""
        provider = get_provider("groq")
        response = await provider.generate("Say hello in one word")
        assert response["content"]
        assert "usage" in response
