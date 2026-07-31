"""Canonical public tool-availability contract for VerifiMind-PEAS.

Keep runtime containment and every discovery surface on one exact set.  A tool
may remain registered for protocol compatibility while being fail-closed.
"""

from __future__ import annotations

import re
from typing import Any, Dict


DEFINED_TOOL_COUNT = 13

COORDINATION_TOOL_NAMES = (
    "coordination_handoff_create",
    "coordination_handoff_read",
    "coordination_team_status",
)

CUSTOM_TEMPLATE_MUTATION_TOOL_NAMES = (
    "register_custom_template",
    "import_template_from_url",
)

UNAVAILABLE_TOOL_NAMES = (
    *COORDINATION_TOOL_NAMES,
    *CUSTOM_TEMPLATE_MUTATION_TOOL_NAMES,
)

ACTIVE_TOOL_COUNT = DEFINED_TOOL_COUNT - len(UNAVAILABLE_TOOL_NAMES)

COORDINATION_MAINTENANCE_PREFIX = "TEMPORARILY UNAVAILABLE (maintenance) — "
CUSTOM_TEMPLATE_MAINTENANCE_PREFIX = "TEMPORARILY UNAVAILABLE (security maintenance) — "


def get_tool_availability() -> Dict[str, Any]:
    """Return the exact availability set projected onto public surfaces."""
    return {
        "defined": DEFINED_TOOL_COUNT,
        "active": ACTIVE_TOOL_COUNT,
        "temporarily_unavailable": len(UNAVAILABLE_TOOL_NAMES),
        "unavailable_tools": list(UNAVAILABLE_TOOL_NAMES),
        "reason": (
            "owner-scoped access-control and custom-template security maintenance"
        ),
        "reason_groups": {
            "coordination_owner_isolation": list(COORDINATION_TOOL_NAMES),
            "custom_template_isolation_and_url_fetch": list(
                CUSTOM_TEMPLATE_MUTATION_TOOL_NAMES
            ),
        },
    }


_ALL_TOOLS_CLAIM = re.compile(
    r"\b(?:all\s+(?:13\s+)?tools|13\s+tools)\b", re.IGNORECASE
)
_ACTIVE_TOOLS_CLAIM = re.compile(
    r"\b8\s+(?:active(?:\s+tools)?|tools\s+active)\b", re.IGNORECASE
)
_UNAVAILABLE_TOOLS_CLAIM = re.compile(
    r"\b5\s+(?:(?:tools\s+)?(?:temporarily\s+)?unavailable|"
    r"temporarily\s+unavailable\s+tools)\b",
    re.IGNORECASE,
)


def system_notice_is_compatible(notice: str) -> bool:
    """Reject an ambient notice that contradicts current containment truth."""
    if not notice:
        return True
    if ACTIVE_TOOL_COUNT >= DEFINED_TOOL_COUNT:
        return True
    if _ALL_TOOLS_CLAIM.search(notice) is None:
        return True
    return bool(
        _ACTIVE_TOOLS_CLAIM.search(notice)
        and _UNAVAILABLE_TOOLS_CLAIM.search(notice)
    )
