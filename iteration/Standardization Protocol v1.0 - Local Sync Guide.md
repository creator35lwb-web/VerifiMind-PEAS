# Standardization Protocol v1.0 - Local Sync Guide

**Commit:** `1a1db6f`  
**Date:** December 21, 2025  
**Status:** ✅ Pushed to GitHub

---

## Quick Sync Instructions

### Option 1: Pull from GitHub (Recommended)

```bash
cd /path/to/VerifiMind-PEAS
git pull origin main
```

This will automatically sync all new files:
- ✅ `docs/STANDARDIZATION_PROTOCOL.md`
- ✅ `mcp-server/src/verifimind_mcp/config/` (new directory)
- ✅ `mcp-server/src/verifimind_mcp/utils/retry.py`
- ✅ `mcp-server/src/verifimind_mcp/utils/metrics.py`
- ✅ `mcp-server/src/verifimind_mcp/agents/base_agent.py` (updated)
- ✅ `test_config_validation.py`
- ✅ `test_standardization.py`
- ✅ `examples/standardization_tests/config.json`

---

## Option 2: Manual File Creation (if needed)

If you need to manually create files (e.g., for Claude Desktop MCP integration):

### 1. Create Config Directory

```bash
mkdir -p mcp-server/src/verifimind_mcp/config
```

### 2. New Files to Create

**File 1:** `mcp-server/src/verifimind_mcp/config/__init__.py`
```python
"""Configuration module for VerifiMind PEAS."""

from .standard_config import (
    LLMConfig,
    RetryConfig,
    RateLimitConfig,
    MonitoringConfig,
    StandardConfig,
    DEFAULT_CONFIG,
)

__all__ = [
    "LLMConfig",
    "RetryConfig",
    "RateLimitConfig",
    "MonitoringConfig",
    "StandardConfig",
    "DEFAULT_CONFIG",
]
```

**File 2:** `mcp-server/src/verifimind_mcp/config/standard_config.py`
- **Size:** ~250 lines
- **Location:** Available on GitHub at commit `1a1db6f`
- **Download:** `git show 1a1db6f:mcp-server/src/verifimind_mcp/config/standard_config.py > standard_config.py`

**File 3:** `mcp-server/src/verifimind_mcp/utils/retry.py`
- **Size:** ~120 lines
- **Location:** Available on GitHub at commit `1a1db6f`
- **Download:** `git show 1a1db6f:mcp-server/src/verifimind_mcp/utils/retry.py > retry.py`

**File 4:** `mcp-server/src/verifimind_mcp/utils/metrics.py`
- **Size:** ~280 lines
- **Location:** Available on GitHub at commit `1a1db6f`
- **Download:** `git show 1a1db6f:mcp-server/src/verifimind_mcp/utils/metrics.py > metrics.py`

**File 5:** `mcp-server/src/verifimind_mcp/agents/base_agent.py` (UPDATED)
- **Changes:** Added `metrics` parameter to `analyze()` method
- **Lines changed:** ~30 lines
- **Download:** `git show 1a1db6f:mcp-server/src/verifimind_mcp/agents/base_agent.py > base_agent.py`

**File 6:** `test_config_validation.py`
- **Size:** ~350 lines
- **Purpose:** Validates standardization configuration
- **Download:** `git show 1a1db6f:test_config_validation.py > test_config_validation.py`

**File 7:** `test_standardization.py`
- **Size:** ~320 lines
- **Purpose:** Full standardization test suite
- **Download:** `git show 1a1db6f:test_standardization.py > test_standardization.py`

**File 8:** `docs/STANDARDIZATION_PROTOCOL.md`
- **Size:** ~500 lines
- **Purpose:** Comprehensive documentation
- **Download:** `git show 1a1db6f:docs/STANDARDIZATION_PROTOCOL.md > STANDARDIZATION_PROTOCOL.md`

**File 9:** `examples/standardization_tests/config.json`
- **Size:** ~50 lines
- **Purpose:** Exported configuration
- **Download:** `git show 1a1db6f:examples/standardization_tests/config.json > config.json`

---

## Option 3: Download Individual Files from GitHub

Visit: https://github.com/creator35lwb-web/VerifiMind-PEAS/tree/1a1db6f

Navigate to each file and download manually.

---

## Verification

After syncing, verify the installation:

```bash
# Run configuration validation tests
python3 test_config_validation.py
```

**Expected Output:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║           VerifiMind PEAS Standardization Protocol v1.0                      ║
║                      CONFIGURATION VALIDATION TESTS                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

================================================================================
OVERALL: 6/6 tests passed
================================================================================
🎉 ALL STANDARDIZATION TESTS PASSED!
```

---

## Claude Desktop MCP Integration

If you're using Claude Desktop with MCP:

### 1. Update MCP Server Code

The standardization files are now part of the MCP server. Simply pull the latest code:

```bash
cd /path/to/VerifiMind-PEAS
git pull origin main
```

### 2. Restart Claude Desktop

After pulling the latest code, restart Claude Desktop to reload the MCP server with the new standardization features.

### 3. Verify Integration

In Claude Desktop, you can now use the standardized validation:

```
Please validate this concept using the standardization protocol:
"AI-Powered Mental Health Chatbot"
```

The MCP server will now use:
- ✅ GPT-4 Turbo for X Agent
- ✅ Claude-3-Haiku for Z & CS Agents
- ✅ Temperature = 0.7
- ✅ Automatic retry on API errors
- ✅ Full metrics tracking

---

## File Structure After Sync

```
VerifiMind-PEAS/
├── mcp-server/
│   └── src/
│       └── verifimind_mcp/
│           ├── agents/
│           │   └── base_agent.py          ← UPDATED
│           ├── config/                     ← NEW
│           │   ├── __init__.py
│           │   └── standard_config.py
│           └── utils/
│               ├── retry.py                ← NEW
│               └── metrics.py              ← NEW
├── docs/
│   └── STANDARDIZATION_PROTOCOL.md        ← NEW
├── examples/
│   └── standardization_tests/             ← NEW
│       └── config.json
├── test_config_validation.py              ← NEW
├── test_standardization.py                ← NEW
└── SYNC_GUIDE.md                          ← THIS FILE
```

---

## Troubleshooting

### Issue: "Module not found: verifimind_mcp.config"

**Solution:**
```bash
# Ensure config directory exists
mkdir -p mcp-server/src/verifimind_mcp/config

# Pull latest code
git pull origin main

# Verify files exist
ls -la mcp-server/src/verifimind_mcp/config/
```

### Issue: "Module not found: verifimind_mcp.utils.metrics"

**Solution:**
```bash
# Ensure files exist
ls -la mcp-server/src/verifimind_mcp/utils/retry.py
ls -la mcp-server/src/verifimind_mcp/utils/metrics.py

# If missing, pull from GitHub
git pull origin main
```

### Issue: Tests fail with "BaseAgent.analyze() got an unexpected keyword argument 'metrics'"

**Solution:**
```bash
# Update base_agent.py
git checkout main -- mcp-server/src/verifimind_mcp/agents/base_agent.py

# Or pull latest
git pull origin main
```

---

## Summary

**Easiest Method:** Just run `git pull origin main` in your local VerifiMind-PEAS directory.

All files will be automatically synced from GitHub commit `1a1db6f`.

---

**Last Updated:** December 21, 2025  
**Commit:** `1a1db6f`  
**Status:** ✅ Pushed to GitHub
