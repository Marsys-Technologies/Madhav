---
artifact: JATAKA_CHART_WORKSPACE_CONTROLLED_PRODUCTION_ROLLOUT_ADDENDUM_v1_0.md
version: 1.1
status: ACTIVE
decision: CCD-018; CCD-019
session: JATAKA-CONTROLLED-PROD-ROLLOUT-20260927
branch: codex/jataka-chart-workspace; successor: codex/jataka-prod-schema-capability
worktree: /Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav
parent: JATAKA_CHART_WORKSPACE_PARALLEL_EXECUTION_AMENDMENT_v1_0.md
purpose: >
  Govern the one-time protected integration, production deployment and live acceptance of the
  reviewed Jātaka chart-workspace candidate without rewriting the completed source-phase records.
---

# Jātaka Chart Workspace — Controlled Production Rollout Addendum

## 1. Authority and exact exception

The native explicitly selected a controlled production rollout instead of creating a separate
non-production Firebase project and disposable local database. CCD-018 therefore supersedes only
the environment and external-action ceiling that kept Task 9 blocked. The completed parent and
Phase-A/A2/A3 addenda remain immutable historical records.

This addendum authorizes one bounded route from the reviewed local candidate to production:

1. refresh protected-main, open-PR and migration-collision evidence;
2. reconcile the candidate with current protected main and rerun all required gates;
3. obtain a focused pull request, required independent review and protected integration;
4. prove a fresh recoverable production backup and a credible restore/rollback path;
5. apply additive migrations 1120–1123 through the established governed deploy path;
6. deploy one exact accepted revision;
7. create one clearly named disposable production test chart and perform the live Task 9 flow;
8. verify data isolation, logs, migration state, service health and rollback readiness;
9. record the result, release the lease and close the session.

## 2. Production change envelope

The production envelope is limited to:

- the application and tests already governed by CCD-013 through CCD-017;
- additive migrations `1120_jataka_conversation_archive_context.sql`,
  `1121_jataka_correction_archive_write_guard.sql`,
  `1122_jataka_chart_context_staleness.sql` and
  `1123_jataka_context_staleness_deferred_surfaces.sql`;
- the repository's existing protected integration and deployment workflows;
- one newly created disposable production test chart owned by the operator's authenticated account;
- one bounded birth-detail correction/recompute on that same disposable chart;
- read-only production queries and logs needed to verify receipts, isolation and health.

No existing important chart may be edited, rebuilt, archived or deleted. No credential may be
printed, copied into the repository, rotated or persisted. No IAM, networking, Firebase, Cloud SQL,
runtime topology or unrelated database configuration change is authorized.

### CCD-019 — exact temporary schema-capability exception

The first controlled deploy attempt stopped at migration 1120 because the routine `amjis_app`
migration login intentionally has `USAGE` but not `CREATE` on the protected `public` schema. The
native explicitly authorized the narrow corrective production permission change on 2026-09-28.

CCD-019 permits one reviewed protected workflow to grant `CREATE ON SCHEMA public` to `amjis_app`
only for the exact migration set 1120–1123, then revoke it on every exit and attest the closed
state before any service deploys. The grant must be issued only through the existing
`data_plane_migrator` → `data_plane_schema_owner` delegate inside the protected production
environment and an explicit manual exact-SHA dispatch. It does not authorize a permanent grant,
role membership, credential/IAM change, direct SQL application, emergency override, different
migration, or any unrelated database mutation.

## 3. Mandatory pre-deploy gates

Deployment is prohibited until all of the following are recorded:

- exact feature head, protected-main head and merge candidate;
- clean worktree and reviewed candidate diff;
- current open-PR migration sweep confirming no collision with 1120–1123;
- migration guard and forward/backward compatibility review;
- scoped lint and TypeScript checks;
- full platform test suite and all affected Python checks;
- required independent review with no unresolved release-blocking finding;
- fresh production backup identifier plus restore or equivalent recovery proof;
- exact deployment workflow and last-known-healthy rollback target;
- active exclusive lease
  `MADHAV-JATAKA-CONTROLLED-PROD-ROLLOUT-20260927`.

Any failed gate stops the rollout. It is not converted to a warning merely because earlier local
evidence was green.

## 4. Deployment and rollback sequence

Use the existing protected branch and deployment mechanisms; do not bypass rules or invoke an
ad-hoc direct deployment. Observe the merge candidate through required checks, merge only when the
repository admits it, and bind production verification to the exact deployed revision.

Rollback triggers include migration failure, service-health regression, authentication or
authorization failure, cross-chart data leakage, more than one recompute, unexpected mutation of
an existing chart, broken historical-conversation semantics, or any material acceptance failure.
On trigger, halt immediately and return the application to the last healthy revision or submit a
reviewed revert through the protected path. Additive migrations may remain only when verified
backward-compatible and healthy; otherwise use a separately reviewed forward correction. Never
destructively reverse an applied migration.

## 5. Live acceptance protocol

Create a new production chart with a conspicuous name such as
`Jataka Rollout Test 2026-09-28`. Use synthetic, non-sensitive birth details. Do not select an
existing chart for correction testing.

Verify, with screenshots or equivalent receipts and exact timestamps:

1. the dashboard shows each chart with minimal information and progress, without Nirmāṇa or
   Paripraśna action buttons;
2. selecting the disposable chart opens its dedicated workspace;
3. the workspace shows the D1 Lagna chart, progress/readiness and the intended action surfaces;
4. a name-only edit persists without starting a build;
5. a birth-detail edit requires explicit confirmation;
6. confirmation causes exactly one recompute, preserves the chart UUID and reaches a terminal state;
7. while rebuilding, Paripraśna is unavailable and readiness is truthful;
8. prior conversations remain visible but are explicitly historical/read-only for the old context;
9. after readiness returns, the current-context Nirmāṇa and Paripraśna paths are available;
10. responsive, keyboard, reduced-motion and high-contrast behavior remain usable;
11. production logs and read-only database receipts show only the disposable chart and expected
    context-staleness/archive transitions.

If the live flow exposes a defect, stop and roll back or prepare a separate reviewed correction.
Do not patch production directly.

## 6. Close requirements

The final record must distinguish source, CI, protected integration, deployment and live acceptance.
It must include the deployed commit/revision, migration state, backup/recovery evidence, exact test
results, disposable chart identifier and disposition, production observations, rollback status and
the coordination lease release commit. Anything not directly proven remains `NOT_RUN` or `BLOCKED`.
