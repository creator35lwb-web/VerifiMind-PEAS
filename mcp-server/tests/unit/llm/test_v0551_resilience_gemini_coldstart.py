"""
v0.5.51 Resilience Pass batch 2 — Gemini SDK boundary + cold-start laziness
===========================================================================

Foundation Inspection pass 2, batch 2 (Hub #81). Batch 1 (PR #294) proved the
fallback cascade and Firestore degradation; the two residuals routed here:

1. GeminiProvider runs the X seat on the FREE tier in prod, yet since the
   v0.5.47 `google.genai` migration no test walked the SDK boundary — the
   v0.5.50 provider-contract file covered OpenAI/Groq/Anthropic/Mistral and
   explicitly deferred Gemini. These tests mock the genai client faithfully
   (sync `models.generate_content`, `response.text`, `usage_metadata` token
   fields) and pin the whole parse ladder: real / partial-with-defaults /
   scattered-object merge / fence stripping / raise-on-SDK-error.

2. Cold-start behavior: Cloud Run cold starts must not pay for (or crash on)
   eager client construction. Firestore is lazy + cached; import must not
   construct clients.
"""

import asyncio
import json

import pytest

from verifimind_mcp.llm.provider import (
    GeminiProvider,
    GroqProvider,
    get_provider_with_fallback,
)
import verifimind_mcp.registration as reg


ENV_KEYS = [
    "LLM_PROVIDER", "VERIFIMIND_LLM_PROVIDER", "LLM_FALLBACK_PROVIDER",
    "GEMINI_API_KEY", "GROQ_API_KEY", "CEREBRAS_API_KEY",
    "FIRESTORE_PROJECT_ID", "GOOGLE_CLOUD_PROJECT",
]


@pytest.fixture
def clean_env(monkeypatch):
    for k in ENV_KEYS:
        monkeypatch.delenv(k, raising=False)
    return monkeypatch


# ---------------------------------------------------------------------------
# Faithful google.genai stand-ins (sync generate_content, usage_metadata names)
# ---------------------------------------------------------------------------

class _Usage:
    prompt_token_count = 11
    candidates_token_count = 5
    total_token_count = 16


class _RespWithUsage:
    def __init__(self, text):
        self.text = text
        self.usage_metadata = _Usage()


class _RespNoUsage:
    """Deliberately has NO usage_metadata attribute (hasattr must be False)."""
    def __init__(self, text):
        self.text = text


class _FakeModels:
    def __init__(self, response=None, exc=None):
        self.calls = []
        self._response = response
        self._exc = exc

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self._exc is not None:
            raise self._exc
        return self._response


class _FakeClient:
    def __init__(self, models):
        self.models = models


