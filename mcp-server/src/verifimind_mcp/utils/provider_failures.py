"""Privacy-safe provider failure contracts for Trinity and standalone tools."""

import json
import re
import sys
from typing import Any, Optional

from ..llm.failover import FailoverExhaustedError, FailoverTerminalError


_DIAGNOSTIC_VALUE_ALLOWED = re.compile(r"[^A-Za-z0-9._:/-]")


def safe_diagnostic_value(value: Any, max_length: int = 160) -> Optional[str]:
    """Bound a diagnostic identifier to a non-secret allowlisted alphabet."""
    if value is None:
        return None
    cleaned = _DIAGNOSTIC_VALUE_ALLOWED.sub("", str(value))[:max_length]
    return cleaned or None


def provider_identity(provider: Any, exc: Optional[Exception] = None) -> tuple:
    """Return a sanitized provider/model tuple, preferring the final attempt."""
    attempts = getattr(exc, "attempts", None) if exc is not None else None
    if attempts:
        final = attempts[-1]
        family = safe_diagnostic_value(final.get("provider"))
        model_value = safe_diagnostic_value(final.get("model"))
        if model_value and "/" in model_value:
            model_family, model_value = model_value.split("/", 1)
            family = family or model_family
        return family, model_value

    raw_name = None
    if provider is not None:
        try:
            raw_name = provider.get_model_name()
        except Exception:
            raw_name = None
    if raw_name and "/" in str(raw_name):
        family, model = str(raw_name).split("/", 1)
        return safe_diagnostic_value(family), safe_diagnostic_value(model)

    class_name = type(provider).__name__ if provider is not None else None
    family = class_name.removesuffix("Provider").lower() if class_name else None
    return safe_diagnostic_value(family), safe_diagnostic_value(raw_name)


