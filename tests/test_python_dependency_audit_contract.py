from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_python_dependency_audit import validate_report  # noqa: E402


class PythonDependencyAuditContractTests(unittest.TestCase):
    def test_clean_nonempty_report_passes(self) -> None:
        report = {
            "dependencies": [
                {"name": "example", "version": "1.0", "vulns": []}
            ],
            "fixes": [],
        }
        self.assertEqual(validate_report(report, 0), [])

    def test_empty_report_fails_non_vacuously(self) -> None:
        failures = validate_report({"dependencies": [], "fixes": []}, 0)
        self.assertIn("report contains zero audited dependencies", failures)

    def test_legacy_top_level_list_is_rejected(self) -> None:
        report = [{"name": "example", "version": "1.0", "vulns": []}]
        failures = validate_report(report, 0)
        self.assertIn("report root must be a JSON object", failures)

    def test_vulnerability_report_fails(self) -> None:
        report = {
            "dependencies": [
                {
                    "name": "example",
                    "version": "1.0",
                    "vulns": [{"id": "TEST-1", "fix_versions": ["1.1"]}],
                }
            ],
            "fixes": [],
        }
        failures = validate_report(report, 1)
        self.assertTrue(any("known vulnerability" in item for item in failures))

    def test_success_exit_cannot_hide_findings(self) -> None:
        report = {
            "dependencies": [
                {
                    "name": "example",
                    "version": "1.0",
                    "vulns": [{"id": "TEST-1", "fix_versions": []}],
                }
            ],
            "fixes": [],
        }
        failures = validate_report(report, 0)
        self.assertTrue(any("returned success" in item for item in failures))

    def test_tool_error_fails_even_with_clean_report(self) -> None:
        report = {
            "dependencies": [
                {"name": "example", "version": "1.0", "vulns": []}
            ],
            "fixes": [],
        }
        failures = validate_report(report, 2)
        self.assertTrue(any("unexpectedly" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
