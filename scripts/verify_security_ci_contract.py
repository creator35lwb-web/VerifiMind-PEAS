#!/usr/bin/env python3
"""Verify that public security checks cannot be replaced by pass-through jobs."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = Path(".github/workflows")
SECURITY_WORKFLOW = WORKFLOW_DIR / "security-scan.yml"
DOCS_WORKFLOW = WORKFLOW_DIR / "docs-ci-bypass.yml"
TEST_WORKFLOW = WORKFLOW_DIR / "test.yml"
SECURITY_COPIES = (
    Path("SECURITY.md"),
    Path(".macp-public/governance/SECURITY.md"),
)


def job_check_names(workflow: Path) -> list[tuple[str, str]]:
    """Return (rendered check name, job id) pairs from a simple workflow."""
    pairs: list[tuple[str, str]] = []
    in_jobs = False
    current_job: str | None = None
    current_name: str | None = None

    def finish() -> None:
        nonlocal current_job, current_name
        if current_job is not None:
            pairs.append((current_name or current_job, current_job))
        current_job = None
        current_name = None

    for line in workflow.read_text(encoding="utf-8").splitlines():
        if line == "jobs:":
            in_jobs = True
            continue
        if not in_jobs:
            continue
        if line and not line.startswith(" "):
            finish()
            break

        job_match = re.match(r"^  ([A-Za-z0-9_-]+):\s*(?:#.*)?$", line)
        if job_match:
            finish()
            current_job = job_match.group(1)
            continue

        name_match = re.match(r"^    name:\s*(.+?)\s*$", line)
        if current_job is not None and name_match:
            current_name = name_match.group(1).strip("'\"")

    finish()
    return pairs


def event_block(workflow_text: str, event: str) -> str | None:
    lines = workflow_text.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line == f"  {event}:"),
        None,
    )
    if start is None:
        return None
    block = [lines[start]]
    for line in lines[start + 1 :]:
        if re.match(r"^  [A-Za-z_][A-Za-z0-9_-]*:\s*$", line):
            break
        if line and not line.startswith(" "):
            break
        block.append(line)
    return "\n".join(block)


def verify(root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    workflow_root = root / WORKFLOW_DIR
    workflows = sorted(workflow_root.glob("*.yml")) + sorted(
        workflow_root.glob("*.yaml")
    )
    if not workflows:
        return ["no GitHub Actions workflows found"]

    owners: dict[str, list[str]] = defaultdict(list)
    for workflow in workflows:
        relative = workflow.relative_to(root).as_posix()
        for check_name, job_id in job_check_names(workflow):
            owners[check_name].append(f"{relative}:{job_id}")
    for check_name, producers in sorted(owners.items()):
        if len(producers) != 1:
            failures.append(
                f"check name {check_name!r} has {len(producers)} producers: {producers}"
            )

    expected = {
        "Bandit SAST Analysis": ".github/workflows/security-scan.yml:bandit-sast",
        "Python Dependency Audit": (
            ".github/workflows/security-scan.yml:python-dependency-audit"
        ),
        "CodeQL Analysis": ".github/workflows/security-scan.yml:codeql-analysis",
        "Public Documentation Contract": (
            ".github/workflows/docs-ci-bypass.yml:public-docs-contract"
        ),
    }
    for check_name, producer in expected.items():
        if owners.get(check_name) != [producer]:
            failures.append(
                f"check {check_name!r} must be owned only by {producer}"
            )

    security_path = root / SECURITY_WORKFLOW
    docs_path = root / DOCS_WORKFLOW
    test_path = root / TEST_WORKFLOW
    for path in (security_path, docs_path, test_path):
        if not path.is_file():
            failures.append(f"required workflow is missing: {path.relative_to(root)}")
    if failures:
        return failures

    security_text = security_path.read_text(encoding="utf-8")
    docs_text = docs_path.read_text(encoding="utf-8")
    test_text = test_path.read_text(encoding="utf-8")

    if "run: python scripts/verify_security_ci_contract.py" not in security_text:
        failures.append(
            "always-on Bandit job does not execute the security CI contract"
        )
    if "      - '.github/workflows/**'" not in docs_text:
        failures.append(
            "documentation contract does not cover every workflow-file change"
        )

    for event in ("push", "pull_request"):
        block = event_block(security_text, event)
        if block is None:
            failures.append(f"security workflow does not run on {event}")
        elif re.search(r"^\s+paths(?:-ignore)?:", block, re.MULTILINE):
            failures.append(f"security workflow {event} trigger is path-scoped")

    scanner_bypass = re.compile(
        r"\b(?:bandit|pip[-_]audit)\b[^\n]*\|\|\s*true",
        re.IGNORECASE,
    )
    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        if scanner_bypass.search(text):
            failures.append(
                f"scanner failure is suppressed in {workflow.relative_to(root)}"
            )
        if re.search(r"^\s*continue-on-error:\s*true\s*$", text, re.MULTILINE):
            failures.append(
                f"workflow contains continue-on-error: {workflow.relative_to(root)}"
            )

        for action in re.findall(r"^\s*uses:\s*([^\s#]+)", text, re.MULTILINE):
            if action.startswith("./"):
                continue
            if not re.fullmatch(r"[^@]+@[0-9a-f]{40}", action):
                failures.append(
                    f"action is not pinned to a full commit SHA in "
                    f"{workflow.relative_to(root)}: {action}"
                )

    if len(
        re.findall(
            r"^\s*bandit\s+-r\s+src/\s+http_server\.py\b",
            security_text,
            re.MULTILINE,
        )
    ) != 1:
        failures.append(
            "security workflow must contain exactly one Bandit scan covering "
            "src/ and http_server.py"
        )
    for needle in (
        "bandit-report.json",
        "if-no-files-found: error",
        "'bandit[toml]==1.9.4'",
        "scan_status=$?",
        "scripts/verify_python_sast_report.py",
        '--scan-exit-code "$scan_status"',
        "'pip-audit==2.10.1'",
        "python -m pip_audit",
        "--strict",
        "scripts/verify_python_dependency_audit.py",
        "pip-audit-report.json",
    ):
        if needle not in security_text:
            failures.append(f"security workflow is missing {needle!r}")
    if "--ignore-vuln" in security_text:
        failures.append("dependency audit contains an ungoverned vulnerability ignore")

    if re.search(r"^  security-scan:\s*$", test_text, re.MULTILINE):
        failures.append("test workflow duplicates the security scanner job")
    if re.search(r"\bsafety\b", security_text + test_text, re.IGNORECASE):
        failures.append("deprecated Safety scanner remains in an active workflow")
    first, second = (root / path for path in SECURITY_COPIES)
    if not first.is_file() or not second.is_file():
        failures.append("both canonical security-policy copies must exist")
    elif first.read_bytes() != second.read_bytes():
        failures.append("canonical security-policy copies are not byte-identical")
    else:
        policy = first.read_text(encoding="utf-8")
        forbidden_claims = (
            "No known unpatched vulnerabilities",
            "Branch protection rules enforce pull request reviews",
            "**Safety**",
        )
        for claim in forbidden_claims:
            if claim in policy:
                failures.append(f"security policy retains stale claim: {claim}")
        for truth in (
            "A public draft pull request is public disclosure",
            "Repository settings—not this document—are",
            "We do not use this file to assert that no unresolved vulnerability exists",
        ):
            if truth not in policy:
                failures.append(f"security policy is missing boundary: {truth}")

    issue_config = root / ".github/ISSUE_TEMPLATE/config.yml"
    if not issue_config.is_file():
        failures.append("issue-template configuration is missing")
    else:
        issue_text = issue_config.read_text(encoding="utf-8")
        if "/security/advisories/new" in issue_text:
            failures.append("issue template points to an unverified private-report form")
        if "/security/policy" not in issue_text:
            failures.append("issue template does not route reporters to SECURITY.md")

    return failures


def main() -> int:
    failures = verify()
    if failures:
        print(f"SECURITY_CI_CONTRACT_FAIL failures={len(failures)}")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("SECURITY_CI_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
