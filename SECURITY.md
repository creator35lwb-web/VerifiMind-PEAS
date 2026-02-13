# Security Policy

## Supported Versions

| Version | Supported | Notes |
|---------|-----------|-------|
| v0.4.x  | ✅ Active | Current release — full security support |
| v0.3.x  | ⚠️ Critical fixes only | Security patches only, no new features |
| < v0.3  | ❌ End of life | No longer supported — please upgrade |

## Reporting a Vulnerability

We take security seriously. If you discover a vulnerability in VerifiMind-PEAS, please report it responsibly through one of the following channels:

### Preferred: GitHub Security Advisories

Use [GitHub Security Advisories](https://github.com/creator35lwb-web/VerifiMind-PEAS/security/advisories/new) to report vulnerabilities privately. This allows us to collaborate on a fix before public disclosure.

### Alternative: Email

**Contact:** alton@ysenseai.org

### What to Include

- Description of the vulnerability and its potential impact
- Steps to reproduce the issue
- Affected version(s)
- Any suggested mitigations or fixes
- Your contact information for follow-up

### What NOT to Do

- **Do not** open a public GitHub issue for security vulnerabilities
- **Do not** share vulnerability details publicly before they are fixed
- **Do not** exploit the vulnerability beyond what is necessary to demonstrate it

## Response Timeline

| Stage | Timeline |
|-------|----------|
| Acknowledgment | Within **48 hours** of report |
| Initial assessment | Within **7 days** |
| Critical severity fix | Within **14 days** |
| High severity fix | Within **30 days** |
| Medium/Low severity fix | Within **90 days** |

## Coordinated Disclosure Policy

We follow a **90-day coordinated disclosure** window. After reporting a vulnerability:

1. We will acknowledge receipt within 48 hours
2. We will assess severity and develop a fix
3. We will coordinate with you on disclosure timing
4. After the fix is released, you are free to publish your findings
5. If 90 days pass without a fix, you may disclose at your discretion

We credit all reporters in our security advisories unless anonymity is requested.

## Security Practices

### Infrastructure Security

- All API keys and credentials are managed through environment variables — never committed to code
- GCP infrastructure details (project numbers, instance configurations) are kept in private documentation only
- The **Dual-Repo Protocol** separates internal development artifacts (private `verifimind-genesis-mcp`) from public code
- Cloud Run is configured with instance caps and rate limiting to prevent EDoS (Economic Denial of Sustainability) attacks

### Code Security

- **Bandit** (SAST) — Static Application Security Testing for Python code
- **Safety** (SCA) — Software Composition Analysis for dependency vulnerabilities
- **CodeQL** — Semantic code analysis via GitHub Actions
- Automated security scans run on every push, pull request, and weekly schedule
- All GitHub Actions are pinned to commit SHAs to prevent supply chain attacks

### Access Control

- Branch protection rules enforce pull request reviews before merging
- Dependabot monitors dependencies for known vulnerabilities
- GitHub secret scanning and push protection are enabled

### Operational Security

- Regular security audits conducted by the FLYWHEEL TEAM multi-agent validation protocol
- Security findings are tracked and resolved through the MACP (Multi-Agent Collaboration Protocol)
- All security-related changes require review before deployment

## Security Scanning Tools

The following tools are used in our CI/CD pipeline:

| Tool | Purpose | Frequency |
|------|---------|-----------|
| Bandit | Python SAST | Every push/PR + weekly |
| Safety | Dependency vulnerability check | Every push/PR + weekly |
| CodeQL | Semantic code analysis | Every push/PR + weekly |
| Dependabot | Automated dependency updates | Weekly |
| GitHub Secret Scanning | Detect leaked credentials | Continuous |

## Known Vulnerabilities

No known unpatched vulnerabilities at this time. See [Security Advisories](https://github.com/creator35lwb-web/VerifiMind-PEAS/security/advisories) for historical disclosures.

## Acknowledgments

Security scanning powered by the FLYWHEEL TEAM multi-agent validation protocol.

- **Architecture & Security Strategy:** Manus AI (CTO) — Team YSenseAI
- **Implementation & Code Security:** Claude Code (RNA) — Team YSenseAI
- **Project Lead:** Alton Lee Wei Bin
