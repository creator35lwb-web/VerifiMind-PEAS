"""Bounded retention and truthful-write contracts for opt-in shared history."""

import json

from verifimind_mcp import server


def _entry(index: int) -> dict:
    return {
        "validation_id": f"validation-{index:02d}",
        "concept_name": f"private-concept-{index:02d}",
        "completed_at": f"2026-08-06T00:{index:02d}:00+00:00",
        "synthesis": {
            "recommendation": "proceed" if index % 2 else "revise",
            "overall_score": 7.0,
            "veto_triggered": False,
        },
    }


def test_save_enforces_twenty_entry_cap_and_atomic_contract(tmp_path, monkeypatch):
    history_path = tmp_path / "history.json"
    monkeypatch.setattr(server, "HISTORY_PATH", history_path)
    history = {
        "validations": [_entry(index) for index in range(25)],
        "metadata": {"total_validations": 25, "last_updated": "stale"},
    }

    assert server.save_validation_history(history) is True

    stored = json.loads(history_path.read_text(encoding="utf-8"))
    assert len(stored["validations"]) == server.VALIDATION_HISTORY_MAX_ENTRIES == 20
    assert stored["validations"][0]["validation_id"] == "validation-05"
    assert stored["validations"][-1]["validation_id"] == "validation-24"
    assert stored["metadata"]["total_validations"] == 20
    assert stored["metadata"]["last_updated"] == "2026-08-06T00:24:00+00:00"
    assert stored["metadata"]["retention"] == (
        server.validation_history_retention_contract()
    )
    assert not history_path.with_suffix(".json.tmp").exists()


def test_load_prunes_legacy_unbounded_file_before_returning_it(tmp_path, monkeypatch):
    history_path = tmp_path / "history.json"
    monkeypatch.setattr(server, "HISTORY_PATH", history_path)
    legacy = {
        "validations": [_entry(index) for index in range(23)],
        "metadata": {"total_validations": 23},
    }
    history_path.write_text(json.dumps(legacy), encoding="utf-8")

    loaded = server.load_validation_history()

    assert len(loaded["validations"]) == 20
    assert loaded["validations"][0]["validation_id"] == "validation-03"
    persisted = json.loads(history_path.read_text(encoding="utf-8"))
    assert persisted == loaded


def test_load_drops_non_record_legacy_values_fail_closed(tmp_path, monkeypatch):
    history_path = tmp_path / "history.json"
    monkeypatch.setattr(server, "HISTORY_PATH", history_path)
    history_path.write_text(
        json.dumps({"validations": ["raw-secret", None, _entry(1)]}),
        encoding="utf-8",
    )

    loaded = server.load_validation_history()

    assert [item["validation_id"] for item in loaded["validations"]] == [
        "validation-01"
    ]
    assert "raw-secret" not in history_path.read_text(encoding="utf-8")


def test_save_failure_is_reported_instead_of_claimed(tmp_path, monkeypatch):
    # A directory cannot be replaced by the atomic history file on any supported OS.
    monkeypatch.setattr(server, "HISTORY_PATH", tmp_path)

    assert server.save_validation_history({"validations": [_entry(1)]}) is False


def test_public_history_summaries_expose_the_retention_contract(monkeypatch):
    monkeypatch.setattr(
        server,
        "load_validation_history",
        lambda: {
            "validations": [_entry(1)],
            "metadata": {"last_updated": "2026-08-06T00:01:00+00:00"},
        },
    )

    aggregate = server._aggregate_validation_stats()
    assert aggregate["total_validations"] == 1
    assert aggregate["retention"]["max_entries"] == 20
    assert aggregate["retention"]["fixed_time_retention_guaranteed"] is False
