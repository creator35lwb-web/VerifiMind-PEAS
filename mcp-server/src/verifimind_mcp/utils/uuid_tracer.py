"""
UUID Tracer — v0.5.15 Scholar Incentives

Validates Scholar UUIDs and emits structured TRACER lines to stdout for
AY analytics pipeline (Cloud Run stdout → jsonPayload → BigQuery).

Security: UUID is validated before logging. Invalid format is silently
ignored — no error raised, no log entry, no response change.

Existing TRACER pattern (v0.5.12 Pioneer tools):
    TRACER_UUID: {pioneer_key} tool=coordination_handoff_create
Extended here for Scholar tools:
    TRACER_UUID: {uuid} tool={tool} tier=scholar
"""

import re
import logging

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
    """Emit structured TRACER line if uuid is a valid UUID format.

    Called from Scholar tool handlers when user_uuid is provided.
    Silently returns without logging if uuid fails format validation.
    Does NOT verify that the UUID is registered — only format-checks.

    Args:
        uuid: The user_uuid value from the tool call parameter.
        tool: The MCP tool name (e.g. "consult_agent_x").
    """
    if not is_valid_uuid(uuid):
        return
    safe_uuid = uuid.strip()
    print(f"TRACER_UUID: {safe_uuid} tool={tool} tier=scholar", flush=True)
    logger.debug("UUID tracer emitted: tool=%s uuid_prefix=%s", tool, safe_uuid[:8])
