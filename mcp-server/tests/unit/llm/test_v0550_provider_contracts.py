"""
v0.5.50 Robustness Pass — provider generate() contracts (mocked SDKs)
=====================================================================

Foundation Inspection pass 1, batch 3 (Hub #81). The map showed provider.py's
generate() bodies at 43% — the mock-walk harness bypasses them (MockProvider),
so the REAL request-building and parse paths were dark. These tests mock the
SDK CLIENT (not the provider), exercising each provider's actual generate()
body: request-kwarg contracts, parse/extraction paths, and error propagation.
"""

import json

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from verifimind_mcp.llm.provider import (
    OpenAIProvider,
    AnthropicProvider,
    GroqProvider,
    GROQ_8K_TPM_COMPLETION_CAP,
)


def _openai_style_response(text: str, prompt_toks=10, completion_toks=5):
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = text
    resp.usage.prompt_tokens = prompt_toks
    resp.usage.completion_tokens = completion_toks
    resp.usage.total_tokens = prompt_toks + completion_toks
    return resp


def _anthropic_style_response(text: str, in_toks=10, out_toks=5):
    resp = MagicMock()
    block = MagicMock()
    block.text = text
    resp.content = [block]
    resp.usage.input_tokens = in_toks
    resp.usage.output_tokens = out_toks
    return resp


def _capture(provider, response):
    captured = {}

    def fake_create(**kwargs):
        captured.update(kwargs)
        return response

    return captured, AsyncMock(side_effect=fake_create)


# ---------------------------------------------------------------------------
# OpenAI — the gpt-5.x request-contract branch (v0.5.47, live-verified rule)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_openai_gpt4x_sends_max_tokens_and_temperature():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
        p = OpenAIProvider(model="gpt-4.1")
    p.client = MagicMock()
    captured, p.client.chat.completions.create = _capture(p, _openai_style_response('{"ok": 1}'))
    await p.generate("hi", temperature=0.3, max_tokens=1234)
    assert captured["max_tokens"] == 1234
    assert captured["temperature"] == pytest.approx(0.3)
    assert "max_completion_tokens" not in captured


@pytest.mark.asyncio
async def test_openai_gpt5x_sends_max_completion_tokens_no_temperature():
    """gpt-5.x rejects max_tokens AND custom temperature (400) — the branch
    must send max_completion_tokens only (v0.5.47 contract)."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
        p = OpenAIProvider(model="gpt-5.5")
    p.client = MagicMock()
    captured, p.client.chat.completions.create = _capture(p, _openai_style_response('{"ok": 1}'))
    await p.generate("hi", temperature=0.3, max_tokens=1234)
    assert captured["max_completion_tokens"] == 1234
    assert "max_tokens" not in captured
    assert "temperature" not in captured


@pytest.mark.asyncio
async def test_openai_clean_json_parses_real_quality():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
        p = OpenAIProvider(model="gpt-4.1")
    p.client = MagicMock()
    _, p.client.chat.completions.create = _capture(p, _openai_style_response('{"score": 7}'))
    out = await p.generate("hi")
    assert out["content"] == {"score": 7}
    assert out["_inference_quality"] == "real"
    assert out["usage"]["total_tokens"] == 15


@pytest.mark.asyncio
async def test_openai_fenced_json_is_stripped():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
        p = OpenAIProvider(model="gpt-4.1")
    p.client = MagicMock()
    _, p.client.chat.completions.create = _capture(
        p, _openai_style_response('```json\n{"score": 8}\n```'))
    out = await p.generate("hi")
    assert out["content"] == {"score": 8}


@pytest.mark.asyncio
async def test_openai_unparseable_content_returns_raw_response_contract():
    """Parse failure does NOT raise — the provider returns raw_response +
    parse_error for the downstream coercion/fill layer."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
        p = OpenAIProvider(model="gpt-4.1")
    p.client = MagicMock()
    _, p.client.chat.completions.create = _capture(
        p, _openai_style_response("I am not JSON at all"))
    out = await p.generate("hi")
    assert out["content"]["raw_response"] == "I am not JSON at all"
    assert "parse_error" in out["content"]


@pytest.mark.asyncio
async def test_openai_sdk_exception_propagates():
    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}):
        p = OpenAIProvider(model="gpt-4.1")
    p.client = MagicMock()
    p.client.chat.completions.create = AsyncMock(side_effect=RuntimeError("boom"))
    with pytest.raises(RuntimeError):
        await p.generate("hi")


# ---------------------------------------------------------------------------
# Groq — think-strip integration + TPM clamp interplay + schema guidance
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_groq_think_block_content_parses(monkeypatch):
    """v0.5.49: Qwen3.x-style <think> prefix must not break JSON parsing
    through the REAL GroqProvider.generate body."""
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    p = GroqProvider(model="qwen/qwen3.6-27b")
    p.client = MagicMock()
    _, p.client.chat.completions.create = _capture(
        p, _openai_style_response('<think>\nreasoning...\n</think>\n{"score": 6}'))
    out = await p.generate("hi")
    assert out["content"].get("score") == 6


@pytest.mark.asyncio
async def test_groq_8k_model_clamps_reservation_in_real_body(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    p = GroqProvider(model="openai/gpt-oss-120b")
    p.client = MagicMock()
    captured, p.client.chat.completions.create = _capture(p, _openai_style_response('{"ok": 1}'))
    await p.generate("hi", max_tokens=8192)
    assert captured["max_tokens"] == GROQ_8K_TPM_COMPLETION_CAP


@pytest.mark.asyncio
async def test_groq_schema_hint_added_to_prompt(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    p = GroqProvider(model="openai/gpt-oss-120b")
    p.client = MagicMock()
    captured, p.client.chat.completions.create = _capture(p, _openai_style_response('{"a": 1}'))
    await p.generate("analyze", output_schema={"required": ["a"], "properties": {"a": {"type": "integer"}}})
    sent = captured["messages"][0]["content"]
    assert "EXACTLY ONE JSON object" in sent and '"a"' in sent


# ---------------------------------------------------------------------------
# Anthropic — content-block extraction + fence stripping (v0.5.23 contract)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_anthropic_fenced_json_parses(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    p = AnthropicProvider()
    p.client = MagicMock()
    _, p.client.messages.create = _capture(
        p, _anthropic_style_response('```json\n{"ethics_score": 8.5}\n```'))
    out = await p.generate("hi")
    assert out["content"].get("ethics_score") == pytest.approx(8.5)
    assert out["usage"]["total_tokens"] == 15


@pytest.mark.asyncio
async def test_anthropic_sdk_exception_propagates(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    p = AnthropicProvider()
    p.client = MagicMock()
    p.client.messages.create = AsyncMock(side_effect=ConnectionError("down"))
    with pytest.raises(ConnectionError):
        await p.generate("hi")
