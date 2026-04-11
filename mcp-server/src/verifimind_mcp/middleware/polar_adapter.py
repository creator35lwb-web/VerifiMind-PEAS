"""
Polar Tier-Gate Adapter — v0.5.13 Fortify
==========================================

Bridges the Polar Customer State API to tier_gate.py middleware.
Provides a caching layer so Pioneer tier is checked efficiently
without hitting the Polar API on every tool invocation.

v0.5.13 additions (X-Agent Item 3 hardening sprint):
  - Retry with exponential backoff (max 3 attempts: 1s → 2s → 4s)
  - Circuit breaker: after 5 consecutive failures within 60s → OPEN
    → raises CircuitOpenError; tier_gate fails-closed (deny access)
  - Structured failure logging (timestamp, error_type, attempt count)
  - Env-var fallback restricted to local dev (no POLAR_ACCESS_TOKEN)

Integration flow:
  Tool call with pioneer_key (UUID)
    → check_tier() [tier_gate.py]
    → PolarAdapter.check_pioneer_access(uuid)
      → Circuit open? → raise CircuitOpenError → tier_gate: deny
      → Cache hit: return cached result (no network call)
      → Cache miss: GET /v1/customers/external/{uuid}/state (with retry)
      → Cache updated by PolarWebhookHandler on customer.state_changed

Phase 1 (v0.5.11): PIONEER_ACCESS_KEYS env var (local dev / no POLAR_ACCESS_TOKEN).
Phase 2 (v0.5.13): PolarAdapter used when POLAR_ACCESS_TOKEN is set.
"""

import asyncio
import os
import time
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..integrations.polar_client import PolarClient

logger = logging.getLogger(__name__)

_DEFAULT_CACHE_TTL = 300  # 5 minutes — matches Polar webhook SLA

# Circuit breaker constants (X-Agent Item 3)
_CIRCUIT_FAILURE_THRESHOLD = 5   # consecutive failures before opening
_CIRCUIT_WINDOW_SECONDS = 60     # rolling window for counting consecutive failures
_CIRCUIT_RESET_SECONDS = 60      # how long before attempting half-open recovery

# Retry constants (X-Agent Item 3)
_RETRY_MAX_ATTEMPTS = 3
_RETRY_BASE_DELAY = 1.0          # seconds; doubled each attempt: 1 → 2 → 4

# Module-level singleton — initialised on first get_polar_adapter() call
_adapter: Optional["PolarAdapter"] = None


class CircuitOpenError(Exception):
    """Raised when the Polar circuit breaker is open.

    Signals tier_gate.py to fail-closed (deny Pioneer access) rather than
    falling back to env vars. This prevents unauthorized access during
    extended Polar outages.
    """


