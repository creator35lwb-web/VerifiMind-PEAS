"""Registration-auth gate contract (RNA S152).

The gate is DARK by default: with REGISTRATION_GATE_ENABLED unset, tool
execution is byte-identical to the ungated server. When enabled, the four
execution tools require a server-verified registered UUID from the
X-VerifiMind-UUID header; verification FAILS CLOSED; denials carry no
caller-supplied identifier; discovery and template reads stay anonymous.
"""

import json
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from verifimind_mcp.middleware import registration_gate as gate_mod
from verifimind_mcp.middleware.registration_gate import (
    GATED_TOOL_NAMES,
    RegistrationGate,
    VERIFIED_REGISTERED_UUID,
    registration_gate_enabled,
)
from verifimind_mcp.middleware.tool_invocation import INSTRUMENTED_TOOL_NAMES
from verifimind_mcp.registration_lookup import (
    NOT_REGISTERED,
    REGISTERED,
    UNAVAILABLE,
    RegistrationState,
)

REGISTERED_UUID = "018f6b2a-1111-7abc-8def-0123456789ab"


def _ctx(tool_name):
    return SimpleNamespace(message=SimpleNamespace(name=tool_name))


def _events(err):
    return [
        json.loads(line)
        for line in err.splitlines()
        if line.startswith("{") and '"event"' in line
    ]


async def _run(monkeypatch, tool, *, enabled, header, state, capsys):
    monkeypatch.setenv(
        "REGISTRATION_GATE_ENABLED", "true" if enabled else "false"
    )
    monkeypatch.setattr(gate_mod, "_request_header_uuid", lambda: header)
    monkeypatch.setattr(gate_mod, "resolve_registration", lambda _u: state)
    called = {}

    async def call_next(_context):
        called["yes"] = True
        called["ctxvar"] = VERIFIED_REGISTERED_UUID.get()
        return {"status": "success"}

    result = await RegistrationGate().on_call_tool(_ctx(tool), call_next)
    return result, called, _events(capsys.readouterr().err)


class TestFlagContract:
    def test_gate_is_dark_by_default(self, monkeypatch):
        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)
        assert registration_gate_enabled() is False

    @pytest.mark.asyncio
    async def test_flag_off_passes_gated_tool_with_no_header(
        self, monkeypatch, capsys
    ):
        result, called, events = await _run(
            monkeypatch, "run_full_trinity",
            enabled=False, header="",
            state=RegistrationState(NOT_REGISTERED), capsys=capsys,
        )
        assert called.get("yes") and result == {"status": "success"}
        assert events == []  # no gate events while dark

    def test_gated_set_is_the_four_execution_tools(self):
        assert GATED_TOOL_NAMES == {
            "consult_agent_x", "consult_agent_z", "consult_agent_cs",
            "run_full_trinity",
        }
        assert GATED_TOOL_NAMES <= INSTRUMENTED_TOOL_NAMES


class TestDenials:
    @pytest.mark.asyncio
    async def test_absent_header_denies_without_calling_handler(
        self, monkeypatch, capsys
    ):
        result, called, events = await _run(
            monkeypatch, "run_full_trinity",
            enabled=True, header="",
            state=RegistrationState(REGISTERED), capsys=capsys,
        )
        payload = result.structured_content
        assert called == {}
        assert payload["error_code"] == "REGISTRATION_REQUIRED"
        assert payload["retryable"] is False
        assert "register" in payload["recovery_hint"].lower()
        assert [e["event"] for e in events] == ["tool_denied"]
        assert events[0]["reason"] == "registration_required"

    @pytest.mark.asyncio
    async def test_invalid_format_header_denies_with_fix_hint(
        self, monkeypatch, capsys
    ):
        result, called, _ = await _run(
            monkeypatch, "consult_agent_x",
            enabled=True, header="not-a-uuid",
            state=RegistrationState(REGISTERED), capsys=capsys,
        )
        assert called == {}
        assert "not a valid UUID" in result.structured_content["recovery_hint"]

    @pytest.mark.asyncio
    async def test_unregistered_uuid_denies(self, monkeypatch, capsys):
        result, called, events = await _run(
            monkeypatch, "consult_agent_z",
            enabled=True, header=REGISTERED_UUID,
            state=RegistrationState(NOT_REGISTERED), capsys=capsys,
        )
        assert called == {}
        assert result.structured_content["error_code"] == "REGISTRATION_REQUIRED"
        assert "not a registered identity" in (
            result.structured_content["recovery_hint"]
        )

    @pytest.mark.asyncio
    async def test_lookup_outage_fails_closed_and_retryable(
        self, monkeypatch, capsys
    ):
        # Inverted default: an outage must DENY, never admit (S111).
        result, called, events = await _run(
            monkeypatch, "consult_agent_cs",
            enabled=True, header=REGISTERED_UUID,
            state=RegistrationState(UNAVAILABLE), capsys=capsys,
        )
        payload = result.structured_content
        assert called == {}
        assert payload["error_code"] == "REGISTRATION_CHECK_UNAVAILABLE"
        assert payload["retryable"] is True
        assert events[0]["reason"] == "registration_check_unavailable"

    @pytest.mark.asyncio
    async def test_denied_events_never_carry_caller_input(
        self, monkeypatch, capsys
    ):
        attacker_string = "11111111-2222-7333-8444-555566667777"
        _, _, events = await _run(
            monkeypatch, "run_full_trinity",
            enabled=True, header=attacker_string,
            state=RegistrationState(NOT_REGISTERED), capsys=capsys,
        )
        for event in events:
            assert attacker_string not in json.dumps(event)
            assert "registered_uuid" not in event

    @pytest.mark.asyncio
    async def test_denial_copy_carries_no_paywall_claim_shapes(
        self, monkeypatch, capsys
    ):
        result, _, _ = await _run(
            monkeypatch, "run_full_trinity",
            enabled=True, header="",
            state=RegistrationState(NOT_REGISTERED), capsys=capsys,
        )
        text = json.dumps(result.structured_content)
        for banned in ("Upgrade to Pioneer", "Pioneer tier", "$", "paid"):
            assert banned not in text
        assert "free" in text.lower()


