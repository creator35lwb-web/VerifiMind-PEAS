from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from security_receipt import load_json_receipt  # noqa: E402


class SecurityReceiptTests(unittest.TestCase):
    def test_relative_report_path_is_rejected(self) -> None:
        data, failures = load_json_receipt(Path("report.json"))
        self.assertIsNone(data)
        self.assertTrue(any("must be absolute" in item for item in failures))

    def test_report_loading_is_independent_of_current_directory(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            report_path = temporary_root / "repository" / "report.json"
            alternate_cwd = temporary_root / "elsewhere"
            report_path.parent.mkdir()
            alternate_cwd.mkdir()
            expected = {"receipt": "clean"}
            report_path.write_text(json.dumps(expected), encoding="utf-8")
            original_cwd = Path.cwd()
            try:
                os.chdir(alternate_cwd)
                data, failures = load_json_receipt(report_path)
            finally:
                os.chdir(original_cwd)
            self.assertEqual(failures, [])
            self.assertEqual(data, expected)

    def test_symbolic_link_report_is_rejected_when_supported(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            target = temporary_root / "outside.json"
            link = temporary_root / "report.json"
            target.write_text("{}", encoding="utf-8")
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symbolic links are unavailable: {exc}")

            data, failures = load_json_receipt(link)
            self.assertIsNone(data)
            self.assertTrue(any("symbolic link" in item for item in failures))

    def test_non_regular_report_is_rejected(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            report_directory = Path(temporary_directory) / "report.json"
            report_directory.mkdir()
            data, failures = load_json_receipt(report_directory)
            self.assertIsNone(data)
            self.assertTrue(any("not a regular file" in item for item in failures))


if __name__ == "__main__":
    unittest.main()
