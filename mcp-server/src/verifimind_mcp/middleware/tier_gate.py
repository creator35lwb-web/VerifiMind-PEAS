"""
Tier-Gating Middleware — v0.5.11 Coordination Foundation
=========================================================

Separates Scholar (free) from Pioneer (paid) tool access.

Tier definitions:
  Scholar  — all 10 free Trinity + template tools. No coordination tools.
  Pioneer  — all Scholar tools + 6 coordination tools ($9/month via Polar).

Phase 1 validation: PIONEER_ACCESS_KEYS env var (comma-separated valid keys).
Phase 2 (v0.5.12+): Replace _validate_pioneer_key() with Polar customer lookup.

Design-in for v0.5.13:
  sanitize_handoff_content() is a stub here — full secret-stripping implemented later.
  All coordination tool responses route through it so the hook is ready.

Usage:
    allowed, tier = check_tier(pioneer_key)
    if not allowed:
        return wrap_response(tier_gate_error())
"""

import os
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_PIONEER_KEYS_RAW = os.environ.get("PIONEER_ACCESS_KEYS", "")
_PIONEER_KEYS: frozenset[str] = frozenset(
    k.strip() for k in _PIONEER_KEYS_RAW.split(",") if k.strip()
)

# Tier labels
TIER_SCHOLAR = "scholar"
TIER_PIONEER = "pioneer"


# ---------------------------------------------------------------------------
# Core check
# ---------------------------------------------------------------------------

async def check_tier(pioneer_key: str | None) -> Tuple[bool, str]:
    """Return (allowed, tier_name) for the given key.

    Phase 2 (v0.5.13): calls PolarAdapter.check_pioneer_access() when
    POLAR_ACCESS_TOKEN is set. Falls back to PIONEER_ACCESS_KEYS env var
    for local dev and when Polar is not configured.

    Args:
        pioneer_key: Key provided by the user (or None / empty string).

    Returns:
        (True, "pioneer")  — access granted
        (False, "scholar") — access denied (Scholar tier or invalid key)
    """
    if not pioneer_key or not pioneer_key.strip():
        return False, TIER_SCHOLAR

    if await _validate_pioneer_key(pioneer_key.strip()):
        logger.debug("Tier check: PIONEER granted")
        return True, TIER_PIONEER

    logger.warning("Tier check: invalid pioneer_key presented — SCHOLAR fallback")
    return False, TIER_SCHOLAR


async def _validate_pioneer_key(key: str) -> bool:
    """Validate a pioneer key.

    Phase 2 (v0.5.13): queries Polar Customer State API via PolarAdapter
    when POLAR_ACCESS_TOKEN env var is set. Cancelled subscription →
    access denied after 5-minute cache expiry.

    Phase 1 fallback: PIONEER_ACCESS_KEYS env var (local dev / no Polar token).
    """
    from .polar_adapter import get_polar_adapter
    adapter = get_polar_adapter()
    if adapter is not None:
        try:
            return await adapter.check_pioneer_access(key)
        except Exception as e:
            logger.error("Polar tier check failed for key %s…: %s — falling back to env var", key[:8], e)
    return key in _PIONEER_KEYS


# ---------------------------------------------------------------------------
# Standard error response
# ---------------------------------------------------------------------------

def tier_gate_error() -> dict:
    """Structured error for Scholar users attempting Pioneer-only tools."""
    return {
        "status": "error",
        "error_code": "PIONEER_TIER_REQUIRED",
        "error": (
            "This tool requires Pioneer tier access. "
            "Pioneer tier includes all coordination tools at $9/month."
        ),
        "recovery_hint": (
            "Provide your pioneer_key parameter. "
            "Register for the Pioneer program at https://verifimind.ysenseai.org/register"
        ),
        "tier_required": TIER_PIONEER,
        "upgrade_url": "https://verifimind.ysenseai.org/register",
    }


# ---------------------------------------------------------------------------
# Handoff sanitization stub (v0.5.13 full implementation)
# ---------------------------------------------------------------------------

# Patterns that will be stripped in v0.5.13 (designed-in now, pass-through for Phase 1)
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9\-_]{20,}"),          # OpenAI / Anthropic keys
    re.compile(r"AIza[A-Za-z0-9\-_]{35}"),           # Google API keys
    re.compile(r"ghp_[A-Za-z0-9]{36}"),              # GitHub personal tokens
    re.compile(r"gho_[A-Za-z0-9]{36}"),              # GitHub OAuth tokens
    re.compile(r"(?i)api[_\-]?key\s*[:=]\s*\S+"),   # Generic api_key: value
    re.compile(r"(?i)secret\s*[:=]\s*\S+"),          # Generic secret: value
]


def sanitize_handoff_content(content: str) -> str:
    """Strip secrets from handoff content before storage.

    v0.5.13 "Fortify": ACTIVE — strips API keys and secrets before Firestore write.
    Security requirement: Z Guardian Section 4.3, Architecture v1.2.

    Args:
        content: Raw handoff markdown content.

    Returns:
        Sanitized content with secrets replaced by [REDACTED].
    """
    for pattern in _SECRET_PATTERNS:
        content = pattern.sub("[REDACTED]", content)
    return content
