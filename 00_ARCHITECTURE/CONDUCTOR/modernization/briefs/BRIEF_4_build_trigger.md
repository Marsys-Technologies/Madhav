---
status: COMPLETE
unit: 4.build_trigger
wave: 4
title: Wire the dashboard Build button to the autonomous chart-build Job
stream: B
worktree: ../MadhavStreamB
blockedBy: [3.consult_nav, 3.legacy_delete]
on_red: halt_queue   # touches prod build orchestration — surface on failure
---

## Context (self-contained)
`marsys-build-pipeline-job` exists as a Cloud Run Job but has no in-app trigger (only manual `gcloud run jobs
execute`). Master-plan §4.2-1 + §5.4: web enqueues a Cloud Task → executor invokes the Job → progress streams
to cockpit via the existing `build_events` SSE rail (the same one the tracker uses).

## Scope
- Provision a Cloud Task queue (`amjis-build-queue`) via IaC; web posts a task on Build/Rebuild from
  `app/clients/[id]/build`.
- Server-side task handler invokes the Cloud Run Job (`amjis-builder` / `marsys-build-pipeline-job`) with
  `{chart_id, ayanamsha_role}`; Job streams progress rows to `build_events`.
- Cockpit `/clients/[id]/build` subscribes to the existing SSE rail and shows the two-level progress UX
  (cross-asset + within-asset) per PLATFORM_REBUILD §4.4.
- Reuse the per-asset verification + freeze-old archive pattern 2a established. Zero-touch prod deploy with
  smoke + auto-rollback.

## Acceptance criteria (all automated)
1. Build action on the native chart enqueues a Cloud Task; the Job runs; build_events rows persist; the
   cockpit reflects progress (click-through mount test).
2. End-to-end smoke: a Rebuild for the native completes green; failure path auto-rolls back the staging swap.
3. authorizeChartAccess gates Build — only the chart's owner or super_admin can trigger.

## must_not_touch
`platform/src/lib/retrieve/**`, `platform/src/lib/pipelines/**`, `platform/src/lib/synthesis/panel/**`.

## Commit cadence / rollback
Commits: (1) Cloud Task queue IaC + task handler, (2) Build action wiring + cockpit progress, (3) end-to-end
smoke. Rollback = revert + flag the Build action off behind the new feature flag (default off until smoke green).
