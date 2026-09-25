"""Z-B1a (2026-09-26): the public completion-diagnostics envelope.

Observability only. The envelope carries, for ONE attempt — the final response
of the final application attempt — the completion reservation actually sent,
the provider-reported completion count and the provider-reported reasoning
count, as nullable non-negative integers plus fixed labels. Nothing is
estimated (no visible-JSON subtraction, no tokenizer), no text is carried, and
no verdict, monitor, error taxonomy, cap, retry or routing behaviour depends
on it. The legacy token monitors keep their exact semantics; this is a
separate, additive carrier.

Provider attribution is never guessed: an adapter that produces no snapshot
reports ``unsupported`` for a non-Groq provider and ``unavailable`` for a Groq
attempt that reached no snapshot. Counters are not billed or cumulative
totals — SDK-level transport retries are invisible to the application, so the
envelope claims nothing about them.
"""
from __future__ import annotations

from typing import Any, Optional

from .provider_failures import provider_identity

COMPLETION_DIAGNOSTICS_ATTR = "_completion_diagnostics"
COMPLETION_DIAGNOSTICS_SCOPE = "final_response_of_final_application_attempt"
COMPLETION_DIAGNOSTICS_NOTE = (
    "provider-reported counters for the final response of the final application "
    "attempt; not a billed or cumulative total; null means not reported"
)
_SNAPSHOT_FIELDS = (
    "provider", "model", "status", "sent_reservation",
    "completion_tokens", "reasoning_tokens", "reasoning_share",
)
_KNOWN_STATUSES = frozenset({"reported", "usage_missing", "no_response", "not_sent"})
_MAX_CAUSE_DEPTH = 4


def _clean_int(value: Any) -> Optional[int]:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _clean_share(value: Any) -> Optional[float]:
    if isinstance(value, float) and 0.0 <= value <= 1.0:  # NaN fails both comparisons
        return value
    return None


def _clean_label(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and 0 < len(value) <= 120 else None


def snapshot_from_exception(exc: Optional[BaseException]) -> Optional[dict]:
    """Return the first atomic snapshot on a bounded, cycle-safe cause/context walk.

    The snapshot is read as ONE unit from ONE exception link, so a reservation
    from one attempt can never be combined with counters from another.
    """
    current = exc
    seen: set = set()
    for _ in range(_MAX_CAUSE_DEPTH):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        snapshot = getattr(current, COMPLETION_DIAGNOSTICS_ATTR, None)
        if isinstance(snapshot, dict):
            return dict(snapshot)
        current = getattr(current, "__cause__", None) or getattr(current, "__context__", None)
    return None


def snapshot_from_result(result: Any) -> Optional[dict]:
    snapshot = getattr(result, COMPLETION_DIAGNOSTICS_ATTR, None)
    return dict(snapshot) if isinstance(snapshot, dict) else None


def completion_diagnostics_envelope(source: Any, provider: Any = None) -> dict:
    """Build the public envelope from a stage result or the exception that ended the stage."""
    is_exc = isinstance(source, BaseException)
    snapshot = snapshot_from_exception(source) if is_exc else snapshot_from_result(source)
    family, model = provider_identity(provider, source if is_exc else None)
    if snapshot is None:
        envelope = {
            "provider": family,
            "model": model,
            "status": "unavailable" if family == "groq" else "unsupported",
            "sent_reservation": None,
            "completion_tokens": None,
            "reasoning_tokens": None,
            "reasoning_share": None,
        }
    else:
        # A snapshot is data read from an attribute, not a trusted object:
        # re-validate every field before it becomes public.
        status = snapshot.get("status")
        envelope = {
            "provider": _clean_label(snapshot.get("provider")) or family,
            "model": _clean_label(snapshot.get("model")) or model,
            "status": status if status in _KNOWN_STATUSES else "unavailable",
            "sent_reservation": _clean_int(snapshot.get("sent_reservation")),
            "completion_tokens": _clean_int(snapshot.get("completion_tokens")),
            "reasoning_tokens": _clean_int(snapshot.get("reasoning_tokens")),
            "reasoning_share": _clean_share(snapshot.get("reasoning_share")),
        }
        completion, reasoning = envelope["completion_tokens"], envelope["reasoning_tokens"]
        if not (completion is not None and completion > 0 and reasoning is not None and reasoning <= completion):
            envelope["reasoning_share"] = None
    envelope["scope"] = COMPLETION_DIAGNOSTICS_SCOPE
    envelope["note"] = COMPLETION_DIAGNOSTICS_NOTE
    return envelope
