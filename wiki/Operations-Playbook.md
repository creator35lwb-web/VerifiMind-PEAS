# Operations Playbook

> **Document boundary — playbook.** This page defines repeatable release, verification, rollback, incident, and truth-update procedures. It does not declare what is currently live; compare its gates with [Current Production Status](Current-Production-Status).

The operating rule is simple: **a public claim is downstream of evidence**. A merge is not a deployment, a deployment is not a verified release, and containment is not incident closure.

## Evidence chain

Every production release must bind this chain:

```text
authorized scope
  -> reviewed source SHA
  -> required CI/security checks at that SHA
  -> build ID and immutable source identity
  -> serving deployment and rollback target
  -> live protocol/discovery checks
  -> real-inference smoke
  -> GitHub Release at the deployed SHA
  -> MCP Registry publication at the same SHA
  -> production-status and disclosure update
```

If a link is unknown, record it as unknown and stop the affected claim. Never reconstruct an identifier from memory or a nearby release.

## Roles

| Role | Responsibility |
|---|---|
| Human release owner | authorizes scope, deployment, rollback, and public close |
| Implementation owner | prepares the bounded change and evidence plan |
| Independent reviewer | verifies the exact candidate SHA and high-risk negative paths |
| Security reviewer | checks secrets, authorization, data paths, and incident constraints |
| Operations recorder | captures build, revision, smoke, release, registry, and truth-update evidence |

One person may perform more than one role in a small project, but the record must not imply independence that did not exist.

## Release procedure

### Gate 0 — freeze the release contract

Before merge, record:

- candidate source SHA and intended base;
- expected server and registry metadata versions;
- expected MCP protocol version;
- expected defined/active/unavailable tool inventory;
- expected default seat/provider/model routes;
- expected runtime failover state;
- rollback source or serving revision;
- required tests, reviewers, and smoke assertions; and
- whether a public statement or policy update is required.

Any unreviewed change to those expectations reopens the gate.

### Gate 1 — review the exact bytes

- Work from the canonical public repository and protected-branch workflow.
- Prove the candidate SHA before accepting test or review evidence.
- Require all substantive checks to complete successfully at that SHA.
- Treat cancelled, skipped, stale, or unrelated-SHA evidence as absent unless the release contract explicitly permits it.
- Preserve the merge parent and rollback target before deployment.

### Gate 2 — merge once, deploy once

For a normal release touching `mcp-server/**`, the protected-main Cloud Build trigger is the deployment lane. Do not follow the trigger deployment with a second manual deployment.

The repository’s canonical manual carrier, `mcp-server/deploy-cloudrun.sh`, is reserved for an explicitly authorized recovery or non-trigger lane. Wiki and command documentation must not embed a second standalone `gcloud builds submit` or `gcloud run deploy` recipe.

Capture the exact merge SHA, build ID, resulting serving revision, deployment time, and rollback target. A build tagged only by a mutable version is insufficient provenance.

### Gate 3 — verify the public boundary

Check the production hostname, not a guessed platform URL:

1. `/health` returns success and the expected server version, protocol, tool counts, provider routes, storage state, and failover state.
2. `/setup` agrees with the discovery and availability contract.
3. `/mcp/` completes a real MCP initialize and tool-list exchange using the expected protocol.
4. Redirecting surfaces such as `/changelog` resolve to their intended canonical location.
5. Terms, Privacy Policy, and security-reporting links render and agree with their canonical sources.

Printing a response is not a check. Each expected field must be asserted and a mismatch must stop the release.

### Gate 4 — run real-inference smoke

Static health cannot prove provider inference. Exercise the release-specific Trinity paths and classify every assertion:

- **PASS:** the product behavior matches the contract.
- **STOP:** a product or release-contract failure; do not close the release.
- **INSTRUMENT:** the test harness, credentials, quota, or observation mechanism failed; repair the instrument and rerun before drawing a product conclusion.

Smoke must cover the happy path and the release’s risk delta. For degradation work, include typed single-seat failure and all-seat failure. Verify that successful seats remain, failed-seat fields are withheld, the result is incomplete, provenance is visible, and incomplete runs are not persisted.

### Gate 5 — bind public distribution

- The GitHub Release tag must resolve to the deployed merge SHA.
- The MCP Registry publication workflow must succeed at that same SHA.
- Registry metadata must match the intended server card and active/unavailable description.
- A surviving older registry entry does not make a failed new publication harmless.

### Gate 6 — update public truth

A trigger-generated build or serving revision cannot be known before merge. Use a two-stage documentation sequence:

1. The release PR contains candidate-safe wording and no claim that it is live.
2. After deployment verification, a bounded follow-up PR records exact production facts in `CHANGELOG.md`, the server status source, and [Current Production Status](Current-Production-Status).

Only after that truth update may an announcement say the release is live. If the change requires a durable disclosure, add or amend the trust ledger according to its correction policy.

### Gate 7 — close the record

The release receipt should contain:

- source and release SHA;
- required-check and review results;
- build ID and serving revision;
- rollback target and whether it was used;
- smoke PASS/STOP/INSTRUMENT totals and detailed artifact;
- GitHub Release URL and exact target;
- registry workflow URL and result;
- production-status/truth PR; and
- remaining risks, owners, and next review date.

## Stop conditions

Stop or hold the release when any of the following applies:

- source is dirty, unreviewed, or not at the declared SHA;
- required CI/security evidence is missing or belongs to another SHA;
- the wrong cloud project, service, region, or image identity is selected;
- the live version, protocol, tool inventory, provider route, or failover state differs from the release contract;
- any smoke assertion is STOP;
- an INSTRUMENT result remains unresolved;
- the serving revision or rollback target is unknown;
- release or registry target differs from the deployed SHA; or
- public text would overstate deployment, incident closure, legal status, or test coverage.

## Rollback

Rollback is a controlled production change, not a way to erase a release record.

1. Preserve evidence before changing traffic.
2. Obtain human authorization for the rollback target.
3. Move traffic or redeploy only through the approved carrier.
4. Re-run health, discovery, and risk-focused smoke against the restored version.
5. update production status and release notes with the rollback fact.
6. Keep published statements and incident records; correct them by dated addendum.

A GitHub Release, public statement, or commit cannot be made “unpublished” by rolling back Cloud Run.

## Incident procedure

Use distinct states:

```text
reported -> triaged -> contained -> remediated -> independently verified -> authorized to restore -> closed
```

- **Contained** means the vulnerable path can no longer be exercised under the tested conditions.
- **Remediated** means the underlying control has been implemented.
- **Closed** additionally requires evidence, owner approval, documentation, and any separate legal/privacy track.

For security or privacy incidents, preserve logs and timestamps, minimize access, avoid public personal data, and keep legal conclusions with qualified counsel. See [Trust and Safety](Trust-and-Safety).

## Routine status review

At each release and scheduled review:

- compare live `/health` and `/setup` with the status page;
- compare release tag, deployed SHA, registry version, and recorded build/revision;
- verify unavailable tools fail in the documented way;
- check that public statements still describe open matters accurately;
- mark metrics with their observation date; and
- open a bounded truth correction when any source disagrees.

The current worked evidence set is recorded in [Current Production Status](Current-Production-Status). The durable method remains in [Genesis Methodology](Genesis-Methodology) and [Architecture](Architecture).
