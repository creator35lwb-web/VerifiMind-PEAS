"""
Coordination-layer containment contract — VM-IR-2026-07-28-COORD-01
===================================================================

P0 incident: the three `coordination_*` tools resolved a CALLER-SUPPLIED
`pioneer_key` into a storage namespace, defaulting to the shared literal
"anonymous" when omitted. Any anonymous internet caller could read complete
handoff bodies, agent identities, pending actions and blockers written by
anyone else who omitted the key — and could write records under an arbitrary
`agent_id` into state that AI agents consume as authoritative coordination
truth (an instruction-injection surface with a trusted provenance stamp).

The invariant that was violated (T S111 RC-1):

    Free access to a tool does not imply shared access to the data
    created through that tool.

A supplied key was never an authorization boundary either: `check_tier()` ran
and its `allowed` result was discarded, so ANY string selected a namespace.
Bearer-string obscurity is not authenticated isolation — so containment denies
every caller, keyed or keyless, rather than leaving an undocumented
compatibility path (T D-111-2 / D-111-5).

These tests encode T's C0 exit criteria. They are the inverse of the contract
that let this ship: `test_v0550_robustness_walk.py::test_coordination_tools_walk`
previously asserted that a keyless create SUCCEEDS (RC-5). A security oracle
must assert the denial, and must assert that the denial leaks nothing.
"""

import json

import pytest

from fastmcp import Client

from verifimind_mcp.server import create_http_server


CONTAINED_TOOLS = (
    "coordination_handoff_create",
    "coordination_handoff_read",
    "coordination_team_status",
)

DENIAL_CODE = "COORDINATION_TEMPORARILY_DISABLED"

# Every credential shape a caller can present. Containment must deny ALL of
# them identically: absent, blank, whitespace, arbitrary string, well-formed
# UUID, and the all-zero UUID (T's own step-4 probes).
CREDENTIAL_SHAPES = (
    ("absent", {}),
    ("blank", {"pioneer_key": ""}),
    ("whitespace", {"pioneer_key": "   "}),
    ("arbitrary_string", {"pioneer_key": "not-a-uuid-at-all-just-a-string"}),
    ("zero_uuid", {"pioneer_key": "00000000-0000-0000-0000-000000000000"}),
    ("wellformed_uuid", {"pioneer_key": "3f2504e0-4f89-11d3-9a0c-0305e82c3301"}),
)

CREATE_ARGS = {
    "agent_id": "RNA-CONTAINMENT-PROBE",
    "session_type": "containment-contract",
    "completed": ["probe"],
    "decisions": [],
    "artifacts": [],
    "pending": [],
    "blockers": [],
}

# Field names that only ever appear when stored state is being disclosed.
DISCLOSURE_FIELDS = (
    "content", "handoff_id", "handoffs", "total_handoffs", "active_agents",
    "pending_actions", "open_blockers", "recent_activity",
    "most_recent_handoff", "recommended_next", "filename", "suggested_path",
)


@pytest.fixture(scope="module")
def app():
    return create_http_server()


def payload_of(result):
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                continue
    raise AssertionError(f"no dict payload in tool result: {result!r}")


async def call(app, name, args):
    async with Client(app) as client:
        return payload_of(await client.call_tool(name, args))


def args_for(tool, credential):
    args = dict(credential)
    if tool == "coordination_handoff_create":
        args.update(CREATE_ARGS)
    return args


@pytest.mark.asyncio
@pytest.mark.parametrize("tool", CONTAINED_TOOLS)
@pytest.mark.parametrize("shape,credential", CREDENTIAL_SHAPES,
                         ids=[s for s, _ in CREDENTIAL_SHAPES])
async def test_every_credential_shape_is_denied(app, tool, shape, credential):
    """C0 exit criteria 1-4: create, read and status all fail closed for every
    credential shape — including a well-formed UUID, because a bearer string
    the server never bound to an authenticated principal is not authorization."""
    result = await call(app, tool, args_for(tool, credential))
    assert result.get("status") == "error", (tool, shape, result)
    assert result.get("error_code") == DENIAL_CODE, (tool, shape, result)


