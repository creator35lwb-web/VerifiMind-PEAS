# CS Agent: Severity Rating Framework

**Version:** 1.0
**Date:** February 22, 2026
**Author:** RNA (Claude Code) — based on XV discovery analysis
**Applies to:** CS Security Agent within VerifiMind-PEAS RefleXion Trinity
**Genesis Prompt Version:** v3.1
**Reference:** `discovery/2026-02/20260221_XV_claude_code_security_cs_agent_upgrade.md`

---

## Overview

This framework defines how CS Agent assigns severity levels to security findings. It provides consistent, repeatable criteria that reduce subjectivity and enable prioritized remediation.

---

## Severity Levels

### CRITICAL

**Definition:** Vulnerability that can be immediately exploited to compromise the system, expose credentials, or breach data.

**Criteria (must meet ALL):**
- Remotely exploitable without authentication
- Impact includes one or more: full system access, credential exposure, mass data breach
- No effective mitigating controls in place
- Known exploit technique or trivially discoverable

**Examples:**
- Hardcoded API keys or secrets in source code
- Unauthenticated admin endpoints
- SQL injection in login/authentication flows
- Remote code execution via unsanitized input
- Exposed database with no access controls

**Response:** Immediate fix required. Do not deploy until resolved.

**Confidence Threshold:** Only assign CRITICAL with confidence ≥ 85%.

---

### HIGH

**Definition:** Significant vulnerability that is likely exploitable and would result in meaningful damage.

**Criteria (must meet MOST):**
- Exploitable with minimal effort or basic tooling
- Impact includes: partial system access, sensitive data exposure, privilege escalation
- Limited mitigating controls that can be bypassed
- Affects production-facing components

**Examples:**
- Cross-site scripting (XSS) in user-facing pages
- Insecure direct object references (IDOR)
- Missing authentication on sensitive API endpoints
- SSRF allowing access to internal services
- Weak cryptographic implementations

**Response:** Fix within 24 hours. May require hotfix deployment.

**Confidence Threshold:** Assign HIGH with confidence ≥ 70%.

---

### MEDIUM

**Definition:** Moderate risk vulnerability that requires specific conditions to exploit.

**Criteria (must meet SOME):**
- Requires authentication or specific setup to exploit
- Impact is limited in scope (affects subset of data or functionality)
- Some mitigating controls exist but are incomplete
- Exploitation requires chained vulnerabilities or social engineering

**Examples:**
- CSRF on non-critical forms
- Information disclosure in error messages
- Missing rate limiting on non-critical endpoints
- Overly permissive CORS configuration
- Session fixation with authenticated access

**Response:** Fix within 1 week. Include in next planned release.

**Confidence Threshold:** Assign MEDIUM with confidence ≥ 60%.

---

### LOW

**Definition:** Minor issue representing a defense-in-depth improvement opportunity.

**Criteria:**
- Requires significant effort, insider access, or unlikely conditions to exploit
- Minimal impact even if exploited
- Strong mitigating controls already exist
- More of a best-practice recommendation than active threat

**Examples:**
- Missing security headers (non-critical)
- Verbose logging of non-sensitive data
- Outdated dependencies with no known exploits
- Missing `HttpOnly` flag on non-session cookies
- Suboptimal but functional access controls

**Response:** Address in next release cycle. No urgency.

**Confidence Threshold:** Any confidence level acceptable.

---

## Scoring Matrix

Use this matrix when the severity level isn't immediately clear:

| | **High Impact** | **Medium Impact** | **Low Impact** |
|---|---|---|---|
| **Easy to Exploit** | CRITICAL | HIGH | MEDIUM |
| **Moderate Effort** | HIGH | MEDIUM | LOW |
| **Difficult to Exploit** | MEDIUM | LOW | LOW |

**Impact** = What could an attacker achieve?
**Exploitability** = How easy is it to achieve?

---

## Confidence Scoring

Confidence reflects CS Agent's certainty that the finding is genuine and correctly rated.

| Range | Label | Meaning | Action |
|-------|-------|---------|--------|
| 90-100% | Very High | Clear vulnerability with demonstrable impact | Present as-is |
| 70-89% | High | Likely vulnerability, some mitigating factors possible | Present with caveats |
| 50-69% | Moderate | Possible vulnerability, significant uncertainty | Flag for human review |
| Below 50% | Low | Uncertain — may be false positive | Present as "needs investigation" |

### Calibration Guidelines

- If you cannot construct a realistic attack scenario → reduce confidence by 20%
- If the runtime environment has built-in protections → reduce confidence by 15%
- If the finding matches a known CVE → increase confidence by 15%
- If the finding is in dead/unreachable code → reduce confidence by 30%
- If multiple independent indicators confirm the finding → increase confidence by 10%

---

## Finding Documentation Template

Each severity-rated finding must include:

```markdown
### Finding #{ID}: {Short Title}

**Severity:** {CRITICAL | HIGH | MEDIUM | LOW}
**Confidence:** {0-100%}
**Category:** {Prompt Injection | SQL Injection | XSS | SSRF | File/Command Injection | API Security}
**Location:** {file:line or endpoint}

**Description:**
{What was found and why it matters}

**Impact Assessment:**
{What could an attacker achieve by exploiting this?}

**Exploitability Assessment:**
{How easy is it to exploit? What preconditions are needed?}

**Self-Examination Notes:**
{How was this finding verified? What was checked to rule out false positive?}

**Recommended Fix:**
{Specific, actionable remediation with code example if applicable}

**Fix Priority:** {Immediate | Within 24h | Within 1 week | Next release}
```

---

## Integration with VerifiMind-PEAS

### Interaction with X Intelligent Scores
- X Agent provides innovation scores (0-10)
- CS Agent severity ratings are independent — a high-innovation concept can still have CRITICAL security findings
- Both scores are presented to the human reviewer

### Interaction with Z Guardian Verdicts
- Z Guardian may veto a concept on ethical grounds
- CS Agent severity ratings complement Z Guardian's assessment
- If Z vetoes AND CS finds CRITICAL issues → strongest signal to reject
- If Z approves AND CS finds only LOW issues → strongest signal to proceed

### Aggregation for Trinity Report
The Trinity synthesis uses CS severity ratings to calculate overall security score:
- 0 CRITICAL + 0 HIGH = Security Score 8-10
- 0 CRITICAL + 1-2 HIGH = Security Score 6-7
- 1+ CRITICAL OR 3+ HIGH = Security Score 3-5
- Multiple CRITICAL = Security Score 1-2

---

## Changelog

### v1.0 (2026-02-22)
- Initial framework creation
- CRITICAL / HIGH / MEDIUM / LOW definitions with examples
- Scoring matrix, confidence calibration, finding template
- Integration guidelines with X and Z agents

---

**Status:** Active
**Maintained by:** FLYWHEEL TEAM
**Protocol:** MACP v2.0
**YSenseAI Ecosystem**
