# VerifiMind-PEAS Server Status

**Last Updated:** January 29, 2026

---

## Current Status: Maintenance Required

We have identified configuration issues affecting the public MCP server at `https://verifimind.ysenseai.org`. We are actively working to resolve these.

---

## Known Issues

### Issue #1: Gemini Model Update Required

**Status:** Code Fix Ready - Pending Deployment
**Severity:** High
**Affected:** All agent consultations (X, Z, CS)

**Description:**
The server is configured with `gemini-2.0-flash-exp` which has been deprecated by Google. This causes a 404 error when attempting to use any agent.

**Error Message:**
```
404 models/gemini-2.0-flash-exp is not found for API version v1beta
```

**Resolution:**
- Code fix implemented in v0.3.1 (see CHANGELOG.md)
- Changed default model to `gemini-1.5-flash` (stable, FREE tier)
- Awaiting server redeployment

---

### Issue #2: API Key Renewal

**Status:** Scheduled
**Severity:** Medium
**Affected:** Premium model features

**Description:**
Certain API keys require renewal for continued service.

**Resolution:** API key renewal in progress

---

## Workarounds

While we resolve these issues, you can:

1. **Use BYOK (Bring Your Own Key):** Configure your own API keys in Claude Desktop
2. **Self-Host:** Run your own instance with your API keys

### BYOK Quick Setup

```bash
# Set your own Gemini API key (FREE tier available)
export LLM_PROVIDER="gemini"
export GEMINI_API_KEY="your-api-key"
```

Get a free Gemini API key: https://aistudio.google.com/apikey

---

## Server Information

| Property | Value |
|----------|-------|
| Endpoint | `https://verifimind.ysenseai.org/mcp` |
| Health Check | `https://verifimind.ysenseai.org/health` |
| Server Version | 0.3.1 (pending deployment) |
| Transport | Streamable HTTP (SSE) |

---

## Updates

We will update this status page as issues are resolved. For real-time updates:

- **GitHub Issues:** [Report or track issues](https://github.com/creator35lwb-web/VerifiMind-PEAS/issues)
- **GitHub Discussions:** [Community support](https://github.com/creator35lwb-web/VerifiMind-PEAS/discussions)

---

## Maintenance Schedule

| Date | Action | Status |
|------|--------|--------|
| Jan 28, 2026 | Issue identified | Complete |
| Jan 28, 2026 | Code fix implemented (v0.3.1) | Complete |
| TBD | Server redeployment | Pending |
| TBD | API key renewal | Pending |
| TBD | Service restoration | Pending |

---

**Thank you for your patience as we work to restore full service.**

*VerifiMind-PEAS Team*
