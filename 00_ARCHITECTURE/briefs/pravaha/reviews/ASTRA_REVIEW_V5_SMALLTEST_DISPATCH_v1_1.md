VERDICT: REJECT

The inactive registry row **allows execution** through the frozen runner path. The remaining blockers concern recovery, another writer-skip path, and interrupted replacement.

Reviewed `2240aa4c…508561b7`. All **87 dispatch tests passed**. Both slice manifests passed the real runner validator and matched the local writer digest. No files were modified; no database or network was accessed.

1. **P2 — The advertised recovery lookup fails when the uncertain commit actually succeeded. Blocks production: YES.**

   [dispatch_v5_small_test_job.py:404](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-disp2/platform/scripts/dispatch_v5_small_test_job.py:404) inserts another planned run before printing the existing-run listing at lines 455–460. Migration `platform/supabase/migrations/595_nirmana_frozen_run_manifest.sql:30–32` prohibits two active runs for the chart.

   **Scenario:** COMMIT succeeds but its acknowledgement is lost. Following the recovery instruction immediately produces a unique-index violation, before the original run ID is displayed. The failure names the *new* attempted ID.

   I reproduced this control flow by injecting SQLSTATE `23505` into the recording fake: the listing query ran, but its results never appeared. This was an in-memory reproduction, not PostgreSQL execution. The test at `test_dispatch_v5_small_test.py:723–733` passes because its fake permits the duplicate active run.

   **Fix:** provide a lookup-only recovery path that reports the requested existing ID independently of admission checks and staging.

2. **P2 — Registry admission does not exclude the runner’s “probe green” shortcut. Blocks production: YES.**

   [dispatch_v5_small_test_job.py:155](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-disp2/platform/scripts/dispatch_v5_small_test_job.py:155) does not validate `rebuild_on_probe_fail`, `integrity_check_sql`, or the data/service routing fields. In `platform/python-sidecar/pipeline/orchestrator/asset_runner.py:1591–1615`, a configured check plus `rebuild_on_probe_fail=true` can mark the asset complete and return without invoking its writer.

   **Scenario:** an inactive row matches every dispatch-validated field, has zero receipts, but retains a passing integrity check and that rebuild policy. Dispatch succeeds; execution takes the green-probe shortcut. I reproduced the admission and runner routing in memory with no writer call.

   Migration 1243 ordinarily leaves the policy at its default false; I did **not** establish that production has the problematic values. Nevertheless, the dispatcher accepts them.

   **Fix:** validate the intended data-writer routing and `rebuild_on_probe_fail=false`. The force flag for delta execution would not bypass this earlier shortcut.

3. **P2 — An interrupted replacement can make both dispatch and teardown refuse recovery. Blocks production: YES for the currently permitted replacement path.**

   [dispatch_v5_small_test_job.py:347](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-disp2/platform/scripts/dispatch_v5_small_test_job.py:347) accepts an existing proven test candidate without receipts. The writer updates its manifest at `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:803–807`, before replacing its snapshot/output at lines 818–842. `asset_runner.py:914–915` commits each substep separately.

   **Scenario:** a failed earlier test left valid partial output but no final receipt. A newly admitted slice commits a different manifest, then crashes before replacing the snapshot. `v5_small_test_shared.py:229–233` now rejects the mismatch. Dispatch says “tear down first”; `teardown_v5_small_test_job.py:359–361` uses the same refusal and says “re-dispatch”.

   **Fix:** the simplest bounded solution is to require teardown whenever any prior candidate/output exists, including failed attempts. Otherwise, supply a separately reviewed recovery path. The proposed teardown-between-every-run sequence avoids this case, but the script does not enforce it.

4. **P3 — The printed cutoff is later than the watchdog’s actual cutoff. Blocks production: NO if execution follows immediately.**

   [dispatch_v5_small_test_job.py:462](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-disp2/platform/scripts/dispatch_v5_small_test_job.py:462) calculates the deadline from the client clock after COMMIT. The watchdog uses database `created_at` (`platform/src/app/api/cockpit/watchdog/route.ts:433–435`), whose default is transaction-time `NOW()` (`171_build_runs.sql:38`).

   **Scenario:** staging takes several minutes, or client and database clocks differ; the run becomes eligible for failure before the displayed cutoff.

   **Fix:** return the stored `created_at` and derive both deadlines from that timestamp.

**A — Round-1 disposition**

| Finding | Status | Evidence |
|---|---|---|
| 1. Published/sealed refusal | **Resolved** | `dispatch:333–334`; shared published/sealed/serving checks at `v5_small_test_shared.py:82–112`, under the chart lock. |
| 2. Eligibility and candidate ownership | **Resolved for admission** | `dispatch:335–350`; shared N-137 checks at `:249–283` and ownership proof at `:186–246`. Replacement recovery remains finding 3 above. |
| 3. Activation invalidates other charts | **Resolved** | No registry UPDATE; inactive candidate SELECT at `dispatch:293–317`. |
| 4. Unlocked registry validation | **Resolved** | `SELECT … FOR SHARE` at `dispatch:159–161`, retained through transaction completion. |
| 5. Requested slice can be skipped | **Partly resolved** | Clean-receipt refusal at `dispatch:339–345` closes delta-skip; finding 2 identifies another shortcut. |
| 6. Commit reporting and recovery | **Partly resolved** | Confirmed COMMIT survives ordinary reporting failures at `dispatch:477–480`; recovery lookup remains broken. |
| 7. CI interpreter/dependency order | **Resolved in this stack** | `.github/workflows/ci.yml:850–859` selects Python before installing writer requirements; dispatch tests run at `:1007–1010`. |

