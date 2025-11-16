# Setting Up Real API Keys for VerifiMind

**Guide to Enable Real LLM Integration**

---

## Overview

VerifiMind works perfectly **without API keys** (using intelligent mocks), but for **real AI-powered analysis**, you can connect to:

1. **OpenAI** (GPT-4, GPT-3.5)
2. **Anthropic** (Claude 3)
3. **Local Models** (Free, no API needed)

---

## Option 1: OpenAI (GPT-4) - Recommended

### Step 1: Get API Key

1. Go to: https://platform.openai.com/signup
2. Create an account (or log in)
3. Add payment method (required for API access)
4. Go to: https://platform.openai.com/api-keys
5. Click "Create new secret key"
6. Copy the key (starts with `sk-...`)

**Cost**: ~$0.03-0.06 per API call with GPT-4

### Step 2: Set Environment Variable (Windows)

**Method A: Temporary (This session only)**
```batch
set OPENAI_API_KEY=sk-your-actual-key-here
```

**Method B: Permanent (Recommended)**
1. Press `Windows + R`
2. Type: `sysdm.cpl` and press Enter
3. Click "Advanced" tab
4. Click "Environment Variables"
5. Under "User variables", click "New"
6. Variable name: `OPENAI_API_KEY`
7. Variable value: `sk-your-actual-key-here`
8. Click OK, OK, OK
9. **Restart Command Prompt**

### Step 3: Verify Setup

1. Open **new** Command Prompt
2. Type: `echo %OPENAI_API_KEY%`
3. Should show your key (starts with `sk-...`)

### Step 4: Launch VerifiMind

1. Double-click `VerifiMind.bat`
2. Press `[4]` - Check System Status
3. Should show: `OpenAI: ✓ Configured`
4. Press `[2]` - Test Enhanced Agents (uses real API!)

---

## Option 2: Anthropic (Claude 3)

### Step 1: Get API Key

1. Go to: https://console.anthropic.com/
2. Create an account
3. Add credits (minimum $5)
4. Go to Settings → API Keys
5. Create new key
6. Copy the key (starts with `sk-ant-...`)

**Cost**: ~$0.015-0.08 per API call with Claude 3

### Step 2: Set Environment Variable

**Temporary:**
```batch
set ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

**Permanent:**
1. Press `Windows + R`
2. Type: `sysdm.cpl`
3. Advanced → Environment Variables
4. New → `ANTHROPIC_API_KEY` = `sk-ant-your-key`
5. OK, OK, OK
6. Restart Command Prompt

### Step 3: Verify

```batch
echo %ANTHROPIC_API_KEY%
```

---

## Option 3: Local Models (Ollama) - FREE!

### Step 1: Install Ollama

1. Go to: https://ollama.ai/download
2. Download Ollama for Windows
3. Run installer
4. Ollama will start automatically

### Step 2: Pull a Model

Open Command Prompt and run:
```batch
ollama pull llama2
```

**Free models available**:
- `llama2` (7B, 13B) - General purpose
- `mistral` - Fast and capable
- `codellama` - Code generation
- `phi` - Microsoft's small model

### Step 3: Start Ollama Server

```batch
ollama serve
```

Keep this running in the background.

### Step 4: Use in VerifiMind

No API key needed! Just:
1. Make sure Ollama is running
2. Launch VerifiMind
3. It will automatically detect local models

---

## Testing Your Setup

### Quick Test Script

Create a file called `test_api.py`:

```python
import asyncio
import os
from src.llm.llm_provider import LLMProviderFactory, LLMMessage

async def test_api():
    """Test real API connection"""

    # Check which APIs are configured
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    print("API Configuration:")
    print(f"  OpenAI: {'✓ Configured' if openai_key else '✗ Not set'}")
    print(f"  Anthropic: {'✓ Configured' if anthropic_key else '✗ Not set'}")
    print()

    # Test OpenAI if configured
    if openai_key:
        print("Testing OpenAI...")
        try:
            provider = LLMProviderFactory.create_provider("openai", model="gpt-4")
            messages = [
                LLMMessage(role="system", content="You are a helpful assistant."),
                LLMMessage(role="user", content="Say 'Hello from GPT-4!' in one sentence.")
            ]
            response = await provider.generate(messages, temperature=0.7, max_tokens=50)
            print(f"✓ OpenAI works! Response: {response.content[:100]}")
        except Exception as e:
            print(f"✗ OpenAI error: {e}")
        print()

    # Test Anthropic if configured
    if anthropic_key:
        print("Testing Anthropic...")
        try:
            provider = LLMProviderFactory.create_provider("anthropic", model="claude-3-opus-20240229")
            messages = [
                LLMMessage(role="system", content="You are a helpful assistant."),
                LLMMessage(role="user", content="Say 'Hello from Claude!' in one sentence.")
            ]
            response = await provider.generate(messages, temperature=0.7, max_tokens=50)
            print(f"✓ Anthropic works! Response: {response.content[:100]}")
        except Exception as e:
            print(f"✗ Anthropic error: {e}")
        print()

    if not openai_key and not anthropic_key:
        print("No API keys configured. Using intelligent mocks.")
        print("Set OPENAI_API_KEY or ANTHROPIC_API_KEY to test real APIs.")

