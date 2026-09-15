"""
LLM Provider abstraction for VerifiMind-PEAS MCP Server.

BYOK v0.4.0 - Provider Sync (model IDs + Cerebras)

This module provides a unified interface for interacting with
different LLM providers, enabling users to bring their own API keys
(BYOK) for any supported provider.

Supported Providers:
- Gemini (FREE tier available)
- Groq (FREE tier available)
- Cerebras (free tier available; limits vary by account)
- OpenAI
- Anthropic
- Mistral
- Ollama (local, FREE)
- Mock (testing)

Environment Variables:
- LLM_PROVIDER: Primary provider (default: mock)
- LLM_FALLBACK_PROVIDER: Fallback if primary fails (default: mock)
- LLM_MODEL: Override default model
- LLM_TEMPERATURE: Override temperature (default: 0.7)
- LLM_MAX_TOKENS: Override max tokens (default: 4096)
- {PROVIDER}_API_KEY: API key for each provider
"""

import os
import json
import logging
import re
from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, Optional, Type, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def _log_provider_exception(provider: str, operation: str, exc: Exception) -> None:
    """Log provider failures without reflecting SDK bodies, prompts, or keys."""
    logger.error(
        "%s %s failed exception_type=%s",
        provider,
        operation,
        type(exc).__name__,
    )

# Reasoning models (Qwen3.x, DeepSeek-R1 family) prefix answers with <think>...</think>.
# Stripped before JSON extraction so structured parsing sees only the answer payload.
_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def strip_markdown_code_fences(text: str) -> str:
    """Strip reasoning think-blocks and markdown code fences to extract clean JSON."""
    text = _THINK_BLOCK_RE.sub("", text).strip()
    lines = text.splitlines()

    # Find the first line that opens a code fence (e.g. ```json, ```JSON, ```)
    open_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            open_idx = i
            break

    if open_idx is None:
        return text

    # Find the matching closing fence (search backwards so nested fences work)
    close_idx = None
    for i in range(len(lines) - 1, open_idx, -1):
        if lines[i].strip() == '```':
            close_idx = i
            break

    content = lines[open_idx + 1 : close_idx] if close_idx is not None else lines[open_idx + 1:]
    return '\n'.join(content).strip()


# ============================================================================
# PROVIDER CONFIGURATION (BYOK v0.4.0 — Provider Sync)
# ============================================================================

# Default model per provider — single source of truth.
# (SonarCloud P2 batch-2: extracted in v0.5.39 from 12 dup-literal occurrences
# across `default_model` fields, models list entries, and per-method defaults.)
# v0.5.51 Gemini currency: gemini-3.5-flash-lite is GA, Google's documented
# migration target from gemini-2.5-flash ("outperforms prior Flash-Lite
# generations", suited for structured JSON parsing — the X-seat workload), and
# a direct responder: unlike gemini-3.5-flash it spends no thinking tokens, so
# strict max_output_tokens budgets return text instead of empty candidates.
# All IDs live-verified against ListModels + generateContent on the free-tier
# key 2026-07-22.
PROVIDER_DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"
PROVIDER_DEFAULT_OPENAI_MODEL = "gpt-5.5"  # v0.5.47 model currency (R-S51-B; live-verified 2026-06-22)
# v0.5.49 Groq migration (D-65-6): llama-3.3-70b-versatile decommissions 2026-08-16.
# NOTE: the namespaced ID is required — bare "gpt-oss-120b" returns 404 (live-verified 2026-07-16).
PROVIDER_DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"

# Groq on_demand admission rejects any request whose input + max_tokens reservation
# exceeds the model's TPM limit. gpt-oss-120b and qwen3.6-27b sit at 8,000 TPM
# (llama-3.3 was 12,000, which absorbed the v0.5.46 8192 reservation). v0.5.49
# clamped completion only; S114 showed that this still 413s for orchestrated Z/CS
# prompts. v0.5.55 makes the reservation input-aware using provider-measured
# prompt shapes, keeps a safety margin, and fails closed when useful output cannot
# fit. Limits were live-read from x-ratelimit-limit-tokens headers 2026-07-16.
# qwen3.8-27b joins the set CONSERVATIVELY: same family/size/tier as
# qwen3.6-27b, whose 8k TPM is live-proven. Over-clamping a roomier model
# only shortens completions; under-clamping an 8k model repeats the
# v0.5.49 413 class. Revisit on a live per-model rate-limit probe.
GROQ_8K_TPM_MODELS = frozenset(
    {"openai/gpt-oss-120b", "qwen/qwen3.6-27b", "qwen/qwen3.8-27b"}
)
GROQ_8K_TPM_LIMIT = 8000
GROQ_8K_TPM_COMPLETION_CAP = 4096
GROQ_TPM_SAFETY_MARGIN = 512
GROQ_MIN_COMPLETION_TOKENS = 1024
GROQ_TOKEN_ESTIMATE_CHARS_PER_TOKEN = 4
GROQ_MESSAGE_TOKEN_OVERHEAD = 8
# v0.5.58 Cerebras currency repair (RNA S128): both previously advertised
# Llama IDs returned 404 in a live BYOK probe.  These replacement IDs were
# listed by Cerebras and successfully probed on 2026-08-06.  This updates the
# BYOK catalogue only; it does not change the hosted X/Z/CS routing topology.
PROVIDER_DEFAULT_CEREBRAS_MODEL = "gpt-oss-120b"

# The six remote BYOK catalogues need an explicit freshness invariant.  A
# model list can be internally consistent and still be wrong in production
# after a provider retires an ID, which is exactly what happened to Cerebras.
# `provider_catalog_currency_issues()` is projected into /health and guarded
# by regression tests; after 90 days a deliberate re-verification is required.
REMOTE_BYOK_PROVIDER_IDS = frozenset({
    "gemini", "openai", "anthropic", "groq", "cerebras", "mistral",
})
MODEL_CURRENCY_MAX_AGE_DAYS = 90
RETIRED_MODEL_IDS_BY_PROVIDER = {
    "groq": frozenset({
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "meta-llama/llama-4-scout-17b-16e-instruct",
    }),
    "cerebras": frozenset({"llama-3.3-70b", "llama-3.1-8b"}),
}


