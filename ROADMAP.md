# VerifiMind PEAS Roadmap

**Last reviewed:** August 10, 2026

**Current production baseline:** v0.5.58

**Roadmap authority:** [Evaluation Roadmap v1.0](docs/research/evaluation-roadmap/roadmap-v1.0.md), frozen by tag `roadmap-v1.0`

This page is the project-roadmap index. It does not silently replace the
pre-registered Evaluation Roadmap, predict release dates, or mark a milestone
complete. Exact releases record what shipped; live discovery records what is
running; tagged roadmap artifacts and dated retrospectives record what the
project promised and learned.

## Three sources, three jobs

| Question | Authority |
|---|---|
| What is running now? | [`/health`](https://verifimind.ysenseai.org/health), [`/setup`](https://verifimind.ysenseai.org/setup), and the [server card](https://verifimind.ysenseai.org/.well-known/mcp/server-card.json) |
| What shipped, and from which source? | [GitHub Releases](https://github.com/creator35lwb-web/VerifiMind-PEAS/releases) and [`CHANGELOG.md`](CHANGELOG.md) |
| What evidence must the project produce next? | [Evaluation Roadmap v1.0](docs/research/evaluation-roadmap/roadmap-v1.0.md) and its future tagged successors |

The public [Wiki](https://github.com/creator35lwb-web/VerifiMind-PEAS/wiki)
explains the stable methodology and operator playbook. It should link these
authorities instead of creating another version calendar.

## Current shipped foundation

As of the evidence cutoff above:

- v0.5.58 is live from public merge
  [`3019f5c4`](https://github.com/creator35lwb-web/VerifiMind-PEAS/commit/3019f5c4889d8334063d4a2d9243e87d96fc93a8);
- 13 MCP tools are defined, 8 are active, and 5 remain temporarily unavailable
  under security containment;
- the X → Z → CS pipeline preserves successful real stages when a sibling
  provider stage fails and withholds aggregate confidence from incomplete runs;
- runtime cross-provider failover remains disabled;
- the MCP Registry package is 3.35.0;
- the Core Tools Always Free pledge remains in force.

See [`SERVER_STATUS.md`](SERVER_STATUS.md) for the dated evidence snapshot and
live discovery for changes after that cutoff.

## Active work lanes

These lanes organize current work. They are not promised release numbers or
claims of completion.

### 1. Containment before restoration

The coordination and custom-template mutation paths stay unavailable until
their replacement contracts have owner-scoped authorization, bounded storage,
deletion semantics, migration handling, adversarial tests, and independent
review. Availability pressure does not override the containment boundary.

### 2. Reliability without overstating validity

Provider-seat separation, in-flight failover, retry policy, and degraded-output
semantics remain evaluation lanes. A routing configuration or passing test is
not evidence that the methodology is accurate, calibrated, or superior to a
single-model baseline.

### 3. The public evaluation clock

The year-one Evaluation Roadmap runs from May 2026 through April 2027. Its
milestones cover governance, labeled data, inter-rater reliability,
co-maintainership, sandboxing, calibration, external benchmarks, NIST AI RMF
self-attestation, and the year-one continue/pivot/sunset decision.

The seed evaluation dataset is public at
[Hugging Face](https://huggingface.co/datasets/YSenseAI/verifimind-peas-eval)
with DOI [10.5281/zenodo.21276884](https://doi.org/10.5281/zenodo.21276884).
That artifact does not by itself claim that every M2 acceptance condition is
closed. Milestone status belongs in a dated retrospective with the required
external signal.

### 4. Documentation as an authority graph

The README remains the concise front door. The Wiki becomes the indexed
textbook and operator playbook. Volatile versions, models, provider routing,
tool counts, deployment identifiers, and policy versions stay in live or
release-bound sources. Public Statements preserve dated disclosures and
explicit non-claims.

### 5. Sustainable open-source operation

The methodology, server code, self-hosting path, documentation, and BYOK
support remain open under the repository's licenses. A second maintainer,
external reviewers, reproducible evidence, and transparent failure reports are
more important at this stage than a speculative paid tier or a version-number
deadline.

## Change discipline

1. Do not edit the frozen `roadmap-v1.0` artifact without a new tagged roadmap
   version and an explicit reason.
2. Do not mark a milestone complete without its required artifact, witness, and
   retrospective.
3. Do not convert a planned lane into a shipped claim until an exact Release
   and public evidence exist.
4. Keep missed dates visible. A miss produces a retrospective, not a rewritten
   past.
5. Keep legal certification, calibrated accuracy, and incident closure outside
   software-release claims unless the named independent authority supplies the
   required evidence.

## Historical note

Earlier revisions of this file contained a March 2026 version calendar and
called v0.4.5 the current release. Git history preserves that planning record;
it is no longer presented as the current roadmap. The tagged Evaluation
Roadmap is the durable commitment surface going forward.
