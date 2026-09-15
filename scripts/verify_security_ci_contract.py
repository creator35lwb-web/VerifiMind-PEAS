#!/usr/bin/env python3
"""Verify that public security checks cannot be replaced by pass-through jobs."""

from __future__ import annotations

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
EXPECTED_CHECK_OWNERS = {
    "Bandit SAST Analysis": ".github/workflows/security-scan.yml:bandit-sast",
    "Python Dependency Audit": (
        ".github/workflows/security-scan.yml:python-dependency-audit"
    ),
    "CodeQL Analysis": ".github/workflows/security-scan.yml:codeql-analysis",
    "Public Documentation Contract": (
        ".github/workflows/docs-ci-bypass.yml:public-docs-contract"
    ),
}
REQUIRED_SECURITY_MARKERS = (
    "bandit-report.json",
    "if-no-files-found: error",
    "'bandit[toml]==1.9.4'",
    "rm -f ../bandit-report.json",
    "scan_status=$?",
    "'pip-audit==2.10.1'",
    "python -m pip_audit",
    "--strict",
    "rm -f pip-audit-report.json",
    "pip-audit-report.json",
)
REQUIRED_SECURITY_LINES = (
    'python scripts/verify_python_sast_report.py --scan-exit-code "$scan_status"',
    'python scripts/verify_python_dependency_audit.py --audit-exit-code "$audit_status"',
)
FORBIDDEN_POLICY_CLAIMS = (
    "No known unpatched vulnerabilities",
    "Branch protection rules enforce pull request reviews",
    "**Safety**",
)
REQUIRED_POLICY_BOUNDARIES = (
    "A public draft pull request is public disclosure",
    "Repository settings—not this document—are",
    "We do not use this file to assert that no unresolved vulnerability exists",
)
JOB_ID_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
)
LOWER_HEX_CHARACTERS = frozenset("0123456789abcdef")


def _indented_mapping_key(line: str, indentation: int) -> str | None:
    """Return a plain YAML mapping key at exactly ``indentation`` spaces."""
    prefix = " " * indentation
    if not line.startswith(prefix) or line.startswith(prefix + " "):
        return None
    key, separator, remainder = line[indentation:].partition(":")
    if not separator or not key or any(char not in JOB_ID_CHARACTERS for char in key):
        return None
    trailing = remainder.strip()
    if trailing and not trailing.startswith("#"):
        return None
    return key


def _indented_scalar(line: str, indentation: int, key: str) -> str | None:
    prefix = f"{' ' * indentation}{key}:"
    if not line.startswith(prefix):
        return None
    value = line[len(prefix) :].strip()
    if not value:
        return None
    return value.strip("'\"")


def _finish_job(
    pairs: list[tuple[str, str]],
    job_id: str | None,
    check_name: str | None,
) -> None:
    if job_id is not None:
        pairs.append((check_name or job_id, job_id))


