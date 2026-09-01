# Third-Party Notices

VerifiMind-PEAS (MIT) redistributes and depends on the following third-party
components. This notice reproduces required attributions; each component
remains governed by its own license.

## Authlib 1.8.0 — BSD-3-Clause

OAuth 2.1 authorization-server protocol core (D-ALTON-2026-09-01-AUTHLIB).

- Homepage: https://authlib.org/
- Source: https://github.com/authlib/authlib (tag `v1.8.0`,
  commit `1a86748b31a2b1940b09cf627d1b70e03d85c077`)
- PyPI: https://pypi.org/project/Authlib/1.8.0/ (Trusted Publishing provenance)
- License: BSD-3-Clause — https://github.com/authlib/authlib/blob/main/LICENSE

BSD-3-Clause requires retention of the copyright notice, this list of
conditions, and the disclaimer, and forbids using the author's name to endorse
derived products without permission. VerifiMind makes no claim of Authlib
maintainer endorsement.

## joserfc 1.7.5 — BSD-3-Clause

JOSE/issuer-validation support in Authlib's dependency closure. Pinned at
>=1.7.3 to include the issuer-validation fix (advisory GHSA-r74j-q665-7rpj).

- Source: https://github.com/authlib/joserfc
- License: BSD-3-Clause

## cryptography 46.0.1 — Apache-2.0 OR BSD-3-Clause

Cryptographic backend used by Authlib and joserfc.

- Source: https://github.com/pyca/cryptography
- License: Apache-2.0 OR BSD-3-Clause

---

These OAuth dependencies participate in the deployment dependency authority
(`pyproject.toml`) and are enforced by
`tests/unit/test_dependency_manifest_parity.py`. This is a technical
compatibility record, not legal advice.
