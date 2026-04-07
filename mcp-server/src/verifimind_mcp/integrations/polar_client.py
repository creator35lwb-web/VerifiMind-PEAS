"""
Polar Customer State API Client — v0.5.12 Pioneer Integration
==============================================================

Queries Polar's Customer State API to determine Pioneer tier access.
Uses Polar Feature Flags as the single source of truth — the pioneer_access
flag is automatically granted when a Pioneer subscription is active and
revoked on cancellation. No custom lifecycle logic needed.

Architecture:
  PolarClient (this module)
    → PolarAdapter (middleware/polar_adapter.py)    ← caching layer
      → tier_gate.check_tier()                      ← access enforcement
    ← PolarWebhookHandler (webhooks/polar_webhook.py)  ← proactive cache updates

Polar docs: https://docs.polar.sh/api/v1/customers/get-customer-state-external
"""

import os
import logging
import httpx

logger = logging.getLogger(__name__)

_SANDBOX_BASE = "https://sandbox-api.polar.sh/v1"
_PRODUCTION_BASE = "https://api.polar.sh/v1"

# Feature flag benefit type in Polar API responses
POLAR_PIONEER_BENEFIT_TYPE = "feature"
# Metadata key that identifies the Pioneer tier benefit
POLAR_PIONEER_TIER_KEY = "pioneer"


class PolarClient:
    """HTTP client for the Polar Customer State API.

    Uses Polar Feature Flags as the single source of truth for Pioneer
    access. The pioneer_access flag is attached to the Pioneer subscription
    product in the Polar dashboard and managed automatically by Polar.

    Phase 2 integration (v0.5.12): PolarAdapter wraps this client and
    replaces env-var key validation when POLAR_ACCESS_TOKEN is configured.
    The single swap point is _validate_pioneer_key() in tier_gate.py —
    all callers remain unchanged.
    """

    def __init__(self, access_token: str, environment: str = "production"):
        """Initialise the Polar client.

        Args:
            access_token: Polar Organization Access Token (polar_oat_... format).
            environment: "production" or "sandbox". Reads POLAR_ENVIRONMENT
                         env var first; falls back to this argument.
        """
        env = os.environ.get("POLAR_ENVIRONMENT", environment).lower()
        self._environment = env
        self.base_url = _SANDBOX_BASE if env == "sandbox" else _PRODUCTION_BASE
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # API calls
    # ------------------------------------------------------------------

    async def get_customer_state(self, external_id: str) -> dict:
        """Fetch full customer state by VerifiMind UUID (Polar External ID).

        Returns active subscriptions, granted benefit flags, and usage meters
        in a single call. The VerifiMind UUID is registered as Polar's
        External ID at the point of EA/Pioneer sign-up.

        Args:
            external_id: VerifiMind user UUID.

        Returns:
            Customer state dict containing benefit_grants, subscriptions, meters.

        Raises:
            httpx.HTTPStatusError: 401 invalid token, 404 customer not found,
                                   5xx Polar server error.
        """
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/customers/external/{external_id}/state",
                headers=self._headers,
            )
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # State inspection
    # ------------------------------------------------------------------

    def has_pioneer_access(self, state: dict) -> bool:
        """Return True if the customer has an active pioneer_access feature flag.

        Iterates benefit_grants in the customer state. A grant is active when:
          - grant["granted"] is True
          - benefit["type"] == "feature"
          - grant.properties.metadata["tier"] == "pioneer"

        Polar sets granted=True on subscribe and granted=False (or removes the
        grant) on cancellation — no extra lifecycle logic needed here.

        Args:
            state: Customer state dict from get_customer_state().

        Returns:
            True if Pioneer access is active, False otherwise.
        """
        for grant in state.get("benefit_grants", []):
            if not grant.get("granted", False):
                continue
            benefit = grant.get("benefit", {})
            if benefit.get("type") != POLAR_PIONEER_BENEFIT_TYPE:
                continue
            props = grant.get("properties", {})
            metadata = props.get("metadata", {})
            if metadata.get("tier") == POLAR_PIONEER_TIER_KEY:
                return True
        return False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def environment(self) -> str:
        """Return the active environment: "sandbox" or "production"."""
        return self._environment
