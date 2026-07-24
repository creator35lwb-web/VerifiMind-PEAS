"""
Runtime failover executor — WP-B v2 (T S88 D-88-2..5 + S90 B-90-1..9 repairs).

This module owns REQUEST-TIME failover: retrying a failed in-flight inference
on the same provider, or hopping ONE bounded step to a resolved backup. It is
a separate layer from construction-time fallback (`get_agent_provider` /
`_resolve_fallback_chain`), which selects a provider BEFORE a request exists
(D-87-3 separation).

Scope and locality (D-88-3 — structural, not advisory):
- Only providers explicitly marked by `mark_hosted_failover()` participate.
  The marker is applied ONLY in `get_agent_provider`'s hosted free-tier
  branches. Session-config BYOK, per-call ephemeral BYOK, per-agent operator
  overrides, Ollama, and Mock are never marked.
- B-90-2: the marker carries the RESOLVED hop chain, computed at resolution
  time with the active provider family excluded — a Gemini-resolved Z/CS can
  never "hop" to Gemini, and a same-family retry is never reported as
  cross-provider failover. Mock is never a hop target (no-silent-mock).

Failure-class policy (D-88-2 + B-90-1/B-90-3):
- Only infrastructure classes (connection, 5xx, attempt timeout) mutate the
  outage circuit. Terminal auth/config, invalid-request, rate-limit, and
  unclassified failures NEVER poison circuit state.
- 429 semantics: a valid in-budget `Retry-After` (delta-seconds or HTTP-date)
  waits and retries the same provider once; absent/malformed/over-budget
  Retry-After means NO blind retry — hop or terminate.
- Safety/policy refusals are responses, not failures (they return normally
  upstream). Model-output parse failures never reach this layer (providers
  degrade `_inference_quality` instead of raising — F-RES-2/F-RES-3 lane).

Bounded execution (D-88-4 + B-90-4/B-90-6):
- Hard caps: MAX_ATTEMPTS total, per-attempt timeout, total deadline;
  cancellation propagates and releases any half-open probe or backup
  admission held (no stranded circuit state).
- The per-attempt timeout is enforceable for every hosted provider: Gemini's
  SDK call is awaited via the async client (`client.aio`) as of this change.

Outage-storm control (D-88-4 + B-90-5):
- Per-provider cooldown circuit + a bounded backup ADMISSION gate: at most
  `FAILOVER_BACKUP_ADMISSION_LIMIT` concurrent hopped requests per backup
  family. Both are **per-process** (one Cloud Run instance) — no fleet-wide
  protection is implied; /health labels the scope honestly.

Evidence semantics (D-88-5 + B-90-7): `runtime_failover_enabled()` FAILS
CLOSED — the env flag alone is not enough; a valid evidence tuple
(`FAILOVER_CONTRACT_TESTED_AT` = ISO-8601 timestamp, `FAILOVER_EVIDENCE_BUILD`
= build/release identity) must accompany it, stamped by the same env update.
Every public surface projects this one live read.

The whole layer ships DARK: flag unset (default) means
`generate_with_failover` delegates 1:1 to `provider.generate()` — behavior is
byte-identical to v0.5.54.
"""

import asyncio
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# --- configuration -----------------------------------------------------------

ENABLE_ENV = "RUNTIME_FAILOVER_ENABLED"
ATTEMPT_TIMEOUT_ENV = "VERIFIMIND_FAILOVER_ATTEMPT_TIMEOUT"
TOTAL_DEADLINE_ENV = "VERIFIMIND_FAILOVER_TOTAL_DEADLINE"
EVIDENCE_TESTED_ENV = "FAILOVER_CONTRACT_TESTED_AT"
EVIDENCE_BUILD_ENV = "FAILOVER_EVIDENCE_BUILD"
ADMISSION_LIMIT_ENV = "FAILOVER_BACKUP_ADMISSION_LIMIT"