class TestAuthorizedPath:
    @pytest.mark.asyncio
    async def test_registered_uuid_authorizes_and_binds_contextvar(
        self, monkeypatch, capsys
    ):
        result, called, events = await _run(
            monkeypatch, "run_full_trinity",
            enabled=True, header=REGISTERED_UUID,
            state=RegistrationState(REGISTERED, source="ea_registrations"),
            capsys=capsys,
        )
        assert result == {"status": "success"}
        # The verified identity was visible DURING the handler and is
        # reset afterwards.
        assert called["ctxvar"] == REGISTERED_UUID
        assert VERIFIED_REGISTERED_UUID.get() is None
        assert [e["event"] for e in events] == ["tool_authorized"]
        assert events[0]["registered_uuid"] == REGISTERED_UUID
        assert events[0]["tool"] == "run_full_trinity"

    @pytest.mark.asyncio
    async def test_ungated_tool_passes_anonymously_with_flag_on(
        self, monkeypatch, capsys
    ):
        result, called, events = await _run(
            monkeypatch, "list_prompt_templates",
            enabled=True, header="",
            state=RegistrationState(NOT_REGISTERED), capsys=capsys,
        )
        assert called.get("yes") and result == {"status": "success"}
        assert events == []


class TestEndToEnd:
    """Real registered tools through the in-process fastmcp client."""

    @pytest.fixture
    def app(self):
        from verifimind_mcp import server as server_mod
        return server_mod.create_http_server()

    @pytest.mark.asyncio
    async def test_gated_denial_emits_no_lifecycle_events(
        self, app, monkeypatch, capsys
    ):
        # In-process clients have no HTTP header -> absent -> denial. The
        # denied Trinity call must not enter the completion-rate
        # denominator: zero started, zero completed.
        from .mcp_tool_harness import call
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        payload = await call(app, "run_full_trinity", {
            "concept_name": "gate-denial-probe",
            "concept_description": "registration gate denial walk.",
        })
        assert payload["error_code"] == "REGISTRATION_REQUIRED"
        err = capsys.readouterr().err
        assert '"trinity_run_started"' not in err
        assert '"trinity_run_completed"' not in err
        assert '"tool_invoked"' in err   # dispatch-attempt layer unchanged
        assert '"tool_denied"' in err

    @pytest.mark.asyncio
    async def test_authorized_trinity_run_joins_lifecycle_to_uuid(
        self, app, monkeypatch, capsys
    ):
        from .mcp_tool_harness import call
        from verifimind_mcp import config_helper

        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setattr(
            gate_mod, "_request_header_uuid", lambda: REGISTERED_UUID
        )
        monkeypatch.setattr(
            gate_mod, "resolve_registration",
            lambda _u: RegistrationState(REGISTERED, source="early_adopters"),
        )

        def _boom(_provider, _key, _agent):
            raise ValueError("unknown provider prefix")

        # Force a fast, deterministic error-outcome run (no live provider):
        # the lifecycle pair still fires, and both events must carry the
        # VERIFIED header identity.
        monkeypatch.setattr(config_helper, "create_ephemeral_provider", _boom)
        payload = await call(app, "run_full_trinity", {
            "concept_name": "gate-join-probe",
            "concept_description": "registered lifecycle join walk.",
            "llm_provider": "bogus-provider",
            "api_key": "not-a-real-key",
        })
        assert payload["status"] == "error"
        err = capsys.readouterr().err
        events = _events(err)
        started = [e for e in events if e["event"] == "trinity_run_started"]
        completed = [e for e in events if e["event"] == "trinity_run_completed"]
        authorized = [e for e in events if e["event"] == "tool_authorized"]
        assert len(started) == len(completed) == len(authorized) == 1
        assert started[0]["registered_uuid"] == REGISTERED_UUID
        assert completed[0]["registered_uuid"] == REGISTERED_UUID

    @pytest.mark.asyncio
    async def test_flag_off_lifecycle_events_carry_no_uuid_field(
        self, app, monkeypatch, capsys
    ):
        from .mcp_tool_harness import call
        from verifimind_mcp import config_helper

        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)

        def _boom(_provider, _key, _agent):
            raise ValueError("unknown provider prefix")

        monkeypatch.setattr(config_helper, "create_ephemeral_provider", _boom)
        payload = await call(app, "run_full_trinity", {
            "concept_name": "dark-gate-parity-probe",
            "concept_description": "flag-off lifecycle parity walk.",
            "llm_provider": "bogus-provider",
            "api_key": "not-a-real-key",
        })
        assert payload["status"] == "error"
        events = _events(capsys.readouterr().err)
        for event in events:
            if event["event"].startswith("trinity_run_"):
                assert "registered_uuid" not in event


