# CS Agent: Multi-Stage Security Verification Protocol

**Version:** 1.0
**Date:** February 22, 2026
**Author:** RNA (Claude Code) — based on XV discovery analysis
**Applies to:** CS Security Agent within VerifiMind-PEAS RefleXion Trinity
**Genesis Prompt Version:** v3.1
**Reference:** `discovery/2026-02/20260221_XV_claude_code_security_cs_agent_upgrade.md`

---

## Overview

The Multi-Stage Security Verification Protocol formalizes CS Agent's security assessment workflow into 4 explicit, sequential stages. This protocol is inspired by Anthropic's Claude Code Security methodology and aligned with the VerifiMind-PEAS X→Z→CS validation chain.

### Why This Protocol Exists

Before v3.1, CS Agent had implicit multi-stage analysis but lacked:
- Explicit self-examination requirements
- Formalized false positive filtering
- Structured severity rating with confidence scores
- Mandatory human review checkpoints

This protocol activates capabilities that were already present in the foundation code through workflow formalization.

### Philosophical Alignment

```
Claude Code Security:  Detection → Self-Examination → Proof/Disproof → False Positive Filtering → Severity Rating → Human Approval
VerifiMind-PEAS:       X (Research) → Z (Guardian Validation) → CS (Security Check) → Human Review → Execution
CS Agent v3.1:         Stage 1 (Detect) → Stage 2 (Self-Examine) → Stage 3 (Rate Severity) → Stage 4 (Human Review)
```

The pattern is identical. Multi-stage verification with human oversight is the correct methodology for responsible AI security assessment.

---

## Stage 1: Initial Detection

### Purpose
Cast a wide net to identify ALL potential security issues before filtering.

### Actions
1. **Scan code and architecture** against the 6 threat detection rule categories:
   - Prompt Injection
   - SQL/NoSQL Injection
   - XSS (Cross-Site Scripting)
   - SSRF (Server-Side Request Forgery)
   - File/Command Injection
   - API Security

2. **Trace data flow** through systems:
   - Identify trust boundaries
   - Map input sources to processing to output
   - Track where user-controlled data reaches sensitive operations

3. **Map attack surfaces:**
   - External-facing endpoints
   - Authentication/authorization boundaries
   - Third-party integrations
   - Data storage and retrieval paths

4. **Document raw findings:**
   - Record EVERY potential issue found
   - No filtering at this stage — capture everything
   - Note the detection rule that triggered each finding

### Output
A complete list of raw findings with:
- Finding ID (sequential)
- Category (which of the 6 threat types)
- Location (file, line, endpoint)
- Description (what was detected)
- Detection rule that triggered it

---

## Stage 2: Self-Examination (MANDATORY)

### Purpose
Reduce false positives by rigorously re-examining each finding. This is the stage that differentiates systematic security analysis from pattern-matching alarms.

### Actions

1. **Re-examine each finding** with fresh perspective:
   - Step back from the initial detection context
   - Consider the finding in isolation AND in system context
   - Ask: "Would a senior security engineer flag this?"

2. **Attempt to PROVE** each finding is genuine:
   - Can you construct a realistic attack scenario?
   - What specific impact would exploitation have?
   - Is there a known CVE or attack pattern that applies?

3. **Attempt to DISPROVE** each finding:
   - Are there existing security controls that mitigate this?
   - Does the runtime environment prevent exploitation?
   - Is the affected component actually reachable by attackers?
   - Would exploitation require unrealistic preconditions?

4. **Apply False Positive Filtering Checklist:**

   | Question | If YES → | If NO → |
   |----------|----------|---------|
   | Is this a real vulnerability or a coding style issue? | Keep | Filter out |
   | Does the runtime environment mitigate this risk? | Filter out | Keep |
   | Are there existing security controls that address this? | Filter out | Keep |
   | Would exploiting this require unrealistic preconditions? | Filter out | Keep |
   | Is the affected component actually reachable by attackers? | Keep | Filter out |

5. **Assign confidence scores:**
   - 90-100%: High confidence — clear vulnerability with demonstrable impact
   - 70-89%: Moderate confidence — likely vulnerability, some mitigating factors
   - Below 70%: Low confidence — flag for human review, do not auto-categorize

### Output
A filtered list with:
- Verified findings (passed self-examination)
- Filtered findings (removed with reasoning)
- Confidence score for each verified finding
- Self-examination notes documenting assumptions challenged