DEFAULT_ATTEMPT_TIMEOUT_S = 30.0
DEFAULT_TOTAL_DEADLINE_S = 70.0
MAX_ATTEMPTS = 3  # primary + <=1 same-provider retry + <=1 hop
DEFAULT_BACKUP_ADMISSION_LIMIT = 4  # concurrent hopped requests per backup, per process

CIRCUIT_FAILURE_THRESHOLD = 3   # consecutive infrastructure failures ...
CIRCUIT_WINDOW_S = 60.0         # ... within this window ...
CIRCUIT_COOLDOWN_S = 120.0      # ... opens the provider for this long


def _flag_on() -> bool:
    return os.getenv(ENABLE_ENV, "").strip().lower() in ("1", "true", "yes", "on")


def evidence_state() -> Dict[str, Any]:
    """The enablement evidence tuple (B-90-7): stamped by the SAME env update
    that flips the flag, so CI failure-injection evidence + build identity
    travel with enablement. `valid` requires an ISO-8601 tested-at AND a
    non-empty build identity."""
    tested_at = os.getenv(EVIDENCE_TESTED_ENV, "").strip() or None
    build = os.getenv(EVIDENCE_BUILD_ENV, "").strip() or None
    valid = False
    if tested_at and build:
        try:
            datetime.fromisoformat(tested_at.replace("Z", "+00:00"))
            valid = True
        except ValueError:
            valid = False
    return {"tested_at": tested_at, "build": build, "valid": valid}


def runtime_failover_enabled() -> bool:
    """Live enablement read — FAILS CLOSED (B-90-7): the flag counts only
    when the evidence tuple validates."""
    if not _flag_on():
        return False
    if not evidence_state()["valid"]:
        logger.warning(
            "%s is set but the evidence tuple (%s + %s) is missing/invalid — "
            "runtime failover stays DISABLED (fail-closed)",
            ENABLE_ENV, EVIDENCE_TESTED_ENV, EVIDENCE_BUILD_ENV)
        return False
    return True


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


def _admission_limit() -> int:
    try:
        return int(os.getenv(ADMISSION_LIMIT_ENV, DEFAULT_BACKUP_ADMISSION_LIMIT))
    except ValueError:
        return DEFAULT_BACKUP_ADMISSION_LIMIT


# --- eligibility marker (resolution-time, hosted free-tier only) -------------

_MARKER_ATTR = "_vf_hosted_failover_agent"
_CHAIN_ATTR = "_vf_hosted_hop_chain"


def mark_hosted_failover(provider: Any, agent_id: str, active_family: str,
                         fallback: Optional[str]) -> Any:
    """Mark a provider as hosted-free-tier failover-eligible, carrying the
    RESOLVED hop chain (B-90-2).

    Called ONLY from `get_agent_provider`'s hosted env-key branches, which
    know both the family they actually constructed (`active_family`) and the
    agent's configured fallback. The chain excludes mock (no-silent-mock) and
    excludes the active family itself — if the resolved primary already IS
    the configured fallback family, there is no hop target and exhaustion is
    explicit rather than a same-family call dressed up as failover.
    """
    chain: Tuple[str, ...] = ()
    if fallback and fallback != "mock" and fallback != active_family:
        chain = (fallback,)
    setattr(provider, _MARKER_ATTR, agent_id.upper())
    setattr(provider, _CHAIN_ATTR, chain)
    return provider


def hosted_failover_agent(provider: Any) -> Optional[str]:
    """The agent id a provider was hosted-resolved for, or None (not eligible)."""
    return getattr(provider, _MARKER_ATTR, None)


def hosted_hop_chain(provider: Any) -> Tuple[str, ...]:
    """The resolved hop chain attached at marking time (may be empty)."""
    return getattr(provider, _CHAIN_ATTR, ())


# --- failure classification (D-88-2, B-90-1, B-90-3) -------------------------

