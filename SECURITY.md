# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in VerifiMind-PEAS, please report it responsibly.

**Contact:** alton@ysenseai.org

**Please DO NOT:**
- Open a public GitHub issue for security vulnerabilities
- Share vulnerability details publicly before they are fixed

**Please DO:**
- Email the security contact with a detailed description
- Allow reasonable time for the issue to be addressed
- Include steps to reproduce the vulnerability if possible

## Security Practices

- All API keys and credentials are managed through environment variables
- GCP infrastructure details are kept in private documentation
- The Dual-Repo Protocol separates internal development artifacts from public code
- CI/CD pipeline includes Bandit and Safety security scanning
- Regular security audits are conducted by the FLYWHEEL TEAM

## Supported Versions

| Version | Supported |
|---------|-----------|
| v0.4.0  | ✅ Current |
| v0.3.x  | ⚠️ Security fixes only |
| < v0.3  | ❌ No longer supported |

## Acknowledgments

Security scanning powered by the FLYWHEEL TEAM multi-agent validation protocol.