def _groq_message_content_text(content: Any) -> str:
    """Normalize OpenAI/Groq message content to text for local token estimation."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                for key in ("text", "input_text", "content"):
                    if key in item:
                        parts.append(str(item[key]))
                        break
                else:
                    parts.append(json.dumps(item, sort_keys=True, default=str))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    if isinstance(content, (dict, tuple)):
        return json.dumps(content, sort_keys=True, default=str)
    return str(content)


def _estimate_groq_input_tokens(messages: List[Dict[str, Any]]) -> int:
    """Estimate Groq prompt tokens for TPM admission budgeting.

    The divisor is calibrated against provider-reported Z/CS prompt measurements
    from S109/S114. The separate safety margin absorbs modest tokenizer overhead
    without rejecting the observed orchestrated CS shape.
    """
    total_chars = 0
    message_count = 0
    for message in messages:
        message_count += 1
        if isinstance(message, dict):
            total_chars += len(str(message.get("role", "")))
            total_chars += len(_groq_message_content_text(message.get("content", "")))
        else:
            total_chars += len(str(message))

    if message_count == 0:
        return 0
    return (
        ((total_chars + GROQ_TOKEN_ESTIMATE_CHARS_PER_TOKEN - 1) // GROQ_TOKEN_ESTIMATE_CHARS_PER_TOKEN)
        + (message_count * GROQ_MESSAGE_TOKEN_OVERHEAD)
        + 1
    )


# D-115-1/2: character heuristics cannot be made safe across scripts. An external
# reviewer showed a 20,000-character CJK aggregate estimating only ~5,010 tokens
# and still admitting 2,478 completion tokens — CJK, dense JSON and code all
# tokenize far denser than Latin prose, and no divisor fixes every script at once.
# The provider's own accounting is the only authoritative source, so a structured
# rejection is treated as MEASUREMENT rather than as failure: Groq states both the
# limit and what it computed for the request, which is enough to derive the true
# prompt cost and retry once with a budget grounded in provider numbers.
#
# Deliberately NOT retried (D-115-2): generic body-size 413s, and any error whose
# structure we cannot parse. Retrying an error we do not understand is how a
# single rejection becomes a loop.
_GROQ_REQUESTED_RE = re.compile(r"Requested\s+(\d+)", re.IGNORECASE)
_GROQ_LIMIT_RE = re.compile(r"Limit\s+(\d+)", re.IGNORECASE)
_GROQ_TPM_ERROR_CODE = "rate_limit_exceeded"


def _groq_error_field(error: Any, *names: str) -> Optional[str]:
    """Pull a field from a provider error body regardless of SDK wrapping."""
    body = getattr(error, "body", None)
    candidates = []
    if isinstance(body, dict):
        candidates.append(body.get("error") if isinstance(body.get("error"), dict) else body)
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for name in names:
            value = candidate.get(name)
            if value is not None:
                return str(value)
    return None


def _groq_provider_informed_budget(error: Any, sent_max_tokens: int) -> Optional[int]:
    """Derive a safe completion budget from a STRUCTURED Groq TPM rejection.

    Only the live-observed HTTP 413 admission shape is recoverable. HTTP 429 is
    rolling-window rate-limit exhaustion and must be left to the caller's
    throttling/backoff layer rather than retried immediately. Returns None when
    the status or body is not the structured admission shape, when the numbers
    cannot be parsed, or when no useful output would fit — every one of which
    must fail rather than retry.
    """
    response = getattr(error, "response", None)
    status_code = getattr(error, "status_code", None)
    if status_code is None:
        status_code = getattr(response, "status_code", None)
    try:
        status_code = int(status_code)
    except (TypeError, ValueError):
        return None
    if status_code != 413:
        return None                      # 429/backoff and all other statuses: do not retry

    if _groq_error_field(error, "code") != _GROQ_TPM_ERROR_CODE:
        return None                      # generic 413 / unrelated error: do not retry

    message = _groq_error_field(error, "message") or ""
    requested_match = _GROQ_REQUESTED_RE.search(message)
    if not requested_match:
        return None                      # malformed/ambiguous: do not retry

    # Prefer the authoritative header; fall back to the limit stated in the message.
    limit = None
    headers = getattr(response, "headers", None)
    if headers is not None:
        header_limit = headers.get("x-ratelimit-limit-tokens")
        if header_limit and str(header_limit).isdigit():
            limit = int(header_limit)
    if limit is None:
        limit_match = _GROQ_LIMIT_RE.search(message)
        if not limit_match:
            return None                  # no trustworthy limit: fail, do not guess
        limit = int(limit_match.group(1))

    # The provider computed `requested = prompt_cost + max_tokens` (verified
    # S109: 3000+6000 -> 9072, 8500+512 -> 9084), so this inverts to the REAL
    # prompt cost — the number the character heuristic got wrong.
    actual_prompt_tokens = int(requested_match.group(1)) - sent_max_tokens
    if actual_prompt_tokens <= 0:
        return None

    safe_budget = limit - actual_prompt_tokens - GROQ_TPM_SAFETY_MARGIN
    if safe_budget < GROQ_MIN_COMPLETION_TOKENS:
        return None                      # cannot carry useful output: fail closed
    return min(safe_budget, GROQ_8K_TPM_COMPLETION_CAP)


def _groq_8k_tpm_max_tokens(model: str, messages: List[Dict[str, Any]], requested: int) -> int:
    """Return the completion reservation that can fit under Groq 8k TPM admission."""
    if model not in GROQ_8K_TPM_MODELS:
        # D-115-3: unknown / BYOK models have no limit we can trust, so no clamp
        # is applied and no universal 8K ceiling is invented. If such a model is
        # rejected, the provider-informed retry supplies real numbers.
        return requested

    estimated_input_tokens = _estimate_groq_input_tokens(messages)
    available_completion = GROQ_8K_TPM_LIMIT - estimated_input_tokens - GROQ_TPM_SAFETY_MARGIN
    if available_completion < GROQ_MIN_COMPLETION_TOKENS:
        raise ValueError(
            f"Request not admissible on {model}: estimated input {estimated_input_tokens} tokens "
            f"leaves {available_completion} for completion under {GROQ_8K_TPM_LIMIT} TPM "
            f"after {GROQ_TPM_SAFETY_MARGIN} safety margin, below the "
            f"{GROQ_MIN_COMPLETION_TOKENS}-token minimum useful output. Reduce prompt size "
            "or use a higher-TPM provider/model."
        )

    return min(requested, GROQ_8K_TPM_COMPLETION_CAP, available_completion)

PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
    "gemini": {
        "name": "Google Gemini",
        # v0.5.51: default -> gemini-3.5-flash-lite (GA, free-tier-verified; see
        # constant note). gemini-3.6-flash added (GA frontier flash). 2.5-flash
        # retained for continuity; 3.5-flash is a THINKING model — callers with
        # tight output budgets should prefer the default. All live-verified 2026-07-22.
        "default_model": PROVIDER_DEFAULT_GEMINI_MODEL,
        "models": [PROVIDER_DEFAULT_GEMINI_MODEL, "gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash", "gemini-3.1-pro-preview"],
        "api_key_env": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "free_tier": True,
        "rate_limit": 15,  # requests per minute on free tier
        "models_verified_at": "2026-07-22",
    },
    "openai": {
        "name": "OpenAI",
        "default_model": PROVIDER_DEFAULT_OPENAI_MODEL,
        "models": [PROVIDER_DEFAULT_OPENAI_MODEL, "gpt-5.4", "gpt-5.4-mini", "gpt-4.1", "gpt-4.1-mini"],
        "api_key_env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "free_tier": False,
        "models_verified_at": "2026-06-22",
    },
    "anthropic": {
        "name": "Anthropic Claude",
        # Claude 5 family live-verified available on a real key 2026-07-29
        # (RNA S106). These are extended-thinking models — see
        # `_thinking_aware_max_tokens`. Default stays on the 4.x line until a
        # deliberate default change is reviewed; the 5 IDs are opt-in via BYOK.
        "default_model": os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        "models": ["claude-opus-5", "claude-sonnet-5", "claude-fable-5",
                   "claude-sonnet-4-6", "claude-opus-4-8", "claude-haiku-4-5-20251001"],
        "api_key_env": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1",
        "free_tier": False,
        "models_verified_at": "2026-07-29",
    },
    "groq": {
        "name": "Groq",
        "default_model": PROVIDER_DEFAULT_GROQ_MODEL,
        # v0.5.49 (D-65-6/7): gpt-oss-120b default (open-source flagship) + qwen3.6-27b fast
        # (replaces deprecated llama-3.1-8b-instant). Both live-verified 2026-07-16.
        # D-115-5: meta-llama/llama-4-scout-17b-16e-instruct REMOVED — Groq
        # retired it 2026-07-17. Advertising a decommissioned model hands BYOK
        # callers a guaranteed 404 and is the same claim-vs-runtime drift class
        # as the stale discovery entries repaired in v0.5.55.
        "models": [
            PROVIDER_DEFAULT_GROQ_MODEL,
            "qwen/qwen3.6-27b",
            # qwen3.8-27b: successor fast option, Groq Preview tier
            # (131k context / 16,384 max completion per Groq model docs,
            # verified 2026-08-29). 3.6 stays listed while Groq serves it.
            "qwen/qwen3.8-27b",
        ],
        "api_key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "free_tier": True,
        "rate_limit": 30,
        "models_verified_at": "2026-08-29",
    },
    "cerebras": {
        "name": "Cerebras",
        "default_model": PROVIDER_DEFAULT_CEREBRAS_MODEL,
        "models": [
            PROVIDER_DEFAULT_CEREBRAS_MODEL,
            "zai-glm-4.7",
            "gemma-4-31b",
        ],
        "api_key_env": "CEREBRAS_API_KEY",
        "base_url": "https://api.cerebras.ai/v1",
        "free_tier": True,
        "rate_limit": 60,  # free-tier limits vary by account; 20x GPU throughput
        "models_verified_at": "2026-08-06",
    },
    "mistral": {
        "name": "Mistral AI",
        # v0.5.53 model currency: mistral-medium-3.5 is the successor (live-verified
        # 2026-07-22 on Alton's key, chat probe OK); medium-3 retained for continuity.
        # EU-sovereignty lane: Mistral = jurisdictional diversity for the Layer-2 thesis.
        "default_model": "mistral-medium-3.5",
        "models": ["mistral-medium-3.5", "mistral-medium-3", "mistral-small-latest", "mistral-large-latest"],
        "api_key_env": "MISTRAL_API_KEY",
        "base_url": "https://api.mistral.ai/v1",
        "free_tier": False,
        "models_verified_at": "2026-07-22",
    },
    "ollama": {
        "name": "Ollama (Local)",
        "default_model": "llama3.2",
        "models": [],  # Dynamic based on local installation
        "api_key_env": None,  # No API key needed
        "base_url": "http://localhost:11434/v1",
        "free_tier": True,
    },
    "mock": {
        "name": "Mock Provider",
        "default_model": "mock-v1",
        "models": ["mock-v1"],
        "api_key_env": None,
        "base_url": None,
        "free_tier": True,
    },
}


def provider_catalog_currency_issues(
    as_of: Optional[date] = None,
) -> Dict[str, List[str]]:
    """Return bounded model-catalogue integrity/freshness findings.

    This is intentionally a local truth gate, not a claim that CI contacted
    six external APIs.  Live provider verification establishes each stamped
    date; this function prevents that evidence from silently aging forever and
    catches default/list drift or the reintroduction of known-retired IDs.
    Ollama is user-local and Mock is synthetic, so neither belongs to the six
    remote-provider currency contract.
    """
    today = as_of or date.today()
    issues: Dict[str, List[str]] = {}

    for provider_id in sorted(REMOTE_BYOK_PROVIDER_IDS):
        config = PROVIDER_CONFIGS.get(provider_id, {})
        provider_issues: List[str] = []
        models = list(config.get("models", []))
        default_model = config.get("default_model")

        if not default_model or default_model not in models:
            provider_issues.append("default_model_not_in_models")
        if len(models) != len(set(models)):
            provider_issues.append("duplicate_model_ids")

        retired = RETIRED_MODEL_IDS_BY_PROVIDER.get(provider_id, frozenset())
        if retired.intersection(models):
            provider_issues.append("known_retired_model_id")

        verified_raw = config.get("models_verified_at")
        try:
            verified_on = date.fromisoformat(str(verified_raw))
        except (TypeError, ValueError):
            provider_issues.append("missing_or_invalid_verification_date")
        else:
            age_days = (today - verified_on).days
            if age_days < 0:
                provider_issues.append("verification_date_in_future")
            elif age_days > MODEL_CURRENCY_MAX_AGE_DAYS:
                provider_issues.append("verification_stale")

        if provider_issues:
            issues[provider_id] = provider_issues

    return issues


@dataclass
class LLMResponse:
    """Structured response from LLM provider."""
    content: str
    model: str
    provider: str
    tokens_used: int
    latency_ms: float
    raw_response: Optional[Dict[str, Any]] = None


def get_provider_info(provider_name: str) -> Dict[str, Any]:
    """Get configuration info for a provider."""
    return PROVIDER_CONFIGS.get(provider_name.lower(), {})


def list_providers() -> List[Dict[str, Any]]:
    """List all available providers with their configurations."""
    return [
        {"id": name, **config}
        for name, config in PROVIDER_CONFIGS.items()
    ]


def list_free_tier_providers() -> List[str]:
    """List providers with free tier available."""
    return [
        name for name, config in PROVIDER_CONFIGS.items()
        if config.get("free_tier", False)
    ]


def _schema_expected_fields(output_schema: Dict[str, Any]) -> List[str]:
    """Required wire fields plus optional fields required for quality claims."""
    expected = list(output_schema.get("required", []))
    for field, prop in output_schema.get("properties", {}).items():
        if prop.get("quality_required") is True and field not in expected:
            expected.append(field)
    return expected


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers must implement the generate() method,
    which takes a prompt and returns a structured response.
    """
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The input prompt
            output_schema: Optional JSON schema for structured output
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            
        Returns:
            Parsed JSON response as a dictionary
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name being used."""
        pass


class OpenAIProvider(LLMProvider):
    """
    OpenAI GPT provider implementation.
    
    Supports GPT-4, GPT-4 Turbo, and GPT-3.5 Turbo models.
    Uses JSON mode for structured output when schema is provided.
    """
    
    def __init__(
        self,
        model: str = None,
        api_key: Optional[str] = None
    ):
        self.model = model or os.environ.get("OPENAI_MODEL", PROVIDER_DEFAULT_OPENAI_MODEL)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable.")
        
        # Import here to avoid requiring openai if not used
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using OpenAI API."""
        
        messages = [{"role": "user", "content": prompt}]
        
        # Use JSON mode if schema provided
        response_format = None
        if output_schema:
            response_format = {"type": "json_object"}
            # Add schema hint to prompt
            messages[0]["content"] += f"\n\nRespond with valid JSON matching this schema:\n{json.dumps(output_schema, indent=2)}"
        
        # gpt-5.x contract differs from gpt-4.x (verified live 2026-06-22): it requires
        # `max_completion_tokens` (rejects `max_tokens` with 400) and supports ONLY the default
        # temperature (a custom `temperature` 400s). Branch so gpt-4.x behavior is unchanged.
        is_gpt5 = self.model.startswith("gpt-5")
        create_kwargs = {
            "model": self.model,
            "messages": messages,
            "response_format": response_format,
        }
        if is_gpt5:
            create_kwargs["max_completion_tokens"] = max_tokens
        else:
            create_kwargs["max_tokens"] = max_tokens
            create_kwargs["temperature"] = temperature

        try:
            response = await self.client.chat.completions.create(**create_kwargs)

            content = response.choices[0].message.content
            
            # Extract token usage
            usage = {
                "input_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                "output_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }
            
            # Parse JSON response
            try:
                clean_content = strip_markdown_code_fences(content)
                parsed_content = json.loads(clean_content)
            except json.JSONDecodeError as e:
                _log_provider_exception("OpenAI", "JSON parse", e)
                logger.debug("Unparseable response length=%s", len(content or ""))
                parsed_content = {"raw_response": content, "parse_error": str(e)}

            # Return both content and usage
            return {
                "content": parsed_content,
                "usage": usage,
                "_inference_quality": "real"
            }

        except Exception as e:
            _log_provider_exception("OpenAI", "API request", e)
            raise
    
    def get_model_name(self) -> str:
        return f"openai/{self.model}"


