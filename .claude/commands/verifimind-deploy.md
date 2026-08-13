---
description: Guarded recovery-deployment wrapper for VerifiMind-PEAS; normal releases deploy through the authorized merge trigger.
version: 1.1
last-reviewed: 2026-08-10
---

# /verifimind-deploy

This public command is a **recovery wrapper**, not a second release recipe.
Normal production releases use the Cloud Build trigger created by an
authorized merge. That trigger already counts as the one deployment execution;
do not run this command after it starts or succeeds.

The private Command Central release orchestrator owns review, authorization,
provenance, smoke, Release, registry, post-deploy truth, and the private
receipt. This repository owns the executable recovery carrier.

## Use only for an authorized recovery

Run the recovery carrier only when the normal trigger is unavailable or failed
before producing an acceptable serving artifact, and Alton has authorized
recovery from an exact reviewed merge.

Before execution, prove all of the following:

- this checkout is `creator35lwb-web/VerifiMind-PEAS`;
- `HEAD` is the exact authorized merge on current `origin/main`;
- the worktree is clean, including untracked files;
- the intended version matches every discovered version assertion;
- the current serving revision and rollback source are recorded;
- no merge-trigger deployment for the same release is still running.

## Execute one canonical carrier

```bash
cd mcp-server
./deploy-cloudrun.sh
```

Do not reproduce or bypass the carrier's build, source-archive, image-identity,
or Cloud Run commands. If a guard fails closed, repair the cause and rebind the
authorization to any changed SHA.

## Required verification

After the single recovery execution:

1. Bind the source merge, build ID, immutable image identity, serving revision,
   traffic percentage, and rollback target.
2. Verify `/health`, `/setup`, and the server card agree on version,
   availability, routing, protocol, and failover semantics.
3. Run the versioned external smoke oracle and record PASS / STOP / INSTRUMENT
   separately.
4. Prepare exact deployment facts through a bounded docs-only truth PR. Do not
   push directly to public `main` or to the live Wiki.
5. Complete the GitHub Release, registry, and private receipt only through the
   Command Central release gate.

If authoritative serving-revision or smoke evidence cannot be recovered, mark
the release record incomplete. Never invent provenance to make the record look
finished.

---

*The executable carrier is `mcp-server/deploy-cloudrun.sh`; this wrapper adds
no independent deployment recipe.*