def _parse_job_section(lines: list[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    current_job: str | None = None
    current_name: str | None = None

    for line in lines:
        if line and not line.startswith(" "):
            break

        job_id = _indented_mapping_key(line, 2)
        if job_id is not None:
            _finish_job(pairs, current_job, current_name)
            current_job = job_id
            current_name = None
            continue

        check_name = _indented_scalar(line, 4, "name")
        if current_job is not None and check_name is not None:
            current_name = check_name

    _finish_job(pairs, current_job, current_name)
    return pairs


def job_check_names(workflow: Path) -> list[tuple[str, str]]:
    """Return (rendered check name, job id) pairs from a simple workflow."""
    lines = workflow.read_text(encoding="utf-8").splitlines()
    try:
        jobs_start = lines.index("jobs:") + 1
    except ValueError:
        return []
    return _parse_job_section(lines[jobs_start:])


def event_block(workflow_text: str, event: str) -> str | None:
    lines = workflow_text.splitlines()
    event_header = f"  {event}:"
    try:
        start = lines.index(event_header)
    except ValueError:
        return None

    block = [event_header]
    for line in lines[start + 1 :]:
        if _indented_mapping_key(line, 2) is not None:
            break
        if line and not line.startswith(" "):
            break
        block.append(line)
    return "\n".join(block)


def _discover_workflows(root: Path) -> list[Path]:
    workflow_root = root / WORKFLOW_DIR
    return sorted(workflow_root.glob("*.yml")) + sorted(
        workflow_root.glob("*.yaml")
    )


def _collect_check_owners(
    root: Path,
    workflows: list[Path],
) -> dict[str, list[str]]:
    owners: dict[str, list[str]] = defaultdict(list)
    for workflow in workflows:
        relative = workflow.relative_to(root).as_posix()
        for check_name, job_id in job_check_names(workflow):
            owners[check_name].append(f"{relative}:{job_id}")
    return owners


def _verify_check_ownership(owners: dict[str, list[str]]) -> list[str]:
    failures = []
    for check_name, producers in sorted(owners.items()):
        if len(producers) != 1:
            failures.append(
                f"check name {check_name!r} has {len(producers)} producers: {producers}"
            )
    for check_name, producer in EXPECTED_CHECK_OWNERS.items():
        if owners.get(check_name) != [producer]:
            failures.append(f"check {check_name!r} must be owned only by {producer}")
    return failures


def _required_workflow_paths(root: Path) -> tuple[Path, Path, Path]:
    return (
        root / SECURITY_WORKFLOW,
        root / DOCS_WORKFLOW,
        root / TEST_WORKFLOW,
    )


def _missing_workflow_failures(paths: tuple[Path, Path, Path], root: Path) -> list[str]:
    return [
        f"required workflow is missing: {path.relative_to(root)}"
        for path in paths
        if not path.is_file()
    ]


def _block_has_key(block: str, keys: frozenset[str]) -> bool:
    for line in block.splitlines():
        key = line.strip().partition(":")[0]
        if key in keys:
            return True
    return False


def _verify_trigger_contract(security_text: str) -> list[str]:
    failures = []
    path_keys = frozenset(("paths", "paths-ignore"))
    for event in ("push", "pull_request"):
        block = event_block(security_text, event)
        if block is None:
            failures.append(f"security workflow does not run on {event}")
        elif _block_has_key(block, path_keys):
            failures.append(f"security workflow {event} trigger is path-scoped")
    return failures


def _contains_scanner_bypass(text: str) -> bool:
    for line in text.splitlines():
        normalized = line.casefold().replace("_", "-")
        scanner_present = "bandit" in normalized or "pip-audit" in normalized
        bypass = normalized.partition("||")[2].strip()
        if scanner_present and bypass.startswith("true"):
            return True
    return False


def _contains_continue_on_error(text: str) -> bool:
    return any(
        line.strip().casefold() == "continue-on-error: true"
        for line in text.splitlines()
    )


def _workflow_actions(text: str) -> list[str]:
    actions = []
    for line in text.splitlines():
        candidate = line.strip()
        if candidate.startswith("- "):
            candidate = candidate[2:].lstrip()
        if not candidate.startswith("uses:"):
            continue
        action = candidate.removeprefix("uses:").partition("#")[0].strip()
        actions.append(action.strip("'\""))
    return actions


def _is_pinned_action(action: str) -> bool:
    if action.startswith("./"):
        return True
    location, separator, revision = action.rpartition("@")
    return bool(
        separator
        and location
        and "@" not in location
        and len(revision) == 40
        and all(char in LOWER_HEX_CHARACTERS for char in revision)
    )


def _verify_workflow_hygiene(root: Path, workflows: list[Path]) -> list[str]:
    failures = []
    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        relative = workflow.relative_to(root)
        if _contains_scanner_bypass(text):
            failures.append(f"scanner failure is suppressed in {relative}")
        if _contains_continue_on_error(text):
            failures.append(f"workflow contains continue-on-error: {relative}")
        for action in _workflow_actions(text):
            if not _is_pinned_action(action):
                failures.append(
                    f"action is not pinned to a full commit SHA in {relative}: {action}"
                )
    return failures


def _is_required_bandit_scan(line: str) -> bool:
    tokens = line.strip().split()
    return len(tokens) >= 4 and tokens[:4] == [
        "bandit",
        "-r",
        "src/",
        "http_server.py",
    ]


def _contains_word(text: str, expected: str) -> bool:
    words = "".join(
        character if character.isalnum() or character == "_" else " "
        for character in text
    ).split()
    return any(word.casefold() == expected.casefold() for word in words)


def _verify_required_security_content(security_text: str) -> list[str]:
    failures = []
    for marker in REQUIRED_SECURITY_MARKERS:
        if marker not in security_text:
            failures.append(f"security workflow is missing {marker!r}")

    normalized_lines = {line.strip() for line in security_text.splitlines()}
    for command in REQUIRED_SECURITY_LINES:
        if command not in normalized_lines:
            failures.append(
                f"security workflow is missing exact verifier command {command!r}"
            )

    if "--ignore-vuln" in security_text:
        failures.append("dependency audit contains an ungoverned vulnerability ignore")
    return failures


def _verify_security_workflow(
    security_text: str,
    docs_text: str,
    test_path: Path,
) -> list[str]:
    failures = []
    if "run: python scripts/verify_security_ci_contract.py" not in security_text:
        failures.append("always-on Bandit job does not execute the security CI contract")
    if "      - '.github/workflows/**'" not in docs_text:
        failures.append("documentation contract does not cover every workflow-file change")

    bandit_scan_count = sum(
        _is_required_bandit_scan(line) for line in security_text.splitlines()
    )
    if bandit_scan_count != 1:
        failures.append(
            "security workflow must contain exactly one Bandit scan covering "
            "src/ and http_server.py"
        )
    failures.extend(_verify_required_security_content(security_text))

    test_job_ids = {job_id for _, job_id in job_check_names(test_path)}
    if "security-scan" in test_job_ids:
        failures.append("test workflow duplicates the security scanner job")
    if _contains_word(security_text + test_path.read_text(encoding="utf-8"), "safety"):
        failures.append("deprecated Safety scanner remains in an active workflow")
    return failures


def _verify_security_policy(root: Path) -> list[str]:
    failures = []
    first, second = (root / path for path in SECURITY_COPIES)
    if not first.is_file() or not second.is_file():
        return ["both canonical security-policy copies must exist"]
    if first.read_bytes() != second.read_bytes():
        return ["canonical security-policy copies are not byte-identical"]

    policy = first.read_text(encoding="utf-8")
    for claim in FORBIDDEN_POLICY_CLAIMS:
        if claim in policy:
            failures.append(f"security policy retains stale claim: {claim}")
    for boundary in REQUIRED_POLICY_BOUNDARIES:
        if boundary not in policy:
            failures.append(f"security policy is missing boundary: {boundary}")
    return failures


def _verify_issue_config(root: Path) -> list[str]:
    issue_config = root / ".github/ISSUE_TEMPLATE/config.yml"
    if not issue_config.is_file():
        return ["issue-template configuration is missing"]

    failures = []
    issue_text = issue_config.read_text(encoding="utf-8")
    if "/security/advisories/new" in issue_text:
        failures.append("issue template points to an unverified private-report form")
    if "/security/policy" not in issue_text:
        failures.append("issue template does not route reporters to SECURITY.md")
    return failures


def verify(root: Path = ROOT) -> list[str]:
    workflows = _discover_workflows(root)
    if not workflows:
        return ["no GitHub Actions workflows found"]

    owners = _collect_check_owners(root, workflows)
    failures = _verify_check_ownership(owners)
    security_path, docs_path, test_path = _required_workflow_paths(root)
    missing = _missing_workflow_failures(
        (security_path, docs_path, test_path),
        root,
    )
    failures.extend(missing)
    if missing:
        return failures

    security_text = security_path.read_text(encoding="utf-8")
    docs_text = docs_path.read_text(encoding="utf-8")
    failures.extend(_verify_trigger_contract(security_text))
    failures.extend(_verify_workflow_hygiene(root, workflows))
    failures.extend(_verify_security_workflow(security_text, docs_text, test_path))
    failures.extend(_verify_security_policy(root))
    failures.extend(_verify_issue_config(root))
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
