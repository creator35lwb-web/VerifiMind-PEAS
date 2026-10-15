"""Registration-gate v2 contract (Design v2 — T S152/S153 consumed).

Dark parity by default; when enabled the four execution tools require the
authenticated subject bound by the HTTP boundary; the ``user_uuid``
argument confers nothing and mismatches FAIL CLOSED (P0 #5); events carry
HMAC-pseudonymous subjects, never raw UUIDs (P0 #6); ``tool_admitted``
proves admission only and ``tool_completed`` is the terminal evidence unit
(P0 #8); denied Trinity calls emit zero lifecycle events.
"""

import json
from contextvars import ContextVar
from types import SimpleNamespace

import pytest

from verifimind_mcp.middleware import registration_gate as gate_mod
from verifimind_mcp.middleware.registration_gate import (
    AUTH_ACTOR_CLASS,
    AUTH_SUBJECT_UUID,
    GATED_TOOL_NAMES,
    RegistrationGate,
    VERIFIED_SUBJECT_HMAC,
    registration_gate_enabled,
)
from verifimind_mcp.middleware.tool_invocation import INSTRUMENTED_TOOL_NAMES

SUBJECT_UUID = "018f6b2a-1111-7abc-8def-0123456789ab"
HMAC_KEY = "test-hmac-key-for-subjects"


def _ctx(tool_name, arguments=None):
    return SimpleNamespace(
        message=SimpleNamespace(name=tool_name, arguments=arguments or {})
    )


def _events(err):
    return [
        json.loads(line)
        for line in err.splitlines()
        if line.startswith("{") and '"event"' in line
    ]


async def _run(monkeypatch, tool, *, enabled, subject, capsys,
               arguments=None, actor="external", handler_payload=None,
               handler_raises=False):
    monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true" if enabled else "false")
    monkeypatch.setenv("VALUE_SUBJECT_HMAC_KEY", HMAC_KEY)
    subject_token = AUTH_SUBJECT_UUID.set(subject)
    actor_token = AUTH_ACTOR_CLASS.set(actor if subject else None)
    called = {}

    async def call_next(_context):
        called["yes"] = True
        called["hmac_ctx"] = VERIFIED_SUBJECT_HMAC.get()
        if handler_raises:
            raise RuntimeError("handler exploded")
        payload = handler_payload if handler_payload is not None else {
            "status": "success", "_inference_quality": "real",
        }
        return SimpleNamespace(structured_content=payload, content=[])

    try:
        result = await RegistrationGate().on_call_tool(
            _ctx(tool, arguments), call_next
        )
    finally:
        AUTH_SUBJECT_UUID.reset(subject_token)
        AUTH_ACTOR_CLASS.reset(actor_token)
    return result, called, _events(capsys.readouterr().err)


class TestFlagContract:
    def test_gate_is_dark_by_default(self, monkeypatch):
        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)
        assert registration_gate_enabled() is False

    @pytest.mark.asyncio
    async def test_flag_off_passes_gated_tool_with_no_subject(
        self, monkeypatch, capsys
    ):
        result, called, events = await _run(
            monkeypatch, "run_full_trinity",
            enabled=False, subject=None, capsys=capsys,
        )
        assert called.get("yes")
        assert events == []  # no gate events while dark

    def test_gated_set_is_the_four_execution_tools(self):
        assert GATED_TOOL_NAMES == {
            "consult_agent_x", "consult_agent_z", "consult_agent_cs",
            "run_full_trinity",
        }
        assert GATED_TOOL_NAMES <= INSTRUMENTED_TOOL_NAMES


