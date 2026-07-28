# /verifimind-deploy

Deploy VerifiMind-PEAS to GCP Cloud Run — by delegating to the ONE guarded
canonical implementation.

## Usage

```
/verifimind-deploy [version]
```

## Workflow

**This command maintains NO build or deploy recipe of its own** (B-96-1:
a duplicated recipe here once bypassed the provenance guards — the skill
now delegates exclusively). All guards live in the canonical script:
clean-worktree check, `origin/main` parity, exact-committed-bytes source
archive, image-baked build identity.

1. **Pre-flight checks:**
   - Verify GCP authentication
   - Check current server health
   - Confirm the version number matches `SERVER_VERSION`

2. **Build + deploy — delegate to the canonical guarded script:**
   ```bash
   cd mcp-server
   ./deploy-cloudrun.sh
   ```
   Do NOT invoke the underlying build or run commands directly; if the
   script's guards fail closed (dirty worktree, unpushed HEAD), fix the
   cause — never bypass.

3. **Post-deployment:**
   - Verify health check (`/health` serves the new version)
   - Update SERVER_STATUS.md
   - Commit and push changes

4. **Update PRIVATE repo:**
   - Create alignment issue for CTO
   - Sync deployment status

## Example

```
/verifimind-deploy 0.5.55
```
