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
FEATURES_PATH = "MCP_SERVER_FEATURES.md"
ROADMAP_PATH = "ROADMAP.md"
PUBLIC_STATEMENTS_PAGE = "Public-Statements.md"
TRINITY_STATEMENT_PAGE = "Statement-001-Trinity-Integrity.md"
HOME_PAGE = "Home.md"
LINK_SKIP = "skip"
LINK_LOCAL = "local"
LINK_EXTERNAL_URI = "external-uri"
LINK_INSECURE_URI = "insecure-uri"
LINK_MALFORMED_URI = "malformed-uri"
INSECURE_URI_SCHEMES = frozenset(("http", "ftp"))
# v0.5.66 (runtime currency) made ONE post-deploy Trinity run, recorded as
# observed (X real, Z real, CS unavailable; partial). The contract binds the
# one-run qualifier on every truth surface and rejects any generalisation to
# reliability. v0.5.65 made no run; its CHANGELOG section must keep saying so.
V0566_ONE_RUN = "run is not a reliability figure"
V0566_RUN_AS_OBSERVED = "X real, Z real, CS unavailable"
V0565_NO_TRINITY_RUN = "no post-deploy Trinity run was made for v0.5.65"
V0565_ATTRIBUTED_RUN = r"X/Z/CS = real/real/real"
# Privacy v2.7 / Terms v2.6 replaced the fixed October 20, 2026 date with a
# standing notice promise; the old date must not be presented as current.
REPLACED_DATE_AS_CURRENT = r"from \*\*October 20, 2026\*\*|from 20 Oct 2026"
STANDING_NOTICE_PROMISE = "at least 14 days in advance, and not before"
# The conversion that preceded the Release described it as pending; that
# wording must not survive the re-pin on any surface.
PENDING_RELEASE_CLAIM = (
    r"3\.42\.0 (?:is )?pending|Release v0\.5\.65: \*\*pending\*\*|pending at this\s+conversion"
    r"|3\.43\.0 (?:is )?pending|pending the v0\.5\.66 (?:GitHub )?Release|were\s+\*\*pending\*\* at this snapshot"
)
RELIABILITY_CLAIM = r"clean smoke|smoke(?: is| was)? clean|Trinity (?:is|remains|now) reliable|reliability (?:is )?(?:proven|established)"
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
require(README_PATH, "version-v0.5.66", "v0.5.66 badge")
require(README_PATH, "2903bb8d3ec4a24e143b359d52b77920ffa8fe25", "exact v0.5.66 merge")
require(README_PATH, "019112d5-b6b8-4497-a136-3276df9038f9", "exact v0.5.66 build")
require(README_PATH, "verifimind-mcp-server-00517-l2d", "exact v0.5.66 release revision")
require(README_PATH, "one run, not a reliability figure", "v0.5.66 one-run qualifier")
require(README_PATH, V0566_RUN_AS_OBSERVED, "v0.5.66 run recorded as observed")
forbid(README_PATH, RELIABILITY_CLAIM, "reliability generalised from a smoke run")
forbid(README_PATH, REPLACED_DATE_AS_CURRENT, "replaced registration date presented as current")
require(README_PATH, STANDING_NOTICE_PROMISE, "standing registration-notice promise")
# 3.43.0 was published by the v0.5.66 GitHub Release on 2026-10-18 (05:08 UTC)
# and is the live Registry identity; prior packages and both interim "pending"
# wordings (v0.5.65 and v0.5.66) are forbidden below.
require(README_PATH, "MCP Registry package:** `3.43.0`", "live Registry identity")
require(README_PATH, "releases/tag/v0.5.66", "v0.5.66 Release link")
forbid(README_PATH, PENDING_RELEASE_CLAIM, "Release/Registry still described as pending")
forbid(SERVER_STATUS_PATH, PENDING_RELEASE_CLAIM, "Release/Registry still described as pending")
require(README_PATH, "13 defined / 8 active / 5 temporarily unavailable", "availability taxonomy")
require(README_PATH, "21345820", "MACP v2.5 version DOI")
require(README_PATH, "Multi-Agent Communication Protocol (MACP) v2.5 — Loop Engineering", "MACP v2.5 title")
require(README_PATH, "version   = {2.5.0}", "MACP v2.5 record version")
require(README_PATH, "/wiki", "Wiki textbook/playbook link")
forbid(README_PATH, r"v0\.6\.0--Beta|v0\.6\.0-Beta", "Beta-as-current marker")
forbid(README_PATH, r"creator35lwb-web/verifimind-genesis-mcp", "private Hub link")
forbid(README_PATH, r"\*\*Providers:\*\*\s*7\b", "conflated remote/local provider count")
forbid(
    README_PATH,
    r"ba02fd02|82444203-10d0|b434979e|e3ca9551-0292|00496-g7s|07b422f1|6b1216e9-94dc|00508-dj8|2685d4c7|50896a37-f06e|00513-klm|00514-dnc|ba9b20a6|da4c87ec-d836|00515-q9f|00516-48g|MCP Registry package:\*\* `3\.(3[89]|4[0-2])\.0`",
    "prior release receipts",
)
forbid(
    README_PATH,
    r"After \[registering\]",
    "registration instruction while account features are in maintenance",
)
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
        if re.match(r"^## v0\.5\.66\b", section, flags=re.IGNORECASE)
    ),
    "",
)
changelog_previous = next(
    (
        section
        for section in changelog_sections
        if re.match(r"^## v0\.5\.65\b", section, flags=re.IGNORECASE)
    ),
    "",
)
checks += 10
if "v0.5.66" not in changelog_current:
    failures.append("CHANGELOG.md: current section is not v0.5.66")
