# VerifiMind-PEAS Security Specification v1.0

**Version:** 1.0
**Effective:** v0.5.0 (March 2026)
**Author:** FLYWHEEL TEAM (Z-Agent lead, RNA implementation)

---

## Overview

This document formalizes the security model for VerifiMind-PEAS MCP Server.
Any new interface (CLI, web UI, SDK) built on top of this server **MUST** inherit
all sections of this specification — see the Security Inheritance Rule (Section 6).

---

## 1. Input Sanitization (since v0.3.5)

**What:** All `concept_name`, `concept_description`, and `context` inputs are
sanitized before reaching any LLM.

**Where:** `src/verifimind_mcp/utils/sanitization.py`

**Rules:**
- Prompt injection patterns detected and stripped (role overrides, instruction injections)
- Maximum input length enforced per field
- Sanitization warnings logged at WARNING level (never the raw injected content)
- `was_modified: true` flag returned in sanitized output for transparency

**Guarantee:** No unsanitized user input reaches an LLM prompt.

---

## 2. BYOK Key Handling (since v0.4.5)

**What:** Users may pass their own LLM API keys via tool call parameters.

**Where:** `src/verifimind_mcp/config_helper.py` → `create_ephemeral_provider()`

**Invariants:**
1. Keys are **ephemeral** — created per-tool-call, used once, garbage collected after the response
2. Keys are **never stored** — not in session state, history, validation records, or any file
3. Keys are **never logged** — all logging at DEBUG level must exclude api_key values
4. Keys are **never exposed in responses** — error messages use generic descriptions, not key values
5. Auto-detection (key prefix → provider) happens locally — the key itself is not transmitted for detection

**Session state rule:** `SessionContext` (v0.5.0) writes only scores and provider model names — never api_key values.

**Verification:** `tests/unit/test_v050_foundation.py::TestSecurityBoundaries::test_api_key_not_logged`

---

## 3. Rate Limiting (since v0.4.1)

**What:** Per-IP and global request rate limiting to prevent EDoS
(Economic Denial of Sustainability — excessive LLM API cost attacks).

**Where:** `src/verifimind_mcp/middleware/rate_limiter.py`

**Limits:**
- Per-IP: 10 requests per 60 seconds
- Global: 100 requests per 60 seconds

**Behavior on exceeded limit:** HTTP 429 response with `Retry-After` header.

**Bypass:** None. Rate limiting cannot be disabled by user parameters.

---

## 4. Z-Protocol Veto Rules

**What:** Z-Agent (Ethics Guardian) has hard VETO power over any concept
that crosses ethical bright lines.

**Where:** `src/verifimind_mcp/agents/z_agent.py`, response field `veto_triggered`

**Rules:**
1. Z-Agent VETO sets `veto_triggered: true` in the tool response
2. VETO **cannot** be overridden by user parameters (no `skip_veto` flag exists or will exist)
3. VETO propagates to Trinity synthesis: `synthesis.veto_triggered` reflects Z's decision
4. VETO does not suppress the response — the full analysis is returned with `veto_triggered: true`
   so users understand *why* the concept was flagged

**Guarantee:** The Z-Protocol guardian is always active in every tool call.

---

## 5. Audit Trail

| Layer | Mechanism |
|-------|-----------|
| Request-level | GCP Cloud Logging (production) |
| Per-run tracing | `_session_id` in Trinity responses (v0.5.0) |
| Validation history | `genesis://history/all` MCP resource |
| Security events | `logging.WARNING` for sanitization hits, BYOK auth failures |

---

## 6. Security Inheritance Rule

**Any new interface** (CLI, web UI, SDK, additional MCP tools) that invokes
VerifiMind agents MUST:

| Requirement | Mandatory |
|-------------|-----------|
| Inherit input sanitization (prompt injection detection) | ✅ Yes |
| Use ephemeral key handling (never store BYOK keys) | ✅ Yes |
| Respect Z-Protocol veto (cannot be disabled) | ✅ Yes |
| Apply rate limiting OR document why it is not needed | ✅ Yes |
| Maintain audit logging at the same level | ✅ Yes |
| Include `_session_id` or equivalent run correlation | ✅ Recommended |

**Reference for future CLI/UI work:** See `docs/future/quad-cli-proposal.md`
for the pending quad-cli design — it must satisfy all requirements above before
any implementation begins.

---

## 7. Known Limitations

| Item | Status | Mitigation |
|------|--------|------------|
| Per-IP rate limiting uses in-memory store | Resets on server restart | Acceptable for current scale |
| Trinity fallback (Gemini timeout) | Pre-existing since v0.4.3 | Retry logic in v0.5.0 |
| No cross-request BYOK usage telemetry | By design (privacy) | Anonymous aggregate stats in health endpoint |

---

*v1.0 — Effective v0.5.0 | FLYWHEEL TEAM Z-Agent lead, RNA implementation*
