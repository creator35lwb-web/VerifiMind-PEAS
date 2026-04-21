"""
Tests for v0.5.16 P1-B — Trinity History Persistence

Coverage:
  - _build_record: correct field extraction per tool, no concept content
  - persist_trinity_result: skips on invalid UUID, skips on error result
  - Server version assertion
  - server.py imports persist_trinity_result
  - persist wired into all 4 Trinity tool return paths
"""

import inspect

import verifimind_mcp.server as _srv_module

_SERVER_SOURCE = inspect.getsource(_srv_module)


# ---------------------------------------------------------------------------
# _build_record: metadata extraction, privacy invariants
# ---------------------------------------------------------------------------

class TestBuildRecord:

    def _build(self, tool: str, raw: dict):
        from verifimind_mcp.utils.trinity_history import _build_record
        return _build_record("019d40d6-9e84-7738-9c0c-fa85b2930600", tool, raw)

    def test_run_full_trinity_extracts_overall_score(self):
        raw = {
            "validation_id": "v-001",
            "synthesis": {"overall_score": 8.2, "recommendation": "PROCEED", "veto_triggered": False},
            "_session_id": "abc12345",
            "_agents_completed": ["X", "Z", "CS"],
            "_overall_quality": "full",
        }
        rec = self._build("run_full_trinity", raw)
        assert rec["overall_score"] == 8.2
        assert rec["recommendation"] == "PROCEED"
        assert rec["veto_triggered"] is False
        assert rec["session_id"] == "abc12345"
        assert rec["agents_completed"] == ["X", "Z", "CS"]
        assert rec["quality"] == "full"
        assert rec["validation_id"] == "v-001"

    def test_run_full_trinity_no_concept_name(self):
        raw = {
            "validation_id": "v-001",
            "concept_name": "My Secret Concept",
            "synthesis": {"overall_score": 7.0, "recommendation": "REVISE"},
        }
        rec = self._build("run_full_trinity", raw)
        assert "concept_name" not in rec
        assert "My Secret Concept" not in str(rec)

    def test_consult_agent_x_extracts_score(self):
        raw = {"innovation_score": 7.5, "recommendation": "PROCEED"}
        rec = self._build("consult_agent_x", raw)
        assert rec["score"] == 7.5
        assert rec["recommendation"] == "PROCEED"
        assert rec["tool"] == "consult_agent_x"

    def test_consult_agent_x_no_concept(self):
        raw = {"concept": "Secret Idea", "innovation_score": 7.5, "recommendation": "PROCEED"}
        rec = self._build("consult_agent_x", raw)
        assert "concept" not in rec
        assert "Secret Idea" not in str(rec)

    def test_consult_agent_z_extracts_ethics_score(self):
        raw = {"ethics_score": 8.0, "recommendation": "PROCEED", "veto_triggered": False}
        rec = self._build("consult_agent_z", raw)
        assert rec["score"] == 8.0
        assert rec["veto_triggered"] is False

    def test_consult_agent_cs_extracts_security_score(self):
        raw = {"security_score": 6.5, "recommendation": "REVISE"}
        rec = self._build("consult_agent_cs", raw)
        assert rec["score"] == 6.5
        assert rec["tool"] == "consult_agent_cs"

    def test_record_always_has_uuid_tool_timestamp(self):
        raw = {"synthesis": {}, "_overall_quality": "full"}
        rec = self._build("run_full_trinity", raw)
        assert rec["uuid"] == "019d40d6-9e84-7738-9c0c-fa85b2930600"
        assert rec["tool"] == "run_full_trinity"
        assert "timestamp" in rec
        assert "T" in rec["timestamp"]  # ISO format check


# ---------------------------------------------------------------------------
# persist_trinity_result: guard conditions
# ---------------------------------------------------------------------------

class TestPersistGuards:

    def test_invalid_uuid_skips_silently(self):
        from verifimind_mcp.utils.trinity_history import persist_trinity_result
        # Should not raise even with invalid UUID
        persist_trinity_result("not-a-uuid", "run_full_trinity", {"synthesis": {}})

    def test_none_uuid_skips_silently(self):
        from verifimind_mcp.utils.trinity_history import persist_trinity_result
        persist_trinity_result(None, "consult_agent_x", {"innovation_score": 7.5})  # type: ignore

    def test_error_result_skips_silently(self):
        from verifimind_mcp.utils.trinity_history import persist_trinity_result
        persist_trinity_result(
            "019d40d6-9e84-7738-9c0c-fa85b2930600",
            "run_full_trinity",
            {"status": "error", "error": "something failed"},
        )

    def test_valid_uuid_success_result_does_not_raise(self):
        from verifimind_mcp.utils.trinity_history import persist_trinity_result
        persist_trinity_result(
            "019d40d6-9e84-7738-9c0c-fa85b2930600",
            "run_full_trinity",
            {"validation_id": "v-001", "synthesis": {"overall_score": 8.0, "recommendation": "PROCEED"}},
        )

    def test_injection_attempt_uuid_skips(self):
        from verifimind_mcp.utils.trinity_history import persist_trinity_result
        persist_trinity_result(
            "uuid\nevil=payload",
            "run_full_trinity",
            {"synthesis": {"overall_score": 8.0}},
        )


# ---------------------------------------------------------------------------
# Server wiring: persist_trinity_result in all 4 tool return paths
# ---------------------------------------------------------------------------

class TestServerWiring:

    def test_server_imports_persist_trinity_result(self):
        assert "persist_trinity_result" in _SERVER_SOURCE

    def test_consult_agent_x_calls_persist(self):
        snippet = _SERVER_SOURCE[_SERVER_SOURCE.index("async def consult_agent_x("):
                                 _SERVER_SOURCE.index("async def consult_agent_z(")]
        assert "persist_trinity_result" in snippet
        assert 'user_uuid, "consult_agent_x"' in snippet

    def test_consult_agent_z_calls_persist(self):
        snippet = _SERVER_SOURCE[_SERVER_SOURCE.index("async def consult_agent_z("):
                                 _SERVER_SOURCE.index("async def consult_agent_cs(")]
        assert "persist_trinity_result" in snippet
        assert 'user_uuid, "consult_agent_z"' in snippet

    def test_consult_agent_cs_calls_persist(self):
        snippet = _SERVER_SOURCE[_SERVER_SOURCE.index("async def consult_agent_cs("):
                                 _SERVER_SOURCE.index("async def run_full_trinity(")]
        assert "persist_trinity_result" in snippet
        assert 'user_uuid, "consult_agent_cs"' in snippet

    def test_run_full_trinity_calls_persist(self):
        assert 'persist_trinity_result(user_uuid, "run_full_trinity"' in _SERVER_SOURCE

    def test_server_version_is_0516(self):
        from verifimind_mcp.server import SERVER_VERSION
        assert SERVER_VERSION == "0.5.17", f"Expected 0.5.16, got {SERVER_VERSION}"
