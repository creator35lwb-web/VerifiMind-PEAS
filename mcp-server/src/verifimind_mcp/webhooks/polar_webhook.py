"""
Polar Webhook Handler — v0.5.12 Pioneer Integration
====================================================

Handles Polar subscription events to keep the PolarAdapter tier cache
in sync with real-time subscription changes.

Events configured by T (CTO) via Polar API (endpoint ID: e7519bc1-...):
  subscription.created   — new subscription (pending payment, NOT yet active)
  subscription.updated   — subscription state changed (check status field)
  subscription.active    — subscription confirmed active → GRANT Pioneer
  subscription.revoked   — subscription access revoked → REVOKE Pioneer
  subscription.canceled  — subscription canceled → REVOKE Pioneer
  order.created          — order placed (ignored, no tier change)

Signature verification:
  Polar uses the Standard Webhooks specification (https://www.standardwebhooks.com/).
  Requires: pip install standardwebhooks

Webhook registered in Polar dashboard:
  URL:    https://verifimind.ysenseai.org/api/webhooks/polar
  ID:     e7519bc1-3966-49c1-9258-6ca418326daf
  Secret: stored in POLAR_WEBHOOK_SECRET env var (whsec_... format)

External ID extraction:
  VerifiMind UUID is stored as Polar External ID at registration.
  In subscription events: event["data"]["customer"]["external_id"]
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Events that grant Pioneer access
_GRANT_EVENTS = frozenset({"subscription.active"})

# Events that revoke Pioneer access
_REVOKE_EVENTS = frozenset({"subscription.revoked", "subscription.canceled"})

# Events that require status inspection
_INSPECT_EVENTS = frozenset({"subscription.updated", "subscription.created"})

# Events that are explicitly ignored (no tier change)
_IGNORE_EVENTS = frozenset({"order.created"})

# All events we receive from Polar (configured in dashboard)
HANDLED_EVENTS = _GRANT_EVENTS | _REVOKE_EVENTS | _INSPECT_EVENTS

# Polar subscription statuses that indicate active Pioneer access
_ACTIVE_STATUSES = frozenset({"active"})


class PolarWebhookHandler:
    """Processes Polar subscription events for tier-gate cache updates.

    Uses Standard Webhooks HMAC-SHA256 signature verification.
    Maps each subscription event type to a Pioneer access decision
    and updates the PolarAdapter cache immediately.

    Subscription status → Pioneer access mapping:
      subscription.active   → True  (payment confirmed)
      subscription.revoked  → False (immediate revocation)
      subscription.canceled → False (revoked now, not at period end)
      subscription.created  → False (pending payment, not yet active)
      subscription.updated  → True if status=="active", False otherwise
      order.created         → ignored

    Usage (in route handler):
        secret = os.environ["POLAR_WEBHOOK_SECRET"]
        handler = PolarWebhookHandler(webhook_secret=secret)
        result = await handler.handle(await request.body(), dict(request.headers))
    """

    def __init__(self, webhook_secret: str, adapter: Optional[Any] = None):
        """Initialise the webhook handler.

        Args:
            webhook_secret: Polar webhook signing secret (whsec_... format).
                            From POLAR_WEBHOOK_SECRET env var.
            adapter: Optional PolarAdapter. If None, get_polar_adapter() is
                     called lazily on first event (singleton).

        Raises:
            ImportError: If standardwebhooks is not installed.
        """
        try:
            from standardwebhooks import Webhook
            self._wh = Webhook(webhook_secret)
        except ImportError:
            raise ImportError(
                "standardwebhooks package required for Polar webhook verification. "
                "Install with: pip install standardwebhooks"
            )
        self._adapter = adapter

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def verify(self, payload: bytes, headers: dict) -> dict:
        """Verify the webhook signature and return the parsed event.

        Delegates to standardwebhooks.Webhook.verify() which checks:
          - webhook-id (unique event ID, replay protection)
          - webhook-timestamp (timestamp staleness check)
          - webhook-signature (HMAC-SHA256 over id + timestamp + payload)

        Args:
            payload: Raw HTTP request body bytes.
            headers: HTTP headers dict.

        Returns:
            Parsed event dict.

        Raises:
            WebhookVerificationError: On invalid signature or stale timestamp.
        """
        return self._wh.verify(payload, headers)

    async def handle(self, payload: bytes, headers: dict) -> dict:
        """Verify and process a Polar subscription event.

        Args:
            payload: Raw HTTP request body bytes.
            headers: HTTP headers containing Standard Webhooks fields.

        Returns:
            Result dict: status ("processed"/"ignored"/"skipped"), event_type,
                         and action details.
        """
        event = self.verify(payload, headers)
        event_type = event.get("type", "")

        if event_type in _IGNORE_EVENTS:
            logger.debug("Polar event %s — ignored (no tier change)", event_type)
            return {"status": "ignored", "event_type": event_type}

        if event_type in _GRANT_EVENTS:
            return await self._handle_subscription_event(event, has_access=True)

        if event_type in _REVOKE_EVENTS:
            return await self._handle_subscription_event(event, has_access=False)

        if event_type in _INSPECT_EVENTS:
            return await self._handle_inspect_event(event)

        # Unknown event type — log and ignore safely
        logger.debug("Unhandled Polar event type: %s — ignored", event_type)
        return {"status": "ignored", "event_type": event_type}

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    async def _handle_subscription_event(self, event: dict, has_access: bool) -> dict:
        """Process a grant or revoke subscription event.

        Args:
            event: Verified Polar event dict.
            has_access: True to grant Pioneer, False to revoke.

        Returns:
            Result dict with external_id, pioneer_access, and action.
        """
        event_type = event.get("type", "")
        external_id = self._extract_external_id(event)

        if not external_id:
            logger.warning("%s missing external_id — skipping", event_type)
            return {"status": "skipped", "reason": "missing external_id", "event_type": event_type}

        action = await self._update_adapter_cache(external_id, has_access)

        logger.info(
            "%s: external_id=%s… pioneer=%s action=%s",
            event_type, external_id[:8], has_access, action
        )
        return {
            "status": "processed",
            "event_type": event_type,
            "external_id": external_id,
            "pioneer_access": has_access,
            "action": action,
        }

    async def _handle_inspect_event(self, event: dict) -> dict:
        """Process subscription.created / subscription.updated.

        Inspects the status field to determine access:
          "active" → Pioneer granted
          anything else → Pioneer revoked

        Args:
            event: Verified Polar subscription event dict.

        Returns:
            Result dict with external_id, pioneer_access, and action.
        """
        event_type = event.get("type", "")
        data = event.get("data", {})
        external_id = self._extract_external_id(event)
        status = data.get("status", "")

        if not external_id:
            logger.warning("%s missing external_id — skipping", event_type)
            return {"status": "skipped", "reason": "missing external_id", "event_type": event_type}

        has_access = status in _ACTIVE_STATUSES
        action = await self._update_adapter_cache(external_id, has_access)

        logger.info(
            "%s: external_id=%s… status=%s pioneer=%s action=%s",
            event_type, external_id[:8], status, has_access, action
        )
        return {
            "status": "processed",
            "event_type": event_type,
            "external_id": external_id,
            "subscription_status": status,
            "pioneer_access": has_access,
            "action": action,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_external_id(self, event: dict) -> Optional[str]:
        """Extract VerifiMind UUID from a Polar subscription event.

        Polar stores the VerifiMind UUID as the customer External ID.
        Location in subscription events: event["data"]["customer"]["external_id"]

        Args:
            event: Verified Polar event dict.

        Returns:
            external_id string, or None if not present.
        """
        data = event.get("data", {})
        customer = data.get("customer", {})
        return customer.get("external_id") or None

    async def _update_adapter_cache(self, external_id: str, has_access: bool) -> str:
        """Push tier update to PolarAdapter cache.

        Args:
            external_id: VerifiMind user UUID.
            has_access: New Pioneer access state.

        Returns:
            Action string: "cache_updated" or "no_adapter".
        """
        adapter = self._adapter
        if adapter is None:
            from ..middleware.polar_adapter import get_polar_adapter
            adapter = get_polar_adapter()

        if adapter:
            adapter.update_cache(external_id, has_access)
            return "cache_updated"

        logger.warning("No PolarAdapter available — POLAR_ACCESS_TOKEN not set? Cache not updated.")
        return "no_adapter"
