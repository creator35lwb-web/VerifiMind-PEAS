"""THIRD_PARTY_NOTICES.md reproduces each pinned artifact's license VERBATIM.

T S156 step 5: third-party-license evidence must come from the exact pinned
release artifacts, not a summary or a link. Every ``LICENSE-FILE`` block in
the notice is compared byte-for-byte against the license file pip installed
from the pinned distribution (``<dist>.dist-info/licenses/``), and the SHA-256
stamped on the block must match those bytes. A pin bump without a notice
refresh fails here; so does any paraphrase, truncation, or duplicated block.
"""

import hashlib
import importlib.metadata as metadata
import pathlib
import re

import pytest

NOTICES = pathlib.Path(__file__).resolve().parents[2] / "THIRD_PARTY_NOTICES.md"

# Mirrors the OAuth pins in pyproject.toml / requirements.txt.
PINS = {"Authlib": "1.8.0", "joserfc": "1.7.5", "cryptography": "46.0.1"}
LICENSE_FILES = {
    "Authlib": {"LICENSE"},
    "joserfc": {"LICENSE"},
    "cryptography": {"LICENSE", "LICENSE.APACHE", "LICENSE.BSD"},
}

BLOCK = re.compile(
    r"<!-- LICENSE-FILE: (?P<rel>\S+) sha256=(?P<sha>[0-9a-f]{64}) -->\n"
    r"```text\n(?P<body>.*?)```\n<!-- END-LICENSE-FILE -->\n",
    re.DOTALL,
)


def _notice_text() -> str:
    # Normalize line endings so a CRLF checkout compares against the LF
    # bytes pip installed.
    return NOTICES.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def _installed_license(name: str, version: str, filename: str):
    dist = metadata.distribution(name)
    assert dist.version == version, f"{name} installed at {dist.version}, pinned {version}"
    root = pathlib.Path(str(dist.locate_file("")))
    dist_info = next(
        p for p in root.iterdir()
        if p.name.lower() == f"{name.lower()}-{version}.dist-info"
    )
    return (
        f"{dist_info.name}/licenses/{filename}",
        (dist_info / "licenses" / filename).read_bytes(),
    )


def _blocks():
    # Keyed by installed path; a duplicated block would otherwise collapse to
    # its LAST copy and let a corrupted first copy hide behind a correct one.
    matches = list(BLOCK.finditer(_notice_text()))
    rels = [m.group("rel") for m in matches]
    assert len(rels) == len(set(rels)), f"duplicate LICENSE-FILE blocks: {rels}"
    return {m.group("rel"): m for m in matches}


def test_every_pinned_license_file_is_reproduced_verbatim():
    blocks = _blocks()
    assert blocks, "no LICENSE-FILE blocks found in THIRD_PARTY_NOTICES.md"
    for name, version in PINS.items():
        for filename in LICENSE_FILES[name]:
            rel, installed = _installed_license(name, version, filename)
            assert rel in blocks, f"{rel} is missing from THIRD_PARTY_NOTICES.md"
            body = blocks[rel].group("body").encode("utf-8")
            assert body == installed, f"{rel} is not reproduced verbatim"
            assert hashlib.sha256(body).hexdigest() == blocks[rel].group("sha")


def test_no_stray_license_blocks():
    # Every block must belong to a pinned distribution: a stale block from a
    # retired dependency is stale evidence.
    expected = set()
    for name, version in PINS.items():
        for filename in LICENSE_FILES[name]:
            expected.add(_installed_license(name, version, filename)[0])
    present = set(_blocks())
    assert present == expected


@pytest.mark.parametrize("name,version", sorted(PINS.items()))
def test_pinned_component_and_version_are_named(name, version):
    assert f"{name} {version}" in _notice_text()


def test_notice_disclaims_legal_advice():
    text = _notice_text().lower()
    assert "not legal advice" in text
