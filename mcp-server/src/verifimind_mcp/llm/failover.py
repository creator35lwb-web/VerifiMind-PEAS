"""
Runtime failover executor — WP-B (T S88 D-88-2..5, design on Hub #81).

This module owns REQUEST-TIME failover: retrying a failed in-flight inference
on the same provider, or hopping ONE bounded step to the agent's configured
backup. It is a separate layer from construction-time fallback
(`get_agent_provider` / `_resolve_fallback_chain`), which selects a provider
BEFORE a request exists (D-87-3 separation).

Scope and locality (D-88-3 — structural, not advisory):
- Only providers explicitly marked by `mark_hosted_failover()` participate.
  The marker is applied ONLY in `get_agent_provider`'s hosted free-tier
  branches (server env keys). Session-config BYOK, per-call ephemeral BYOK,
  per-agent operator overrides, Ollama, and Mock are never marked — a failing
  BYOK key must never silently consume developer-funded hosted keys, and a
  local Ollama request must never become a cloud call.
- Mock is never a runtime hop target: exhaustion raises an explicit error
  instead of degrading to synthetic inference (no-silent-mock).

The whole layer ships DARK: with `RUNTIME_FAILOVER_ENABLED` unset (default),
`generate_with_failover` delegates 1:1 to `provider.generate()` — behavior is
byte-identical to v0.5.54. Enabling the flag is a separately receipted,
Alton-gated action (`gcloud run services update --update-env-vars`).

Failure-class policy (D-88-2): same-provider retry and cross-provider hop are
SEPARATE eligibilities — see `classify_failure`. Safety/policy refusals are
responses, not failures (they return normally upstream and never reach the
classifier). Model-output parse failures are also not failures here: providers
degrade `_inference_quality` instead of raising (F-RES-2/F-RES-3 parse-ladder
lane), so a hop can never mask a parse problem.

Bounded execution (D-88-4): per-attempt timeout, total consultation deadline,
hard attempt cap (primary + <=1 same-provider retry + <=1 hop), cancellation
propagated. Known v1 limit, disclosed to T: GeminiProvider calls its SDK
synchronously inside the async method, so `asyncio.wait_for` cannot interrupt
an in-flight Gemini call mid-attempt; the deadline is enforced between
attempts. (Follow-up candidate: `asyncio.to_thread` in the provider.)

Outage-storm control: a per-provider cooldown circuit — N consecutive
hop-class failures opens the provider for a cooldown; requests during OPEN
skip the doomed primary and go straight to the hop target. Aggregate state
only is exposed (`circuit_snapshot`), nothing correlatable to users.
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# --- configuration -----------------------------------------------------------

ENABLE_ENV = "RUNTIME_FAILOVER_ENABLED"
ATTEMPT_TIMEOUT_ENV = "VERIFIMIND_FAILOVER_ATTEMPT_TIMEOUT"
TOTAL_DEADLINE_ENV = "VERIFIMIND_FAILOVER_TOTAL_DEADLINE"

DEFAULT_ATTEMPT_TIMEOUT_S = 30.0
DEFAULT_TOTAL_DEADLINE_S = 70.0
MAX_ATTEMPTS = 3  # primary + <=1 same-provider retry + <=1 hop

CIRCUIT_FAILURE_THRESHOLD = 3   # consecutive hop-class failures ...
CIRCUIT_WINDOW_S = 60.0         # ... within this window ...
CIRCUIT_COOLDOWN_S = 120.0      # ... opens the provider for this long


def runtime_failover_enabled() -> bool:
    """Live read of the enablement flag (the truth contract projects this)."""
    return os.getenv(ENABLE_ENV, "").strip().lower() in ("1", "true", "yes", "on")


def _attempt_timeout() -> float:
    try:
        return float(os.getenv(ATTEMPT_TIMEOUT_ENV, DEFAULT_ATTEMPT_TIMEOUT_S))
    except ValueError:
        return DEFAULT_ATTEMPT_TIMEOUT_S


def _total_deadline() -> float:
    try:
        return float(os.getenv(TOTAL_DEADLINE_ENV, DEFAULT_TOTAL_DEADLINE_S))
    except ValueError:
        return DEFAULT_TOTAL_DEADLINE_S


# --- eligibility marker (resolution-time, hosted free-tier only) -------------

_MARKER_ATTR = "_vf_hosted_failover_agent"


def mark_hosted_failover(provider: Any, agent_id: str) -> Any:
    """Mark a provider as hosted-free-tier failover-eligible.

    Called ONLY from `get_agent_provider`'s hosted env-key branches. The
    marker must be produced at resolution time because a session-BYOK
    GeminiProvider is structurally indistinguishable from a hosted one at the
    call site (same class, same attrs) — locality cannot be reconstructed
    downstream.
    """
    setattr(provider, _MARKER_ATTR, agent_id.upper())
    return provider


def hosted_failover_agent(provider: Any) -> Optional[str]:
    """The agent id a provider was hosted-resolved for, or None (not eligible)."""
    return getattr(provider, _MARKER_ATTR, None)


# --- failure classification (D-88-2) -----------------------------------------

RETRY = "retry"          # same-provider retry eligible
HOP = "hop"              # cross-provider hop eligible (no same-provider retry)
TERMINAL = "terminal"    # neither — surface the error


class FailureDecision:
    """Classification of one failed attempt."""

    def __init__(self, action: str, reason_class: str,
                 retry_after: Optional[float] = None):
        self.action = action
        self.reason_class = reason_class
        self.retry_after = retry_after


def _exc_status_code(exc: BaseException) -> Optional[int]:
    for attr in ("status_code", "code", "http_status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    if response is not None:
        value = getattr(response, "status_code", None)
        if isinstance(value, int):
            return value
    return None


def _exc_retry_after(exc: BaseException) -> Optional[float]:
    value = getattr(exc, "retry_after", None)
    if isinstance(value, (int, float)):
        return float(value)
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None) if response is not None else None
    if headers:
        raw = None
        try:
            raw = headers.get("retry-after") or headers.get("Retry-After")
        except AttributeError:
            pass
        if raw is not None:
            try:
                return float(raw)
            except (TypeError, ValueError):
                return None
    return None


# Class-name fragments, matched case-insensitively. The providers re-raise raw
# SDK exceptions with no shared hierarchy (WP-B recon), so classification is
# duck-typed on names + status codes and unit-tested with shaped fakes.
_AUTH_NAMES = ("authentication", "permissiondenied", "unauthorized", "forbidden")
_RATE_NAMES = ("ratelimit", "resourceexhausted", "toomanyrequests")
_TIMEOUT_NAMES = ("timeout", "deadlineexceeded")
_CONNECT_NAMES = ("connect", "connectionerror", "apiconnection", "serviceunavailable")
_SERVER_NAMES = ("internalservererror", "servererror", "apistatuserror", "badgateway")
_INVALID_NAMES = ("badrequest", "invalidrequest", "invalidargument",
                  "unprocessable", "notfound", "validationerror")


def classify_failure(exc: BaseException) -> FailureDecision:
    """Map a raw provider exception to a failover decision.

    Policy (T S88 amendment group 2):
    - auth/config failure: TERMINAL — hosted auth is an ops incident, and a
      hop would paper over it (BYOK auth never reaches here by construction).
    - invalid request / our schema bug: TERMINAL — a hop cannot fix our bug.
    - 429: honor Retry-After when present (same-provider wait+retry if it
      fits the budget); quota-style exhaustion without a viable retry hops.
    - timeout: HOP (the retry budget is better spent on the backup).
    - connect / 5xx: RETRY once, then hop.
    - anything unrecognized: TERMINAL (conservative — never hop blind).
    """
    name = type(exc).__name__.lower()
    status = _exc_status_code(exc)

    if isinstance(exc, asyncio.TimeoutError):
        return FailureDecision(HOP, "attempt_timeout")

    if any(fragment in name for fragment in _AUTH_NAMES) or status in (401, 403):
        return FailureDecision(TERMINAL, "auth_or_config")

    if any(fragment in name for fragment in _INVALID_NAMES) or status in (400, 404, 422):
        return FailureDecision(TERMINAL, "invalid_request")

    if any(fragment in name for fragment in _RATE_NAMES) or status == 429:
        return FailureDecision(RETRY, "rate_limited",
                               retry_after=_exc_retry_after(exc))

    if any(fragment in name for fragment in _TIMEOUT_NAMES):
        return FailureDecision(HOP, "attempt_timeout")

    if any(fragment in name for fragment in _CONNECT_NAMES):
        return FailureDecision(RETRY, "connection_error")

    if any(fragment in name for fragment in _SERVER_NAMES) or (
            status is not None and 500 <= status <= 599):
        return FailureDecision(RETRY, "server_error")

    return FailureDecision(TERMINAL, "unclassified")


# --- cooldown circuit (D-88-4) -----------------------------------------------

class _Circuit:
    def __init__(self):
        self.consecutive_failures = 0
        self.first_failure_at = 0.0
        self.opened_at: Optional[float] = None
        self.half_open_probe_inflight = False

    def state(self, now: float) -> str:
        if self.opened_at is None:
            return "closed"
        if now - self.opened_at < CIRCUIT_COOLDOWN_S:
            return "open"
        return "half_open"


_circuits: Dict[str, _Circuit] = {}


def _circuit_for(provider_name: str) -> _Circuit:
    return _circuits.setdefault(provider_name, _Circuit())


def record_provider_failure(provider_name: str, now: Optional[float] = None) -> None:
    now = time.monotonic() if now is None else now
    circuit = _circuit_for(provider_name)
    if circuit.state(now) == "half_open":
        # the probe failed — reopen for a fresh cooldown
        circuit.opened_at = now
        circuit.half_open_probe_inflight = False
        return
    if (circuit.consecutive_failures == 0
            or now - circuit.first_failure_at > CIRCUIT_WINDOW_S):
        circuit.consecutive_failures = 1
        circuit.first_failure_at = now
    else:
        circuit.consecutive_failures += 1
    if circuit.consecutive_failures >= CIRCUIT_FAILURE_THRESHOLD:
        circuit.opened_at = now
        logger.warning("failover circuit OPEN for provider %s", provider_name)


def record_provider_success(provider_name: str) -> None:
    circuit = _circuit_for(provider_name)
    circuit.consecutive_failures = 0
    circuit.opened_at = None
    circuit.half_open_probe_inflight = False


def circuit_allows(provider_name: str, now: Optional[float] = None) -> bool:
    """Whether a request may attempt this provider right now."""
    now = time.monotonic() if now is None else now
    circuit = _circuit_for(provider_name)
    state = circuit.state(now)
    if state == "closed":
        return True
    if state == "half_open" and not circuit.half_open_probe_inflight:
        circuit.half_open_probe_inflight = True  # exactly one probe
        return True
    return False


def circuit_snapshot() -> Dict[str, str]:
    """Aggregate circuit state for /health — provider name -> state only."""
    now = time.monotonic()
    return {name: c.state(now) for name, c in sorted(_circuits.items())}


def reset_circuits() -> None:
    """Test hook: clear all circuit state."""
    _circuits.clear()


# --- the executor ------------------------------------------------------------

class FailoverExhaustedError(RuntimeError):
    """All bounded attempts failed — surfaced instead of silent degradation.

    Carries the privacy-minimal attempt trail (provider, class, duration —
    never prompts, responses, or identifiers).
    """

    def __init__(self, message: str, attempts: List[Dict[str, Any]],
                 final_reason_class: str):
        super().__init__(message)
        self.attempts = attempts
        self.final_reason_class = final_reason_class
        self.error_code = "FAILOVER_EXHAUSTED"


def _safe_model_name(provider: Any) -> str:
    try:
        return provider.get_model_name()
    except Exception:  # NOSONAR — telemetry naming must never break inference
        return type(provider).__name__.lower()


def _provider_family(provider: Any) -> str:
    """'groq/openai/gpt-oss-120b' -> 'groq' (circuit + telemetry key)."""
    model_name = _safe_model_name(provider)
    return model_name.split("/", 1)[0] if "/" in model_name else model_name


def _hop_target_name(agent_id: str) -> Optional[str]:
    """The agent's configured runtime hop target, or None. Mock is never one."""
    from ..config_helper import AGENT_PROVIDER_DEFAULTS
    fallback = AGENT_PROVIDER_DEFAULTS.get(agent_id, {}).get("fallback")
    if not fallback or fallback == "mock":
        return None
    return fallback


