"""v0.5.60 Trinity Completion — orchestration-layer retry + stagger contracts.

The completion guardrail these tests pin: a retry either produces a REAL
second attempt or propagates the second failure into the unchanged honest
degradation contract. No path may convert a failure into a fabricated
success, and no failure class without a provider-stated wait may retry.
"""

import asyncio

import pytest

from verifimind_mcp.utils import trinity_retry
from verifimind_mcp.utils.trinity_retry import (
    RETRY_AFTER_CAP_SECONDS,
    RETRY_MARGIN_SECONDS,
    SHARED_PROVIDER_STAGGER_SECONDS,
    TrinityRetryBudget,
    analyze_with_completion_retry,
    retry_wait_for,
    stagger_if_shared_provider,
)
from verifimind_mcp.utils.provider_failures import trinity_stage_failure


# --- fakes -----------------------------------------------------------------

class FakeRateLimitError(Exception):
    """Class name contains 'ratelimit' -> PROVIDER_RATE_LIMITED."""
    def __init__(self, retry_after=None):
        super().__init__("capacity exhausted")
        self.status_code = 429
        if retry_after is not None:
            self.retry_after = retry_after


class FakeTimeoutError(Exception):
    """-> PROVIDER_TIMEOUT: retryable but carries NO provider-stated wait."""
    def __init__(self):
        super().__init__("request timed out")
        self.status_code = 504


class FakeAuthError(Exception):
    """-> auth failure: non-retryable."""
    def __init__(self):
        super().__init__("invalid api key")
        self.status_code = 401


class FakeProvider:
    def __init__(self, model_name):
        self._model_name = model_name

    def get_model_name(self):
        return self._model_name


class SleepRecorder:
    def __init__(self):
        self.calls = []

    async def __call__(self, seconds):
        self.calls.append(seconds)


@pytest.fixture
def no_sleep(monkeypatch):
    # Overrides the conftest autouse instant-sleep on the SAME seam, so these
    # tests can assert the exact waits production would have slept.
    rec = SleepRecorder()
    monkeypatch.setattr(trinity_retry, "_sleep", rec)
    return rec


def make_stage(outcomes):
    """A stage whose successive calls raise or return per `outcomes`."""
    calls = {"n": 0}

    async def stage():
        idx = min(calls["n"], len(outcomes) - 1)
        calls["n"] += 1
        outcome = outcomes[idx]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    return stage, calls


# --- retry_wait_for eligibility matrix -------------------------------------

class TestRetryEligibility:
    def test_retryable_with_short_wait_is_honoured_with_margin(self):
        assert retry_wait_for(
            {"retryable": True, "retry_after_seconds": 8.0}
        ) == 8.0 + RETRY_MARGIN_SECONDS

    def test_retryable_without_wait_is_deliberately_not_eligible(self):
        assert retry_wait_for(
            {"retryable": True, "retry_after_seconds": None}
        ) is None

    def test_non_retryable_never_eligible_even_with_wait(self):
        assert retry_wait_for(
            {"retryable": False, "retry_after_seconds": 5.0}
        ) is None

    def test_wait_above_cap_not_eligible(self):
        # The observed 54s outlier: holding a request open that long trades an
        # honest partial for a probable client-side timeout.
        assert retry_wait_for(
            {"retryable": True, "retry_after_seconds": 54.0}
        ) is None

    def test_wait_exactly_at_cap_is_eligible(self):
        assert retry_wait_for(
            {"retryable": True, "retry_after_seconds": RETRY_AFTER_CAP_SECONDS}
        ) == RETRY_AFTER_CAP_SECONDS + RETRY_MARGIN_SECONDS

    def test_garbage_wait_not_eligible(self):
        assert retry_wait_for(
            {"retryable": True, "retry_after_seconds": "soon"}
        ) is None
        assert retry_wait_for(
            {"retryable": True, "retry_after_seconds": -3}
        ) is None


