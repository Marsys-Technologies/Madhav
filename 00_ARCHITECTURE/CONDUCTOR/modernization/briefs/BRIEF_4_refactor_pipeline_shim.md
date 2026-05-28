---
status: COMPLETE
unit: 4.refactor_pipeline_shim
wave: 4
title: Move pipeline.run() bodies out of route.ts + retire the selector shim
stream: A
worktree: ../MadhavStreamA
blockedBy: [3.legacy_delete]
on_red: rollback
---

## Context (self-contained)
3.legacy_delete left a deprecated constant-true `MARSYS_FLAG_PIPELINE_SELECTOR` / `isPipelineSelectorEnabled()`
shim, and the cutover landed in `consult/route.ts` (post-Batch-1 rename) with some pipeline body still inline.
This small unit finishes the cleanup so the route is a pure thin selector.

## Scope
- Move any remaining `pipeline.run()` / pipeline body code out of `platform/src/app/api/chat/consult/route.ts`
  into the appropriate `platform/src/lib/pipelines/{single_pass|agentic|shared}/` module. The route file
  becomes only: auth + chart resolution + planner-context + `selectPipeline().run(ctx)`.
- Delete `isPipelineSelectorEnabled()` shim + `MARSYS_FLAG_PIPELINE_SELECTOR` constant + its references; remove
  the env var from `.github/workflows/deploy.yml`.

## Acceptance criteria (all automated)
1. `grep -rn "MARSYS_FLAG_PIPELINE_SELECTOR\|isPipelineSelectorEnabled" platform deploy.yml` returns nothing.
2. `consult/route.ts` has no inline pipeline body (LoC reduced; verifier check passes).
3. `npx vitest run platform/src/app/api/chat` green; no behaviour change.

## must_not_touch
`platform/src/lib/synthesis/panel/**` (active), `chart_facts`/`l25_*`, `platform/python-sidecar/**`.

## Commit cadence / rollback
Commits: (1) extract pipeline body to lib/pipelines, (2) delete shim + env var. Rollback = revert.
Operator follow-up (deferred): `gcloud run services update amjis-web --remove-env-vars MARSYS_FLAG_PIPELINE_SELECTOR`.
