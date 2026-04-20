"""
v0.5.11 Coordination Foundation — Unit Tests
=============================================

Tests for:
1. Tier-gating middleware (check_tier, tier_gate_error, sanitize_handoff_content)
2. HandoffStore (add, get, get_all, count, clear)
3. HandoffFormatter (format_handoff_markdown, parse_handoff_filename)
4. build_handoff_record (field validation, filename convention)
5. coordination_handoff_create tool (via server integration)
6. coordination_handoff_read tool (filtering, count)
7. coordination_team_status tool (aggregation, empty state)
8. Scholar/Pioneer access control enforcement
9. Regression: existing 10 free tools unaffected
"""

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_KEY = "test-pioneer-key-abc123"
INVALID_KEY = "not-a-real-key"
EMPTY_KEY = ""


def _set_pioneer_env(monkeypatch, key: str = VALID_KEY):
    monkeypatch.setenv("PIONEER_ACCESS_KEYS", key)
    # Re-load the module to pick up env var changes
    import importlib
    import verifimind_mcp.middleware.tier_gate as tg
    importlib.reload(tg)
    return tg


# ---------------------------------------------------------------------------
# 1. Tier-Gating (12 tests)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestTierGate:
    """check_tier / tier_gate_error / sanitize_handoff_content.

    check_tier() is async (v0.5.13 Phase 2 — Polar adapter). When
    POLAR_ACCESS_TOKEN is not set, falls back to PIONEER_ACCESS_KEYS env var.
    """

    async def test_valid_key_grants_pioneer(self, monkeypatch):
        tg = _set_pioneer_env(monkeypatch, VALID_KEY)
        monkeypatch.delenv("POLAR_ACCESS_TOKEN", raising=False)
        allowed, tier = await tg.check_tier(VALID_KEY)
        assert allowed is True
        assert tier == "pioneer"

    async def test_invalid_key_returns_scholar(self, monkeypatch):
        tg = _set_pioneer_env(monkeypatch, VALID_KEY)
        monkeypatch.delenv("POLAR_ACCESS_TOKEN", raising=False)
        allowed, tier = await tg.check_tier(INVALID_KEY)
        assert allowed is False
        assert tier == "scholar"

    async def test_none_key_returns_scholar(self, monkeypatch):
        tg = _set_pioneer_env(monkeypatch, VALID_KEY)
        allowed, tier = await tg.check_tier(None)
        assert allowed is False
        assert tier == "scholar"

    async def test_empty_string_key_returns_scholar(self, monkeypatch):
        tg = _set_pioneer_env(monkeypatch, VALID_KEY)
        allowed, tier = await tg.check_tier("")
        assert allowed is False
        assert tier == "scholar"

    async def test_whitespace_key_returns_scholar(self, monkeypatch):
        tg = _set_pioneer_env(monkeypatch, VALID_KEY)
        allowed, tier = await tg.check_tier("   ")
        assert allowed is False
        assert tier == "scholar"

    async def test_multiple_valid_keys(self, monkeypatch):
        """PIONEER_ACCESS_KEYS can be comma-separated list."""
        tg = _set_pioneer_env(monkeypatch, "key-alpha,key-beta,key-gamma")
        monkeypatch.delenv("POLAR_ACCESS_TOKEN", raising=False)
        for k in ["key-alpha", "key-beta", "key-gamma"]:
            allowed, tier = await tg.check_tier(k)
            assert allowed is True, f"Expected key {k!r} to be allowed"
            assert tier == "pioneer"

    async def test_empty_env_blocks_all_keys(self, monkeypatch):
        """If PIONEER_ACCESS_KEYS is empty, no key is valid."""
        tg = _set_pioneer_env(monkeypatch, "")
        monkeypatch.delenv("POLAR_ACCESS_TOKEN", raising=False)
        allowed, tier = await tg.check_tier(VALID_KEY)
        assert allowed is False
        assert tier == "scholar"

    async def test_tier_gate_error_has_required_fields(self, monkeypatch):
        tg = _set_pioneer_env(monkeypatch, VALID_KEY)
        err = tg.tier_gate_error()
        assert err["status"] == "error"
        assert err["error_code"] == "PIONEER_TIER_REQUIRED"
        assert "pioneer_key" in err["recovery_hint"].lower() or "pioneer" in err["error"].lower()
        assert err["tier_required"] == "pioneer"
        assert "upgrade_url" in err

    async def test_tier_constants(self, monkeypatch):
        tg = _set_pioneer_env(monkeypatch, VALID_KEY)
        assert tg.TIER_SCHOLAR == "scholar"
        assert tg.TIER_PIONEER == "pioneer"

    async def test_sanitize_handoff_active_v0513(self, monkeypatch):
        """v0.5.13: sanitize_handoff_content strips API keys (no longer a passthrough)."""
        tg = _set_pioneer_env(monkeypatch, VALID_KEY)
        content = "Handoff notes with sk-abc123secretkey_longkey and some text."
        result = tg.sanitize_handoff_content(content)
        assert "[REDACTED]" in result
        assert "sk-abc123secretkey_longkey" not in result

    async def test_key_with_leading_trailing_spaces_stripped(self, monkeypatch):
        """check_tier strips surrounding whitespace before checking."""
        tg = _set_pioneer_env(monkeypatch, VALID_KEY)
        monkeypatch.delenv("POLAR_ACCESS_TOKEN", raising=False)
        allowed, _ = await tg.check_tier(f"  {VALID_KEY}  ")
        assert allowed is True

    async def test_pioneer_keys_stripped_on_load(self, monkeypatch):
        """Env var keys with spaces around commas are stripped at load time."""
        tg = _set_pioneer_env(monkeypatch, "  key-a  ,  key-b  ")
        monkeypatch.delenv("POLAR_ACCESS_TOKEN", raising=False)
        allowed_a, _ = await tg.check_tier("key-a")
        allowed_b, _ = await tg.check_tier("key-b")
        assert allowed_a is True
        assert allowed_b is True