# --- analyze_with_completion_retry -----------------------------------------

class TestCompletionRetry:
    def test_first_attempt_success_calls_once_and_sleeps_never(self, no_sleep):
        stage, calls = make_stage(["real-result"])
        budget = TrinityRetryBudget()
        result = asyncio.run(analyze_with_completion_retry(
            stage, agent_id="Z", byok=False, session_id="s1", budget=budget,
        ))
        assert result == "real-result"
        assert calls["n"] == 1
        assert no_sleep.calls == []
        assert budget.summary() == {}

    def test_rate_limited_then_success_recovers(self, no_sleep):
        stage, calls = make_stage([FakeRateLimitError(retry_after=8), "recovered"])
        budget = TrinityRetryBudget()
        result = asyncio.run(analyze_with_completion_retry(
            stage, agent_id="Z", byok=False, session_id="s2", budget=budget,
        ))
        assert result == "recovered"
        assert calls["n"] == 2
        assert no_sleep.calls == [8.0 + RETRY_MARGIN_SECONDS]
        assert budget.summary()["Z"]["outcome"] == "recovered"
        assert budget.summary()["Z"]["on_error_code"] == "PROVIDER_RATE_LIMITED"

    def test_rate_limited_twice_raises_second_with_marker(self, no_sleep):
        second = FakeRateLimitError(retry_after=9)
        stage, calls = make_stage([FakeRateLimitError(retry_after=8), second])
        budget = TrinityRetryBudget()
        attempt = analyze_with_completion_retry(
            stage, agent_id="CS", byok=False, session_id="s3", budget=budget,
        )
        with pytest.raises(FakeRateLimitError) as excinfo:
            asyncio.run(attempt)
        assert excinfo.value is second
        assert getattr(excinfo.value, "_trinity_retry_attempted", False) is True
        assert calls["n"] == 2
        assert budget.summary()["CS"]["outcome"] == "failed_again"

    def test_auth_failure_never_retries(self, no_sleep):
        first = FakeAuthError()
        stage, calls = make_stage([first, "must-not-reach"])
        budget = TrinityRetryBudget()
        attempt = analyze_with_completion_retry(
            stage, agent_id="X", byok=True, session_id="s4", budget=budget,
        )
        with pytest.raises(FakeAuthError) as excinfo:
            asyncio.run(attempt)
        assert excinfo.value is first
        assert calls["n"] == 1
        assert no_sleep.calls == []
        assert budget.summary() == {}

    def test_timeout_without_stated_wait_never_retries(self, no_sleep):
        # The deliberate boundary: retryable-but-unscheduled failures do not
        # get a blind re-run.
        first = FakeTimeoutError()
        stage, calls = make_stage([first, "must-not-reach"])
        budget = TrinityRetryBudget()
        attempt = analyze_with_completion_retry(
            stage, agent_id="Z", byok=False, session_id="s5", budget=budget,
        )
        with pytest.raises(FakeTimeoutError):
            asyncio.run(attempt)
        assert calls["n"] == 1
        assert no_sleep.calls == []

    def test_exhausted_budget_blocks_retry(self, no_sleep):
        first = FakeRateLimitError(retry_after=8)
        stage, calls = make_stage([first, "must-not-reach"])
        budget = TrinityRetryBudget(budget_seconds=5.0)  # below 8.5 needed
        attempt = analyze_with_completion_retry(
            stage, agent_id="Z", byok=False, session_id="s6", budget=budget,
        )
        with pytest.raises(FakeRateLimitError) as excinfo:
            asyncio.run(attempt)
        assert excinfo.value is first
        assert calls["n"] == 1
        assert no_sleep.calls == []

    def test_budget_depletes_across_stages(self, no_sleep):
        budget = TrinityRetryBudget(budget_seconds=20.0)
        stage_z, _ = make_stage([FakeRateLimitError(retry_after=10), "z-ok"])
        asyncio.run(analyze_with_completion_retry(
            stage_z, agent_id="Z", byok=False, session_id="s7", budget=budget,
        ))
        # 20 - 10.5 = 9.5 left; a 10s wait no longer fits
        first = FakeRateLimitError(retry_after=10)
        stage_cs, calls_cs = make_stage([first, "must-not-reach"])
        attempt = analyze_with_completion_retry(
            stage_cs, agent_id="CS", byok=False, session_id="s7", budget=budget,
        )
        with pytest.raises(FakeRateLimitError):
            asyncio.run(attempt)
        assert calls_cs["n"] == 1

    def test_no_fabrication_on_double_failure(self, no_sleep):
        """The guardrail: a failed retry yields the SAME honest degradation
        contract as no retry — plus the retry_attempted disclosure."""
        second = FakeRateLimitError(retry_after=9)
        second._trinity_retry_attempted = True  # as the wrapper sets it
        placeholder, record = trinity_stage_failure(
            agent_id="Z",
            provider=FakeProvider("groq/openai/gpt-oss-120b"),
            exc=second,
            byok=False,
            session_id="s8",
        )
        assert placeholder._inference_quality == "unavailable"
        assert record["error_code"] == "PROVIDER_RATE_LIMITED"
        assert record["retryable"] is True
        assert record["retry_attempted"] is True

    def test_record_without_marker_has_no_retry_attempted_key(self):
        _, record = trinity_stage_failure(
            agent_id="Z",
            provider=FakeProvider("groq/openai/gpt-oss-120b"),
            exc=FakeRateLimitError(retry_after=9),
            byok=False,
            session_id="s9",
        )
        assert "retry_attempted" not in record