if re.search(r"release candidate|not merged|not deployed", changelog_current, re.IGNORECASE):
    failures.append("CHANGELOG.md: v0.5.66 still described as a candidate")
if "2903bb8d3ec4a24e143b359d52b77920ffa8fe25" not in changelog_current:
    failures.append("CHANGELOG.md: exact v0.5.66 merge is absent")
if "019112d5-b6b8-4497-a136-3276df9038f9" not in changelog_current:
    failures.append("CHANGELOG.md: exact v0.5.66 build is absent")
if "verifimind-mcp-server-00517-l2d" not in changelog_current:
    failures.append("CHANGELOG.md: exact v0.5.66 release revision is absent")
if re.search(r"^## v0\.5\.65\b", changelog_current, flags=re.IGNORECASE | re.MULTILINE):
    failures.append("CHANGELOG.md: current section includes the prior release")
if V0566_ONE_RUN not in changelog_current or V0566_RUN_AS_OBSERVED not in changelog_current:
    failures.append("CHANGELOG.md: v0.5.66 does not record its one Trinity run as observed with the one-run qualifier")
if re.search(RELIABILITY_CLAIM, changelog_current, re.IGNORECASE):
    failures.append("CHANGELOG.md: v0.5.66 generalises a smoke run into reliability")
if V0565_NO_TRINITY_RUN not in changelog_previous or re.search(V0565_ATTRIBUTED_RUN, changelog_previous):
    failures.append("CHANGELOG.md: the v0.5.65 section no longer states truthfully that it made no post-deploy Trinity run")
if re.search(PENDING_RELEASE_CLAIM, changelog_previous):
    failures.append("CHANGELOG.md: v0.5.65 Release/Registry still described as pending")
# v0.5.63 shipped a Groq BYOK catalogue change while its entry denied one; the
# sentence shape that made that claim must not return in any current section.
if re.search(
    r"provider catalogue,?\s+or\s+tool-availability|no provider[- ]catalogue change is included",
    changelog_current,
    re.IGNORECASE,
):
    failures.append("CHANGELOG.md: current section denies a provider-catalogue change with the v0.5.63 sentence shape")

