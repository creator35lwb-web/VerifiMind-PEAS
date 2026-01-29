# /verifimind-handoff

Create a session handoff document for the next Claude Code session.

## Usage

```
/verifimind-handoff
```

## Workflow

1. **Gather session information:**
   - Work completed this session
   - Current server state
   - Pending CTO reviews
   - Files modified

2. **Create handoff document:**
   - Location: `iteration/Session_Handoff_{YYYYMMDD}.md`

3. **Template:**
   ```markdown
   # Session Handoff - {date}

   **Session ID:** {if available}
   **Agent:** Claude Code (Opus 4.5)

   ## Work Completed
   - {item 1}
   - {item 2}

   ## Current State
   | Property | Value |
   |----------|-------|
   | Server Version | {version} |
   | Deployment Status | {status} |
   | Pending CTO Reviews | {issues} |

   ## Next Session Should
   1. Read CLAUDE.md first
   2. {action 1}
   3. {action 2}

   ## Open Issues
   - {blockers}

   ## Files Modified This Session
   - {files}

   ## Protocol Reminder
   - All development → PRIVATE repo first
   - Create alignment issue for CTO
   - Wait for approval before PUBLIC sync
   ```

4. **Commit and push:**
   - Commit to PUBLIC repo
   - Sync to PRIVATE repo

## Output

Confirms handoff document created and synced to both repos.
