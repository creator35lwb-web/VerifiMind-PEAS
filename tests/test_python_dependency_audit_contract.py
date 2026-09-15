from __future__ import annotations

import sys
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_python_dependency_audit import (  # noqa: E402
    EXPECTED_REPORT_NAME,
    REPORT_PATH,
    main,
    validate_report,
)


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

    def test_report_path_is_fixed_to_repository_root(self) -> None:
        self.assertTrue(REPORT_PATH.is_absolute())
        self.assertEqual(REPORT_PATH, ROOT / EXPECTED_REPORT_NAME)

    def test_cli_rejects_former_positional_report_argument(self) -> None:
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit) as ctx:
            main([EXPECTED_REPORT_NAME, "--audit-exit-code", "0"])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