class TestQuarantineUnaffected:
    @pytest.mark.asyncio
    async def test_registered_identity_does_not_unlock_contained_tools(
        self, monkeypatch, capsys
    ):
        # Registration never satisfies Gate R0: the coordination tools are
        # NOT in the gated set (they fail closed in their handlers for every
        # caller), so the gate passes the call through to the containment
        # denial rather than minting an authorization of its own.
        _, called, events = await _run(
            monkeypatch, "coordination_handoff_read",
            enabled=True, header=REGISTERED_UUID,
            state=RegistrationState(REGISTERED), capsys=capsys,
        )
        assert called.get("yes")  # handler (containment denial) still owns it
        assert events == []       # no tool_authorized for ungated tools


class TestPolicyNotice:
    def test_gate_effective_date_honors_14_day_notice(self):
        # The Terms v2.4 promise, machine-checked: the activation date must
        # sit at least 14 days after the v2.5/v2.6 policy publication date.
        from verifimind_mcp.policies.activation_notice import (
            REGISTRATION_GATE_EFFECTIVE_DATE,
        )
        from verifimind_mcp.policies.privacy_policy import (
            PRIVACY_POLICY_EFFECTIVE_DATE,
        )
        from verifimind_mcp.policies.terms import TERMS_EFFECTIVE_DATE

        gate_day = date.fromisoformat(REGISTRATION_GATE_EFFECTIVE_DATE)
        for published in (TERMS_EFFECTIVE_DATE, PRIVACY_POLICY_EFFECTIVE_DATE):
            assert gate_day >= (
                date.fromisoformat(published) + timedelta(days=14)
            )

    def test_both_policies_carry_the_activation_date(self):
        from verifimind_mcp.policies.activation_notice import (
            REGISTRATION_GATE_EFFECTIVE_HUMAN_EN,
            REGISTRATION_GATE_EFFECTIVE_HUMAN_MS,
        )
        from verifimind_mcp.policies.privacy_policy import PRIVACY_POLICY
        from verifimind_mcp.policies.terms import TERMS_AND_CONDITIONS

        assert REGISTRATION_GATE_EFFECTIVE_HUMAN_EN in TERMS_AND_CONDITIONS
        assert REGISTRATION_GATE_EFFECTIVE_HUMAN_EN in PRIVACY_POLICY
        assert REGISTRATION_GATE_EFFECTIVE_HUMAN_MS in PRIVACY_POLICY

    def test_contract_projects_gate_state_truthfully(self, monkeypatch):
        from verifimind_mcp.contract import get_public_contract

        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)
        dark = get_public_contract()["registration"]
        assert dark["execution_gate_enabled"] is False
        assert dark["pricing"] == "free"
        assert "without registration" in dark["summary"]

        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        lit = get_public_contract()["registration"]
        assert lit["execution_gate_enabled"] is True
        assert sorted(GATED_TOOL_NAMES) == lit["gated_tools"]
        assert "free" in lit["summary"]