class TestDenials:
    @pytest.mark.asyncio
    async def test_no_authenticated_subject_denies(self, monkeypatch, capsys):
        result, called, events = await _run(
            monkeypatch, "run_full_trinity",
            enabled=True, subject=None, capsys=capsys,
        )
        payload = result.structured_content
        assert called == {}
        assert payload["error_code"] == "AUTHENTICATION_REQUIRED"
        assert payload["resource_metadata"].endswith(
            "/.well-known/oauth-protected-resource"
        )
        assert [e["event"] for e in events] == ["tool_denied"]
        assert events[0]["reason"] == "authentication_required"

    @pytest.mark.asyncio
    async def test_cross_subject_user_uuid_fails_closed(
        self, monkeypatch, capsys
    ):
        other = "99999999-2222-7333-8444-555566667777"
        result, called, events = await _run(
            monkeypatch, "consult_agent_x",
            enabled=True, subject=SUBJECT_UUID, capsys=capsys,
            arguments={"user_uuid": other, "concept": "x"},
        )
        assert called == {}
        assert result.structured_content["error_code"] == "CROSS_SUBJECT_MISMATCH"
        assert events[0]["reason"] == "cross_subject_mismatch"
        # Neither the mismatched claim nor the real subject leaks (P0 #6).
        blob = json.dumps(events)
        assert other not in blob and SUBJECT_UUID not in blob

    @pytest.mark.asyncio
    async def test_matching_user_uuid_argument_is_allowed(
        self, monkeypatch, capsys
    ):
        result, called, events = await _run(
            monkeypatch, "consult_agent_z",
            enabled=True, subject=SUBJECT_UUID, capsys=capsys,
            arguments={"user_uuid": SUBJECT_UUID},
        )
        assert called.get("yes")
        assert {e["event"] for e in events} == {"tool_admitted", "tool_completed"}

    @pytest.mark.asyncio
    async def test_denial_copy_carries_no_paywall_claim_shapes(
        self, monkeypatch, capsys
    ):
        result, _, _ = await _run(
            monkeypatch, "run_full_trinity",
            enabled=True, subject=None, capsys=capsys,
        )
        text = json.dumps(result.structured_content)
        for banned in ("Upgrade to Pioneer", "Pioneer tier", "$", "paid"):
            assert banned not in text
        assert "free" in text.lower()


class TestAuthorizedPath:
    @pytest.mark.asyncio
    async def test_admitted_and_completed_carry_hmac_subject_only(
        self, monkeypatch, capsys
    ):
        result, called, events = await _run(
            monkeypatch, "run_full_trinity",
            enabled=True, subject=SUBJECT_UUID, capsys=capsys,
        )
        admitted = [e for e in events if e["event"] == "tool_admitted"]
        completed = [e for e in events if e["event"] == "tool_completed"]
        assert len(admitted) == len(completed) == 1
        subject = admitted[0]["subject"]
        assert subject.startswith("s1_") and SUBJECT_UUID not in subject
        assert completed[0]["subject"] == subject
        assert completed[0]["success"] is True
        assert completed[0]["inference_quality"] == "real"
        assert completed[0]["traffic_class"] == "external"
        assert completed[0]["execution_id"]
        # T P0-10: terminal evidence carries the route lane and an
        # environment label bound to the OAuth env, not a K_SERVICE guess.
        assert completed[0]["route"] == "hosted"
        assert completed[0]["environment"] in ("production", "staging", "development")
        # Raw UUID appears in NO event (P0 #6).
        assert SUBJECT_UUID not in json.dumps(events)
        # The handler saw the hmac subject via contextvar; reset afterwards.
        assert called["hmac_ctx"] == subject
        assert VERIFIED_SUBJECT_HMAC.get() is None

    @pytest.mark.asyncio
    async def test_byok_arguments_are_routed_as_byok(self, monkeypatch, capsys):
        _result, _called, events = await _run(
            monkeypatch, "run_full_trinity",
            enabled=True, subject=SUBJECT_UUID, capsys=capsys,
            arguments={"llm_provider": "groq", "api_key": "k"},
        )
        completed = [e for e in events if e["event"] == "tool_completed"]
        assert completed[0]["route"] == "byok"
        # Raw UUID appears in NO event (P0 #6).
        assert SUBJECT_UUID not in json.dumps(events)

    @pytest.mark.asyncio
    async def test_error_payload_completes_with_success_false(
        self, monkeypatch, capsys
    ):
        _result, _called, events = await _run(
            monkeypatch, "consult_agent_cs",
            enabled=True, subject=SUBJECT_UUID, capsys=capsys,
            handler_payload={"status": "error", "error_code": "BYOK_AUTH_FAILED"},
        )
        completed = [e for e in events if e["event"] == "tool_completed"][0]
        assert completed["success"] is False

    @pytest.mark.asyncio
    async def test_handler_exception_completes_false_and_reraises(
        self, monkeypatch, capsys
    ):
        with pytest.raises(RuntimeError):
            await _run(
                monkeypatch, "consult_agent_x",
                enabled=True, subject=SUBJECT_UUID, capsys=capsys,
                handler_raises=True,
            )
        events = _events(capsys.readouterr().err)
        completed = [e for e in events if e["event"] == "tool_completed"]
        assert len(completed) == 1
        assert completed[0]["success"] is False
        assert completed[0]["inference_quality"] == "exception"

    @pytest.mark.asyncio
    async def test_ungated_tool_passes_without_events(self, monkeypatch, capsys):
        _r, called, events = await _run(
            monkeypatch, "list_prompt_templates",
            enabled=True, subject=None, capsys=capsys,
        )
        assert called.get("yes")
        assert events == []

    @pytest.mark.asyncio
    async def test_unkeyed_hmac_omits_subject_rather_than_leaking(
        self, monkeypatch, capsys
    ):
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.delenv("VALUE_SUBJECT_HMAC_KEY", raising=False)
        token = AUTH_SUBJECT_UUID.set(SUBJECT_UUID)
        try:
            async def call_next(_c):
                return SimpleNamespace(
                    structured_content={"status": "success"}, content=[]
                )
            await RegistrationGate().on_call_tool(
                _ctx("consult_agent_z"), call_next
            )
        finally:
            AUTH_SUBJECT_UUID.reset(token)
        events = _events(capsys.readouterr().err)
        for event in events:
            assert "subject" not in event          # silent, never raw
            assert SUBJECT_UUID not in json.dumps(event)


