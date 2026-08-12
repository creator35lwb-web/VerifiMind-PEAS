# Wiki source contract

This directory is the source set for the VerifiMind PEAS GitHub Wiki. It intentionally separates durable explanation from mutable evidence so a release update cannot silently rewrite the method or an old metric cannot masquerade as live truth.

This file is a maintainer guide. It is deliberately excluded from `manifest.json` and must not be published as a Wiki page.

## Information classes

| Class | Canonical pages | Change rule |
|---|---|---|
| **Textbook** | `Genesis-Methodology.md`, `Architecture.md` | Stable concepts and boundaries only; no mutable provider, version, or incident claims |
| **Playbook** | `Operations-Playbook.md`, `Trust-and-Safety.md` | Repeatable procedures and standing commitments; current examples link to the live reference |
| **Live reference** | `Current-Production-Status.md` | Dated snapshot with exact source/build/runtime/registry evidence; update after production change |
| **Dated evidence** | `Metrics-Dashboard.md` | Every number carries a report, observation period, method, and limitation |
| **Plans** | `Roadmap.md` | Targets and gates are not completion or deployment claims |
| **Publication register** | `Publications.md` | Exact immutable identifiers; distinguish version DOI from concept DOI |
| **Trust ledger** | `Public-Statements.md`, `Statement-001-Trinity-Integrity.md` | Durable disclosures; corrections by dated addendum, never silent historical rewrite |

Other Wiki pages are navigation, onboarding, or reference companions. If they state a mutable fact, they must defer to `Current-Production-Status.md`.

`Genesis-Methodology.md` is the canonical textbook slug. `Methodology.md` remains retired and must not be reintroduced. Do not create or publish a second Genesis alias.

## Truth precedence

When sources disagree, do not blend them. Mark the field unknown or stale and reconcile it through a reviewed change.

1. Live runtime evidence for runtime facts (`/health`, `/setup`, MCP initialize/list, real inference).
2. Exact release target and source commit for code identity.
3. Cloud build, serving revision, and smoke receipt for deployment evidence.
4. Registry workflow and `server.json` for distribution metadata.
5. Current production status for the reviewed public snapshot.
6. Trust ledger for dated disclosures and their correction history.
7. Metrics report for only its named observation window.

No single source proves the entire chain.

## Publishing contract

- `manifest.json` is the explicit allowlist of publishable Markdown files.
- `sourceWikiHead` records the live Wiki source audited before this migration;
  `protectedPages` pins normalized-LF SHA-256 hashes for the byte-preserved
  trust-ledger content across Windows and Linux checkouts.
- Every listed source must exist and end in `.md`.
- Source-only maintainer material is not listed.
- Special GitHub Wiki pages `_Sidebar.md` and `_Footer.md` are allowlisted explicitly.
- A publisher must copy only allowlisted files and must not delete a remote trust-ledger page merely because a local unrelated page was retired.
- `Public-Statements.md` and `Statement-001-Trinity-Integrity.md` require byte-preserving publication unless a separately reviewed addendum is authorized.

## Review checklist

Before publishing:

1. validate `manifest.json` and confirm every entry exists;
2. confirm the maintainer guide is absent from the allowlist;
3. confirm alternative Genesis aliases and retired `Methodology.md` are absent;
4. scan links for the canonical `Genesis-Methodology` slug;
5. compare current production facts with live and release evidence;
6. ensure metrics include dates and are not labeled current;
7. verify MACP v2.5 DOI `10.5281/zenodo.21345820` and concept DOI `10.5281/zenodo.20399788` exactly;
8. verify COORD-01 says **contained, not closed**;
9. compare protected trust-ledger files byte-for-byte with their approved source; and
10. review the final Wiki diff before publication.
