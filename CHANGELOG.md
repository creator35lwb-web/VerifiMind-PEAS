# Changelog

All notable changes to the VerifiMind PEAS project will be documented in this file.

---

## v0.4.0 - Unified Prompt Templates (January 30, 2026)

### New MCP Tools (6 new tools, 10 total)

| Tool | Purpose | Parameters |
|------|---------|------------|
| `list_prompt_templates` | List/filter templates | agent_id, category, tags |
| `get_prompt_template` | Get template by ID | template_id, include_content |
| `export_prompt_template` | Export to MD/JSON | template_id, format |
| `register_custom_template` | Create custom template | name, agent_id, content, ... |
| `import_template_from_url` | Import from URL/Gist | url, validate |
| `get_template_statistics` | Registry statistics | - |

### Template Library (6 libraries, 18+ templates)

| Library | Agent | Genesis Phase | Templates |
|---------|-------|---------------|-----------|
| `startup_validation` | X | Phase 1 | 3 |
| `market_research` | X | Phase 1 | 3 |
| `ethics_review` | Z | Phase 2 | 3 |
| `security_audit` | CS | Phase 3 | 3 |
| `technical_review` | CS | Phase 3 | 3 |
| `trinity_synthesis` | ALL | Phase 4 | 3 |

### Template Features
- **Prompt Export** - Download as Markdown/JSON with full documentation
- **Custom Variables** - User-defined placeholders with validation
- **Version Control** - Template versioning and changelog
- **Import from URL** - GitHub Gist and raw file support
- **Provider Compatibility** - Multi-LLM awareness matrix
- **Genesis Methodology Tags** - Phase alignment (phase-1 to phase-4)

### Files Added
- `templates/models.py` - PromptTemplate, TemplateVariable models
- `templates/registry.py` - TemplateRegistry singleton
- `templates/export.py` - Markdown/JSON export utilities
- `templates/import_url.py` - URL/Gist import functionality
- `templates/library/*.yaml` - 6 template library files

### Files Modified
- `server.py` - Added 6 new MCP tools, version 0.4.0
- `http_server.py` - Updated tool count to 10, version 0.4.0

### Credits
- Implementation: Claude Code
- Architecture Review: Manus AI (CTO)

---

## v0.3.5 - Input Sanitization + Security Hardening (January 30, 2026)

### Security Enhancements

#### Input Sanitization Module
Comprehensive input sanitization for all MCP tools to protect against:

| Attack Type | Protection | Status |
|------------|------------|--------|
| Prompt Injection | Pattern detection + logging | Active |
| XSS Attacks | HTML entity escaping | Active |
| Null Byte Injection | Control character removal | Active |
| Input Length Abuse | Field truncation | Active |

**Sanitization Functions:**
- `sanitize_concept_name()` - Concept name sanitization (max 200 chars)
- `sanitize_description()` - Description sanitization (max 10,000 chars)
- `sanitize_category()` - Category sanitization (max 100 chars)
- `sanitize_context()` - Context sanitization (max 5,000 chars)
- `sanitize_concept_input()` - Full concept input sanitization
- `detect_prompt_injection()` - Pattern-based injection detection
- `is_safe_input()` - Quick safety check

**Prompt Injection Detection Patterns:**
- "ignore previous/all instructions"
- "disregard all previous prompts"
- "you are now a..."
- System prompt markers ([INST], <|im_start|>, etc.)
- Role hijacking attempts

### Integration
All four MCP tools now sanitize inputs:
- `consult_agent_x` - Sanitized
- `consult_agent_z` - Sanitized
- `consult_agent_cs` - Sanitized
- `run_full_trinity` - Sanitized

### Files Modified
- `mcp-server/src/verifimind_mcp/server.py` - Added sanitization to all tools
- `mcp-server/src/verifimind_mcp/utils/sanitization.py` - Fixed pattern for "disregard all previous"
- `mcp-server/http_server.py` - Updated version to v0.3.5

### Files Created
- `mcp-server/requirements.txt` - For CI/CD compatibility

### Testing
- 29/29 sanitization unit tests passing
- Server imports successfully
- All existing functionality preserved

### Credits
- Implementation: Claude Code
- Task: Issue #3 (verifimind-genesis-mcp)

---

## v0.3.2 - Gemini 2.5 Model Update (January 29, 2026)

