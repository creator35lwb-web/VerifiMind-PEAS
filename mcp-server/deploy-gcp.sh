#!/bin/bash
# ============================================================================
# HARD-RETIRED (B-95-3, T S95 review of PR #304) — DO NOT USE
# ============================================================================
#
# This legacy path deployed verifimind-mcp-server WITHOUT the attested build
# identity (no COMMIT_SHA bake, mutable :latest tag), which would let a new
# artifact inherit an older artifact's failover evidence. Every live
# deployment must go through one of the two attested paths:
#
#   - the Cloud Build trigger (root cloudbuild.yaml), or
#   - ./deploy-cloudrun.sh (clean-worktree + remote-parity guards, then
#     cloudbuild-image.yaml bakes the verified source commit into the image).
#
# This stub exists (rather than deletion) so the retirement is explicit,
# discoverable, and MACHINE-ENFORCED: the WP-B deploy-surface inventory test
# asserts this file fails closed. RETIREMENT-STUB-MARKER: deploy-path-retired
# ============================================================================

echo "ERROR: deploy-gcp.sh is HARD-RETIRED (B-95-3)." >&2
echo "Use ./deploy-cloudrun.sh (attested build identity) instead." >&2
exit 1