# --- catch-all contract (§2.2 repair) ---------------------------------------

class TestCatchallContract:
    """The 'omit BYOK params' hint must never reach a caller who sent none."""

    def test_no_byok_generic_failure_does_not_mention_byok(self):
        from verifimind_mcp.utils.provider_failures import trinity_catchall_contract
        contract = trinity_catchall_contract(
            RuntimeError("something unexpected"), byok_supplied=False,
        )
        assert contract["error_code"] == "TRINITY_ERROR"
        assert "byok" not in contract["recovery_hint"].lower()

    def test_byok_generic_failure_keeps_the_byok_hint(self):
        from verifimind_mcp.utils.provider_failures import trinity_catchall_contract
        contract = trinity_catchall_contract(
            RuntimeError("something unexpected"), byok_supplied=True,
        )
        assert contract["error_code"] == "TRINITY_ERROR"
        assert "BYOK" in contract["recovery_hint"]

    def test_auth_shaped_without_byok_is_hosted_lane_not_byok(self):
        from verifimind_mcp.utils.provider_failures import trinity_catchall_contract
        contract = trinity_catchall_contract(
            RuntimeError("401 authentication failed"), byok_supplied=False,
        )
        assert contract["error_code"] == "PROVIDER_AUTH_FAILED"
        assert "api_key" not in contract["recovery_hint"].lower()

    def test_auth_shaped_with_byok_stays_byok_attributed(self):
        from verifimind_mcp.utils.provider_failures import trinity_catchall_contract
        contract = trinity_catchall_contract(
            RuntimeError("invalid api key"), byok_supplied=True,
        )
        assert contract["error_code"] == "BYOK_AUTH_FAILED"

    def test_timeout_shape_preserved(self):
        from verifimind_mcp.utils.provider_failures import trinity_catchall_contract
        contract = trinity_catchall_contract(
            RuntimeError("request timed out"), byok_supplied=False,
        )
        assert contract["error_code"] == "PROVIDER_TIMEOUT"


# --- small batch: templates, monitor ----------------------------------------

