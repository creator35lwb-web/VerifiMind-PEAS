#!/usr/bin/env python3
"""Fail closed unless a pip-audit JSON receipt is complete and clean."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def validate_report(data: Any, audit_exit_code: int) -> list[str]:
    """Return contract failures for one pinned pip-audit JSON report."""
    failures: list[str] = []

    if audit_exit_code not in (0, 1):
        failures.append(f"pip-audit exited unexpectedly with code {audit_exit_code}")

    if not isinstance(data, dict):
        return failures + ["report root must be a JSON object"]

    dependencies = data.get("dependencies")
    if not isinstance(dependencies, list):
        return failures + ["report.dependencies must be a list"]
    if not dependencies:
        return failures + ["report contains zero audited dependencies"]

    fixes = data.get("fixes")
    if not isinstance(fixes, list):
        failures.append("report.fixes must be a list")

    vulnerability_count = 0
    for index, dependency in enumerate(dependencies):
        label = f"dependency[{index}]"
        if not isinstance(dependency, dict):
            failures.append(f"{label} must be an object")
            continue

        name = dependency.get("name")
        version = dependency.get("version")
        vulnerabilities = dependency.get("vulns")
        if not isinstance(name, str) or not name.strip():
            failures.append(f"{label} has no package name")
        if not isinstance(version, str) or not version.strip():
            failures.append(f"{label} has no resolved version")
        if not isinstance(vulnerabilities, list):
            failures.append(f"{label}.vulns must be a list")
            continue
        vulnerability_count += len(vulnerabilities)

    if failures:
        return failures

    if vulnerability_count:
        if audit_exit_code == 0:
            failures.append(
                "report contains known vulnerabilities but pip-audit returned success"
            )
        failures.append(
            f"report contains {vulnerability_count} known vulnerability finding(s)"
        )
    elif audit_exit_code != 0:
        failures.append(
            "report is clean but pip-audit returned a non-success exit code"
        )

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
    parser.add_argument("--audit-exit-code", required=True, type=int)
    args = parser.parse_args(argv)

    data, failures = load_report(args.report)
    if not failures:
        failures.extend(validate_report(data, args.audit_exit_code))

    if failures:
        print(
            "PYTHON_DEPENDENCY_AUDIT_FAIL "
            f"failures={len(failures)} audit_exit={args.audit_exit_code}"
        )
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        "PYTHON_DEPENDENCY_AUDIT_PASS "
        f"dependencies={len(data['dependencies'])} audit_exit={args.audit_exit_code}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
