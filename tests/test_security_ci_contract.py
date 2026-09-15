from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_security_ci_contract import verify  # noqa: E402


class SecurityCIContractTests(unittest.TestCase):
    def make_fixture(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shutil.copytree(ROOT / ".github", root / ".github")
        shutil.copytree(ROOT / ".macp-public", root / ".macp-public")
        shutil.copytree(ROOT / "scripts", root / "scripts")
        shutil.copy2(ROOT / "SECURITY.md", root / "SECURITY.md")
        return root

    def replace_in_fixture(
        self,
        root: Path,
        relative_path: str,
        old: str,
        new: str,
    ) -> None:
        path = root / relative_path
        original = path.read_text(encoding="utf-8")
        self.assertIn(old, original)
        path.write_text(original.replace(old, new, 1), encoding="utf-8")

    def assert_contract_failure(self, root: Path, expected: str) -> None:
        failures = verify(root)
        self.assertTrue(
            any(expected in item for item in failures),
            f"expected {expected!r} in {failures!r}",
        )

    def test_repository_contract_passes(self) -> None:
        self.assertEqual(verify(ROOT), [])

    def test_duplicate_required_check_is_rejected(self) -> None:
        root = self.make_fixture()
        self.replace_in_fixture(
            root,
            ".github/workflows/docs-ci-bypass.yml",
            "name: Public Documentation Contract\n    runs-on:",
            "name: Bandit SAST Analysis\n    runs-on:",
        )
        self.assert_contract_failure(root, "has 2 producers")

    def test_scanner_passthrough_is_rejected(self) -> None:
        root = self.make_fixture()
        self.replace_in_fixture(
            root,
            ".github/workflows/security-scan.yml",
            "-o ../bandit-report.json",
            "-o ../bandit-report.json || true",
        )
        self.assert_contract_failure(root, "scanner failure is suppressed")

    def test_pip_audit_passthrough_with_underscore_is_rejected(self) -> None:
        root = self.make_fixture()
        self.replace_in_fixture(
            root,
            ".github/workflows/security-scan.yml",
            "python -m pip_audit \\",
            "python -m pip_audit || true # forbidden bypass\n          # \\",
        )
        self.assert_contract_failure(root, "scanner failure is suppressed")

    def test_bandit_scope_cannot_omit_http_entrypoint(self) -> None:
        root = self.make_fixture()
        self.replace_in_fixture(
            root,
            ".github/workflows/security-scan.yml",
            "bandit -r src/ http_server.py",
            "bandit -r src/",
        )
        self.assert_contract_failure(root, "covering src/ and http_server.py")

    def test_verifiers_cannot_restore_caller_supplied_report_paths(self) -> None:
        mutations = (
            (
                'python scripts/verify_python_sast_report.py --scan-exit-code "$scan_status"',
                'python scripts/verify_python_sast_report.py bandit-report.json '
                '--scan-exit-code "$scan_status"',
            ),
            (
                'python scripts/verify_python_dependency_audit.py '
                '--audit-exit-code "$audit_status"',
                'python scripts/verify_python_dependency_audit.py '
                'pip-audit-report.json --audit-exit-code "$audit_status"',
            ),
        )
        for exact_command, caller_path_command in mutations:
            with self.subTest(command=exact_command):
                root = self.make_fixture()
                self.replace_in_fixture(
                    root,
                    ".github/workflows/security-scan.yml",
                    exact_command,
                    caller_path_command,
                )
                self.assert_contract_failure(root, "missing exact verifier command")

    def test_always_on_bandit_job_must_run_ci_contract(self) -> None:
        root = self.make_fixture()
        self.replace_in_fixture(
            root,
            ".github/workflows/security-scan.yml",
            "      - name: Verify security CI contract\n"
            "        run: python scripts/verify_security_ci_contract.py\n\n",
            "",
        )
        self.assert_contract_failure(root, "does not execute")

    def test_docs_contract_must_cover_every_workflow_file(self) -> None:
        root = self.make_fixture()
        self.replace_in_fixture(
            root,
            ".github/workflows/docs-ci-bypass.yml",
            "      - '.github/workflows/**'",
            "      - '.github/workflows/security-scan.yml'",
        )
        self.assert_contract_failure(root, "every workflow-file change")

    def test_path_scoped_security_trigger_is_rejected(self) -> None:
        root = self.make_fixture()
        self.replace_in_fixture(
            root,
            ".github/workflows/security-scan.yml",
            "  pull_request:\n    branches: [main]",
            "  pull_request:\n    branches: [main]\n    paths-ignore:\n      - 'docs/**'",
        )
        self.assert_contract_failure(root, "pull_request trigger is path-scoped")

    def test_policy_drift_is_rejected(self) -> None:
        root = self.make_fixture()
        duplicate = root / ".macp-public/governance/SECURITY.md"
        duplicate.write_text(
            duplicate.read_text(encoding="utf-8") + "\nDrift.\n",
            encoding="utf-8",
        )
        failures = verify(root)
        self.assertIn(
            "canonical security-policy copies are not byte-identical",
            failures,
        )

    def test_unpinned_action_is_rejected(self) -> None:
        root = self.make_fixture()
        self.replace_in_fixture(
            root,
            ".github/workflows/security-scan.yml",
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "actions/checkout@v7",
        )
        self.assert_contract_failure(root, "not pinned")

    def test_unpinned_shorthand_action_is_rejected(self) -> None:
        root = self.make_fixture()
        self.replace_in_fixture(
            root,
            ".github/workflows/test.yml",
            "- uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
            "- uses: actions/checkout@v7",
        )
        self.assert_contract_failure(root, "not pinned")

    def test_continue_on_error_is_rejected(self) -> None:
        root = self.make_fixture()
        self.replace_in_fixture(
            root,
            ".github/workflows/security-scan.yml",
            "    runs-on: ubuntu-latest",
            "    runs-on: ubuntu-latest\n    continue-on-error: true",
        )
        self.assert_contract_failure(root, "continue-on-error")

    def test_test_workflow_cannot_restore_security_scanner_job(self) -> None:
        root = self.make_fixture()
        self.replace_in_fixture(
            root,
            ".github/workflows/test.yml",
            "  health-check:\n    name: Server Health Check",
            "  security-scan:\n    name: Server Health Check",
        )
        self.assert_contract_failure(root, "duplicates the security scanner job")

    def test_missing_required_workflow_is_reported_without_crashing(self) -> None:
        root = self.make_fixture()
        (root / ".github/workflows/test.yml").unlink()
        self.assert_contract_failure(root, "required workflow is missing")


if __name__ == "__main__":
    unittest.main()