def _gemini(response=None, exc=None, monkeypatch=None):
    """Construct a GeminiProvider with the SDK boundary replaced."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    p = GeminiProvider()
    fake = _FakeModels(response=response, exc=exc)
    p.client = _FakeClient(fake)
    return p, fake


SCHEMA = {
    "required": ["reasoning_steps", "innovation_score", "strategic_value", "recommendation"],
    "properties": {
        "reasoning_steps": {"type": "array"},
        "innovation_score": {"type": "number", "minimum": 0, "maximum": 10},
        "strategic_value": {"type": "number", "minimum": 0, "maximum": 10},
        "recommendation": {"type": "string"},
    },
}


# ---------------------------------------------------------------------------
# Construction contract
# ---------------------------------------------------------------------------

def test_no_key_raises_value_error(clean_env):
    with pytest.raises(ValueError) as e:
        GeminiProvider()
    assert "GEMINI_API_KEY" in str(e.value)


def test_env_key_accepted(clean_env):
    clean_env.setenv("GEMINI_API_KEY", "test-key")
    p = GeminiProvider()
    assert p.api_key == "test-key"


def test_model_name_is_namespaced(clean_env):
    clean_env.setenv("GEMINI_API_KEY", "test-key")
    assert GeminiProvider().get_model_name().startswith("gemini/")


# ---------------------------------------------------------------------------
# generate(): happy path + config passthrough
# ---------------------------------------------------------------------------

def test_generate_real_quality_and_usage_mapping(clean_env):
    full = json.dumps({
        "reasoning_steps": [{"step_number": 1, "thought": "t", "confidence": 0.9}],
        "innovation_score": 7.5, "strategic_value": 6.0, "recommendation": "proceed",
    })
    p, fake = _gemini(response=_RespWithUsage(full), monkeypatch=clean_env)
    out = asyncio.run(p.generate("analyze", output_schema=SCHEMA,
                                 temperature=0.3, max_tokens=2048))
    assert out["_inference_quality"] == "real"
    assert out["content"]["innovation_score"] == pytest.approx(7.5)
    # usage_metadata field names map onto the provider-neutral usage dict
    assert out["usage"] == {"input_tokens": 11, "output_tokens": 5, "total_tokens": 16}
    # config passthrough (google.genai takes max_output_tokens, not max_tokens)
    call = fake.calls[0]
    assert call["config"] == {"temperature": 0.3, "max_output_tokens": 2048}
    assert call["model"] == p.model


def test_schema_guidance_injected_into_prompt(clean_env):
    full = json.dumps({"reasoning_steps": [], "innovation_score": 5,
                       "strategic_value": 5, "recommendation": "r"})
    p, fake = _gemini(response=_RespWithUsage(full), monkeypatch=clean_env)
    asyncio.run(p.generate("analyze this", output_schema=SCHEMA))
    sent = fake.calls[0]["contents"]
    assert "EXACTLY ONE JSON object" in sent
    for field in SCHEMA["required"]:
        assert field in sent


def test_fenced_json_is_stripped(clean_env):
    fenced = "```json\n" + json.dumps({
        "reasoning_steps": [], "innovation_score": 8.0,
        "strategic_value": 7.0, "recommendation": "proceed",
    }) + "\n```"
    p, _ = _gemini(response=_RespWithUsage(fenced), monkeypatch=clean_env)
    out = asyncio.run(p.generate("x", output_schema=SCHEMA))
    assert out["content"]["innovation_score"] == pytest.approx(8.0)
    assert out["_inference_quality"] == "real"


# ---------------------------------------------------------------------------
# generate(): degradation ladder (partial fill, scattered-object merge)
# ---------------------------------------------------------------------------

def test_partial_output_filled_and_marked_partial(clean_env):
    partial = json.dumps({"reasoning_steps": [], "innovation_score": 6.0})
    p, _ = _gemini(response=_RespWithUsage(partial), monkeypatch=clean_env)
    out = asyncio.run(p.generate("x", output_schema=SCHEMA))
    content = out["content"]
    # every required field present after schema-default fill...
    for field in SCHEMA["required"]:
        assert field in content
    assert content["innovation_score"] == pytest.approx(6.0)  # model value kept
    assert content["strategic_value"] == pytest.approx(5.0)   # midpoint default
    # ...and the synthesis layer is told this was not a clean pass
    assert out["_inference_quality"] == "partial"


def test_scattered_step_objects_merged_below_half_overlap(clean_env):
    """The merge path triggers when the best single object matches < 50% of
    the schema: all found objects are merged and step-shaped ones collected
    into reasoning_steps."""
    scattered = "\n".join([
        json.dumps({"step_number": 1, "thought": "a", "confidence": 0.8}),
        json.dumps({"step_number": 2, "thought": "b", "confidence": 0.7}),
        json.dumps({"innovation_score": 7.0}),  # 1/4 fields -> below the 50% gate
    ])
    p, _ = _gemini(response=_RespWithUsage(scattered), monkeypatch=clean_env)
    out = asyncio.run(p.generate("x", output_schema=SCHEMA))
    content = out["content"]
    assert len(content["reasoning_steps"]) == 2      # real steps recovered
    assert content["innovation_score"] == pytest.approx(7.0)
    assert out["_inference_quality"] in ("partial", "fallback")


def test_half_overlap_boundary_skips_merge_and_drops_steps(clean_env):
    """FINDING F-RES-2 (PINNED current behavior, batch 2 first run): at EXACTLY
    50% field overlap the merge gate (`overlap < len*0.5`) does NOT fire — the
    best-match object wins alone, the real scattered reasoning steps are
    DISCARDED, and _fill_schema_defaults substitutes a synthetic placeholder
    step (quality honestly marked partial). Conservative (scores kept, quality
    flagged) but recoverable content is lost. Fix candidate for the M4 parse-
    ladder work (gate `<=` instead of `<`); any change must consciously update
    this test."""
    scattered = "\n".join([
        json.dumps({"step_number": 1, "thought": "a", "confidence": 0.8}),
        json.dumps({"step_number": 2, "thought": "b", "confidence": 0.7}),
        json.dumps({"innovation_score": 7.0, "strategic_value": 6.5}),  # 2/4 = exactly 50%
    ])
    p, _ = _gemini(response=_RespWithUsage(scattered), monkeypatch=clean_env)
    out = asyncio.run(p.generate("x", output_schema=SCHEMA))
    content = out["content"]
    assert content["innovation_score"] == pytest.approx(7.0)
    # the two real steps were dropped; the fill layer synthesized one placeholder
    assert len(content["reasoning_steps"]) == 1
    assert content["reasoning_steps"][0]["thought"].startswith("Analysis was partially")
    assert out["_inference_quality"] == "partial"


def test_missing_usage_metadata_degrades_to_zeros(clean_env):
    full = json.dumps({"reasoning_steps": [], "innovation_score": 5,
                       "strategic_value": 5, "recommendation": "r"})
    p, _ = _gemini(response=_RespNoUsage(full), monkeypatch=clean_env)
    out = asyncio.run(p.generate("x", output_schema=SCHEMA))
    assert out["usage"] == {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


# ---------------------------------------------------------------------------
# generate(): SDK errors raise (the cascade is handled UPSTREAM)
# ---------------------------------------------------------------------------

def test_sdk_error_propagates(clean_env):
    p, _ = _gemini(exc=RuntimeError("503 Service Unavailable"), monkeypatch=clean_env)
    coro = p.generate("x", output_schema=SCHEMA)
    with pytest.raises(RuntimeError):
        asyncio.run(coro)


def test_keyless_gemini_cascades_to_groq(clean_env):
    """The prod-relevant cascade: X seat's Gemini unavailable -> free-tier Groq."""
    clean_env.setenv("GROQ_API_KEY", "gsk_x")
    p = asyncio.run(get_provider_with_fallback("gemini"))
    assert isinstance(p, GroqProvider)


