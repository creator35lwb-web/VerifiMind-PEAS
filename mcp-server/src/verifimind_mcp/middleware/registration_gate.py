"""Execution gate + evidence events for gated tools — dark by default (v2).

Design v2 split (T S152/S153): the HTTP boundary (mcp_auth_boundary)
authenticates OAuth/PAT credentials and resolves the subject; THIS
middleware enforces per-tool semantics and emits the evidence ladder:

  tool_invoked    dispatch attempt (v0.5.62 name-only contract, unchanged)
  tool_admitted   authenticated attempt admitted for a gated tool — proves
                  admission only, never completion or value (T P0 #8)
  tool_completed  terminal server completion with success/quality/actor —
                  the external-value evidence unit
  tool_denied     denied gated attempt; carries NO caller-supplied input

Identity rules (T P0 #5/#6): the authenticated subject comes only from the
boundary contextvar; the ``user_uuid`` tool argument confers nothing and a
mismatch with the authenticated subject FAILS CLOSED. Events carry the
HMAC-pseudonymous subject — raw UUIDs never enter value telemetry.

ACTIVATION CONTRACT: ``REGISTRATION_GATE_ENABLED`` defaults OFF; while off
this middleware passes every call through untouched. The flip is a human
configuration action on/after the published policy effective date.
"""

import json
import os
import sys
import uuid as _uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

from fastmcp.server.middleware import Middleware
from fastmcp.tools.tool import ToolResult

from verifimind_mcp.oauth.subjects import derive_subject

# The execution/inference tools named by the product decision ("consult +
# Trinity"). Template reads stay anonymous at this layer; the quarantined
# tools stay fail-closed for every caller regardless of any credential —
# registration/authentication never satisfies Gate R0.
GATED_TOOL_NAMES = frozenset({
    "consult_agent_x",
    "consult_agent_z",
    "consult_agent_cs",
    "run_full_trinity",
})

REGISTER_URL = "https://verifimind.ysenseai.org/register"
PRM_URL = "https://verifimind.ysenseai.org/.well-known/oauth-protected-resource"


def _env_urls() -> tuple:
    """Environment-bound (register_url, prm_url) for denial payloads.

    CS Finding 4: the in-band denial must NOT point a staging client at the
    PRODUCTION authorization server — that mints a production-audience token
    the staging boundary then rejects, an endless lockout loop. Resolve from
    the live environment; the module constants are only a last-resort fallback
    if the environment cannot be read (a misconfigured deploy prefers the
    honest register page over a cross-environment auth server)."""
    try:
        from verifimind_mcp.oauth import config

        env = config.current_environment()
        return f"{env.origin}/register", env.prm_url
    except Exception:
        return REGISTER_URL, None

# Authenticated identity for the current request, set by the HTTP boundary
# after full token validation. Never derived from tool arguments.
AUTH_SUBJECT_UUID: ContextVar[Optional[str]] = ContextVar(
    "auth_subject_uuid", default=None
)
AUTH_ACTOR_CLASS: ContextVar[Optional[str]] = ContextVar(
    "auth_actor_class", default=None
)
# HMAC-pseudonymous subject for downstream emitters (lifecycle events).
VERIFIED_SUBJECT_HMAC: ContextVar[Optional[str]] = ContextVar(
    "verified_subject_hmac", default=None
)

DENIAL_AUTHENTICATION_REQUIRED = "authentication_required"
DENIAL_CROSS_SUBJECT = "cross_subject_mismatch"


def registration_gate_enabled() -> bool:
    """Read the activation flag. Default OFF — activation is a human action."""
    return os.getenv("REGISTRATION_GATE_ENABLED", "false").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _emit(payload: dict) -> None:
    print(json.dumps(payload), file=sys.stderr, flush=True)


def emit_tool_admitted(tool_name: str, subject: Optional[str]) -> None:
    event = {"severity": "INFO", "event": "tool_admitted", "tool": tool_name}
    if subject:
        event["subject"] = subject
    _emit(event)


def emit_tool_denied(tool_name: str, reason: str) -> None:
    """Deliberately carries NO identifier: unverified or mismatched caller
    input must never become a log label."""
    _emit({
        "severity": "INFO",
        "event": "tool_denied",
        "tool": tool_name,
        "reason": reason,
    })


def _environment_label() -> str:
    """Environment label from the OAuth env binding (T P0-8), so a staging
    service never labels its traffic as production."""
    try:
        from verifimind_mcp.oauth import config

        return config.current_environment().name
    except Exception:
        return "production" if os.getenv("K_SERVICE") else "development"


def _protocol_era() -> Optional[str]:
    """Negotiated MCP protocol revision, from the request header when the
    call arrives over HTTP (T P0-10). None outside an HTTP request."""
    try:
        from fastmcp.server.dependencies import get_http_headers

        headers = get_http_headers() or {}
        era = str(headers.get("mcp-protocol-version", "")).strip()
        return era or None
    except Exception:
        return None