# Models that emit extended-thinking blocks. Thinking tokens are drawn from the
# SAME `max_tokens` budget as the answer, so a budget sized for the answer alone
# silently truncates it. Measured on a real Z-agent assessment: 5,437 thinking
# tokens on one call — at our 8,192 agent budget the JSON answer was cut mid-
# object and surfaced as a parse failure, i.e. the model was blamed for our
# accounting. Same family as the Gemini 3.5-flash thinking-token trap.
_THINKING_MODEL_MARKERS = ("claude-opus-5", "claude-sonnet-5", "claude-fable-5")
_THINKING_TOKEN_ALLOWANCE = 8192
_ANTHROPIC_TRUNCATION_STOP_REASONS = frozenset({
    "max_tokens",
    "model_context_window_exceeded",
})
_GROQ_TRUNCATION_FINISH_REASONS = frozenset({"length"})


def _attach_completion_telemetry(
    exc: Exception,
    *,
    reservation: Optional[int],
    output_tokens: Optional[int] = None,
) -> None:
    """Attach bounded numeric request metadata without wrapping provider errors."""
    fields = {
        "_completion_token_reservation": reservation,
        "_provider_reported_output_tokens": output_tokens,
    }
    for name, value in fields.items():
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            continue
        try:
            setattr(exc, name, value)
        except Exception:
            # Some third-party exception classes disallow new attributes. The
            # original exception contract is more important than telemetry.
            pass


def _safe_usage_token_count(usage: Any, field: str) -> Optional[int]:
    """Read one non-negative SDK usage counter without affecting verdicts."""
    try:
        value = getattr(usage, field, None)
    except Exception:
        return None
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _thinking_aware_max_tokens(model: str, requested: int) -> int:
    """Add a thinking allowance so `requested` remains available for the ANSWER.

    Callers size `max_tokens` for the output they need. On extended-thinking
    models that number must additionally cover the model's scratchpad, so the
    allowance is added rather than the caller's budget being reinterpreted.
    """
    if any(marker in (model or "") for marker in _THINKING_MODEL_MARKERS):
        return requested + _THINKING_TOKEN_ALLOWANCE
    return requested


def _raise_if_anthropic_truncated(stop_reason: str | None, model: str) -> None:
    """Reject every Anthropic stop reason that denotes truncated output.

    `model_context_window_exceeded` was added as a distinct stop reason: the
    API may return it instead of `max_tokens` when the model reaches its
    context-window ceiling. Both mean the response is incomplete and therefore
    unsafe to parse as a complete structured answer.
    """
    if stop_reason in _ANTHROPIC_TRUNCATION_STOP_REASONS:
        raise ValueError(
            "Anthropic response truncated before completion "
            f"(model={model}, stop_reason={stop_reason}). The answer is "
            "incomplete; reduce the input or increase the available output "
            "budget rather than parsing a partial response."
        )