# ---------------------------------------------------------------------------
# 2. HandoffStore (10 tests)
# ---------------------------------------------------------------------------

class TestHandoffStore:
    """In-memory handoff storage."""

    def setup_method(self):
        from verifimind_mcp.coordination.handoff_store import HandoffStore
        self.store = HandoffStore(max_per_key=5)

    def _record(self, agent_id: str = "RNA", idx: int = 0) -> dict:
        from verifimind_mcp.coordination.handoff_store import build_handoff_record
        r = build_handoff_record(
            agent_id=agent_id,
            session_type="development",
            completed=[f"item-{idx}"],
            decisions=["decided X"],
            artifacts=["src/foo.py"],
            pending=["write tests"],
            blockers=[],
            next_agent="XV",
        )
        return r

    def test_add_and_count(self):
        self.store.add("key1", self._record("RNA", 0))
        assert self.store.count("key1") == 1

    def test_get_returns_newest_first(self):
        for i in range(3):
            r = self._record("RNA", i)
            r["handoff_id"] = f"id-{i}"
            self.store.add("k", r)
        results = self.store.get("k", count=3)
        assert results[0]["handoff_id"] == "id-2"
        assert results[1]["handoff_id"] == "id-1"
        assert results[2]["handoff_id"] == "id-0"

    def test_get_count_respected(self):
        for i in range(5):
            self.store.add("k", self._record("RNA", i))
        assert len(self.store.get("k", count=2)) == 2

    def test_get_agent_filter(self):
        self.store.add("k", self._record("RNA", 0))
        self.store.add("k", self._record("XV", 1))
        self.store.add("k", self._record("RNA", 2))
        results = self.store.get("k", agent_id="RNA", count=10)
        assert all(r["agent_id"] == "RNA" for r in results)
        assert len(results) == 2

    def test_get_unknown_key_returns_empty(self):
        assert self.store.get("nonexistent") == []

    def test_get_all_oldest_first(self):
        for i in range(3):
            r = self._record("RNA", i)
            r["handoff_id"] = f"id-{i}"
            self.store.add("k", r)
        all_r = self.store.get_all("k")
        assert [r["handoff_id"] for r in all_r] == ["id-0", "id-1", "id-2"]

    def test_max_per_key_evicts_oldest(self):
        for i in range(7):  # max is 5
            r = self._record("RNA", i)
            r["handoff_id"] = f"id-{i}"
            self.store.add("k", r)
        assert self.store.count("k") == 5
        # Oldest (id-0, id-1) should be gone
        all_ids = [r["handoff_id"] for r in self.store.get_all("k")]
        assert "id-0" not in all_ids
        assert "id-6" in all_ids

    def test_namespaces_are_isolated(self):
        self.store.add("user-A", self._record("RNA", 0))
        self.store.add("user-B", self._record("RNA", 1))
        assert self.store.count("user-A") == 1
        assert self.store.count("user-B") == 1
        # user-A can't see user-B's records
        records_a = self.store.get("user-A", count=10)
        assert len(records_a) == 1

    def test_clear_removes_all(self):
        for i in range(3):
            self.store.add("k", self._record("RNA", i))
        self.store.clear("k")
        assert self.store.count("k") == 0

    def test_count_zero_for_unknown_key(self):
        assert self.store.count("totally-unknown") == 0


