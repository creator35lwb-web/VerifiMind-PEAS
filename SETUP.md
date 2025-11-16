# VerifiMind PEAS Setup Guide

**Complete installation and configuration guide for VerifiMind PEAS (Genesis Prompt Ecosystem for Application Synthesis)**

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Quick Start](#quick-start)
5. [Troubleshooting](#troubleshooting)
6. [Next Steps](#next-steps)

---

## Prerequisites

Before installing VerifiMind PEAS, ensure you have:

### Required

- **Python 3.11 or higher** ([Download](https://www.python.org/downloads/))
  ```bash
  python --version  # Should show 3.11.x or higher
  ```

- **pip** (Python package installer, usually comes with Python)
  ```bash
  pip --version
  ```

- **git** (for cloning the repository)
  ```bash
  git --version
  ```

### Recommended

- **Virtual environment support** (venv, already included in Python 3.11+)
- **Code editor** (VS Code, PyCharm, or your preferred editor)
- **At least 2GB free disk space** (for dependencies and generated apps)

### API Keys (at least one required)

You'll need API access to at least one LLM provider:

- **OpenAI API Key** ([Get here](https://platform.openai.com/api-keys))
  - Recommended models: GPT-4, GPT-4 Turbo
  - Pricing: Pay-per-use (~$0.01-0.03 per 1K tokens)

- **Anthropic API Key** ([Get here](https://console.anthropic.com/))
  - Recommended models: Claude 3.5 Sonnet, Claude 3 Opus
  - Pricing: Pay-per-use (~$0.003-0.015 per 1K tokens)

---

## Installation

### Step 1: Clone the Repository

```bash
# Clone from GitHub
git clone https://github.com/creator35lwb-web/VerifiMind-PEAS.git
cd VerifiMind-PEAS
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate
```

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt, indicating the virtual environment is active.

### Step 3: Install Dependencies

```bash
# Upgrade pip to latest version
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
```

This will install:
- LLM providers (OpenAI, Anthropic)
- Web framework (FastAPI)
- Code generation tools
- Blockchain libraries (optional)
- Testing frameworks
- All other dependencies

**Installation time:** 2-5 minutes depending on your internet connection

### Step 4: Verify Installation

```bash
# Check if key packages are installed
python -c "import openai; import anthropic; print('✅ LLM providers installed')"
python -c "import fastapi; import pydantic; print('✅ Web framework installed')"
python -c "from src.agents import XIntelligentAgent; print('✅ VerifiMind agents loaded')"
```

If all commands succeed, your installation is complete!

---

## Configuration

### Step 1: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Windows alternative:
copy .env.example .env
```

### Step 2: Configure API Keys

Open `.env` in your text editor and configure at minimum:

**For OpenAI:**
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4
LLM_PROVIDER=openai
```

**For Anthropic (Claude):**
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
LLM_PROVIDER=anthropic
```

### Step 3: Configure Creator Attribution

Set your information for proper attribution:

```bash
CREATOR_NAME=Your Full Name
CREATOR_EMAIL=your.email@example.com
CREATOR_ORGANIZATION=Your Organization (optional)
```

### Step 4: Configure Application Settings

**Basic Settings:**
```bash
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO
OUTPUT_DIR=./output
MAX_ITERATIONS=3
```

**Feature Flags:**
```bash
ENABLE_X_AGENT=true
ENABLE_Z_AGENT=true
ENABLE_CS_AGENT=true
ENABLE_ITERATIVE_GENERATION=true
ENABLE_FRONTEND_GENERATION=true
ENABLE_ATTRIBUTION=true
```

### Step 5: (Optional) Configure Blockchain Attribution

If you want blockchain-based IP protection:

```bash
BLOCKCHAIN_ENABLED=true
POLYGON_RPC_URL=https://polygon-rpc.com
WALLET_PRIVATE_KEY=your_private_key_here  # ⚠️ NEVER commit this!
WALLET_ADDRESS=0xYourWalletAddress
PINATA_API_KEY=your_pinata_api_key
PINATA_SECRET_KEY=your_pinata_secret_key
```

**⚠️ Security Warning:** Never commit your `.env` file or share your private keys!

---

## Quick Start

### Test Your Setup

```bash
# Run the demo script
python demo_iterative_generation.py
```

**Expected Output:**
```
🌟 VerifiMind PEAS - Iterative Code Generation Demo
==================================================

📋 Step 1: Creating app specification...
✅ App specification created

🤖 Step 2: Initializing RefleXion Trinity agents...
   → X Intelligent Agent (Innovation Engine)
   → Z Guardian Agent (Ethics & Compliance)
   → CS Security Agent (Security Scanner)
✅ All agents initialized

🎯 Step 3: Running iterative generation...
   Iteration 1/3: Initial generation
   Iteration 2/3: Reflection + improvement
   Iteration 3/3: Final refinement
✅ Generation complete

📦 Output saved to: ./output/confucian_education_app_v3/
```

### Validate Your First Concept

```bash
# Run the interactive CLI
python -m src.cli.interactive

# Or use the complete system
python verifimind_complete.py
```

### Run a Specific Example

```bash
# Confucian Education AI example
python examples/confucian_education_ai.py

# Custom concept
python examples/custom_concept.py
```

---

## Troubleshooting

### Issue 1: Import Errors

**Problem:**
```
ModuleNotFoundError: No module named 'openai'
```

**Solution:**
```bash
# Make sure virtual environment is activated
# You should see (venv) in your prompt

# If not, activate it:
# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 2: API Key Errors

**Problem:**
```
Error: Invalid API key provided
```

**Solution:**
1. Check that `.env` file exists in project root
2. Verify API key is correct (no extra spaces or quotes)
3. Test API key directly:
   ```bash
   python -c "import openai; openai.api_key='YOUR_KEY'; print('Key valid')"
   ```

### Issue 3: Permission Errors

**Problem:**
```
PermissionError: [Errno 13] Permission denied: './output'
```

**Solution:**
```bash
# Create output directory manually
mkdir output

# On Windows:
md output

# Set permissions (Mac/Linux)
chmod 755 output
```

### Issue 4: Python Version Issues

**Problem:**
```
SyntaxError: match is only supported in Python 3.10+
```

**Solution:**
```bash
# Check Python version
python --version

# If < 3.11, install Python 3.11+ and recreate virtual environment
python3.11 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Issue 5: Slow Generation

**Problem:** Generation takes > 5 minutes

**Solution:**
1. Check your internet connection
2. Verify API rate limits aren't exceeded
3. Use faster model:
   ```bash
   # In .env
   OPENAI_MODEL=gpt-4-turbo  # Faster than gpt-4
   ```
4. Reduce max iterations:
   ```bash
   MAX_ITERATIONS=2  # Instead of 3
   ```

### Issue 6: Mock Mode Stuck

**Problem:** System uses mock responses instead of real API

**Solution:**
```bash
# In .env, ensure:
MOCK_MODE=false

# And verify API keys are set:
OPENAI_API_KEY=sk-proj-xxxxx  # Should start with sk-
```

### Getting More Help

1. **Check logs:**
   ```bash
   # Enable verbose logging
   # In .env:
   LOG_LEVEL=DEBUG
   VERBOSE=true
   ```

2. **Review error messages carefully** - they often indicate exactly what's wrong

3. **Check GitHub Issues:** [VerifiMind PEAS Issues](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues)

4. **Read documentation:**
   - [Architecture](ARCHITECTURE_V2.md)
   - [True Vision](VERIFIMIND_TRUE_VISION.md)
   - [Development Roadmap](DEVELOPMENT_ROADMAP_V2.md)

---

## Next Steps

### 1. Explore the Codebase

**Core Components:**
- `src/agents/` - RefleXion Trinity agents (X, Z, CS)
- `src/generation/` - Code generation and iteration logic
- `src/llm/` - LLM provider abstraction
- `src/blockchain/` - Attribution and IP protection
- `examples/` - Example concepts and demos

### 2. Read Key Documentation

Start with these files in order:
1. **[VERIFIMIND_TRUE_VISION.md](VERIFIMIND_TRUE_VISION.md)** - Understand the philosophy
2. **[ARCHITECTURE_V2.md](ARCHITECTURE_V2.md)** - Learn the system design
3. **[PEAS_INTEGRATION_PLAN.md](PEAS_INTEGRATION_PLAN.md)** - See how it all fits together
4. **[reflexion-master-prompts-v1.1.md](reflexion-master-prompts-v1.1.md)** - Explore agent specifications

### 3. Try Different Use Cases

**Non-Technical Founder:**
```bash
# Validate your startup idea
python verifimind_complete.py
# Describe your idea in natural language
# Get validated architecture + roadmap
```

**Technical Founder:**
```bash
# Pressure-test your assumptions
python examples/socratic_validation.py
# Challenge your concept with Socratic dialogue
```

**Cultural Heritage Project:**
```bash
# Build culturally-sensitive AI
python examples/confucian_education_ai.py
# Z Guardian ensures cultural respect
```

### 4. Customize Agents

Edit agent prompts in:
- `src/agents/x_intelligent_agent.py` - Innovation analysis
- `src/agents/z_guardian_agent.py` - Ethics & compliance
- `src/agents/cs_security_agent.py` - Security scanning

### 5. Build Your First App

```bash
# Create new concept file
cp examples/confucian_education_ai.py examples/my_concept.py

# Edit with your idea
# Run:
python examples/my_concept.py

# Check output:
ls output/my_app_v3/
```

### 6. Enable Advanced Features

**Blockchain Attribution:**
1. Get Polygon wallet ([MetaMask](https://metamask.io/))
2. Get MATIC tokens for gas fees
3. Get Pinata account for IPFS
4. Configure `.env` with credentials
5. Set `BLOCKCHAIN_ENABLED=true`

**Web API Mode:**
```bash
# Run as web service
python -m src.api.server

# Access at http://localhost:8000
# API docs at http://localhost:8000/docs
```

---

## Configuration Reference

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_API_KEY` | string | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | string | - | Anthropic API key |
| `LLM_PROVIDER` | `openai`\|`anthropic` | `openai` | Default LLM provider |
| `OUTPUT_DIR` | path | `./output` | Where to save generated apps |
| `MAX_ITERATIONS` | int | `3` | RefleXion loop iterations |
| `CREATOR_NAME` | string | - | Your name for attribution |
| `CREATOR_EMAIL` | string | - | Your email for attribution |
| `BLOCKCHAIN_ENABLED` | bool | `false` | Enable blockchain IP tracking |
| `DEBUG` | bool | `false` | Enable debug mode |
| `LOG_LEVEL` | `DEBUG`\|`INFO`\|`WARNING` | `INFO` | Logging verbosity |

See `.env.example` for complete reference.

---

## System Requirements

**Minimum:**
- Python 3.11+
- 2GB RAM
- 2GB disk space
- Internet connection

**Recommended:**
- Python 3.11+
- 8GB RAM
- 10GB disk space
- Fast internet (for API calls)

**OS Support:**
- ✅ Windows 10/11
- ✅ macOS 12+
- ✅ Linux (Ubuntu 20.04+, Debian 11+)

---

## Success Checklist

Before running your first generation, ensure:

- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created from `.env.example`
- [ ] At least one API key configured (OpenAI or Anthropic)
- [ ] Creator name and email set in `.env`
- [ ] `output/` directory exists (or will be auto-created)
- [ ] Demo script runs successfully

---

## FAQ

**Q: Do I need both OpenAI and Anthropic API keys?**
A: No, one is sufficient. Configure `LLM_PROVIDER` in `.env` to your chosen provider.

**Q: How much do API calls cost?**
A: Varies by provider and model. Typical validation: $0.10-0.50. Full app generation: $1-5. Check your provider's pricing.

**Q: Can I run this offline?**
A: No, VerifiMind requires internet access to call LLM APIs. A local LLM mode is planned for future releases.

**Q: Is blockchain required?**
A: No, blockchain is optional. Set `BLOCKCHAIN_ENABLED=false` to use local attribution only.

**Q: Can I use this for commercial projects?**
A: Check the [LICENSE](LICENSE) file. Generated code is yours to use, but review the framework's license terms.

**Q: How do I update VerifiMind?**
A: `git pull origin main && pip install -r requirements.txt`

---

## Resources

**Documentation:**
- [GitHub Repository](https://github.com/creator35lwb-web/VerifiMind-PEAS)
- [White Paper](docs/white_paper.md)
- [Architecture V2](ARCHITECTURE_V2.md)
- [Development Roadmap](DEVELOPMENT_ROADMAP_V2.md)

**External Links:**
- [YSenseAI™ Philosophy](https://ysenseai.substack.com)
- [Defensive Publication](https://doi.org/10.5281/zenodo.17616329)
- [OpenAI Documentation](https://platform.openai.com/docs)
- [Anthropic Documentation](https://docs.anthropic.com)

**Community:**
- GitHub Issues: Bug reports and feature requests
- GitHub Discussions: Questions and conversations

---

**Installation complete! You're ready to co-create with AI. 🚀**

*VerifiMind™ PEAS - Genesis Prompt Ecosystem for Application Synthesis*
