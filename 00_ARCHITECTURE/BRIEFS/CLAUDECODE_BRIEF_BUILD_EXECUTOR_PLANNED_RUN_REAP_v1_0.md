# Build Executor + Stuck `planned` Run — Reap + Restore (paste into Claude Code / Antigravity)

**Read CLAUDE.md §C first.** This brief fixes the reason cockpit-triggered builds silently do nothing: the
web app enqueues a `build_runs` row but the **executor never runs it**, and the watchdog **cannot reap it**
because it's stuck in `planned` (not `running`). Surfaced 2026-06-18 while trying to clear three legitimately
`build_state_stale` L1 assets (`ga_sade_sati`, `ga_yoga`, `ga_transit_anchors`) via the cockpit.

## STANDING RAILS
FROZEN orchestrator contract (HALT if a contract change seems needed — this is an executor/ops + reaper gap,
NOT a writer change); surgical migrations only (≥ next free above 319), ledger-reconciled; **verify via the
ENDPOINT `/api/cockpit/stats?chart_id=482012f1-710e-4a25-994a-93821f5871aa`** (underscore param) AND
`/api/cockpit/runs/active?chart_id=...` — never DB-only, never a report's claim; only chart 482012f1;
floors = ACHIEVED count; branch-complete ≠ prod-true.

---

## THE DIAGNOSIS (code-verified 2026-06-18 — do not re-derive, just confirm still true)

