#!/usr/bin/env python3
"""Fail closed unless a Bandit JSON receipt is complete and clean."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _positive_loc(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _normalized_metric_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def validate_report(data: Any, scan_exit_code: int) -> list[str]:
    """Return contract failures for one pinned Bandit JSON report."""
    failures: list[str] = []

    if scan_exit_code != 0:
        failures.append(f"Bandit exited with non-success code {scan_exit_code}")

    if not isinstance(data, dict):
        return failures + ["report root must be a JSON object"]

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

    metrics = data.get("metrics")
    if not isinstance(metrics, dict):
        return failures + ["report.metrics must be a JSON object"]

    totals = metrics.get("_totals")
    if not isinstance(totals, dict) or not _positive_loc(totals.get("loc")):
        failures.append("report has no positive _totals.loc receipt")

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

    if http_loc <= 0:
        failures.append("report has no positive metric for http_server.py")
    if src_loc <= 0:
        failures.append("report has no positive metrics for the src/ tree")

    total_loc = totals.get("loc") if isinstance(totals, dict) else None
    if _positive_loc(total_loc) and total_loc < http_loc + src_loc:
        failures.append("report _totals.loc is inconsistent with required targets")

    return failures


def load_report(path: Path) -> tuple[Any | None, list[str]]:
    if not path.is_file():
        return None, [f"report is missing: {path}"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [f"report is not valid UTF-8 JSON: {exc}"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--scan-exit-code", required=True, type=int)
    args = parser.parse_args(argv)

    data, failures = load_report(args.report)
    if not failures:
        failures.extend(validate_report(data, args.scan_exit_code))

    if failures:
        print(
            "PYTHON_SAST_REPORT_FAIL "
            f"failures={len(failures)} scan_exit={args.scan_exit_code}"
        )
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        "PYTHON_SAST_REPORT_PASS "
        f"files={len(data['metrics']) - 1} "
        f"loc={data['metrics']['_totals']['loc']} "
        f"scan_exit={args.scan_exit_code}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