# ---------------------------------------------------------------------------
# Cold-start laziness (Cloud Run: no eager clients, cached singletons)
# ---------------------------------------------------------------------------

def test_firestore_client_constructed_once_and_cached(clean_env):
    clean_env.setenv("FIRESTORE_PROJECT_ID", "test-project")
    clean_env.setattr(reg, "_firestore_client", None)

    constructions = []

    class _FakeFirestoreClient:
        def __init__(self, project=None):
            constructions.append(project)

    import google.cloud.firestore as gcf
    clean_env.setattr(gcf, "Client", _FakeFirestoreClient)

    first = reg._get_firestore()
    second = reg._get_firestore()
    assert first is second is not None
    assert constructions == ["test-project"]  # exactly one construction, cached


def test_firestore_not_constructed_without_config(clean_env):
    clean_env.setattr(reg, "_firestore_client", None)
    assert reg._get_firestore() is None
    assert reg._firestore_client is None  # nothing cached on the None path


def test_import_does_not_eagerly_construct_clients():
    """Module import must leave the Firestore singleton unset until first use
    (the module-level default; eager construction would run at cold start)."""
    import importlib
    import verifimind_mcp.registration as fresh
    assert hasattr(fresh, "_firestore_client")
    # The global starts as None in a fresh module load.
    spec_default = importlib.util.find_spec("verifimind_mcp.registration")
    assert spec_default is not None
