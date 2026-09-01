"""Fail closed when the two dependency manifests disagree.

Why this exists
---------------
`pyproject.toml` is the DEPLOYMENT DEPENDENCY AUTHORITY: the production
Dockerfile runs ``uv pip install --system --no-cache .``, which resolves that
file and never reads ``requirements.txt``. CI, by contrast, installs
``requirements.txt`` first and then runs ``pip install -e .`` — which re-resolves
``pyproject.toml`` and silently overwrites whatever the first step installed.

The failure mode this guards is therefore not "a version is wrong". It is:

* a dependency change lands in ``requirements.txt`` only,
* every CI check passes because the *second* install quietly reverts it,
* and the deployed image ships the old set while the PR claims the new one.

That happened. PR #329 originally bumped four interdependent packages in
``requirements.txt`` alone; nine displayed checks passed against the old set, and
the production image would have carried the old pins. Audit of the same commit
found the two manifests had *already* drifted on nine runtime packages, including
one (``smithery``) present only in ``pyproject.toml`` — installed into production
while ``test_v050_foundation.py::TestSmitheryRemoval`` reported its removal green,
because that class only ever inspected ``requirements.txt``.

Comments cannot enforce parity. This module does.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

SERVER_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = SERVER_ROOT / "pyproject.toml"
REQUIREMENTS = SERVER_ROOT / "requirements.txt"

# The ONLY packages permitted to appear in requirements.txt without appearing in
# pyproject.toml. These are never installed into the production image. Adding a
# name here is a deliberate declaration that it is test-only.
TEST_ONLY_PACKAGES = frozenset({"pytest", "pytest-asyncio", "pytest-cov"})

_REQUIREMENT = re.compile(
    r"^(?P<name>[A-Za-z0-9._-]+)"
    r"(?:\[(?P<extras>[^\]]*)\])?"
    r"(?P<spec>.*)$"
)


def canonical(name: str) -> str:
    """PEP 503 normalised distribution name."""
    return re.sub(r"[-_.]+", "-", name).strip().lower()


def parse_requirement(raw: str) -> tuple[str, frozenset[str], str]:
    """Return (canonical_name, extras, specifier) for one requirement string."""
    match = _REQUIREMENT.match(raw.strip())
    if match is None:  # pragma: no cover - guarded by test_every_line_parses
        raise ValueError(f"unparsable requirement: {raw!r}")
    extras_raw = match.group("extras") or ""
    extras = frozenset(
        canonical(item) for item in extras_raw.split(",") if item.strip()
    )
    return canonical(match.group("name")), extras, match.group("spec").strip()


def load_pyproject_dependencies() -> dict[str, tuple[frozenset[str], str]]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dependencies = data.get("project", {}).get("dependencies")
    assert isinstance(dependencies, list), (
        "pyproject.toml [project].dependencies is not a list — refusing to treat "
        "an unreadable authority as an empty one"
    )
    assert dependencies, (
        "pyproject.toml declares an empty [project].dependencies — refusing to "
        "pass vacuously against nothing"
    )
    parsed: dict[str, tuple[frozenset[str], str]] = {}
    for entry in dependencies:
        name, extras, spec = parse_requirement(entry)
        parsed[name] = (extras, spec)
    return parsed


def load_requirements() -> dict[str, tuple[frozenset[str], str]]:
    parsed: dict[str, tuple[frozenset[str], str]] = {}
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped:
            continue
        name, extras, spec = parse_requirement(stripped)
        parsed[name] = (extras, spec)
    return parsed


@pytest.fixture(scope="module")
def manifests():
    return load_pyproject_dependencies(), load_requirements()


class TestDependencyManifestParity:
    """pyproject.toml is authoritative; requirements.txt must mirror it exactly."""

    def test_both_manifests_exist(self):
        assert PYPROJECT.is_file(), f"missing dependency authority: {PYPROJECT}"
        assert REQUIREMENTS.is_file(), f"missing CI mirror: {REQUIREMENTS}"

    def test_every_authority_package_is_mirrored(self, manifests):
        pyproject, requirements = manifests
        missing = sorted(set(pyproject) - set(requirements))
        assert not missing, (
            "packages declared in pyproject.toml (which production installs) are "
            f"absent from requirements.txt (which CI installs): {missing}. CI is "
            "therefore not exercising the production dependency set."
        )

    def test_no_unmirrored_runtime_package(self, manifests):
        pyproject, requirements = manifests
        extra = sorted(set(requirements) - set(pyproject) - TEST_ONLY_PACKAGES)
        assert not extra, (
            f"requirements.txt declares runtime packages absent from the "
            f"deployment authority: {extra}. Either add them to pyproject.toml or "
            f"declare them test-only in TEST_ONLY_PACKAGES."
        )

    def test_specifiers_are_identical(self, manifests):
        pyproject, requirements = manifests
        drift = {
            name: {"pyproject": spec, "requirements": requirements[name][1]}
            for name, (_extras, spec) in pyproject.items()
            if name in requirements and requirements[name][1] != spec
        }
        assert not drift, (
            "version specifier drift between the deployment authority and the CI "
            f"mirror: {drift}. A green CI run against these is not evidence about "
            "the deployed artifact."
        )

    def test_extras_are_identical(self, manifests):
        pyproject, requirements = manifests
        drift = {
            name: {"pyproject": sorted(extras), "requirements": sorted(requirements[name][0])}
            for name, (extras, _spec) in pyproject.items()
            if name in requirements and requirements[name][0] != extras
        }
        assert not drift, (
            f"extras drift between manifests: {drift}. Extras change what is "
            "installed just as surely as versions do."
        )

    def test_test_only_packages_are_absent_from_the_production_authority(self, manifests):
        pyproject, _requirements = manifests
        leaked = sorted(TEST_ONLY_PACKAGES & set(pyproject))
        assert not leaked, (
            f"test-only packages leaked into the production image: {leaked}"
        )


class TestInstalledVersionsMatchTheAuthority:
    """The environment running these tests must carry the pinned versions.

    Resolving a version set and *running the suite against* that version set are
    two different claims. CI previously installed the targets and then reverted
    them one line later; the suite passed and reported nothing, because nothing
    ever compared what was installed to what was declared.

    Driven from pyproject.toml rather than a hardcoded list, so it cannot go
    stale the way a copied version literal does.
    """

    def test_exact_pins_are_the_versions_actually_installed(self):
        from importlib.metadata import PackageNotFoundError, version

        pyproject = load_pyproject_dependencies()
        exact = {
            name: spec[2:]
            for name, (_extras, spec) in pyproject.items()
            if spec.startswith("==")
        }
        assert exact, "no exact pins found — refusing to pass vacuously"

        mismatched: dict[str, dict[str, str]] = {}
        for name, expected in sorted(exact.items()):
            try:
                installed = version(name)
            except PackageNotFoundError:
                mismatched[name] = {"declared": expected, "installed": "NOT INSTALLED"}
                continue
            if installed != expected:
                mismatched[name] = {"declared": expected, "installed": installed}

        assert not mismatched, (
            "the running environment does not match the deployment authority: "
            f"{mismatched}. Test results from this environment are not evidence "
            "about the deployed artifact."
        )


class TestSmitheryRemovalCoversBothCarriers:
    """Regression guard for the carrier gap that hid smithery in production.

    ``test_v050_foundation.py::TestSmitheryRemoval`` has asserted since v0.5.0
    that smithery is gone, checking only ``requirements.txt``. ``pyproject.toml``
    still listed it, so production installed smithery plus toml/typer/art/
    shellingham — and the one test that would have caught this,
    ``test_smithery_not_importable``, is ``skipif`` the package is importable.
    Its own presence disabled its detector.
    """

    def test_smithery_absent_from_deployment_authority(self):
        # Parse the declared dependency list rather than substring-matching the
        # file text: the removal rationale is documented in a comment that names
        # the package, and a naive text search matches its own explanation.
        assert "smithery" not in load_pyproject_dependencies(), (
            "smithery is declared in pyproject.toml — it has zero imports in this "
            "codebase, it pulls toml/typer/art/shellingham into the production "
            "image, and its presence auto-skips test_smithery_not_importable"
        )

    def test_smithery_absent_from_ci_mirror(self):
        assert "smithery" not in load_requirements()


class TestAuthlibDependencyAuthority:
    """D-ALTON-2026-09-01-AUTHLIB (WP-A): the OAuth core is an exact pin, not a
    floating transitive, and the security-critical closure is bound."""

    def test_authlib_is_pinned_exactly(self):
        pyproject = load_pyproject_dependencies()
        assert pyproject.get("authlib", (None, None))[1] == "==1.8.0", (
            "Authlib must be an exact ==1.8.0 pin in pyproject.toml; direct "
            "imports may not rely on FastMCP's floating transitive."
        )
        assert load_requirements().get("authlib", (None, None))[1] == "==1.8.0"

    def test_joserfc_includes_issuer_validation_fix(self):
        # joserfc must be >=1.7.3 (issuer-validation fix GHSA-r74j-q665-7rpj);
        # pinned exactly here.
        spec = load_pyproject_dependencies().get("joserfc", (None, ""))[1]
        assert spec.startswith("=="), "joserfc must be exact-pinned"
        version = spec.lstrip("=")
        parts = tuple(int(p) for p in version.split(".")[:3])
        assert parts >= (1, 7, 3), f"joserfc {version} predates the issuer fix"

    def test_cryptography_backend_pinned(self):
        assert load_pyproject_dependencies().get("cryptography", (None, None))[1].startswith("==")

    def test_third_party_notices_cover_authlib(self):
        notices = (SERVER_ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
        for token in ("Authlib 1.8.0", "BSD-3-Clause", "joserfc", "cryptography"):
            assert token in notices, f"THIRD_PARTY_NOTICES.md missing {token!r}"
