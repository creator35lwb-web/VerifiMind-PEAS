# /verifimind-status

Check the current status of VerifiMind-PEAS deployment and repos.

## Usage

```
/verifimind-status
```

## Workflow

1. **Check server health:**
   ```bash
   curl -s https://verifimind-mcp-server-690976799907.us-central1.run.app/health
   ```

2. **Check PUBLIC repo status:**
   ```bash
   cd "C:\Users\weibi\OneDrive\Desktop\VerifiMind Project 2025"
   git status
   git log --oneline -5
   ```

3. **Check PRIVATE repo status:**
   ```bash
   gh issue list --repo creator35lwb-web/verifimind-genesis-mcp --label cto-alignment
   ```

4. **Report summary:**
   - Server version and health
   - Pending CTO reviews
   - Recent commits
   - Any uncommitted changes

## Output Format

```markdown
## VerifiMind-PEAS Status

### Server
- Version: {version}
- Status: {healthy/unhealthy}
- URL: https://verifimind-mcp-server-690976799907.us-central1.run.app

### Repos
- PUBLIC: {clean/dirty}
- PRIVATE: {pending issues}

### Pending CTO Reviews
- {list of open alignment issues}
```