class TestTemplateAttribution:
    """P2-B: every breakdown sums to total_templates by construction, and the
    shared-'all' templates are reachable through the filter for the first time."""

    def _registry(self):
        # Hermetic fresh instance: object.__new__ (never the singleton slot)
        # + a real load from the shipped library YAMLs. TemplateRegistry() is
        # a process-wide singleton and other suites may have shaped it.
        from pathlib import Path
        from verifimind_mcp.templates import registry as registry_module
        from verifimind_mcp.templates.registry import TemplateRegistry
        reg = object.__new__(TemplateRegistry)
        reg._templates = {}
        reg._libraries = {}
        reg._custom_templates = {}
        reg._initialized = True
        reg._library_path = Path(registry_module.__file__).parent / "library"
        reg._load_builtin_templates()
        return reg

    def test_agent_breakdown_sums_to_total(self):
        stats = self._registry().get_statistics()
        assert sum(stats["templates_by_agent"].values()) == stats["total_templates"]
        assert stats["templates_by_agent"] == {"X": 6, "Z": 3, "CS": 6, "all": 4}

    def test_phase_breakdown_sums_to_total(self):
        # One template carries two genesis-phase tags; attribution counts it
        # once (under its primary tag) so the sum equals the total.
        stats = self._registry().get_statistics()
        assert sum(stats["templates_by_phase"].values()) == stats["total_templates"]

    def test_shared_templates_match_agent_queries(self):
        registry = self._registry()
        # "all" query returns exactly the shared set
        assert len(registry.list_templates(agent_id="all")) == 4
        # an agent query includes its own PLUS the shared set (membership)
        assert len(registry.list_templates(agent_id="X")) == 10
        assert len(registry.list_templates(agent_id="Z")) == 7
        assert len(registry.list_templates(agent_id="CS")) == 10

    def test_tags_filter_still_works_at_registry_layer(self):
        registry = self._registry()
        hits = registry.list_templates(tags=["stride"])
        assert [t.template_id for t in hits] == ["security-threat-modeling"]


class TestTagsInputCoercion:
    """P2-A: a stringified JSON array — the shape MCP clients actually send —
    resolves instead of becoming a literal '[\"stride\"]' tag."""

    @pytest.mark.asyncio
    async def test_json_array_shaped_tags_resolve(self):
        from verifimind_mcp import server as server_mod
        from .mcp_tool_harness import call
        app = server_mod.create_http_server()
        payload = await call(app, "list_prompt_templates", {"tags": '["stride"]'})
        assert payload["count"] == 1
        assert payload["templates"][0]["template_id"] == "security-threat-modeling"

    @pytest.mark.asyncio
    async def test_documented_string_form_unchanged(self):
        from verifimind_mcp import server as server_mod
        from .mcp_tool_harness import call
        app = server_mod.create_http_server()
        payload = await call(app, "list_prompt_templates", {"tags": "stride"})
        assert payload["count"] == 1


class TestCsTokenMonitor:
    """P3-B: CS gets the instrumentation Z has had since v0.5.3."""

    def test_cs_monitor_mirrors_z_thresholds(self):
        from verifimind_mcp.utils import check_cs_agent_response
        low = check_cs_agent_response(1000)
        assert low["risk_level"] == "LOW"
        assert low["truncated"] is False
        critical = check_cs_agent_response(8192)
        assert critical["risk_level"] == "CRITICAL"
        assert critical["truncated"] is True


# --- T S135 end-to-end regressions (F-331-T1 / F-331-T2) ---------------------

def _lifecycle_events(stderr):
    import json as _json
    started = [
        _json.loads(line) for line in stderr.splitlines()
        if line.startswith("{") and '"trinity_run_started"' in line
    ]
    completed = [
        _json.loads(line) for line in stderr.splitlines()
        if line.startswith("{") and '"trinity_run_completed"' in line
    ]
    return started, completed