def _raise_if_groq_truncated(finish_reason: str | None, model: str) -> None:
    """Reject OpenAI-compatible Groq responses cut off at the token ceiling."""
    if finish_reason in _GROQ_TRUNCATION_FINISH_REASONS:
        exc = ValueError(
            "Groq response truncated before completion "
            f"(model={model}, finish_reason={finish_reason}). The answer is "
            "incomplete and must not be parsed as a complete Trinity stage."
        )
        # Privacy-safe semantic marker survives typed failover wrappers via
        # their cause chain; the public stage-error contract stays unchanged.
        exc._provider_output_truncated = True
        raise exc


def _first_text_block(blocks) -> str:
    """Return the first TEXT block's content from an Anthropic response.

    Anthropic responses are a LIST of typed content blocks, and `content[0]`
    is not guaranteed to be the text. Extended-thinking models (the Claude 5
    family) emit a `thinking` block first, so indexing position zero raised
    `'ThinkingBlock' object has no attribute 'text'` and BYOK failed for every
    such model — found by dogfooding a real Z-agent assessment on
    `claude-opus-5`.

    Selecting by TYPE rather than by POSITION is also forward-compatible: any
    future non-text block prepended to the list leaves this correct. Thinking
    content is deliberately discarded — it is the model's scratchpad, not its
    answer, and must never reach a caller as if it were the response.
    """
    # Exclude by KNOWN NON-TEXT type rather than admitting only type=="text".
    # Both directions matter: an allow-list rejects any block whose `type` is
    # absent or unrecognised (including legitimately-shaped test doubles and
    # future SDK block types that do carry text), while a deny-list keeps the
    # one property that must hold — reasoning scratchpads never surface as the
    # answer.
    _NON_TEXT = {"thinking", "redacted_thinking", "tool_use", "server_tool_use"}
    text_parts = []
    for b in blocks or []:
        if getattr(b, "type", None) in _NON_TEXT:
            continue
        value = getattr(b, "text", None)
        if isinstance(value, str) and value:
            text_parts.append(value)
    if text_parts:
        return "".join(text_parts)

    # Fail LOUD with a diagnosable message rather than returning empty content
    # that a downstream parser would report as a malformed model answer.
    seen = [getattr(b, "type", type(b).__name__) for b in (blocks or [])]
    raise ValueError(
        f"Anthropic response contained no text block (block types: {seen})"
    )


