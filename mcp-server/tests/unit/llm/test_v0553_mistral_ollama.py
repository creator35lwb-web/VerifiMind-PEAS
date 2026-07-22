"""
v0.5.53 — Mistral currency + Ollama SDK-boundary contract
=========================================================

Two lanes from Alton's S78 direction:

1. Mistral (EU-sovereign diversification): BYOK default bumped to
   mistral-medium-3.5 (live-verified 2026-07-22 on Alton's key — chat probe OK,
   25k TPM / 50 RPM headers observed). Menu currency pinned here.

2. Ollama (the keyless local open-source path): the provider class shipped in
   v0.4.x but its httpx boundary had ZERO tests — same gap class the Gemini
   SDK had before resilience batch 2. Alton's device is CPU-only, so the
   health check is a faithful mocked-boundary contract, not live inference.

FINDING F-RES-3 (pinned below): Ollama's parse-failure path returns
`_inference_quality: "real"` while shipping `{"raw_response", "parse_error"}`
content — unlike Gemini/Groq, which mark the same situation "fallback".
Downstream quality gates (degraded-Z caps) would NOT fire on an Ollama parse
failure. Candidate fix routed; behavior pinned so any change is conscious.
"""

import asyncio
import json

import pytest

from verifimind_mcp.llm.provider import (
    PROVIDER_CONFIGS,
    OllamaProvider,
)


# ---------------------------------------------------------------------------
# Mistral currency (v0.5.53)
# ---------------------------------------------------------------------------

def test_mistral_default_is_medium_35():
    assert PROVIDER_CONFIGS["mistral"]["default_model"] == "mistral-medium-3.5"


def test_mistral_menu_current():
    models = PROVIDER_CONFIGS["mistral"]["models"]
    assert "mistral-medium-3.5" in models
    assert "mistral-medium-3" in models  # retained for continuity
    assert models[0] == "mistral-medium-3.5"


# ---------------------------------------------------------------------------
# Faithful httpx stand-in for the Ollama /api/generate boundary
# ---------------------------------------------------------------------------

class _FakeResponse:
    def __init__(self, payload, status_error=None):
        self._payload = payload
        self._status_error = status_error

    def raise_for_status(self):
        if self._status_error:
            raise self._status_error

    def json(self):
        return self._payload


class _FakeAsyncClient:
    """Mimics `async with httpx.AsyncClient() as client: await client.post(...)`."""
    calls = []
    next_response = None
    next_exc = None

    def __init__(self, *a, **kw):
        # Accepts and ignores httpx.AsyncClient constructor kwargs (timeout etc.)
        # — the fake needs no per-instance state; class attributes carry the script.
        pass

    async def __aenter__(self):  # NOSONAR — async protocol required by `async with`
        return self

    async def __aexit__(self, *a):  # NOSONAR — async protocol required by `async with`
        return False

    async def post(self, url, **kwargs):  # NOSONAR — awaited by the provider; async signature required
        _FakeAsyncClient.calls.append({"url": url, **kwargs})
        if _FakeAsyncClient.next_exc:
            raise _FakeAsyncClient.next_exc
        return _FakeAsyncClient.next_response


@pytest.fixture
def fake_httpx(monkeypatch):
    import httpx
    _FakeAsyncClient.calls = []
    _FakeAsyncClient.next_response = None
    _FakeAsyncClient.next_exc = None
    monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)
    return _FakeAsyncClient


def _payload(text, prompt_tokens=7, eval_tokens=3):
    return {"response": text, "prompt_eval_count": prompt_tokens, "eval_count": eval_tokens}


# ---------------------------------------------------------------------------
# Construction contract — the keyless local path
# ---------------------------------------------------------------------------

def test_construction_requires_no_api_key():
    p = OllamaProvider()
    assert p.model == "llama3.2"
    assert p.base_url == "http://localhost:11434"


def test_custom_model_and_base_url():
    p = OllamaProvider(model="qwen2.5:0.5b", base_url="https://ollama.lan.example:11434")
    assert p.get_model_name() == "ollama/qwen2.5:0.5b"
    assert p.base_url == "https://ollama.lan.example:11434"


def test_config_declares_free_tier_no_key():
    cfg = PROVIDER_CONFIGS["ollama"]
    assert cfg["free_tier"] is True
    assert cfg["api_key_env"] is None


# ---------------------------------------------------------------------------
# generate(): request shape + happy path
# ---------------------------------------------------------------------------

def test_generate_happy_path_and_request_shape(fake_httpx):
    fake_httpx.next_response = _FakeResponse(_payload('{"score": 7}'))
    p = OllamaProvider(model="llama3.2")
    out = asyncio.run(p.generate("analyze", output_schema={"type": "object"},
                                 temperature=0.4, max_tokens=1024))
    assert out["content"] == {"score": 7}
    assert out["_inference_quality"] == "real"
    # Ollama's native token fields map onto the provider-neutral usage dict
    assert out["usage"] == {"input_tokens": 7, "output_tokens": 3, "total_tokens": 10}
    call = fake_httpx.calls[0]
    assert call["url"].endswith("/api/generate")
    body = call["json"]
    assert body["model"] == "llama3.2"
    assert body["stream"] is False
    # Ollama takes num_predict, not max_tokens
    assert body["options"] == {"temperature": 0.4, "num_predict": 1024}
    # schema guidance is injected into the prompt
    assert "valid JSON only" in body["prompt"]


def test_fenced_output_stripped(fake_httpx):
    fake_httpx.next_response = _FakeResponse(_payload('```json\n{"ok": true}\n```'))
    out = asyncio.run(OllamaProvider().generate("x"))
    assert out["content"] == {"ok": True}


def test_json_embedded_in_prose_extracted(fake_httpx):
    fake_httpx.next_response = _FakeResponse(_payload('Here you go: {"a": 1} hope that helps'))
    out = asyncio.run(OllamaProvider().generate("x"))
    assert out["content"] == {"a": 1}


# ---------------------------------------------------------------------------
# Degradation + error contract
# ---------------------------------------------------------------------------

def test_non_json_output_wraps_raw_response_but_stays_real(fake_httpx):
    """F-RES-3 (PINNED current behavior — routed): no JSON in the output ->
    content becomes {"raw_response": ...} yet _inference_quality remains
    "real" (Gemini/Groq mark the equivalent situation "fallback"). Downstream
    degraded-quality gates would not fire. Any change must consciously update
    this test."""
    fake_httpx.next_response = _FakeResponse(_payload("I cannot answer in JSON."))
    out = asyncio.run(OllamaProvider().generate("x"))
    assert out["content"] == {"raw_response": "I cannot answer in JSON."}
    assert out["_inference_quality"] == "real"  # the pinned inconsistency


def test_http_error_propagates(fake_httpx):
    fake_httpx.next_response = _FakeResponse({}, status_error=RuntimeError("500 Server Error"))
    with pytest.raises(RuntimeError):
        asyncio.run(OllamaProvider().generate("x"))


def test_connection_error_propagates(fake_httpx):
    fake_httpx.next_exc = ConnectionError("Ollama not running on localhost:11434")
    with pytest.raises(ConnectionError):
        asyncio.run(OllamaProvider().generate("x"))


def test_missing_usage_fields_default_to_zero(fake_httpx):
    fake_httpx.next_response = _FakeResponse({"response": '{"ok": 1}'})
    out = asyncio.run(OllamaProvider().generate("x"))
    assert out["usage"] == {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
