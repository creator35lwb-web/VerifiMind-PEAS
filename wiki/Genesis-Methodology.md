# Genesis: a human-directed validation method

> **Document boundary — textbook.** This page explains the durable method. It does not declare which software version, model, provider, tool, or incident state is live. For those facts, use [Current Production Status](Current-Production-Status).

Genesis is a repeatable way to examine an AI concept before treating an answer as a decision. It combines distinct analytical roles, explicit evidence, adversarial challenge, and a human decision owner. The aim is not to make an AI output infallible. The aim is to make uncertainty, disagreement, and missing evidence visible early enough to act responsibly.

## The five moves

| Move | Question | Required output |
|---|---|---|
| **1. Frame** | What decision is being made, for whom, under which constraints? | A bounded problem, success criteria, assumptions, and named decision owner |
| **2. Explore** | What opportunities and feasible approaches exist? | Alternatives, expected value, dependencies, and disconfirming evidence to seek |
| **3. Challenge** | Who could be harmed, what could fail, and what is being taken for granted? | Ethical objections, security threats, misuse cases, and unresolved questions |
| **4. Synthesize** | What survives the challenge, and with what confidence? | A traceable recommendation that preserves disagreement and withholds unsupported fields |
| **5. Iterate** | What new evidence would change the decision? | Tests, owners, stop conditions, and a dated review point |

The moves are recursive. A challenge can force reframing; new evidence can reopen synthesis. “Finished” means the decision owner has enough evidence to choose a next action, not that uncertainty has disappeared.

## Roles, not personalities

The production Trinity implements three analytical seats:

- **X — opportunity and critical analysis:** tests value, differentiation, feasibility, and alternatives.
- **Z — ethics and safety:** examines affected parties, consent, fairness, legal and social risk, and can raise a blocking veto.
- **CS — security:** examines threats, abuse paths, data exposure, controls, and residual risk.

The names are role labels. They do not prove independence. Real diversity depends on prompts, model families, providers, evidence sources, and failure domains. Current routing belongs in [Current Production Status](Current-Production-Status), never in this textbook page.

## The human orchestrator

The human remains the decision owner. The orchestrator must:

1. define the decision and acceptable risk;
2. disclose material context the agents cannot infer;
3. distinguish evidence from model-generated interpretation;
4. resolve or preserve disagreement without averaging it away;
5. decide whether to proceed, test, revise, pause, or stop; and
6. remain accountable for the action taken.

AI review is decision support. It is not legal advice, professional certification, or transferred accountability.

## What a trustworthy result contains

A useful Genesis result is an evidence packet, not just a score. It should contain:

- the original question and material constraints;
- each seat’s findings and provenance;
- assumptions, citations, and confidence limits;
- objections and vetoes without silent deletion;
- stage/provider failure information;
- a synthesis that states what is complete and what is not; and
- human-owned next actions and stop conditions.

When a stage does not produce real inference, its score, confidence, verdict, and derived counts must not be presented as if they exist. Successful stages may be preserved, but the overall result must be marked incomplete and routed for human review. This is the method’s **fail-closed completeness rule**.

## A practical worksheet

Use these prompts before accepting a recommendation:

### Frame

- What exact decision follows from this analysis?
- Who benefits, who bears risk, and who can refuse?
- What would make the result unusable?

### Explore

- What are the strongest alternative explanations or designs?
- Which claims rely on market, technical, or behavioral assumptions?
- What evidence would falsify the preferred path?

### Challenge

- Can the system be abused, coerced, or made to overclaim?
- Are data collection, retention, deletion, and provider processing understood?
- Does any seat disagree strongly enough to stop or narrow the proposal?

### Synthesize and iterate

- Which findings are observed facts, which are inferences, and which are plans?
- What remains unknown?
- Who owns the next test, by when, and what is the stop condition?

## Claims this method does not make

- Multiple agents do not guarantee truth.
- A high score does not erase a named risk or veto.
- Model agreement is not independent validation when failure sources are correlated.
- A citation is not evidence that the cited source supports the claim.
- Production availability is not evidence of effectiveness.
- Engagement metrics are not proof that the method improves decisions.

Those limits are part of Genesis, not exceptions to it.

## Further reading

- [Genesis v2.0 White Paper — DOI 10.5281/zenodo.17972751](https://doi.org/10.5281/zenodo.17972751)
- [Architecture](Architecture) — how the method maps to system boundaries
- [Trust and Safety](Trust-and-Safety) — standing safety commitments and disclosure rules
- [Operations Playbook](Operations-Playbook) — how release evidence is produced
- [Public Statements](Public-Statements) — the append-only trust ledger