class TestLifecycleAndByokEndToEnd:
    """T S135's exact-head counterexamples, pinned so they cannot return."""

    @pytest.fixture
    def app(self):
        from verifimind_mcp import server as server_mod
        return server_mod.create_http_server()

    @pytest.mark.asyncio
    async def test_invalid_byok_before_resolution_is_byok_attributed(
        self, app, monkeypatch, capsys
    ):
        # F-331-T2: a BYOK parameter that fails during resolution — before
        # byok_status is ever populated — must be attributed to the caller's
        # BYOK input, never to the hosted service.
        from verifimind_mcp import config_helper
        from .mcp_tool_harness import call

        def _boom(_provider, _key, _agent):
            raise ValueError("unknown provider prefix")

        monkeypatch.setattr(config_helper, "create_ephemeral_provider", _boom)
        payload = await call(app, "run_full_trinity", {
            "concept_name": "byok-preresolution-probe",
            "concept_description": "F-331-T2 regression.",
            "llm_provider": "bogus-provider",
            "api_key": "not-a-real-key",
        })
        assert payload["status"] == "error"
        hint = payload["recovery_hint"]
        assert "BYOK" in hint
        assert "no change to your request" not in hint.lower()

        started, completed = _lifecycle_events(capsys.readouterr().err)
        assert len(started) == 1
        assert len(completed) == 1
        assert completed[0]["outcome"] == "error"
        assert completed[0]["session_id"] == started[0]["session_id"]

    @pytest.mark.asyncio
    async def test_pre_resolution_failure_has_paired_start(
        self, app, monkeypatch, capsys
    ):
        # F-331-T1 (zero-start shape): a failure during request preparation
        # must still produce one started AND one completed, same session.
        from verifimind_mcp import utils as utils_mod
        from .mcp_tool_harness import call

        def _boom(**_kwargs):
            raise RuntimeError("sanitizer exploded")

        monkeypatch.setattr(utils_mod, "sanitize_concept_input", _boom)
        payload = await call(app, "run_full_trinity", {
            "concept_name": "paired-start-probe",
            "concept_description": "F-331-T1 zero-start regression.",
        })
        assert payload["status"] == "error"
        started, completed = _lifecycle_events(capsys.readouterr().err)
        assert len(started) == 1
        assert len(completed) == 1
        assert completed[0]["outcome"] == "error"
        assert completed[0]["session_id"] == started[0]["session_id"]

    @pytest.mark.asyncio
    async def test_post_analysis_failure_yields_exactly_one_error_completion(
        self, app, monkeypatch, capsys
    ):
        # F-331-T1 (double-completion shape): a failure AFTER all three stages
        # succeed but BEFORE the response exists must produce exactly ONE
        # completion, outcome=error — never full followed by error.
        from verifimind_mcp import config_helper, utils as utils_mod
        from verifimind_mcp.agents import CSAgent, XAgent, ZAgent
        from .mcp_tool_harness import call
        from .test_v0558_trinity_traceability import _NamedProvider, _real_results

        x_result, z_result, cs_result = _real_results()
        providers = {
            "X": _NamedProvider("gemini/gemini-3.5-flash-lite"),
            "Z": _NamedProvider("groq/openai/gpt-oss-120b"),
            "CS": _NamedProvider("groq/openai/gpt-oss-120b"),
        }
        monkeypatch.setattr(
            config_helper, "get_trinity_providers", lambda _ctx: providers
        )

        async def x_analyze(_self, _concept, _prior=None, _metrics=None):
            return x_result

        async def z_analyze(_self, _concept, _prior=None, _metrics=None):
            return z_result

        async def cs_analyze(_self, _concept, _prior=None, _metrics=None):
            return cs_result

        monkeypatch.setattr(XAgent, "analyze", x_analyze)
        monkeypatch.setattr(ZAgent, "analyze", z_analyze)
        monkeypatch.setattr(CSAgent, "analyze", cs_analyze)

        # Injection point matters (known-positive lesson): create_trinity_result
        # raises BEFORE the pre-repair emit and therefore never discriminated.
        # persist_trinity_result sits AFTER the old early emit and BEFORE the
        # repaired per-return emit — exactly T's full+error counterexample
        # window on the old head, and the exactly-once proof on the new one.
        from verifimind_mcp import server as server_inner

        def _render_boom(*_args, **_kwargs):
            raise RuntimeError("post-analysis assembly exploded")

        monkeypatch.setattr(server_inner, "persist_trinity_result", _render_boom)
        payload = await call(app, "run_full_trinity", {
            "concept_name": "exactly-once-probe",
            "concept_description": "F-331-T1 double-completion regression.",
        })
        assert payload["status"] == "error"
        started, completed = _lifecycle_events(capsys.readouterr().err)
        assert len(started) == 1
        assert len(completed) == 1, (
            f"expected exactly one completion, got {len(completed)}: "
            f"{[c.get('outcome') for c in completed]}"
        )
        assert completed[0]["outcome"] == "error"