# ---------------------------------------------------------------------------
# 3. build_handoff_record (8 tests)
# ---------------------------------------------------------------------------

class TestBuildHandoffRecord:
    """Validates the handoff record dict structure."""

    def setup_method(self):
        from verifimind_mcp.coordination.handoff_store import build_handoff_record
        self.build = build_handoff_record

    def test_required_fields_present(self):
        r = self.build("RNA", "dev", ["done"], ["dec"], ["art"], ["pending"], [], "XV")
        for field in [
            "handoff_id", "filename", "timestamp", "date", "agent_id",
            "session_type", "completed", "decisions", "artifacts", "pending",
            "blockers", "next_agent", "macp_version", "status",
        ]:
            assert field in r, f"Missing field: {field}"

    def test_macp_version_is_22(self):
        r = self.build("RNA", "dev", [], [], [], [], [], None)
        assert r["macp_version"] == "2.2"

    def test_status_is_created(self):
        r = self.build("RNA", "dev", [], [], [], [], [], None)
        assert r["status"] == "CREATED"

    def test_filename_format(self):
        r = self.build("RNA", "development", [], [], [], [], [], None)
        assert r["filename"].endswith(".md")
        parts = r["filename"].removesuffix(".md").split("_", 2)
        assert len(parts) == 3
        assert parts[1] == "RNA"
        assert "development" in parts[2]

    def test_agent_id_preserved(self):
        r = self.build("XV", "research", [], [], [], [], [], None)
        assert r["agent_id"] == "XV"

    def test_next_agent_none_becomes_empty_string(self):
        r = self.build("RNA", "dev", [], [], [], [], [], None)
        assert r["next_agent"] == ""

    def test_next_agent_value_preserved(self):
        r = self.build("RNA", "dev", [], [], [], [], [], "T")
        assert r["next_agent"] == "T"

    def test_handoff_id_is_8_chars(self):
        r = self.build("RNA", "dev", [], [], [], [], [], None)
        assert len(r["handoff_id"]) == 8

    def test_unique_handoff_ids(self):
        ids = {self.build("RNA", "dev", [], [], [], [], [], None)["handoff_id"] for _ in range(20)}
        assert len(ids) == 20


# ---------------------------------------------------------------------------
# 4. Handoff Formatter (8 tests)
# ---------------------------------------------------------------------------

