#!/usr/bin/env python3
"""
Standardization Configuration Validation Test

Validates that the standardization configuration is properly implemented
and meets all requirements for reproducible, reliable validations.

Author: VerifiMind PEAS Team
Date: December 21, 2025
Version: 1.0.0
"""

import sys
from pathlib import Path

# Add mcp-server to path
sys.path.insert(0, str(Path(__file__).parent / "mcp-server" / "src"))

from verifimind_mcp.config.standard_config import DEFAULT_CONFIG
from verifimind_mcp.utils.retry import APIError, retry_with_backoff
from verifimind_mcp.utils.metrics import AgentMetrics, ValidationMetrics, METRICS_COLLECTOR
import asyncio
import json


def test_llm_config():
    """Test LLM configuration standardization."""
    print("\n" + "="*80)
    print("TEST 1: LLM Configuration")
    print("="*80)
    
    config = DEFAULT_CONFIG.llm
    
    tests = [
        ("X Agent Model", config.x_agent_model, "gpt-4-turbo-2024-04-09"),
        ("Z Agent Model", config.z_agent_model, "claude-3-haiku-20240307"),
        ("CS Agent Model", config.cs_agent_model, "claude-3-haiku-20240307"),
        ("Temperature", config.temperature, 0.7),
        ("Max Tokens X", config.max_tokens_x, 2000),
        ("Max Tokens Z", config.max_tokens_z, 2000),
        ("Max Tokens CS", config.max_tokens_cs, 2000),
        ("Top P", config.top_p, 0.9),
        ("Use Seed", config.use_seed, True),
        ("Seed Value", config.seed, 42),
        ("CoT Steps", config.cot_steps, 5),
    ]
    
    passed = 0
    failed = 0
    
    for name, actual, expected in tests:
        if actual == expected:
            print(f"✅ {name}: {actual}")
            passed += 1
        else:
            print(f"❌ {name}: Expected {expected}, got {actual}")
            failed += 1
    
    print(f"\nResult: {passed}/{len(tests)} passed")
    return failed == 0


def test_retry_config():
    """Test retry configuration."""
    print("\n" + "="*80)
    print("TEST 2: Retry Configuration")
    print("="*80)
    
    config = DEFAULT_CONFIG.retry
    
    tests = [
        ("Max Retries", config.max_retries, 3),
        ("Initial Delay", config.initial_delay, 1.0),
        ("Max Delay", config.max_delay, 60.0),
        ("Exponential Base", config.exponential_base, 2.0),
        ("Jitter Enabled", config.jitter, True),
        ("Retry on 429", 429 in config.retry_on_errors, True),
        ("Retry on 500", 500 in config.retry_on_errors, True),
        ("Retry on 503", 503 in config.retry_on_errors, True),
    ]
    
    passed = 0
    failed = 0
    
    for name, actual, expected in tests:
        if actual == expected:
            print(f"✅ {name}: {actual}")
            passed += 1
        else:
            print(f"❌ {name}: Expected {expected}, got {actual}")
            failed += 1
    
    # Test delay calculation
    print("\n📊 Exponential Backoff Delays:")
    for attempt in range(3):
        delay = config.calculate_delay(attempt)
        expected_base = config.initial_delay * (config.exponential_base ** attempt)
        print(f"  Attempt {attempt + 1}: {delay:.2f}s (base: {expected_base:.2f}s)")
    
    print(f"\nResult: {passed}/{len(tests)} passed")
    return failed == 0


def test_monitoring_config():
    """Test monitoring configuration."""
    print("\n" + "="*80)
    print("TEST 3: Monitoring Configuration")
    print("="*80)
    
    config = DEFAULT_CONFIG.monitoring
    
    tests = [
        ("Track Metrics", config.track_metrics, True),
        ("Track Latency", config.track_latency, True),
        ("Track Token Usage", config.track_token_usage, True),
        ("Track Cost", config.track_cost, True),
        ("Track Error Rate", config.track_error_rate, True),
        ("Track Retry Count", config.track_retry_count, True),
        ("Min Reasoning Steps", config.min_reasoning_steps, 5),
        ("Min Confidence", config.min_confidence, 0.70),
    ]
    
    passed = 0
    failed = 0
    
    for name, actual, expected in tests:
        if actual == expected:
            print(f"✅ {name}: {actual}")
            passed += 1
        else:
            print(f"❌ {name}: Expected {expected}, got {actual}")
            failed += 1
    
    print(f"\nResult: {passed}/{len(tests)} passed")
    return failed == 0


