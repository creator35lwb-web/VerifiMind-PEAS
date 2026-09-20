#!/usr/bin/env python3
"""Fail closed unless a pip-audit JSON receipt is complete and clean."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from security_receipt import load_json_receipt, run_receipt_verifier


EXPECTED_REPORT_NAME = "pip-audit-report.json"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = REPOSITORY_ROOT / EXPECTED_REPORT_NAME


def _validate_dependency(dependency: Any, index: int) -> tuple[list[str], int]:
    label = f"dependency[{index}]"
    if not isinstance(dependency, dict):
        return [f"{label} must be an object"], 0

    failures: list[str] = []
    name = dependency.get("name")
    version = dependency.get("version")
    vulnerabilities = dependency.get("vulns")
    if not isinstance(name, str) or not name.strip():
        failures.append(f"{label} has no package name")
    if not isinstance(version, str) or not version.strip():
        failures.append(f"{label} has no resolved version")
    if not isinstance(vulnerabilities, list):
        failures.append(f"{label}.vulns must be a list")
        return failures, 0
    return failures, len(vulnerabilities)


def _validate_dependencies(dependencies: Any) -> tuple[list[str], int]:
    if not isinstance(dependencies, list):
        return ["report.dependencies must be a list"], 0
    if not dependencies:
        return ["report contains zero audited dependencies"], 0

    failures: list[str] = []
    vulnerability_count = 0
    for index, dependency in enumerate(dependencies):
        dependency_failures, dependency_vulnerabilities = _validate_dependency(
            dependency, index
        )
        failures.extend(dependency_failures)
        vulnerability_count += dependency_vulnerabilities
    return failures, vulnerability_count


def _finding_failures(vulnerability_count: int, audit_exit_code: int) -> list[str]:
    if vulnerability_count == 0:
        if audit_exit_code != 0:
            return ["report is clean but pip-audit returned a non-success exit code"]
        return []

    failures: list[str] = []
    if audit_exit_code == 0:
        failures.append(
            "report contains known vulnerabilities but pip-audit returned success"
        )
    failures.append(
        f"report contains {vulnerability_count} known vulnerability finding(s)"
    )
    return failures


def validate_report(data: Any, audit_exit_code: int) -> list[str]:
    """Return contract failures for one pinned pip-audit JSON report."""
    failures: list[str] = []

    if audit_exit_code not in (0, 1):
        failures.append(f"pip-audit exited unexpectedly with code {audit_exit_code}")

    if not isinstance(data, dict):
        return failures + ["report root must be a JSON object"]

    dependency_failures, vulnerability_count = _validate_dependencies(
        data.get("dependencies")
    )
    if dependency_failures:
        return failures + dependency_failures

    fixes = data.get("fixes")
    if not isinstance(fixes, list):
        failures.append("report.fixes must be a list")

    if failures:
        return failures

    return _finding_failures(vulnerability_count, audit_exit_code)


def load_report() -> tuple[Any | None, list[str]]:
    """Load only the regular workflow-owned receipt at the repository root."""
    return load_json_receipt(REPORT_PATH)


def _pass_summary(data: Any, audit_exit_code: int) -> str:
    return (
        "PYTHON_DEPENDENCY_AUDIT_PASS "
        f"dependencies={len(data['dependencies'])} audit_exit={audit_exit_code}"
    )


def main(argv: list[str] | None = None) -> int:
    return run_receipt_verifier(
        argv,
        exit_code_option="--audit-exit-code",
        report_path=REPORT_PATH,
        validator=validate_report,
        failure_prefix="PYTHON_DEPENDENCY_AUDIT",
        exit_label="audit_exit",
        pass_summary=_pass_summary,
    )


if __name__ == "__main__":
    sys.exit(main())