RETRY = "retry"          # same-provider retry eligible
HOP = "hop"              # cross-provider hop eligible (no same-provider retry)
TERMINAL = "terminal"    # neither — surface the error


class FailureDecision:
    """Classification of one failed attempt. `circuit_relevant` marks the
    infrastructure classes that may mutate outage-circuit state (B-90-1):
    terminal auth/config, invalid-request, rate-limit, and unclassified
    failures never poison the circuit."""

    def __init__(self, action: str, reason_class: str,
                 retry_after: Optional[float] = None,
                 circuit_relevant: bool = False):
        self.action = action
        self.reason_class = reason_class
        self.retry_after = retry_after
        self.circuit_relevant = circuit_relevant


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


def _parse_retry_after(raw: Any) -> Optional[float]:
    """B-90-3: parse both Retry-After forms. delta-seconds and HTTP-date are
    honored (negative clamps to 0 = immediate single retry); anything
    malformed returns None, which the policy treats as NOT retryable."""
    if isinstance(raw, (int, float)):
        return max(float(raw), 0.0)
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    try:
        return max(float(text), 0.0)
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max((when - datetime.now(timezone.utc)).total_seconds(), 0.0)


def _exc_retry_after(exc: BaseException) -> Optional[float]:
    value = getattr(exc, "retry_after", None)
    parsed = _parse_retry_after(value)
    if parsed is not None:
        return parsed
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None) if response is not None else None
    if headers is None:
        return None
    try:
        raw = headers.get("retry-after") or headers.get("Retry-After")
    except AttributeError:
        return None  # headers object without .get — treat as absent
    return _parse_retry_after(raw)


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

    Policy (T S88 group 2 + S90 B-90-1/B-90-3):
    - auth/config: TERMINAL, circuit-neutral — an ops incident a hop would
      paper over (BYOK auth never reaches here by construction).
    - invalid request / our schema bug: TERMINAL, circuit-neutral.
    - 429 WITH a valid Retry-After: one same-provider wait+retry if it fits
      the budget. 429 WITHOUT a viable Retry-After: hop, never a blind retry.
      Rate limiting is capacity, not outage — circuit-neutral either way.
    - attempt timeout: HOP, circuit-relevant.
    - connect / 5xx: RETRY once then hop, circuit-relevant.
    - anything unrecognized: TERMINAL, circuit-neutral (never hop blind).
    """
    name = type(exc).__name__.lower()
    status = _exc_status_code(exc)

    if isinstance(exc, asyncio.TimeoutError):
        return FailureDecision(HOP, "attempt_timeout", circuit_relevant=True)

    if any(fragment in name for fragment in _AUTH_NAMES) or status in (401, 403):
        return FailureDecision(TERMINAL, "auth_or_config")

    if any(fragment in name for fragment in _INVALID_NAMES) or status in (400, 404, 422):
        return FailureDecision(TERMINAL, "invalid_request")

    if any(fragment in name for fragment in _RATE_NAMES) or status == 429:
        retry_after = _exc_retry_after(exc)
        if retry_after is None:
            return FailureDecision(HOP, "rate_limited_no_retry_after")
        return FailureDecision(RETRY, "rate_limited", retry_after=retry_after)

    if any(fragment in name for fragment in _TIMEOUT_NAMES):
        return FailureDecision(HOP, "attempt_timeout", circuit_relevant=True)

    if any(fragment in name for fragment in _CONNECT_NAMES):
        return FailureDecision(RETRY, "connection_error", circuit_relevant=True)

    if any(fragment in name for fragment in _SERVER_NAMES) or (
            status is not None and 500 <= status <= 599):
        return FailureDecision(RETRY, "server_error", circuit_relevant=True)

    return FailureDecision(TERMINAL, "unclassified")


# --- cooldown circuit (D-88-4, per-process) ----------------------------------

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
    """Record an INFRASTRUCTURE failure (callers gate on
    `FailureDecision.circuit_relevant` — B-90-1)."""
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


def acquire_slot(provider_name: str, now: Optional[float] = None) -> Tuple[bool, bool]:
    """Whether a request may attempt this provider now → (allowed, probe_held).
    `probe_held` is True when the caller consumed the single half-open probe
    and is responsible for releasing it if neither success nor an
    infrastructure failure gets recorded (B-90-4)."""
    now = time.monotonic() if now is None else now
    circuit = _circuit_for(provider_name)
    state = circuit.state(now)
    if state == "closed":
        return True, False
    if state == "half_open" and not circuit.half_open_probe_inflight:
        circuit.half_open_probe_inflight = True
        return True, True
    return False, False


def circuit_allows(provider_name: str, now: Optional[float] = None) -> bool:
    """Boolean view of `acquire_slot` (kept for tests/diagnostics)."""
    return acquire_slot(provider_name, now)[0]


def release_probe(provider_name: str) -> None:
    """Release a held half-open probe WITHOUT recording an outcome (B-90-4:
    cancellation / circuit-neutral failures must not strand the circuit)."""
    _circuit_for(provider_name).half_open_probe_inflight = False


def circuit_snapshot() -> Dict[str, str]:
    """Aggregate circuit state for /health — provider name -> state only."""
    now = time.monotonic()
    return {name: c.state(now) for name, c in sorted(_circuits.items())}


# --- backup admission bulkhead (B-90-5, per-process) --------------------------

_admission: Dict[str, int] = {}

ADMISSION_SCOPE = "per-process"  # honest label: one Cloud Run instance, no fleet claim


def admit_backup(provider_name: str) -> bool:
    """Bounded admission for hopped load: at most N concurrent hopped
    requests per backup family in this process. Prevents an open primary
    from moving the entire instance's load onto the shared backup at once."""
    if _admission.get(provider_name, 0) >= _admission_limit():
        return False
    _admission[provider_name] = _admission.get(provider_name, 0) + 1
    return True