### Bug Fixes
- **Critical**: Fixed Gemini 1.5-flash model retirement
  - Changed default model from `gemini-1.5-flash` to `gemini-2.5-flash`
  - Updated `GeminiProvider` class default in `provider.py`
  - Updated `PROVIDER_CONFIGS` models list

### Technical Details
- **Root Cause**: Google retired `gemini-1.5-flash` model in 2026
- **Error**: `404 models/gemini-1.5-flash is not found`
- **Resolution**: Default to `gemini-2.5-flash` (stable, FREE tier)

### Deployment
- Deployed to GCP Cloud Run: `verifimind.ysenseai.org`
- All v0.3.1 protection features remain active

### Credits
- Implementation: Claude Code

---

## v0.3.1 - Smart Fallback + Rate Limiting + Per-Agent Providers (January 29, 2026)

### New Features

#### Rate Limiting (EDoS Protection)
Protects against Economic Denial of Sustainability attacks:

| Limit | Value | Purpose |
|-------|-------|---------|
| Per IP | 10 req/min | Prevent single-user abuse |
| Global | 100 req/min/instance | Prevent auto-scale cost attacks |
| Burst | 2x limit | Allow short bursts |

**Environment Variables:**
```bash
RATE_LIMIT_PER_IP=10      # requests per minute per IP
RATE_LIMIT_GLOBAL=100     # requests per minute per instance
RATE_LIMIT_BURST=2.0      # burst multiplier
RATE_LIMIT_WINDOW=60      # window in seconds
```

#### Smart Fallback Per-Agent Provider System
Intelligent provider selection optimized for each agent's specialty:

| Agent | Default (FREE) | Recommended (BYOK) | Specialty |
|-------|----------------|-------------------|-----------|
| **X Agent** | Gemini | Gemini | Innovation, creativity |
| **Z Agent** | Gemini | Anthropic Claude | Ethical reasoning |
| **CS Agent** | Gemini | Anthropic Claude | Code/security analysis |

**Strategy:**
- **Default**: All agents use Gemini (FREE tier) - no cost to maintainer
- **Smart Upgrade**: If `ANTHROPIC_API_KEY` is set, Z and CS agents automatically use Claude
- **Per-Agent Override**: `X_AGENT_PROVIDER`, `Z_AGENT_PROVIDER`, `CS_AGENT_PROVIDER` env vars

#### New Helper Functions
- `get_agent_provider(agent_id, ctx)` - Get optimized provider for specific agent
- `get_trinity_providers(ctx)` - Get all three agent providers at once
- `get_provider_status()` - Diagnostic function showing current configuration

### Bug Fixes
- **Critical**: Fixed deprecated Gemini model causing 404 errors
  - Changed default model from `gemini-2.0-flash-exp` to `gemini-1.5-flash`
  - Updated `GeminiProvider` class default in `provider.py`
  - Updated `PROVIDER_CONFIGS` models list

### Technical Details
- **Root Cause**: Google deprecated `gemini-2.0-flash-exp` model
- **Error**: `404 models/gemini-2.0-flash-exp is not found for API version v1beta`
- **Resolution**: Default to `gemini-1.5-flash` (stable, FREE tier)

### Environment Variables
```bash
# Default: All agents use Gemini FREE tier
GEMINI_API_KEY=your-key

# Optional: Z and CS automatically upgrade to Claude if set
ANTHROPIC_API_KEY=your-key

# Optional: Per-agent overrides
X_AGENT_PROVIDER=gemini
Z_AGENT_PROVIDER=anthropic
CS_AGENT_PROVIDER=anthropic
```

### Files Modified
- `mcp-server/src/verifimind_mcp/llm/provider.py` - Updated default Gemini model
- `mcp-server/src/verifimind_mcp/config_helper.py` - Added smart fallback functions
- `mcp-server/src/verifimind_mcp/server.py` - Updated all tools to use per-agent providers
- `mcp-server/src/verifimind_mcp/middleware/rate_limiter.py` - NEW: Rate limiting middleware
- `mcp-server/src/verifimind_mcp/middleware/__init__.py` - NEW: Middleware module
- `mcp-server/http_server.py` - Integrated rate limiting, updated version
- `.env.example` - Added rate limiting variables
- `CHANGELOG.md` - This update
- `SERVER_STATUS.md` - Updated status