class AnthropicProvider(LLMProvider):
    """
    Anthropic Claude provider implementation.
    
    Supports Claude 3.5 Sonnet, Claude 3 Opus, and other Claude models.
    Uses prompt engineering for structured output.
    """
    
    def __init__(
        self,
        model: str = None,
        api_key: Optional[str] = None
    ):
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable.")
        
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using Anthropic API."""
        
        # Add JSON instruction if schema provided
        if output_schema:
            prompt += f"\n\nRespond with valid JSON only, matching this schema:\n{json.dumps(output_schema, indent=2)}\n\nJSON Response:"
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=_thinking_aware_max_tokens(self.model, max_tokens),
                messages=[{"role": "user", "content": prompt}]
            )

            # Fail LOUD on truncation. A response cut off at the token ceiling
            # yields malformed JSON that a downstream parser reports as "the
            # model returned bad output" — blaming the model for OUR budget.
            _raise_if_anthropic_truncated(
                getattr(response, "stop_reason", None),
                self.model,
            )

            content = _first_text_block(response.content)

            # Extract token usage
            usage = {
                "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else 0,
                "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else 0,
                "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if hasattr(response, 'usage') else 0
            }
            
            # Parse JSON response
            try:
                # Strip markdown fences before parsing (Claude often wraps JSON in ```json...```)
                clean_content = strip_markdown_code_fences(content)
                if clean_content.strip().startswith("{"):
                    parsed_content = json.loads(clean_content)
                else:
                    # Try to find JSON in response
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', clean_content)
                    if json_match:
                        parsed_content = json.loads(json_match.group())
                    else:
                        parsed_content = {"raw_response": content}
            except json.JSONDecodeError as e:
                _log_provider_exception("Anthropic", "JSON parse", e)
                parsed_content = {"raw_response": content, "parse_error": str(e)}
            
            # Return both content and usage
            return {
                "content": parsed_content,
                "usage": usage,
                "_inference_quality": "real"
            }

        except Exception as e:
            _log_provider_exception("Anthropic", "API request", e)
            raise
    
    def get_model_name(self) -> str:
        return f"anthropic/{self.model}"


class GeminiProvider(LLMProvider):
    """
    Google Gemini provider implementation (google.genai SDK — v0.5.47 R-S51-G).

    Supports Gemini 3.x (gemini-3.1-pro-preview, gemini-3.5-flash) and the 2.5 line.
    Uses prompt engineering for structured JSON output.

    Default: gemini-3.5-flash-lite (v0.5.51 - GA, FREE tier, direct responder;
    3.5-flash is a THINKING model, budget output accordingly). gemini-3.1-pro-preview
    available as a BYOK/frontier option. Note: Gemini 1.5 models retired in 2026.
    """

    def __init__(
        self,
        model: str = PROVIDER_DEFAULT_GEMINI_MODEL,
        api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Gemini API key not provided. Set GEMINI_API_KEY environment variable.")
        
        try:
            # v0.5.47 (R-S51-G): migrated from the deprecated `google.generativeai` to the
            # current `google.genai` SDK — required to serve Gemini 3.x (e.g. gemini-3.1-pro-preview),
            # which 404s on the old SDK. Client-based API; same usage_metadata field names.
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.genai = genai
        except ImportError:
            raise ImportError("google-genai package not installed. Run: pip install google-genai")
    
    def _build_response_schema(self, output_schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert a JSON Schema (from Pydantic) to Gemini's response_schema format.

        Gemini structured output requires a subset of OpenAPI 3.0 schema.
        We strip unsupported fields (title, default, etc.), resolve $ref/$defs
        references inline, and return a clean schema suitable for the API.
        """
        def _resolve_ref(ref_str: str) -> dict:
            """Resolve a $ref like '#/$defs/ReasoningStep' to the actual definition."""
            parts = ref_str.lstrip("#/").split("/")
            node = output_schema
            for part in parts:
                node = node.get(part, {})
            return node

        def _clean(node):
            if not isinstance(node, dict):
                return node
            # Resolve $ref first
            if "$ref" in node:
                resolved = _resolve_ref(node["$ref"])
                return _clean(resolved)
            cleaned = {}
            # Fields supported by Gemini response_schema
            for key in ("type", "properties", "required", "items", "enum", "description"):
                if key in node:
                    val = node[key]
                    if key == "properties" and isinstance(val, dict):
                        cleaned[key] = {k: _clean(v) for k, v in val.items()}
                    elif key == "items" and isinstance(val, dict):
                        cleaned[key] = _clean(val)
                    else:
                        cleaned[key] = val
            # Handle anyOf with null (Optional fields) — pick the non-null type
            if "anyOf" in node:
                non_null = [s for s in node["anyOf"] if s.get("type") != "null"]
                if non_null:
                    cleaned.update(_clean(non_null[0]))
                elif node["anyOf"]:
                    cleaned.update(_clean(node["anyOf"][0]))
            return cleaned

        try:
            return _clean(output_schema)
        except Exception as e:
            logger.warning(
                "Gemini response-schema construction failed exception_type=%s",
                type(e).__name__,
            )
            return None

    @staticmethod
    def _extract_best_json(text: str, expected_fields: list) -> Optional[dict]:
        """Extract the JSON object that best matches expected schema fields.

        Uses json.JSONDecoder.raw_decode() to find all valid JSON objects
        in the text (handles nested braces in strings correctly), scores
        each by field overlap, and returns the best match.
        """
        decoder = json.JSONDecoder()
        candidates = []
        idx = 0
        while idx < len(text):
            # Find next '{' character
            brace_pos = text.find('{', idx)
            if brace_pos == -1:
                break
            try:
                obj, end_idx = decoder.raw_decode(text, brace_pos)
                if isinstance(obj, dict):
                    score = sum(1 for f in expected_fields if f in obj)
                    candidates.append((score, obj))
                idx = end_idx
            except json.JSONDecodeError:
                idx = brace_pos + 1

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_obj = candidates[0]
            logger.info(
                f"extract_best_json: {len(candidates)} candidates, "
                f"best has {best_score}/{len(expected_fields)} fields, "
                f"keys={list(best_obj.keys())[:5]}"
            )
            return best_obj if best_score > 0 else None
        logger.warning("extract_best_json: no JSON objects found in text")
        return None

    @staticmethod
    def _fill_schema_defaults(data: dict, output_schema: dict) -> dict:
        """Backward-compatible wrapper returning only the repaired data."""
        repaired, _ = GeminiProvider._fill_schema_defaults_with_repairs(
            data, output_schema
        )
        return repaired

    @staticmethod
    def _fill_schema_defaults_with_repairs(
        data: dict, output_schema: dict
    ) -> Tuple[dict, List[str]]:
        """Fill missing/null required fields and explicitly report repairs.

        When Gemini returns partial JSON (e.g. reasoning steps but no scores),
        this fills gaps so Pydantic validation succeeds. The _inference_quality
        marker tells downstream code the result was partially synthesized.

        A key-set difference cannot detect a present-but-null repair, so callers
        must use the returned field list rather than infer repairs from key growth.
        """
        required = output_schema.get("required", [])
        properties = output_schema.get("properties", {})
        repaired_fields = []

        for field in required:
            if field in data and data[field] is not None:
                continue
            prop = properties.get(field, {})
            field_type = prop.get("type", "")

            # Resolve anyOf (Optional fields)
            if "anyOf" in prop:
                non_null = [s for s in prop["anyOf"] if s.get("type") != "null"]
                if non_null:
                    field_type = non_null[0].get("type", "string")

            if field_type == "number" or field_type == "integer":
                # Score fields (0-10) get neutral 5.0, confidence (0-1) gets 0.5
                # JSON Schema uses "minimum"/"maximum" (Pydantic ge/le map to these)
                lo = prop.get("minimum", prop.get("exclusiveMinimum", 0))
                hi = prop.get("maximum", prop.get("exclusiveMaximum", 10))
                if hi <= 1.0:
                    data[field] = 0.5
                else:
                    data[field] = round((lo + hi) / 2, 1)
            elif field_type == "boolean":
                # Conservative default
                data[field] = False
            elif field_type == "array":
                if field == "reasoning_steps":
                    data[field] = [{
                        "step_number": 1,
                        "thought": "Analysis was partially completed by LLM.",
                        "confidence": 0.5
                    }]
                else:
                    data[field] = ["Inference incomplete — partial analysis"]
            elif field_type == "string":
                data[field] = "Partial inference — LLM did not return this field."
            else:
                data[field] = "Partial inference"

            repaired_fields.append(field)

        return data, repaired_fields

    @staticmethod
    def _quality_incomplete_fields(data: dict, output_schema: dict) -> List[str]:
        """Return promised quality fields that are missing or null.

        These fields stay optional at the Pydantic compatibility layer, but the
        hosted product promises them as evidence. They are never populated with
        fabricated detail; their absence downgrades inference quality instead.
        """
        properties = output_schema.get("properties", {})
        return sorted(
            field
            for field, prop in properties.items()
            if prop.get("quality_required") is True
            and (field not in data or data[field] is None)
        )

    @staticmethod
    def _merge_json_objects(text: str, expected_fields: list) -> Optional[dict]:
        """Merge all JSON objects from text into one composite dict.

        When Gemini returns individual reasoning steps as separate objects,
        this collects all objects and merges their keys. Objects that look
        like reasoning steps (have step_number) are collected into a
        reasoning_steps array.
        """
        decoder = json.JSONDecoder()
        all_objects = []
        idx = 0
        while idx < len(text):
            brace_pos = text.find('{', idx)
            if brace_pos == -1:
                break
            try:
                obj, end_idx = decoder.raw_decode(text, brace_pos)
                if isinstance(obj, dict):
                    all_objects.append(obj)
                idx = end_idx
            except json.JSONDecodeError:
                idx = brace_pos + 1

        if not all_objects:
            return None

        # Separate reasoning steps from model-level fields
        reasoning_steps = []
        merged = {}
        for obj in all_objects:
            if "step_number" in obj or ("thought" in obj and "step_number" in obj):
                reasoning_steps.append(obj)
            else:
                # Merge model-level fields (later objects override earlier)
                merged.update(obj)

        if reasoning_steps and "reasoning_steps" in expected_fields:
            merged["reasoning_steps"] = reasoning_steps

        overlap = sum(1 for f in expected_fields if f in merged)
        logger.info(f"merge_json_objects: {len(all_objects)} objects → {overlap}/{len(expected_fields)} fields")
        return merged if overlap >= 2 else None

    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using Gemini API with structured output when schema provided."""

        try:
            # Build generation config
            gen_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            # v0.4.3.1: Stronger prompt guidance for structured output.
            # Gemini's native structured output mode was tested but produces
            # single sub-objects. Instead we guide via prompt + extract best JSON.
            if output_schema:
                required = _schema_expected_fields(output_schema)
                properties = output_schema.get("properties", {})
                # Build compact schema hint showing field names and types
                field_hints = []
                for field_name in required:
                    prop = properties.get(field_name, {})
                    field_type = prop.get("type", "any")
                    if "items" in prop:
                        field_type = f"array of {prop['items'].get('type', 'objects')}"
                    elif "$ref" in prop or "allOf" in prop:
                        field_type = "object"
                    field_hints.append(f'  "{field_name}": <{field_type}>')
                schema_example = "{\n" + ",\n".join(field_hints) + "\n}"
                prompt += (
                    f"\n\nIMPORTANT: You MUST respond with EXACTLY ONE JSON object. "
                    f"The JSON object must have ALL of these top-level fields:\n"
                    f"{schema_example}\n\n"
                    f"Do NOT output multiple separate JSON objects. "
                    f"Do NOT output reasoning steps as individual JSON objects. "
                    f"Include reasoning_steps as an ARRAY inside the single JSON object.\n"
                    f"Respond ONLY with the JSON object, no other text.\n\nJSON:"
                )

            # Generate response (google.genai client API — v0.5.47 R-S51-G).
            # WP-B B-90-6: awaited via the SDK's async client (`client.aio`)
            # so `asyncio.wait_for` can actually bound the attempt — the old
            # sync call inside this async method blocked the event loop and
            # made the per-attempt timeout unenforceable for Gemini.
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=gen_config,
            )

            content = response.text

            # Extract token usage
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
                "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0
            }

            # Parse JSON response
            expected_fields = []
            if output_schema:
                expected_fields = _schema_expected_fields(output_schema)
            elif output_schema and "properties" in output_schema:
                expected_fields = list(output_schema["properties"].keys())

            clean_content = strip_markdown_code_fences(content)
            logger.debug("Gemini cleaned response length=%s", len(clean_content))

            # v0.4.3.1 C-S-P Compression: Use robust best-match extraction.
            # raw_decode() finds all valid JSON objects and scores by field overlap
            # to pick the full model object, not a sub-object (reasoning step).
            # v0.4.3.1g: Fill missing required fields with schema defaults so
            # Pydantic validation ALWAYS succeeds — _inference_quality marks degradation.
            inference_quality = "real"
            repaired_fields = []
            quality_incomplete_fields = []
            if expected_fields:
                parsed_content = self._extract_best_json(clean_content, expected_fields)
                if parsed_content is not None:
                    overlap = sum(1 for f in expected_fields if f in parsed_content)
                    if overlap < len(expected_fields) * 0.5:
                        # Low overlap — best object is likely a reasoning step, not the full model.
                        # Try to merge ALL found objects into one composite.
                        logger.warning(f"Low field overlap: {overlap}/{len(expected_fields)}, attempting merge")
                        merged = self._merge_json_objects(clean_content, expected_fields)
                        if merged:
                            merged_overlap = sum(1 for f in expected_fields if f in merged)
                            if merged_overlap > overlap:
                                parsed_content = merged
                                overlap = merged_overlap
                        inference_quality = "partial" if overlap >= 2 else "fallback"
                else:
                    logger.warning(
                        "Best-match extraction found nothing; content_len=%s",
                        len(clean_content),
                    )
                    inference_quality = "fallback"
                    try:
                        parsed_content = json.loads(clean_content)
                    except json.JSONDecodeError:
                        parsed_content = {}

                # Fill any missing required fields with schema-aware defaults.
                # This ensures Pydantic validation succeeds even when Gemini
                # returns individual reasoning steps instead of a complete model.
                if output_schema and isinstance(parsed_content, dict):
                    parsed_content, repaired_fields = (
                        self._fill_schema_defaults_with_repairs(
                            parsed_content, output_schema
                        )
                    )
                    if repaired_fields:
                        logger.warning(
                            "Filled %s missing/null required fields: %s",
                            len(repaired_fields),
                            repaired_fields,
                        )
                        if inference_quality == "real":
                            inference_quality = "partial"
                    quality_incomplete_fields = self._quality_incomplete_fields(
                        parsed_content, output_schema
                    )
                    if quality_incomplete_fields:
                        logger.warning(
                            "Missing/null quality fields: %s",
                            quality_incomplete_fields,
                        )
                        if inference_quality == "real":
                            inference_quality = "partial"
            else:
                # No schema — simple parse (backward compatible)
                try:
                    if clean_content.strip().startswith("{"):
                        parsed_content = json.loads(clean_content)
                    else:
                        import re
                        json_match = re.search(r'\{[\s\S]*\}', clean_content)
                        if json_match:
                            parsed_content = json.loads(json_match.group())
                        else:
                            parsed_content = {"raw_response": content}
                            inference_quality = "fallback"
                except json.JSONDecodeError as e:
                    _log_provider_exception("Gemini", "JSON parse", e)
                    parsed_content = {"raw_response": content, "parse_error": str(e)}
                    inference_quality = "fallback"

            # Return content, usage, and inference quality marker
            return {
                "content": parsed_content,
                "usage": usage,
                "_inference_quality": inference_quality,
                "_schema_repaired_fields": repaired_fields,
                "_schema_incomplete_fields": quality_incomplete_fields,
            }

        except Exception as e:
            _log_provider_exception("Gemini", "API request", e)
            raise

    def get_model_name(self) -> str:
        return f"gemini/{self.model}"


class GroqProvider(LLMProvider):
    """
    Groq provider implementation.

    v0.4.4: Primary provider for Z Agent (ethics/reasoning).
    Supports Llama 3.3, Mixtral, and other models.
    FREE tier available with generous rate limits!

    Uses the same robust JSON extraction pipeline as GeminiProvider:
    - strip_markdown_code_fences()
    - _extract_best_json() with raw_decode()
    - _merge_json_objects() for scattered reasoning steps
    - _fill_schema_defaults() for missing required fields
    - _inference_quality markers (real/partial/fallback)
    """

    def __init__(
        self,
        model: str = PROVIDER_DEFAULT_GROQ_MODEL,
        api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError("Groq API key not provided. Set GROQ_API_KEY environment variable.")

        try:
            from groq import AsyncGroq
            self.client = AsyncGroq(api_key=self.api_key)
        except ImportError:
            raise ImportError("groq package not installed. Run: pip install groq")

    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using Groq API with robust JSON extraction."""

        messages = [{"role": "user", "content": prompt}]

        # v0.4.4: Same structured output guidance as GeminiProvider
        if output_schema:
            required = _schema_expected_fields(output_schema)
            properties = output_schema.get("properties", {})
            field_hints = []
            for field_name in required:
                prop = properties.get(field_name, {})
                field_type = prop.get("type", "any")
                if "items" in prop:
                    field_type = f"array of {prop['items'].get('type', 'objects')}"
                elif "$ref" in prop or "allOf" in prop:
                    field_type = "object"
                field_hints.append(f'  "{field_name}": <{field_type}>')
            schema_example = "{\n" + ",\n".join(field_hints) + "\n}"
            messages[0]["content"] += (
                f"\n\nIMPORTANT: You MUST respond with EXACTLY ONE JSON object. "
                f"The JSON object must have ALL of these top-level fields:\n"
                f"{schema_example}\n\n"
                f"Do NOT output multiple separate JSON objects. "
                f"Do NOT output reasoning steps as individual JSON objects. "
                f"Include reasoning_steps as an ARRAY inside the single JSON object.\n"
                f"Respond ONLY with the JSON object, no other text.\n\nJSON:"
            )

        # v0.5.55: Groq admission is input + completion, not completion alone.
        max_tokens = _groq_8k_tpm_max_tokens(self.model, messages, max_tokens)

        reported_output_tokens = None
        try:
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            except Exception as admission_error:
                # D-115-1: exactly ONE retry, and only when the provider supplied
                # real numbers. `_groq_provider_informed_budget` returns None for
                # generic body-size 413s, unparseable errors, missing limits, or
                # budgets below the useful-output floor — all of which re-raise
                # unchanged. No second retry is possible by construction: the
                # recovery path calls `create` directly rather than recursing.
                retry_budget = _groq_provider_informed_budget(admission_error, max_tokens)
                if retry_budget is None:
                    raise
                logger.warning(
                    "Groq admission rejected on %s; the local character estimate "
                    "under-counted this prompt. Retrying ONCE with a "
                    "provider-derived budget of %d completion tokens (was %d).",
                    self.model, retry_budget, max_tokens)
                max_tokens = retry_budget
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

            choice = response.choices[0]
            finish_reason = getattr(choice, "finish_reason", None)

            # Usage is optional provider metadata. A missing/partial usage
            # object must never outrank an authoritative truncation verdict.
            try:
                response_usage = getattr(response, "usage", None)
            except Exception:
                response_usage = None
            input_tokens = _safe_usage_token_count(
                response_usage, "prompt_tokens"
            )
            reported_output_tokens = _safe_usage_token_count(
                response_usage, "completion_tokens"
            )
            total_tokens = _safe_usage_token_count(
                response_usage, "total_tokens"
            )
            usage = {
                "input_tokens": input_tokens if input_tokens is not None else 0,
                "output_tokens": (
                    reported_output_tokens
                    if reported_output_tokens is not None
                    else 0
                ),
                "total_tokens": total_tokens if total_tokens is not None else 0,
            }
            _raise_if_groq_truncated(finish_reason, self.model)
            content = choice.message.content

            # v0.4.4: Same robust extraction pipeline as GeminiProvider
            expected_fields = []
            if output_schema:
                expected_fields = _schema_expected_fields(output_schema)
            elif output_schema and "properties" in output_schema:
                expected_fields = list(output_schema["properties"].keys())

            clean_content = strip_markdown_code_fences(content)
            logger.debug("Groq cleaned response length=%s", len(clean_content))

            inference_quality = "real"
            repaired_fields = []
            quality_incomplete_fields = []
            if expected_fields:
                parsed_content = GeminiProvider._extract_best_json(clean_content, expected_fields)
                if parsed_content is not None:
                    overlap = sum(1 for f in expected_fields if f in parsed_content)
                    if overlap < len(expected_fields) * 0.5:
                        logger.warning(f"Groq: Low field overlap: {overlap}/{len(expected_fields)}, attempting merge")
                        merged = GeminiProvider._merge_json_objects(clean_content, expected_fields)
                        if merged:
                            merged_overlap = sum(1 for f in expected_fields if f in merged)
                            if merged_overlap > overlap:
                                parsed_content = merged
                                overlap = merged_overlap
                        inference_quality = "partial" if overlap >= 2 else "fallback"
                else:
                    inference_quality = "fallback"
                    try:
                        parsed_content = json.loads(clean_content)
                    except json.JSONDecodeError:
                        parsed_content = {}

                # Fill missing required fields with schema-aware defaults
                if output_schema and isinstance(parsed_content, dict):
                    parsed_content, repaired_fields = (
                        GeminiProvider._fill_schema_defaults_with_repairs(
                            parsed_content, output_schema
                        )
                    )
                    if repaired_fields:
                        logger.warning(
                            "Groq: Filled %s missing/null required fields: %s",
                            len(repaired_fields),
                            repaired_fields,
                        )
                        if inference_quality == "real":
                            inference_quality = "partial"
                    quality_incomplete_fields = (
                        GeminiProvider._quality_incomplete_fields(
                            parsed_content, output_schema
                        )
                    )
                    if quality_incomplete_fields:
                        logger.warning(
                            "Groq: Missing/null quality fields: %s",
                            quality_incomplete_fields,
                        )
                        if inference_quality == "real":
                            inference_quality = "partial"
            else:
                try:
                    if clean_content.strip().startswith("{"):
                        parsed_content = json.loads(clean_content)
                    else:
                        import re
                        json_match = re.search(r'\{[\s\S]*\}', clean_content)
                        if json_match:
                            parsed_content = json.loads(json_match.group())
                        else:
                            parsed_content = {"raw_response": content}
                            inference_quality = "fallback"
                except json.JSONDecodeError as e:
                    _log_provider_exception("Groq", "JSON parse", e)
                    parsed_content = {"raw_response": content, "parse_error": str(e)}
                    inference_quality = "fallback"

            return {
                "content": parsed_content,
                "usage": usage,
                "_inference_quality": inference_quality,
                "_schema_repaired_fields": repaired_fields,
                "_schema_incomplete_fields": quality_incomplete_fields,
                "_completion_token_reservation": max_tokens,
            }

        except Exception as e:
            _attach_completion_telemetry(
                e,
                reservation=max_tokens,
                output_tokens=reported_output_tokens,
            )
            _log_provider_exception("Groq", "API request", e)
            raise

    def get_model_name(self) -> str:
        return f"groq/{self.model}"