The cockpit "Run plan" → `POST /api/cockpit/runs` (`platform/src/app/api/cockpit/runs/route.ts`):
1. Inserts a `build_runs` row in state `'planned'` + `build_run_assets` rows in `'queued'` (lines 63-80).
2. Calls `invokeRunJob(runId)` (line 84) to dispatch the **Cloud Run Job `brahma-build-pipeline-job`** (the
   actual executor) — and **swallows any error as "non-fatal"** (lines 83-87, comment: *"watchdog will reap
   if needed"*).

`invokeRunJob` (`platform/src/lib/build/jobInvoker.ts`) needs `GCP_PROJECT` + GCP creds and calls the prod
Cloud Run Job via `@google-cloud/run`. **On localhost it throws** (`readJobInvokerEnv` missing-env OR
`JobsClient()` no-creds) → the throw is swallowed → the run sits `planned` forever, `started_at=null`,
`current_asset_id=null`. Confirmed live: run `5b2975f2-fc92-4efd-9b2d-42e4656fcb7b` (rebuild, plan
`[ga_sade_sati]`) is stuck `planned`/`queued`. `/api/cockpit/status` reports `build: idle, queue: 0` — it
doesn't even count `planned` runs.

**The watchdog CANNOT fix this case.** `platform/src/app/api/cockpit/watchdog/route.ts` only reaps (1)
`build_runs` stuck **`running`** > 30 min and (2) `asset_throughput` stuck **`building`** > 15 min. A run
stuck in **`planned`** with `started_at=null` matches NEITHER predicate → it is a permanent phantom. Also the
watchdog is a prod-only Cloud Scheduler job (`provision_watchdog_scheduler.sh`), auth-gated by
`WATCHDOG_SECRET` (returns 401 locally).

So there are TWO defects:
- **D1 (executor):** cockpit-triggered runs are not executed in this environment (invokeRunJob fails, swallowed).
- **D2 (reaper gap):** even when working, a run that fails to dispatch is left `planned` forever — the watchdog
  has no `planned`-run reaper.

---

## TASK 1 — Reap the existing phantom run (data hygiene, surgical)

Run `5b2975f2-fc92-4efd-9b2d-42e4656fcb7b` (chart 482012f1) is stuck `planned`. Mark it `failed` (or `cancelled`
per the `build_runs.state` CHECK — VERIFY the allowed enum first; memory notes `build_steps.status` does NOT
allow `cancelled`, so CHECK `build_runs.state`'s constraint before writing) with an `ended_at` + a reason, and
its `build_run_assets` rows out of `queued`. Do this as a **one-shot surgical SQL against prod** (via the Cloud
SQL Auth Proxy / `start_db_proxy.sh`, port 5433 — data-plane is ALWAYS prod), not a migration. Then confirm via
`/api/cockpit/runs/active?chart_id=482012f1-...` returns NO active run, and `/api/cockpit/stats` is unchanged
(the three assets stay lit, still `build_state_stale: true` — reaping the run does NOT clear the cascade flag;
only a real rebuild does).

## TASK 2 — Make the executor actually run (the core fix; choose the right scope)

The goal: a "Run plan" click results in the run's writers executing and `asset_throughput` advancing. INVESTIGATE
which is true, then fix the smallest correct thing:
- **(a) Env/creds gap only:** if `invokeRunJob` is throwing purely because `GCP_PROJECT` / `BUILD_JOB_NAME` /
  ADC creds aren't present in the environment that's supposed to run builds → this is an **ops/config** fix
  (provide the env + creds so the web app can invoke `brahma-build-pipeline-job`). Confirm the Cloud Run Job
  `brahma-build-pipeline-job` exists + accepts `--run-id` (jobInvoker passes `['--run-id', runId]` +
  `MARSYS_RUN_ID`). This is the `brahma-pipeline` repo's contract — do NOT change the FROZEN writer contract.
- **(b) Swallowed-dispatch-failure visibility:** regardless of (a), the silent swallow at runs/route.ts:86 is a
  trap — a dispatch failure leaves the user with a phantom "building" UI and no signal. Make the dispatch
  failure **visible**: on `invokeRunJob` throw, mark the just-created run `failed` (with the error) instead of
  leaving it `planned`, and return a non-201 so the cockpit shows the failure. (This is the honest-failure fix;
  it turns D1 from "silent" into "surfaced" even when the executor is genuinely unavailable.)

**Decide (a) vs (b) vs both by INVESTIGATION, and if the fix would touch the FROZEN orchestrator contract or the
brahma-pipeline executor's own repo → STOP and report, don't reach across.** Likely answer: (b) in Madhav (make
the failure visible + don't leave `planned`), plus an ops note for (a) if the executor genuinely isn't wired to
this environment.

## TASK 3 — Close the watchdog reaper gap (D2)

Add a third reaper clause to `watchdog/route.ts`: a `build_runs` row stuck **`planned`** with `started_at IS
NULL` for > N minutes (propose 10; it never dispatched) → `failed`, with `last_error='orphan-watchdog: run
never dispatched'`, emit the `run.state_change` event. This protects against future swallowed-dispatch failures
even if Task 2(b) regresses. Keep the existing two thresholds **unchanged** (the file header forbids loosening
them — respect it). Add a unit test for the new clause. Do NOT provision/alter the Cloud Scheduler job here
(that's `provision_watchdog_scheduler.sh`, operator-run) — just make the endpoint reap `planned` orphans when it
fires.

## TASK 4 — Prove it end-to-end on the three stale assets (the real verification)

Once the executor runs (Task 2): trigger a rebuild of **`ga_sade_sati`** (asset scope) and watch it actually
execute — `build_runs` → `running` → `complete`, `asset_throughput.ga_sade_sati.last_built_at` advances past
2026-06-17. Then verify via `/api/cockpit/stats?chart_id=482012f1-...` that **`ga_sade_sati.build_state_stale`
flips `true → false`** with `actual_rows` still 11,019 (rebuild REPLACES, delete-then-insert — count must hold,
not grow). Repeat for **`ga_yoga`** (rows stay 5) and **`ga_transit_anchors`** (rows stay 45). These three are
legitimately stale because their upstream value-assets (ga_strength/ga_sensitive/ga_condition/ga_nakshatra/
ga_structural) were rebuilt after them on Jun-17/18 — the cascade flag is CORRECT; rebuilding absorbs the new
upstream data. (NOTE: builds serialize per chart — the runs POST 409s if a run is active — so run the three
**sequentially**, confirming each clears before starting the next.)

---

## DELIVERABLE + VERIFY (paste evidence, not claims)
- Task 1: phantom run `5b2975f2…` reaped; `/api/cockpit/runs/active` shows no active run (paste JSON).
- Task 2: a "Run plan" click now EITHER executes the build OR fails visibly (no more silent `planned`); say which
  path (a/b/both) and why, with the code diff.
- Task 3: watchdog reaps `planned`-orphans; unit test green; existing thresholds untouched.
- Task 4: all three assets rebuilt + `build_state_stale: false` on the endpoint, with counts held
  (11,019 / 5 / 45). Paste the before/after endpoint JSON for the three.
- FROZEN contract untouched (HALT-flag if it would change); CI green; migrations (if any) ledger-reconciled.

**This unblocks every cockpit-triggered build, not just these three flags** — until the executor runs, no
Build/Update/Rebuild click does anything, which matters before L2 Bodha (whose first act is a cockpit build of
bo_laksana).
