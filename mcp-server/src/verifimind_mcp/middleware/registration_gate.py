"""Registration-auth gate for MCP tool EXECUTION — dark by default.

Free tools stay free. When ACTIVE, the four execution tools require a
registered UUID presented via the ``X-VerifiMind-UUID`` header (the same
header every issued mcp_config already sends). Discovery — the MCP
handshake, ``tools/list``, template reads, and every HTTP page — stays
anonymous.

ACTIVATION CONTRACT
-------------------
``REGISTRATION_GATE_ENABLED`` (env) defaults OFF. While off, this middleware
passes every call through untouched — runtime behavior is identical to the
ungated server. The flip is a human configuration action taken on/after the
published policy effective date; no code path activates the gate on its own.

SECURITY CONTRACT
-----------------
- Identity is the HTTP header, verified server-side against the registration
  store (``resolve_registration``). The caller-typed ``user_uuid`` tool
  argument is diagnostics, never authorization.
- Verification FAILS CLOSED: if the registration store cannot be consulted,
  the call is denied with a retryable ``REGISTRATION_CHECK_UNAVAILABLE`` —
  an outage never becomes an open gate.
- ``tool_denied`` events never carry the caller's string: unverified input
  must not become a log label. ``tool_authorized`` carries the UUID only
  after it verified as a registered, active identity.
- Denials are in-band structured tool errors (the same shape handlers
  return); registration is FREE and the denial copy says so — this is an
  attribution gate, not a paywall.
"""

import json
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

from fastmcp.server.middleware import Middleware
from fastmcp.tools.tool import ToolResult

from verifimind_mcp.registration_lookup import (
    REGISTERED,
    UNAVAILABLE,
    resolve_registration,
)
from verifimind_mcp.utils.uuid_tracer import is_valid_uuid

# The execution/inference tools named by the product decision ("consult +
# Trinity"). Template reads stay anonymous (discovery-class, no inference);
# the quarantined tools stay fail-closed for every caller regardless of this
# gate — registration never unlocks a contained surface.
GATED_TOOL_NAMES = frozenset({
    "consult_agent_x",
    "consult_agent_z",
    "consult_agent_cs",
    "run_full_trinity",
})

UUID_HEADER = "x-verifimind-uuid"

REGISTER_URL = "https://verifimind.ysenseai.org/register"
SETUP_URL = "https://verifimind.ysenseai.org/setup"
WHOAMI_URL = "https://verifimind.ysenseai.org/whoami"

DENIAL_REGISTRATION_REQUIRED = "registration_required"
DENIAL_CHECK_UNAVAILABLE = "registration_check_unavailable"

# Verified identity for the current tools/call, set ONLY after the header
# UUID resolved as registered-active. Downstream emitters read it to join
# telemetry to the authenticated identity; it is never derived from tool
# arguments.
VERIFIED_REGISTERED_UUID: ContextVar[Optional[str]] = ContextVar(
    "verified_registered_uuid", default=None
)


def registration_gate_enabled() -> bool:
    """Read the activation flag. Default OFF — activation is a human action."""
    return os.getenv("REGISTRATION_GATE_ENABLED", "false").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _request_header_uuid() -> str:
    """Return the X-VerifiMind-UUID header for the current request, or "".

    Uses the supported fastmcp HTTP dependency. Outside an HTTP request
    (in-process clients, stdio) there is no header, which reads as "absent"
    — the gate then denies rather than guessing (fail closed).
    """
    try:
        from fastmcp.server.dependencies import get_http_headers

        headers = get_http_headers() or {}
        return str(headers.get(UUID_HEADER, "")).strip()
    except Exception:
        return ""


def _emit_gate_event(payload: dict) -> None:
    print(json.dumps(payload), file=sys.stderr, flush=True)


def emit_tool_authorized(tool_name: str, registered_uuid: str) -> None:
    """One event per authorized gated call — the Registered tool-use signal.

    The UUID here is server-verified against the registration store, so the
    label cardinality is bounded by the consented registration set, never by
    caller-controlled input.
    """
    _emit_gate_event({
        "severity": "INFO",
        "event": "tool_authorized",
        "tool": tool_name,
        "registered_uuid": registered_uuid,
    })