def release_backup(provider_name: str) -> None:
    _admission[provider_name] = max(_admission.get(provider_name, 0) - 1, 0)


def admission_snapshot() -> Dict[str, int]:
    return {name: count for name, count in sorted(_admission.items()) if count}


def reset_circuits() -> None:
    """Test hook: clear all circuit + admission state."""
    _circuits.clear()
    _admission.clear()


# --- typed boundary errors (B-90-8) ------------------------------------------

class FailoverExhaustedError(RuntimeError):
    """All bounded attempts failed — surfaced instead of silent degradation.

    Carries the privacy-minimal attempt trail (provider/model/class/duration
    — never prompts, responses, or identifiers) plus an ephemeral
    per-consultation correlation value."""

    def __init__(self, message: str, attempts: List[Dict[str, Any]],
                 final_reason_class: str, correlation: str):
        super().__init__(message)
        self.attempts = attempts
        self.final_reason_class = final_reason_class
        self.correlation = correlation
        self.error_code = "FAILOVER_EXHAUSTED"


class FailoverTerminalError(RuntimeError):
    """A terminal (non-retryable, non-hoppable) hosted-provider failure —
    auth/config or invalid-request. Distinct from BYOK_AUTH_FAILED by
    construction: BYOK providers never enter the executor, so this code
    always means the HOSTED lane needs operator attention."""

    def __init__(self, message: str, attempts: List[Dict[str, Any]],
                 reason_class: str, correlation: str):
        super().__init__(message)
        self.attempts = attempts
        self.final_reason_class = reason_class
        self.correlation = correlation
        self.error_code = "HOSTED_PROVIDER_TERMINAL"


# --- helpers ------------------------------------------------------------------

def _safe_model_name(provider: Any) -> str:
    try:
        return provider.get_model_name()
    except Exception:  # NOSONAR — telemetry naming must never break inference
        return type(provider).__name__.lower()


