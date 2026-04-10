"""
Tier-Gating Middleware — v0.5.13 Fortify
=========================================

Separates Scholar (free) from Pioneer (paid) tool access.

Tier definitions:
  Scholar  — all 10 free Trinity + template tools. No coordination tools.
  Pioneer  — all Scholar tools + 6 coordination tools ($9/month via Polar).

Phase 1 validation: PIONEER_ACCESS_KEYS env var (comma-separated valid keys).
Phase 2 (v0.5.13+): Replace _validate_pioneer_key() with Polar customer lookup.

sanitize_handoff_content() is ACTIVE in v0.5.13 (was a stub in Phase 1).
Covers 20+ provider secret patterns (X-Agent Item 2 hardening sprint).

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

    Phase 1 fallback: PIONEER_ACCESS_KEYS env var — LOCAL DEV ONLY.
    When POLAR_ACCESS_TOKEN is set (production), any Polar failure results
    in deny access (fail-closed). Env-var fallback is NEVER used in production.

    Fail-closed scenarios (production):
      - CircuitOpenError (5 consecutive Polar failures in 60s) → deny
      - Any other Polar exception → deny
    """
    from .polar_adapter import get_polar_adapter, CircuitOpenError
    adapter = get_polar_adapter()
    if adapter is not None:
        # POLAR_ACCESS_TOKEN is set — production mode, fail-closed on any error
        try:
            return await adapter.check_pioneer_access(key)
        except CircuitOpenError as e:
            logger.error(
                "Polar circuit open for key %s…: %s — fail-closed (denying Pioneer access)",
                key[:8], e,
            )
            return False
        except Exception as e:
            logger.error(
                "Polar tier check error for key %s…: %s — fail-closed (production mode, denying access)",
                key[:8], e,
            )
            return False
    # No POLAR_ACCESS_TOKEN → local dev mode → env-var fallback
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
# Handoff sanitization — ACTIVE in v0.5.13 (X-Agent Item 2, 20+ providers)
# ---------------------------------------------------------------------------
#
# Provider pattern coverage (last updated: 2026-04-10, v0.5.13 hardening sprint):
#
#  Provider              Pattern prefix / structure
#  --------------------  -------------------------------------------------------
#  OpenAI                sk-[A-Za-z0-9-_]{20,}  (also matches sk-proj-...)
#  Anthropic             sk-ant-[A-Za-z0-9-_]{20,}  (subset of above)
#  Google AI / Firebase  AIza[A-Za-z0-9_-]{35}
#  GitHub PAT            ghp_[A-Za-z0-9]{36,}
#  GitHub OAuth          gho_[A-Za-z0-9]{36,}
#  GitHub Server         ghs_[A-Za-z0-9]{36,}
#  AWS Access Key ID     AKIA[A-Z0-9]{16}
#  sk_live_ secret key   sk_live_[A-Za-z0-9]{24,}
#  sk_test_ secret key   sk_test_[A-Za-z0-9]{24,}
#  pk_live_ publishable  pk_live_[A-Za-z0-9]{24,}
#  Polar                 polar_[A-Za-z0-9_]{20,}
#  Hugging Face          hf_[A-Za-z0-9]{34,}
#  Replicate             r8_[A-Za-z0-9]{40,}
#  SendGrid              SG.[A-Za-z0-9_-]{22}.[A-Za-z0-9_-]{43}
#  Twilio Auth Token     SK[a-f0-9]{32}
#  Mailgun               key-[a-f0-9]{32}
#  Slack                 xox[bpars]-[A-Za-z0-9-]{10,}
#  JWT (Supabase, etc.)  eyJ...\.eyJ...\.sig (3-segment base64url)
#  Bearer token          Bearer <token>
#  Azure subscription    ocp-apim-subscription-key / azure_key = <32 hex>
#  Generic api_key       api[_-]?key[:=]\S+
#  Generic secret        secret[:=]\S+
#  Generic token/pass    (token|password|passwd)[:=]\S{20,}
#  Generic credential    (credential|private_key|access_token)[:=]\S{20,}
#
_SECRET_PATTERNS: list[re.Pattern] = [
    # --- Dedicated prefixes (low false-positive risk) ---
    re.compile(r"sk-[A-Za-z0-9\-_]{20,}"),                         # OpenAI / Anthropic
    re.compile(r"AIza[A-Za-z0-9\-_]{35}"),                          # Google AI / Firebase
    re.compile(r"gh[pos]_[A-Za-z0-9]{36,}"),                        # GitHub PAT / OAuth / server
    re.compile(r"AKIA[A-Z0-9]{16}"),                                 # AWS Access Key ID
    re.compile(r"sk_(?:live|test)_[A-Za-z0-9]{24,}"),               # sk_live_ / sk_test_ payment secret keys
    re.compile(r"pk_live_[A-Za-z0-9]{24,}"),                         # pk_live_ payment publishable keys
    re.compile(r"polar_[A-Za-z0-9_]{20,}"),                          # Polar access token
    re.compile(r"hf_[A-Za-z0-9]{34,}"),                             # Hugging Face token
    re.compile(r"r8_[A-Za-z0-9]{40,}"),                             # Replicate token
    re.compile(r"SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}"),     # SendGrid API key
    re.compile(r"SK[a-f0-9]{32}"),                                   # Twilio auth token
    re.compile(r"key-[a-f0-9]{32}"),                                 # Mailgun API key
    re.compile(r"xox[bpars]-[A-Za-z0-9\-]{10,}"),                   # Slack tokens (bot/user/app/workspace)
    # --- JWT / Bearer ---
    re.compile(                                                       # JWT (Supabase, Firebase Auth, etc.)
        r"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"
    ),
    re.compile(r"Bearer\s+[A-Za-z0-9_\.\-]{20,}"),                  # Authorization: Bearer <token>
    # --- Context-dependent patterns ---
    re.compile(r"(?i)api[_\-]?key\s*[:=]\s*\S+"),                   # Generic api_key: value
    re.compile(r"(?i)secret\s*[:=]\s*\S+"),                          # Generic secret: value
    re.compile(r"(?i)(?:token|password|passwd)\s*[:=]\s*\S{20,}"),  # Generic token / password
    re.compile(                                                       # Azure subscription key
        r"(?i)(?:ocp-apim-subscription-key|azure[_\-]?(?:key|secret))\s*[:=]\s*[a-f0-9]{32}"
    ),
    # --- Catch-all: high-entropy strings in sensitive key contexts ---
    re.compile(
        r"(?i)(?:credential|private[_\-]?key|access[_\-]?token)\s*[:=]\s*[A-Za-z0-9+/=_\-]{20,}"
    ),
]


def sanitize_handoff_content(content: str) -> str:
    """Strip secrets from handoff content before storage.

    v0.5.13 "Fortify": ACTIVE — strips API keys and secrets before Firestore write.
    Covers 20+ provider patterns (X-Agent Item 2 hardening sprint, 2026-04-10).
    Security requirement: Z Guardian Section 4.3, Architecture v1.2.

    Args:
        content: Raw handoff markdown content.

    Returns:
        Sanitized content with secrets replaced by [REDACTED].
    """
    for pattern in _SECRET_PATTERNS:
        content = pattern.sub("[REDACTED]", content)
    return content
