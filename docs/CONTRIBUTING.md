# Contributing to VerifiMind

**Welcome!** Thank you for your interest in improving VerifiMind. This document provides guidelines for contributing to the project.

---

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Project Structure](#project-structure)
5. [Coding Standards](#coding-standards)
6. [Making Changes](#making-changes)
7. [Testing](#testing)
8. [Documentation](#documentation)
9. [Pull Request Process](#pull-request-process)
10. [Release Process](#release-process)

---

## 📜 Code of Conduct

### Our Principles

- **Respectful**: Treat all contributors with respect
- **Collaborative**: Work together towards common goals
- **Constructive**: Provide helpful feedback
- **Inclusive**: Welcome diverse perspectives

### Expected Behavior

✅ Be professional and courteous
✅ Focus on what's best for the project
✅ Accept constructive criticism gracefully
✅ Help others learn and grow

### Unacceptable Behavior

❌ Personal attacks or harassment
❌ Discriminatory language or behavior
❌ Publishing others' private information
❌ Trolling or inflammatory comments

---

## 🚀 Getting Started

### Areas for Contribution

1. **Bug Fixes** (See `KNOWN_ISSUES.md`)
   - Critical issues (CRIT-001, CRIT-002)
   - High priority issues
   - Documentation bugs

2. **Feature Development** (See `ROADMAP.md`)
   - Frontend generation
   - Deployment automation
   - Multi-stack support

3. **Documentation**
   - Tutorials and guides
   - API documentation
   - Example applications

4. **Testing**
   - Unit tests
   - Integration tests
   - End-to-end tests

5. **Community**
   - Answer questions
   - Review pull requests
   - Share use cases

### Where to Start

**First-Time Contributors**:
- Look for issues labeled `good-first-issue`
- Fix documentation typos
- Improve error messages
- Add code comments

**Experienced Contributors**:
- Tackle `high-priority` issues
- Implement roadmap features
- Refactor complex code
- Optimize performance

---

## 💻 Development Setup

### Prerequisites

**Required**:
- Python 3.13+
- Git
- Text editor (VS Code recommended)

**For Testing Generated Apps**:
- Node.js 18+
- PostgreSQL 14+
- npm or yarn

### Installation

1. **Clone Repository**
```bash
git clone https://github.com/verifimind/verifimind.git
cd verifimind
```

2. **Create Virtual Environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure Environment**
```bash
cp .env.example .env

# Edit .env with your API keys:
# OPENAI_API_KEY=your-key-here
# ANTHROPIC_API_KEY=your-key-here
```

5. **Verify Installation**
```bash
python verifimind_complete.py --test
```

### Development Tools

**Recommended VS Code Extensions**:
- Python (Microsoft)
- Pylance (type checking)
- Python Docstring Generator
- GitLens

**Code Quality Tools**:
```bash
# Install
pip install black flake8 mypy pytest

# Format code
black .

# Lint
flake8 src/

# Type check
mypy src/

# Test
pytest tests/
```

---

## 📁 Project Structure

```
VerifiMind Project 2025/
├── docs/                    # Documentation
│   ├── PROJECT_OVERVIEW.md
│   ├── DEVELOPMENT_HISTORY.md
│   ├── ARCHITECTURE.md
│   ├── KNOWN_ISSUES.md
│   ├── ROADMAP.md
│   └── CONTRIBUTING.md (this file)
│
├── src/                     # Source code
│   ├── agents/             # Validation agents
│   │   ├── x_intelligent_agent.py
│   │   ├── z_guardian_agent.py
│   │   ├── cs_security_agent.py
│   │   ├── reflection_agent.py
│   │   └── orchestrator.py
│   │
│   ├── generation/         # Code generation
│   │   ├── iterative_generator.py
│   │   ├── core_generator.py
│   │   └── version_tracker.py
│   │
│   └── llm/                # LLM providers
│       └── llm_provider.py
│
├── tests/                  # Test suite (to be created)
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── output/                 # Generated applications
├── verifimind_complete.py  # Main entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md              # Project README
```

---

## 📐 Coding Standards

### Python Style Guide

Follow [PEP 8](https://pep8.org/) with these specifics:

**Formatting**:
```python
# Use Black formatter (line length: 100)
black --line-length 100 src/

# Good
def generate_application(
    spec: AppSpecification,
    output_dir: str = "output"
) -> GeneratedApp:
    """Generate complete application from specification."""
    pass

# Bad
def generate_application(spec: AppSpecification, output_dir: str = "output") -> GeneratedApp:
    pass  # Line too long
```

**Type Hints**:
```python
# Always use type hints
from typing import List, Dict, Optional

def analyze(
    concept: ConceptInput,
    config: Optional[Dict[str, Any]] = None
) -> AgentResult:
    pass
```

**Docstrings**:
```python
def generate_schema(entities: List[Dict]) -> str:
    """Generate PostgreSQL schema from entity list.

    Args:
        entities: List of entity dictionaries with name, fields

    Returns:
        Complete SQL schema as string

    Raises:
        ValueError: If entities list is empty

    Example:
        >>> entities = [{'name': 'user', 'fields': [...]}]
        >>> schema = generate_schema(entities)
    """
    pass
```

**Async/Await**:
```python
# Use async for I/O operations
async def fetch_data(url: str) -> Dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Gather concurrent operations
results = await asyncio.gather(
    agent_x.analyze(concept),
    agent_z.analyze(concept),
    agent_cs.analyze(concept)
)
```

**Error Handling**:
```python
# Specific exceptions, clear messages
try:
    generated_app = await generator.generate(spec)
except LLMAPIError as e:
    logger.error(f"LLM API failed: {e}")
    generated_app = await generator.generate_with_fallback(spec)
except Exception as e:
    logger.error(f"Unexpected error in generation: {e}")
    raise GenerationError(f"Failed to generate app: {e}") from e
```

**Logging**:
```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug("Detailed debug info")
logger.info("General info")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical failure")
```

### JavaScript/Node.js Style Guide

For generated code:

**Formatting**:
- 2 spaces indentation
- Semicolons required
- Single quotes for strings
- Trailing commas

**Modern JavaScript**:
```javascript
// Use const/let, not var
const express = require('express');
let counter = 0;

// Arrow functions
const add = (a, b) => a + b;

// Async/await
const fetchUser = async (id) => {
  const result = await query('SELECT * FROM users WHERE id = $1', [id]);
  return result.rows[0];
};

// Destructuring
const { name, email } = user;
```

---

## 🔧 Making Changes

### Branch Strategy

```
main (stable releases)
  ├── develop (integration branch)
  │   ├── feature/entity-detection
  │   ├── feature/frontend-generation
  │   ├── bugfix/crit-002-timeout
  │   └── docs/api-documentation
```

**Branch Naming**:
- `feature/description` - New features
- `bugfix/issue-id-description` - Bug fixes
- `docs/description` - Documentation
- `refactor/description` - Code refactoring
- `test/description` - Test additions

### Workflow

1. **Create Issue** (if not exists)
   - Describe problem/feature
   - Link to relevant docs (KNOWN_ISSUES.md, ROADMAP.md)
   - Get feedback before starting

2. **Create Branch**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

3. **Make Changes**
   - Write code
   - Add tests
   - Update documentation
   - Test locally

4. **Commit**
```bash
# Stage changes
git add src/agents/new_feature.py

# Commit with clear message
git commit -m "feat: add entity detection with timeout

- Implement fast entity detection using GPT-3.5-turbo
- Add 10-second timeout with retry logic
- Fall back to category templates on failure

Fixes #42 (CRIT-002)"
```

**Commit Message Format**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Test additions
- `chore`: Maintenance

**Examples**:
```
feat(agents): add HIPAA compliance agent

Implements healthcare compliance checking for HIPAA requirements.
Includes PHI detection and encryption validation.

Closes #123

fix(generator): resolve entity detection timeout

Switches to GPT-3.5-turbo for faster generation.
Adds asyncio.timeout(10) wrapper.

Fixes CRIT-002

docs(readme): update installation instructions

Clarifies Python 3.13 requirement and virtual environment setup.
```

5. **Push Branch**
```bash
git push origin feature/your-feature-name
```

6. **Create Pull Request** (see below)

---

## 🧪 Testing

### Test Structure

```
tests/
├── unit/
│   ├── test_agents.py
│   ├── test_generators.py
│   └── test_llm_providers.py
├── integration/
│   ├── test_end_to_end.py
│   └── test_agent_coordination.py
└── fixtures/
    ├── sample_concepts.py
    └── mock_responses.py
```

### Writing Tests

**Unit Tests**:
```python
# tests/unit/test_agents.py
import pytest
from src.agents import XIntelligentAgent, ConceptInput

@pytest.mark.asyncio
async def test_x_agent_validates_valid_concept():
    """Test X Agent approves valid business concept"""
    agent = XIntelligentAgent("x-1", mock_llm, {})

    concept = ConceptInput(
        id="test-1",
        description="Fitness tracking app for runners",
        category="Health & Fitness",
        user_context={},
        session_id="test-session"
    )

    result = await agent.analyze(concept)

    assert result.status == "success"
    assert result.risk_score < 50
    assert len(result.recommendations) > 0
```

**Integration Tests**:
```python
# tests/integration/test_end_to_end.py
@pytest.mark.asyncio
async def test_complete_generation_flow():
    """Test full flow from concept to generated app"""
    verifimind = VerifiMindComplete(config=test_config)

    generated_app, history = await verifimind.create_app_from_idea(
        idea_description="Simple todo list app",
        output_dir="tests/output"
    )

    # Verify generation
    assert generated_app is not None
    assert len(generated_app.backend_code) > 0
    assert 'src/server.js' in generated_app.backend_code

    # Verify iterations
    assert history.total_iterations >= 1
    assert history.final_score > 0
```

**Mocking LLM Calls**:
```python
# tests/fixtures/mock_responses.py
class MockLLMProvider:
    async def generate(self, messages, **kwargs):
        return LLMResponse(
            content="Mock response",
            model="gpt-4",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
            raw_response={}
        )
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_agents.py

# Run with coverage
pytest --cov=src tests/

# Run integration tests only
pytest tests/integration/

# Run and show print statements
pytest -s

# Run in parallel
pytest -n auto
```

### Test Coverage Goals

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: Key workflows covered
- **E2E Tests**: Happy path + critical error cases

---

## 📝 Documentation

### Types of Documentation

1. **Code Documentation**
   - Docstrings (all public functions/classes)
   - Inline comments (complex logic)
   - Type hints (all functions)

2. **API Documentation**
   - Function signatures
   - Parameters and return values
   - Examples

3. **User Documentation**
   - README files
   - Completion guides
   - Tutorials

4. **Developer Documentation**
   - Architecture docs
   - Design decisions
   - Contribution guides

### Documentation Standards

**Docstrings**:
```python
def apply_improvements(
    spec: AppSpecification,
    issues: List[Issue]
) -> AppSpecification:
    """Apply identified issues as improvements to specification.

    Converts reflection agent issues into actionable modifications
    for the next generation iteration.

    Args:
        spec: Current application specification
        issues: List of issues from reflection analysis

    Returns:
        Modified specification with improvements applied

    Raises:
        ValueError: If issues list is empty
        SpecificationError: If spec cannot be modified

    Example:
        >>> issues = reflection.issues
        >>> improved_spec = apply_improvements(spec, issues)
        >>> # improved_spec now includes fixes for identified issues

    Note:
        This function modifies spec in-place and returns it for chaining.

    See Also:
        - ReflectionAgent.analyze() for issue generation
        - IterativeGenerator.generate_with_iterations() for usage
    """
    pass
```

**README Updates**:
- Update README when adding features
- Include usage examples
- Update installation instructions if needed

**Changelog**:
```markdown
# Changelog

## [1.1.0] - 2025-11-15

### Added
- Entity detection with GPT-3.5-turbo
- Timeout handling for LLM calls
- Category-based entity templates

### Fixed
- CRIT-002: Entity detection timeout
- BUG-001: datetime deprecation warnings

### Changed
- Improved iteration effectiveness
- Faster generation (90s vs 120s)
```

---

## 🔀 Pull Request Process

### Before Creating PR

**Checklist**:
- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Commit messages are clear

### Creating PR

1. **Go to GitHub** → Pull Requests → New Pull Request

2. **Fill Template**:
```markdown
## Description
Brief description of changes

## Related Issue
Fixes #123 (CRIT-002)

## Type of Change
- [ ] Bug fix
- [x] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [x] Unit tests added
- [x] Integration tests added
- [x] Tested locally with restaurant concept

## Screenshots (if applicable)
[Before/after comparison]

## Checklist
- [x] Code follows style guide
- [x] Self-review completed
- [x] Documentation updated
- [x] Tests pass
```

3. **Request Reviews**
   - Tag relevant reviewers
   - Link to related discussions

### Review Process

**As Author**:
- Respond to comments promptly
- Make requested changes
- Mark conversations resolved
- Keep PR scope focused

**As Reviewer**:
- Review within 48 hours
- Be constructive and specific
- Test the changes locally
- Approve when satisfied

**Review Checklist**:
- [ ] Code quality (readability, maintainability)
- [ ] Functionality (does it work as intended?)
- [ ] Tests (adequate coverage?)
- [ ] Documentation (clear and complete?)
- [ ] Performance (any concerns?)
- [ ] Security (any vulnerabilities?)

### Merging

**Requirements**:
- 1+ approvals
- All checks pass (CI/CD)
- No merge conflicts
- Up to date with base branch

**Merge Strategy**:
- `develop` → Squash and merge
- `develop` → `main` → Create merge commit (for releases)

---

## 🚢 Release Process

### Version Numbering

**Semantic Versioning**: MAJOR.MINOR.PATCH

- **MAJOR**: Breaking changes (v1.0 → v2.0)
- **MINOR**: New features, backwards compatible (v1.0 → v1.1)
- **PATCH**: Bug fixes (v1.0.0 → v1.0.1)

### Release Steps

1. **Prepare Release Branch**
```bash
git checkout develop
git pull origin develop
git checkout -b release/v1.1.0
```

2. **Update Version**
- `verifimind_complete.py` - Update VERSION constant
- `README.md` - Update version badge
- `CHANGELOG.md` - Finalize entries

3. **Test Release**
```bash
pytest
python verifimind_complete.py --test
```

4. **Create PR to main**
```bash
git push origin release/v1.1.0
# Create PR: release/v1.1.0 → main
```

5. **After Merge**
```bash
# Tag release
git tag -a v1.1.0 -m "Release v1.1.0 - Core Improvements"
git push origin v1.1.0

# Merge back to develop
git checkout develop
git merge main
git push origin develop
```

6. **GitHub Release**
- Go to GitHub → Releases → Draft Release
- Select tag `v1.1.0`
- Title: "v1.1.0 - Core Improvements"
- Description: Copy from CHANGELOG.md
- Attach binaries if applicable
- Publish release

---

## 🙏 Recognition

### Contributors

All contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

### Hall of Fame

Outstanding contributions may be featured in:
- Project README
- Blog posts
- Conference talks

---

## 📞 Getting Help

**Questions?**
- GitHub Discussions (general questions)
- GitHub Issues (bug reports, feature requests)
- Email: creator35lwb@gmail.com

**Development Help**:
- Check ARCHITECTURE.md for technical details
- Review KNOWN_ISSUES.md for common problems
- Ask in pull request comments

---

## 📚 Additional Resources

- [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) - Project vision
- [DEVELOPMENT_HISTORY.md](./DEVELOPMENT_HISTORY.md) - Evolution timeline
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical architecture
- [KNOWN_ISSUES.md](./KNOWN_ISSUES.md) - Current limitations
- [ROADMAP.md](./ROADMAP.md) - Future plans

---

## 🎉 Thank You!

Your contributions make VerifiMind better for everyone. Whether you're fixing typos, adding features, or helping other users, you're making a difference!

**Welcome to the VerifiMind community!**

---

*Last Updated*: October 12, 2025
*Version*: 1.0.0
*Maintained By*: VerifiMind Development Team