class CerebrasProvider(LLMProvider):
    """
    Cerebras provider implementation.

    v0.4.0: OpenAI-compatible API on Cerebras wafer-scale hardware.
    Free tier available (limits vary by account). 20x GPU throughput vs cloud.
    Key prefix: csk_

    Follows the same robust JSON extraction pipeline as GroqProvider.
    """

    def __init__(
        self,
        model: str = PROVIDER_DEFAULT_CEREBRAS_MODEL,
        api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = api_key or os.getenv("CEREBRAS_API_KEY")

        if not self.api_key:
            raise ValueError("Cerebras API key not provided. Set CEREBRAS_API_KEY environment variable.")

        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.cerebras.ai/v1"
            )
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")

    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using Cerebras API with robust JSON extraction."""

        messages = [{"role": "user", "content": prompt}]

        if output_schema:
            required = _schema_expected_fields(output_schema)
            properties = output_schema.get("properties", {})
            field_hints = []
            for field_name in required:
                prop = properties.get(field_name, {})
                field_type = prop.get("type", "any")
                if "items" in prop:
                    field_type = f"array of {prop['items'].get('type', 'objects')}"
                elif "$ref" in prop or "allOf" in prop:
                    field_type = "object"
                field_hints.append(f'  "{field_name}": <{field_type}>')
            schema_example = "{\n" + ",\n".join(field_hints) + "\n}"
            messages[0]["content"] += (
                f"\n\nIMPORTANT: You MUST respond with EXACTLY ONE JSON object. "
                f"The JSON object must have ALL of these top-level fields:\n"
                f"{schema_example}\n\n"
                f"Do NOT output multiple separate JSON objects. "
                f"Do NOT output reasoning steps as individual JSON objects. "
                f"Include reasoning_steps as an ARRAY inside the single JSON object.\n"
                f"Respond ONLY with the JSON object, no other text.\n\nJSON:"
            )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content

            usage = {
                "input_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                "output_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }

            expected_fields = []
            if output_schema:
                expected_fields = _schema_expected_fields(output_schema)
            elif output_schema and "properties" in output_schema:
                expected_fields = list(output_schema["properties"].keys())

            clean_content = strip_markdown_code_fences(content)
            logger.debug("Cerebras cleaned response length=%s", len(clean_content))

            inference_quality = "real"
            repaired_fields = []
            quality_incomplete_fields = []
            if expected_fields:
                parsed_content = GeminiProvider._extract_best_json(clean_content, expected_fields)
                if parsed_content is not None:
                    overlap = sum(1 for f in expected_fields if f in parsed_content)
                    if overlap < len(expected_fields) * 0.5:
                        logger.warning(f"Cerebras: Low field overlap: {overlap}/{len(expected_fields)}, attempting merge")
                        merged = GeminiProvider._merge_json_objects(clean_content, expected_fields)
                        if merged:
                            merged_overlap = sum(1 for f in expected_fields if f in merged)
                            if merged_overlap > overlap:
                                parsed_content = merged
                                overlap = merged_overlap
                        inference_quality = "partial" if overlap >= 2 else "fallback"
                else:
                    inference_quality = "fallback"
                    try:
                        parsed_content = json.loads(clean_content)
                    except json.JSONDecodeError:
                        parsed_content = {}

                if output_schema and isinstance(parsed_content, dict):
                    parsed_content, repaired_fields = (
                        GeminiProvider._fill_schema_defaults_with_repairs(
                            parsed_content, output_schema
                        )
                    )
                    if repaired_fields:
                        logger.warning(
                            "Cerebras: Filled %s missing/null required fields: %s",
                            len(repaired_fields),
                            repaired_fields,
                        )
                        if inference_quality == "real":
                            inference_quality = "partial"
                    quality_incomplete_fields = (
                        GeminiProvider._quality_incomplete_fields(
                            parsed_content, output_schema
                        )
                    )
                    if quality_incomplete_fields:
                        logger.warning(
                            "Cerebras: Missing/null quality fields: %s",
                            quality_incomplete_fields,
                        )
                        if inference_quality == "real":
                            inference_quality = "partial"
            else:
                try:
                    if clean_content.strip().startswith("{"):
                        parsed_content = json.loads(clean_content)
                    else:
                        import re
                        json_match = re.search(r'\{[\s\S]*\}', clean_content)
                        if json_match:
                            parsed_content = json.loads(json_match.group())
                        else:
                            parsed_content = {"raw_response": content}
                            inference_quality = "fallback"
                except json.JSONDecodeError as e:
                    _log_provider_exception("Cerebras", "JSON parse", e)
                    parsed_content = {"raw_response": content, "parse_error": str(e)}
                    inference_quality = "fallback"

            return {
                "content": parsed_content,
                "usage": usage,
                "_inference_quality": inference_quality,
                "_schema_repaired_fields": repaired_fields,
                "_schema_incomplete_fields": quality_incomplete_fields,
            }

        except Exception as e:
            _log_provider_exception("Cerebras", "API request", e)
            raise

    def get_model_name(self) -> str:
        return f"cerebras/{self.model}"


class MistralProvider(LLMProvider):
    """
    Mistral AI provider implementation.

    Supports Mistral Small, Large, and other models.
    """

    def __init__(
        self,
        model: str = "mistral-small-latest",
        api_key: Optional[str] = None
    ):
        self.model = model
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")

        if not self.api_key:
            raise ValueError("Mistral API key not provided. Set MISTRAL_API_KEY environment variable.")

        try:
            from mistralai.client import Mistral
            self.client = Mistral(api_key=self.api_key)
        except ImportError:
            raise ImportError("mistralai package not installed. Run: pip install mistralai")

    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using Mistral API."""

        messages = [{"role": "user", "content": prompt}]

        # Add JSON instruction if schema provided
        if output_schema:
            messages[0]["content"] += f"\n\nRespond with valid JSON only, matching this schema:\n{json.dumps(output_schema, indent=2)}\n\nJSON Response:"

        try:
            response = await self.client.chat.complete_async(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content

            # Extract token usage
            usage = {
                "input_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
                "output_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0,
                "total_tokens": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }

            # Parse JSON response
            try:
                clean_content = strip_markdown_code_fences(content)
                if clean_content.strip().startswith("{"):
                    parsed_content = json.loads(clean_content)
                else:
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', clean_content)
                    if json_match:
                        parsed_content = json.loads(json_match.group())
                    else:
                        parsed_content = {"raw_response": content}
            except json.JSONDecodeError as e:
                _log_provider_exception("Mistral", "JSON parse", e)
                parsed_content = {"raw_response": content, "parse_error": str(e)}

            return {
                "content": parsed_content,
                "usage": usage,
                "_inference_quality": "real"
            }

        except Exception as e:
            _log_provider_exception("Mistral", "API request", e)
            raise

    def get_model_name(self) -> str:
        return f"mistral/{self.model}"


class OllamaProvider(LLMProvider):
    """
    Ollama provider implementation for local LLM inference.

    Supports any model installed locally via Ollama.
    FREE - runs entirely on your local machine.

    Requires Ollama to be running: https://ollama.ai
    """

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434"
    ):
        self.model = model
        self.base_url = base_url

    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Generate response using Ollama local API."""
        import httpx

        # Add JSON instruction if schema provided
        if output_schema:
            prompt += f"\n\nRespond with valid JSON only, matching this schema:\n{json.dumps(output_schema, indent=2)}\n\nJSON Response:"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()

            content = data.get("response", "")

            # Extract token usage (Ollama provides eval_count and prompt_eval_count)
            usage = {
                "input_tokens": data.get("prompt_eval_count", 0),
                "output_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
            }

            # Parse JSON response
            try:
                clean_content = strip_markdown_code_fences(content)
                if clean_content.strip().startswith("{"):
                    parsed_content = json.loads(clean_content)
                else:
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', clean_content)
                    if json_match:
                        parsed_content = json.loads(json_match.group())
                    else:
                        parsed_content = {"raw_response": content}
            except json.JSONDecodeError as e:
                _log_provider_exception("Ollama", "JSON parse", e)
                parsed_content = {"raw_response": content, "parse_error": str(e)}

            return {
                "content": parsed_content,
                "usage": usage,
                "_inference_quality": "real"
            }

        except Exception as e:
            _log_provider_exception("Ollama", "API request", e)
            raise

    def get_model_name(self) -> str:
        return f"ollama/{self.model}"


class MockProvider(LLMProvider):
    """
    Mock LLM provider for testing.
    
    Returns predefined responses without making API calls.
    Useful for development and testing.
    """
    
    def __init__(self, responses: Optional[Dict[str, Dict]] = None):
        self.responses = responses or {}
        self.call_count = 0
    
    async def generate(
        self,
        prompt: str,
        output_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Return mock response based on schema type."""
        self.call_count += 1

        # Check for predefined response
        for key, response in self.responses.items():
            if key in prompt:
                return response

        # Determine agent type from schema
        schema_title = output_schema.get("title", "") if output_schema else ""

        # Base reasoning steps for all agents
        reasoning_steps = [
            {
                "step_number": 1,
                "thought": "Analyzing the concept from my specialized perspective.",
                "evidence": "Based on the provided description and context.",
                "confidence": 0.85
            },
            {
                "step_number": 2,
                "thought": "Evaluating key factors and potential implications.",
                "evidence": "Industry best practices and standards.",
                "confidence": 0.80
            }
        ]

        # Build agent-specific mock content
        if "ZAgentAnalysis" in schema_title:
            mock_content = {
                "reasoning_steps": reasoning_steps,
                "ethics_score": 7.5,
                "z_protocol_compliance": True,
                "ethical_concerns": ["Data privacy considerations", "Potential for misuse"],
                "mitigation_measures": ["Implement access controls", "Add audit logging"],
                "recommendation": "Proceed with ethical safeguards in place.",
                "veto_triggered": False,
                "confidence": 0.82
            }
        elif "CSAgentAnalysis" in schema_title:
            mock_content = {
                "reasoning_steps": reasoning_steps,
                "security_score": 6.5,
                "vulnerabilities": ["Input validation needed", "Authentication gaps"],
                "attack_vectors": ["Injection attacks", "Unauthorized access"],
                "security_recommendations": ["Add input sanitization", "Implement MFA"],
                "socratic_questions": ["What happens if the API key is compromised?", "How do we handle malicious inputs?"],
                "recommendation": "Address security concerns before deployment.",
                "confidence": 0.78
            }
        else:
            mock_content = {
                "reasoning_steps": reasoning_steps,
                "innovation_score": 7.5,
                "strategic_value": 8.0,
                "opportunities": ["Market differentiation", "Efficiency gains", "Scalability potential"],
                "risks": ["Competition", "Technical complexity"],
                "recommendation": "Strong innovation potential with manageable risks.",
                "confidence": 0.85
            }

        return {
            "content": mock_content,
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "_inference_quality": "mock",
        }
    
    def get_model_name(self) -> str:
        return "mock/test-model"


