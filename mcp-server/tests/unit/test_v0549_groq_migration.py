"""
v0.5.49 — Groq Migration (D-65-6/7/8)
======================================

llama-3.3-70b-versatile decommissions 2026-08-16 (Groq notice). Bundle:
  - Groq default -> openai/gpt-oss-120b (namespaced ID; bare "gpt-oss-120b" 404s)
  - qwen/qwen3.6-27b replaces deprecated llama-3.1-8b-instant as the fast option
  - <think>-block stripping in the shared JSON-extraction path (Qwen3.x /
    reasoning models prefix answers with <think>...</think>)
  - /health reports protocol_version (AY/AZ ask, MCP RC assessment)
"""

import json

from verifimind_mcp.llm.provider import (
    PROVIDER_CONFIGS,
    PROVIDER_DEFAULT_GROQ_MODEL,
    strip_markdown_code_fences,
)


class TestGroqModelStack:

    def test_default_is_namespaced_gpt_oss(self):
        assert PROVIDER_DEFAULT_GROQ_MODEL == "openai/gpt-oss-120b"
        assert PROVIDER_CONFIGS["groq"]["default_model"] == "openai/gpt-oss-120b"

    def test_qwen_fast_option_listed(self):
        assert "qwen/qwen3.6-27b" in PROVIDER_CONFIGS["groq"]["models"]

    def test_llama4_scout_retained(self):
        assert "meta-llama/llama-4-scout-17b-16e-instruct" in PROVIDER_CONFIGS["groq"]["models"]

    def test_decommissioned_models_absent(self):
        models = PROVIDER_CONFIGS["groq"]["models"]
        assert "llama-3.3-70b-versatile" not in models
        assert "llama-3.1-8b-instant" not in models

    def test_groq_still_free_tier(self):
        assert PROVIDER_CONFIGS["groq"]["free_tier"] is True


class TestThinkBlockStripping:
    """Qwen3.x (and other reasoning models) prefix output with <think>...</think>."""

    def test_think_block_stripped_before_json(self):
        raw = '<think>\nLet me reason about this.\n</think>\n{"score": 7}'
        assert json.loads(strip_markdown_code_fences(raw)) == {"score": 7}

    def test_think_block_with_fences(self):
        raw = '<think>reasoning here</think>\n```json\n{"verdict": "PROCEED"}\n```'
        assert json.loads(strip_markdown_code_fences(raw)) == {"verdict": "PROCEED"}

    def test_case_insensitive_think_tags(self):
        raw = '<THINK>upper</THINK>{"ok": true}'
        assert json.loads(strip_markdown_code_fences(raw)) == {"ok": True}

    def test_no_think_block_passthrough_unchanged(self):
        raw = '{"score": 9}'
        assert strip_markdown_code_fences(raw) == '{"score": 9}'

    def test_plain_fences_still_work(self):
        raw = '```json\n{"a": 1}\n```'
        assert json.loads(strip_markdown_code_fences(raw)) == {"a": 1}

    def test_multiline_think_block(self):
        raw = "<think>\nline1\nline2\n\nline3\n</think>\n\n" + '{"b": 2}'
        assert json.loads(strip_markdown_code_fences(raw)) == {"b": 2}


class TestHealthProtocolVersion:

    def test_health_exposes_protocol_version(self):
        import http_server
        assert hasattr(http_server, "MCP_PROTOCOL_VERSION")
        assert isinstance(http_server.MCP_PROTOCOL_VERSION, str)
        assert http_server.MCP_PROTOCOL_VERSION != ""

    def test_protocol_version_resolves_from_sdk(self):
        # mcp is a pinned dependency — the fallback should not be needed in CI.
        assert http_server_protocol_version() != "unknown"


def http_server_protocol_version():
    import http_server
    return http_server.MCP_PROTOCOL_VERSION
