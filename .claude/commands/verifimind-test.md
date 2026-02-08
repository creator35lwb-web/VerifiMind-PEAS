# /verifimind-test

Test the VerifiMind-PEAS Trinity validation on the deployed server.

## Usage

```
/verifimind-test [concept_name] [concept_description]
```

## Workflow

1. **Initialize MCP session:**
   ```bash
   SESSION_ID=$(curl -s -i -X POST "https://verifimind.ysenseai.org/mcp/" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
     2>&1 | grep -i "mcp-session-id" | cut -d: -f2 | tr -d ' \r')
   ```

2. **Run Trinity validation:**
   ```bash
   curl -s -X POST "https://verifimind.ysenseai.org/mcp/" \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -H "mcp-session-id: $SESSION_ID" \
     -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"run_full_trinity","arguments":{"concept_name":"{CONCEPT_NAME}","concept_description":"{CONCEPT_DESCRIPTION}"}}}' \
     --max-time 180
   ```

3. **Parse and report results:**
   - X Agent score
   - Z Agent score + veto status
   - CS Agent score
   - Synthesis recommendation

## Default Test

If no arguments provided, use default test case:
- **Concept:** "Test Validation"
- **Description:** "A simple test to verify Trinity validation is working"

## Output Format

```markdown
## Trinity Validation Results

### Test Concept: {concept_name}

| Agent | Score | Status |
|-------|-------|--------|
| X Agent | {innovation}/{strategic} | {status} |
| Z Agent | {ethics} | {veto_status} |
| CS Agent | {security} | {vulnerabilities} |

### Synthesis
- **Overall Score:** {score}
- **Recommendation:** {recommendation}
- **Veto Triggered:** {yes/no}
```

## Example

```
/verifimind-test "AI Chatbot" "A customer service chatbot for e-commerce"
```
