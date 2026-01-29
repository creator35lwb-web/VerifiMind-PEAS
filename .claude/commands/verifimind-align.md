# /verifimind-align

Create an alignment update for Manus AI (CTO) in the PRIVATE repo.

## Usage

```
/verifimind-align [version] [summary]
```

## Workflow

1. **Gather information:**
   - Current server version
   - Changes since last alignment
   - Deployment status
   - Any blockers

2. **Create alignment issue in PRIVATE repo:**
   ```bash
   gh issue create --repo creator35lwb-web/verifimind-genesis-mcp \
     --title "[Alignment] v{VERSION} - {SUMMARY}" \
     --label cto-alignment \
     --body "{ALIGNMENT_TEMPLATE}"
   ```

3. **Template:**
   ```markdown
   # Alignment Update for Manus AI (CTO)

   **Date:** {date}
   **From:** Claude Code
   **Version:** {version}

   ## Summary
   {summary}

   ## Changes Implemented
   - {changes}

   ## Testing Results
   {test results}

   ## Deployment Status
   | Property | Value |
   |----------|-------|
   | Version | {version} |
   | Status | {status} |
   | URL | https://verifimind-mcp-server-690976799907.us-central1.run.app |

   ## Next Steps
   {next steps}

   ## Awaiting
   - [ ] CTO Review
   - [ ] CTO Approval
   ```

4. **Sync to PRIVATE repo:**
   - Ensure iteration/ folder is updated
   - Push any pending changes

## Example

```
/verifimind-align 0.4.0 "Unified Prompt Templates implementation complete"
```