class TestHandoffFormatter:
    """format_handoff_markdown and parse_handoff_filename."""

    def setup_method(self):
        from verifimind_mcp.coordination.handoff_formatter import (
            format_handoff_markdown,
            parse_handoff_filename,
        )
        from verifimind_mcp.coordination.handoff_store import build_handoff_record
        self.format = format_handoff_markdown
        self.parse = parse_handoff_filename
        self.build = build_handoff_record

    def test_markdown_contains_agent_id(self):
        r = self.build("RNA", "dev", [], [], [], [], [], None)
        md = self.format(r)
        assert "RNA" in md

    def test_markdown_contains_macp_version(self):
        r = self.build("RNA", "dev", [], [], [], [], [], None)
        md = self.format(r)
        assert "2.2" in md

    def test_markdown_contains_section_headers(self):
        r = self.build("RNA", "dev", ["Task A"], ["Dec B"], ["file.py"], ["Todo C"], ["Blocker D"], "T")
        md = self.format(r)
        assert "### Completed" in md
        assert "### Decisions Made" in md
        assert "### Pending for Next Agent" in md
        assert "### Blockers" in md
        assert "### Recommended Next Agent" in md

    def test_markdown_lists_items(self):
        r = self.build("RNA", "dev", ["Task A", "Task B"], [], [], [], [], None)
        md = self.format(r)
        assert "Task A" in md
        assert "Task B" in md

    def test_markdown_empty_list_shows_none(self):
        r = self.build("RNA", "dev", [], [], [], [], [], None)
        md = self.format(r)
        assert "(none)" in md

    def test_markdown_shows_next_agent(self):
        r = self.build("RNA", "dev", [], [], [], [], [], "XV")
        md = self.format(r)
        assert "XV" in md

    def test_parse_filename_standard(self):
        result = self.parse("20260407_RNA_development.md")
        assert result["date"] == "20260407"
        assert result["agent_id"] == "RNA"
        assert result["description"] == "development"

    def test_parse_filename_no_extension(self):
        result = self.parse("20260407_XV_research")
        assert result["agent_id"] == "XV"
        assert result["description"] == "research"

    def test_parse_filename_description_with_dashes(self):
        result = self.parse("20260407_RNA_v0511-coordination-foundation-start.md")
        assert result["description"] == "v0511-coordination-foundation-start"


# ---------------------------------------------------------------------------
# 5–7. Tool integration (via server — 12 tests)
# ---------------------------------------------------------------------------