def emit_tool_denied(tool_name: str, reason: str) -> None:
    """One event per denied gated call. Deliberately carries NO identifier:
    an unverified caller string must not become a log label."""
    _emit_gate_event({
        "severity": "INFO",
        "event": "tool_denied",
        "tool": tool_name,
        "reason": reason,
    })


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _denial_payload(tool_name: str, uuid_status: str) -> dict:
    """Structured REGISTRATION_REQUIRED denial. Free-registration CTA only —
    no paid-tier language exists or may appear here."""
    if uuid_status == "invalid":
        hint = (
            "A VerifiMind UUID header was received but is not a valid UUID. "
            "Check that VERIFIMIND_UUID in your MCP config is set to your real "
            f"UUID (not a placeholder). Setup help: {SETUP_URL}"
        )
    elif uuid_status == "unregistered":
        hint = (
            "This UUID is not a registered identity (or its registration was "
            f"closed). Check {WHOAMI_URL}, or register free in under a minute "
            f"at {REGISTER_URL} — all gated tools remain free after "
            "registration."
        )
    else:  # absent
        hint = (
            "Registration is free and takes under a minute: get a UUID at "
            f"{REGISTER_URL}, then send it as the X-VerifiMind-UUID header "
            f"(your registration response includes a ready mcp_config; see "
            f"{SETUP_URL})."
        )
    return {
        "status": "error",
        "error_code": "REGISTRATION_REQUIRED",
        "error": (
            f"'{tool_name}' now requires a free registered UUID. "
            "Discovery, template reads, and all pages remain available "
            "without registration."
        ),
        "recovery_hint": hint,
        "register_url": REGISTER_URL,
        "setup_url": SETUP_URL,
        "retryable": False,
        "timestamp": _now_iso(),
    }


def _unavailable_payload(tool_name: str) -> dict:
    """Structured fail-closed denial for a registration-store outage."""
    return {
        "status": "error",
        "error_code": "REGISTRATION_CHECK_UNAVAILABLE",
        "error": (
            "The registration check is temporarily unavailable, so "
            f"'{tool_name}' cannot verify your UUID right now. No data was "
            "processed."
        ),
        "recovery_hint": (
            "This is a temporary server-side condition — please retry in a "
            "few minutes. Server health: https://verifimind.ysenseai.org/health"
        ),
        "retryable": True,
        "timestamp": _now_iso(),
    }


def _as_tool_result(payload: dict) -> ToolResult:
    return ToolResult(
        content=json.dumps(payload),
        structured_content=payload,
    )


class RegistrationGate(Middleware):
    """Deny gated tools/call requests that lack a verified registered UUID.

    Registered AFTER ToolInvocationTelemetry so a denied dispatch still
    emits its name-only ``tool_invoked`` event — the dispatch-attempt layer
    keeps its meaning; ``tool_authorized`` is the new authenticated layer.
    Denials happen before the handler, so a denied Trinity call emits no
    lifecycle events and never enters the completion-rate denominator.
    """

    async def on_call_tool(self, context, call_next):
        tool_name = getattr(context.message, "name", None)
        if not registration_gate_enabled() or tool_name not in GATED_TOOL_NAMES:
            return await call_next(context)

        uuid = _request_header_uuid()
        if not uuid:
            emit_tool_denied(tool_name, DENIAL_REGISTRATION_REQUIRED)
            return _as_tool_result(_denial_payload(tool_name, "absent"))
        if not is_valid_uuid(uuid):
            emit_tool_denied(tool_name, DENIAL_REGISTRATION_REQUIRED)
            return _as_tool_result(_denial_payload(tool_name, "invalid"))

        state = resolve_registration(uuid)
        if state.state == UNAVAILABLE:
            emit_tool_denied(tool_name, DENIAL_CHECK_UNAVAILABLE)
            return _as_tool_result(_unavailable_payload(tool_name))
        if state.state != REGISTERED:
            emit_tool_denied(tool_name, DENIAL_REGISTRATION_REQUIRED)
            return _as_tool_result(_denial_payload(tool_name, "unregistered"))

        emit_tool_authorized(tool_name, uuid)
        token = VERIFIED_REGISTERED_UUID.set(uuid)
        try:
            return await call_next(context)
        finally:
            VERIFIED_REGISTERED_UUID.reset(token)