---

## Stage 3: Severity Rating

### Purpose
Prioritize verified findings so human reviewers can focus on what matters most.

### Severity Levels

| Level | Criteria | Impact | Exploitability | Response Time |
|-------|----------|--------|----------------|---------------|
| **CRITICAL** | Immediate exploitation possible | System compromise, data breach, credential exposure | Remote, no auth required | Immediate |
| **HIGH** | Significant vulnerability | Partial access, sensitive data exposure | Minimal effort required | Within 24 hours |
| **MEDIUM** | Moderate risk | Limited exposure, functionality abuse | Requires auth or specific setup | Within 1 week |
| **LOW** | Defense-in-depth improvement | Minimal impact, information disclosure | Significant effort or insider access | Next release cycle |

### Rating Process

For each verified finding, document:

1. **Severity Level** — One of CRITICAL / HIGH / MEDIUM / LOW
2. **Justification** — Why this severity level (not higher or lower)
3. **Confidence Score** — From Stage 2 (0-100%)
4. **Impact Assessment** — What could an attacker achieve?
5. **Exploitability Assessment** — How easy is it to exploit?
6. **Recommended Fix** — Specific, actionable remediation
7. **Fix Priority** — Immediate / Within 24h / Within 1 week / Next release

### Sorting
Present findings sorted by severity (CRITICAL first), then by confidence score (highest first within each severity level).

---

## Stage 4: Human Review Checkpoint

### Purpose
Ensure human oversight before any action is taken. CS Agent provides analysis; humans make decisions.

### Requirements

1. **Present ALL verified findings** — never hide or suppress findings
2. **Clear explanations** — no jargon without definition, no assumptions about reviewer's expertise
3. **Actionable recommendations** — each finding includes a specific suggested fix
4. **Transparency flags:**
   - Findings where confidence is below 85% (needs human judgment)
   - Findings that conflict with Z Guardian's ethical assessment
   - Findings where CS Agent is uncertain about severity level
5. **NEVER auto-apply fixes** — always wait for explicit human approval

### Human Review Actions
The human reviewer can:
- **Accept** a finding and approve the fix
- **Reject** a finding as false positive (feedback loop for CS Agent learning)
- **Escalate** a finding for deeper investigation
- **Defer** a finding to a later release cycle
- **Override** the severity level with justification

---

## Integration with VerifiMind-PEAS Architecture

### Position in X→Z→CS Chain

```
X Intelligent (Research/Innovation)
    ↓ provides analysis and claims
Z Guardian (Ethics/Validation)
    ↓ validates ethics, may veto
CS Security (Security + Socratic Challenge)
    ↓ applies 4-stage verification protocol
    ↓ provides severity-rated findings + Socratic questions
Human Orchestrator (Final Review)
    ↓ approves, rejects, or escalates
Execution
```

### Interaction with Z Guardian

- CS Agent receives Z Guardian's reasoning as `prior_reasoning`
- If Z Guardian triggered a veto, CS Agent acknowledges it but still completes security assessment
- CS Agent flags any security findings that conflict with Z Guardian's ethical assessment
- Z Protocol veto power is respected — CS Agent cannot override a Z veto

### Socratic Challenge Integration

The Socratic Challenge Framework (v3.0) continues to operate alongside the Multi-Stage Verification Protocol:
- Socratic questions are generated AFTER the 4-stage process
- Questions target specific claims, metrics, or assumptions from the subject being validated
- Minimum 3 deep questions per validation (unchanged from v3.0)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| False Positive Rate | < 20% | Findings filtered in Stage 2 / Total raw findings |
| Self-Examination Completion | 100% | Stage 2 must run for every assessment |
| Severity Accuracy | > 80% | Human agreement with CS Agent severity ratings |
| Human Review Compliance | 100% | No auto-applied fixes |
| Confidence Calibration | Within 10% | CS Agent's confidence vs actual accuracy |

---

## Changelog

### v1.0 (2026-02-22)
- Initial protocol creation
- Based on XV discovery analysis of Claude Code Security methodology
- Aligned with Genesis Master Prompt v3.1 upgrade
- 4-stage workflow formalized: Detection → Self-Examination → Severity Rating → Human Review

---

**Status:** Active
**Maintained by:** FLYWHEEL TEAM
**Protocol:** MACP v2.0
**YSenseAI Ecosystem**