def _provider_family(provider: Any) -> str:
    """'groq/openai/gpt-oss-120b' -> 'groq' (circuit + telemetry key)."""
    model_name = _safe_model_name(provider)
    return model_name.split("/", 1)[0] if "/" in model_name else model_name


# --- the executor -------------------------------------------------------------

class _FailoverRun:
    """One consultation's bounded attempt loop. Instance state keeps each
    method small (complexity) and makes hold-release on ANY exit path —
    including cancellation — a single `finally` (B-90-4)."""

    def __init__(self, provider: Any, agent_id: str,
                 chain: Tuple[str, ...], kwargs: Dict[str, Any]):
        self.primary = provider
        self.agent_id = agent_id
        self.chain = chain
        self.kwargs = kwargs
        self.correlation = uuid.uuid4().hex[:8]  # ephemeral, per-consultation
        self.attempts: List[Dict[str, Any]] = []
        self.hop_used = False
        self.retry_used = False
        self.probe_held: Optional[str] = None
        self.admission_held: Optional[str] = None
        self.last_reason = "unclassified"
        self.deadline = time.monotonic() + _total_deadline()
        self.attempt_timeout = _attempt_timeout()

    # -- bookkeeping ----------------------------------------------------------

    def _note(self, provider_name: str, outcome: str, duration_ms: int = 0,
              model: Optional[str] = None) -> None:
        entry: Dict[str, Any] = {
            "provider": provider_name,
            "model": model or provider_name,
            "outcome_class": outcome,
            "duration_ms": duration_ms,
        }
        self.attempts.append(entry)

    def _release_holds(self) -> None:
        if self.probe_held:
            release_probe(self.probe_held)
            self.probe_held = None
        if self.admission_held:
            release_backup(self.admission_held)
            self.admission_held = None

    def _exhausted(self, message: str) -> FailoverExhaustedError:
        return FailoverExhaustedError(
            message, self.attempts, self.last_reason, self.correlation)

    # -- attempt outcomes -----------------------------------------------------

    def _record_failure(self, family: str, decision: FailureDecision) -> None:
        """B-90-1: only infrastructure classes touch the circuit; circuit-
        neutral failures release a held probe instead of recording."""
        if decision.circuit_relevant:
            record_provider_failure(family)
            if self.probe_held == family:
                self.probe_held = None  # record_provider_failure consumed it
        elif self.probe_held == family:
            release_probe(family)
            self.probe_held = None

    def _retry_viable(self, decision: FailureDecision) -> bool:
        """Same-provider retry: once, and for a rate-limit only when a valid
        Retry-After fits the remaining budget (B-90-3)."""
        if decision.action != RETRY or self.retry_used:
            return False
        if decision.retry_after is None:
            return True  # connection/5xx: one immediate retry
        return decision.retry_after <= (self.deadline - time.monotonic())

    def _hop(self) -> Any:
        """Cross to the resolved backup (B-90-2 chain), honoring its circuit
        and the admission bulkhead (B-90-5). Returns the constructed provider
        or raises FailoverExhaustedError."""
        if not self.chain:
            raise self._exhausted(f"no runtime hop target for agent {self.agent_id}")
        target = self.chain[0]
        allowed, probe = acquire_slot(target)
        if not allowed:
            self._note(target, "circuit_open_skipped")
            raise self._exhausted(f"hop target {target} cooling down")
        if probe:
            self.probe_held = target
        if not admit_backup(target):
            if probe:
                release_probe(target)
                self.probe_held = None
            self._note(target, "backup_admission_rejected")
            raise self._exhausted(f"backup {target} admission limit reached")
        self.admission_held = target
        try:
            from . import get_provider
            provider = get_provider(target)
        except Exception as exc:
            self._note(target, "hop_construction_failed")
            raise self._exhausted(f"hop target {target} unavailable") from exc
        logger.info("failover: agent %s hopping to %s (%s) [%s]",
                    self.agent_id, target, self.last_reason, self.correlation)
        self.hop_used = True
        return provider

    async def _handle_failure(self, active: Any, family: str,
                              exc: Exception, duration_ms: int) -> Any:
        """Classify one failed attempt and return the provider for the next
        attempt (same or hopped), or raise the typed terminal/exhausted error."""
        decision = classify_failure(exc)
        self.last_reason = decision.reason_class
        self._note(family, decision.reason_class, duration_ms,
                   _safe_model_name(active))
        self._record_failure(family, decision)
        logger.warning("failover: %s attempt failed (%s) for agent %s [%s]",
                       family, decision.reason_class, self.agent_id,
                       self.correlation)

        if decision.action == TERMINAL:
            raise FailoverTerminalError(
                f"hosted provider {family} terminal failure "
                f"({decision.reason_class})",
                self.attempts, decision.reason_class, self.correlation) from exc
        if self.hop_used:
            # The backup got its single shot (T S88: "one retry plus one hop
            # can otherwise become three paid/limited calls").
            raise self._exhausted("hop budget exhausted") from exc
        if len(self.attempts) >= MAX_ATTEMPTS:
            raise self._exhausted("attempt budget exhausted") from exc

        if self._retry_viable(decision):
            self.retry_used = True
            if decision.retry_after:
                await asyncio.sleep(decision.retry_after)
            return active
        return self._hop()

    def _finish(self, response: Any, family: str, duration_ms: int,
                model: str) -> Any:
        record_provider_success(family)
        if self.probe_held == family:
            self.probe_held = None  # success consumed/cleared the probe
        self._note(family, "success", duration_ms, model)
        if isinstance(response, dict):
            response["_provider_attempts"] = self.attempts
            response["_failover_occurred"] = self.hop_used
            response["_failover_correlation"] = self.correlation
        return response

    # -- main loop ------------------------------------------------------------

    async def execute(self) -> Any:
        try:
            return await self._loop()
        finally:
            self._release_holds()  # cancellation / any exit: nothing stranded

    async def _loop(self) -> Any:
        active = self.primary
        family = _provider_family(active)
        allowed, probe = acquire_slot(family)
        if probe:
            self.probe_held = family
        if not allowed:
            self._note(family, "circuit_open_skipped")
            self.last_reason = "circuit_open"
            active = self._hop()
            family = _provider_family(active)

        while True:
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise self._exhausted("total consultation deadline exhausted")
            started = time.monotonic()
            try:
                response = await asyncio.wait_for(
                    active.generate(**self.kwargs),
                    timeout=min(self.attempt_timeout, remaining))
            except asyncio.CancelledError:
                raise  # propagates; execute()'s finally releases holds (B-90-4)
            except Exception as exc:
                duration_ms = int((time.monotonic() - started) * 1000)
                active = await self._handle_failure(
                    active, family, exc, duration_ms)
                family = _provider_family(active)
                continue
            duration_ms = int((time.monotonic() - started) * 1000)
            return self._finish(response, family, duration_ms,
                                _safe_model_name(active))


async def generate_with_failover(provider: Any, **kwargs: Any) -> Any:
    """generate() with bounded runtime failover for marked hosted providers.

    Dark path (flag off / evidence invalid / provider unmarked — every
    BYOK/Ollama/override/mock provider): a plain delegated call, no wrapping,
    no telemetry keys — byte-identical legacy behavior.

    Enabled path: the bounded `_FailoverRun` loop. On success the provider's
    response dict gains `_provider_attempts`, `_failover_occurred`, and an
    ephemeral `_failover_correlation` (additive keys; `_inference_quality` is
    whatever the FINAL provider truly stamped — a hop never upgrades quality,
    so the Z-veto and degraded-caps consumers read the same truth as today).
    """
    agent_id = hosted_failover_agent(provider)
    if agent_id is None or not runtime_failover_enabled():
        return await provider.generate(**kwargs)
    run = _FailoverRun(provider, agent_id, hosted_hop_chain(provider), kwargs)
    return await run.execute()
