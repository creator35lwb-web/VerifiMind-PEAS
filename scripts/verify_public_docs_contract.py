#!/usr/bin/env python3
"""Fail closed when current public documentation contradicts its authority map."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
failures: list[str] = []
checks = 0


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(relative: str, needle: str, label: str) -> None:
    global checks
    checks += 1
    if needle not in text(relative):
        failures.append(f"{relative}: missing {label}")


def forbid(relative: str, pattern: str, label: str) -> None:
    global checks
    checks += 1
    if re.search(pattern, text(relative), flags=re.IGNORECASE | re.MULTILINE):
        failures.append(f"{relative}: contains stale/unsafe {label}")


# Concise public front door and release-bound truth.
require("README.md", "version-v0.5.58", "v0.5.58 badge")
require("README.md", "13 defined / 8 active / 5 temporarily unavailable", "availability taxonomy")
require("README.md", "21345820", "MACP v2.5 version DOI")
require("README.md", "Multi-Agent Communication Protocol (MACP) v2.5 — Loop Engineering", "MACP v2.5 title")
require("README.md", "version   = {2.5.0}", "MACP v2.5 record version")
require("README.md", "/wiki", "Wiki textbook/playbook link")
forbid("README.md", r"v0\.6\.0--Beta|v0\.6\.0-Beta", "Beta-as-current marker")
forbid("README.md", r"creator35lwb-web/verifimind-genesis-mcp", "private Hub link")
forbid("README.md", r"\*\*Providers:\*\*\s*7\b", "conflated remote/local provider count")

changelog_match = re.search(
    r"^## v0\.5\.58\b.*?(?=^---\s*$|^## v0\.)",
    text("CHANGELOG.md"),
    flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
changelog_current = changelog_match.group(0) if changelog_match else ""
checks += 4
if "v0.5.58" not in changelog_current:
    failures.append("CHANGELOG.md: current section is not v0.5.58")
if re.search(r"candidate|not merged|not deployed", changelog_current, re.IGNORECASE):
    failures.append("CHANGELOG.md: v0.5.58 still described as a candidate")
if "3019f5c4889d8334063d4a2d9243e87d96fc93a8" not in changelog_current:
    failures.append("CHANGELOG.md: exact v0.5.58 merge is absent")
if "be6ed621-c0b8-49a3-a9f3-7ba36e68c7ea" not in changelog_current:
    failures.append("CHANGELOG.md: exact v0.5.58 build is absent")

require("SERVER_STATUS.md", "| Application | **v0.5.58**", "current production version")
require("SERVER_STATUS.md", "31 pass / 0 stop / 0 instrument", "post-deploy smoke")
require("SERVER_STATUS.md", "Serving revision", "serving-revision provenance field")
require("MCP_SERVER_FEATURES.md", "MCP 2025-11-25", "current MCP protocol")
forbid("MCP_SERVER_FEATURES.md", r"Gemini 2\.5 Flash|2025-03-26|\bxAI\b", "stale runtime/catalogue claim")

# The public command delegates; it must never grow a second cloud recipe.
require(".claude/commands/verifimind-deploy.md", "mcp-server/deploy-cloudrun.sh", "canonical recovery carrier")
forbid(".claude/commands/verifimind-deploy.md", r"^\s*gcloud\s+(?:builds\s+submit|run\s+deploy)\b", "standalone deployment recipe")
forbid(".claude/commands/verifimind-deploy.md", r"git add -A", "indiscriminate staging")
require(".github/workflows/docs-ci-bypass.yml", "python scripts/verify_public_docs_contract.py", "docs CI contract execution")
require(".github/workflows/docs-ci-bypass.yml", "- 'wiki/**'", "Wiki-source CI path")

require("ROADMAP.md", "Evaluation Roadmap v1.0", "tagged roadmap authority")
forbid("ROADMAP.md", r"Current-v0\.4\.5|v0\.4\.5 BYOK Live \(Current Release\)", "March 2026 current-state claim")

# Canonical Wiki source and explicit publication manifest.
manifest = json.loads((WIKI / "manifest.json").read_text(encoding="utf-8"))
pages = manifest.get("pages")
checks += 1
if not isinstance(pages, list) or not pages or any(not isinstance(item, str) for item in pages):
    failures.append("wiki/manifest.json: pages must be a non-empty string list")
    pages = []

manifest_pages = set(pages)
source_pages = {path.name for path in WIKI.glob("*.md") if path.name != "README.md"}
checks += 3
if len(pages) != len(manifest_pages):
    failures.append("wiki/manifest.json: duplicate page entries")
if manifest_pages != source_pages:
    missing = sorted(source_pages - manifest_pages)
    extra = sorted(manifest_pages - source_pages)
    failures.append(f"wiki/manifest.json: source mismatch missing={missing} extra={extra}")
if "README.md" in manifest_pages:
    failures.append("wiki/manifest.json: source-control README must not be published")

for required_page in (
    "Home.md",
    "Current-Production-Status.md",
    "Operations-Playbook.md",
    "Trust-and-Safety.md",
    "Public-Statements.md",
    "Statement-001-Trinity-Integrity.md",
):
    checks += 1
    if required_page not in manifest_pages:
        failures.append(f"wiki/manifest.json: missing required page {required_page}")

current_wiki = [
    page
    for page in manifest_pages
    if page not in {"Public-Statements.md", "Statement-001-Trinity-Integrity.md"}
]
stale_wiki = re.compile(
    r"Gemini 2\.5 Flash|MCP 2025-03-26|server v0\.5\.49|registry v?3\.11\.0|"
    r"(?:3|6) months? free|save_to_history.{0,30}default `?true`?",
    re.IGNORECASE | re.DOTALL,
)
for page in current_wiki:
    checks += 1
    if stale_wiki.search((WIKI / page).read_text(encoding="utf-8")):
        failures.append(f"wiki/{page}: contains a known stale current claim")

# Preserve the already-published trust ledger exactly in this migration.
expected_trust_hashes = {
    page: metadata.get("sha256Lf")
    for page, metadata in manifest.get("protectedPages", {}).items()
    if isinstance(metadata, dict)
}
checks += 2
if set(expected_trust_hashes) != {
    "Public-Statements.md",
    "Statement-001-Trinity-Integrity.md",
}:
    failures.append("wiki/manifest.json: protected trust-ledger set is incomplete")
if manifest.get("sourceWikiHead") != "774620481d13b123d9882af24aeacba3fdf8ae9a":
    failures.append("wiki/manifest.json: source Wiki head is not pinned")
for page, expected in expected_trust_hashes.items():
    checks += 1
    canonical_bytes = (WIKI / page).read_bytes().replace(b"\r\n", b"\n")
    actual = hashlib.sha256(canonical_bytes).hexdigest()
    if actual != expected:
        failures.append(f"wiki/{page}: trust-ledger content changed during migration")

# Validate local Wiki links without requesting the network.
markdown_link = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
for page in sorted(source_pages):
    body = (WIKI / page).read_text(encoding="utf-8")
    for raw_target in markdown_link.findall(body):
        target = unquote(raw_target.strip().split()[0].strip("<>"))
        # Skip in-page anchors and anything carrying a URI scheme. Testing for
        # "://" rather than listing http/https also skips ftp:, data: and other
        # schemes, which the previous tuple let fall through to local-path
        # resolution and report as a spurious missing file.
        if not target or target.startswith(("#", "mailto:")) or "://" in target:
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        checks += 1
        if target.endswith(".md") or "/" in target:
            candidate = (WIKI / page).parent / target
        else:
            candidate = WIKI / f"{target}.md"
        if not candidate.exists():
            failures.append(f"wiki/{page}: broken local link {raw_target}")

if failures:
    print(f"PUBLIC_DOCS_CONTRACT_FAIL checks={checks} failures={len(failures)}")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print(
    "PUBLIC_DOCS_CONTRACT_PASS "
    f"checks={checks} publishable_wiki_pages={len(manifest_pages)}"
)
