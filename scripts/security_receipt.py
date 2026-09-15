"""Shared fail-closed loading for repository-owned security receipts."""

from __future__ import annotations

import argparse
import json
import stat
from collections.abc import Callable
from pathlib import Path
from typing import Any


ReceiptValidator = Callable[[Any, int], list[str]]
PassSummary = Callable[[Any, int], str]


def _path_failure(path: Path) -> str | None:
    if not path.is_absolute():
        return f"report path must be absolute: {path}"
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return f"report is missing: {path}"
    except OSError as exc:
        return f"report path cannot be inspected: {exc}"

    if stat.S_ISLNK(metadata.st_mode):
        return f"report must not be a symbolic link: {path}"
    if not stat.S_ISREG(metadata.st_mode):
        return f"report is not a regular file: {path}"
    return None


def load_json_receipt(path: Path) -> tuple[Any | None, list[str]]:
    """Load a regular, non-symlink JSON receipt from a trusted fixed path."""
    path_failure = _path_failure(path)
    if path_failure:
        return None, [path_failure]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [f"report is not valid UTF-8 JSON: {exc}"]


def _parse_exit_code(
    argv: list[str] | None, exit_code_option: str
) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        exit_code_option,
        dest="tool_exit_code",
        required=True,
        type=int,
    )
    return parser.parse_args(argv).tool_exit_code


def run_receipt_verifier(
    argv: list[str] | None,
    *,
    exit_code_option: str,
    report_path: Path,
    validator: ReceiptValidator,
    failure_prefix: str,
    exit_label: str,
    pass_summary: PassSummary,
) -> int:
    """Run common fixed-path receipt verification and emit one stable result."""
    tool_exit_code = _parse_exit_code(argv, exit_code_option)
    data, failures = load_json_receipt(report_path)
    if not failures:
        failures.extend(validator(data, tool_exit_code))

    if failures:
        print(
            f"{failure_prefix}_FAIL failures={len(failures)} "
            f"{exit_label}={tool_exit_code}"
        )
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(pass_summary(data, tool_exit_code))
    return 0