class TestQuarantineUnaffected:
    @pytest.mark.asyncio
    async def test_authentication_does_not_unlock_contained_tools(
        self, monkeypatch, capsys
    ):
        # Coordination tools are NOT gated here: the call passes through to
        # their own fail-closed containment denial — no credential, OAuth or
        # otherwise, satisfies Gate R0.
        _r, called, events = await _run(
            monkeypatch, "coordination_handoff_read",
            enabled=True, subject=SUBJECT_UUID, capsys=capsys,
        )
        assert called.get("yes")
        assert events == []


class TestEndToEnd:
    @pytest.fixture
    def app(self):
        from verifimind_mcp import server as server_mod
        return server_mod.create_http_server()

    @pytest.mark.asyncio
    async def test_gated_denial_emits_no_lifecycle_events(
        self, app, monkeypatch, capsys
    ):
        from .mcp_tool_harness import call
        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        payload = await call(app, "run_full_trinity", {
            "concept_name": "gate-denial-probe",
            "concept_description": "v2 denial walk.",
        })
        assert payload["error_code"] == "AUTHENTICATION_REQUIRED"
        err = capsys.readouterr().err
        assert '"trinity_run_started"' not in err
        assert '"trinity_run_completed"' not in err
        assert '"tool_invoked"' in err   # dispatch-attempt layer unchanged
        assert '"tool_denied"' in err

    @pytest.mark.asyncio
    async def test_authenticated_trinity_joins_lifecycle_to_hmac_subject(
        self, app, monkeypatch, capsys
    ):
        from .mcp_tool_harness import call
        from verifimind_mcp import config_helper

        monkeypatch.setenv("REGISTRATION_GATE_ENABLED", "true")
        monkeypatch.setenv("VALUE_SUBJECT_HMAC_KEY", HMAC_KEY)
        monkeypatch.setattr(
            gate_mod, "AUTH_SUBJECT_UUID",
            ContextVar("test_subject", default=SUBJECT_UUID),
        )
        monkeypatch.setattr(
            gate_mod, "AUTH_ACTOR_CLASS",
            ContextVar("test_actor", default="external"),
        )

        def _boom(_provider, _key, _agent):
            raise ValueError("unknown provider prefix")

        monkeypatch.setattr(config_helper, "create_ephemeral_provider", _boom)
        payload = await call(app, "run_full_trinity", {
            "concept_name": "gate-join-probe",
            "concept_description": "v2 lifecycle join walk.",
            "llm_provider": "bogus-provider",
            "api_key": "not-a-real-key",
        })
        assert payload["status"] == "error"
        err = capsys.readouterr().err
        events = _events(err)
        started = [e for e in events if e["event"] == "trinity_run_started"]
        completed = [e for e in events if e["event"] == "trinity_run_completed"]
        admitted = [e for e in events if e["event"] == "tool_admitted"]
        tool_done = [e for e in events if e["event"] == "tool_completed"]
        assert len(started) == len(completed) == len(admitted) == len(tool_done) == 1
        subject = admitted[0]["subject"]
        assert started[0]["subject"] == subject
        assert completed[0]["subject"] == subject
        assert tool_done[0]["success"] is False
        # The raw UUID never appears anywhere in telemetry (P0 #6).
        assert SUBJECT_UUID not in err

    @pytest.mark.asyncio
    async def test_flag_off_lifecycle_events_carry_no_subject_field(
        self, app, monkeypatch, capsys
    ):
        from .mcp_tool_harness import call
        from verifimind_mcp import config_helper

        monkeypatch.delenv("REGISTRATION_GATE_ENABLED", raising=False)

        def _boom(_provider, _key, _agent):
            raise ValueError("unknown provider prefix")

        monkeypatch.setattr(config_helper, "create_ephemeral_provider", _boom)
        payload = await call(app, "run_full_trinity", {
            "concept_name": "dark-parity-probe",
            "concept_description": "flag-off lifecycle parity walk.",
            "llm_provider": "bogus-provider",
            "api_key": "not-a-real-key",
        })
        assert payload["status"] == "error"
        for event in _events(capsys.readouterr().err):
            if event["event"].startswith("trinity_run_"):
                assert "subject" not in event


