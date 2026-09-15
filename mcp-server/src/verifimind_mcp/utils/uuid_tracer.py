"""
UUID Tracer — v0.5.15 Scholar Incentives (contained)

The compatibility entry point and format validator remain available, but
caller-supplied UUID attribution is disabled during the legacy identity
incident. A UUID is not authenticated ownership evidence.

Security: UUID is validated before logging. Invalid format is silently
ignored — no error raised, no log entry, no response change.

Existing TRACER pattern (v0.5.12 Pioneer tools):
    TRACER_UUID: {pioneer_key} tool=coordination_handoff_create
Extended here for Scholar tools:
    TRACER_UUID: {uuid} tool={tool} tier=scholar
"""

import re
import logging

from verifimind_mcp.security_containment import TRUST_UNAUTHENTICATED_UUID_INPUT

logger = logging.getLogger(__name__)

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def is_valid_uuid(value: str) -> bool:
    """Return True if value is a well-formed UUID (any version)."""
    if not value or not isinstance(value, str):
        return False
    return bool(_UUID_RE.match(value.strip()))


def emit_tracer(uuid: str, tool: str) -> None:
    """Compatibility tracer, fail-closed until UUID ownership is authenticated.

    Called from Scholar tool handlers when user_uuid is provided.
    During containment this always returns without logging. The historical
    implementation below additionally validates format, but format validity is
    never treated as proof that the caller controls that UUID.

    Args:
        uuid: The user_uuid value from the tool call parameter.
        tool: The MCP tool name (e.g. "consult_agent_x").
    """
    # A caller-supplied UUID is not authenticated account ownership. Retain the
    # argument for MCP schema compatibility but do not attribute logs until the
    # OAuth subject-binding replacement is active.
    if not TRUST_UNAUTHENTICATED_UUID_INPUT:
        return
    if not is_valid_uuid(uuid):
        return
    safe_uuid = uuid.strip()
    print(f"TRACER_UUID: {safe_uuid} tool={tool} tier=scholar", flush=True)
    logger.debug("UUID tracer emitted: tool=%s uuid_prefix=%s", tool, safe_uuid[:8])