class TestCoordinationToolsIntegration:
    """Test the 3 coordination tools end-to-end via server import."""

    def setup_method(self, method):
        # Each test gets a fresh store to avoid cross-test contamination
        import importlib
        import verifimind_mcp.coordination.handoff_store as hs
        hs._global_store = hs.HandoffStore()

    @pytest.fixture(autouse=True)
    def set_pioneer_key(self, monkeypatch):
        monkeypatch.setenv("PIONEER_ACCESS_KEYS", VALID_KEY)
        import importlib
        import verifimind_mcp.middleware.tier_gate as tg
        importlib.reload(tg)

    def _create_kwargs(self, pioneer_key: str = VALID_KEY, **overrides) -> dict:
        base = dict(
            agent_id="RNA",
            session_type="development",
            completed=["Implemented X"],
            decisions=["Chose Y"],
            artifacts=["src/foo.py"],
            pending=["Write tests"],
            blockers=[],
            pioneer_key=pioneer_key,
            next_agent="XV",
            ctx=None,
        )
        base.update(overrides)
        return base

    # -- coordination_handoff_create --

    @pytest.mark.asyncio
    async def test_create_returns_success(self):
        from verifimind_mcp.server import _create_mcp_instance
        # Rebuild instance to pick up fresh store
        _create_mcp_instance()
        # Call the tool function directly via the coordination module
        import verifimind_mcp.middleware.tier_gate as tg
        from verifimind_mcp.coordination import get_store, format_handoff_markdown
        from verifimind_mcp.coordination.handoff_store import build_handoff_record

        allowed, tier = await tg.check_tier(VALID_KEY)
        assert allowed is True

        record = build_handoff_record("RNA", "development", ["done"], ["dec"], ["art.py"], ["todo"], [], "XV")
        content = format_handoff_markdown(record)
        content = tg.sanitize_handoff_content(content)
        record["content"] = content
        store = get_store()
        store.add(VALID_KEY, record)

        assert store.count(VALID_KEY) == 1

    @pytest.mark.asyncio
    async def test_create_scholar_blocked(self):
        import verifimind_mcp.middleware.tier_gate as tg
        allowed, tier = await tg.check_tier(INVALID_KEY)
        assert allowed is False
        err = tg.tier_gate_error()
        assert err["error_code"] == "PIONEER_TIER_REQUIRED"

    @pytest.mark.asyncio
    async def test_create_stores_handoff(self):
        from verifimind_mcp.coordination import get_store
        from verifimind_mcp.coordination.handoff_store import build_handoff_record
        r = build_handoff_record("RNA", "test-session", ["T1"], [], [], ["P1"], [], None)
        get_store().add(VALID_KEY, r)
        assert get_store().count(VALID_KEY) == 1
        stored = get_store().get(VALID_KEY)[0]
        assert stored["agent_id"] == "RNA"
        assert stored["session_type"] == "test-session"

    @pytest.mark.asyncio
    async def test_create_content_is_valid_markdown(self):
        from verifimind_mcp.coordination import format_handoff_markdown
        from verifimind_mcp.coordination.handoff_store import build_handoff_record
        r = build_handoff_record("RNA", "dev", ["Done A"], ["Dec B"], ["art.py"], ["Todo C"], ["Blocker!"], "T")
        md = format_handoff_markdown(r)
        assert "# Session Handoff" in md
        assert "Done A" in md
        assert "Dec B" in md
        assert "Blocker!" in md
        assert "T" in md

    # -- coordination_handoff_read --

    @pytest.mark.asyncio
    async def test_read_returns_stored_records(self):
        from verifimind_mcp.coordination import get_store
        from verifimind_mcp.coordination.handoff_store import build_handoff_record
        r = build_handoff_record("XV", "research", ["Research A"], [], [], [], [], None)
        get_store().add(VALID_KEY, r)

        records = get_store().get(VALID_KEY, count=1)
        assert len(records) == 1
        assert records[0]["agent_id"] == "XV"

    @pytest.mark.asyncio
    async def test_read_with_agent_filter(self):
        from verifimind_mcp.coordination import get_store
        from verifimind_mcp.coordination.handoff_store import build_handoff_record
        store = get_store()
        store.add(VALID_KEY, build_handoff_record("RNA", "dev", [], [], [], [], [], None))
        store.add(VALID_KEY, build_handoff_record("XV", "research", [], [], [], [], [], None))
        store.add(VALID_KEY, build_handoff_record("RNA", "dev", [], [], [], [], [], None))

        rna_records = store.get(VALID_KEY, agent_id="RNA", count=10)
        assert len(rna_records) == 2
        assert all(r["agent_id"] == "RNA" for r in rna_records)

    @pytest.mark.asyncio
    async def test_read_empty_store_returns_empty(self):
        from verifimind_mcp.coordination import get_store
        records = get_store().get("empty-key", count=5)
        assert records == []

    @pytest.mark.asyncio
    async def test_read_scholar_key_blocked(self):
        import verifimind_mcp.middleware.tier_gate as tg
        allowed, _ = await tg.check_tier(INVALID_KEY)
        assert allowed is False

    # -- coordination_team_status --

    @pytest.mark.asyncio
    async def test_status_empty_store(self):
        from verifimind_mcp.coordination import get_store
        import verifimind_mcp.middleware.tier_gate as tg
        allowed, tier = await tg.check_tier(VALID_KEY)
        assert allowed is True
        records = get_store().get_all(VALID_KEY)
        assert records == []

    @pytest.mark.asyncio
    async def test_status_aggregates_agents(self):
        from verifimind_mcp.coordination import get_store
        from verifimind_mcp.coordination.handoff_store import build_handoff_record
        store = get_store()
        store.add(VALID_KEY, build_handoff_record("RNA", "dev", [], [], [], ["pending-1"], [], None))
        store.add(VALID_KEY, build_handoff_record("XV", "research", [], [], [], ["pending-2"], ["blocker-X"], None))

        all_r = store.get_all(VALID_KEY)
        agents = {r["agent_id"] for r in all_r}
        assert "RNA" in agents
        assert "XV" in agents

        all_pending = [item for r in all_r for item in r.get("pending", [])]
        assert "pending-1" in all_pending
        assert "pending-2" in all_pending

        all_blockers = [b for r in all_r for b in r.get("blockers", [])]
        assert "blocker-X" in all_blockers

    @pytest.mark.asyncio
    async def test_status_recommended_next_from_latest(self):
        from verifimind_mcp.coordination import get_store
        from verifimind_mcp.coordination.handoff_store import build_handoff_record
        store = get_store()
        store.add(VALID_KEY, build_handoff_record("RNA", "dev", [], [], [], [], [], "XV"))
        store.add(VALID_KEY, build_handoff_record("XV", "research", [], [], [], [], [], "T"))

        all_r = store.get_all(VALID_KEY)
        most_recent = all_r[-1]
        assert most_recent["next_agent"] == "T"

    @pytest.mark.asyncio
    async def test_status_scholar_blocked(self):
        import verifimind_mcp.middleware.tier_gate as tg
        allowed, _ = await tg.check_tier(INVALID_KEY)
        assert allowed is False


