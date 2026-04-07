"""
Polar Tier-Gate Adapter — v0.5.12 Pioneer Integration
======================================================

Bridges the Polar Customer State API to tier_gate.py middleware.
Provides a caching layer so Pioneer tier is checked efficiently
without hitting the Polar API on every tool invocation.

Integration flow:
  Tool call with pioneer_key (UUID)
    → check_tier() [tier_gate.py — Phase 1 env-var still works]
    → OR: PolarAdapter.check_pioneer_access(uuid)  ← Phase 2 (this module)
      → Cache hit: return cached result (no network call)
      → Cache miss: GET /v1/customers/external/{uuid}/state
      → Cache updated by PolarWebhookHandler on customer.state_changed

Phase 1 (v0.5.11): PIONEER_ACCESS_KEYS env var (still active as fallback).
Phase 2 (v0.5.12): PolarAdapter is used when POLAR_ACCESS_TOKEN is set.
  The adapter is a singleton initialised once on first call to get_polar_adapter().
"""

import os
import time
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..integrations.polar_client import PolarClient

logger = logging.getLogger(__name__)

_DEFAULT_CACHE_TTL = 300  # 5 minutes — matches Polar webhook SLA

# Module-level singleton — initialised on first get_polar_adapter() call
_adapter: Optional["PolarAdapter"] = None


def get_polar_adapter() -> Optional["PolarAdapter"]:
    """Return the active PolarAdapter singleton, or None if not configured.

    Returns None when POLAR_ACCESS_TOKEN env var is absent, preserving
    Phase 1 (env-var key) behavior as the active path.

    On first call with POLAR_ACCESS_TOKEN present, creates and caches the
    singleton for the lifetime of the process.

    Returns:
        PolarAdapter instance, or None if POLAR_ACCESS_TOKEN is not set.
    """
    global _adapter
    if _adapter is not None:
        return _adapter

    token = os.environ.get("POLAR_ACCESS_TOKEN", "").strip()
    if not token:
        return None

    from ..integrations.polar_client import PolarClient

    env = os.environ.get("POLAR_ENVIRONMENT", "production")
    ttl = int(os.environ.get("POLAR_CACHE_TTL", str(_DEFAULT_CACHE_TTL)))

    _adapter = PolarAdapter(PolarClient(token, environment=env), cache_ttl=ttl)
    logger.info(
        "PolarAdapter initialised (environment=%s, cache_ttl=%ss)", env, ttl
    )
    return _adapter


def reset_polar_adapter() -> None:
    """Reset the adapter singleton.

    Used in tests and for runtime config reload (e.g. after env var change).
    After reset, next get_polar_adapter() call re-initialises from current env.
    """
    global _adapter
    _adapter = None


class PolarAdapter:
    """Caching adapter between Polar Customer State API and tier_gate.py.

    Cache behaviour:
      Hit (< cache_ttl): return cached result — no Polar API call.
      Miss or expired: query Polar Customer State API, cache result.
      Webhook update: immediately overwrite cache (timer reset).
      404 from Polar: cache as False (Scholar tier) — customer not registered.

    Typical cache_ttl = 300s (5 minutes). The PolarWebhookHandler keeps the
    cache in sync with actual subscription state for real-time transitions.
    """

    def __init__(self, polar_client: "PolarClient", cache_ttl: int = _DEFAULT_CACHE_TTL):
        """Initialise the adapter.

        Args:
            polar_client: PolarClient instance (sandbox or production).
            cache_ttl: Seconds before a cached entry is considered stale.
        """
        self.client = polar_client
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[bool, float]] = {}

    # ------------------------------------------------------------------
    # Primary access check
    # ------------------------------------------------------------------

    async def check_pioneer_access(self, user_uuid: str) -> bool:
        """Return True if the user has an active Pioneer subscription.

        1. Check local cache (fast path — no network).
        2. If miss or expired: query Polar Customer State API.
        3. Cache the result for cache_ttl seconds.

        Args:
            user_uuid: VerifiMind user UUID (stored as Polar External ID).

        Returns:
            True if Pioneer access active, False for Scholar.

        Raises:
            httpx.HTTPStatusError: On non-404 Polar API errors (5xx, 401).
        """
        import httpx

        if not user_uuid or not user_uuid.strip():
            return False

        uuid = user_uuid.strip()

        # Cache hit
        if uuid in self._cache:
            has_access, cached_at = self._cache[uuid]
            if time.time() - cached_at < self.cache_ttl:
                logger.debug("Cache hit for %s…: pioneer=%s", uuid[:8], has_access)
                return has_access

        # Cache miss — query Polar
        try:
            state = await self.client.get_customer_state(uuid)
            has_access = self.client.has_pioneer_access(state)
            logger.debug("Polar API: %s… pioneer=%s", uuid[:8], has_access)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Customer not registered in Polar → Scholar tier
                logger.debug("Polar customer not found: %s… → Scholar", uuid[:8])
                has_access = False
            else:
                logger.error(
                    "Polar API error %s for %s…", e.response.status_code, uuid[:8]
                )
                raise

        self._cache[uuid] = (has_access, time.time())
        return has_access

    # ------------------------------------------------------------------
    # Cache management (called by PolarWebhookHandler)
    # ------------------------------------------------------------------

    def update_cache(self, user_uuid: str, has_pioneer_access: bool) -> None:
        """Immediately overwrite the tier cache entry for a user.

        Called by PolarWebhookHandler on customer.state_changed so that
        subscription transitions are reflected before the cache TTL expires.

        Args:
            user_uuid: VerifiMind user UUID.
            has_pioneer_access: Current pioneer access state from Polar event.
        """
        self._cache[user_uuid] = (has_pioneer_access, time.time())
        logger.info(
            "Cache updated via webhook: %s… pioneer=%s",
            user_uuid[:8] if user_uuid else "?",
            has_pioneer_access,
        )

    def invalidate_cache(self, user_uuid: str) -> None:
        """Remove a user from cache, forcing a fresh Polar API call next check.

        Args:
            user_uuid: VerifiMind user UUID to evict.
        """
        self._cache.pop(user_uuid, None)

    def get_cache_stats(self) -> dict:
        """Return cache statistics for monitoring and observability.

        Returns:
            Dict with total_cached, active_entries, expired_entries, cache_ttl_seconds.
        """
        now = time.time()
        active = sum(
            1 for _, (_, t) in self._cache.items() if now - t < self.cache_ttl
        )
        return {
            "total_cached": len(self._cache),
            "active_entries": active,
            "expired_entries": len(self._cache) - active,
            "cache_ttl_seconds": self.cache_ttl,
        }