# ============================================================================
# PROVIDER REGISTRY (BYOK v0.3.0)
# ============================================================================

_PROVIDERS: Dict[str, Type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "cerebras": CerebrasProvider,
    "mistral": MistralProvider,
    "ollama": OllamaProvider,
    "mock": MockProvider
}


def get_provider(
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> LLMProvider:
    """
    Get an LLM provider instance.

    BYOK v0.3.0: Supports multiple environment variable formats for compatibility.

    Args:
        provider_name: Provider name (gemini, openai, anthropic, groq, mistral, ollama, mock)
                      Defaults to LLM_PROVIDER env var or "mock"
        model: Model name to use
               Defaults to LLM_MODEL env var or provider default
        api_key: API key (optional, falls back to provider-specific env var)
        **kwargs: Additional arguments passed to provider constructor

    Returns:
        Configured LLMProvider instance

    Environment Variables:
        LLM_PROVIDER: Primary provider to use (gemini, openai, anthropic, groq, mistral, ollama, mock)
        LLM_MODEL: Override default model for the provider
        {PROVIDER}_API_KEY: API key for each provider (e.g., GEMINI_API_KEY)
    """
    # Get provider name from env if not specified (support both new and legacy env vars)
    if provider_name is None:
        provider_name = os.getenv("LLM_PROVIDER") or os.getenv("VERIFIMIND_LLM_PROVIDER", "mock")

    provider_name = provider_name.lower()

    if provider_name not in _PROVIDERS:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available providers: {list(_PROVIDERS.keys())}"
        )

    # Get API key from env if not specified
    if api_key is None:
        config = PROVIDER_CONFIGS.get(provider_name, {})
        api_key_env = config.get("api_key_env")
        if api_key_env:
            api_key = os.getenv(api_key_env)

    # Get model from env if not specified (support both new and legacy env vars)
    if model is None:
        model = os.getenv("LLM_MODEL") or os.getenv("VERIFIMIND_LLM_MODEL")

    # Build kwargs
    if model:
        kwargs["model"] = model
    if api_key and provider_name not in ["mock", "ollama"]:
        kwargs["api_key"] = api_key

    return _PROVIDERS[provider_name](**kwargs)