@pytest.mark.asyncio
@pytest.mark.parametrize("tool", CONTAINED_TOOLS)
async def test_denial_discloses_no_stored_state(app, tool):
    """The denial must not carry any stored-state field. A maintenance response
    that still returned counts or agent names would keep the enumeration step
    of the disclosure chain alive."""
    result = await call(app, tool, args_for(tool, {}))
    for field in DISCLOSURE_FIELDS:
        assert field not in result, (tool, field, result)


@pytest.mark.asyncio
@pytest.mark.parametrize("tool", CONTAINED_TOOLS)
async def test_denial_does_not_reflect_caller_input(app, tool):
    """The denial must not echo caller-supplied values. Reflecting the key or
    the agent id would turn the error itself into a namespace probe."""
    secret_key = "probe-key-must-not-be-reflected"
    args = args_for(tool, {"pioneer_key": secret_key})
    blob = json.dumps(await call(app, tool, args))
    assert secret_key not in blob, (tool, blob)
    assert "anonymous" not in blob, (tool, blob)
    if tool == "coordination_handoff_create":
        assert CREATE_ARGS["agent_id"] not in blob, (tool, blob)


@pytest.mark.asyncio
async def test_create_stores_nothing_while_contained(app):
    """Containment must stop the WRITE, not merely hide the read. Asserted
    against the store itself: a denied create leaves every namespace it could
    have targeted untouched."""
    from verifimind_mcp.coordination import get_store

    store = get_store()
    probed = ("anonymous", "probe-key-must-not-be-reflected")
    before = {ns: len(store.get_all(ns)) for ns in probed}

    for credential in ({}, {"pioneer_key": "probe-key-must-not-be-reflected"}):
        result = await call(app, "coordination_handoff_create",
                            args_for("coordination_handoff_create", credential))
        assert result.get("error_code") == DENIAL_CODE, result

    after = {ns: len(store.get_all(ns)) for ns in probed}
    assert after == before, (before, after)


@pytest.mark.asyncio
async def test_contained_tools_remain_registered(app):
    """Containment denies behaviour, not existence: the tools stay listed so
    the published tool contract and manifests remain truthful, and clients get
    an actionable error instead of an unknown-tool failure."""
    async with Client(app) as client:
        listed = {t.name for t in await client.list_tools()}
    for tool in CONTAINED_TOOLS:
        assert tool in listed, (tool, sorted(listed))


@pytest.mark.asyncio
@pytest.mark.parametrize("tool", CONTAINED_TOOLS)
async def test_denial_is_actionable_and_incident_referenced(app, tool):
    """An honest denial tells the caller what to do instead and carries the
    incident reference, so the maintenance state is auditable rather than
    mysterious."""
    result = await call(app, tool, args_for(tool, {}))
    hint = json.dumps(result)
    assert "VM-IR-2026-07-28-COORD-01" in hint, (tool, result)
    assert "repository" in hint.lower(), (tool, result)


def test_no_handler_resolves_a_caller_supplied_namespace():
    """Source-level invariant (the defect's exact shape): no coordination
    handler may fall back to a shared literal namespace or derive one from
    caller input. Guards against a future edit reintroducing the pattern in a
    handler that this suite's behavioural tests do not yet cover."""
    from pathlib import Path

    source = Path(__file__).resolve().parents[2] / "src" / "verifimind_mcp" / "server.py"
    text = source.read_text(encoding="utf-8")

    # The exact fail-open idiom that caused the incident.
    assert 'else "anonymous"' not in text, (
        "a handler still falls back to the shared 'anonymous' namespace"
    )
    # `pioneer_key` may appear as an accepted-and-ignored argument, but must
    # never again be assigned into a namespace variable.
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("namespace =") or stripped.startswith("namespace="):
            assert "pioneer_key" not in stripped, (
                f"namespace is still derived from caller input: {stripped}"
            )
