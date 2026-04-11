"""
Token Ceiling Monitor for Z Agent responses.

Strategy 3 from T's citation mitigation guide (v4.2).
Uses API-reported output_tokens (already captured in AgentMetrics)
instead of tiktoken — zero new dependencies, more accurate.

Author: RNA (Claude Code), CSO
Version: v0.5.3
"""



# Z Agent token ceiling (Groq/Llama-3.3-70B context limit)
Z_AGENT_CEILING = 8192

# Risk thresholds
RISK_HIGH_THRESHOLD = 7000
RISK_MEDIUM_THRESHOLD = 5500


def check_z_agent_response(
    output_tokens: int,
    ceiling: int = Z_AGENT_CEILING
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

    if output_tokens >= ceiling:
        risk_level = "CRITICAL"
    elif output_tokens > RISK_HIGH_THRESHOLD:
        risk_level = "HIGH"
    elif output_tokens > RISK_MEDIUM_THRESHOLD:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "token_count": output_tokens,
        "ceiling": ceiling,
        "utilization": f"{utilization_pct:.1f}%",
        "risk_level": risk_level,
        "truncated": output_tokens >= ceiling,
    }


def is_z_response_safe(output_tokens: int, ceiling: int = Z_AGENT_CEILING) -> bool:
    """Return True if Z Agent response is below HIGH risk threshold."""
    return output_tokens <= RISK_HIGH_THRESHOLD
