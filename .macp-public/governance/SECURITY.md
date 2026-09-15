# Security Policy

## Supported Versions

| Version | Supported | Notes |
|---------|-----------|-------|
| v0.5.x  | ✅ Maintained | Current release line; security fixes are prioritized |
| v0.4.x  | ⚠️ Limited | Critical fixes considered case by case |
| < v0.4  | ❌ Not maintained | Please upgrade before requesting a fix |

## Reporting a Vulnerability

Please report suspected vulnerabilities privately. Do not open a public issue,
pull request, discussion, or social-media thread containing vulnerability
details before a mitigation is available.

### Private reporting channel

Email **alton@ysenseai.org** with the subject `VerifiMind security report`.

If GitHub displays a **Report a vulnerability** button on this repository's
Security tab, that private GitHub form is also supported. The presence of that
button—not a link in this document—is the authority for whether GitHub Private
Vulnerability Reporting is currently enabled.

Please include, when possible:

- A description of the issue and its potential impact
- The affected version, commit, endpoint, or component
- Minimal reproduction steps or a proof of concept
- Suggested mitigations
- Your preferred contact details and disclosure expectations

Please do not:

- Access, modify, retain, or disclose data that is not yours
- Degrade the service or exceed the minimum testing needed to demonstrate the issue
- Publish credentials, live exploit instructions, private infrastructure
  evidence, or unresolved vulnerability details

## Response Targets

These are good-faith operational targets, not contractual service-level
agreements. Complex reports may require more time.

| Stage | Target |
|-------|--------|
| Acknowledgment | Within 48 hours |
| Initial assessment | Within 7 days |
| Critical-severity mitigation | Within 14 days |
| High-severity mitigation | Within 30 days |
| Medium/low-severity mitigation | Within 90 days |

## Coordinated Disclosure

We normally work within a 90-day coordinated-disclosure window, adjusted for
active exploitation, impact, fix complexity, and reporter needs. We will aim to
agree on disclosure timing, credit reporters who want attribution, and publish
an advisory after affected users can protect themselves.

Source design, post-fix regression tests, and non-sensitive lessons can be
public. Before mitigation, exploit mechanics, live targets, credentials, IAM
details, raw logs, and staging receipts belong in the private reporting channel.
A public draft pull request is public disclosure; marking it "draft" does not
make its contents private.

## Security Practices and Their Boundaries

### Secrets and infrastructure

- Credentials should be stored in an appropriate secret manager or protected
  environment, not in source, workflow output, issue text, or pull-request text.
- Non-secret identifiers such as public service URLs and release revisions may
  be public. Credentials, sensitive IAM topology, raw operational evidence, and
  incident details remain private until disclosure is safe.
- The private/public repository split supports provenance and review. It is not
  by itself a security boundary and does not make a public branch or pull
  request private.

### Source and dependency checks

- **Bandit** performs Python static analysis.
- **pip-audit** checks Python dependencies against public vulnerability data.
- **CodeQL** performs semantic analysis.
- GitHub secret scanning, push protection, and Dependabot provide additional
  repository-level signals when enabled in repository settings.

The security workflow runs on pushes to `main`, pull requests targeting `main`,
and a weekly schedule. A scanner invocation must return success itself; artifact
upload and summary steps do not convert a scanner failure into a pass.

All third-party and GitHub-authored Actions referenced by the current workflow
files are pinned to full commit SHAs. Repository settings—not this document—are
authoritative for whether SHA pinning or a particular status check is enforced.

### Reviews and required checks

`CODEOWNERS` requests review; it does not prove that an independent approval
occurred. Likewise, a green CI check is not necessarily a required check.
GitHub's live ruleset and branch settings are the authority for merge
enforcement. Security-sensitive changes are expected to carry documented human
review before deployment even when the repository cannot technically require an
independent reviewer.

### Operational review

The FLYWHEEL TEAM validation process may be used to review security-sensitive
changes. Multi-agent agreement is supporting evidence, not a substitute for
bounded authorization, reproducible tests, human release authority, or private
incident handling.

## Security Check Frequency

| Check | Purpose | Repository workflow frequency |
|-------|---------|-------------------------------|
| Bandit | Python SAST | Every push to `main`, every PR to `main`, weekly |
| pip-audit | Python dependency audit | Every push to `main`, every PR to `main`, weekly |
| CodeQL | Semantic analysis | Every push to `main`, every PR to `main`, weekly |
| Dependabot | Dependency update and advisory signal | As configured in GitHub |
| GitHub secret scanning | Credential detection | Continuous when enabled |

## Published Advisories

We do not use this file to assert that no unresolved vulnerability exists.
Resolved and coordinated disclosures appear in
[GitHub Security Advisories](https://github.com/creator35lwb-web/VerifiMind-PEAS/security/advisories).
Please send unresolved findings through a private reporting channel.

## Acknowledgments

Security review is supported by the YSenseAI FLYWHEEL TEAM validation process.
Final publication, deployment, and disclosure authority remains with the human
project maintainer.