def _provider_status_code(exc: Exception) -> Optional[int]:
    """Duck-type an SDK HTTP status without serializing its response body."""
    for attr in ("status_code", "code", "http_status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    response = getattr(exc, "response", None)
    value = getattr(response, "status_code", None) if response is not None else None
    return value if isinstance(value, int) else None


def _bounded_retry_after(exc: Exception) -> Optional[float]:
    """Read only a numeric, bounded Retry-After value from an SDK exception."""
    raw = getattr(exc, "retry_after", None)
    if raw is None:
        response = getattr(exc, "response", None)
        headers = getattr(response, "headers", None) if response is not None else None
        if hasattr(headers, "get"):
            raw = headers.get("retry-after") or headers.get("Retry-After")
    try:
        parsed = float(raw)
    except (TypeError, ValueError):
        return None
    if parsed < 0 or parsed > 3600:
        return None
    return round(parsed, 3)


def provider_failure_contract(
    exc: Exception,
    *,
    byok: bool = False,
    default_code: str = "PROVIDER_ERROR",
) -> dict:
    """Classify a provider failure into a stable, non-reflecting public contract."""
    if isinstance(exc, (FailoverExhaustedError, FailoverTerminalError)):
        exhausted = getattr(exc, "error_code", "") == "FAILOVER_EXHAUSTED"
        return {
            "error_code": getattr(exc, "error_code", default_code),
            "message": (
                "All bounded hosted-provider attempts failed."
                if exhausted else "The hosted provider rejected the request."
            ),
            "recovery_hint": (
                "Try again shortly or use an explicit BYOK provider."
                if exhausted else "Operator review is required before retrying this hosted route."
            ),
            "retryable": exhausted,
            "retry_after_seconds": None,
        }

    status = _provider_status_code(exc)
    exception_name = type(exc).__name__.lower()
    try:
        detail = str(exc).lower()
    except Exception:
        detail = ""

    truncation_markers = (
        "response truncated before completion",
        "finish_reason=length",
        "stop_reason=max_tokens",
        "model_context_window_exceeded",
    )
    if any(marker in detail for marker in truncation_markers):
        return {
            "error_code": "PROVIDER_OUTPUT_TRUNCATED",
            "message": "The provider output ended before the analysis was complete.",
            "recovery_hint": (
                "Retry with a shorter input or a provider/model with sufficient output capacity."
            ),
            "retryable": True,
            "retry_after_seconds": None,
        }

    if status == 429 or "ratelimit" in exception_name or "toomanyrequests" in exception_name:
        retry_after = _bounded_retry_after(exc)
        return {
            "error_code": "PROVIDER_RATE_LIMITED",
            "message": "The provider temporarily rejected this stage because capacity was exhausted.",
            "recovery_hint": (
                "Retry after the provider quota window resets."
                if retry_after is None else
                f"Retry after at least {retry_after:g} seconds."
            ),
            "retryable": True,
            "retry_after_seconds": retry_after,
        }

    if (
        status in (408, 504)
        or "timeout" in exception_name
        or "deadlineexceeded" in exception_name
        or "timed out" in detail
    ):
        return {
            "error_code": "PROVIDER_TIMEOUT",
            "message": "The provider timed out before completing this stage.",
            "recovery_hint": "Try again shortly or select a lower-latency provider.",
            "retryable": True,
            "retry_after_seconds": None,
        }

    admission_too_large = status == 413 or (
        "413" in detail
        and any(marker in detail for marker in (
            "too large", "tokens per minute", "tpm", "request entity",
        ))
    )
    if admission_too_large:
        return {
            "error_code": "PROVIDER_REQUEST_TOO_LARGE",
            "message": "The provider rejected this stage because the request was too large.",
            "recovery_hint": (
                "Reduce the input or select a provider/model with a larger admission budget."
            ),
            "retryable": False,
            "retry_after_seconds": None,
        }

    auth_signal = (
        status in (401, 403)
        or any(marker in exception_name for marker in (
            "authentication", "unauthorized", "forbidden", "permissiondenied",
        ))
        or "invalid api key" in detail
    )
    if auth_signal:
        return {
            "error_code": "BYOK_AUTH_FAILED" if byok else "PROVIDER_AUTH_FAILED",
            "message": (
                "API key authentication failed."
                if byok else "The hosted provider authentication check failed."
            ),
            "recovery_hint": (
                "Check that the key matches the selected provider, or omit BYOK parameters."
                if byok else "Operator credential review is required."
            ),
            "retryable": False,
            "retry_after_seconds": None,
        }

    if type(exc).__name__ == "ValidationError":
        return {
            "error_code": "INCOMPLETE_PROVIDER_RESPONSE",
            "message": "The provider returned an incomplete structured analysis.",
            "recovery_hint": (
                "Retry the analysis; generated fields from the failed response were withheld."
            ),
            "retryable": True,
            "retry_after_seconds": None,
        }

    if status is not None and 500 <= status <= 599:
        return {
            "error_code": "PROVIDER_UNAVAILABLE",
            "message": "The provider was temporarily unavailable.",
            "recovery_hint": "Try again shortly or select another provider.",
            "retryable": True,
            "retry_after_seconds": None,
        }

    return {
        "error_code": default_code,
        "message": "The agent analysis could not be completed.",
        "recovery_hint": "Try again. If the issue persists, use another provider.",
        "retryable": False,
        "retry_after_seconds": None,
    }


def trinity_catchall_contract(exc: Exception, *, byok_supplied: bool) -> dict:
    """Typed contract for exceptions that escape every per-stage gate.

    v0.5.60 (§2.2 repair): the old catch-all unconditionally advised "omit
    BYOK params to use server defaults" — including on runs where NO BYOK
    parameter was supplied, sending users to change something they were not
    using. Hints now condition on whether BYOK was actually in play, and an
    auth-shaped failure on a hosted run is attributed to the hosted lane, not
    to the caller's (absent) key.
    """
    try:
        err_str = str(exc).lower()
    except Exception:
        # Deliberate (CodeQL #223): an exception whose __str__ itself raises
        # must not mask the original failure — classification proceeds on the
        # empty string and the generic TRINITY_ERROR contract applies.
        err_str = ""

    auth_shaped = (
        "401" in err_str or "invalid api key" in err_str or "authentication" in err_str
    )
    if auth_shaped:
        if byok_supplied:
            return {
                "error_code": "BYOK_AUTH_FAILED",
                "message": "API key authentication failed.",
                "recovery_hint": (
                    "Check your api_key is valid and matches the llm_provider. "
                    "Get a free Groq key at console.groq.com or omit api_key to use server defaults."
                ),
            }
        return {
            "error_code": "PROVIDER_AUTH_FAILED",
            "message": "The hosted provider authentication check failed.",
            "recovery_hint": (
                "No BYOK key was supplied; this is a hosted-credential issue. "
                "Try again shortly — operator credential review is required if it persists."
            ),
        }

    if "timeout" in err_str or "timed out" in err_str:
        return {
            "error_code": "PROVIDER_TIMEOUT",
            "message": "The LLM provider timed out.",
            "recovery_hint": (
                "The LLM provider took too long. Try again"
                + (", or switch to a faster provider." if byok_supplied else " shortly.")
            ),
        }

    return {
        "error_code": "TRINITY_ERROR",
        "message": "The Trinity analysis could not be completed.",
        "recovery_hint": (
            "Try again. If the issue persists, omit BYOK params to use server defaults."
            if byok_supplied else
            "Try again shortly. If the issue persists, the failure is on the hosted "
            "service side — no change to your request is required."
        ),
    }


# v0.5.60: structured-log agent labels are the canonical short IDs, always.
# The standalone consult tools pass display names ("CS Security"), and the
# sanitizer's space-stripping turned them into a THIRD label ("CSSecurity")
# that broke cross-run aggregation (VM-TR follow-up finding). User-facing
# payloads keep display names; logs get one vocabulary.
_CANONICAL_AGENT_IDS = {
    "X Intelligent": "X",
    "Z Guardian": "Z",
    "CS Security": "CS",
    "XIntelligent": "X",
    "ZGuardian": "Z",
    "CSSecurity": "CS",
    "Trinity": "Trinity",
}


def canonical_agent_id(agent: Optional[str]) -> Optional[str]:
    if agent is None:
        return None
    return _CANONICAL_AGENT_IDS.get(str(agent), str(agent))


def emit_structured_failure(
    *,
    error_code: str,
    agent: Optional[str],
    exc: Exception,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    session_id: Optional[str] = None,
    retryable: Optional[bool] = None,
) -> None:
    """Emit a Cloud-Logging-friendly event with explicit severity and no body."""
    event = {
        "severity": "ERROR",
        "event": "trinity_provider_failure",
        "error_code": safe_diagnostic_value(error_code),
        "agent": safe_diagnostic_value(canonical_agent_id(agent)),
        "provider": safe_diagnostic_value(provider),
        "model": safe_diagnostic_value(model),
        "session_id": safe_diagnostic_value(session_id),
        "exception_type": safe_diagnostic_value(type(exc).__name__),
        "retryable": retryable,
    }
    print(
        json.dumps({key: value for key, value in event.items() if value is not None}),
        file=sys.stderr,
        flush=True,
    )


def emit_trinity_run_event(
    *,
    event: str,
    session_id: Optional[str],
    severity: str = "INFO",
    **fields: Any,
) -> None:
    """v0.5.60: run-lifecycle events — the completion-rate DENOMINATOR.

    Until now only failures were instrumented (`trinity_provider_failure`),
    so no production completion rate was computable from logs — client-side
    burst tests were the only rate anyone had, and those load the same quota
    they measure. Every run now emits exactly one `trinity_run_completed`
    (any outcome, including catch-all errors); `trinity_run_started` marks
    intake. Rate = completed-with-outcome-full / all-completed.
    """
    payload = {
        "severity": severity,
        "event": safe_diagnostic_value(event),
        "session_id": safe_diagnostic_value(session_id),
    }
    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, (int, float, bool)):
            payload[key] = value
        elif isinstance(value, (list, tuple)):
            payload[key] = [safe_diagnostic_value(item) for item in value]
        else:
            payload[key] = safe_diagnostic_value(value)
    print(json.dumps(payload), file=sys.stderr, flush=True)


