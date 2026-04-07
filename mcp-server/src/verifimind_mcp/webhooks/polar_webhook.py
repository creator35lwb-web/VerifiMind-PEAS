"""
Polar Webhook Handler — v0.5.12 Pioneer Integration
====================================================

Handles customer.state_changed events from Polar to keep the
PolarAdapter tier cache in sync with real-time subscription changes.

Events handled:
  customer.state_changed — fires when a user subscribes, cancels,
    has a payment failure or recovery, or their benefit grants change.
    One event covers all subscription lifecycle transitions.

Signature verification:
  Polar uses the Standard Webhooks specification (https://www.standardwebhooks.com/).
  Requires: pip install standardwebhooks

Deployment:
  Register this endpoint in the Polar dashboard:
    URL: https://verifimind.ysenseai.org/api/webhooks/polar
    Event: customer.state_changed
    Secret: stored in POLAR_WEBHOOK_SECRET env var

References:
  Polar webhooks: https://docs.polar.sh/features/webhooks
  Standard Webhooks: https://www.standardwebhooks.com/
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

EVENT_CUSTOMER_STATE_CHANGED = "customer.state_changed"
HANDLED_EVENTS = frozenset({EVENT_CUSTOMER_STATE_CHANGED})


class PolarWebhookHandler:
    """Processes Polar webhook events for tier-gate cache updates.

    Uses Standard Webhooks HMAC-SHA256 signature verification.
    Only customer.state_changed is needed to cover all subscription transitions.

    Usage (in FastAPI route handler):
        handler = PolarWebhookHandler(webhook_secret=os.environ["POLAR_WEBHOOK_SECRET"])
        result = await handler.handle(request.body(), dict(request.headers))
    """

    def __init__(self, webhook_secret: str, adapter: Optional[Any] = None):
        """Initialise the webhook handler.

        Args:
            webhook_secret: Polar webhook signing secret (whsec_... format).
                            Retrieved from the Polar dashboard after endpoint registration.
            adapter: Optional PolarAdapter instance. If None, get_polar_adapter()
                     is called lazily on first event — singleton will be used.

        Raises:
            ImportError: If the standardwebhooks package is not installed.
        """
        try:
            from standardwebhooks import Webhook
            self._wh = Webhook(webhook_secret)
        except ImportError:
            raise ImportError(
                "standardwebhooks package is required for Polar webhook verification. "
                "Install with: pip install standardwebhooks"
            )
        self._adapter = adapter

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def verify(self, payload: bytes, headers: dict) -> dict:
        """Verify the webhook signature and return the parsed event.

        Delegates to standardwebhooks.Webhook.verify() which checks:
          - webhook-id header (event unique ID)
          - webhook-timestamp header (replay protection)
          - webhook-signature header (HMAC-SHA256)

        Args:
            payload: Raw HTTP request body bytes.
            headers: HTTP headers dict (case-insensitive key lookup handled by
                     standardwebhooks internally).

        Returns:
            Parsed event dict.

        Raises:
            WebhookVerificationError: If the signature is invalid or the
                                      timestamp is outside the allowed window.
        """
        return self._wh.verify(payload, headers)

    async def handle(self, payload: bytes, headers: dict) -> dict:
        """Verify and process a Polar webhook event.

        Args:
            payload: Raw HTTP request body bytes.
            headers: HTTP headers containing Standard Webhooks signature fields.

        Returns:
            Result dict with keys: status, event_type, and action details.
            status values: "processed", "ignored", "skipped", "error"
        """
        event = self.verify(payload, headers)
        event_type = event.get("type", "")

        if event_type not in HANDLED_EVENTS:
            logger.debug("Unhandled Polar event type: %s — ignored", event_type)
            return {"status": "ignored", "event_type": event_type}

        if event_type == EVENT_CUSTOMER_STATE_CHANGED:
            return await self._handle_customer_state_changed(event)

        # Future events handled here
        return {"status": "ignored", "event_type": event_type}

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _handle_customer_state_changed(self, event: dict) -> dict:
        """Process customer.state_changed — update PolarAdapter cache.

        Extracts the VerifiMind UUID (external_id) from the event, checks
        whether the pioneer_access feature flag is granted, and updates
        the adapter cache immediately.

        Args:
            event: Verified Polar event dict.

        Returns:
            Result dict with external_id, pioneer_access, and action taken.
        """
        customer_data = event.get("data", {})
        external_id = customer_data.get("external_id")

        if not external_id:
            logger.warning("customer.state_changed missing external_id — skipping")
            return {"status": "skipped", "reason": "missing external_id"}

        has_pioneer = self._check_pioneer_benefit(customer_data)

        adapter = self._adapter
        if adapter is None:
            from ..middleware.polar_adapter import get_polar_adapter
            adapter = get_polar_adapter()

        if adapter:
            adapter.update_cache(external_id, has_pioneer)
            action = "cache_updated"
        else:
            logger.warning(
                "No PolarAdapter available — POLAR_ACCESS_TOKEN not set? Cache not updated."
            )
            action = "no_adapter"

        logger.info(
            "customer.state_changed: external_id=%s… pioneer=%s action=%s",
            external_id[:8],
            has_pioneer,
            action,
        )

        return {
            "status": "processed",
            "event_type": EVENT_CUSTOMER_STATE_CHANGED,
            "external_id": external_id,
            "pioneer_access": has_pioneer,
            "action": action,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_pioneer_benefit(self, customer_state: dict) -> bool:
        """Return True if pioneer_access feature flag is granted in customer state.

        Mirrors PolarClient.has_pioneer_access() — kept here to avoid an
        import cycle between webhooks and integrations packages.

        Args:
            customer_state: Polar customer state data (event["data"]).

        Returns:
            True if pioneer feature flag is active, False otherwise.
        """
        from ..integrations.polar_client import (
            POLAR_PIONEER_BENEFIT_TYPE,
            POLAR_PIONEER_TIER_KEY,
        )
        for grant in customer_state.get("benefit_grants", []):
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
