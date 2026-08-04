"""
Genesis Context Server - Phase 2 (Core Tools)
==============================================

MCP server exposing VerifiMind-PEAS Genesis Methodology context as Resources
and agent consultation as Tools.

Resources Exposed:
- genesis://config/master_prompt - Genesis Master Prompt v16.1
- genesis://history/latest - Most recent validation result
- genesis://history/all - Complete validation history
- genesis://state/project_info - Current project information

Tools Exposed:
- consult_agent_x - Consult X Intelligent for innovation analysis
- consult_agent_z - Consult Z Guardian for ethical review
- consult_agent_cs - Consult CS Security for security validation
- run_full_trinity - Run complete X → Z → CS validation

Author: Alton Lee
Version: 0.4.5 (BYOK Live — Per-Tool-Call Provider Override)
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

from fastmcp import FastMCP, Context

from pydantic import BaseModel, Field

from verifimind_mcp.utils.uuid_tracer import emit_tracer
from verifimind_mcp.utils.trinity_history import persist_trinity_result
from verifimind_mcp.llm.failover import FailoverExhaustedError, FailoverTerminalError
from verifimind_mcp.availability import system_notice_is_compatible

# Initialize logger for security events
logger = logging.getLogger(__name__)

# v0.4.3 — System Notice: broadcast messages to all MCP users via env var
_RAW_SYSTEM_NOTICE = os.environ.get("SYSTEM_NOTICE", "")
SERVER_VERSION = "0.5.56"

# Agent role names + master prompt filename — single source of truth.
# (SonarCloud P2 batch-2: extracted in v0.5.39 from 13 dup-literal occurrences
# across project_info dict, agent dispatch, and path resolution.)
AGENT_X_NAME = "X Intelligent"
AGENT_Z_NAME = "Z Guardian"
AGENT_CS_NAME = "CS Security"
MASTER_PROMPT_FILENAME = "reflexion-master-prompts-v1.1.md"

# Mock mode transparency — shown in every tool response when no real inference is available
MOCK_MODE_WARNING = (
    "Mock mode active — LLM inference unavailable (no API keys configured). "
    "The Trinity framework, chain-of-thought structure, and output schema are fully intact. "
    "Scores and reasoning content are synthetic placeholders — suitable for onboarding, "
    "demos, and integration testing, but not for real business decisions. "
    "Add GEMINI_API_KEY for free real inference: https://aistudio.google.com/apikey"
)

# Track C — SYSTEM_NOTICE sanitization constants
_NOTICE_MAX_LEN = 280
_NOTICE_ALLOWED = re.compile(r"[^A-Za-z0-9 .,!?'\"\-()\/:@#=&]")
_NOTICE_ALLOWED_DOMAINS = {"verifimind.ysenseai.org", "verifimind.io", "ysenseai.org"}


def _sanitize_system_notice(notice: str) -> str:
    """Sanitize SYSTEM_NOTICE: max 280 chars, allow-list chars, domain-check URLs."""
    if not notice:
        return ""
    notice = notice[:_NOTICE_MAX_LEN]
    notice = _NOTICE_ALLOWED.sub("", notice)
    for m in re.finditer(r"https?://([^\s/]+)", notice):
        domain = m.group(1)
        if not any(domain == d or domain.endswith("." + d) for d in _NOTICE_ALLOWED_DOMAINS):
            logger.warning(f"SYSTEM_NOTICE: blocked URL domain '{domain}'")
            notice = notice.replace(m.group(0), "")
    return notice.strip()


_SANITIZED_SYSTEM_NOTICE = _sanitize_system_notice(_RAW_SYSTEM_NOTICE)
if _SANITIZED_SYSTEM_NOTICE and not system_notice_is_compatible(
    _SANITIZED_SYSTEM_NOTICE
):
    logger.warning(
        "SYSTEM_NOTICE suppressed because it contradicts current tool availability"
    )
    SYSTEM_NOTICE = ""
else:
    SYSTEM_NOTICE = _SANITIZED_SYSTEM_NOTICE


def wrap_response(response: dict) -> dict:
    """Add system notice and version metadata to every tool response."""
    if SYSTEM_NOTICE and system_notice_is_compatible(SYSTEM_NOTICE):
        response["_system_notice"] = SYSTEM_NOTICE
    response["_server_version"] = SERVER_VERSION
    return response


def actual_provider_used(result, provider) -> str:
    """WP-B honest disclosure: when runtime failover hopped, `_provider_used`
    must name the provider that actually served the request, not the primary
    the handler constructed. Without failover attempts (the normal/dark
    path), this is exactly `provider.get_model_name()` as before."""
    attempts = getattr(result, "_provider_attempts", None)
    if attempts:
        final = attempts[-1]
        if final.get("outcome_class") == "success" and final.get("model"):
            return final["model"]
    return provider.get_model_name()


def attach_failover_disclosure(payload: dict, result) -> None:
    """Add the privacy-minimal attempt trail to a tool payload when the
    failover executor ran (absent otherwise — strictly additive). B-92-3:
    the ephemeral consultation correlation is part of the success contract,
    not only the error contract."""
    attempts = getattr(result, "_provider_attempts", None)
    if attempts:
        payload["_provider_attempts"] = attempts
        payload["_failover_occurred"] = getattr(result, "_failover_occurred", False)
        correlation = getattr(result, "_failover_correlation", None)
        if correlation:
            payload["_failover_correlation"] = correlation


def trinity_failover_meta(stage_results: dict) -> dict:
    """Trinity-level failover disclosure (B-92-3): per-stage attempt trails
    and correlations, present only when at least one stage ran the executor."""
    stage_attempts = {
        aid: getattr(res, "_provider_attempts", None)
        for aid, res in stage_results.items()
    }
    if not any(stage_attempts.values()):
        return {}
    meta = {
        "_provider_attempts": {
            aid: attempts for aid, attempts in stage_attempts.items() if attempts
        },
        "_failover_occurred": any(
            getattr(res, "_failover_occurred", False)
            for res in stage_results.values()
        ),
    }
    correlations = {
        aid: getattr(res, "_failover_correlation", None)
        for aid, res in stage_results.items()
        if getattr(res, "_failover_correlation", None)
    }
    if correlations:
        meta["_failover_correlations"] = correlations
    return meta


def failover_error_payload(exc, agent: str, concept_name: Optional[str] = None) -> dict:
    """B-90-8: the stable terminal contract for failover-lane failures.

    FAILOVER_EXHAUSTED = all bounded attempts failed (explicit instead of a
    silent mock). HOSTED_PROVIDER_TERMINAL = auth/config or invalid-request
    on the HOSTED lane — distinct from BYOK_AUTH_FAILED by construction,
    because BYOK providers never enter the executor. Both carry the
    privacy-minimal attempt trail (provider/model/class/duration only) and an
    ephemeral per-consultation correlation value; no prompts, responses, or
    user/registration identifiers."""
    exhausted = getattr(exc, "error_code", "") == "FAILOVER_EXHAUSTED"
    if exhausted:
        message = "All bounded runtime-failover attempts failed."
        hint = ("The hosted providers for this agent are currently failing. "
                "Try again shortly, or pass BYOK params to use your own provider.")
    else:
        message = f"Hosted provider terminal failure ({exc.final_reason_class})."
        hint = ("This hosted-lane failure is not retryable (auth/config or "
                "invalid request) — the operator has been signalled via logs. "
                "BYOK requests are unaffected.")
    payload = build_error_response(
        error_code=exc.error_code,
        message=message,
        recovery_hint=hint,
        agent=agent,
        original_error=exc,
    )
    payload["_provider_attempts"] = exc.attempts
    payload["attempt_count"] = len(exc.attempts)
    payload["final_reason_class"] = exc.final_reason_class
    # B-92-1: EXPLICIT terminal truth from the executor — never inferred
    # from the trail. A proposed-but-rejected hop is not failover, and the
    # final provider is the one that actually executed inference (or None).
    payload["_failover_occurred"] = exc.hop_executed
    payload["final_provider"] = exc.final_provider
    payload["_failover_correlation"] = exc.correlation
    payload["_inference_quality"] = "unavailable"
    if concept_name is not None:
        payload["concept"] = concept_name
    return payload


def build_error_response(
    error_code: str,
    message: str,
    recovery_hint: str,
    agent: Optional[str] = None,
    original_error: Optional[Exception] = None,
) -> dict:
    """Build a structured error response (v0.5.0 Error Handling v2).

    Args:
        error_code: Machine-readable error code (e.g. "BYOK_AUTH_FAILED")
        message: Human-readable error description
        recovery_hint: Actionable suggestion for the user
        agent: Which agent raised the error (X, Z, CS, or None for orchestrator)
        original_error: Original exception for debug logging

    Returns:
        Structured error dict ready for wrap_response()
    """
    import datetime as _dt
    if original_error:
        logger.error(
            "[%s] agent=%s exception_type=%s",
            error_code,
            agent,
            type(original_error).__name__,
        )
    return {
        "status": "error",
        "error_code": error_code,
        "error": message,
        "recovery_hint": recovery_hint,
        "agent": agent,
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }


def _agent_exception_payload(
    exc: Exception,
    agent: str,
    concept_name: str,
) -> dict:
    """Return a stable error without reflecting provider/model output."""
    detail = str(exc).lower()
    if "401" in detail or "invalid api key" in detail or "authentication" in detail:
        error_code = "BYOK_AUTH_FAILED"
        message = "API key authentication failed."
        hint = "Check that the key matches the selected provider, or omit BYOK parameters."
    elif "timeout" in detail or "timed out" in detail:
        error_code = "PROVIDER_TIMEOUT"
        message = "The LLM provider timed out."
        hint = "Try again shortly or select a lower-latency provider."
    elif type(exc).__name__ == "ValidationError":
        error_code = "INCOMPLETE_PROVIDER_RESPONSE"
        message = "The provider returned an incomplete structured analysis."
        hint = "Retry the analysis; no generated fields from the failed response were returned."
    else:
        error_code = "AGENT_ANALYSIS_ERROR"
        message = "The agent analysis could not be completed."
        hint = "Try again. If the issue persists, omit BYOK parameters to use hosted routing."

    payload = build_error_response(
        error_code=error_code,
        message=message,
        recovery_hint=hint,
        agent=agent,
        original_error=exc,
    )
    payload["concept"] = concept_name
    payload["_inference_quality"] = "unavailable"
    return payload


def _apply_agent_quality_gate(
    payload: dict,
    result,
    generated_fields: tuple,
) -> dict:
    """Withhold generated standalone-agent fields unless inference is real."""
    quality = getattr(result, "_inference_quality", "unknown")
    repaired = list(getattr(result, "_schema_repaired_fields", []))
    incomplete = list(getattr(result, "_schema_incomplete_fields", []))
    payload["analysis_incomplete"] = quality != "real"
    payload["_schema_diagnostics"] = {
        "repaired_fields": repaired,
        "incomplete_fields": incomplete,
    }
    if quality != "real":
        payload["reasoning_steps"] = []
        for field in generated_fields:
            if field in payload:
                payload[field] = None
        payload["_warning"] = (
            f"Agent inference quality was '{quality}', not 'real'. Generated "
            "analysis fields are withheld pending a clean rerun."
        )
    return payload


CUSTOM_TEMPLATE_CONTAINMENT_INCIDENT = "VM-IR-2026-08-01-TEMPLATE-01"


def _template_mutation_contained(tool_name: str) -> dict:
    """Stable, non-reflecting denial for unsafe custom-template mutation."""
    contained = wrap_response(build_error_response(
        error_code="CUSTOM_TEMPLATE_TEMPORARILY_DISABLED",
        message=(
            "Custom-template registration and URL import are temporarily "
            "disabled while owner-scoped storage and URL-fetch protections "
            "are completed. Built-in template read tools remain available."
        ),
        recovery_hint=(
            "Use the built-in template library or keep custom templates in your "
            "own repository until private owner-scoped storage is released. "
            f"Incident reference: {CUSTOM_TEMPLATE_CONTAINMENT_INCIDENT}."
        ),
        agent=tool_name,
    ))
    contained.pop("_system_notice", None)
    return contained


class VerifiMindConfig(BaseModel):
    """Session configuration for VerifiMind Genesis Server.

    BYOK v0.3.0 - Multi-Provider Support

    Allows users to bring their own API keys for any supported LLM provider.
    Free tier providers (Gemini, Groq, Ollama) are recommended for cost-free usage.
    """
    llm_provider: str = Field(
        default="mock",
        description="LLM provider: 'gemini' (FREE), 'groq' (FREE), 'openai', 'anthropic', 'mistral', 'ollama' (local), or 'mock' (testing)"
    )
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (optional, can also use OPENAI_API_KEY env var)"
    )
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key (optional, can also use ANTHROPIC_API_KEY env var)"
    )
    gemini_api_key: str = Field(
        default="",
        description="Gemini API key (optional, can also use GEMINI_API_KEY env var) - FREE tier available!"
    )
    groq_api_key: str = Field(
        default="",
        description="Groq API key (optional, can also use GROQ_API_KEY env var) - FREE tier available!"
    )
    mistral_api_key: str = Field(
        default="",
        description="Mistral API key (optional, can also use MISTRAL_API_KEY env var)"
    )
    validation_mode: str = Field(
        default="standard",
        description="Validation strictness: 'standard' or 'strict'"
    )


# Constants - Use robust path resolution for Docker and local environments
def _get_master_prompt_path() -> Path:
    """Find master prompt file in Docker or local environment."""
    # Locations to check (in order of priority):
    # 1. Current working directory (Docker: /app)
    # 2. Parent of package directory
    # 3. Repository root (development)

    candidates = [
        Path.cwd() / MASTER_PROMPT_FILENAME,  # Docker: /app/
        Path(__file__).parent.parent.parent / MASTER_PROMPT_FILENAME,  # Package parent
        Path(__file__).parent.parent.parent.parent / MASTER_PROMPT_FILENAME,  # Repo root
    ]

    for path in candidates:
        if path.exists():
            return path

    # Return first candidate as default (will show error in load_master_prompt)
    return candidates[0]


def _get_history_path() -> Path:
    """Find or create validation history file path."""
    # Use current working directory (Docker: /app, Local: project root)
    return Path.cwd() / "verifimind_history.json"


MASTER_PROMPT_PATH = _get_master_prompt_path()
HISTORY_PATH = _get_history_path()
MASTER_PROMPT_UNAVAILABLE = (
    "# Error Building Master Prompt\n\nThe live methodology is temporarily unavailable."
)
VALIDATION_HISTORY_UNAVAILABLE = "Validation history is temporarily unavailable."
TEMPLATE_READ_UNAVAILABLE = "Prompt template operation failed."


def load_master_prompt() -> str:
    """Build the Genesis methodology surface from the LIVE production prompts.

    v0.5.43 fix: this resource previously served a Sept-2025 v1.1 collection that
    no longer matched the prompts the agents actually run and embedded internal
    business targets + personal contact info. It is now generated directly from
    the in-code AGENT_CONFIGS, so the public methodology surface is exactly the
    prompt contract X / Z / CS execute — it cannot drift or misrepresent.
    """
    try:
        from .models.concepts import AGENT_CONFIGS
    except Exception:  # pragma: no cover - defensive
        return MASTER_PROMPT_UNAVAILABLE

    role_titles = {
        "X": "X Intelligent — Innovation & Strategy",
        "Z": "Z Guardian — Ethics & Compliance (VETO power)",
        "CS": "CS Security — Security & Socratic Challenge",
    }

    lines = [
        "# VerifiMind™ PEAS — Genesis Methodology (Live Production Prompts)",
        "",
        (
            f"*Server version: {SERVER_VERSION}. Generated from the in-code agent "
            "configuration — this is the exact prompt contract the X / Z / CS agents run.*"
        ),
        "",
        (
            "The RefleXion Trinity validates a concept through three sequential agents. "
            "Each agent sees the prior agents' Chain-of-Thought reasoning. Synthesis "
            "weights: Innovation (X) 30% · Ethics (Z) 40% · Security (CS) 30%. A Z veto "
            "caps the overall score at 3.0 and forces a REJECT verdict. If any agent's "
            "inference is degraded, no recommendation more permissive than REVISE is "
            "allowed; a trusted real Z veto still forces REJECT (fail-safe)."
        ),
        "",
        "---",
        "",
    ]

    for agent_id in ("X", "Z", "CS"):
        cfg = AGENT_CONFIGS[agent_id]
        lines.extend([
            f"## {role_titles.get(agent_id, cfg.name)}",
            "",
            f"**Role:** {cfg.role}",
            "",
            "**Focus areas:** " + "; ".join(cfg.focus_areas),
            "",
            f"**Inference settings:** temperature={cfg.temperature}, max_tokens={cfg.max_tokens}",
            "",
            "**Production prompt template (verbatim):**",
            "",
            "```text",
            cfg.prompt_template.strip(),
            "```",
            "",
            "---",
            "",
        ])

    lines.append("*VerifiMind™ PEAS — github.com/creator35lwb-web/VerifiMind-PEAS*")
    return "\n".join(lines)


def load_validation_history() -> dict[str, Any]:
    """Load validation history from JSON file."""
    try:
        if HISTORY_PATH.exists():
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            return {
                "validations": [],
                "metadata": {
                    "total_validations": 0,
                    "last_updated": None,
                    "note": "No validation history found. Run verifimind_complete.py to generate validation data."
                }
            }
    except Exception:
        return {
            "error": VALIDATION_HISTORY_UNAVAILABLE,
            "validations": []
        }


def save_validation_history(history: dict[str, Any]) -> None:
    """Save validation history to JSON file."""
    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, default=str)
    except Exception as e:
        print(f"Warning: Failed to save validation history: {e}")


def get_latest_validation() -> dict[str, Any]:
    """Get most recent validation result."""
    history = load_validation_history()
    validations = history.get("validations", [])
    
    if validations:
        return validations[-1]
    else:
        return {
            "status": "no_validations",
            "message": "No validation history available. Run verifimind_complete.py to generate validation data."
        }


def _redacted_latest_validation() -> dict[str, Any]:
    """Non-identifying summary of the most recent validation.

    The validation-history store is shared across all clients of this server
    instance, so this MUST NOT return concept_name / concept_description or any
    free-text the caller supplied (v0.5.43 cross-tenant privacy fix).
    """
    latest = get_latest_validation()
    if not isinstance(latest, dict) or latest.get("status") == "no_validations":
        return {
            "status": "no_validations",
            "message": "No validations recorded on this instance.",
        }
    synthesis = latest.get("synthesis", {}) if isinstance(latest.get("synthesis"), dict) else {}
    return {
        "validation_id": latest.get("validation_id"),
        "recommendation": synthesis.get("recommendation"),
        "overall_score": synthesis.get("overall_score"),
        "veto_triggered": synthesis.get("veto_triggered"),
        "completed_at": latest.get("completed_at"),
        "_note": "Concept name/description intentionally omitted — shared instance store (v0.5.43 privacy).",
    }


def _aggregate_validation_stats() -> dict[str, Any]:
    """Aggregate, non-identifying statistics over the shared validation history."""
    history = load_validation_history()
    validations = history.get("validations", []) if isinstance(history, dict) else []
    total = len(validations)
    if total == 0:
        return {
            "total_validations": 0,
            "recommendation_distribution": {},
            "veto_count": 0,
            "last_updated": history.get("metadata", {}).get("last_updated") if isinstance(history, dict) else None,
            "_note": "Aggregate stats only — per-concept detail never exposed (v0.5.43 privacy).",
        }
    rec_dist: dict[str, int] = {}
    veto_count = 0
    for v in validations:
        synthesis = v.get("synthesis", {}) if isinstance(v, dict) else {}
        rec = synthesis.get("recommendation", "unknown")
        rec_dist[rec] = rec_dist.get(rec, 0) + 1
        if synthesis.get("veto_triggered"):
            veto_count += 1
    return {
        "total_validations": total,
        "recommendation_distribution": rec_dist,
        "veto_count": veto_count,
        "last_updated": history.get("metadata", {}).get("last_updated"),
        "_note": "Aggregate stats only — per-concept detail never exposed (v0.5.43 privacy).",
    }


def get_project_info() -> dict[str, Any]:
    """Get current project information."""
    return {
        "project_name": "VerifiMind-PEAS",
        "methodology": "Genesis Methodology",
        "version": "2.0.1",
        "architecture": "RefleXion Trinity (X-Z-CS)",
        "mcp_server_version": SERVER_VERSION,
        "agents": {
            "X": {
                "name": AGENT_X_NAME,
                "role": "Innovation and Strategy Engine",
                "focus": ["Innovation potential", "Strategic value", "Market opportunities"]
            },
            "Z": {
                "name": AGENT_Z_NAME,
                "role": "Ethical Review and Z-Protocol Enforcement",
                "focus": ["Ethics", "Privacy", "Bias", "Social impact"],
                "has_veto_power": True
            },
            "CS": {
                "name": AGENT_CS_NAME,
                "role": "Security Validation and Socratic Interrogation",
                "focus": ["Security vulnerabilities", "Attack vectors", "Socratic questioning"]
            }
        },
        "master_prompt_version": "live (generated from production AGENT_CONFIGS)",
        "repository": "https://github.com/creator35lwb-web/VerifiMind-PEAS",
        "documentation": "https://github.com/creator35lwb-web/VerifiMind-PEAS/docs",
        "white_paper": "https://github.com/creator35lwb-web/VerifiMind-PEAS/docs/white_paper/Genesis_Methodology_White_Paper_v1.1.md"
    }


def _create_mcp_instance():
    """Internal function to create the raw FastMCP instance.

    This is used by both create_server() (Smithery playground) and
    create_http_server() (HTTP deployment).

    Returns:
        FastMCP: Raw FastMCP server instance with all tools and resources registered.
    """
    # Initialize MCP server
    app = FastMCP("verifimind-genesis", version=SERVER_VERSION)

    # ===== RESOURCES =====

    @app.resource("genesis://config/master_prompt")
    def get_master_prompt() -> str:
        """
        Genesis Methodology — Live Production Prompts

        Returns the X / Z / CS prompt contract generated directly from the agents'
        in-code configuration, so it always matches what the agents actually run
        (v0.5.43). Includes roles, focus areas, inference settings, and the verbatim
        production prompt templates.

        URI: genesis://config/master_prompt
        Format: Markdown
        """
        return load_master_prompt()


    @app.resource("genesis://history/latest")
    def get_latest_validation_resource() -> str:
        """
        Latest Validation — Privacy-Safe Summary

        Returns a NON-IDENTIFYING summary of the most recent validation (verdict,
        scores, timestamp). Concept names and descriptions are NOT exposed: the
        validation-history store is shared across all clients of this server
        instance, so returning raw concept text would leak one caller's idea to
        another (v0.5.43 cross-tenant privacy fix).

        URI: genesis://history/latest
        Format: JSON
        """
        return json.dumps(_redacted_latest_validation(), indent=2)


    @app.resource("genesis://history/all")
    def get_all_validations() -> str:
        """
        Validation History — Aggregate Statistics Only

        Returns aggregate statistics over the shared validation history (total
        count, score/verdict distribution, last-updated) — never the per-concept
        names or descriptions. The history store is instance-global; exposing raw
        entries here would leak other clients' concepts (v0.5.43 privacy fix).

        URI: genesis://history/all
        Format: JSON
        """
        return json.dumps(_aggregate_validation_stats(), indent=2)


    @app.resource("genesis://state/project_info")
    def get_project_info_resource() -> str:
        """
        Project Information

        Returns metadata about the VerifiMind-PEAS project including architecture,
        agent roles, version information, and documentation links.

        URI: genesis://state/project_info
        Format: JSON
        """
        info = get_project_info()
        return json.dumps(info, indent=2)


    # ===== TOOLS =====

    @app.tool()
    async def consult_agent_x(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        detail: str = "standard",
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
        user_uuid: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Consult X Intelligent agent for innovation and strategy analysis.

        X Intelligent specializes in:
        - Innovation potential assessment
        - Strategic value analysis
        - Market opportunity identification
        - Competitive positioning
        - Growth potential evaluation

        BYOK (v0.4.5): Pass llm_provider and api_key to use your own LLM.
        If only api_key is provided, the provider is auto-detected from the key prefix.
        Keys are ephemeral (never stored) and garbage collected after the call.

        Args:
            concept_name: Short name or title of the concept
            concept_description: Detailed description of the concept
            context: Optional additional context or background
            llm_provider: Optional LLM provider override ('groq', 'anthropic', 'openai', 'gemini', 'mistral', 'ollama', 'mock')
            api_key: Optional API key for the provider (ephemeral, never stored)

        Returns:
            Structured analysis with reasoning chain, scores, and recommendations
        """
        if user_uuid:
            emit_tracer(user_uuid, "consult_agent_x")
        try:
            from .models import Concept
            from .agents import XAgent
            from .utils import sanitize_concept_input

            # Sanitize inputs for security (v0.3.5)
            sanitized = sanitize_concept_input(
                name=concept_name,
                description=concept_description,
                context=context
            )
            if sanitized['was_modified']:
                logger.warning(f"X Agent input sanitized: {sanitized['warnings']}")

            # Create concept with sanitized values
            concept = Concept(
                name=sanitized['name'],
                description=sanitized['description'],
                context=sanitized['context']
            )

            # v0.4.5 BYOK: Try ephemeral provider first, fall back to server default
            from .config_helper import get_agent_provider, create_ephemeral_provider
            byok_used = False
            provider = create_ephemeral_provider(llm_provider, api_key, "X")
            if provider is not None:
                byok_used = True
            else:
                provider = get_agent_provider("X", ctx)

            # Create agent and analyze
            agent = XAgent(llm_provider=provider)
            result = await agent.analyze(concept)

            _iq = getattr(result, '_inference_quality', 'unknown')
            from .utils.reasoning_view import normalize_detail, consult_steps
            detail = normalize_detail(detail)
            payload = {
                "agent": AGENT_X_NAME,
                "concept": concept_name,
                "reasoning_steps": consult_steps(result.reasoning_steps, detail),
                "innovation_score": result.innovation_score,
                "strategic_value": result.strategic_value,
                "opportunities": result.opportunities,
                "risks": result.risks,
                "recommendation": result.recommendation,
                "confidence": result.confidence,
                "_inference_quality": _iq,
                "_provider_used": actual_provider_used(result, provider),
                "_byok": byok_used
            }
            # v0.5.44: structured fields at standard+; heaviest at full
            if detail in ("standard", "full"):
                payload["next_steps"] = getattr(result, "next_steps", None) or []
                payload["research_prompts"] = getattr(result, "research_prompts", None) or []
            if detail == "full":
                payload["market_competition"] = getattr(result, "market_competition", None)
                payload["competitive_analysis"] = getattr(result, "competitive_analysis", None)
            _apply_agent_quality_gate(payload, result, (
                "innovation_score", "strategic_value", "opportunities", "risks",
                "recommendation", "confidence", "next_steps", "research_prompts",
                "market_competition", "competitive_analysis",
            ))
            attach_failover_disclosure(payload, result)
            persist_trinity_result(user_uuid, "consult_agent_x", payload)
            return wrap_response(payload)

        except (FailoverExhaustedError, FailoverTerminalError) as e:
            # B-90-8: the executor's typed contract survives the MCP boundary
            return wrap_response(failover_error_payload(e, AGENT_X_NAME, concept_name))
        except Exception as e:
            return wrap_response(_agent_exception_payload(
                e, AGENT_X_NAME, concept_name
            ))


    @app.tool()
    async def consult_agent_z(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        prior_reasoning: Optional[str] = None,
        detail: str = "standard",
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
        user_uuid: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Consult Z Guardian agent for ethical review and Z-Protocol enforcement.

        Z Guardian specializes in:
        - Ethical implications assessment
        - Privacy and data protection review
        - Bias and fairness analysis
        - Social impact evaluation
        - Z-Protocol compliance verification

        Z Guardian has VETO POWER. If veto_triggered is True, the concept
        should not proceed as it crosses ethical red lines.

        BYOK (v0.4.5): Pass llm_provider and api_key to use your own LLM.
        If only api_key is provided, the provider is auto-detected from the key prefix.
        Keys are ephemeral (never stored) and garbage collected after the call.

        Args:
            concept_name: Short name or title of the concept
            concept_description: Detailed description of the concept
            context: Optional additional context or background
            prior_reasoning: Optional reasoning from X agent to consider
            llm_provider: Optional LLM provider override ('groq', 'anthropic', 'openai', 'gemini', 'mistral', 'ollama', 'mock')
            api_key: Optional API key for the provider (ephemeral, never stored)

        Returns:
            Structured analysis with reasoning chain, ethics score, and veto status
        """
        if user_uuid:
            emit_tracer(user_uuid, "consult_agent_z")
        try:
            from .models import Concept, PriorReasoning, ChainOfThought, ReasoningStep
            from .agents import ZAgent
            from .utils import sanitize_concept_input

            # Sanitize inputs for security (v0.3.5)
            sanitized = sanitize_concept_input(
                name=concept_name,
                description=concept_description,
                context=context
            )
            if sanitized['was_modified']:
                logger.warning(f"Z Agent input sanitized: {sanitized['warnings']}")

            # Create concept with sanitized values
            concept = Concept(
                name=sanitized['name'],
                description=sanitized['description'],
                context=sanitized['context']
            )

            # Parse prior reasoning if provided
            prior = None
            if prior_reasoning:
                # Create a simple prior reasoning object
                prior = PriorReasoning()
                prior.add(ChainOfThought(
                    agent_id="X",
                    agent_name=AGENT_X_NAME,
                    concept_name=concept_name,
                    reasoning_steps=[ReasoningStep(step_number=1, thought=prior_reasoning)],
                    final_conclusion="See prior reasoning above",
                    overall_confidence=0.8
                ))

            # v0.4.5 BYOK: Try ephemeral provider first, fall back to server default
            from .config_helper import get_agent_provider, create_ephemeral_provider
            byok_used = False
            provider = create_ephemeral_provider(llm_provider, api_key, "Z")
            if provider is not None:
                byok_used = True
            else:
                provider = get_agent_provider("Z", ctx)

            # Create agent and analyze
            agent = ZAgent(llm_provider=provider)
            result = await agent.analyze(concept, prior)

            _iq = getattr(result, '_inference_quality', 'unknown')
            from .utils.reasoning_view import normalize_detail, consult_steps
            detail = normalize_detail(detail)
            payload = {
                "agent": AGENT_Z_NAME,
                "concept": concept_name,
                "reasoning_steps": consult_steps(result.reasoning_steps, detail),
                "ethics_score": result.ethics_score,
                "z_protocol_compliance": result.z_protocol_compliance,
                "ethical_concerns": result.ethical_concerns,
                "mitigation_measures": result.mitigation_measures,
                "recommendation": result.recommendation,
                "veto_triggered": result.veto_triggered,
                "confidence": result.confidence,
                "_inference_quality": _iq,
                "_provider_used": actual_provider_used(result, provider),
                "_byok": byok_used
            }
            # v0.5.44: framework citations + scoring breakdown at standard+
            if detail in ("standard", "full"):
                payload["scoring_breakdown"] = getattr(result, "scoring_breakdown", None)
                payload["jurisdiction_detected"] = getattr(result, "jurisdiction_detected", None)
                payload["applicable_frameworks"] = getattr(result, "applicable_frameworks", None)
                payload["compliance_timeline"] = getattr(result, "compliance_timeline", None)
            if detail == "full":
                payload["total_frameworks_evaluated"] = getattr(result, "total_frameworks_evaluated", None)
            _apply_agent_quality_gate(payload, result, (
                "ethics_score", "z_protocol_compliance", "ethical_concerns",
                "mitigation_measures", "recommendation", "veto_triggered",
                "confidence", "scoring_breakdown", "jurisdiction_detected",
                "applicable_frameworks", "compliance_timeline",
                "total_frameworks_evaluated",
            ))
            attach_failover_disclosure(payload, result)
            persist_trinity_result(user_uuid, "consult_agent_z", payload)
            return wrap_response(payload)

        except (FailoverExhaustedError, FailoverTerminalError) as e:
            return wrap_response(failover_error_payload(e, AGENT_Z_NAME, concept_name))
        except Exception as e:
            return wrap_response(_agent_exception_payload(
                e, AGENT_Z_NAME, concept_name
            ))


    @app.tool()
    async def consult_agent_cs(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        prior_reasoning: Optional[str] = None,
        detail: str = "standard",
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
        user_uuid: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Consult CS Security agent for security validation and Socratic interrogation.

        CS Security specializes in:
        - Security vulnerability assessment
        - Attack vector identification
        - Data security review
        - System integrity analysis
        - Socratic questioning (challenging assumptions)

        BYOK (v0.4.5): Pass llm_provider and api_key to use your own LLM.
        If only api_key is provided, the provider is auto-detected from the key prefix.
        Keys are ephemeral (never stored) and garbage collected after the call.

        Args:
            concept_name: Short name or title of the concept
            concept_description: Detailed description of the concept
            context: Optional additional context or background
            prior_reasoning: Optional reasoning from X and Z agents to consider
            llm_provider: Optional LLM provider override ('groq', 'anthropic', 'openai', 'gemini', 'mistral', 'ollama', 'mock')
            api_key: Optional API key for the provider (ephemeral, never stored)

        Returns:
            Structured analysis with security score, vulnerabilities, and Socratic questions
        """
        if user_uuid:
            emit_tracer(user_uuid, "consult_agent_cs")
        try:
            from .models import Concept, PriorReasoning, ChainOfThought, ReasoningStep
            from .agents import CSAgent
            from .utils import sanitize_concept_input

            # Sanitize inputs for security (v0.3.5)
            sanitized = sanitize_concept_input(
                name=concept_name,
                description=concept_description,
                context=context
            )
            if sanitized['was_modified']:
                logger.warning(f"CS Agent input sanitized: {sanitized['warnings']}")

            # Create concept with sanitized values
            concept = Concept(
                name=sanitized['name'],
                description=sanitized['description'],
                context=sanitized['context']
            )

            # Parse prior reasoning if provided
            prior = None
            if prior_reasoning:
                prior = PriorReasoning()
                prior.add(ChainOfThought(
                    agent_id="XZ",
                    agent_name="X Intelligent & Z Guardian",
                    concept_name=concept_name,
                    reasoning_steps=[ReasoningStep(step_number=1, thought=prior_reasoning)],
                    final_conclusion="See prior reasoning above",
                    overall_confidence=0.8
                ))

            # v0.4.5 BYOK: Try ephemeral provider first, fall back to server default
            from .config_helper import get_agent_provider, create_ephemeral_provider
            byok_used = False
            provider = create_ephemeral_provider(llm_provider, api_key, "CS")
            if provider is not None:
                byok_used = True
            else:
                provider = get_agent_provider("CS", ctx)

            # Create agent and analyze
            agent = CSAgent(llm_provider=provider)
            result = await agent.analyze(concept, prior)

            from .utils.reasoning_view import normalize_detail, consult_steps
            detail = normalize_detail(detail)
            payload = {
                "agent": AGENT_CS_NAME,
                "concept": concept_name,
                "reasoning_steps": consult_steps(result.reasoning_steps, detail),
                "security_score": result.security_score,
                "vulnerabilities": result.vulnerabilities,
                "attack_vectors": result.attack_vectors,
                "security_recommendations": result.security_recommendations,
                "socratic_questions": result.socratic_questions,
                "recommendation": result.recommendation,
                "confidence": result.confidence,
                "_inference_quality": getattr(result, '_inference_quality', 'unknown'),
                "_provider_used": actual_provider_used(result, provider),
                "_byok": byok_used
            }
            # v0.5.44: threat assessment at standard+; 12-dim/6-stage/MACP at full
            if detail in ("standard", "full"):
                payload["threat_level"] = getattr(result, "threat_level", None)
                payload["agentic_threats"] = getattr(result, "agentic_threats", None)
                payload["reasoning_layer_findings"] = getattr(result, "reasoning_layer_findings", None)
            if detail == "full":
                payload["dimensions_evaluated"] = getattr(result, "dimensions_evaluated", None)
                payload["stages_completed"] = getattr(result, "stages_completed", None)
                payload["macp_security_assessment"] = getattr(result, "macp_security_assessment", None)
                payload["standards_referenced"] = getattr(result, "standards_referenced", None)
            _apply_agent_quality_gate(payload, result, (
                "security_score", "vulnerabilities", "attack_vectors",
                "security_recommendations", "socratic_questions", "recommendation",
                "confidence", "threat_level", "agentic_threats",
                "reasoning_layer_findings", "dimensions_evaluated", "stages_completed",
                "macp_security_assessment", "standards_referenced",
            ))
            attach_failover_disclosure(payload, result)
            persist_trinity_result(user_uuid, "consult_agent_cs", payload)
            return wrap_response(payload)

        except (FailoverExhaustedError, FailoverTerminalError) as e:
            return wrap_response(failover_error_payload(e, AGENT_CS_NAME, concept_name))
        except Exception as e:
            return wrap_response(_agent_exception_payload(
                e, AGENT_CS_NAME, concept_name
            ))


    @app.tool()
    async def run_full_trinity(
        concept_name: str,
        concept_description: str,
        context: Optional[str] = None,
        save_to_history: bool = False,
        detail: str = "standard",
        llm_provider: Optional[str] = None,
        api_key: Optional[str] = None,
        x_provider: Optional[str] = None,
        x_api_key: Optional[str] = None,
        z_provider: Optional[str] = None,
        z_api_key: Optional[str] = None,
        cs_provider: Optional[str] = None,
        cs_api_key: Optional[str] = None,
        user_uuid: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Run complete X → Z → CS Trinity validation with Chain of Thought.

        This tool orchestrates all three agents in sequence:
        1. X Intelligent analyzes innovation and strategy
        2. Z Guardian reviews ethics (sees X's reasoning)
        3. CS Security validates security (sees X and Z reasoning)
        4. Results are synthesized into a unified assessment

        Each agent sees the reasoning of previous agents, enabling
        true collaborative analysis with full transparency.

        BYOK (v0.4.5): Pass llm_provider/api_key for all agents, or use
        per-agent overrides (x_provider/x_api_key, z_provider/z_api_key,
        cs_provider/cs_api_key). Per-agent params take priority over global.
        Keys are ephemeral (never stored) and garbage collected after the call.

        Args:
            concept_name: Short name or title of the concept
            concept_description: Detailed description of the concept
            context: Optional additional context or background
            save_to_history: Whether to save result to validation history (default: False).
                History is a single shared store on this server instance; leaving this
                False prevents the full concept/result from being written there. If
                user_uuid is supplied separately, pseudonymous validation metadata may
                still be written to UUID-keyed Firestore history (see Privacy v2.4).
            detail: Reasoning verbosity (v0.5.44) — "standard" (default) returns the
                auditable `reasoning` block (per-step reasoning, ethics scoring breakdown
                + framework citations, Socratic questions, threat assessment) alongside
                the scores; "full" adds per-step evidence and the heaviest structured
                fields (12-dimension matrix, 6-stage record, MACP assessment); "summary"
                omits the reasoning block for the smallest payload. The block is additive —
                existing response fields are unchanged at every level.
            llm_provider: Optional global LLM provider for all agents
            api_key: Optional global API key for all agents (ephemeral, never stored)
            x_provider: Optional provider override for X agent only
            x_api_key: Optional API key override for X agent only
            z_provider: Optional provider override for Z agent only
            z_api_key: Optional API key override for Z agent only
            cs_provider: Optional provider override for CS agent only
            cs_api_key: Optional API key override for CS agent only

        Returns:
            Complete Trinity validation result with all agent analyses and synthesis
        """
        if user_uuid:
            emit_tracer(user_uuid, "run_full_trinity")
        # v0.5.44: normalize reasoning verbosity (invalid → "standard")
        from .utils.reasoning_view import normalize_detail
        detail = normalize_detail(detail)
        # Check Accept header for markdown content negotiation
        output_format = "json"
        if ctx and hasattr(ctx, 'request_context'):
            req_ctx = ctx.request_context
            # RequestContext may be a dict or object — handle both safely
            if isinstance(req_ctx, dict):
                accept = req_ctx.get('accept', '')
            elif hasattr(req_ctx, 'get'):
                accept = req_ctx.get('accept', '')
            else:
                accept = getattr(req_ctx, 'accept', '')
            if 'text/markdown' in str(accept):
                output_format = "markdown"
        try:
            from .models import Concept, PriorReasoning
            from .agents import XAgent, ZAgent, CSAgent
            from .utils import create_trinity_result, sanitize_concept_input

            # Sanitize inputs for security (v0.3.5)
            sanitized = sanitize_concept_input(
                name=concept_name,
                description=concept_description,
                context=context
            )
            if sanitized['was_modified']:
                logger.warning(f"Trinity input sanitized: {sanitized['warnings']}")

            # Create concept with sanitized values
            concept = Concept(
                name=sanitized['name'],
                description=sanitized['description'],
                context=sanitized['context']
            )

            # v0.4.5 BYOK: Resolve per-agent providers with fallback to global BYOK, then server default
            from .config_helper import get_trinity_providers, create_ephemeral_provider
            byok_status = {}

            agent_byok_params = {
                "X": (x_provider or llm_provider, x_api_key or api_key),
                "Z": (z_provider or llm_provider, z_api_key or api_key),
                "CS": (cs_provider or llm_provider, cs_api_key or api_key),
            }

            resolved_providers = {}
            for agent_id, (prov, key) in agent_byok_params.items():
                ephemeral = create_ephemeral_provider(prov, key, agent_id)
                if ephemeral is not None:
                    resolved_providers[agent_id] = ephemeral
                    byok_status[agent_id] = True
                else:
                    byok_status[agent_id] = False

            # Fill in any agents that didn't get BYOK providers
            server_providers = get_trinity_providers(ctx)
            for agent_id in ("X", "Z", "CS"):
                if agent_id not in resolved_providers:
                    resolved_providers[agent_id] = server_providers[agent_id]

            # Initialize agents with their resolved providers
            x_agent = XAgent(llm_provider=resolved_providers["X"])
            z_agent = ZAgent(llm_provider=resolved_providers["Z"])
            cs_agent = CSAgent(llm_provider=resolved_providers["CS"])

            # v0.5.0 SessionContext: unique ID for run traceability and log correlation
            from .models.session import SessionContext
            session = SessionContext(concept_name=concept_name)

            # v0.4.3.1 C-S-P State: Track inference quality across chain
            chain_status = {}

            # Step 1: X Agent analysis (no prior reasoning)
            x_result = await x_agent.analyze(concept)
            x_quality = getattr(x_result, '_inference_quality', 'unknown')
            chain_status["x_agent"] = x_quality
            logger.info(f"Trinity X stage: quality={x_quality} session={session.session_id}")
            session.write("X", {
                "score": x_result.innovation_score if x_quality == "real" else None,
                "provider": resolved_providers["X"].get_model_name(),
            })
            x_cot = x_result.to_chain_of_thought(concept_name)

            # Step 2: Z Agent analysis (sees X's reasoning)
            z_prior = PriorReasoning()
            if x_quality == "real":
                z_prior.add(x_cot)
            z_result = await z_agent.analyze(concept, z_prior)
            z_quality = getattr(z_result, '_inference_quality', 'unknown')
            chain_status["z_agent"] = z_quality
            logger.info(f"Trinity Z stage: quality={z_quality} session={session.session_id}")

            # v0.5.3 Token Ceiling Monitor — Strategy 3
            from .utils import check_z_agent_response
            z_output_tokens = getattr(z_result, '_output_tokens', 0)
            z_token_monitor = check_z_agent_response(z_output_tokens)
            if z_token_monitor["risk_level"] in ("HIGH", "CRITICAL"):
                logger.warning(
                    f"Z Agent token ceiling risk: {z_token_monitor['utilization']} "
                    f"({z_token_monitor['token_count']}/{z_token_monitor['ceiling']}) "
                    f"risk={z_token_monitor['risk_level']}"
                )
            session.write("Z", {
                "score": z_result.ethics_score if z_quality == "real" else None,
                "veto": z_result.veto_triggered if z_quality == "real" else None,
                "provider": resolved_providers["Z"].get_model_name(),
            })
            z_cot = z_result.to_chain_of_thought(concept_name)

            # Step 3: CS Agent analysis (sees X and Z reasoning)
            cs_prior = PriorReasoning()
            if x_quality == "real":
                cs_prior.add(x_cot)
            if z_quality == "real":
                cs_prior.add(z_cot)
            cs_result = await cs_agent.analyze(concept, cs_prior)
            cs_quality = getattr(cs_result, '_inference_quality', 'unknown')
            chain_status["cs_agent"] = cs_quality
            logger.info(f"Trinity CS stage: quality={cs_quality} session={session.session_id}")
            session.write("CS", {
                "score": cs_result.security_score if cs_quality == "real" else None,
                "provider": resolved_providers["CS"].get_model_name(),
            })

            # v0.4.3.1 C-S-P Propagation: Compute overall quality
            quality_values = list(chain_status.values())
            if all(v == "real" for v in quality_values):
                overall_quality = "full"
            elif any(v == "mock" for v in quality_values):
                overall_quality = "synthetic"
            elif any(v == "fallback" for v in quality_values):
                overall_quality = "degraded"
            else:
                overall_quality = "partial"
            logger.info(f"Trinity chain complete: {chain_status} → {overall_quality}")
            if overall_quality != "full":
                logger.warning(
                    "Trinity quality gate withheld aggregate confidence: "
                    "x=%s z=%s cs=%s overall=%s",
                    x_quality,
                    z_quality,
                    cs_quality,
                    overall_quality,
                )

            schema_diagnostics = {}
            for agent_id, result in (
                ("X", x_result),
                ("Z", z_result),
                ("CS", cs_result),
            ):
                repaired = list(
                    getattr(result, "_schema_repaired_fields", [])
                )
                incomplete = list(
                    getattr(result, "_schema_incomplete_fields", [])
                )
                if repaired or incomplete:
                    schema_diagnostics[agent_id] = {
                        "repaired_fields": repaired,
                        "incomplete_fields": incomplete,
                    }

            # Step 4: Create Trinity result
            trinity_result = create_trinity_result(
                concept_name=concept_name,
                concept_description=concept_description,
                x_result=x_result,
                z_result=z_result,
                cs_result=cs_result
            )

            # Save to history if requested
            if save_to_history:
                history = load_validation_history()
                history_entry = trinity_result.model_dump()
                for result_key, agent_id, quality in (
                    ("x_analysis", "X", x_quality),
                    ("z_analysis", "Z", z_quality),
                    ("cs_analysis", "CS", cs_quality),
                ):
                    if quality != "real":
                        history_entry[result_key] = {
                            "agent": agent_id,
                            "withheld": True,
                            "inference_quality": quality,
                        }
                history["validations"].append(history_entry)
                history["metadata"]["total_validations"] = len(history["validations"])
                history["metadata"]["last_updated"] = str(trinity_result.completed_at)
                save_validation_history(history)

            # BYOK metadata for response
            _stage_results = {"X": x_result, "Z": z_result, "CS": cs_result}
            _byok_meta = {
                "_byok": any(byok_status.values()),
                "_byok_agents": byok_status,
                # WP-B: names the provider that ACTUALLY served each stage
                # (identical to the resolved provider unless a runtime hop ran)
                "_providers_used": {
                    aid: actual_provider_used(_stage_results[aid], resolved_providers[aid])
                    for aid in ("X", "Z", "CS")
                },
            }
            _byok_meta.update(trinity_failover_meta(_stage_results))

            # Return result — Markdown-first if requested (v0.4.1)
            if output_format == "markdown":
                from .reporting import generate_markdown_report
                md_payload = {
                    "format": "markdown",
                    "content": generate_markdown_report(trinity_result),
                    "validation_id": trinity_result.validation_id,
                    "saved_to_history": save_to_history,
                    "_agent_chain_status": chain_status,
                    "_overall_quality": overall_quality,
                    "_schema_diagnostics": schema_diagnostics,
                    "_z_token_monitor": z_token_monitor,
                    **_byok_meta,
                    **session.to_metadata(),
                }
                if overall_quality != "full":
                    md_payload["_warning"] = (
                        trinity_result.synthesis.inference_warning
                        or MOCK_MODE_WARNING
                    )
                persist_trinity_result(user_uuid, "run_full_trinity", md_payload)
                return wrap_response(md_payload)

            payload = {
                "validation_id": trinity_result.validation_id,
                "concept_name": concept_name,
                "x_analysis": {
                    "innovation_score": (
                        x_result.innovation_score if x_quality == "real" else None
                    ),
                    "strategic_value": (
                        x_result.strategic_value if x_quality == "real" else None
                    ),
                    "recommendation": (
                        x_result.recommendation if x_quality == "real" else None
                    ),
                    "confidence": (
                        x_result.confidence if x_quality == "real" else None
                    ),
                    "research_prompts": (
                        getattr(x_result, 'research_prompts', None)
                        if x_quality == "real" else None
                    ),
                },
                "z_analysis": {
                    "ethics_score": (
                        z_result.ethics_score if z_quality == "real" else None
                    ),
                    "z_protocol_compliance": (
                        z_result.z_protocol_compliance
                        if z_quality == "real" else None
                    ),
                    "veto_triggered": (
                        z_result.veto_triggered if z_quality == "real" else None
                    ),
                    "recommendation": (
                        z_result.recommendation if z_quality == "real" else None
                    ),
                    "confidence": (
                        z_result.confidence if z_quality == "real" else None
                    )
                },
                "cs_analysis": {
                    "security_score": (
                        cs_result.security_score if cs_quality == "real" else None
                    ),
                    "vulnerability_count": (
                        len(cs_result.vulnerabilities)
                        if cs_quality == "real" else None
                    ),
                    "recommendation": (
                        cs_result.recommendation if cs_quality == "real" else None
                    ),
                    "confidence": (
                        cs_result.confidence if cs_quality == "real" else None
                    )
                },
                "synthesis": {
                    "overall_score": trinity_result.synthesis.overall_score,
                    "recommendation": trinity_result.synthesis.recommendation,
                    "veto_triggered": trinity_result.synthesis.veto_triggered,
                    "strengths": trinity_result.synthesis.strengths[:3],
                    "concerns": trinity_result.synthesis.concerns[:3],
                    "confidence": trinity_result.synthesis.confidence,
                    "confidence_valid": trinity_result.synthesis.confidence_valid,
                    "analysis_incomplete": trinity_result.synthesis.analysis_incomplete,
                    "degraded_agents": trinity_result.synthesis.degraded_agents,
                    "quality_gate": trinity_result.synthesis.quality_gate,
                    "founder_summary": getattr(trinity_result.synthesis, 'founder_summary', None),
                    "inference_warning": getattr(trinity_result.synthesis, 'inference_warning', None),
                },
                "human_decision_required": True,
                "saved_to_history": save_to_history,
                "_agent_chain_status": chain_status,
                "_overall_quality": overall_quality,
                "_schema_diagnostics": schema_diagnostics,
                "_z_token_monitor": z_token_monitor,
                **_byok_meta,
                **session.to_metadata(),
            }
            # v0.5.44: attach the auditable reasoning block (additive). "summary"
            # callers opt out and receive the exact pre-0.5.44 shape.
            if detail in ("standard", "full"):
                from .utils.reasoning_view import build_reasoning_block
                payload["reasoning"] = build_reasoning_block(
                    x_result, z_result, cs_result,
                    chain_status, overall_quality,
                    getattr(trinity_result.synthesis, 'inference_warning', None),
                    detail,
                )
            if overall_quality != "full":
                payload["_warning"] = (
                    trinity_result.synthesis.inference_warning
                    or MOCK_MODE_WARNING
                )
            persist_trinity_result(user_uuid, "run_full_trinity", payload)
            return wrap_response(payload)

        except (FailoverExhaustedError, FailoverTerminalError) as e:
            # B-90-8: hosted-lane typed contract — distinct from BYOK_AUTH_FAILED
            # below (BYOK providers never enter the failover executor).
            return wrap_response(failover_error_payload(e, "Trinity", concept_name))
        except Exception as e:
            err_str = str(e).lower()
            # Detect BYOK authentication failures for targeted recovery hints
            if "401" in err_str or "invalid api key" in err_str or "authentication" in err_str:
                return wrap_response(build_error_response(
                    error_code="BYOK_AUTH_FAILED",
                    message="API key authentication failed.",
                    recovery_hint=(
                        "Check your api_key is valid and matches the llm_provider. "
                        "Get a free Groq key at console.groq.com or omit api_key to use server defaults."
                    ),
                    agent="Trinity",
                    original_error=e,
                ))
            elif "timeout" in err_str or "timed out" in err_str:
                return wrap_response(build_error_response(
                    error_code="PROVIDER_TIMEOUT",
                    message="The LLM provider timed out.",
                    recovery_hint=(
                        "The LLM provider took too long. Try again, or switch to a faster provider "
                        "(e.g. llm_provider='groq' for low-latency inference)."
                    ),
                    agent="Trinity",
                    original_error=e,
                ))
            else:
                return wrap_response(build_error_response(
                    error_code="TRINITY_ERROR",
                    message="The Trinity analysis could not be completed.",
                    recovery_hint="Try again. If the issue persists, omit BYOK params to use server defaults.",
                    agent="Trinity",
                    original_error=e,
                ))

    # ===== v0.4.0 TEMPLATE TOOLS =====

    @app.tool()
    async def list_prompt_templates(
        agent_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[str] = None,
        user_uuid: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        List available prompt templates with optional filtering.

        v0.4.0 Unified Prompt Templates feature.

        Args:
            agent_id: Filter by agent (X, Z, CS, or 'all')
            category: Filter by category (startup, security, ethics, etc.)
            tags: Comma-separated tags to filter by (e.g., 'genesis:phase-1,default')

        Returns:
            List of templates with metadata
        """
        if user_uuid:
            emit_tracer(user_uuid, "list_prompt_templates")
        try:
            from .templates import TemplateRegistry

            registry = TemplateRegistry()

            # Parse tags if provided
            tag_list = None
            if tags:
                tag_list = [t.strip() for t in tags.split(',')]

            templates = registry.list_templates(
                agent_id=agent_id,
                category=category,
                tags=tag_list,
                include_custom=False,
            )

            return wrap_response({
                "count": len(templates),
                "filters": {
                    "agent_id": agent_id,
                    "category": category,
                    "tags": tag_list
                },
                "templates": [
                    {
                        "template_id": t.template_id,
                        "name": t.name,
                        "agent_id": t.agent_id,
                        "category": t.category,
                        "version": t.version,
                        "tags": t.tags,
                        "description": t.description,
                        "variable_count": len(t.variables)
                    }
                    for t in templates
                ]
            })

        except Exception:
            return wrap_response({
                "status": "error",
                "error": TEMPLATE_READ_UNAVAILABLE
            })

    @app.tool()
    async def get_prompt_template(
        template_id: str,
        include_content: bool = True,
        user_uuid: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Get a specific prompt template by ID.

        v0.4.0 Unified Prompt Templates feature.

        Args:
            template_id: Unique template identifier
            include_content: Whether to include full template content

        Returns:
            Complete template with all metadata and variables
        """
        if user_uuid:
            emit_tracer(user_uuid, "get_prompt_template")
        try:
            from .templates import TemplateRegistry

            registry = TemplateRegistry()
            template = registry.get_template(template_id, include_custom=False)

            if not template:
                return wrap_response({
                    "status": "not_found",
                    "error": f"Template not found: {template_id}",
                    "available_templates": len(
                        registry.list_templates(include_custom=False)
                    )
                })

            result = {
                "template_id": template.template_id,
                "name": template.name,
                "agent_id": template.agent_id,
                "category": template.category,
                "version": template.version,
                "tags": template.tags,
                "description": template.description,
                "variables": [
                    {
                        "name": v.name,
                        "type_hint": v.type_hint,
                        "required": v.required,
                        "default": v.default,
                        "description": v.description
                    }
                    for v in template.variables
                ],
                "compatible_providers": template.compatible_providers,
                "recommended_temperature": template.recommended_temperature,
                "recommended_max_tokens": template.recommended_max_tokens,
                "changelog": template.changelog
            }

            if include_content:
                result["content"] = template.content

            return wrap_response(result)

        except Exception:
            return wrap_response({
                "status": "error",
                "error": TEMPLATE_READ_UNAVAILABLE
            })

    @app.tool()
    async def export_prompt_template(
        template_id: str,
        format: str = "markdown",
        user_uuid: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Export a prompt template to Markdown or JSON format.

        v0.4.0 Unified Prompt Templates feature.

        Args:
            template_id: Template to export
            format: Export format ('markdown' or 'json')

        Returns:
            Exported template content in specified format
        """
        if user_uuid:
            emit_tracer(user_uuid, "export_prompt_template")
        try:
            from .templates import (
                TemplateRegistry,
                export_template_markdown,
                export_template_json,
            )

            registry = TemplateRegistry()
            template = registry.get_template(template_id, include_custom=False)

            if not template:
                return wrap_response({
                    "status": "not_found",
                    "error": f"Template not found: {template_id}"
                })

            format_lower = format.lower()
            if format_lower == "markdown" or format_lower == "md":
                exported = export_template_markdown(template)
                content_type = "text/markdown"
            elif format_lower == "json":
                exported = export_template_json(template)
                content_type = "application/json"
            else:
                return wrap_response({
                    "status": "error",
                    "error": f"Unsupported format: {format}. Use 'markdown' or 'json'"
                })

            return wrap_response({
                "template_id": template_id,
                "format": format_lower,
                "content_type": content_type,
                "exported_content": exported,
                "template_name": template.name,
                "template_version": template.version
            })

        except Exception:
            return wrap_response({
                "status": "error",
                "error": TEMPLATE_READ_UNAVAILABLE
            })

    @app.tool()
    async def register_custom_template(
        name: str,
        agent_id: str,
        content: str,
        category: str = "custom",
        description: Optional[str] = None,
        tags: Optional[str] = None,
        user_uuid: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Register a new custom prompt template.

        v0.4.0 Unified Prompt Templates feature.

        Args:
            name: Template display name
            agent_id: Target agent (X, Z, CS, or 'all')
            content: Template content with {variable} placeholders
            category: Template category (default: 'custom')
            description: Template description
            tags: Comma-separated tags

        Returns:
            Registered template info with generated ID
        """
        return _template_mutation_contained("register_custom_template")

    @app.tool()
    async def import_template_from_url(
        url: str,
        validate: bool = True,
        user_uuid: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Import a prompt template from a URL (GitHub Gist, raw file, etc.).

        v0.4.0 Unified Prompt Templates feature.

        Supports:
        - GitHub Gist URLs
        - Raw GitHub file URLs
        - Any HTTPS URL pointing to JSON/YAML template

        Args:
            url: URL to import template from
            validate: Whether to validate template content (default: True)

        Returns:
            Import result with template info or error details
        """
        return _template_mutation_contained("import_template_from_url")

    @app.tool()
    async def get_template_statistics(
        user_uuid: Optional[str] = None,
        ctx: Context = None
    ) -> dict:
        """
        Get statistics about the template registry.

        v0.4.0 Unified Prompt Templates feature.

        Returns:
            Statistics including template counts by agent, phase, and type
        """
        if user_uuid:
            emit_tracer(user_uuid, "get_template_statistics")
        try:
            from .templates import TemplateRegistry

            registry = TemplateRegistry()
            stats = registry.get_statistics(include_custom=False)

            # Add library info
            libraries = registry.list_libraries()

            return wrap_response({
                "status": "success",
                **stats,
                "libraries": [
                    {
                        "library_id": lib.library_id,
                        "name": lib.name,
                        "template_count": len(lib.templates),
                        "genesis_phase": lib.genesis_phase
                    }
                    for lib in libraries
                ]
            })

        except Exception:
            return wrap_response({
                "status": "error",
                "error": TEMPLATE_READ_UNAVAILABLE
            })

    # ===== v0.5.11 COORDINATION TOOLS — CONTAINED (VM-IR-2026-07-28-COORD-01) =====
    #
    # P0 containment. These three handlers previously resolved a CALLER-SUPPLIED
    # `pioneer_key` string into a storage namespace, defaulting to the shared
    # literal "anonymous" when the argument was omitted or blank. Any anonymous
    # internet caller could therefore read full handoff bodies, agent identities,
    # pending actions, and blockers written by anyone else who omitted the key —
    # and could write records under an arbitrary `agent_id` into the same shared
    # state that AI agents consume as authoritative coordination truth.
    #
    # Root cause (T S111 RC-1..RC-3): free ACCESS was implemented as unauthenticated
    # SHARED DATA. The invariant we violated:
    #
    #     Free access to a tool does not imply shared access to the data
    #     created through that tool.
    #
    # A supplied key was never an authorization boundary either: `check_tier()` was
    # called and its `allowed` result discarded, so any arbitrary string selected a
    # namespace. Bearer-string obscurity is not authenticated isolation, so
    # containment denies EVERY caller — keyed or keyless — rather than preserving an
    # undocumented compatibility path (T D-111-2/D-111-5).
    #
    # The tools remain registered so the published tool contract and manifests stay
    # truthful about the surface's existence; they return a stable, non-reflecting
    # maintenance denial that stores nothing, reads nothing, and echoes no caller
    # input. Re-enablement is gated on server-derived ownership, owner-scoped
    # storage, an adversarial isolation matrix, independent CS + T review, and
    # explicit Alton authorization (T D-111-9).
    COORDINATION_CONTAINMENT_INCIDENT = "VM-IR-2026-07-28-COORD-01"

    def _coordination_contained(tool_name: str) -> dict:
        """Stable fail-closed denial for every contained coordination handler.

        Deliberately reflects NO caller-supplied value (no key, no agent_id, no
        namespace) and exposes no stored state, so the denial itself cannot be
        used to probe the affected namespaces.
        """
        # V-6 (external validation, 2026-07-29): the ambient SYSTEM_NOTICE
        # advertises "All 13 tools free forever". Emitting it inside THIS
        # payload put a product claim and its own falsification in one JSON
        # object — a caller reading the denial saw the service assert
        # availability it was simultaneously refusing. The notice is a
        # marketing surface and has no business on a denial, so it is dropped
        # here rather than reworded: a response that says no should say only
        # that, plus how to proceed. `_server_version` is kept because a
        # caller diagnosing the denial legitimately needs it.
        contained = wrap_response(build_error_response(
            error_code="COORDINATION_TEMPORARILY_DISABLED",
            message=(
                "The coordination layer is temporarily disabled while its access "
                "control is rebuilt. Records created through this tool were stored "
                "in a shared, unauthenticated namespace; they are no longer "
                "readable or writable through the public API. No other VerifiMind "
                "tool is affected, and validation tools remain fully available."
            ),
            recovery_hint=(
                "Keep coordination state in your own repository (the handoff "
                "markdown format is documented at "
                "https://github.com/creator35lwb-web/VerifiMind-PEAS). This tool "
                "will return only after private, owner-scoped storage ships. "
                f"Incident reference: {COORDINATION_CONTAINMENT_INCIDENT}."
            ),
            agent=tool_name,
        ))
        contained.pop("_system_notice", None)
        return contained

    @app.tool()
    async def coordination_handoff_create(
        agent_id: str,
        session_type: str,
        completed: list,
        decisions: list,
        artifacts: list,
        pending: list,
        blockers: list,
        pioneer_key: Optional[str] = None,
        next_agent: Optional[str] = None,
        ctx: Context = None,
    ) -> dict:
        """
        Create a structured MACP v2.5 handoff record.

        TEMPORARILY DISABLED — this tool is contained pending a security repair
        (incident VM-IR-2026-07-28-COORD-01) and always returns a denial.

        Handoff bodies written through this tool were stored in a shared namespace
        that any unauthenticated caller could read. Nothing is stored or returned
        while containment is in force. Coordination state belongs in your own
        repository until private, owner-scoped storage ships.

        All arguments are accepted for schema stability and are ignored; no
        supplied value is stored, logged, or echoed back.

        Returns:
            A COORDINATION_TEMPORARILY_DISABLED error with an incident reference.
        """
        return _coordination_contained("coordination_handoff_create")

    @app.tool()
    async def coordination_handoff_read(
        pioneer_key: Optional[str] = None,
        agent_id: Optional[str] = None,
        count: int = 1,
        ctx: Context = None,
    ) -> dict:
        """
        Read the most recent coordination handoff record(s).

        TEMPORARILY DISABLED — this tool is contained pending a security repair
        (incident VM-IR-2026-07-28-COORD-01) and always returns a denial.

        This read path returned complete handoff bodies from a caller-selected
        namespace with no authenticated ownership check. It is closed to every
        caller — with or without a key — while owner-scoped access control is
        rebuilt. No record body is returned.

        All arguments are accepted for schema stability and are ignored.

        Returns:
            A COORDINATION_TEMPORARILY_DISABLED error with an incident reference.
        """
        return _coordination_contained("coordination_handoff_read")

    @app.tool()
    async def coordination_team_status(
        pioneer_key: Optional[str] = None,
        ctx: Context = None,
    ) -> dict:
        """
        Return current team coordination state and session summary.

        TEMPORARILY DISABLED — this tool is contained pending a security repair
        (incident VM-IR-2026-07-28-COORD-01) and always returns a denial.

        This summary exposed agent identities, pending actions, open blockers, and
        a timestamped activity index from a caller-selected namespace with no
        authenticated ownership check — enough to enumerate a namespace before
        reading it. It is closed to every caller while owner-scoped access control
        is rebuilt.

        All arguments are accepted for schema stability and are ignored.

        Returns:
            A COORDINATION_TEMPORARILY_DISABLED error with an incident reference.
        """
        return _coordination_contained("coordination_team_status")

    return app


def create_http_server():
    """Create MCP server for HTTP deployment.

    Returns raw FastMCP instance without Smithery wrapper.
    This allows using .http_app() for HTTP/SSE transport.

    Returns:
        FastMCP: Server instance that can be mounted in FastAPI.
    """
    return _create_mcp_instance()


def create_server():
    """Create MCP server instance.

    Smithery free hosting ended March 1, 2026. GCP Cloud Run via streamable-HTTP
    is the primary deployment target. This function is kept for backward compatibility
    with any tooling that calls create_server() directly.

    Returns:
        FastMCP: Server instance.
    """
    return _create_mcp_instance()


# Entry point for direct execution
if __name__ == "__main__":
    # For local testing
    
    print("=" * 60)
    print("Genesis Context Server - Phase 2 (Core Tools)")
    print("=" * 60)
    print("\nTesting resource loading...\n")
    
    # Test Master Prompt loading
    print("1. Testing Master Prompt loading...")
    prompt = load_master_prompt()
    print(f"   ✓ Loaded {len(prompt)} characters")
    print(f"   First 100 chars: {prompt[:100]}...")
    
    # Test validation history loading
    print("\n2. Testing validation history loading...")
    history = load_validation_history()
    print(f"   ✓ Loaded {len(history.get('validations', []))} validations")
    
    # Test latest validation
    print("\n3. Testing latest validation retrieval...")
    latest = get_latest_validation()
    print(f"   ✓ Latest validation status: {latest.get('status', 'N/A')}")
    
    # Test project info
    print("\n4. Testing project info retrieval...")
    info = get_project_info()
    print(f"   ✓ Project: {info['project_name']}")
    print(f"   ✓ Methodology: {info['methodology']}")
    print(f"   ✓ Version: {info['version']}")
    print(f"   ✓ MCP Server Version: {info['mcp_server_version']}")
    
    print("\n" + "=" * 60)
    print("Resources and Tools available:")
    print("=" * 60)
    print("\nResources:")
    print("  - genesis://config/master_prompt")
    print("  - genesis://history/latest")
    print("  - genesis://history/all")
    print("  - genesis://state/project_info")
    print("\nTools:")
    print("  - consult_agent_x(concept_name, concept_description, context)")
    print("  - consult_agent_z(concept_name, concept_description, context, prior_reasoning)")
    print("  - consult_agent_cs(concept_name, concept_description, context, prior_reasoning)")
    print("  - run_full_trinity(concept_name, concept_description, context, save_to_history)")
    print("\n" + "=" * 60)
    print("All tests passed! Server is ready.")
    print("=" * 60)
    print("\nTo run the MCP server:")
    print("  python -m verifimind_mcp.server")
    print("\nTo configure Claude Desktop:")
    print("  See examples/claude_desktop_config.json")
    print("=" * 60)
