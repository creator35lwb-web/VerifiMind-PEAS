# The Evaluation Roadmap

*Companion document to [The Validation Paradox](https://verifimind.ysenseai.org/research/paradox).*
*v1.0 — Published May 2026 · Tagged `roadmap-v1.0` · Year-one window: May 2026 → April 2027.*

---

## What this page is

The paradox page named what VerifiMind is: three agents — X, Z, CS — that are prompt templates running on frontier models, with no labeled evaluation set, no calibration, no execution sandbox, and no inter-judge agreement statistics. It ended on a single line: *the only available exit from a closed validation loop is an external signal.*

This page is the cheapest forgery-resistant external signal a solo project can manufacture: a public clock.

It commits to ten dated milestones over twelve months, each with (a) a concrete artifact, (b) a pre-registered numerical threshold for what "passes," and (c) a named external witness who is identified *before* the work starts so we cannot quietly choose a friendlier judge afterward. Every milestone closes with a public retrospective. Every silent edit to this page is mechanically blocked by a CI workflow that fails the build if `roadmap-v*.md` is modified without a new git tag.

We are publishing this knowing the most likely outcome is that we miss milestones. The structure is designed for that. Failure numbers ship in the same font size as success numbers.

---

## What VerifiMind is not yet

Before the roadmap, the disclaimer block — written so an enterprise buyer who finds this page through search cannot misread the paradox page as proof of certification:

- VerifiMind is **not** a certified safety auditor.
- VerifiMind is **not** a validated production evaluation tool.
- VerifiMind does **not** currently produce calibrated confidence intervals.
- VerifiMind does **not** currently execute submitted code in an isolated sandbox.
- VerifiMind has **not** yet established inter-judge agreement statistics against a held-out human-labeled set.

What VerifiMind *is*, today, is a structured hypothesis about how a three-agent critique pipeline (novelty / scoring / code-security) might improve on single-call frontier-model critique. This roadmap is the plan to make that hypothesis falsifiable.

---

## Pre-registered thresholds

These are stated *before* any data is collected. Failure to clear them does not kill the project. It triggers a public retrospective that names what changed and why.

| Threshold | Metric | Pre-registered bar |
|---|---|---|
| Inter-rater reliability | Cohen's κ (Landis–Koch scale) | κ ≥ 0.60 for usable claims; ≥ 0.80 for production-eligible language |
| Scoring calibration | Expected Calibration Error | ECE ≤ 0.05 on the held-out labeled set |
| Cross-family judge validity | \( \bar\kappa_{cross} \) across Anthropic/OpenAI/Google judges | \( \bar\kappa_{cross} \ge 0.60 \) (lower 95% CI) |
| Perturbation invariance | Agreement under semantics-preserving perturbations | \( I > 0.90 \) |
| Human-anchor agreement | Judge vs. human gold on anchor set | \( A_H \ge 0.80 \) |
| "Better than baseline" claim | F1 lift vs. single-call frontier baseline | \( \Delta F_1 \ge 0.10 \), lower 95% CI above 0 |
| CS execution success | Sandbox runs without crash on labeled vulnerability corpus | ESR ≥ 0.95 on runnable tasks |

The labeled-set size is sized to detect a 10-point F1 improvement at α = 0.05, power = 0.8: **800 items total, ≥ 400 positives per primary slice**, **400 adversarial items** (≥ 100 per attack family), **200 retest items** for test-retest reliability, and **200 human-anchor items**.

---

## Section A — The Public Roadmap

### Milestones

| # | Date | Milestone | Concrete artifact | External-signal evidence required |
|---|------|-----------|-------------------|-----------------------------------|
| M0 | **May 2026** | Roadmap published | This page + git tag `roadmap-v1.0` + CI workflow that fails on untagged roadmap edits | Roadmap referenced by ≥ 1 external blog, mailing list, or social post outside the VerifiMind/YSenseAI ecosystem |
| M1 | **Jun 2026** | Governance fixes shipped | LLM "C-suite" personas renamed to `(model, role-in-this-reflection)` tuples; `SECURITY.md` (90-day coordinated-disclosure window); `MAINTAINERS.md` with open second slot; `GOVERNANCE.md` (amendment process); co-maintainer search post live | ≥ 1 inbound CV or "interested" reply to the co-maintainer post; security disclosure email reachable and monitored |
| M2 | **Jul 2026** | Seed labeled eval set v0 | **100 items** under intra-annotator test-retest protocol (Gemini's design), expanded to **200 items** by month-end (Opus's milestone). Stratified across X / Z / CS. Published on Hugging Face Datasets with Zenodo DOI. License: MIT. Schema: `{input, agent, gold_label, annotator_id, annotator_notes, timestamp, perturbation_family}` | Dataset DOI minted; ≥ 1 independent download or fork logged; intra-annotator κ from 2-week washout protocol published |
| M3 | **Sep 2026** | First Cohen's κ report | Pre-registered three-way κ: (a) each agent vs. human gold, (b) same agent vs. itself across reruns with different seeds, (c) cross-family κ across Anthropic/OpenAI/Google judges. Bootstrap 95% CIs. Class-conditional confusion matrices. | Numbers published as found — including failure cases. Named external annotator (paid via Prolific) confirms label set independently. |
| M4 | **Oct 2026** | Co-maintainer onboarded **or** publicly conceded | Either second named maintainer in `MAINTAINERS.md` with merged independent PR, **or** a published retrospective explaining why recruitment failed and what changes next | Co-maintainer's first independent PR merged with passing CI, *or* timestamped + signed concession retrospective |
| M5 | **Nov 2026** | CS execution sandbox v0 | gVisor or Firecracker isolation; no network egress by default; explicit allow-list per evaluation; published threat model covering MCP-specific attack classes (prompt injection via repo content, SSRF, plaintext credentials, response leakage); one-command reproduction harness | One named external security researcher invited to break it; their write-up published whether positive or negative |
| M6 | **Jan 2027** | Z calibration & abstention | Z emits confidence + ECE + reliability diagram against the M2 labeled set. Mandatory abstention when cross-judge κ on item type < 0.40. Brier score reported. | Reliability diagram + ECE + Brier published with 95% bootstrap CIs and a list of high-confidence wrong answers |
| M7 | **Feb 2027** | External benchmark — readiness-gated | One named benchmark per agent, pre-registered in `roadmap-v1.x` *before* running. Candidates: **HaluEval** (X), **MLCommons AILuminate** (Z), **SWE-Bench Lite** or **PaperBench** (CS). Readiness memo published first: dataset version, κ, calibration results, known blind spots, pre-registered interpretation of failure. | Full prompt logs, seeds, model identifiers, and raw outputs published. Results acknowledged by ≥ 1 external party. |
| M8 | **Mar 2027** | NIST AI RMF self-attestation | Mapping of VerifiMind's practices to the [NIST AI RMF Generative AI Profile](https://www.nist.gov/itl/ai-risk-management-framework) Govern/Map/Measure/Manage functions, with honest gap statement | One external reviewer (academic, journalist, or practitioner) invited to critique; their critique published |
| M9 | **Apr 2027** | Year-1 retrospective | Full retrospective covering every milestone hit, slipped, or abandoned. Decision: continue OSS-free, pivot, or sunset. Labeled set at **800 items** (GPT-5.4's power-calculated floor). | Retrospective signed and dated; raw progress data and all dataset versions linked |

### Kill-conditions

The roadmap is real only if abandonment conditions are stated up front. VerifiMind-as-tool will be retired and the work continued as methodology research if any of the following observable conditions occurs, with a public retrospective explaining the trigger:

1. **No external human validation by day 180** — fewer than 3 independent non-friend users complete a structured evaluation task and consent to be cited.
2. **No ML co-maintainer by day 120** — no qualified collaborator signs a scoped RFC role or completes a substantive PR/review cycle despite a public role spec.
3. **Label reliability failure** — after two label-protocol revisions, core label κ remains below 0.60 on a representative sample.
4. **Calibration failure** — Z cannot show materially better-than-baseline calibrated confidence on the labeled set, with high-confidence false positives remaining frequent and unexplained.
5. **Security gating failure** — CS requires code execution for its advertised claims but no sandbox + threat model are shipped by day 180.
6. **Benchmark falsification without learning** — external benchmark shows weak performance and no credible error taxonomy is produced within 30 days.
7. **Cost-revenue inversion** — frontier-model and hosting costs exceed project revenue or committed sponsor funding for 3 consecutive months with no credible unit-cost path.
8. **Trust harm** — a buyer, vendor, or public reviewer reasonably interprets VerifiMind as claiming validated ML rigor this roadmap admits it does not yet possess.

A kill-condition firing produces a *documented decision*, not an automatic pivot. The decision is published, dated, and signed.

### Commitment mechanism

A roadmap that lives only on a webpage is editable. Four mechanisms operate together to convert it from aspirational to binding:

1. **Git tags as commitments.** This document is tagged `roadmap-v1.0`. Any modification of a milestone date or definition requires a new tag with a diff and a public reason. `git log --tags` is the audit trail.
2. **Milestone-keyed retrospectives.** Each milestone closes with a public retrospective post. The retrospective is the artifact; the milestone is not complete until the retrospective is published.
3. **Pre-named third-party witnesses.** For M3, M5, M7, M8, the external party is named *in advance*, publicly. A milestone with a named external reviewer cannot be unilaterally marked complete.
4. **Pre-registered failure conditions.** Every milestone has an explicit "this counts as a miss" definition stated now, not after the fact. Post-hoc rationalization is visible because the rationalization comes after the pre-registration.

Git tags make silent edits visible. Retrospectives make silent skips visible. Witnesses make false completions visible. Pre-registered failure conditions make rationalization visible. Together they form the cheapest available substitute for the institutional review structure VerifiMind cannot afford.

### What this roadmap deliberately does not promise

To avoid the failure mode the paradox page warned against (frameworks producing more frameworks):

- It does **not** promise revenue, users, or adoption metrics.
- It does **not** promise that κ will be high — only that κ will be measured and published.
- It does **not** promise the co-maintainer search succeeds — only that the search happens publicly and its outcome is reported.
- It does **not** promise VerifiMind becomes a credible eval framework by April 2027. It promises that by April 2027, any external reader can answer "is this project methodologically serious?" from public evidence — in either direction.

---

## Section B — Technical RFC Appendix

*Intended audience: an ML-literate person considering joining VerifiMind as a second maintainer. This appendix exists because Section A above is deliberately non-technical and will not on its own surface the questions a co-maintainer needs answered.*

### B.1 Abstract

VerifiMind is currently a set of prompt-template-based evaluation agents (X / Z / CS) running over frontier model APIs and exposed via an MCP server at `verifimind.ysenseai.org`. This RFC proposes building a falsifiable evaluation substrate beneath those agents. It is not a claim that AI validation is solved. It is a scoped plan to produce evidence that distinguishes the agents' behavior from the underlying models' single-call behavior, with pre-registered thresholds and named external witnesses.

### B.2 Non-goals

- Certified safety audits.
- Production security guarantees.
- Autonomous code execution outside a sandbox.
- Calibrated scoring claims before the calibration report ships.
- Any "verification" claim before the cross-family judge triangulation clears its pre-registered bounds.

### B.3 System overview

Three agents exposed via MCP:

- **X (novelty / contradiction)** — grounded against a curated prior-art corpus once retrieval ships; outputs are decomposed into atomic claims with cited evidence spans for faithfulness scoring.
- **Z (scoring)** — produces confidence + abstention rather than scalar scores; calibrated against the M2 labeled set.
- **CS (code / security audit)** — runs in a gVisor or Firecracker sandbox post-M5; emits execution receipts, not opinions.

Known circularity risks documented on the [paradox page](https://verifimind.ysenseai.org/research/paradox).

### B.4 Evaluation dataset spec

- **Size**: 100 → 200 → 800 across M2 → M2-close → M9. Stratification: ≈ 35% X, 35% Z, 30% CS, with ≥ 400 positives per primary slice at full size.
- **Adversarial set**: 400 items, ≥ 100 per attack family (paraphrase, prompt-injection-style instruction conflict, evidence omission, formatting/noise).
- **Retest set**: 100 minimum, 200 preferred for per-slice stability claims under Fisher-\(z\) asymptotics.
- **Human-anchor set**: ≥ 200 items, stratified by slice and difficulty, used for judge-validity anchoring.
- **Format**: JSONL `{input, agent, gold_label, annotator_id, annotator_notes, timestamp, perturbation_family, slice}`. Versioned via DVC or git-lfs; mirrored to Hugging Face Datasets and Zenodo (DOI).
- **Annotation protocol**: until co-maintainer onboarded, intra-annotator test-retest with 2-week washout on a randomized 30% subset; after onboarding, double-annotation with adjudication.
- **License**: MIT. Rubric versioned independently; rubric changes force a dataset minor-version bump.

### B.5 Metric definitions (mathematically pre-registered)

**Agent X (faithfulness, coverage, precision)**:

\[
\mathrm{Ground}_X = \frac{1}{\sum_i m_i}\sum_{i,j}\mathbb{1}[E_i \models \hat g_{ij}], \quad
\mathrm{Cov}_X = \frac{\sum_i |\mathrm{match}(\hat G_i,G_i)|}{\sum_i |G_i|}, \quad
\mathrm{Prec}_X = \frac{\sum_i |\mathrm{match}(\hat G_i,G_i)|}{\sum_i |\hat G_i|}
\]

Scalar summary \( Q_X = 3 / (\mathrm{Ground}_X^{-1} + \mathrm{Cov}_X^{-1} + \mathrm{Prec}_X^{-1}) \) — but the public report ships the full vector to prevent coverage-by-hallucination.

**Agent Z (calibration)**:

\[
\mathrm{ECE} = \sum_{m=1}^{M}\frac{|B_m|}{n}\left|\mathrm{acc}(B_m) - \mathrm{conf}(B_m)\right|, \quad
\mathrm{Brier} = \frac{1}{N}\sum_{i=1}^{N}(y_i - \hat p_i)^2
\]

Reliability diagram plots \(\mathrm{acc}(B_m)\) vs. \(\mathrm{conf}(B_m)\) against the identity line. ([Guo et al. 2017](https://proceedings.mlr.press/v70/guo17a/guo17a.pdf))

**Agent CS (detection + execution)**:

\[
P = \frac{TP}{TP+FP}, \quad R = \frac{TP}{TP+FN}, \quad F_1 = \frac{2PR}{P+R}, \quad \mathrm{ESR} = \frac{\#\text{successful runs}}{\#\text{runnable tasks}}
\]

Report both micro-F1 and macro-F1 across CWE slices. "Better at security" is not a claim VerifiMind can make unless detection quality AND execution quality are both non-inferior to baseline.

### B.6 Inter-rater reliability plan

Cohen's κ definition: \( \kappa = (p_o - p_e) / (1 - p_e) \). Pre-registered Landis–Koch thresholds: κ < 0.40 = "unfit"; 0.40–0.59 = "moderate, ship with caveats"; 0.60–0.79 = "substantial, usable"; ≥ 0.80 = "near-perfect, production-eligible." Bootstrap 95% CIs. 200 items will produce wide CIs; that fact will be visible in the M3 report.

### B.7 Cross-family judge triangulation

Let \( J_i^{(a)}, J_i^{(o)}, J_i^{(g)} \) be judge labels from Anthropic, OpenAI, Google. Compute pairwise \( \kappa_{ao}, \kappa_{ag}, \kappa_{og} \) and \( \bar\kappa_{cross} = (\kappa_{ao} + \kappa_{ag} + \kappa_{og})/3 \). Define perturbation invariance \( I = \frac{1}{n}\sum_i \mathbb{1}[J_i(x_i) = J_i(\tilde x_i)] \) and human-anchor agreement \( A_H = \frac{1}{n}\sum_i \mathbb{1}[J_i = H_i] \). A judge is used only if lower 95% CIs satisfy \( \bar\kappa_{cross} > 0.60 \), \( I > 0.90 \), \( A_H > 0.80 \). This is the structural answer to the "AI grading AI" objection.

### B.8 External methodology mapping

| Agent | External method | Submission |
|---|---|---|
| X | [RAGAS](https://github.com/explodinggradients/ragas) Faithfulness + [ARES](https://github.com/stanford-futuredata/ARES) | HaluEval |
| Z | [G-Eval](https://arxiv.org/abs/2303.16634) + [Prometheus-Eval](https://github.com/prometheus-eval/prometheus-eval) | MLCommons AILuminate |
| CS | [SWE-Bench Lite](https://www.swebench.com/) + [HumanEval](https://github.com/openai/human-eval) + [OWASP Top 10 for LLMs](https://owasp.org/www-project-top-10-for-large-language-model-applications/) | SWE-Bench Lite or PaperBench |

### B.9 Sandbox & security plan (M5)

- **Isolation**: gVisor (preferred for solo-maintainer overhead) or Firecracker.
- **Network policy**: no egress by default; explicit allow-list per evaluation.
- **Resource limits**: time, memory, CPU pinned per task.
- **Threat model**: covers MCP-specific attack classes ([Equixly](https://equixly.com/blog/2025/03/29/mcp-server-new-security-nightmare/), [Vulnerable MCP Project](https://vulnerablemcp.info)): prompt injection via repo content, SSRF on fetch tools, plaintext credentials, response leakage across clients.
- **Reproduction harness**: `make sandbox-demo` spins up a one-command reproduction so external reviewers don't negotiate environment setup.

### B.10 MCP version-pinning

MCP is a dated specification with active evolution ([MCP spec](https://modelcontextprotocol.io/specification/2025-06-18)). All MCP integration sits behind an adapter layer; spec versions are pinned; a compatibility test suite runs each release.

### B.11 Reproducibility checklist

Modeled on the [NeurIPS Paper Checklist](https://neurips.cc/public/guides/PaperChecklist):

- [ ] All random seeds pinned and logged.
- [ ] Temperature, top-p, decoding parameters logged per run.
- [ ] All system prompts and templates hashed and committed.
- [ ] Exact model identifiers + provider release identifiers pinned per run.
- [ ] Dataset version + split version recorded with each result.
- [ ] Raw judge outputs preserved (not just aggregated scores).
- [ ] Evaluation harness commit SHA + container digest recorded.
- [ ] Exact commands published for reproducing every table and figure.
- [ ] All headline claims report bootstrap confidence intervals or significance tests.
- [ ] Compute resources, runtime, licenses, and known limitations disclosed.

A CI check rejects any run missing required version metadata.

### B.12 Co-maintainer role

**Scope.** First-author co-credit on the M3 inter-rater report and the M7 external benchmark write-up. DOI on the M2 dataset (Zenodo). Veto authority on any claim that outruns evidence. 12-month engagement to year-1 retrospective with a public exit ramp at M9 — not an indefinite commitment.

**Time commitment.** 2–4 hours/week for the first 8 weeks for RFC review and label-protocol design, then renegotiated based on funding and fit.

**Compensation (staged, honest).**

1. Public co-authorship and governance authority from day one.
2. Paid milestone stipend if/when funds exist.
3. GitHub Sponsors / Open Collective passthrough once registered, per [GitHub Sponsors program rules](https://docs.github.com/en/sponsors/receiving-sponsorships-through-github-sponsors/about-github-sponsors-for-open-source-contributors).
4. Revenue / grant share on any commercial wrap-around services.

Current US senior ML engineer base ranges are $173k–$295k remote ([Signify Technology, 2025–2026](https://www.signifytechnology.com/news/machine-learning-engineer-salary-benchmarks-us-market-2025-2026/)). VerifiMind cannot match that; the offer is bounded, transparent, and structured for someone who wants visible authorship of a public eval methodology rather than full-time compensation.

**IP & licensing.** Repository: MIT. Dataset: MIT. Contributor Certificate of Origin (DCO) sign-off on commits. Independent prior work remains the contributor's. Co-authorship rights on all publications.

**Exit clause.** Either party may exit with 14 days' notice. Handoff notes on any merged work. Attribution preserved. Unpaid drafts, datasets, and pending sponsor funds disposition is documented in `GOVERNANCE.md`.

### B.13 Methodological gaps a co-maintainer would own

1. **Elicitation gap** — designing adversarial elicitation protocols (paraphrase robustness, prompt-perturbation tests, role-play jailbreaks targeting the X/Z/CS judges themselves). ([Apollo "The Evals Gap"](https://www.apolloresearch.ai/science/the-evals-gap/))
2. **Label-set bias** — a 200-item seed authored by the prompt author is structurally circular; the co-maintainer designs the v1 expansion (target 1,000+ by M9) with explicit out-of-distribution slices and a held-out test set never seen by the prompt author.
3. **Construct validity** — operational definitions of "novelty" (X), "scoring" (Z), and "vulnerability" (CS) are owed before the v1 label expansion.
4. **Cost-quality frontier** — benchmarking whether smaller judges (Llama-3 70B, JudgeLM-7B) reach acceptable κ at a fraction of cost, per [Thakur et al. 2024](https://arxiv.org/html/2406.12624v1).

### B.14 Acceptance criteria for the co-maintainer's first "done"

- Public dataset v0.1 on Hugging Face + Zenodo DOI.
- κ report (three-way, with bootstrap CIs).
- Z calibration report (ECE + Brier + reliability diagram).
- X grounding prototype with retrieval against a curated corpus.
- CS threat model published.
- Go/no-go memo for M7 external benchmark submission.

---

## Signed and dated

This roadmap is inside the loop it describes. We publish it anyway, because the only available exit from a closed validation loop is an external signal — and a public clock is one of the few external signals a solo project can manufacture honestly.

*— Lee Wei Bin (Alton), VerifiMind. May 2026. Tagged `roadmap-v1.0`.*

---

### Sources & methodology

- [The Validation Paradox](https://verifimind.ysenseai.org/research/paradox) — companion document
- [Anthropic, Responsible Scaling Policy v3](https://www.anthropic.com/news/responsible-scaling-policy-v3) — public-roadmap-as-forcing-function model
- [Apollo Research, "We Need A Science of Evals"](https://www.apolloresearch.ai/science/we-need-a-science-of-evals/)
- [Apollo Research, "The Evals Gap"](https://www.apolloresearch.ai/science/the-evals-gap/)
- [METR — Common Elements of Frontier AI Safety Policies](https://metr.org/common-elements)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [Guo et al., "On Calibration of Modern Neural Networks" (ICML 2017)](https://proceedings.mlr.press/v70/guo17a/guo17a.pdf) — ECE definition
- [scikit-learn — Cohen's κ](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html), [Brier score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html), [Calibration](https://scikit-learn.org/stable/modules/calibration.html)
- [HaluEval](https://arxiv.org/abs/2305.11747), [MLCommons AILuminate](https://ailuminate.mlcommons.org), [SWE-Bench](https://www.swebench.com/), [HumanEval](https://github.com/openai/human-eval), [PaperBench](https://openai.com/index/paperbench/)
- [Galileo — Why LLM Judges Disagree With Your Experts](https://galileo.ai/blog/llm-judge-sme-feedback-expert-disagreement) — κ deployment thresholds
- [Thakur et al., "Evaluating Alignment and Vulnerabilities in LLMs-as-Judges" (arXiv:2406.12624)](https://arxiv.org/html/2406.12624v1)
- [MCP Specification (2025-06-18)](https://modelcontextprotocol.io/specification/2025-06-18), [Equixly: MCP Servers — The New Security Nightmare](https://equixly.com/blog/2025/03/29/mcp-server-new-security-nightmare/), [Vulnerable MCP Project](https://vulnerablemcp.info)
- [NeurIPS Paper Checklist](https://neurips.cc/public/guides/PaperChecklist) — reproducibility template
- [GitHub Sponsors for Open Source Contributors](https://docs.github.com/en/sponsors/receiving-sponsorships-through-github-sponsors/about-github-sponsors-for-open-source-contributors), [Signify Technology ML salary benchmarks 2025–2026](https://www.signifytechnology.com/news/machine-learning-engineer-salary-benchmarks-us-market-2025-2026/)