class TestPolicyNotice:
    # Two states, one source (policies/activation_notice.py): no announced activation date,
    # or an announced ISO date. Every assertion below is written against whichever state the
    # constant is in, so a release that flips it cannot leave a carrier behind.

    def test_notice_period_arithmetic(self):
        from verifimind_mcp.policies.activation_notice import (
            NOTICE_DAYS,
            notice_period_honored,
        )

        assert NOTICE_DAYS == 14
        assert notice_period_honored(None, "2026-09-22") is True
        assert notice_period_honored("2026-10-06", "2026-09-22") is True  # exactly +14
        assert notice_period_honored("2026-10-05", "2026-09-22") is False  # +13
        # one announcing revision too recent: the promise is per carrier, not on average
        assert notice_period_honored("2026-10-20", "2026-09-22", "2026-10-07") is False
        with pytest.raises(ValueError):
            notice_period_honored("2026-10-20")  # no published date: never a vacuous pass

    def test_gate_phrases_render_both_states(self):
        from verifimind_mcp.policies.activation_notice import (
            TO_BE_ANNOUNCED_EN,
            TO_BE_ANNOUNCED_MS,
            gate_when_en,
            gate_when_ms,
            sentence_case,
        )

        assert "at least 14 days in advance" in TO_BE_ANNOUNCED_EN
        assert "sekurang-kurangnya 14 hari" in TO_BE_ANNOUNCED_MS
        assert gate_when_en(None) == f"from {TO_BE_ANNOUNCED_EN}"
        assert gate_when_ms(None) == f"mulai {TO_BE_ANNOUNCED_MS}"
        assert gate_when_en("2026-12-01") == "from December 1, 2026"
        assert gate_when_ms("2026-12-01") == "mulai 1 Disember 2026"
        assert sentence_case(gate_when_en(None)).startswith("From a date")
        assert sentence_case(gate_when_ms(None)).startswith("Mulai tarikh")

    def test_announced_gate_date_honors_the_notice_period(self):
        from verifimind_mcp.policies.activation_notice import (
            REGISTRATION_GATE_EFFECTIVE_DATE,
            notice_period_honored,
        )
        from verifimind_mcp.policies.privacy_policy import (
            PRIVACY_POLICY_EFFECTIVE_DATE,
        )
        from verifimind_mcp.policies.terms import TERMS_EFFECTIVE_DATE

        assert notice_period_honored(
            REGISTRATION_GATE_EFFECTIVE_DATE,
            TERMS_EFFECTIVE_DATE,
            PRIVACY_POLICY_EFFECTIVE_DATE,
        )

    def test_every_carrier_renders_the_current_gate_state(self):
        # The counts bind the carriers: Privacy Sections 2, 3, 5 and 8 in English and the
        # NOTIS AWAL, UUID and HAK paragraphs of the Bahasa Malaysia mirror; Terms Section 3.
        # A dropped or retyped carrier changes a count. The standing promise appears if and
        # only if no date is announced: the revision that announces one must rewrite the
        # Changes sections too.
        from verifimind_mcp.policies.activation_notice import (
            REGISTRATION_GATE_EFFECTIVE_DATE,
            TO_BE_ANNOUNCED_EN,
            TO_BE_ANNOUNCED_MS,
            gate_when_en,
            gate_when_ms,
        )
        from verifimind_mcp.policies.privacy_policy import PRIVACY_POLICY
        from verifimind_mcp.policies.terms import TERMS_AND_CONDITIONS

        privacy = " ".join(PRIVACY_POLICY.split()).lower()
        terms = " ".join(TERMS_AND_CONDITIONS.split()).lower()
        when_en = gate_when_en(REGISTRATION_GATE_EFFECTIVE_DATE).lower()
        when_ms = gate_when_ms(REGISTRATION_GATE_EFFECTIVE_DATE).lower()
        assert privacy.count(when_en) == 4
        assert terms.count(when_en) == 1
        assert privacy.count(when_ms) == 3

        unannounced = REGISTRATION_GATE_EFFECTIVE_DATE is None
        assert (TO_BE_ANNOUNCED_EN.lower() in privacy) is unannounced
        assert (TO_BE_ANNOUNCED_EN.lower() in terms) is unannounced
        assert (TO_BE_ANNOUNCED_MS.lower() in privacy) is unannounced

    def test_v27_and_v26_changes_sections_name_the_replaced_date_once(self):
        # Privacy v2.7 and Terms v2.6 replaced the fixed date (2026-10-20) that v2.6 and v2.5
        # announced. The superseded date may appear exactly once per policy, in the Changes
        # section that names what was replaced, and nowhere operative.
        from verifimind_mcp.policies.privacy_policy import PRIVACY_POLICY
        from verifimind_mcp.policies.terms import TERMS_AND_CONDITIONS

        privacy = " ".join(PRIVACY_POLICY.split())
        terms = " ".join(TERMS_AND_CONDITIONS.split())
        before_changes, rest = privacy.split("11. CHANGES", 1)
        changes_en, malay = rest.split("12. NOTIS PERLINDUNGAN DATA PERIBADI", 1)
        malay_body, malay_changes = malay.split("KESELAMATAN, KUKI DAN PERUBAHAN", 1)
        terms_body, terms_changes = terms.split("14. CONTACT AND CHANGES", 1)

        assert "October 20, 2026" not in before_changes
        assert changes_en.count("October 20, 2026") == 1
        assert "20 Oktober 2026" not in malay_body
        assert malay_changes.count("20 Oktober 2026") == 1
        assert "October 20, 2026" not in terms_body
        assert terms_changes.count("October 20, 2026") == 1
        for section in (changes_en, terms_changes):
            assert "and not before" in section
            assert "effective on publication" in section
        assert "dan tidak sebelum itu" in malay_changes

    def test_both_policies_state_their_own_publication_date(self):
        # The ISO constants feed the JSON carriers and, since v2.7/v2.6, render the sentences
        # people read in two languages. Keep the binding asserted from the outside, so a
        # retyped line would still be caught.
        from verifimind_mcp.policies.activation_notice import _human_en, _human_ms
        from verifimind_mcp.policies.privacy_policy import (
            PRIVACY_POLICY,
            PRIVACY_POLICY_EFFECTIVE_DATE,
        )
        from verifimind_mcp.policies.terms import (
            TERMS_AND_CONDITIONS,
            TERMS_EFFECTIVE_DATE,
        )

        assert PRIVACY_POLICY_EFFECTIVE_DATE == TERMS_EFFECTIVE_DATE
        assert (
            f"Published and effective: {_human_en(PRIVACY_POLICY_EFFECTIVE_DATE)} "
            in PRIVACY_POLICY
        )
        assert (
            f"Published and effective: {_human_en(TERMS_EFFECTIVE_DATE)} "
            in TERMS_AND_CONDITIONS
        )
        assert (
            f"Diterbitkan dan berkuat kuasa pada {_human_ms(PRIVACY_POLICY_EFFECTIVE_DATE)}"
            in PRIVACY_POLICY
        )

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