# --- T S136 counterexamples (R-331-T136-1 / R-331-T136-2) --------------------

class TestPhaseAwareAttributionAndPrelude:
    """T S136's two exact counterexamples, pinned end-to-end."""

    @pytest.fixture
    def app(self):
        from verifimind_mcp import server as server_mod
        return server_mod.create_http_server()

    @pytest.mark.asyncio
    async def test_keyless_selector_post_resolution_failure_is_hosted(
        self, app, monkeypatch, capsys
    ):
        # R-331-T136-1: a supported provider selector WITHOUT a key is
        # deliberately ignored by resolution (hosted defaults). A hosted-side
        # failure AFTER that boundary must be attributed to the hosted lane —
        # the caller's inert parameter is not the cause.
        from verifimind_mcp import config_helper
        from .mcp_tool_harness import call

        def _hosted_boom(_agent_id, _ctx=None):
            raise RuntimeError("hosted provider construction exploded")

        # R-331-T138 moved hosted construction to the per-agent seam; this
        # counterexample (hosted fill fails) injects there now.
        monkeypatch.setattr(config_helper, "get_agent_provider", _hosted_boom)
        payload = await call(app, "run_full_trinity", {
            "concept_name": "keyless-selector-probe",
            "concept_description": "R-331-T136-1 regression.",
            "llm_provider": "groq",  # supported selector, NO key -> ignored
        })
        assert payload["status"] == "error"
        hint = payload["recovery_hint"]
        assert "BYOK" not in hint
        assert "hosted" in hint.lower()

        started, completed = _lifecycle_events(capsys.readouterr().err)
        assert len(started) == 1
        assert len(completed) == 1
        assert completed[0]["outcome"] == "error"
        assert completed[0]["session_id"] == started[0]["session_id"]

    @pytest.mark.asyncio
    async def test_prelude_failure_has_lifecycle_and_structured_error(
        self, app, monkeypatch, capsys
    ):
        # R-331-T136-2: a failure in the request prelude (detail
        # normalization — T's exact injection) must yield ONE structured
        # error response with one paired start + one error completion, never
        # a raw ToolError with zero lifecycle events.
        from verifimind_mcp.utils import reasoning_view
        from .mcp_tool_harness import call

        def _prelude_boom(_detail):
            raise RuntimeError("detail normalization exploded")

        monkeypatch.setattr(reasoning_view, "normalize_detail", _prelude_boom)
        payload = await call(app, "run_full_trinity", {
            "concept_name": "prelude-probe",
            "concept_description": "R-331-T136-2 regression.",
        })
        assert payload["status"] == "error"
        assert payload["error_code"] == "TRINITY_ERROR"

        started, completed = _lifecycle_events(capsys.readouterr().err)
        assert len(started) == 1
        assert len(completed) == 1
        assert completed[0]["outcome"] == "error"
        assert completed[0]["session_id"] == started[0]["session_id"]


# --- T S137 counterexamples (R-331-T137, mixed-lane resolution) --------------

