<div align="center">

<img src="https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/docs/assets/branding/VerifiMind-PEAS-Logo-transparent.png?raw=true" alt="VerifiMind PEAS" width="150"/>

# VerifiMind PEAS Wiki

**Structured multi-LLM critique with human final authority**

VerifiMind PEAS is an MCP server that reviews a concept through three specialized
perspectives: innovation, ethics, and security. It helps people find questions,
risks, and trade-offs before they build.

[Connect](Installation) · [Tool reference](MCP-Tools-Reference) · [Current production status](Current-Production-Status) · [Public statements](Public-Statements)

</div>

---

> **Status boundary:** This Wiki teaches the durable concepts and operating
> workflow. Runtime version, model IDs, routing, protocol version, tool
> availability, and deployment evidence change independently. Check
> [`/health`](https://verifimind.ysenseai.org/health),
> [`/setup`](https://verifimind.ysenseai.org/setup), the
> [live server card](https://verifimind.ysenseai.org/.well-known/mcp/server-card.json),
> and [Current Production Status](Current-Production-Status) before relying on
> an operational fact.

## Start here

| Goal | Page |
|---|---|
| Connect an MCP client | [Installation](Installation) |
| Understand what each callable tool does | [MCP Tools Reference](MCP-Tools-Reference) |
| Use your own model provider | [BYOK Guide](BYOK-Guide) |
| Understand the public X → Z → CS runtime | [AI Council](AI-Council) |
| Learn the broader human-directed methodology | [Genesis Methodology](Genesis-Methodology) |
| Check what is live now | [Current Production Status](Current-Production-Status) |
| Review incidents, limitations, and exact release evidence | [Public Statements](Public-Statements) |

## The stable mental model

The public Trinity runtime has three sequential analysis stages:

| Stage | Lens | Core question |
|---|---|---|
| **X — Innovation & Strategy** | novelty, alternatives, market and execution | What is promising, weak, or already known? |
| **Z — Ethics & Compliance** | affected people, rights, governance and ethical red lines | What could cause harm or require human/legal review? |
| **CS — Security** | threats, misuse, data and system integrity | What can break, and what should be tested or contained? |

`run_full_trinity` executes X → Z → CS. Later stages receive only trustworthy
reasoning from earlier completed stages. The service then returns a structured
assessment for a human to interpret.

The human remains responsible for scope, evidence, trade-offs, and the final
decision. A tool recommendation is an input to judgment, not delegated
authority.

## What the service does not claim

- It is not formal verification or mathematical proof.
- It is not legal, regulatory, medical, financial, or security certification.
- It is not exhaustive; untested risks may remain.
- Multiple seats do not guarantee independent models or providers. Check the
  live routing record for the run you are evaluating.
- A high score is not permission to ignore findings, degraded stages, or human
  review.

## Current availability contract

The current production contract defines **13 tools**:

- **8 active:** four Trinity tools and four built-in template-reading tools.
- **5 temporarily unavailable:** two custom-template mutation tools and three
  coordination tools.

The unavailable tools remain defined for schema stability but return explicit
maintenance denials. They do not read, write, or reveal a shared coordination
namespace. Their unavailability is security containment, not a paywall.

Availability is operational state. Verify it from
[`/health`](https://verifimind.ysenseai.org/health) rather than inferring it
from the pricing pledge or an old release note.

All active tools remain free under the
[Core Tools Always Free pledge](https://github.com/creator35lwb-web/VerifiMind-PEAS#core-tools-always-free-pledge).
Separate professional services, if offered, do not change tool availability.

## Quick start

Use the hosted MCP endpoint with streamable HTTP:

```bash
claude mcp add -s user verifimind -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/
```

For a native streamable-HTTP client:

```json
{
  "servers": {
    "verifimind": {
      "url": "https://verifimind.ysenseai.org/mcp/",
      "transport": "streamable-http"
    }
  }
}
```

Then ask the client:

> Use `run_full_trinity` to review this concept. Preserve uncertainty, identify
> any unavailable stage, and explain which findings need human follow-up.

See [Installation](Installation) for client-specific setup and verification.

## How to read a result

Treat these as separate facts:

1. **Stage quality:** Was each stage produced by real inference, or marked
   degraded/unavailable?
2. **Findings:** What concerns, vulnerabilities, alternatives, and evidence did
   the completed stages produce?
3. **Aggregate:** Was a combined score or confidence allowed? Incomplete runs
   must not look complete.
4. **Failure trace:** Which stage, provider, model, and normalized failure class
   were reported, and was retry guidance actually applicable?
5. **Human decision:** What remains unverified, and who has authority to decide?

Provider failures can leave a run explicitly incomplete while preserving
trustworthy sibling stages. Never interpret missing output as a clean finding.

## Privacy defaults

`run_full_trinity` defaults `save_to_history` to `false`. If a caller explicitly
opts into aggregate history, production keeps only a bounded, instance-local
set and does not guarantee a fixed time-based retention period. Incomplete
exception runs are not written to that history.

Supplying a UUID is a separate optional choice that may create pseudonymous
usage metadata. Read the live [Privacy Policy](https://verifimind.ysenseai.org/privacy)
and [Terms](https://verifimind.ysenseai.org/terms) before sending personal,
confidential, regulated, or third-party data.

## Learn, operate, verify

### Textbook

- [Genesis Methodology](Genesis-Methodology)
- [Architecture](Architecture)
- [AI Council](AI-Council)

### Operator playbook

- [Installation](Installation)
- [MCP Tools Reference](MCP-Tools-Reference)
- [BYOK Guide](BYOK-Guide)
- [Early Adopter Program](Early-Adopter-Program)

### Evidence and trust

- [Current Production Status](Current-Production-Status)
- [Public Statements](Public-Statements)
- [Statement 001 — Trinity Integrity](Statement-001-Trinity-Integrity)
- [Evaluation Roadmap v1.0](https://verifimind.ysenseai.org/research/evaluation-roadmap)
- [Publications](Publications)

---

VerifiMind PEAS is MIT licensed. Forks and derivatives must use distinct
branding. See the repository [LICENSE](https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/LICENSE).
