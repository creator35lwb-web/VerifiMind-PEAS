"""
Tests for v0.5.25 — inference_mode in /health

Coverage:
  - _get_inference_mode returns "mock" when LLM_PROVIDER not set
  - _get_inference_mode returns "mock" when LLM_PROVIDER=mock
  - _get_inference_mode returns "live" when primary provider key is present
  - _get_inference_mode returns "degraded" when primary key missing but fallback key present
  - _get_inference_mode returns "mock" when no keys available
  - Server version is 0.5.25
"""

import os
import importlib
import pytest


def _reload_http_server():
    import http_server
    importlib.reload(http_server)
    return http_server


class TestGetInferenceMode:

    def test_returns_mock_when_no_provider_set(self, monkeypatch):
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
        import http_server
        result = http_server._get_inference_mode()
        assert result == "mock"

    def test_returns_mock_when_provider_is_mock(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        import http_server
        result = http_server._get_inference_mode()
        assert result == "mock"

    def test_returns_live_when_primary_key_present(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-test")
        import http_server
        result = http_server._get_inference_mode()
        assert result == "live"

    def test_returns_degraded_when_primary_key_missing_groq_present(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setenv("GROQ_API_KEY", "fake-groq-key")
        monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
        import http_server
        result = http_server._get_inference_mode()
        assert result == "degraded"

    def test_returns_degraded_when_primary_key_missing_cerebras_present(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.setenv("CEREBRAS_API_KEY", "fake-cerebras-key")
        import http_server
        result = http_server._get_inference_mode()
        assert result == "degraded"

    def test_returns_mock_when_all_keys_missing(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("CEREBRAS_API_KEY", raising=False)
        import http_server
        result = http_server._get_inference_mode()
        assert result == "mock"

    def test_valid_return_values(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        import http_server
        result = http_server._get_inference_mode()
        assert result in ("live", "degraded", "mock")


class TestServerVersion:

    def test_server_version_is_0525(self):
        import http_server
        assert http_server.SERVER_VERSION == "0.5.27"
