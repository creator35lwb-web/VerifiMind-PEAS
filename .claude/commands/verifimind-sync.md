# /verifimind-sync

Sync approved changes from PRIVATE repo to PUBLIC repo.

## Usage

```
/verifimind-sync [files...]
```

## Pre-requisites

- CTO approval on alignment issue in PRIVATE repo
- Changes committed in PRIVATE repo

## Workflow

1. **Verify CTO approval:**
   ```bash
   gh issue list --repo creator35lwb-web/verifimind-genesis-mcp --label approved
   ```

2. **Pull latest from PRIVATE repo:**
   ```bash
   cd /c/Users/weibi/OneDrive/Desktop/verifimind-genesis-mcp-private
   git pull origin main
   ```

3. **Copy approved files to PUBLIC repo:**
   ```bash
   # For each file
   cp {PRIVATE_REPO}/{file} {PUBLIC_REPO}/{file}
   ```

4. **Commit to PUBLIC repo:**
   ```bash
   cd "C:\Users\weibi\OneDrive\Desktop\VerifiMind Project 2025"
   git add {files}
   git commit -m "feat: Sync approved changes from PRIVATE repo

   Approved in: {issue_url}

   Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
   git push origin main
   ```

5. **Update alignment issue:**
   - Add comment noting sync complete
   - Close issue if all changes synced

## Files That Should Sync

| From PRIVATE | To PUBLIC | When |
|--------------|-----------|------|
| mcp-server/src/** | mcp-server/src/** | After approval |
| CHANGELOG entries | CHANGELOG.md | After release |
| Documentation | docs/ | After review |

## Files That Should NOT Sync

| File | Reason |
|------|--------|
| iteration/CTO_Report_*.md | Internal only |
| Cost analysis | Sensitive |
| Security investigations | Pre-patch |

## Example

```
/verifimind-sync mcp-server/src/verifimind_mcp/templates/
```