class TestMixedLaneResolution:
    """T S137: active-any is not the failing lane. A hosted-fill failure must
    be hosted even when an unrelated ephemeral is active, and an all-resolved
    run must never execute hosted construction at all."""

    @pytest.fixture
    def app(self):
        from verifimind_mcp import server as server_mod
        return server_mod.create_http_server()

    @pytest.mark.asyncio
    async def test_mixed_lane_hosted_fill_failure_is_hosted(
        self, app, monkeypatch, capsys
    ):
        # X carries a real active ephemeral (gsk_ prefix -> Groq); Z/CS need
        # the hosted fill, which fails. The failing LANE is hosted — the
        # unrelated X ephemeral must not convert this into caller blame.
        from verifimind_mcp import config_helper
        from .mcp_tool_harness import call

        def _hosted_boom(_agent_id, _ctx=None):
            raise RuntimeError("hosted provider construction exploded")

        # Per-agent seam (R-331-T138): the required Z/CS fill fails hosted.
        monkeypatch.setattr(config_helper, "get_agent_provider", _hosted_boom)
        payload = await call(app, "run_full_trinity", {
            "concept_name": "mixed-lane-probe",
            "concept_description": "R-331-T137 mixed-lane regression.",
            "x_api_key": "gsk_fakefakefake123",  # active X ephemeral
        })
        assert payload["status"] == "error"
        hint = payload["recovery_hint"]
        assert "BYOK" not in hint
        assert "hosted" in hint.lower()

        started, completed = _lifecycle_events(capsys.readouterr().err)
        assert len(started) == 1
        assert len(completed) == 1
        assert completed[0]["outcome"] == "error"

    @pytest.mark.asyncio
    async def test_all_resolved_run_never_calls_hosted_construction(
        self, app, monkeypatch, capsys
    ):
        # All three agents resolve to ephemerals: hosted construction is not
        # needed and must be SKIPPED — a hosted-side outage cannot fail a run
        # that never required the hosted lane.
        from verifimind_mcp import config_helper
        from .mcp_tool_harness import call

        def _hosted_boom(_ctx):
            raise RuntimeError("hosted construction must not be called")

        monkeypatch.setattr(config_helper, "get_trinity_providers", _hosted_boom)
        payload = await call(app, "run_full_trinity", {
            "concept_name": "all-resolved-probe",
            "concept_description": "R-331-T137 all-resolved regression.",
            "x_api_key": "gsk_fakefakefake123",
            "z_api_key": "gsk_fakefakefake456",
            "cs_api_key": "gsk_fakefakefake789",
        })
        # The run must reach the STAGES (which fail per-stage on the fake
        # keys, honestly) — never the catch-all via hosted construction.
        assert payload.get("error_code") != "TRINITY_ERROR"
        assert "_stage_errors" in payload
        assert sorted(payload["_agents_failed"]) == ["CS", "X", "Z"]

        started, completed = _lifecycle_events(capsys.readouterr().err)
        assert len(started) == 1
        assert len(completed) == 1


# --- T S138 counterexample (R-331-T138, partial-lane construction scope) -----