def runtime_hop_chain(agent_id: str) -> List[str]:
    """Config truth for /health: hop targets this agent WOULD use (may be [])."""
    target = _hop_target_name(agent_id.upper())
    return [target] if target else []


async def _one_attempt(provider: Any, kwargs: Dict[str, Any],
                       timeout: float) -> Dict[str, Any]:
    return await asyncio.wait_for(provider.generate(**kwargs), timeout=timeout)


async def generate_with_failover(provider: Any, **kwargs: Any) -> Any:
    """generate() with bounded runtime failover for marked hosted providers.

    Dark path (flag off, or provider unmarked — every BYOK/Ollama/override/
    mock provider): a plain delegated call, no wrapping, no telemetry keys.

    Enabled path: bounded attempt loop. On success the provider's response
    dict gains `_provider_attempts` + `_failover_occurred` (additive keys;
    `_inference_quality` is whatever the FINAL provider truly stamped — a hop
    never upgrades quality, so the Z-veto and degraded-caps consumers read
    the same truth as today).
    """
    agent_id = hosted_failover_agent(provider)
    if agent_id is None or not runtime_failover_enabled():
        return await provider.generate(**kwargs)

    deadline = time.monotonic() + _total_deadline()
    attempt_timeout = _attempt_timeout()
    attempts: List[Dict[str, Any]] = []
    same_provider_retry_used = False
    hop_used = False
    active = provider
    active_family = _provider_family(provider)
    last_reason = "unclassified"

    if not circuit_allows(active_family):
        # primary is cooling down — go straight to the hop target if one exists
        hopped = await _try_hop(agent_id, attempts, reason="circuit_open")
        if hopped is None:
            raise FailoverExhaustedError(
                f"provider {active_family} cooling down and no hop target",
                attempts, "circuit_open")
        active, active_family = hopped
        hop_used = True

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise FailoverExhaustedError(
                "total consultation deadline exhausted", attempts, last_reason)
        started = time.monotonic()
        try:
            response = await _one_attempt(
                active, kwargs, min(attempt_timeout, remaining))
        except asyncio.CancelledError:
            raise  # cancellation always propagates (D-88-4)
        except BaseException as exc:  # NOSONAR — classified and bounded below
            duration_ms = int((time.monotonic() - started) * 1000)
            decision = classify_failure(exc)
            last_reason = decision.reason_class
            attempts.append({
                "provider": active_family,
                "model": _safe_model_name(active),
                "outcome_class": decision.reason_class,
                "duration_ms": duration_ms,
            })
            record_provider_failure(active_family)
            logger.warning(
                "failover: %s attempt failed (%s) for agent %s",
                active_family, decision.reason_class, agent_id)

            if decision.action == TERMINAL:
                raise
            if hop_used:
                # The backup got its single shot (T S88: "one retry plus one
                # hop can otherwise become three paid/limited calls") — a
                # post-hop failure is exhaustion, never a backup retry.
                raise FailoverExhaustedError(
                    "hop budget exhausted", attempts, last_reason) from exc
            if len(attempts) >= MAX_ATTEMPTS:
                raise FailoverExhaustedError(
                    "attempt budget exhausted", attempts, last_reason) from exc

            if decision.action == RETRY and not same_provider_retry_used:
                wait = decision.retry_after
                if wait is not None:
                    if wait > (deadline - time.monotonic()):
                        # Retry-After exceeds the budget — no blind wait; hop.
                        pass
                    else:
                        same_provider_retry_used = True
                        await asyncio.sleep(wait)
                        continue
                else:
                    same_provider_retry_used = True
                    continue

            # hop (either the decision says hop, or retry is spent/nonviable)
            hopped = await _try_hop(agent_id, attempts, reason=last_reason)
            if hopped is None:
                raise FailoverExhaustedError(
                    f"no runtime hop target for agent {agent_id}",
                    attempts, last_reason) from exc
            active, active_family = hopped
            hop_used = True
            continue

        # success
        duration_ms = int((time.monotonic() - started) * 1000)
        record_provider_success(active_family)
        attempts.append({
            "provider": active_family,
            "model": _safe_model_name(active),
            "outcome_class": "success",
            "duration_ms": duration_ms,
        })
        if isinstance(response, dict):
            response["_provider_attempts"] = attempts
            response["_failover_occurred"] = hop_used
        return response


async def _try_hop(agent_id: str, attempts: List[Dict[str, Any]],
                   reason: str):
    """Construct the hop-target provider, honoring its circuit. None if no
    viable target (missing config, construction failure, circuit open)."""
    target_name = _hop_target_name(agent_id)
    if target_name is None:
        return None
    if not circuit_allows(target_name):
        attempts.append({"provider": target_name,
                         "outcome_class": "circuit_open_skipped",
                         "duration_ms": 0})
        return None
    try:
        from . import get_provider
        target = get_provider(target_name)
    except Exception as exc:  # construction failure => no viable hop
        logger.warning("failover: hop target %s unavailable for agent %s: %s",
                       target_name, agent_id, exc)
        attempts.append({"provider": target_name,
                         "outcome_class": "hop_construction_failed",
                         "duration_ms": 0})
        return None
    logger.info("failover: agent %s hopping to %s (%s)",
                agent_id, target_name, reason)
    return target, target_name
