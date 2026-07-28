# DEPLOY_GCP.md — HARD-RETIRED (B-95-3)

**This document described the legacy `deploy-gcp.sh` path, which is
hard-retired** (T S95 review of PR #304): it deployed
`verifimind-mcp-server` without the attested build identity (no commit
bake, mutable `:latest` tag), which would allow a new artifact to inherit
an older artifact's failover evidence.

## Current deployment paths (the only authorized ones)

| Path | When | Identity attestation |
|---|---|---|
| Cloud Build trigger (root `cloudbuild.yaml`) | Every merge to PUBLIC `main` touching `mcp-server/**` | `--build-arg COMMIT_SHA=$COMMIT_SHA` → image-owned `/app/.build_commit_sha` |
| `./deploy-cloudrun.sh` (the `/verifimind-deploy` skill) | Deliberate manual releases | Clean-worktree + origin/main-parity guards, then `cloudbuild-image.yaml` bakes the verified commit |

`deploy-gcp.sh` is now a fail-closed stub (`exit 1`). The WP-B
deploy-surface inventory test machine-enforces that every same-service
deploy surface is either attested or non-executable.

*Retired 2026-07-25 per the B-95-3 repair contract. History preserved in git.*
