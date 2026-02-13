# Contributing to VerifiMind-PEAS

Thank you for your interest in contributing to VerifiMind-PEAS! This document provides guidelines and information to help you contribute effectively.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Security](#security)
- [Early Adopter Program](#early-adopter-program)
- [Resources](#resources)

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](docs/CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

1. **Fork** the repository to your GitHub account
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/VerifiMind-PEAS.git
   cd VerifiMind-PEAS
   ```
3. **Set up** the development environment following [SETUP.md](SETUP.md)
4. **Create a branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## How to Contribute

### Reporting Bugs

- Search [existing issues](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues) first to avoid duplicates
- Use the **Bug Report** issue template when creating a new issue
- Include steps to reproduce, expected behavior, and actual behavior
- Include your environment details (OS, Python version, etc.)

### Suggesting Enhancements

- Use the **Feature Request** issue template
- Clearly describe the problem your enhancement would solve
- Explain how your suggestion aligns with the Genesis Methodology

### Submitting Code Changes

1. Ensure your change addresses an existing issue or create one first
2. Follow the [Development Workflow](#development-workflow) below
3. Write or update tests for your changes
4. Update documentation as needed
5. Submit a pull request using the PR template

## Development Workflow

### Branch Naming Convention

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/description` | `feature/add-new-agent` |
| Bug fix | `fix/description` | `fix/rate-limiter-bypass` |
| Documentation | `docs/description` | `docs/update-api-guide` |
| Security | `security/description` | `security/patch-cve-xxxx` |

### Commit Message Format

Use clear, descriptive commit messages:

```
type(scope): brief description

Detailed explanation if needed.

Refs: #issue-number
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `security`, `ci`, `deps`

### Pull Request Process

1. Ensure all tests pass locally before submitting
2. Fill out the PR template completely
3. Link the related issue(s)
4. Request review from the maintainers
5. Address any review feedback promptly
6. PRs require at least one approval before merging

## Code Standards

### Python (MCP Server)

- Follow **PEP 8** style guidelines
- Use type hints for function signatures
- Maximum line length: 120 characters
- Add docstrings to all public functions and classes
- Run `bandit` for security checks before submitting

### Testing

- Add tests for all new features and bug fixes
- Maintain or improve code coverage
- Integration tests should use mock services, not production endpoints
- Never include real API keys or credentials in test files

### Documentation

- Update relevant documentation when changing functionality
- Use clear, concise language
- Include code examples where appropriate

## Security

**Do NOT report security vulnerabilities through public issues.** Please read our [Security Policy](SECURITY.md) for responsible disclosure procedures.

When contributing code, please ensure:

- No API keys, credentials, or secrets are committed
- No internal infrastructure details (project numbers, IP addresses) are exposed
- Dependencies are from trusted sources
- Input validation is implemented for user-facing features

## Early Adopter Program

Join our Early Adopter Program for direct collaboration with the FLYWHEEL TEAM.

**Website:** [https://verifimind.io](https://verifimind.io)
**Contact:** alton@ysenseai.org

## Resources

| Resource | Description |
|----------|-------------|
| [README.md](README.md) | Project overview and methodology |
| [QUICK_START.md](QUICK_START.md) | Quick start guide |
| [SETUP.md](SETUP.md) | Development setup instructions |
| [SECURITY.md](SECURITY.md) | Security policy and reporting |
| [LICENSE](LICENSE) | MIT License |
| [Code of Conduct](docs/CODE_OF_CONDUCT.md) | Community guidelines |
| [Landing Page](https://verifimind.io) | Official project website |

## Questions?

If you have questions, please:

1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues)
3. Join the [Discussions](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions)
4. Open a [new issue](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues/new)
5. Email: alton@ysenseai.org

---

**Thank you for contributing to the future of ethical AI validation!**
