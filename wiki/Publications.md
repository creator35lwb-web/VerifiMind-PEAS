# Publications and citation register

> **Document boundary — publication metadata.** This page records stable publication identifiers and canonical sources. It does not establish current runtime state, milestone completion, or adoption. Follow each record for its own version, date, authorship, license, and corrections.

## Canonical records

| Work | Canonical identifier | Scope |
|---|---|---|
| **Multi-Agent Communication Protocol (MACP) v2.5** | [Version DOI 10.5281/zenodo.21345820](https://doi.org/10.5281/zenodo.21345820) | The immutable v2.5 publication record |
| **MACP concept record** | [Concept DOI 10.5281/zenodo.20399788](https://doi.org/10.5281/zenodo.20399788) | Stable DOI resolving to the MACP publication family and its versions |
| **Genesis v2.0 White Paper** | [DOI 10.5281/zenodo.17972751](https://doi.org/10.5281/zenodo.17972751) | Genesis Prompt Engineering Methodology and multi-model orchestration |
| **Original VerifiMind PEAS White Paper** | [DOI 10.5281/zenodo.17645665](https://doi.org/10.5281/zenodo.17645665) | Initial project concept and methodology record |
| **Evaluation Roadmap v1.0** | [`roadmap-v1.0` release tag](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases/tag/roadmap-v1.0) | Pre-registered M0–M9 evaluation plan and thresholds |
| **The Validation Paradox** | [Canonical live article](https://verifimind.ysenseai.org/research/paradox) | Self-referential validation problem, reflections, and open questions |

### Which MACP DOI should I use?

- Cite **`10.5281/zenodo.21345820`** when referring specifically to MACP v2.5.
- Cite **`10.5281/zenodo.20399788`** when referring to MACP as a continuing work across versions.

Do not substitute a nearby Zenodo record number. Version and concept DOIs have different purposes.

## Citation guidance

Zenodo’s record page is authoritative for the exact title, authors, publication date, license, and generated citation. Export BibTeX, DataCite, or another style directly from the DOI record when formal metadata matters.

Minimal version-specific BibTeX:

```bibtex
@misc{macp_v2_5,
  author = {Lee, Alton Wei Bin and {VerifiMind-PEAS FLYWHEEL TEAM}},
  title = {{Multi-Agent Communication Protocol (MACP) v2.5 — Loop Engineering}},
  year = {2026},
  version = {2.5.0},
  publisher = {Zenodo},
  doi = {10.5281/zenodo.21345820},
  url = {https://doi.org/10.5281/zenodo.21345820},
  note = {Version-specific record; concept DOI: 10.5281/zenodo.20399788}
}
```

Minimal project citation:

```bibtex
@software{verifimind_peas,
  title = {VerifiMind PEAS: Multi-Agent AI Validation System},
  year = {2025--2026},
  publisher = {GitHub},
  url = {https://github.com/creator35lwb-web/VerifiMind-PEAS},
  doi = {10.5281/zenodo.17645665}
}
```

Add the creators exactly as shown by the cited record rather than copying an older Wiki attribution.

## Research pages and reports

These are public research surfaces, but they are not substitutes for immutable DOI metadata:

- [Evaluation Roadmap v1.0](https://verifimind.ysenseai.org/research/evaluation-roadmap)
- [The Validation Paradox](https://verifimind.ysenseai.org/research/paradox)
- [Genesis Research Library](https://verifimind.ysenseai.org/library)
- [Public Statements](Public-Statements)

GitHub Discussions and operational reports can provide valuable context. Cite their title, URL, author, and observation date. Do not describe a discussion, mutable web page, or metrics snapshot as peer reviewed unless the artifact itself establishes that status.

## Publication classes

| Class | What it proves | What it does not prove |
|---|---|---|
| Version DOI | An immutable archived version exists | That it is the latest version or implemented in production |
| Concept DOI | A stable publication family exists | The contents of any particular version |
| Git tag/release | Repository content is bound to a commit | That the commit is deployed or operationally healthy |
| Live research page | Current rendered project content | Immutability or external peer review |
| Metrics report | Measurements for a stated window and method | Current health, causal impact, or future performance |
| Public statement | A dated project disclosure | Legal certification or exhaustive investigation |

## Integrity rules

1. Preserve exact DOI digits and distinguish version from concept records.
2. Treat a new publication version as a new immutable record; do not rewrite an older citation.
3. Publish corrections as corrections or addenda.
4. Keep release, deployment, registry, and research-publication claims separate.
5. Verify DOI metadata at the resolver before using it in formal work.

See [Genesis Methodology](Genesis-Methodology) for the textbook method, [Roadmap](Roadmap) for planned evaluation work, and [Current Production Status](Current-Production-Status) for the mutable runtime snapshot.
