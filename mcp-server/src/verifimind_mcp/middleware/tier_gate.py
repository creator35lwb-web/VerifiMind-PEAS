"""
Tier-Gating Middleware — v0.5.11 Coordination Foundation
=========================================================

Separates Scholar (free) from Pioneer (paid) tool access.

Tier definitions:
  Scholar  — all 10 free Trinity + template tools. No coordination tools.
  Pioneer  — all Scholar tools + 6 coordination tools ($9/month, future Stripe).

Phase 1 validation: PIONEER_ACCESS_KEYS env var (comma-separated valid keys).
Phase 2 (v0.5.13+): Replace _validate_pioneer_key() with Stripe customer lookup.

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

def check_tier(pioneer_key: str | None) -> Tuple[bool, str]:
    """Return (allowed, tier_name) for the given key.

    Phase 1: validates against PIONEER_ACCESS_KEYS env var.
    Phase 2 hook: swap _validate_pioneer_key() for Stripe lookup — caller stays unchanged.

    Args:
        pioneer_key: Key provided by the user (or None / empty string).

    Returns:
        (True, "pioneer")  — access granted
        (False, "scholar") — access denied (Scholar tier or invalid key)
    """
    if not pioneer_key or not pioneer_key.strip():
        return False, TIER_SCHOLAR

    if _validate_pioneer_key(pioneer_key.strip()):
        logger.debug("Tier check: PIONEER granted")
        return True, TIER_PIONEER

    logger.warning("Tier check: invalid pioneer_key presented — SCHOLAR fallback")
    return False, TIER_SCHOLAR


def _validate_pioneer_key(key: str) -> bool:
    """Validate a pioneer key.

    Phase 1: env var lookup.
    Phase 2 (v0.5.13): replace body with Stripe subscription check.
    """
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

    Phase 1: pass-through stub — patterns are defined but not applied.
    Phase 2 (v0.5.13): uncomment the loop below to activate.
    Security requirement: Z Guardian Section 4.3, Architecture v1.2.

    Args:
        content: Raw handoff markdown content.

    Returns:
        Sanitized content (Phase 1: unchanged).
    """
    # --- Phase 2 activation point ---
    # for pattern in _SECRET_PATTERNS:
    #     content = pattern.sub("[REDACTED]", content)
    return content