if __name__ == "__main__":
    asyncio.run(test_api())
```

Run it:
```batch
python test_api.py
```

---

## Using Real APIs in VerifiMind

Once API keys are set:

### Option A: Through Launcher (Easiest)

1. Double-click `VerifiMind.bat`
2. Press `[4]` - Check System Status
3. Verify APIs show as `✓ Configured`
4. Press `[2]` - Test Enhanced Agents (uses real APIs!)
5. Press `[1]` - Generate New Application (uses real APIs!)

### Option B: Direct Script

```python
import asyncio
from src.llm.llm_provider import LLMProviderFactory
from src.agents.x_intelligent_agent import XIntelligentAgent
from src.agents.base_agent import ConceptInput

async def generate_with_real_api():
    # Create LLM provider (will use real API if key is set)
    llm = LLMProviderFactory.create_provider("openai", model="gpt-4")

    # Create agent
    config = {"log_level": "INFO"}
    x_agent = XIntelligentAgent("X-001", llm, config)

    # Your app idea
    concept = ConceptInput(
        id="my-app-001",
        description="Your app idea here...",
        category="Your Category",
        user_context={},
        session_id="session-001"
    )

    # Analyze with real AI!
    result = await x_agent.analyze(concept)
    print(f"Analysis: {result.analysis}")

asyncio.run(generate_with_real_api())
```

---

## Cost Estimates

### OpenAI Pricing (GPT-4)
- **Input**: $0.03 per 1K tokens
- **Output**: $0.06 per 1K tokens
- **Per VerifiMind analysis**: ~$0.03-0.10
- **Per app generation**: ~$0.10-0.30

### Anthropic Pricing (Claude 3 Opus)
- **Input**: $0.015 per 1K tokens
- **Output**: $0.075 per 1K tokens
- **Per VerifiMind analysis**: ~$0.02-0.08
- **Per app generation**: ~$0.08-0.25

### Ollama (Local)
- **Cost**: $0 (FREE!)
- **Requires**: GPU recommended (but works on CPU)
- **Speed**: Slower than cloud APIs
- **Privacy**: 100% local, no data leaves your computer

---

## Recommendations

### For Testing/Learning
→ Use **Ollama** (free, unlimited)

### For Production/Best Quality
→ Use **OpenAI GPT-4** (best results, moderate cost)

### For Privacy-Conscious
→ Use **Ollama** (100% local)

### For Balanced Cost/Quality
→ Use **Anthropic Claude 3 Sonnet** (cheaper than Opus, still great)

---

## Troubleshooting

### Issue: "Invalid API key"
**Solution:**
1. Double-check the key (copy again from website)
2. Make sure no extra spaces
3. Restart Command Prompt after setting
4. Run: `echo %OPENAI_API_KEY%` to verify

### Issue: "Rate limit exceeded"
**OpenAI:**
- You're sending too many requests
- Wait a few minutes
- Or upgrade your OpenAI plan

**Anthropic:**
- Add more credits to account
- Check your usage limits

### Issue: API works but gives errors
**Solution:**
1. Check your account has credits
2. Verify model name is correct
3. Check API status: status.openai.com or status.anthropic.com

### Issue: Ollama not connecting
**Solution:**
1. Make sure Ollama is running: `ollama serve`
2. Try: `ollama list` to see installed models
3. Pull a model: `ollama pull llama2`

---

## Security Best Practices

### ✅ DO:
- Store API keys in environment variables
- Use `.env` files for local development (never commit!)
- Rotate keys periodically
- Monitor usage on provider dashboard

### ❌ DON'T:
- Hardcode keys in source code
- Commit keys to Git
- Share keys publicly
- Use production keys for testing

---

## Quick Command Reference

### Windows (Temporary - Current Session)
```batch
set OPENAI_API_KEY=sk-...
set ANTHROPIC_API_KEY=sk-ant-...
```

### Windows (Permanent - All Sessions)
```batch
setx OPENAI_API_KEY "sk-..."
setx ANTHROPIC_API_KEY "sk-ant-..."
```
(Restart Command Prompt after `setx`)

### Verify Keys Are Set
```batch
echo %OPENAI_API_KEY%
echo %ANTHROPIC_API_KEY%
```

### Test Ollama
```batch
ollama serve
ollama pull llama2
ollama run llama2 "Hello!"
```

---

## Ready to Try!

Once you've set up your API keys:

1. **Close all Command Prompt windows**
2. **Open a NEW Command Prompt**
3. **Double-click VerifiMind.bat**
4. **Press [4]** to check status
5. **Press [2]** to test with real APIs!

You'll see much more detailed and intelligent analysis compared to the mock responses!

---

## Support

If you need help:
1. Check VerifiMind launcher: Press [4] for system status
2. Run `test_api.py` to test API connections
3. Check provider status pages:
   - OpenAI: https://status.openai.com
   - Anthropic: https://status.anthropic.com

---

**Generated**: October 8, 2025
**For**: VerifiMind™ Real API Integration
**Status**: Ready to Configure ✅
