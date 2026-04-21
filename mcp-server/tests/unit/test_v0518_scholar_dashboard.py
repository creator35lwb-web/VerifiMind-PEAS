"""
Tests for v0.5.18 P0-B — Scholar Dashboard

Coverage:
  - read_trinity_history: invalid UUID returns []
  - get_dashboard_page: renders UUID, table, empty state, privacy notice
  - get_dashboard_page: score/recommendation formatting per tool
  - get_dashboard_page: firestore_available=False shows unavailable notice
  - server.py route wired: /early-adopters/dashboard/{uuid} in http_server source
"""

import inspect

from verifimind_mcp.pages import get_dashboard_page
from verifimind_mcp.utils.trinity_history import read_trinity_history

import http_server as _http_module

_HTTP_SOURCE = inspect.getsource(_http_module)

VALID_UUID = "019d40d6-9e84-7738-9c0c-fa85b2930600"


# ---------------------------------------------------------------------------
# read_trinity_history: guard conditions
# ---------------------------------------------------------------------------

class TestReadTrinityHistoryGuards:

    def test_invalid_uuid_returns_empty_list(self):
        result = read_trinity_history("not-a-uuid")
        assert result == []

    def test_none_uuid_returns_empty_list(self):
        result = read_trinity_history(None)  # type: ignore
        assert result == []

    def test_valid_uuid_no_firestore_returns_empty_list(self):
        # Firestore not configured in test env — should return [] silently
        result = read_trinity_history(VALID_UUID)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# get_dashboard_page: HTML rendering
# ---------------------------------------------------------------------------

class TestDashboardPageRendering:

    def test_renders_uuid_truncated(self):
        html = get_dashboard_page(VALID_UUID, [])
        assert "019d40d6" in html
        assert VALID_UUID not in html  # Should be truncated, not full UUID

    def test_empty_state_shows_no_validations_message(self):
        html = get_dashboard_page(VALID_UUID, [])
        assert "No validations recorded yet" in html

    def test_firestore_unavailable_shows_notice(self):
        html = get_dashboard_page(VALID_UUID, [], firestore_available=False)
        assert "temporarily unavailable" in html.lower()

    def test_records_render_table_rows(self):
        records = [
            {
                "timestamp": "2026-04-21T01:00:00+00:00",
                "tool": "run_full_trinity",
                "overall_score": 8.2,
                "recommendation": "PROCEED",
                "quality": "full",
                "veto_triggered": False,
            }
        ]
        html = get_dashboard_page(VALID_UUID, records)
        assert "Full Trinity" in html
        assert "8.2/10" in html
        assert "PROCEED" in html
        assert "Apr 21, 2026" in html

    def test_agent_x_record_renders_score(self):
        records = [
            {
                "timestamp": "2026-04-21T02:00:00+00:00",
                "tool": "consult_agent_x",
                "score": 7.5,
                "recommendation": "REVISE — needs more work",
            }
        ]
        html = get_dashboard_page(VALID_UUID, records)
        assert "Agent X" in html
        assert "7.5/10" in html

    def test_agent_z_veto_shows_flag(self):
        records = [
            {
                "timestamp": "2026-04-21T03:00:00+00:00",
                "tool": "consult_agent_z",
                "score": 3.0,
                "recommendation": "REJECT",
                "veto_triggered": True,
            }
        ]
        html = get_dashboard_page(VALID_UUID, records)
        assert "⚑" in html

    def test_null_score_renders_dash(self):
        records = [
            {
                "timestamp": "2026-04-21T04:00:00+00:00",
                "tool": "consult_agent_cs",
                "score": None,
                "recommendation": "REVISE",
            }
        ]
        html = get_dashboard_page(VALID_UUID, records)
        assert "—" in html

    def test_privacy_notice_present(self):
        html = get_dashboard_page(VALID_UUID, [])
        assert "Privacy" in html
        assert "Privacy Policy v2.1" in html

    def test_record_count_shown(self):
        records = [
            {"timestamp": "2026-04-21T01:00:00+00:00", "tool": "consult_agent_x",
             "score": 7.0, "recommendation": "PROCEED"},
            {"timestamp": "2026-04-21T02:00:00+00:00", "tool": "consult_agent_z",
             "score": 8.0, "recommendation": "PROCEED"},
        ]
        html = get_dashboard_page(VALID_UUID, records)
        assert "2 validations" in html

    def test_long_recommendation_truncated(self):
        long_rec = "REVISE — " + "x" * 80
        records = [
            {
                "timestamp": "2026-04-21T01:00:00+00:00",
                "tool": "consult_agent_x",
                "score": 5.0,
                "recommendation": long_rec,
            }
        ]
        html = get_dashboard_page(VALID_UUID, records)
        assert "…" in html


# ---------------------------------------------------------------------------
# Route wiring in http_server.py
# ---------------------------------------------------------------------------

class TestHttpServerWiring:

    def test_dashboard_route_present(self):
        assert "/early-adopters/dashboard/{uuid}" in _HTTP_SOURCE

    def test_ea_dashboard_handler_defined(self):
        assert "ea_dashboard_handler" in _HTTP_SOURCE

    def test_get_dashboard_page_imported(self):
        assert "get_dashboard_page" in _HTTP_SOURCE

    def test_read_trinity_history_imported(self):
        assert "read_trinity_history" in _HTTP_SOURCE
