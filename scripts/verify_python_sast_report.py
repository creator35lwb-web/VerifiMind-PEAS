#!/usr/bin/env python3
"""Fail closed unless a Bandit JSON receipt is complete and clean."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from security_receipt import load_json_receipt, run_receipt_verifier


EXPECTED_REPORT_NAME = "bandit-report.json"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPOSITORY_ROOT / EXPECTED_REPORT_NAME


def _positive_loc(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _normalized_metric_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _scan_content_failures(data: dict[str, Any], scan_exit_code: int) -> list[str]:
    failures: list[str] = []
    errors = data.get("errors")
    if not isinstance(errors, list):
        failures.append("report.errors must be a list")
    elif errors:
        failures.append(f"report contains {len(errors)} scan/input error(s)")

    results = data.get("results")
    if not isinstance(results, list):
        failures.append("report.results must be a list")
    elif results:
        failures.append(f"report contains {len(results)} security finding(s)")
        if scan_exit_code == 0:
            failures.append("report contains findings but Bandit returned success")
    return failures


def _target_loc(metrics: dict[Any, Any]) -> tuple[int, int]:
    http_loc = 0
    src_loc = 0
    for raw_path, metric in metrics.items():
        if raw_path == "_totals" or not isinstance(raw_path, str):
            continue
        if not isinstance(metric, dict):
            continue
        loc = metric.get("loc")
        if not _positive_loc(loc):
            continue

        path = _normalized_metric_path(raw_path)
        if path == "http_server.py":
            http_loc += loc
        elif path.startswith("src/"):
            src_loc += loc
    return http_loc, src_loc


def _metric_failures(metrics: dict[Any, Any]) -> list[str]:
    failures: list[str] = []
    totals = metrics.get("_totals")
    total_loc = totals.get("loc") if isinstance(totals, dict) else None
    if not _positive_loc(total_loc):
        failures.append("report has no positive _totals.loc receipt")

    http_loc, src_loc = _target_loc(metrics)
    if http_loc <= 0:
        failures.append("report has no positive metric for http_server.py")
    if src_loc <= 0:
        failures.append("report has no positive metrics for the src/ tree")
    if _positive_loc(total_loc) and total_loc < http_loc + src_loc:
        failures.append("report _totals.loc is inconsistent with required targets")
    return failures


def validate_report(data: Any, scan_exit_code: int) -> list[str]:
    """Return contract failures for one pinned Bandit JSON report."""
    failures: list[str] = []

    if scan_exit_code != 0:
        failures.append(f"Bandit exited with non-success code {scan_exit_code}")

    if not isinstance(data, dict):
        return failures + ["report root must be a JSON object"]

    failures.extend(_scan_content_failures(data, scan_exit_code))

    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        return failures + ["report.metrics must be a JSON object"]

    failures.extend(_metric_failures(metrics))
    return failures


def load_report() -> tuple[Any | None, list[str]]:
    """Load only the regular workflow-owned receipt at the repository root."""
    return load_json_receipt(REPORT_PATH)


def _pass_summary(data: Any, scan_exit_code: int) -> str:
    return (
        "PYTHON_SAST_REPORT_PASS "
        f"files={len(data['metrics']) - 1} "
        f"loc={data['metrics']['_totals']['loc']} "
        f"scan_exit={scan_exit_code}"
    )


def main(argv: list[str] | None = None) -> int:
    return run_receipt_verifier(
        argv,
        exit_code_option="--scan-exit-code",
        report_path=REPORT_PATH,
        validator=validate_report,
        failure_prefix="PYTHON_SAST_REPORT",
        exit_label="scan_exit",
        pass_summary=_pass_summary,
    )


if __name__ == "__main__":
    sys.exit(main())
