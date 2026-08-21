"""
Token Ceiling Monitor for Z Agent responses.

Strategy 3 from T's citation mitigation guide (v4.2).
Uses API-reported output_tokens (already captured in AgentMetrics)
instead of tiktoken — zero new dependencies, more accurate.

Author: RNA (Claude Code), CSO
Version: v0.5.3
"""



# Z Agent token ceiling — matches the configured Z max_tokens (raised to 8192 in
# v0.5.46). Originally sized to the Groq/Llama-3.3 context era; still correct for
# the v0.5.49 default (openai/gpt-oss-120b) since it caps OUR configured output.
Z_AGENT_CEILING = 8192

# Risk thresholds
RISK_HIGH_THRESHOLD = 7000
RISK_MEDIUM_THRESHOLD = 5500
RISK_HIGH_RATIO = RISK_HIGH_THRESHOLD / Z_AGENT_CEILING
RISK_MEDIUM_RATIO = RISK_MEDIUM_THRESHOLD / Z_AGENT_CEILING


def _risk_thresholds(ceiling: int) -> tuple[float, float]:
    """Scale the established risk bands to the actual completion budget."""
    return ceiling * RISK_MEDIUM_RATIO, ceiling * RISK_HIGH_RATIO


def check_z_agent_response(
    output_tokens: int,
    ceiling: int = Z_AGENT_CEILING,
    *,
    configured_ceiling: int = Z_AGENT_CEILING,
    ceiling_source: str | None = None,
) -> dict:
    """
    Monitor Z Agent response token utilization.

    Uses API-reported output_tokens from AgentMetrics — no tiktoken
    dependency, accurate across all providers (Groq, Gemini, Anthropic).

    Args:
        output_tokens: Actual output token count from LLM API response
        ceiling: Token ceiling for the model (default: 8192)

    Returns:
        dict with token_count, ceiling, utilization, risk_level, truncated
    """
    utilization_pct = (output_tokens / ceiling) * 100 if ceiling > 0 else 0.0
    medium_threshold, high_threshold = _risk_thresholds(ceiling)

    if output_tokens >= ceiling:
        risk_level = "CRITICAL"
    elif output_tokens > high_threshold:
        risk_level = "HIGH"
    elif output_tokens > medium_threshold:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "token_count": output_tokens,
        "ceiling": ceiling,
        "configured_ceiling": configured_ceiling,
        "ceiling_source": ceiling_source or (
            "agent_config"
            if ceiling == configured_ceiling
            else "provider_completion_reservation"
        ),
        "utilization": f"{utilization_pct:.1f}%",
        "risk_level": risk_level,
        "truncated": output_tokens >= ceiling,
    }


def is_z_response_safe(output_tokens: int, ceiling: int = Z_AGENT_CEILING) -> bool:
    """Return True if Z Agent response is below HIGH risk threshold."""
    _, high_threshold = _risk_thresholds(ceiling)
    return output_tokens <= high_threshold


# v0.5.60 (P3-B): CS runs the same configured 8192 output ceiling as Z
# (both raised in v0.5.46) and HAS truncated in production
# (PROVIDER_OUTPUT_TRUNCATED, VM-TR attempt 9) with no instrumentation —
# the monitor existed for Z only. Same thresholds; separate constant so the
# ceilings can diverge deliberately later without a silent coupling.
CS_AGENT_CEILING = 8192


def check_cs_agent_response(
    output_tokens: int,
    ceiling: int = CS_AGENT_CEILING,
    *,
    configured_ceiling: int = CS_AGENT_CEILING,
    ceiling_source: str | None = None,
) -> dict:
    """Monitor CS Agent response token utilization (mirror of the Z monitor)."""
    return check_z_agent_response(
        output_tokens,
        ceiling=ceiling,
        configured_ceiling=configured_ceiling,
        ceiling_source=ceiling_source,
    )


def _exception_completion_telemetry(
    exc: Exception | None,
) -> tuple[int | None, int | None, bool]:
    """Read only bounded numeric telemetry from an exception cause chain."""
    reservation = None
    output_tokens = None
    provider_truncated = False
    current = exc
    seen: set[int] = set()
    for _ in range(4):
        if current is None or id(current) in seen:
            break
        seen.add(id(current))
        raw_reservation = getattr(current, "_completion_token_reservation", None)
        raw_output = getattr(current, "_provider_reported_output_tokens", None)
        if getattr(current, "_provider_output_truncated", False) is True:
            provider_truncated = True
        if (
            reservation is None
            and isinstance(raw_reservation, int)
            and not isinstance(raw_reservation, bool)
            and raw_reservation > 0
        ):
            reservation = raw_reservation
        if (
            output_tokens is None
            and isinstance(raw_output, int)
            and not isinstance(raw_output, bool)
            and raw_output >= 0
        ):
            output_tokens = raw_output
        current = getattr(current, "__cause__", None) or getattr(
            current, "__context__", None
        )
    return reservation, output_tokens, provider_truncated


def unavailable_agent_token_monitor(
    *,
    configured_ceiling: int,
    exc: Exception | None = None,
    truncated: bool | None = None,
) -> dict:
    """Build an honest failure monitor without inventing an effective ceiling."""
    reservation, output_tokens, provider_truncated = (
        _exception_completion_telemetry(exc)
    )
    if truncated is None and provider_truncated:
        truncated = True
    monitor = {
        "token_count": output_tokens if truncated is True else None,
        "ceiling": reservation,
        "configured_ceiling": configured_ceiling,
        "ceiling_source": (
            "provider_completion_reservation" if reservation is not None else "unknown"
        ),
        "utilization": None,
        "risk_level": "CRITICAL" if truncated is True else "UNAVAILABLE",
        "truncated": truncated,
    }
    if truncated is True and reservation is not None and output_tokens is not None:
        monitor = check_z_agent_response(
            output_tokens,
            ceiling=reservation,
            configured_ceiling=configured_ceiling,
            ceiling_source="provider_completion_reservation",
        )
        # Provider finish metadata is authoritative even if its usage count is
        # a few tokens below the reservation because of accounting semantics.
        monitor["risk_level"] = "CRITICAL"
        monitor["truncated"] = True
    return monitor
