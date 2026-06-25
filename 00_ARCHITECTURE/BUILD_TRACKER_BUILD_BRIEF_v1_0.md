---
artifact: BUILD_TRACKER_BUILD_BRIEF_v1_0.md
canonical_id: BUILD_TRACKER_BUILD_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
parent: BUILD_TRACKER_HARDENING_MASTER_v1_0.md
purpose: Prove press-Build at layer scope drives the orchestrator through every in-scope asset in DAG order to completion, and that an errored asset never reads green.
audience: Claude Code (Antigravity)
---

# Build Hardening — "press Build → the whole layer lights, honestly"

## §0 — The path (audited)
UI → `POST /api/cockpit/runs` → `resolveBuildPlan` (reads `asset_registry.depends_on`, topo-sorts) →
insert `build_runs` (planned) + `build_run_assets` → `invokeRunJob(runId)` → Cloud Run Job
`brahma-build-pipeline-job` → `runner.py execute_run` walks `plan`, calls `run_asset` per asset,
skipping already-lit assets unless `action=='rebuild'`. Job image is built SEPARATELY from the web
app — `job_image_tag` is surfaced in the runs response.

## §1 — Audit findings this brief must close
- **F3:** `runner.py` sets `build_runs.state='completed'` UNCONDITIONALLY after the loop. "completed"
  = "plan walked", not "all assets healthy." The UI must NEVER paint a layer fully green if any asset
  errored — the error-count badge (from commit 0d79f13b) is the signal; verify it actually fires.
- **Plan completeness:** plan is built from `asset_registry WHERE is_active=true` filtered by layer.
  Confirm on prod that the L1 manifest is right (GATE P0): which `ga_*` are `layer='L1' AND
  is_active=true`, and that `ga_transit_anchors` is excluded as service-not-storage.
- **Stale job image:** a stale Cloud Run job image silently runs OLD orchestrator code. Always check
  `job_image_tag` in the runs response against the SHA you expect.

## §2 — Read-only pre-flight (GATE P0, run on prod :5433 first)
PASTE TO CLAUDE CODE:
```
Read-only on prod via :5433. Output the authoritative L1 build manifest:
  SELECT asset_id, layer, is_active, scope, asset_type, asset_kind,
         depends_on, target_table, count_sql
  FROM asset_registry WHERE layer='L1' ORDER BY sort_order;
Confirm: (a) which ga_ assets are is_active=true (these form the layer-build plan); (b) ga_transit_anchors
is asset_type/asset_kind='service' (excluded from a data build, shown service_ok); (c) every is_active
data asset has a non-null count_sql (else stats shows it 'error'/'missing_table'). List any data asset
with NULL count_sql as a pre-build gap. Do NOT build yet. Report the table.
```

## §3 — End-to-end layer build proof (on 1c826d5a ONLY)
Sequence the SAFE chart into a known-empty L1, then build the layer and prove every asset lights.
PASTE TO CLAUDE CODE (run after §2 is clean AND the CLEAR brief is PASS so you can trust the reset):
```
Prove a layer-scope Gaṇita build end-to-end on Abhinandan Mohanty
1c826d5a-41cb-4450-b4dc-59d440e5f75a (SAFE non-native). NEVER native 482012f1. Chrome read-tier →
mcp__Claude_in_Chrome__*. DB via :5433 is the arbiter. Web app on the SHA under test; CONFIRM the
Cloud Run job image is current (compare job_image_tag in the runs response to the latest job build —
if stale, rebuild/deploy the job image FIRST or STOP and report, since a stale image runs old code).

PRE: clear the Gaṇita layer on 1c826d5a (proven by the CLEAR brief) so it starts empty. Verify DB:
  every ga_ fact_category = 0, chart_dashas/chart_divisionals/ga_condition_composite = 0 for this chart.

BUILD: open http://localhost:3000/clients/1c826d5a-.../nirmana, press the Gaṇita LAYER Build control.
  Capture the POST /api/cockpit/runs response: record run_id, plan (the full asset list + order),
  asset_count, and job_image_tag. Assert plan == the is_active L1 data assets from §2 (no missing
  asset, no L0/global asset, no service asset).

WATCH to completion: poll /api/cockpit/runs/[id] (or the SSE/tracker). Record per-asset transitions
  queued→building→lit. When build_runs.state='completed', capture build_run_assets states.

PROVE (DB arbiter):
  - every in-scope ga_ asset has rows > 0 in DB (per-asset count) matching its target;
  - asset_throughput.state='lit' + rows_written populated for each;
  - the tracker shows each asset lit with a count == DB count (REFRESH fix must hold here too).
HONESTY CHECK (F3): if ANY asset errored, assert build_run_assets shows its error AND the layer header
  shows a non-zero error badge AND the layer is NOT painted fully green despite state='completed'.
  If a layer with an errored asset reads all-green, that's an F3 regression → report it.

Deliver: the runs response (plan + job_image_tag), the per-asset queued→lit timeline, the BEFORE(empty)
/AFTER(lit) DB counts per asset, a screenshot of the completed layer, and a PASS/FAIL with any errored
asset called out. STOP and report.
```

## §4 — Likely hardening edits (apply only if §3 surfaces them)
- If `state='completed'` ever co-exists with a green-looking layer that has errors → fix the UI
  badge/derivation (NOT runner.py — the contract is FROZEN; the truth is in build_run_assets +
  asset_throughput, the UI must read it).
- If a NULL-count_sql data asset shows perpetual 'error' post-build → add its chart-scoped count_sql
  to `asset_registry` (the "cockpit truth" standard, §N.4). This is the L1 trap from prior closure.
- If the job image was stale → document the job-image deploy step in the runbook (separate from web).

## §5 — Done when
Pressing layer-Build on an empty 1c826d5a lights every in-scope L1 data asset to DB-confirmed rows,
the tracker count == DB count per asset, and any errored asset is surfaced (badge + non-green) rather
than hidden behind state='completed'.