class TestPartialLaneConstructionScope:
    """T S138: filtered selection must not invoke a bulk constructor — hosted
    construction executes for exactly the unresolved lanes, never a resolved
    one."""

    @pytest.fixture
    def app(self):
        from verifimind_mcp import server as server_mod
        return server_mod.create_http_server()

    @pytest.mark.asyncio
    async def test_resolved_x_is_never_reconstructed(
        self, app, monkeypatch, capsys
    ):
        # T's exact probe: X resolved ephemerally (x_provider="mock"), only
        # Z/CS unresolved; hosted X construction FAILS if called; construction
        # calls must be exactly ["Z", "CS"]; no TRINITY_ERROR; the run reaches
        # stage-level handling with one paired lifecycle completion.
        from verifimind_mcp import config_helper
        from .mcp_tool_harness import call
        from .test_v0558_trinity_traceability import _NamedProvider

        constructed = []

        def _instrumented(agent_id, _ctx=None):
            constructed.append(agent_id)
            if agent_id == "X":
                raise RuntimeError("hosted X construction must not occur")
            return _NamedProvider("groq/openai/gpt-oss-120b")

        monkeypatch.setattr(config_helper, "get_agent_provider", _instrumented)
        payload = await call(app, "run_full_trinity", {
            "concept_name": "partial-lane-probe",
            "concept_description": "R-331-T138 regression.",
            "x_provider": "mock",  # X resolves ephemerally; Z/CS stay hosted
        })
        assert constructed == ["Z", "CS"], constructed
        assert payload.get("error_code") != "TRINITY_ERROR"
        assert "_stage_errors" in payload or payload.get("status") in ("partial", "success")

        started, completed = _lifecycle_events(capsys.readouterr().err)
        assert len(started) == 1
        assert len(completed) == 1
        assert completed[0]["session_id"] == started[0]["session_id"]


# --- canonical agent labels + run events ------------------------------------

class TestStructuredLogVocabulary:
    def test_display_names_map_to_canonical_ids(self):
        from verifimind_mcp.utils.provider_failures import canonical_agent_id
        assert canonical_agent_id("CS Security") == "CS"
        assert canonical_agent_id("X Intelligent") == "X"
        assert canonical_agent_id("Z Guardian") == "Z"
        # the sanitizer's historical space-stripped forms map too
        assert canonical_agent_id("CSSecurity") == "CS"
        assert canonical_agent_id("CS") == "CS"
        assert canonical_agent_id(None) is None

    def test_emit_uses_canonical_id_for_display_name(self, capsys):
        import json
        from verifimind_mcp.utils.provider_failures import emit_structured_failure
        emit_structured_failure(
            error_code="PROVIDER_RATE_LIMITED",
            agent="CS Security",
            exc=FakeRateLimitError(retry_after=5),
        )
        line = capsys.readouterr().err.strip().splitlines()[-1]
        assert json.loads(line)["agent"] == "CS"

    def test_run_event_bounds_all_string_fields(self, capsys):
        import json
        from verifimind_mcp.utils.provider_failures import emit_trinity_run_event
        emit_trinity_run_event(
            event="trinity_run_completed",
            session_id="abc123",
            outcome="full",
            agents_failed=None,          # None fields are omitted entirely
            retried_stages=["Z"],
            stagger_applied=True,
        )
        payload = json.loads(capsys.readouterr().err.strip().splitlines()[-1])
        assert payload["event"] == "trinity_run_completed"
        assert payload["outcome"] == "full"
        assert "agents_failed" not in payload
        assert payload["retried_stages"] == ["Z"]
        assert payload["stagger_applied"] is True


# --- stagger ---------------------------------------------------------------

class TestSharedProviderStagger:
    def test_same_family_staggers(self, no_sleep):
        applied = asyncio.run(stagger_if_shared_provider(
            FakeProvider("groq/openai/gpt-oss-120b"),
            FakeProvider("groq/openai/gpt-oss-120b"),
        ))
        assert applied is True
        assert no_sleep.calls == [SHARED_PROVIDER_STAGGER_SECONDS]

    def test_cross_provider_pays_nothing(self, no_sleep):
        applied = asyncio.run(stagger_if_shared_provider(
            FakeProvider("groq/openai/gpt-oss-120b"),
            FakeProvider("cerebras/zai-glm-4.7"),
        ))
        assert applied is False
        assert no_sleep.calls == []

    def test_unknown_provider_identity_skips_stagger(self, no_sleep):
        applied = asyncio.run(stagger_if_shared_provider(
            None, FakeProvider("groq/openai/gpt-oss-120b"),
        ))
        assert applied is False
        assert no_sleep.calls == []