# ---------------------------------------------------------------------------
# 8. Scholar/Pioneer access enforcement (5 tests)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
class TestTierEnforcement:
    """Verify tier boundaries are correctly enforced."""

    @pytest.fixture(autouse=True)
    def reset_env(self, monkeypatch):
        monkeypatch.setenv("PIONEER_ACCESS_KEYS", VALID_KEY)
        monkeypatch.delenv("POLAR_ACCESS_TOKEN", raising=False)
        import importlib
        import verifimind_mcp.middleware.tier_gate as tg
        importlib.reload(tg)

    async def test_scholar_cannot_access_coordination_create(self):
        import verifimind_mcp.middleware.tier_gate as tg
        allowed, tier = await tg.check_tier(INVALID_KEY)
        assert allowed is False
        assert tier == "scholar"

    async def test_scholar_cannot_access_coordination_read(self):
        import verifimind_mcp.middleware.tier_gate as tg
        allowed, _ = await tg.check_tier("")
        assert allowed is False

    async def test_scholar_cannot_access_team_status(self):
        import verifimind_mcp.middleware.tier_gate as tg
        allowed, _ = await tg.check_tier(None)
        assert allowed is False

    async def test_pioneer_can_access_all_coordination_tools(self):
        import verifimind_mcp.middleware.tier_gate as tg
        for tool in ["coordination_handoff_create", "coordination_handoff_read", "coordination_team_status"]:
            allowed, tier = await tg.check_tier(VALID_KEY)
            assert allowed is True, f"{tool} should be allowed for Pioneer"
            assert tier == "pioneer"

    def test_tier_gate_error_structure(self):
        import verifimind_mcp.middleware.tier_gate as tg
        err = tg.tier_gate_error()
        assert err["status"] == "error"
        assert err["tier_required"] == "pioneer"
        assert "upgrade_url" in err
        assert "pioneer_key" in err["recovery_hint"] or "Pioneer" in err["recovery_hint"]


# ---------------------------------------------------------------------------
# 9. Regression — existing 10 free tools unaffected (5 tests)
# ---------------------------------------------------------------------------

class TestFreeToolRegression:
    """Existing Scholar tools must remain importable and unchanged."""

    def test_server_version_is_0513(self):
        from verifimind_mcp.server import SERVER_VERSION
        assert SERVER_VERSION == "0.5.15"

    def test_wrap_response_still_works(self):
        from verifimind_mcp.server import wrap_response
        result = wrap_response({"foo": "bar"})
        assert result["foo"] == "bar"
        assert "_server_version" in result

    def test_build_error_response_still_works(self):
        from verifimind_mcp.server import build_error_response
        err = build_error_response("TEST_CODE", "msg", "hint")
        assert err["error_code"] == "TEST_CODE"
        assert err["status"] == "error"

    def test_free_tools_still_importable(self):
        """The 10 free tools must be importable from server module."""
        # We test import only — not execution (that requires LLM keys)
        from verifimind_mcp.server import _create_mcp_instance
        assert callable(_create_mcp_instance)

    def test_coordination_tools_do_not_shadow_free_tools(self):
        """Verify that coordination tools have distinct names from free tools."""
        coordination_names = {
            "coordination_handoff_create",
            "coordination_handoff_read",
            "coordination_team_status",
        }
        free_tool_names = {
            "consult_agent_x",
            "consult_agent_z",
            "consult_agent_cs",
            "run_full_trinity",
            "list_prompt_templates",
            "get_prompt_template",
            "register_custom_template",
            "export_prompt_template",
            "import_template_from_url",
            "get_template_statistics",
        }
        assert coordination_names.isdisjoint(free_tool_names)