def get_polar_adapter() -> Optional["PolarAdapter"]:
    """Return the active PolarAdapter singleton, or None if not configured.

    Returns None when POLAR_ACCESS_TOKEN env var is absent, preserving
    Phase 1 (env-var key) behavior as the active path for local dev.

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
      Miss or expired: query Polar Customer State API (with retry), cache result.
      Webhook update: immediately overwrite cache (timer reset).
      404 from Polar: cache as False (Scholar tier) — customer not registered.

    Circuit breaker behaviour (v0.5.13):
      After _CIRCUIT_FAILURE_THRESHOLD consecutive failures within
      _CIRCUIT_WINDOW_SECONDS, the circuit OPENS and raises CircuitOpenError
      for all subsequent calls. After _CIRCUIT_RESET_SECONDS the circuit
      enters half-open state — the next call is allowed through, and on
      success the circuit fully closes.

    Retry behaviour (v0.5.13):
      Transient errors (5xx, timeout, connection) are retried up to
      _RETRY_MAX_ATTEMPTS times with exponential backoff (1s → 2s → 4s).
      404 and 401 are not retried.

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

        # Circuit breaker state
        self._consecutive_failures: int = 0
        self._first_failure_at: float = 0.0
        self._circuit_open: bool = False
        self._circuit_opened_at: float = 0.0

    # ------------------------------------------------------------------
    # Circuit breaker internals
    # ------------------------------------------------------------------

    def _is_circuit_open(self) -> bool:
        """Return True if requests should be blocked (circuit is OPEN).

        After _CIRCUIT_RESET_SECONDS the circuit enters half-open state:
        one request is allowed through. A success closes the circuit;
        a failure re-opens it and resets the window.
        """
        if not self._circuit_open:
            return False
        if time.time() - self._circuit_opened_at >= _CIRCUIT_RESET_SECONDS:
            # Half-open: allow one attempt through
            logger.info(
                "Polar circuit breaker entering half-open state — attempting recovery"
            )
            self._circuit_open = False
            self._consecutive_failures = 0
            self._first_failure_at = 0.0
            return False
        return True

    def _record_success(self) -> None:
        """Reset failure tracking after a successful Polar API call."""
        if self._consecutive_failures > 0 or self._circuit_open:
            logger.info(
                "Polar circuit breaker: CLOSED after successful call "
                "(was at %d consecutive failures)",
                self._consecutive_failures,
            )
        self._consecutive_failures = 0
        self._circuit_open = False
        self._first_failure_at = 0.0
        self._circuit_opened_at = 0.0

    def _record_failure(self, error_type: str, attempts_made: int) -> None:
        """Update circuit breaker state after all retries are exhausted.

        Args:
            error_type: Human-readable error class name for structured logging.
            attempts_made: Number of retry attempts that were made.
        """
        now = time.time()

        # Start a fresh window if the last failure was outside the window
        if self._first_failure_at == 0.0 or now - self._first_failure_at > _CIRCUIT_WINDOW_SECONDS:
            self._consecutive_failures = 1
            self._first_failure_at = now
        else:
            self._consecutive_failures += 1

        logger.error(
            "Polar failure #%d/%d (error_type=%s, attempts=%d, window_start=%.0f, now=%.0f)",
            self._consecutive_failures,
            _CIRCUIT_FAILURE_THRESHOLD,
            error_type,
            attempts_made,
            self._first_failure_at,
            now,
        )

        if self._consecutive_failures >= _CIRCUIT_FAILURE_THRESHOLD:
            if not self._circuit_open:
                logger.error(
                    "Polar circuit breaker OPEN — %d consecutive failures in %ds window. "
                    "All Pioneer access denied until %.0f (now+%ds).",
                    self._consecutive_failures,
                    _CIRCUIT_WINDOW_SECONDS,
                    now + _CIRCUIT_RESET_SECONDS,
                    _CIRCUIT_RESET_SECONDS,
                )
            self._circuit_open = True
            self._circuit_opened_at = now

    # ------------------------------------------------------------------
    # Primary access check
    # ------------------------------------------------------------------

    async def check_pioneer_access(self, user_uuid: str) -> bool:
        """Return True if the user has an active Pioneer subscription.

        Flow:
          1. Circuit open? → raise CircuitOpenError (fail-closed).
          2. Cache hit? → return cached result (no network call).
          3. Retry loop (max 3 attempts, 1s/2s/4s backoff):
             a. GET /v1/customers/external/{uuid}/state
             b. 404 → Scholar (not in Polar); cache + return False.
             c. 5xx / timeout → retry; on exhaustion → record failure.
          4. All retries failed → record failure → re-raise last error.

        Args:
            user_uuid: VerifiMind user UUID (stored as Polar External ID).

        Returns:
            True if Pioneer access active, False for Scholar.

        Raises:
            CircuitOpenError: Circuit is open (5+ consecutive failures in window).
            httpx.HTTPStatusError: On auth (401) or non-retryable Polar errors.
            httpx.TimeoutException / httpx.ConnectError: If all retries fail.
        """
        import httpx

        if not user_uuid or not user_uuid.strip():
            return False

        uuid = user_uuid.strip()

        # 1. Circuit breaker guard
        if self._is_circuit_open():
            raise CircuitOpenError(
                f"Polar circuit open — denying Pioneer access for {uuid[:8]}… "
                f"(will retry after {_CIRCUIT_RESET_SECONDS}s)"
            )

        # 2. Cache hit
        if uuid in self._cache:
            has_access, cached_at = self._cache[uuid]
            if time.time() - cached_at < self.cache_ttl:
                logger.debug("Cache hit for %s…: pioneer=%s", uuid[:8], has_access)
                return has_access

        # 3. Retry loop
        last_error: Exception | None = None
        for attempt in range(_RETRY_MAX_ATTEMPTS):
            try:
                state = await self.client.get_customer_state(uuid)
                has_access = self.client.has_pioneer_access(state)
                logger.debug("Polar API: %s… pioneer=%s", uuid[:8], has_access)
                self._record_success()
                self._cache[uuid] = (has_access, time.time())
                return has_access

            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status == 404:
                    # Customer not registered in Polar → Scholar; not a failure
                    logger.debug("Polar customer not found: %s… → Scholar", uuid[:8])
                    self._record_success()
                    self._cache[uuid] = (False, time.time())
                    return False
                if status == 401:
                    # Auth error — do not retry; count as failure immediately
                    logger.error(
                        "Polar auth error 401 for %s… (POLAR_ACCESS_TOKEN invalid?)", uuid[:8]
                    )
                    last_error = e
                    break
                # 5xx — retryable
                logger.warning(
                    "Polar HTTP %d for %s… (attempt %d/%d)",
                    status, uuid[:8], attempt + 1, _RETRY_MAX_ATTEMPTS,
                )
                last_error = e

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                logger.warning(
                    "Polar %s for %s… (attempt %d/%d)",
                    type(e).__name__, uuid[:8], attempt + 1, _RETRY_MAX_ATTEMPTS,
                )
                last_error = e

            # Backoff before next attempt (skip on last attempt)
            if attempt < _RETRY_MAX_ATTEMPTS - 1:
                delay = _RETRY_BASE_DELAY * (2 ** attempt)  # 1.0s, 2.0s
                logger.warning(
                    "Polar retry %d/%d in %.1fs for %s…",
                    attempt + 1, _RETRY_MAX_ATTEMPTS, delay, uuid[:8],
                )
                await asyncio.sleep(delay)

        # 4. All retries exhausted — record this as a single circuit-breaker failure
        error_type = type(last_error).__name__ if last_error else "unknown"
        self._record_failure(error_type, _RETRY_MAX_ATTEMPTS if last_error else 0)

        if last_error:
            raise last_error
        raise RuntimeError("Polar: all retries exhausted with no error captured")

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
            Dict with total_cached, active_entries, expired_entries,
            cache_ttl_seconds, circuit_open, consecutive_failures.
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
            "circuit_open": self._circuit_open,
            "consecutive_failures": self._consecutive_failures,
        }