### Benefits
- **Sustainable**: Public server uses FREE Gemini tier (no cost to maintainer)
- **Accessible**: Works out-of-box for everyone
- **Optimized**: Right model for each agent when BYOK configured
- **Flexible**: Full customization via environment variables

### Credits
- Implementation: Claude Code
- Architecture: Alton Lee Wei Bin (CTO Team YSenseAI)

---

## v0.3.0 - BYOK Multi-Provider Support (January 28, 2026)

### BYOK (Bring Your Own Key) Enhancement

This release implements full multi-provider BYOK support, enabling users to connect their own LLM API keys for multiple providers, making the system sustainable without increasing maintainer costs.

### New Features
- **Multi-Provider Support**: Added support for 7 LLM providers:
  - Gemini (FREE tier available)
  - Groq (FREE tier available)
  - OpenAI
  - Anthropic
  - Mistral (NEW)
  - Ollama (local, FREE) (NEW)
  - Mock (testing)

- **Automatic Fallback**: New `LLM_FALLBACK_PROVIDER` environment variable enables automatic fallback if primary provider fails

- **Provider Configuration**: New `PROVIDER_CONFIGS` dictionary with metadata about each provider including:
  - Default models
  - Available models
  - Free tier availability
  - Rate limits

- **Validation Utilities**: New helper functions:
  - `get_provider_with_fallback()` - Factory with automatic fallback
  - `validate_provider_config()` - Validate provider setup
  - `list_providers()` - List all available providers
  - `list_free_tier_providers()` - List free tier options

### Files Modified
- `mcp-server/src/verifimind_mcp/llm/provider.py` - Added Mistral and Ollama providers, fallback support
- `mcp-server/src/verifimind_mcp/llm/__init__.py` - Updated exports
- `mcp-server/src/verifimind_mcp/config_helper.py` - Multi-provider support
- `mcp-server/src/verifimind_mcp/server.py` - Added Groq/Mistral config fields
- `.env.example` - Updated with BYOK v0.3.0 configuration
- `MCP_SETUP_GUIDE.md` - Updated BYOK documentation
- `CHANGELOG.md` - This update

### Environment Variables
```bash
# Primary provider
LLM_PROVIDER=gemini

# Fallback provider
LLM_FALLBACK_PROVIDER=mock

# Optional overrides
LLM_MODEL=gemini-1.5-flash
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

### Breaking Changes
- None. Backward compatible with v0.2.x environment variables.

### Credits
- Implementation: Claude Code
- Specifications: Manus AI (T), CTO - Team YSenseAI

---

## v0.2.5 - Documentation & Encoding Fixes (January 2026)

### Documentation
- Improved BYOK documentation
- Fixed encoding issues in documentation files

---

## v1.0.2 - IP Update (November 19, 2025)

### Security
- Added **Genesis Prompt Engineering Methodology** to the defensive publication to establish prior art for the multi-model validation process.

---

## Phase 2 Track 1 - Complete (November 19, 2025)

### Code Enhancements
-  Code cleanup and organization
-  Comprehensive error handling with custom exception hierarchy
-  Testing infrastructure with 18 async tests
-  Structured logging framework
-  Professional CLI with argparse

### Documentation Cleanup
-  Consolidated vision, architecture, and roadmap documentation
-  Archived historical summary files
-  Added Concept Scrutinizer methodology specification
-  Created clear documentation hierarchy

### Project Organization
-  Moved demo scripts to `examples/`
-  Moved test files to `tests/`
-  Moved utility scripts to `scripts/`
-  Created `archive/` for historical files
-  Created `docs/methodology/` for foundational docs

### Canonical Documentation
- `docs/VISION.md` - Consolidated from 3 vision documents
- `docs/ARCHITECTURE.md` - Consolidated from 2 architecture documents
- `docs/ROADMAP.md` - Consolidated from 2 roadmap documents

---

## Phase 1 - Complete (November 15, 2025)

### Initial Setup
-  Initial codebase sync to GitHub
-  Project structure setup
-  Configuration files and setup documentation

### Core Implementation
-  LLM provider abstraction (OpenAI, Anthropic)
-  X-Z-CS agent framework
-  Iterative code generation engine
-  Agent orchestration system

---

## Phase 2 Track 2 - In Progress

### Genesis Methodology Formalization
- � Genesis Methodology white paper
- � RefleXion C1 case study documentation
- � API documentation

---

**Document Version**: 1.0
**Last Updated**: November 19, 2025
