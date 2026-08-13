# AI Council and Public Runtime

“AI Council” is used in two different contexts. Keeping them separate prevents
methodology language from becoming a false runtime claim.

## Scope 1: the public MCP runtime

The hosted Trinity is a three-stage pipeline:

| Stage | Runtime role | What it contributes |
|---|---|---|
| **X — Innovation & Strategy** | explores novelty, alternatives, positioning, assumptions, and execution | an innovation/strategy analysis |
| **Z — Ethics & Compliance** | examines affected people, rights, governance, frameworks, and ethical red lines | an ethics-oriented analysis and possible veto signal |
| **CS — Security** | examines threats, vulnerabilities, misuse, data, and system integrity | a security analysis and questions for testing |

`run_full_trinity` executes X → Z → CS. Z can receive completed trustworthy X
reasoning; CS can receive completed trustworthy X and Z reasoning. A failed
stage is not fabricated, and untrusted output is not propagated as genuine
reasoning.

The public runtime does **not** execute a fourth Y stage. Historical and internal
methodology diagrams that include Y describe a broader ideation role, not the
public MCP tool chain.

## Scope 2: the internal human-directed council

The FLYWHEEL TEAM uses a broader, evolving set of human and AI roles for
research, engineering, operations, review, and synthesis. Those roles may
include identifiers such as Y, L, T, RNA, XV, AY, or AZ.

That internal council is:

- an operating and governance practice, not a fixed public API;
- allowed to change models, platforms, and role assignments;
- coordinated through controlled project repositories and review gates;
- distinct from the X/Z/CS schemas exposed by the public MCP server.

The public coordination tools are temporarily unavailable. They do not expose
the internal council, a shared anonymous namespace, pending work, or team
status. See [Public Statements](Public-Statements).

## Lens, provider, and model are different things

An agent lens defines the question being asked. A provider hosts inference. A
model produces a response. They must not be treated as interchangeable.

For example:

- X remains the innovation lens even if its provider changes.
- Two seats can have different prompts but still use the same model family.
- “Multi-agent” does not prove “multi-model.”
- Configured diversity does not prove the returned stages actually completed
  with the intended routes.

The current hosted provider/model assignment is volatile. Read it from
[`/health`](https://verifimind.ysenseai.org/health) and verify returned
stage metadata for the specific run. The service currently supports a six-
provider remote BYOK catalogue plus caller-managed local Ollama; see the
[BYOK Guide](BYOK-Guide).

## Human authority

The council is designed to improve scrutiny, not remove accountability. The
human reviewer must:

1. define the decision and its constraints;
2. decide which evidence and expertise are required;
3. inspect quality, incompleteness, and disagreements;
4. escalate legal, security, ethical, or domain questions to qualified people;
5. make and own the final decision.

No agent score, recommendation, or veto is a legal certification, formal proof,
or authorization to deploy.

## Epistemic limits

Multiple structured perspectives can surface different failure modes, but the
benefit is an empirical question rather than a guaranteed property. Shared
training data, shared models, correlated prompts, and common blind spots can
produce agreement without independence.

Use the council to generate inspectable claims and tests. Preserve dissent and
unavailable stages. Compare against external evidence and, where consequences
justify it, independent human or technical review.

## Public runtime flow

```text
Human frames the concept and decision
                |
                v
      X: innovation and strategy
                |
                v
        Z: ethics and governance
                |
                v
          CS: security review
                |
                v
Structured result + explicit quality state
                |
                v
Human interpretation and authority
```

Provider and model choices sit underneath each stage and may be changed through
hosted routing or BYOK. They do not change the stable responsibilities above.

## Related pages

- [Genesis Methodology](Genesis-Methodology) — broader human-directed process
- [Architecture](Architecture) — system boundaries
- [MCP Tools Reference](MCP-Tools-Reference) — callable public tools
- [BYOK Guide](BYOK-Guide) — provider selection and routing
- [Current Production Status](Current-Production-Status) — live release facts

---

[← Home](Home)
