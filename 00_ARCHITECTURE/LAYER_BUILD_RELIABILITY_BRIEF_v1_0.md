---
artifact: LAYER_BUILD_RELIABILITY_BRIEF_v1_0.md
canonical_id: LAYER_BUILD_RELIABILITY_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-24
purpose: >
  ANALYZE the entire press-Build-to-layer-complete path (Nirmāṇa build tracker UI → build API →
  build_run → Cloud Run orchestrator job → per-asset writers → tracker display) and FIX every point
  where a layer build can fail to complete. GOAL: when the operator presses Build for a layer in the
  cockpit on localhost, the orchestrator builds that layer COMPLETELY — every asset, in DAG order,
  every time — with the tracker showing true live progress. This must generalize to ALL layers
  (L1 now; L2/L3/L4 later by the same button). Claude Code does ANALYSIS + FIX only — it does NOT
  trigger any data build. The operator runs the build from the web page.
audience: Claude Code executor
constraints: L0 untouched; no data builds triggered by Claude Code; prod data plane; main only.
---

# Layer-Build Reliability — Analyze the Tracker + Orchestrator, Fix Press-Build-Builds-The-Layer

## §GOAL (the acceptance test, stated first)
Operator opens the Nirmāṇa build tracker on localhost:3000, selects a layer (start with L1 Gaṇita),
presses Build. Expected: the orchestrator builds EVERY asset of that layer, in correct dependency
order, to completion — no asset stuck "failed/reconnecting", no asset silently skipped, tracker
shows real live progress + final real row counts, and at the end the layer is fully lit. The SAME
must hold when the operator later presses Build on L2, L3, L4. Claude Code's job is to make this
true by analysis + fix. **Claude Code does not press Build or trigger any data generation — the
operator does.**

## §0 — Verified architecture map (Cowork, against main; build on this, confirm each)
The press-Build path, end to end:
1. **UI:** `platform/src/components/cockpit/` — `BuildButton.tsx` / `BuildControlsBar.tsx` POST to
   `/api/build/start` (also: continue, rebuild-all, stop). Live view: `LiveBuildGraph.tsx` subscribes
   to `/api/build/events/[buildId]` (SSE). Tracker state cards read `/api/cockpit/stats`.
2. **Plan assembly:** `/api/cockpit/plan/route.ts` + `/api/build/cascade/route.ts` topologically walk
   `depends_on`. `/api/build/data-readiness` calls `build_dependencies` "the authoritative DAG".
   ⚠ TWO DAG SOURCES exist — `build_dependencies` table AND `asset_registry.depends_on`. Divergence
   here = incomplete or mis-ordered plan.
3. **build_run:** `/api/build/start` inserts a `build_runs` row (scope / scope_target / plan JSONB /
   state). For a LAYER build the plan must be the full ordered asset list for that layer.
4. **Invocation:** `platform/src/lib/build/jobInvoker.ts` launches Cloud Run Job
   `brahma-build-pipeline-job` (asia-south1) with `--run-id`. ⚠ THE ORCHESTRATOR RUNS IN THE CLOUD
   JOB, NOT in localhost Next.js. Localhost only triggers + displays. The job image must carry current
   main's code (PyJHora + Phase-0 fixes) or the build runs stale code.
5. **Orchestrator:** `platform/python-sidecar/pipeline/orchestrator/runner.py` loads the build_run,
   acquires a chart advisory lock, walks `plan`, calls `run_asset()` per asset (FROZEN contract:
   savepoint per sub-step, heartbeat, delete-then-insert, asset_throughput state writes).
6. **Per-asset:** `@register('<asset_id>')` WriterBase subclasses; ga_ writers (8 engine-fed via
   pyjhora_adapter + 5 downstream).
7. **Display:** `asset_throughput` (state/rows_written) ← read by `/api/cockpit/stats` (now with the
   Phase-0 hybrid live-count fallback) ← rendered as tracker progress.

## §ANALYSIS — trace every failure point (read-only; produce a findings report FIRST)
Walk the path above and answer each, with file:line evidence. This is the core deliverable —
do NOT fix until the full failure-mode map is reported.

**A. Plan completeness + ordering (the "builds the WHOLE layer" question).**
- When `/api/build/start` is called with a LAYER scope, does it produce a plan containing EVERY
  active asset of that layer? Trace exactly how the layer's asset list is assembled. Is it from
  `asset_registry WHERE layer=$1 AND is_active=true`, from `build_dependencies`, or a mix?
- Are the two DAG sources (`build_dependencies` vs `asset_registry.depends_on`) CONSISTENT? If a
  layer's assets/edges differ between them, the plan can miss assets or mis-order them. Report any
  divergence per layer (focus L1 now; note the shape for L2-L4).
- Is the plan TOPOLOGICALLY SORTED so every asset's deps precede it (ga_structural after ga_condition
  + ga_nakshatra, etc.)? Where is the sort, and is it correct?
- Does a layer build correctly EXCLUDE service/on-demand assets (storage_type='service', e.g.
  transit anchors) from the data-build plan, or would it try to "build" them and stall?

