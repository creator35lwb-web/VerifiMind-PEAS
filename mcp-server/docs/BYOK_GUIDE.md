# BYOK (Bring Your Own Key) Guide — v0.4.5+

Use your own LLM API keys for any or all agents, or use the server's free defaults.
Keys are **ephemeral** — used per-tool-call, never stored, never logged.

---

## Step 1: Connect (Required — Clears Schema Cache)

MCP clients cache tool schemas. You must reconnect to see the BYOK parameters:

```bash
# Remove stale connection
claude mcp remove verifimind-gcp -s user

# Re-add with fresh connection
claude mcp add -s user verifimind-gcp -- npx -y mcp-remote https://verifimind.ysenseai.org/mcp/

# IMPORTANT: Start a NEW Claude Code session after reconnecting
```

---

## ⚠️ Important: Where to Enter Your API Key

**DO NOT paste your API key into the Claude.ai web chat window.**

Since Opus 4.7, Claude's safety classifier actively detects and blocks API keys,
secrets, and credentials typed in conversation text — this is an Anthropic privacy
protection at the conversation layer.

**BYOK only works through the MCP tool parameter in Claude Code.** The key travels
as a JSON tool argument to the VerifiMind server — a completely separate code path
that the conversation-layer classifier does not scan.

| Surface | How to use BYOK | Works? |
|---------|-----------------|:------:|
| **Claude Code (CLI)** | Pass `api_key` as tool argument | ✅ Correct |
| **Claude.ai web chat** | Do NOT type key in chat window | ❌ Blocked |

**In Claude Code, use it like this:**

```
run_full_trinity(
  query="Your validation question",
  api_key="gsk_..."   ← goes as tool argument, not chat text
)
```

---

## Step 2: Use BYOK

### Single Agent

In `consult_agent_x`, `consult_agent_z`, or `consult_agent_cs`:

```
api_key: "gsk_..."          # Your key — auto-detected as Groq from gsk_ prefix
llm_provider: "groq"        # Optional — auto-detected if omitted
```

### Full Trinity — Global Key (All Agents)

In `run_full_trinity`:

```
api_key: "gsk_..."          # All agents (X, Z, CS) use your Groq key
```

### Full Trinity — Per-Agent Override

```
x_api_key: "gsk_..."        # X uses your Groq key
z_api_key: "sk-ant-..."     # Z uses your Anthropic key
# cs_api_key omitted        # CS uses server default (free Groq)
```

---

## Auto-Detection (Key Prefix → Provider)

| Key Prefix | Provider Auto-Detected |
|-----------|------------------------|
| `sk-ant-` | Anthropic (Claude) |
| `gsk_`    | Groq (llama-3.3-70b) |
| `sk-`     | OpenAI (GPT) |
| `AIza`    | Gemini |
| `csk_`    | Cerebras |

> **Note:** `sk-ant-` is checked before `sk-` to prevent Anthropic keys being misrouted to OpenAI.

---

## Response Fields

Every BYOK response includes:

| Field | Type | Description |
|-------|------|-------------|
| `_byok` | bool | `true` if your key was used for this call |
| `_provider_used` | string | Model that served this agent (e.g. `groq/llama-3.3-70b-versatile`) |
| `_byok_agents` | dict | *(Trinity only)* Per-agent BYOK status: `{X: true, Z: false, CS: false}` |
| `_providers_used` | dict | *(Trinity only)* Per-agent model name |
| `_session_id` | string | *(Trinity only)* 8-char unique run ID for log correlation |

---

## Free Providers (No Key Needed)

The server runs on free-tier APIs by default — no key required:

| Provider | Free Tier | Sign Up |
|----------|-----------|---------|
| **Groq** | ✅ Free (rate limited) | [console.groq.com](https://console.groq.com) |
| **Gemini** | ✅ Free (rate limited) | [aistudio.google.com](https://aistudio.google.com) |
| **Cerebras** | ✅ Free (1M tokens/day) | [cloud.cerebras.ai](https://cloud.cerebras.ai) |

---

## Supported Providers (BYOK)

| `llm_provider` value | Model Used | Notes |
|----------------------|------------|-------|
| `groq` | `llama-3.3-70b-versatile` | Fast, free tier available |
| `anthropic` | `claude-sonnet-4-6` | High quality, paid |
| `openai` | `gpt-4.1-mini` | Paid |
| `gemini` | `gemini-2.5-flash` | Free tier available |
| `cerebras` | `llama3.1-70b` | Free tier available (1M tokens/day) |
| `mistral` | `mistral-small-latest` | Paid |
| `mock` | `mock/test-model` | Testing only (no real inference) |

---

## Troubleshooting

**"No `api_key` parameter in tool schema"**
→ Your MCP client has a stale cache. Follow Step 1 above to reconnect.

**`error_code: BYOK_AUTH_FAILED`**
→ Your key is invalid or expired. Check the key matches the provider (e.g. `gsk_` = Groq).

**`error_code: PROVIDER_TIMEOUT`**
→ The LLM provider timed out. Try again, or switch to `llm_provider: "groq"` for lower latency.

**BYOK result looks identical to non-BYOK**
→ Check `_byok: true` in the response. If `false`, the key was not accepted (possibly empty string).

---

## Model Freshness

VerifiMind-PEAS tracks provider model deprecations monthly. If a provider
retires a model, the BYOK Guide and `provider.py` will be updated within
7 days of the deprecation announcement.

| Provider | Current Default | Stable Until |
|----------|----------------|:------------:|
| Groq | `llama-3.3-70b-versatile` | No notice issued |
| Gemini | `gemini-2.5-flash` | Jun 17, 2026 (then → `gemini-2.5-flash-latest`) |
| Anthropic | `claude-sonnet-4-6` | No confirmed EOL |
| OpenAI | `gpt-4.1-mini` | No confirmed EOL |
| Cerebras | `llama3.1-70b` | No notice issued |
| Mistral | `mistral-small-latest` | Stable alias — auto-tracks |

If you hit `model_not_found` errors, check our
[changelog](https://verifimind.ysenseai.org/changelog) for the latest default models.
