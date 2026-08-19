"""Unit tests for Token Ceiling Monitor (v0.5.3 Strategy 3)."""

import pytest
from verifimind_mcp.utils.token_monitor import (
    check_z_agent_response,
    is_z_response_safe,
    unavailable_agent_token_monitor,
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
    assert result["configured_ceiling"] == Z_AGENT_CEILING
    assert result["ceiling_source"] == "agent_config"


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


@pytest.mark.unit
def test_effective_provider_budget_scales_risk_thresholds():
    high = check_z_agent_response(
        output_tokens=2600,
        ceiling=2700,
        configured_ceiling=8192,
    )
    critical = check_z_agent_response(
        output_tokens=2700,
        ceiling=2700,
        configured_ceiling=8192,
    )

    assert high == {
        "token_count": 2600,
        "ceiling": 2700,
        "configured_ceiling": 8192,
        "ceiling_source": "provider_completion_reservation",
        "utilization": "96.3%",
        "risk_level": "HIGH",
        "truncated": False,
    }
    assert critical["risk_level"] == "CRITICAL"
    assert critical["truncated"] is True
    assert is_z_response_safe(2600, ceiling=2700) is False


@pytest.mark.unit
def test_default_threshold_equalities_preserve_the_legacy_contract():
    assert check_z_agent_response(5500)["risk_level"] == "LOW"
    assert check_z_agent_response(7000)["risk_level"] == "MEDIUM"
    assert is_z_response_safe(7000) is True


@pytest.mark.unit
def test_truncation_failure_uses_bounded_provider_metadata_only():
    exc = ValueError("Groq response truncated before completion")
    exc._completion_token_reservation = 2700
    exc._provider_reported_output_tokens = 2700

    monitor = unavailable_agent_token_monitor(
        configured_ceiling=8192,
        exc=exc,
        truncated=True,
    )

    assert monitor == {
        "token_count": 2700,
        "ceiling": 2700,
        "configured_ceiling": 8192,
        "ceiling_source": "provider_completion_reservation",
        "utilization": "100.0%",
        "risk_level": "CRITICAL",
        "truncated": True,
    }


@pytest.mark.unit
def test_failure_without_a_sent_request_never_invents_an_effective_ceiling():
    monitor = unavailable_agent_token_monitor(
        configured_ceiling=8192,
        exc=ValueError("preflight failure"),
    )

    assert monitor == {
        "token_count": None,
        "ceiling": None,
        "configured_ceiling": 8192,
        "ceiling_source": "unknown",
        "utilization": None,
        "risk_level": "UNAVAILABLE",
        "truncated": None,
    }


@pytest.mark.unit
def test_wrapped_failure_reads_only_the_bounded_numeric_cause_metadata():
    cause = ValueError("provider body must never be reflected")
    cause._completion_token_reservation = 2450
    wrapper = RuntimeError("wrapper")
    wrapper.__cause__ = cause

    monitor = unavailable_agent_token_monitor(
        configured_ceiling=8192,
        exc=wrapper,
    )

    assert monitor["ceiling"] == 2450
    assert monitor["token_count"] is None
    assert monitor["ceiling_source"] == "provider_completion_reservation"


@pytest.mark.unit
def test_wrapped_failover_truncation_remains_critical():
    from verifimind_mcp.llm.failover import FailoverTerminalError

    cause = ValueError("Groq response truncated before completion")
    cause._completion_token_reservation = 2700
    cause._provider_reported_output_tokens = 2700
    cause._provider_output_truncated = True
    wrapper = FailoverTerminalError(
        "hosted provider groq terminal failure (invalid_request)",
        [{"provider": "groq", "model": "groq/test", "outcome_class": "invalid_request"}],
        "invalid_request",
        "abcd1234",
        final_provider="groq",
    )
    wrapper.__cause__ = cause

    monitor = unavailable_agent_token_monitor(
        configured_ceiling=8192,
        exc=wrapper,
    )

    assert monitor["ceiling"] == 2700
    assert monitor["token_count"] == 2700
    assert monitor["risk_level"] == "CRITICAL"
    assert monitor["truncated"] is True
