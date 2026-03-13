"""Unit tests for Token Ceiling Monitor (v0.5.3 Strategy 3)."""

import pytest
from verifimind_mcp.utils.token_monitor import (
    check_z_agent_response,
    is_z_response_safe,
    Z_AGENT_CEILING,
    RISK_HIGH_THRESHOLD,
    RISK_MEDIUM_THRESHOLD,
)


@pytest.mark.unit
def test_token_monitor_exists_and_returns_required_fields():
    """Token monitor returns all required fields."""
    result = check_z_agent_response(output_tokens=4450)
    assert "token_count" in result
    assert "ceiling" in result
    assert "utilization" in result
    assert "risk_level" in result
    assert "truncated" in result
    assert result["token_count"] == 4450
    assert result["ceiling"] == Z_AGENT_CEILING


@pytest.mark.unit
def test_token_monitor_risk_level_thresholds():
    """Risk levels are correctly assigned at threshold boundaries."""
    # LOW — below MEDIUM threshold
    low = check_z_agent_response(output_tokens=RISK_MEDIUM_THRESHOLD - 1)
    assert low["risk_level"] == "LOW"
    assert low["truncated"] is False

    # MEDIUM — above MEDIUM, below HIGH
    medium = check_z_agent_response(output_tokens=RISK_MEDIUM_THRESHOLD + 1)
    assert medium["risk_level"] == "MEDIUM"
    assert medium["truncated"] is False

    # HIGH — above HIGH threshold, below ceiling
    high = check_z_agent_response(output_tokens=RISK_HIGH_THRESHOLD + 1)
    assert high["risk_level"] == "HIGH"
    assert high["truncated"] is False

    # CRITICAL — at or above ceiling
    critical = check_z_agent_response(output_tokens=Z_AGENT_CEILING)
    assert critical["risk_level"] == "CRITICAL"
    assert critical["truncated"] is True


@pytest.mark.unit
def test_token_monitor_truncation_guard():
    """Truncated flag fires correctly and is_z_response_safe reflects HIGH risk."""
    # Normal Z Agent response after v4.2 mitigation (~4450 tokens)
    normal = check_z_agent_response(output_tokens=4450)
    assert normal["truncated"] is False
    assert is_z_response_safe(4450) is True

    # Response approaching ceiling
    near_ceiling = check_z_agent_response(output_tokens=7500)
    assert near_ceiling["truncated"] is False
    assert is_z_response_safe(7500) is False  # HIGH risk

    # Response at ceiling — truncated
    truncated = check_z_agent_response(output_tokens=8192)
    assert truncated["truncated"] is True
    assert is_z_response_safe(8192) is False

    # Zero tokens (fallback / mock response)
    zero = check_z_agent_response(output_tokens=0)
    assert zero["risk_level"] == "LOW"
    assert zero["truncated"] is False
    assert zero["utilization"] == "0.0%"