def test_metrics_tracking():
    """Test metrics tracking functionality."""
    print("\n" + "="*80)
    print("TEST 4: Metrics Tracking")
    print("="*80)
    
    # Create test metrics
    agent_metrics = AgentMetrics(
        agent_type="x",
        model_name="openai/gpt-4-turbo-2024-04-09"
    )
    
    # Simulate token usage
    agent_metrics.input_tokens = 1000
    agent_metrics.output_tokens = 500
    agent_metrics.total_tokens = 1500
    agent_metrics.success = True
    agent_metrics.finish()
    
    # Calculate cost
    agent_metrics.calculate_cost("openai")
    
    print(f"✅ Agent Metrics Created")
    print(f"  - Latency: {agent_metrics.latency:.3f}s")
    print(f"  - Input Tokens: {agent_metrics.input_tokens}")
    print(f"  - Output Tokens: {agent_metrics.output_tokens}")
    print(f"  - Total Cost: ${agent_metrics.total_cost:.6f}")
    print(f"  - Success: {agent_metrics.success}")
    
    # Create validation metrics
    validation_metrics = ValidationMetrics(
        validation_id="test_001",
        concept_name="Test Concept"
    )
    
    validation_metrics.x_agent = agent_metrics
    validation_metrics.finish()
    
    print(f"\n✅ Validation Metrics Created")
    print(f"  - Total Duration: {validation_metrics.total_duration:.3f}s")
    print(f"  - Total Tokens: {validation_metrics.total_tokens}")
    print(f"  - Total Cost: ${validation_metrics.total_cost:.6f}")
    print(f"  - Success: {validation_metrics.success}")
    
    return True


async def test_retry_logic():
    """Test retry logic with simulated failures."""
    print("\n" + "="*80)
    print("TEST 5: Retry Logic")
    print("="*80)
    
    # Test 1: Immediate success
    print("\n📝 Test 5.1: Immediate Success")
    call_count = 0
    
    async def success_func():
        nonlocal call_count
        call_count += 1
        return "success"
    
    result = await retry_with_backoff(success_func, max_retries=3)
    print(f"✅ Result: {result}, Calls: {call_count}")
    assert call_count == 1, "Should succeed on first try"
    
    # Test 2: Retry on 429
    print("\n📝 Test 5.2: Retry on Rate Limit (429)")
    call_count = 0
    
    async def retry_429_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise APIError(429, "Rate limit exceeded")
        return "success after retries"
    
    result = await retry_with_backoff(retry_429_func, max_retries=3)
    print(f"✅ Result: {result}, Calls: {call_count}")
    assert call_count == 3, "Should retry twice before success"
    
    # Test 3: Non-retryable error
    print("\n📝 Test 5.3: Non-Retryable Error (400)")
    call_count = 0
    
    async def non_retryable_func():
        nonlocal call_count
        call_count += 1
        raise APIError(400, "Bad request")
    
    try:
        await retry_with_backoff(non_retryable_func, max_retries=3)
        print("❌ Should have raised APIError")
        return False
    except APIError as e:
        print(f"✅ Correctly raised APIError: {e.message}, Calls: {call_count}")
        assert call_count == 1, "Should not retry on 400"
    
    print("\n✅ All retry logic tests passed!")
    return True


def test_config_export():
    """Test configuration export to dict/JSON."""
    print("\n" + "="*80)
    print("TEST 6: Configuration Export")
    print("="*80)
    
    config_dict = DEFAULT_CONFIG.to_dict()
    
    print("✅ Configuration exported to dictionary")
    print(f"  - LLM Config Keys: {list(config_dict['llm'].keys())}")
    print(f"  - Retry Config Keys: {list(config_dict['retry'].keys())}")
    print(f"  - Rate Limit Config Keys: {list(config_dict['rate_limit'].keys())}")
    print(f"  - Monitoring Config Keys: {list(config_dict['monitoring'].keys())}")
    
    # Test JSON serialization
    json_str = json.dumps(config_dict, indent=2)
    print(f"\n✅ Configuration serialized to JSON ({len(json_str)} bytes)")
    
    # Save to file
    output_file = Path(__file__).parent / "examples" / "standardization_tests" / "config.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json_str)
    print(f"✅ Configuration saved to: {output_file}")
    
    return True


async def main():
    """Run all standardization tests."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║           VerifiMind PEAS Standardization Protocol v1.0                      ║
║                                                                              ║
║                      CONFIGURATION VALIDATION TESTS                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    results = []
    
    # Run tests
    results.append(("LLM Configuration", test_llm_config()))
    results.append(("Retry Configuration", test_retry_config()))
    results.append(("Monitoring Configuration", test_monitoring_config()))
    results.append(("Metrics Tracking", test_metrics_tracking()))
    results.append(("Retry Logic", await test_retry_logic()))
    results.append(("Config Export", test_config_export()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{'='*80}")
    print(f"OVERALL: {passed}/{total} tests passed")
    print(f"{'='*80}")
    
    if passed == total:
        print("\n🎉 ALL STANDARDIZATION TESTS PASSED!")
        print("\n✅ Standardization Protocol v1.0 is properly configured and ready for use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the configuration.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