def _resolve_fallback_chain(exclude: str) -> List[str]:
    """Return ordered fallback providers, preferring free tiers over mock.

    v0.4.0: Cascades BYOK → Groq (if key set) → Cerebras (if key set) → mock
    rather than falling to mock immediately when the explicit fallback isn't set.
    """
    explicit = os.getenv("LLM_FALLBACK_PROVIDER")
    if explicit:
        return [explicit, "mock"]
    chain = []
    if os.getenv("GROQ_API_KEY") and exclude != "groq":
        chain.append("groq")
    if os.getenv("CEREBRAS_API_KEY") and exclude != "cerebras":
        chain.append("cerebras")
    chain.append("mock")
    return chain


async def get_provider_with_fallback(
    provider_name: Optional[str] = None,
    fallback_provider: Optional[str] = None
) -> LLMProvider:
    """
    Get LLM provider with automatic fallback support.

    BYOK v0.4.0: If the primary provider fails, cascades through free-tier
    providers (Groq → Cerebras) before falling back to mock, preventing
    silent empty responses when a BYOK key rate-limits.

    Args:
        provider_name: Primary provider (defaults to LLM_PROVIDER env var)
        fallback_provider: Explicit fallback; if None, uses smart cascade

    Returns:
        Configured LLMProvider instance (primary or best available fallback)

    Environment Variables:
        LLM_PROVIDER: Primary provider to use
        LLM_FALLBACK_PROVIDER: Explicit fallback (overrides smart cascade)
        GROQ_API_KEY: If set, Groq is tried before mock in fallback cascade
        CEREBRAS_API_KEY: If set, Cerebras is tried before mock in cascade
    """
    if provider_name is None:
        provider_name = os.getenv("LLM_PROVIDER") or os.getenv("VERIFIMIND_LLM_PROVIDER", "mock")

    # Try primary provider
    try:
        provider = get_provider(provider_name)
        logger.info(f"Using primary provider: {provider_name}")
        return provider
    except Exception as e:
        logger.warning(
            "Primary provider %s failed exception_type=%s",
            provider_name,
            type(e).__name__,
        )

    # Build fallback chain
    chain = [fallback_provider] if fallback_provider else _resolve_fallback_chain(provider_name)

    for candidate in chain:
        if not candidate or candidate == provider_name:
            continue
        try:
            provider = get_provider(candidate)
            logger.info(f"Fallback: using {candidate}")
            return provider
        except Exception as e:
            logger.warning(
                "Fallback provider %s failed exception_type=%s",
                candidate,
                type(e).__name__,
            )

    # Guaranteed last resort
    logger.info("Using mock provider as last resort")
    return get_provider("mock")


def register_provider(name: str, provider_class: Type[LLMProvider]) -> None:
    """
    Register a custom LLM provider.

    Args:
        name: Provider name for lookup
        provider_class: Provider class implementing LLMProvider
    """
    _PROVIDERS[name.lower()] = provider_class


def validate_provider_config(provider_name: str) -> Dict[str, Any]:
    """
    Validate that a provider is properly configured.

    Args:
        provider_name: Provider to validate

    Returns:
        Dict with validation status and details
    """
    provider_name = provider_name.lower()

    if provider_name not in _PROVIDERS:
        return {
            "valid": False,
            "provider": provider_name,
            "error": f"Unknown provider. Available: {list(_PROVIDERS.keys())}"
        }

    config = PROVIDER_CONFIGS.get(provider_name, {})
    api_key_env = config.get("api_key_env")

    # Check if API key is configured (if required)
    if api_key_env:
        api_key = os.getenv(api_key_env)
        if not api_key:
            return {
                "valid": False,
                "provider": provider_name,
                "error": f"API key not set. Set {api_key_env} environment variable.",
                "free_tier": config.get("free_tier", False)
            }

    return {
        "valid": True,
        "provider": provider_name,
        "name": config.get("name", provider_name),
        "default_model": config.get("default_model"),
        "free_tier": config.get("free_tier", False)
    }
