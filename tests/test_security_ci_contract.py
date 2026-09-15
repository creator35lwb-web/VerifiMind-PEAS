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
    def make_fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        shutil.copytree(ROOT / ".github", root / ".github")
        shutil.copytree(ROOT / ".macp-public", root / ".macp-public")
        shutil.copytree(ROOT / "scripts", root / "scripts")
        shutil.copy2(ROOT / "SECURITY.md", root / "SECURITY.md")
        return temporary, root

    def test_repository_contract_passes(self) -> None:
        self.assertEqual(verify(ROOT), [])

    def test_duplicate_required_check_is_rejected(self) -> None:
        temporary, root = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        docs = root / ".github/workflows/docs-ci-bypass.yml"
        docs.write_text(
            docs.read_text(encoding="utf-8").replace(
                "name: Public Documentation Contract\n    runs-on:",
                "name: Bandit SAST Analysis\n    runs-on:",
            ),
            encoding="utf-8",
        )
        failures = verify(root)
        self.assertTrue(any("has 2 producers" in item for item in failures))

    def test_scanner_passthrough_is_rejected(self) -> None:
        temporary, root = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        workflow = root / ".github/workflows/security-scan.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "-o ../bandit-report.json",
                "-o ../bandit-report.json || true",
            ),
            encoding="utf-8",
        )
        failures = verify(root)
        self.assertTrue(any("scanner failure is suppressed" in item for item in failures))

    def test_bandit_scope_cannot_omit_http_entrypoint(self) -> None:
        temporary, root = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        workflow = root / ".github/workflows/security-scan.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "bandit -r src/ http_server.py",
                "bandit -r src/",
            ),
            encoding="utf-8",
        )
        failures = verify(root)
        self.assertTrue(
            any("covering src/ and http_server.py" in item for item in failures)
        )

    def test_always_on_bandit_job_must_run_ci_contract(self) -> None:
        temporary, root = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        workflow = root / ".github/workflows/security-scan.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "      - name: Verify security CI contract\n"
                "        run: python scripts/verify_security_ci_contract.py\n\n",
                "",
            ),
            encoding="utf-8",
        )
        failures = verify(root)
        self.assertTrue(any("does not execute" in item for item in failures))

    def test_docs_contract_must_cover_every_workflow_file(self) -> None:
        temporary, root = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        workflow = root / ".github/workflows/docs-ci-bypass.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "      - '.github/workflows/**'",
                "      - '.github/workflows/security-scan.yml'",
            ),
            encoding="utf-8",
        )
        failures = verify(root)
        self.assertTrue(any("every workflow-file change" in item for item in failures))

    def test_policy_drift_is_rejected(self) -> None:
        temporary, root = self.make_fixture()
        self.addCleanup(temporary.cleanup)
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
        temporary, root = self.make_fixture()
        self.addCleanup(temporary.cleanup)
        workflow = root / ".github/workflows/security-scan.yml"
        workflow.write_text(
            workflow.read_text(encoding="utf-8").replace(
                "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
                "actions/checkout@v7",
                1,
            ),
            encoding="utf-8",
        )
        failures = verify(root)
        self.assertTrue(any("not pinned" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