require(SERVER_STATUS_PATH, "| Application | **v0.5.66**", "current production version")
require(SERVER_STATUS_PATH, "| MCP Registry package | **3.43.0**", "live Registry identity")
require(SERVER_STATUS_PATH, "releases/tag/v0.5.66", "v0.5.66 Release link")
require(SERVER_STATUS_PATH, V0566_ONE_RUN, "v0.5.66 one-run qualifier")
require(SERVER_STATUS_PATH, V0566_RUN_AS_OBSERVED, "v0.5.66 run recorded as observed")
forbid(SERVER_STATUS_PATH, RELIABILITY_CLAIM, "reliability generalised from a smoke run")
require(SERVER_STATUS_PATH, "Serving revision", "serving-revision provenance field")
require(SERVER_STATUS_PATH, "verifimind-mcp-server-00517-l2d", "exact v0.5.66 release revision")
require(SERVER_STATUS_PATH, "verifimind-mcp-server-00518-pkp", "current serving revision (ambient-notice refresh)")
forbid(SERVER_STATUS_PATH, r"still\s+(?:carries|announces) (?:the )?v0\.5\.6[45] (?:text|notice)\b(?! on a 0\.5\.66)", "ambient notice described as stale after its refresh")
require(SERVER_STATUS_PATH, "019112d5-b6b8-4497-a136-3276df9038f9", "exact v0.5.66 build")
require(SERVER_STATUS_PATH, "sha256:fc705da94716925264c316b99ccba695258635f4361895458de634ff933fd5de", "exact v0.5.66 image digest")
require(SERVER_STATUS_PATH, "Terms v2.6 / Privacy v2.7", "current policy versions")
forbid(SERVER_STATUS_PATH, REPLACED_DATE_AS_CURRENT, "replaced registration date presented as current")
require(SERVER_STATUS_PATH, STANDING_NOTICE_PROMISE, "standing registration-notice promise")
require(FEATURES_PATH, "MCP 2026-07-28", "current MCP protocol")
forbid(FEATURES_PATH, r"advertises MCP 2025-11-25", "stale protocol-era claim")
forbid(FEATURES_PATH, r"Gemini 2\.5 Flash|2025-03-26|\bxAI\b", "stale runtime/catalogue claim")

# The public command delegates; it must never grow a second cloud recipe.
require(DEPLOY_COMMAND_PATH, "mcp-server/deploy-cloudrun.sh", "canonical recovery carrier")
forbid(DEPLOY_COMMAND_PATH, r"^\s*gcloud\s+(?:builds\s+submit|run\s+deploy)\b", "standalone deployment recipe")
forbid(DEPLOY_COMMAND_PATH, r"git add -A", "indiscriminate staging")
require(".github/workflows/docs-ci-bypass.yml", "python scripts/verify_public_docs_contract.py", "docs CI contract execution")
require(".github/workflows/docs-ci-bypass.yml", "- 'wiki/**'", "Wiki-source CI path")

require(ROADMAP_PATH, "Evaluation Roadmap v1.0", "tagged roadmap authority")
forbid(ROADMAP_PATH, r"Current-v0\.4\.5|v0\.4\.5 BYOK Live \(Current Release\)", "March 2026 current-state claim")

# The features guide and the roadmap carry no volatile release identity (it
# lives in SERVER_STATUS.md, /health and GitHub Releases), and rows that
# describe retired or contained behaviour must not return.
forbid(FEATURES_PATH, r"\*\*Production Version:\*\*|\*\*MCP Registry Package:\*\*|\*\*Last Updated:\*\*", "volatile release identity in the features guide")
require(FEATURES_PATH, SERVER_STATUS_PATH, "link to the dated status authority")
require(FEATURES_PATH, "13 defined / 8 active / 5 temporarily unavailable", "availability taxonomy (shared with README)")
forbid(FEATURES_PATH, r"requires `mcp-session-id` header|Session termination|Verify UUID \+ connection health|Full version history \(sanitized\)|Claude 4\.[0-9], 4\.[0-9]", "retired endpoint or fixed-catalogue claim")
require(FEATURES_PATH, "at least 14 days in advance, and not before", "standing registration-notice promise")
forbid(ROADMAP_PATH, r"\*\*Current production baseline:\*\* v0\.|is live from public merge|MCP Registry package is 3\.", "volatile release identity in the roadmap")
require(ROADMAP_PATH, SERVER_STATUS_PATH, "link to the dated status authority")
require(ROADMAP_PATH, "Authentication and registration", "authentication lane")
require(ROADMAP_PATH, "Dependency currency", "dependency lane")

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
