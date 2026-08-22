#!/usr/bin/env python3
"""Fail closed when current public documentation contradicts its authority map."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
README_PATH = "README.md"
CHANGELOG_PATH = "CHANGELOG.md"
SERVER_STATUS_PATH = "SERVER_STATUS.md"
DEPLOY_COMMAND_PATH = ".claude/commands/verifimind-deploy.md"
PUBLIC_STATEMENTS_PAGE = "Public-Statements.md"
TRINITY_STATEMENT_PAGE = "Statement-001-Trinity-Integrity.md"
HOME_PAGE = "Home.md"
LINK_SKIP = "skip"
LINK_LOCAL = "local"
LINK_EXTERNAL_URI = "external-uri"
LINK_INSECURE_URI = "insecure-uri"
LINK_MALFORMED_URI = "malformed-uri"
INSECURE_URI_SCHEMES = frozenset(("http", "ftp"))
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


def classify_wiki_link(raw_target: str) -> tuple[str, str]:
    """Classify a Markdown target and return its local path when applicable."""
    stripped_target = raw_target.strip()
    target = unquote(stripped_target.split()[0].strip("<>")) if stripped_target else ""
    if not target or target.startswith("#"):
        return LINK_SKIP, ""

    try:
        parsed = urlsplit(target)
    except ValueError:
        return LINK_MALFORMED_URI, ""

    scheme = parsed.scheme.casefold()
    if scheme in INSECURE_URI_SCHEMES:
        return LINK_INSECURE_URI, ""
    if scheme or parsed.netloc:
        return LINK_EXTERNAL_URI, ""
    return LINK_LOCAL, parsed.path


def wiki_link_failure(page: str, raw_target: str) -> str | None:
    """Return one deterministic contract failure for a Wiki link, if any."""
    classification, local_target = classify_wiki_link(raw_target)
    if classification in {LINK_SKIP, LINK_EXTERNAL_URI}:
        return None
    if classification == LINK_INSECURE_URI:
        return f"wiki/{page}: insecure URI-scheme link {raw_target}"
    if classification == LINK_MALFORMED_URI:
        return f"wiki/{page}: malformed URI reference {raw_target}"

    if not local_target:
        return None
    if local_target.endswith(".md") or "/" in local_target:
        candidate = (WIKI / page).parent / local_target
    else:
        candidate = WIKI / f"{local_target}.md"
    if not candidate.exists():
        return f"wiki/{page}: broken local link {raw_target}"
    return None


# Concise public front door and release-bound truth.
require(README_PATH, "version-v0.5.62", "v0.5.62 badge")
require(README_PATH, "b434979ea68da0a2326ad3f62dac30888b93dfcd", "exact v0.5.62 merge")
require(README_PATH, "e3ca9551-0292-4b02-9cbf-0cc2b92daa3e", "exact v0.5.62 build")
require(README_PATH, "verifimind-mcp-server-00496-g7s", "exact v0.5.62 serving revision")
require(README_PATH, "X/Z/CS = real/real/real", "v0.5.62 Trinity smoke")
require(README_PATH, "MCP Registry package:** `3.39.0`", "current Registry identity")
require(README_PATH, "13 defined / 8 active / 5 temporarily unavailable", "availability taxonomy")
require(README_PATH, "21345820", "MACP v2.5 version DOI")
require(README_PATH, "Multi-Agent Communication Protocol (MACP) v2.5 — Loop Engineering", "MACP v2.5 title")
require(README_PATH, "version   = {2.5.0}", "MACP v2.5 record version")
require(README_PATH, "/wiki", "Wiki textbook/playbook link")
forbid(README_PATH, r"v0\.6\.0--Beta|v0\.6\.0-Beta", "Beta-as-current marker")
forbid(README_PATH, r"creator35lwb-web/verifimind-genesis-mcp", "private Hub link")
forbid(README_PATH, r"\*\*Providers:\*\*\s*7\b", "conflated remote/local provider count")
forbid(README_PATH, r"ba02fd02|82444203-10d0|MCP Registry package:\*\* `3\.38\.0`", "prior release receipts")
forbid(
    CHANGELOG_PATH,
    r"Deployed truth surfaces:[^\n]*\n\s*remain at v0\.5\.61",
    "v0.5.62 truth surfaces described as pre-deployment",
)

changelog_sections = re.split(
    r"(?=^## v0\.)",
    text(CHANGELOG_PATH),
    flags=re.IGNORECASE | re.MULTILINE,
)
changelog_current = next(
    (
        section
        for section in changelog_sections
        if re.match(r"^## v0\.5\.62\b", section, flags=re.IGNORECASE)
    ),
    "",
)
checks += 5
if "v0.5.62" not in changelog_current:
    failures.append("CHANGELOG.md: current section is not v0.5.62")
if re.search(r"candidate|not merged|not deployed", changelog_current, re.IGNORECASE):
    failures.append("CHANGELOG.md: v0.5.62 still described as a candidate")
if "b434979ea68da0a2326ad3f62dac30888b93dfcd" not in changelog_current:
    failures.append("CHANGELOG.md: exact v0.5.62 merge is absent")
if "e3ca9551-0292-4b02-9cbf-0cc2b92daa3e" not in changelog_current:
    failures.append("CHANGELOG.md: exact v0.5.62 build is absent")
if re.search(r"^## v0\.5\.61\b", changelog_current, flags=re.IGNORECASE | re.MULTILINE):
    failures.append("CHANGELOG.md: current section includes the prior release")

require(SERVER_STATUS_PATH, "| Application | **v0.5.62**", "current production version")
require(SERVER_STATUS_PATH, "X/Z/CS = real/real/real", "post-deploy smoke")
require(SERVER_STATUS_PATH, "Serving revision", "serving-revision provenance field")
require("MCP_SERVER_FEATURES.md", "MCP 2025-11-25", "current MCP protocol")
forbid("MCP_SERVER_FEATURES.md", r"Gemini 2\.5 Flash|2025-03-26|\bxAI\b", "stale runtime/catalogue claim")

# The public command delegates; it must never grow a second cloud recipe.
require(DEPLOY_COMMAND_PATH, "mcp-server/deploy-cloudrun.sh", "canonical recovery carrier")
forbid(DEPLOY_COMMAND_PATH, r"^\s*gcloud\s+(?:builds\s+submit|run\s+deploy)\b", "standalone deployment recipe")
forbid(DEPLOY_COMMAND_PATH, r"git add -A", "indiscriminate staging")
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
source_pages = {path.name for path in WIKI.glob("*.md") if path.name != README_PATH}
checks += 3
if len(pages) != len(manifest_pages):
    failures.append("wiki/manifest.json: duplicate page entries")
if manifest_pages != source_pages:
    missing = sorted(source_pages - manifest_pages)
    extra = sorted(manifest_pages - source_pages)
    failures.append(f"wiki/manifest.json: source mismatch missing={missing} extra={extra}")
if README_PATH in manifest_pages:
    failures.append("wiki/manifest.json: source-control README must not be published")

for required_page in (
    HOME_PAGE,
    "Current-Production-Status.md",
    "Operations-Playbook.md",
    "Trust-and-Safety.md",
    PUBLIC_STATEMENTS_PAGE,
    TRINITY_STATEMENT_PAGE,
):
    checks += 1
    if required_page not in manifest_pages:
        failures.append(f"wiki/manifest.json: missing required page {required_page}")

current_wiki = [
    page
    for page in manifest_pages
    if page not in {PUBLIC_STATEMENTS_PAGE, TRINITY_STATEMENT_PAGE}
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
    PUBLIC_STATEMENTS_PAGE,
    TRINITY_STATEMENT_PAGE,
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
http_probe = "".join(("http", ":", "//", "example.invalid", "/docs"))
ftp_probe = "".join(("ftp", ":", "//", "example.invalid", "/archive"))
link_classification_cases = (
    ("", (LINK_SKIP, "")),
    ("#section", (LINK_SKIP, "")),
    ("Home", (LINK_LOCAL, "Home")),
    ("Home.md#section", (LINK_LOCAL, HOME_PAGE)),
    ("./Home.md?view=1#section", (LINK_LOCAL, f"./{HOME_PAGE}")),
    ("Some%20Page.md#section", (LINK_LOCAL, "Some Page.md")),
    ("../Roadmap.md#section", (LINK_LOCAL, "../Roadmap.md")),
    ("https://example.invalid/docs", (LINK_EXTERNAL_URI, "")),
    ("mailto:docs@example.invalid", (LINK_EXTERNAL_URI, "")),
    (ftp_probe, (LINK_INSECURE_URI, "")),
    ("data:text/plain;base64,SGVsbG8=", (LINK_EXTERNAL_URI, "")),
    ("javascript:void%280%29", (LINK_EXTERNAL_URI, "")),
    ("web+demo:resource", (LINK_EXTERNAL_URI, "")),
    ("//example.invalid/docs", (LINK_EXTERNAL_URI, "")),
    (http_probe, (LINK_INSECURE_URI, "")),
    (http_probe.upper(), (LINK_INSECURE_URI, "")),
    ("https://[", (LINK_MALFORMED_URI, "")),
)
for target, expected_result in link_classification_cases:
    checks += 1
    actual_result = classify_wiki_link(target)
    if actual_result != expected_result:
        failures.append(
            "link-classifier regression: "
            f"{target!r} classified as {actual_result!r}, expected {expected_result!r}"
        )

link_validation_cases = (
    (HOME_PAGE, "Home", None),
    (HOME_PAGE, f"./{HOME_PAGE}?view=1#section", None),
    (HOME_PAGE, "https://example.invalid/docs", None),
    (HOME_PAGE, "data:text/plain,hello", None),
    (
        HOME_PAGE,
        "D-129-10-missing-probe",
        f"wiki/{HOME_PAGE}: broken local link D-129-10-missing-probe",
    ),
    (
        HOME_PAGE,
        http_probe,
        f"wiki/{HOME_PAGE}: insecure URI-scheme link {http_probe}",
    ),
    (
        HOME_PAGE,
        ftp_probe,
        f"wiki/{HOME_PAGE}: insecure URI-scheme link {ftp_probe}",
    ),
    (
        HOME_PAGE,
        "https://[",
        f"wiki/{HOME_PAGE}: malformed URI reference https://[",
    ),
)
for page, raw_target, expected_failure in link_validation_cases:
    checks += 1
    actual_failure = wiki_link_failure(page, raw_target)
    if actual_failure != expected_failure:
        failures.append(
            "link-validator regression: "
            f"{raw_target!r} returned {actual_failure!r}, expected {expected_failure!r}"
        )

for page in sorted(source_pages):
    body = (WIKI / page).read_text(encoding="utf-8")
    for raw_target in markdown_link.findall(body):
        checks += 1
        failure = wiki_link_failure(page, raw_target)
        if failure:
            failures.append(failure)

if failures:
    print(f"PUBLIC_DOCS_CONTRACT_FAIL checks={checks} failures={len(failures)}")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print(
    "PUBLIC_DOCS_CONTRACT_PASS "
    f"checks={checks} publishable_wiki_pages={len(manifest_pages)}"
)