def unavailable_agent_result(agent_id: str, exc: Exception):
    """Create an internal placeholder that synthesis must treat as unavailable."""
    from ..models import XAgentAnalysis, ZAgentAnalysis, CSAgentAnalysis

    if agent_id == "X":
        result = XAgentAnalysis(
            reasoning_steps=[],
            innovation_score=0.0,
            strategic_value=0.0,
            opportunities=[],
            risks=[],
            recommendation="Analysis unavailable.",
            confidence=0.0,
        )
    elif agent_id == "Z":
        result = ZAgentAnalysis(
            reasoning_steps=[],
            ethics_score=0.0,
            z_protocol_compliance=False,
            ethical_concerns=[],
            mitigation_measures=[],
            recommendation="Analysis unavailable.",
            veto_triggered=False,
            confidence=0.0,
        )
    else:
        result = CSAgentAnalysis(
            reasoning_steps=[],
            security_score=0.0,
            vulnerabilities=[],
            attack_vectors=[],
            security_recommendations=[],
            socratic_questions=[],
            recommendation="Analysis unavailable.",
            confidence=0.0,
        )

    result._inference_quality = "unavailable"
    result._schema_repaired_fields = []
    result._schema_incomplete_fields = []
    if isinstance(exc, (FailoverExhaustedError, FailoverTerminalError)):
        result._provider_attempts = list(getattr(exc, "attempts", []))
        result._failover_occurred = bool(getattr(exc, "hop_executed", False))
        result._failover_correlation = getattr(exc, "correlation", None)
    return result


def trinity_stage_failure(
    *,
    agent_id: str,
    provider: Any,
    exc: Exception,
    byok: bool,
    session_id: str,
) -> tuple:
    """Build the placeholder + trace record for one failed Trinity stage."""
    contract = provider_failure_contract(exc, byok=byok)
    provider_id, model = provider_identity(provider, exc)
    record = {
        "error_code": contract["error_code"],
        "message": contract["message"],
        "recovery_hint": contract["recovery_hint"],
        "provider": provider_id,
        "model": model,
        "retryable": contract["retryable"],
    }
    if contract["retry_after_seconds"] is not None:
        record["retry_after_seconds"] = contract["retry_after_seconds"]
    # v0.5.60: when the orchestrator already spent its one bounded retry on
    # this stage, say so — the caller should not expect an immediate manual
    # retry to behave differently.
    if getattr(exc, "_trinity_retry_attempted", False):
        record["retry_attempted"] = True
    emit_structured_failure(
        error_code=contract["error_code"],
        agent=agent_id,
        exc=exc,
        provider=provider_id,
        model=model,
        session_id=session_id,
        retryable=contract["retryable"],
    )
    return unavailable_agent_result(agent_id, exc), record
