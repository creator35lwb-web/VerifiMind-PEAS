"""Orchestration-layer completion retry for Trinity stages (v0.5.60).

Scope and the decision boundary this module respects
----------------------------------------------------
D-115-2 (stated precisely — T S135 corrected an earlier shorthand here):
that decision selected exactly ONE provider-informed retry at the provider
layer, for the structured Groq HTTP 413 admission shape, and rejected
blind/generic 413 retry. As part of its scope, the provider layer
deliberately re-raises 429s rather than retrying them there — leaving
rate-limit backoff to a bounded CALLER-level layer, which did not exist
until now. This module is that layer: when a whole Trinity stage fails and
the provider's error explicitly states BOTH that the failure is retryable
AND how long to wait, the orchestrator re-executes that stage exactly once
after sleeping the provider-stated interval. It is compatible with D-115-2,
not a reversal of it.

Live evidence this encodes (VM-TR-2026-08-13-V0559-01 §1.4): Groq returns
``retryable: true`` + ``retry_after_seconds`` in rate-limit rejections, and
until v0.5.60 the server surfaced both fields to the caller and acted on
neither, while a viable analysis sat one short sleep away.

What deliberately does NOT retry here:

* failures without a provider-stated wait (timeouts, truncation, 5xx) — their
  retry semantics are not provider-guaranteed, and a blind re-run doubles
  worst-case latency for an unknown payoff;
* waits above ``RETRY_AFTER_CAP_SECONDS`` — observed short windows are 8–10s;
  the one observed outlier (54s) exceeds any interactive request budget, and
  holding the connection that long converts an honest partial into a probable
  client-side timeout;
* anything once the per-run ``RETRY_SLEEP_BUDGET_SECONDS`` is spent.

The completion guardrail: a retry either produces a REAL second attempt or
propagates the second failure into the unchanged degradation contract. Nothing
in this module may convert a failure into a fabricated success.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any, Optional

from .provider_failures import provider_failure_contract, safe_diagnostic_value

# Explicit sleep seam: production uses asyncio.sleep; the unit suite patches
# THIS name to keep provider-stated waits and staggers instant in tests
# without touching the global asyncio module.
_sleep = asyncio.sleep

# Maximum single provider-stated wait the orchestrator will honour.
RETRY_AFTER_CAP_SECONDS = 15.0
# Total sleep the orchestrator may spend on retries across one Trinity run.
RETRY_SLEEP_BUDGET_SECONDS = 30.0
# Small fixed margin on top of the provider-stated wait, because the stated
# window is when the quota RESETS, not when a request is guaranteed admitted.
RETRY_MARGIN_SECONDS = 0.5
# Gap inserted between two consecutive stages that bill the same provider
# family (today: Z then CS on the shared hosted Groq budget).
SHARED_PROVIDER_STAGGER_SECONDS = 2.0


class TrinityRetryBudget:
    """Per-run accounting for retry sleeps and what they achieved."""

    def __init__(self, budget_seconds: float = RETRY_SLEEP_BUDGET_SECONDS):
        self.remaining = float(budget_seconds)
        self.retries: dict[str, dict] = {}

    def allow(self, wait: float) -> bool:
        return wait <= self.remaining

    def consume(self, wait: float) -> None:
        self.remaining = max(0.0, self.remaining - wait)

    def record(self, agent_id: str, *, wait: float, error_code: str, outcome: str) -> None:
        self.retries[agent_id] = {
            "waited_seconds": round(wait, 3),
            "on_error_code": error_code,
            "outcome": outcome,  # "recovered" | "failed_again"
        }

    def summary(self) -> dict:
        """Response-surface summary; empty dict when no retry happened."""
        return dict(self.retries)


def _emit_retry_event(
    *,
    agent_id: str,
    session_id: Optional[str],
    error_code: str,
    wait: float,
    outcome: str,
) -> None:
    """Cloud-Logging-friendly structured record of one retry decision."""
    event = {
        "severity": "WARNING",
        "event": "trinity_stage_retry",
        "agent": safe_diagnostic_value(agent_id),
        "session_id": safe_diagnostic_value(session_id),
        "error_code": safe_diagnostic_value(error_code),
        "waited_seconds": round(wait, 3),
        "outcome": safe_diagnostic_value(outcome),
    }
    print(
        json.dumps({k: v for k, v in event.items() if v is not None}),
        file=sys.stderr,
        flush=True,
    )


def retry_wait_for(contract: dict) -> Optional[float]:
    """Return the wait to honour for a stage failure, or None if not eligible.

    Eligible only when the provider both marked the failure retryable AND
    stated a numeric wait within the cap. A retryable failure WITHOUT a stated
    wait is deliberately not eligible (see module docstring).
    """
    if not contract.get("retryable"):
        return None
    wait = contract.get("retry_after_seconds")
    if wait is None:
        return None
    try:
        wait = float(wait)
    except (TypeError, ValueError):
        return None
    if wait < 0 or wait > RETRY_AFTER_CAP_SECONDS:
        return None
    return wait + RETRY_MARGIN_SECONDS


async def analyze_with_completion_retry(
    analyze_call,
    *,
    agent_id: str,
    byok: bool,
    session_id: Optional[str],
    budget: TrinityRetryBudget,
):
    """Run one stage's analyze; on a provider-stated retryable wait, retry once.

    ``analyze_call`` is a zero-argument coroutine factory (e.g. a lambda
    closing over the agent and its inputs) so a retry re-executes the REAL
    call, not a cached coroutine.

    Success (first or second attempt) returns the result into the caller's
    untouched success path. A terminal failure raises — the second exception
    when a retry was attempted — so the caller's existing degradation except
    block handles it unchanged. When the retry itself fails, the propagated
    exception carries ``_trinity_retry_attempted = True`` for the stage-error
    record.
    """
    try:
        return await analyze_call()
    except Exception as first_exc:
        contract = provider_failure_contract(first_exc, byok=byok)
        wait = retry_wait_for(contract)
        if wait is None or not budget.allow(wait):
            raise
        budget.consume(wait)
        _emit_retry_event(
            agent_id=agent_id,
            session_id=session_id,
            error_code=contract["error_code"],
            wait=wait,
            outcome="attempting",
        )
        await _sleep(wait)
        try:
            result = await analyze_call()
        except Exception as second_exc:
            budget.record(
                agent_id, wait=wait,
                error_code=contract["error_code"], outcome="failed_again",
            )
            _emit_retry_event(
                agent_id=agent_id,
                session_id=session_id,
                error_code=contract["error_code"],
                wait=wait,
                outcome="failed_again",
            )
            second_exc._trinity_retry_attempted = True
            raise
        budget.record(
            agent_id, wait=wait,
            error_code=contract["error_code"], outcome="recovered",
        )
        _emit_retry_event(
            agent_id=agent_id,
            session_id=session_id,
            error_code=contract["error_code"],
            wait=wait,
            outcome="recovered",
        )
        return result


def _provider_family(provider: Any) -> Optional[str]:
    """Best-effort provider family for stagger decisions ("groq/..." -> "groq")."""
    raw = None
    if provider is not None:
        try:
            raw = provider.get_model_name()
        except Exception:
            raw = None
    if raw and "/" in str(raw):
        return str(raw).split("/", 1)[0].lower()
    if raw:
        return str(raw).lower()
    name = type(provider).__name__ if provider is not None else None
    return name.removesuffix("Provider").lower() if name else None


async def stagger_if_shared_provider(prior_provider: Any, next_provider: Any) -> bool:
    """Sleep a fixed gap when two consecutive stages bill the same provider.

    Returns True when a stagger was applied. Cross-provider pairs (e.g. BYOK
    splits) skip the sleep entirely so clean configurations pay nothing.
    """
    prior = _provider_family(prior_provider)
    nxt = _provider_family(next_provider)
    if prior is None or nxt is None or prior != nxt:
        return False
    await _sleep(SHARED_PROVIDER_STAGGER_SECONDS)
    return True