def emit_tool_completed(
    tool_name: str,
    subject: Optional[str],
    *,
    success: bool,
    inference_quality: str,
    traffic_class: str,
    execution_id: str,
    route: str,
) -> None:
    event = {
        "severity": "INFO",
        "event": "tool_completed",
        "tool": tool_name,
        "success": success,
        "inference_quality": inference_quality,
        "route": route,
        "environment": _environment_label(),
        "traffic_class": traffic_class,
        "execution_id": execution_id,
    }
    era = _protocol_era()
    if era:
        event["protocol_era"] = era
    if subject:
        event["subject"] = subject
    _emit(event)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _denial_payload(tool_name: str, reason: str) -> dict:
    """Build the in-band denial payload for one admitted denial reason.

    One exhaustive ``if``/``else`` decision (T S156 gate-truth repair): both
    ``error`` and ``hint`` are bound on every path, so static analysis can
    prove initialization. Both payloads are unchanged from the prior
    two-branch form; any reason other than ``DENIAL_CROSS_SUBJECT`` resolves
    to the authentication-required payload exactly as before.
    """
    register_url, prm_url = _env_urls()
    if reason == DENIAL_CROSS_SUBJECT:
        error = (
            f"'{tool_name}' was called with a user_uuid that does not match "
            "the authenticated account. The argument confers no authority; "
            "remove it or use your own account's value."
        )
        hint = (
            "Tool-argument identity is diagnostics only. Your authenticated "
            "session already attributes this call; omit user_uuid entirely."
        )
    else:
        prm_clause = (
            f"Connect through an OAuth-capable MCP client (authorization server "
            f"in {prm_url}), or " if prm_url else "Connect through an "
            "OAuth-capable MCP client, or "
        )
        error = (
            f"'{tool_name}' requires an authenticated session. Discovery, "
            "template reads, and all pages remain available without one."
        )
        hint = (
            f"{prm_clause}register free at {register_url} and use a personal "
            "access token for local clients. All gated tools remain free after "
            "registration."
        )
    payload = {
        "status": "error",
        "error_code": (
            "CROSS_SUBJECT_MISMATCH"
            if reason == DENIAL_CROSS_SUBJECT
            else "AUTHENTICATION_REQUIRED"
        ),
        "error": error,
        "recovery_hint": hint,
        "register_url": register_url,
        "retryable": False,
        "timestamp": _now_iso(),
    }
    if prm_url:
        payload["resource_metadata"] = prm_url
    return payload


def _as_tool_result(payload: dict) -> ToolResult:
    return ToolResult(content=json.dumps(payload), structured_content=payload)


def _payload_of(result) -> Optional[dict]:
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            try:
                parsed = json.loads(text)
            except (TypeError, ValueError):
                continue
            if isinstance(parsed, dict):
                return parsed
    if isinstance(result, dict):
        return result
    return None


class RegistrationGate(Middleware):
    """Per-tool authorization semantics + the evidence event ladder.

    Registered AFTER ToolInvocationTelemetry so a denied dispatch still
    emits its name-only ``tool_invoked`` event. Denials happen before the
    handler, so a denied Trinity call emits no lifecycle events and never
    enters the completion-rate denominator.
    """

    async def on_call_tool(self, context, call_next):
        tool_name = getattr(context.message, "name", None)
        if not registration_gate_enabled() or tool_name not in GATED_TOOL_NAMES:
            return await call_next(context)

        subject_uuid = AUTH_SUBJECT_UUID.get()
        if not subject_uuid:
            emit_tool_denied(tool_name, DENIAL_AUTHENTICATION_REQUIRED)
            return _as_tool_result(
                _denial_payload(tool_name, DENIAL_AUTHENTICATION_REQUIRED)
            )

        arguments = getattr(context.message, "arguments", None) or {}
        claimed = arguments.get("user_uuid") if isinstance(arguments, dict) else None
        if claimed and str(claimed).strip() and str(claimed) != subject_uuid:
            emit_tool_denied(tool_name, DENIAL_CROSS_SUBJECT)
            return _as_tool_result(
                _denial_payload(tool_name, DENIAL_CROSS_SUBJECT)
            )

        subject = derive_subject(subject_uuid)
        traffic_class = AUTH_ACTOR_CLASS.get() or "unknown"
        execution_id = _uuid.uuid4().hex
        # Route lane (T P0-10): caller-supplied provider/key parameters mean
        # the run is BYOK; otherwise it uses hosted construction-time routing.
        route = "byok" if (
            isinstance(arguments, dict) and any(
                arguments.get(param) for param in (
                    "api_key", "x_api_key", "z_api_key", "cs_api_key",
                    "llm_provider", "x_provider", "z_provider", "cs_provider",
                )
            )
        ) else "hosted"
        emit_tool_admitted(tool_name, subject)
        token = VERIFIED_SUBJECT_HMAC.set(subject)
        try:
            result = await call_next(context)
        except Exception:
            emit_tool_completed(
                tool_name, subject,
                success=False,
                inference_quality="exception",
                traffic_class=traffic_class,
                execution_id=execution_id,
                route=route,
            )
            raise
        finally:
            VERIFIED_SUBJECT_HMAC.reset(token)

        payload = _payload_of(result)
        if payload is None:
            success, quality = False, "unparseable"
        else:
            success = payload.get("status") != "error"
            quality = str(
                payload.get("_inference_quality")
                or payload.get("_overall_quality")
                or ("real" if success else "unavailable")
            )
        emit_tool_completed(
            tool_name, subject,
            success=success,
            inference_quality=quality,
            traffic_class=traffic_class,
            execution_id=execution_id,
            route=route,
        )
        return result
