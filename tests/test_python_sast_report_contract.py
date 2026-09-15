from __future__ import annotations

import sys
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_python_sast_report import validate_report  # noqa: E402


def clean_report() -> dict:
    return {
        "errors": [],
        "results": [],
        "metrics": {
            "_totals": {"loc": 30},
            ".\\http_server.py": {"loc": 10},
            "src\\verifimind_mcp\\server.py": {"loc": 20},
        },
    }


class PythonSASTReportContractTests(unittest.TestCase):
    def test_clean_nonvacuous_report_passes(self) -> None:
        self.assertEqual(validate_report(clean_report(), 0), [])

    def test_bandit_scan_error_fails_even_with_success_exit(self) -> None:
        report = clean_report()
        report["errors"] = [
            {"filename": "missing.py", "reason": "No such file or directory"}
        ]
        failures = validate_report(report, 0)
        self.assertTrue(any("scan/input error" in item for item in failures))

    def test_missing_http_entrypoint_metric_fails(self) -> None:
        report = clean_report()
        del report["metrics"][".\\http_server.py"]
        failures = validate_report(report, 0)
        self.assertTrue(any("http_server.py" in item for item in failures))

    def test_missing_src_tree_metric_fails(self) -> None:
        report = clean_report()
        del report["metrics"]["src\\verifimind_mcp\\server.py"]
        failures = validate_report(report, 0)
        self.assertTrue(any("src/ tree" in item for item in failures))

    def test_zero_total_is_rejected_as_vacuous(self) -> None:
        report = clean_report()
        report["metrics"]["_totals"]["loc"] = 0
        failures = validate_report(report, 0)
        self.assertTrue(any("positive _totals.loc" in item for item in failures))

    def test_findings_fail_even_with_success_exit(self) -> None:
        report = clean_report()
        report["results"] = [{"test_id": "B999"}]
        failures = validate_report(report, 0)
        self.assertTrue(any("security finding" in item for item in failures))
        self.assertTrue(any("returned success" in item for item in failures))

    def test_nonzero_exit_fails_even_with_clean_report(self) -> None:
        failures = validate_report(deepcopy(clean_report()), 2)
        self.assertTrue(any("non-success code 2" in item for item in failures))

    def test_non_object_report_fails(self) -> None:
        failures = validate_report([], 0)
        self.assertIn("report root must be a JSON object", failures)


if __name__ == "__main__":
    unittest.main()