Here, `dispatch` denotes `platform/scripts/dispatch_v5_small_test_job.py`.

**B — Inactive execution is allowed.** The decisive trace is:

- `runner.py:206–213` loads the persisted run; `:234–323` validates its frozen manifest without checking activity.
- Writer-gap preflight checks `has_writer`, not activity (`:175–201`). Registry comparison likewise does not filter the planned asset by activity (`:343–385`).
- The scheduler uses `frozen.plan` (`:1201–1203`) and invokes `run_asset` (`:901–907`). Its active-registry query at `:867–876` serves downstream staleness propagation, not plan filtering.
- `asset_runner.py:1591–1593` loads metadata by asset ID; the ordinary data path calls `_run_data_writer` at `:1661–1664`, which calls `_drive_substeps` at `:1179–1182`, then `writer.run_substep` at `:895`.

Thus **`is_active=false` itself neither blocks nor skips v5**. Dependency readiness, code/image compatibility, and the probe shortcut remain separate conditions.

**C — Zero receipts closes delta-skip, but not every skip.** `provenance.py:167–178` reads the exact asset/chart/partition receipt; `:423–425` returns false when none exists. I also exercised that predicate with an empty cursor result: false.

The already-`lit` scheduler shortcut applies only when action is **not** `rebuild` (`runner.py:858–865`). No completed substep keys are supplied (`asset_runner.py:1179–1182`, `:867–875`). No-op completion is evaluated **after** writer execution (`:1210–1258`). The asset’s own freshness does not independently skip it; missing/stale prerequisite freshness blocks execution (`:78–114`, `:1465–1529`). Finding 2 remains the other pre-writer shortcut.

**D — `FOR SHARE` is sufficient for the registry row, but does require UPDATE privilege.** It conflicts with concurrent UPDATE/DELETE and remains held until COMMIT/ROLLBACK. PostgreSQL requires SELECT plus UPDATE privilege on at least one column. The source acknowledges this at `dispatch:156–157`; migration `1070_data_plane_builder_orchestrator_grants.sql:63–65` grants the builder UPDATE on health columns. The intended application **owner** role has the necessary privilege through ownership. No registry UPDATE statement or activation trigger is executed. Live ownership/grants were not verified.

**E — No lock-order inversion found in the named paths.** Dispatch takes Gochara chart lock → registry share lock → staging writes. Teardown takes orchestrator exclusion → Gochara chart lock (`teardown:193–210`); the runner holds orchestrator exclusion while its worker takes Gochara locks. Dispatch never subsequently requests orchestrator exclusion, so it does not reverse that ordering. The active-run unique index supplies the staging concurrency boundary. Database admission refusals occur within the staging transaction; flag/marker refusals occur before connecting.

This is a source-level assessment, **not proof of deadlock freedom under arbitrary concurrent transactions**. Lock waits are bounded by the configured timeout.

**F — Watchdog and crash outcomes are conditionally recoverable.**

- An undispatched run becomes `failed`, with queued assets `aborted` (`watchdog/route.ts:429–446`). Its old ID cannot be claimed (`runner.py:428–439`). Once terminal, teardown can remove this empty test run; a fresh dispatch can then be staged.
- Caught worker failures normally become terminal; committed earlier substeps remain. A hard crash can leave the run `running` until retry or watchdog recovery. Teardown refuses active runs (`teardown:265–270`).
- A failed run started from a clean generation normally leaves attributable candidate state that teardown can remove. **Do not generalize that guarantee to replacement attempts:** finding 3 is the counterexample.

**G — A production dry run is necessary, but insufficient to clear this review.** Fix findings 1–3 before production use. The missing real-database coverage remains a blocker here: the fake currently passes a recovery scenario that migration 595 rejects. A clean initial production dry run cannot exercise that conflict, interrupted replacement, or concurrent lock behavior.

Add focused PostgreSQL tests against the actual migrations for staging/rollback, active-run collision and lookup, refusals, and intended-role privileges. Steward ruling 9 remains unmet. Ruling 10 also remains unmet here: `test_dispatch_v5_small_test.py:141–143` silently bypasses the migration-1304 comparison when the file is absent; it reports a passing test rather than an explicit skip.

**Not verified:** live schema/data, applied migration 1304, actual grants/RLS/triggers, PostgreSQL concurrency or crash behavior, COMMIT fault behavior, deployed worker image/environment, ephemeris availability, real writer completion, or CI execution. The separately reviewed shared module was inspected for this integration, not independently requalified in full.