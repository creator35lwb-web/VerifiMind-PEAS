"""v0.5.62 privacy-minimal tool invocation telemetry contracts."""

import json
from types import SimpleNamespace

import pytest
from fastmcp import Client

from verifimind_mcp.middleware.tool_invocation import (
    INSTRUMENTED_TOOL_NAMES,
    ToolInvocationTelemetry,
)
from verifimind_mcp.server import _create_mcp_instance


def _events(stderr: str) -> list[dict]:
    events = []
    for line in stderr.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("event") == "tool_invoked":
            events.append(payload)
    return events


@pytest.mark.asyncio
async def test_allowlist_equals_the_exact_registered_tool_set():
    app = _create_mcp_instance()
    registered = {
        tool.name for tool in await app.list_tools(run_middleware=False)
    }

    assert len(registered) == 13
    assert INSTRUMENTED_TOOL_NAMES == registered
    assert sum(
        isinstance(item, ToolInvocationTelemetry) for item in app.middleware
    ) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name", sorted(INSTRUMENTED_TOOL_NAMES))
async def test_every_registered_tool_emits_one_exact_name_only_event(
    tool_name, capsys
):
    middleware = ToolInvocationTelemetry()
    context = SimpleNamespace(message=SimpleNamespace(
        name=tool_name,
        arguments={"api_key": "gsk_SECRET", "concept": "PRIVATE-CONCEPT"},
    ))
    calls = 0

    async def call_next(received_context):
        nonlocal calls
        calls += 1
        assert received_context is context
        return "ok"

    assert await middleware.on_call_tool(context, call_next) == "ok"
    assert calls == 1
    assert _events(capsys.readouterr().err) == [{
        "severity": "INFO",
        "event": "tool_invoked",
        "tool": tool_name,
    }]


@pytest.mark.asyncio
async def test_event_survives_handler_exception_without_reflecting_arguments(capsys):
    secret = "UUID-AND-API-KEY-MUST-NOT-APPEAR"
    middleware = ToolInvocationTelemetry()
    context = SimpleNamespace(message=SimpleNamespace(
        name="run_full_trinity",
        arguments={"concept_description": secret},
    ))

    async def fail(_context):
        raise RuntimeError(secret)

    with pytest.raises(RuntimeError, match=secret):
        await middleware.on_call_tool(context, fail)

    stderr = capsys.readouterr().err
    assert secret not in stderr
    assert _events(stderr) == [{
        "severity": "INFO",
        "event": "tool_invoked",
        "tool": "run_full_trinity",
    }]


@pytest.mark.asyncio
async def test_internal_attempts_do_not_multiply_the_outer_event(capsys):
    middleware = ToolInvocationTelemetry()
    context = SimpleNamespace(message=SimpleNamespace(name="consult_agent_z"))
    attempts = []

    async def internally_retried(_context):
        attempts.extend(("first", "second"))
        return "recovered"

    assert await middleware.on_call_tool(context, internally_retried) == "recovered"
    assert attempts == ["first", "second"]
    assert len(_events(capsys.readouterr().err)) == 1


@pytest.mark.asyncio
async def test_unknown_caller_controlled_tool_name_is_not_emitted(capsys):
    middleware = ToolInvocationTelemetry()
    context = SimpleNamespace(message=SimpleNamespace(
        name="consult_agent_x!!!ATTACKER-LABEL"
    ))

    async def call_next(_context):
        return "unknown"

    assert await middleware.on_call_tool(context, call_next) == "unknown"
    assert _events(capsys.readouterr().err) == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "tool_name",
    ("list_prompt_templates", "coordination_team_status"),
)
async def test_real_fastmcp_success_and_contained_paths_each_emit_once(
    tool_name, capsys
):
    app = _create_mcp_instance()
    async with Client(app) as client:
        await client.call_tool(tool_name, {})

    matching = [
        event for event in _events(capsys.readouterr().err)
        if event["tool"] == tool_name
    ]
    assert matching == [{
        "severity": "INFO",
        "event": "tool_invoked",
        "tool": tool_name,
    }]