**B. Invocation + image freshness (the "runs the RIGHT code" question).**
- Confirm `jobInvoker.ts` targets `brahma-build-pipeline-job` and passes `--run-id` correctly.
- How does the operator/localhost know the Cloud Run JOB image is current (PyJHora + Phase-0)? Is
  there any image-SHA surfacing, or can a stale job image silently run old code? If no guard, that's
  a finding — propose a pre-build check or a surfaced job-image SHA in the tracker.
- Localhost triggers a CLOUD job that writes PROD. Confirm the tracker on localhost correctly
  reflects a cloud-run build (SSE/polling reaches it). The earlier "failed/reconnecting" symptom may
  be the localhost tracker losing the cloud job's event stream, NOT the build actually failing —
  distinguish these.

**C. Per-asset failure + stall modes (the "no stuck asset" question).**
- The watchdog (orphan-run 30min / stuck-asset 15min, heartbeat per sub-step). Does every writer
  emit the heartbeat so a long-but-healthy asset (ga_dashas 536k rows) isn't falsely reaped?
- What happens on a single asset error mid-plan? `run_asset` marks it 'error' and continues (per the
  frozen contract). Does the tracker show that asset as failed AND does the layer build report
  incomplete, or does it look "done" with a silent hole? A layer that finishes with one errored
  asset must NOT read as complete.
- The "failed/reconnecting" assets the operator saw: trace the exact cause. Is it (a) a real writer
  error, (b) the SSE/tracker reconnect (display only), (c) a watchdog false-reap, or (d) asset_throughput
  state drift (the Phase-0 class of bug)? Name which, per asset.

**D. State + display truth (the "tracker tells the truth" question).**
- After the Phase-0 fix, does `/api/cockpit/stats` show real counts for a mid-build and completed
  layer? Does the per-asset state (building→lit / error / stale) match reality during a cloud-job run?
- Does the tracker distinguish "layer fully built" from "layer built except N errored"? The Build
  button's completion signal must be honest.

**E. Idempotency / re-press (the "press Build again safely" question).**
- If the operator presses Build on a layer that's partially built (or re-presses after a failure),
  does it cleanly resume/replace (delete-then-insert per asset) without duplicating or corrupting?
  Is there a guard against two concurrent build_runs for the same chart (the advisory lock)?

## §FIX — after the findings report, fix every failure mode found
Priorities (the brief's whole point — a layer Build that completes):
1. **Plan completeness:** ensure a layer-scope Build assembles the FULL, correctly-ordered, service-
   excluded asset list for that layer. If the two DAG sources diverge, reconcile to ONE authoritative
   source (or make the plan builder read the correct one) — and make it generalize to all layers.
2. **No silent incompletion:** a layer build that ends with any errored/skipped asset must report
   INCOMPLETE in the tracker, never green. Surface which asset failed and why.
3. **Stall/reconnect fixes:** fix whatever caused the "failed/reconnecting" assets — real error,
   watchdog false-reap, or SSE reconnect. If it's display-only (cloud job healthy, localhost lost the
   stream), fix the tracker's reconnect so a long cloud build stays visible.
4. **Image-freshness guard:** prevent a stale Cloud Run job image from silently running old engine
   code — surface the job image SHA, or gate the build on it matching main.
5. **Honest completion signal:** the tracker's "done" state must mean every layer asset is lit with
   real rows.
Keep every fix within the FROZEN orchestrator contract (no contract changes — if a fix seems to need
one, STOP and raise). L0 untouched. No data builds triggered.

## §VERIFY (how Claude Code proves the fix WITHOUT building data)
Claude Code cannot press Build (operator-only). So verification is:
- Unit/integration tests on the plan builder: a layer-scope request yields the full ordered,
  service-excluded asset list for L1 (and a synthetic L2/L3/L4 fixture proves it generalizes).
- DAG-consistency test: `build_dependencies` vs `asset_registry.depends_on` agree for every layer (or
  the single authoritative source is provably the one the plan uses).
- A test that a build_run ending with an errored asset reports incomplete, not complete.
- Tracker reconnect test (SSE drop → re-subscribe shows live cloud-job state).
- Report a READINESS STATEMENT: "press Build on layer X → these N assets build in this order; here is
  what now prevents silent incompletion / stall / stale-image." Then the OPERATOR runs the real build.

## §HANDOFF TO OPERATOR (what you do after Claude Code reports ready)
Once the path is fixed + tested, YOU (operator) drive the real run from localhost:3000:
1. Confirm the Cloud Run job image is current (the new guard will surface this).
2. Press Build on L1 (Gaṇita) for the chart you choose. Watch the tracker build the full layer.
3. Validate the PyJHora regeneration per the separate validation gates (FORENSIC 7/7 on native,
   value-diff vs snapshot, citation-resolution) — see L1_PYJHORA_REVALIDATION_REBUILD_BRIEF_v1_0.md,
   which now becomes the VALIDATION companion to this RELIABILITY brief.
4. Repeat for L2/L3/L4 as each layer's fixes are confirmed.

## §HARD CONSTRAINTS
- Claude Code does ANALYSIS + FIX + TESTS only. It NEVER presses Build or triggers data generation.
- L0 (Brahmagyan) untouched — no bg_ asset, no L0-scope anything.
- FROZEN orchestrator contract — fixes conform; a needed contract change is a STOP-and-raise.
- Prod data plane; main branch only; every merge auto-deploys (mind the cloud job image too).
- Findings report BEFORE fixes. Don't fix blind.
```
