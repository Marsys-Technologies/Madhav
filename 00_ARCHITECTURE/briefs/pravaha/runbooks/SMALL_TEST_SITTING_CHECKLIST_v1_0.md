---
artifact: SMALL_TEST_SITTING_CHECKLIST
version: "1.4"
status: "DRAFT — authorises NOTHING. Written for the steward (steward SMALLTEST-CHECKLIST, 2026-10-05). Commands are as of the heads named in section 'Heads this was written against'; re-read the scripts at the FINAL merged heads before the sitting (Stream A's fixes may rename flags)."
date: 2026-10-05
author: Stream B (Śāstra), session madhav-8b
owner_ruling: "ST-OWNER-SMALL-TEST-1 (Ruling 3, 2026-10-03): a very small test rebuild of Gochara 5 first; the one full build waits for Suvarna's elevation."
how_to_use: "Do the rows in order. Any FALSE readback = STOP, report, no unreviewed repair. Nothing here is a go: every row that touches production for a Gochara build, dry run or measurement on chart 482012f1 needs the steward's explicit word first (the standing hold is in force until the steward lifts it). Read-only readbacks on production are rows 3 and 9/11 readbacks; they are not builds."
changelog:
  - "1.4 (2026-10-05, Stream B): corpus probe note — after PR 3142 conftest defines SE1_CHECKSUMS by import, so PR 3102's probe (AST literal parse) must read PINNED_SE1_SHA256 from services/gochara_kernel/ephemeris_pins.py; graze interim and G11 recorded (row 7); the real-chart counts."
  - "1.3 (2026-10-05, steward P1-EMPTY-CLASS, Stream B ruling): prerequisite 0.1 gains the P1 exclusion fix — the eight H-unknown classes (ST-H-UNKNOWN-20261002) make the in-build P1 anchor check fail at the FIRST class of an all-classes run (achievement_recognition sorts first); run 1 cannot complete until the verifier verifies the exclusion; run 2 (marriage) is unaffected; the open-questions list names it."
  - "1.2 (2026-10-05, Stream B, found reviewing PR 3142 / ephemeris fix): the sitting ALSO writes GLOBAL rows the teardown keeps (rule registry and seals, sky convention and bridge, physical objects, sky events for the 8 bodies 1998-2085; all 0 in production today, read R2b); owner told in row 1.4; the 7200 s asset timeout must cover that first-ever substrate build; R9/9.4/11.1 expect those rows to remain."
  - "1.1 (2026-10-05, steward CHECKLIST-ADD): HARD RULE in row 7 — the runner process exits 0 even when the run ends FAILED, so the Cloud Run execution status proves nothing and success or failure is read ONLY from build_runs, build_run_assets, asset_throughput and the manifest (query R7c); a P1 anchor failure on production stops the sitting (row 7 table); the unset-ephemeris failure is named and takes under a second."
  - "1.0 (2026-10-05): first version, from everything found on 2026-10-04/05 (G8, teardown 3098, dispatch 3097, ephemeris gap, production catalog reads)."
---

# Small test sitting — ordered steward checklist (DRAFT, authorises nothing)

## What this sitting is

Two small, unsealed, removable builds of `ka_gochara_v5` for the canonical chart `482012f1-710e-4a25-994a-93821f5871aa`, generation `5.0`, each torn down afterwards:

| Run | Dispatch flags | What it exercises |
|---|---|---|
| **Run 1** | `--run all_classes_1y --classes all --horizon-start 2025-04-17T00:00:00+00:00 --horizon-end 2026-04-17T00:00:00+00:00` | all 26 scored classes over one year (365 days, inside DEFAULT_HORIZON 1998-01-01 to 2026-04-17; the dispatch caps at 366 days) |
| **Run 2** | `--run one_class_full --classes marriage` (no horizon flags) | one class over the full DEFAULT_HORIZON (10,334 days) |

**The order is fixed: run 1, teardown, run 2, teardown.** The dispatch refuses while any provenance receipt of the asset exists for the chart (the orchestrator's delta-skip compares a receipt with the chart and birth configuration, not the slice marker, so a left-over receipt could make the next run skip the writer and re-attribute the old output).

A test slice is **unsealable by construction** (`stored_scope = test_slice`, a stamp the verifier vocabulary does not know) and is refused by the verification job, the seal flow, publication (`ledger.publish`) and the MCP contact-ledger reader. `all_classes_1y` claims all 26 classes and so passes the G8 class census (if G8, PR 3141, has landed by then; it is NOT to be merged before this test) but stays unsealable for its own reason; `one_class_full` claims one class and fails both.

## Roles and credentials at a glance

| Step | Credential | Role | Note |
|---|---|---|---|
| Readbacks (rows 2, 3, 9, 11) | the steward's READ-ONLY production connection (`default_transaction_read_only = on`) | any read-only login | no write-capable credential |
| Dispatch dry run / execute (rows 5, 6, 10) | `DATABASE_URL` in the process environment only (never an argument, never printed, never read from a file) | **`data_plane_builder`** | verified by Stream B on the production catalog: holds every privilege the staging transaction needs (SELECT on registry, receipts, freshness, seal, authority, publication, snapshot, inventory tables; INSERT/UPDATE on `asset_throughput`, `build_runs`, `build_run_assets`; EXECUTE on `ka_gochara_lock_chart`; UPDATE on a probe column of `asset_registry`, which `SELECT ... FOR SHARE` needs). No UPDATE of `is_active`, no DELETE anywhere. |
| Cloud Run execution (rows 6, 10) | the steward under the owner's account | project `madhav-astrology`, region `asia-south1`; job runs as service account `data-plane-builder-runtime` | the BUILD itself runs as `data_plane_builder` (migration 1070: the dedicated identity of `brahma-build-pipeline-job`, deliberately no DELETE) |
| Teardown dry run / execute (rows 4, 9, 11) | `DATABASE_URL` in the process environment only; **DIRECT connection to the database host and port, never a pooler** | **OWNER DECISION, not yet made** (row 1) | the teardown must DELETE; `data_plane_builder` cannot. Even the DRY RUN performs the DELETEs inside a transaction it rolls back, so it needs the same privileges |

Rows needing a **write-capable credential**: 5 (dry run runs the staging INSERTs and rolls back), 6, 10 (dispatch), 6/10 (Cloud Run execute), 4, 9, 11 (teardown, dry run included). Rows 0-3 and the readbacks need none.

## Heads this was written against

PR 3098 teardown `2240aa4c0`, PR 3097 dispatch `508561b7e` (stacked on 3098), main `5d9e71279` (PR 3110, the writer's test slice), job image `brahma-pipeline:5d9e712799336958e5a82bce74b57859a2944f44`. Codex rounds on 3098/3097 and the ephemeris fix (EPHE ruling) were still open; flags, a `--lookup` mode and the ephemeris fallback may change. PR 3141 (G8) is held and must not merge before this test.

---

## The checklist

Columns: **#**, **Step**, **Who**, **Cred** (needs a write-capable credential), **Action / exact command or readback**, **Expected**, **STOP if (and who is told)**.

### Row 0 — prerequisites merged on main and DEPLOYED

| # | Step | Who | Cred | Action / readback | Expected | STOP if / told |
|---|---|---|---|---|---|---|
| 0.1 | Prerequisite PRs merged on `main` | steward | none | `gh pr view <n> --json state,mergeCommit` for: the **ephemeris fallback fix** (Stream A; without it no run can complete, small or full: the real runner gives the writer only `chart_id` and `birth_params`, the v5 writer needs `ephe_path`, and the run fails at the manifest substep AFTER the 8 body substeps), **PR 3098** (teardown), **PR 3097** (dispatch), **PR 3101** (migration 1304, the registry row's small-test shape) | all four MERGED. **and the P1 exclusion fix** (steward P1-EMPTY-CLASS ruling: for the eight classes whose signature houses are unknown, ST-H-UNKNOWN-20261002 excludes P1/P3/P4; the in-build anchor check must verify that exclusion, i.e. zero P1 records, instead of demanding transit contacts; without it run 1 dies at its first class, achievement_recognition; run 2 with marriage does not need it). PR 3141 (G8) and PR 3140 (DB-level slice publication refusal, later window) are NOT yet merged | any not merged: stop; tell the steward |
| 0.2 | CI and deploy of the final `main` finished | steward | none | `gh run list --branch main --limit 5`; the deploy run for the final SHA finished green | final `main` SHA = S | red or running: stop |
| 0.3 | The job image is built from the SAME commit as the checkout the dispatch will run from | steward | none | `gcloud run jobs describe brahma-build-pipeline-job --region=asia-south1 --project=madhav-astrology --format='value(template.template.containers[0].image)'` and `git rev-parse HEAD` in the checkout; then print the writer digest the dispatch will freeze: `python3 -c "import json;print(json.load(open('platform/src/generated/nirmana-writer-digests.json'))['writers']['ka_gochara_v5'])"` | image tag ends in S; checkout HEAD = S; digest printed and RECORDED (evidence folder) | tag differs from S: `execute_run` refuses a run whose job image writer digest differs from the manifest's ('sidecar code digest does not match', run terminalised failed). Re-deploy or re-checkout; a later writer change (the ephemeris fix, PR 3141) means re-dispatch from the matching checkout |
| 0.4 | Job definition carries no override that changes behaviour | steward | none | `gcloud run jobs describe brahma-build-pipeline-job ... --format=json` and read the env NAMES only (never values): expect DATABASE_URL, GCP_PROJECT, KA_KSHETRA_HASH_SPILL_DIR, MARSYS_REPO_ROOT, ORCHESTRATOR_WORKER_LIMIT, PUBSUB_TOPIC, WRITER_TIMEOUT_SECONDS | no NIRMANA_FORCE_EXECUTE, no ORCHESTRATOR_WRITER_GAP_CHECK=off, no ephemeris variable (the image's own ENV SE_EPHE_PATH=/app/ephe applies, per Dockerfile.pipeline). Task timeout 86400 s, 16Gi, 4 cpu | an override present: stop, report |

### Row 1 — owner items

| # | Step | Who | Cred | Action | Expected | STOP if / told |
|---|---|---|---|---|---|---|
| 1.1 | **Teardown role decision** | **owner** | none | Present the table in section "Teardown role: the question for the owner" below | owner names ONE role and says how the teardown's DATABASE_URL is provided; steward records it | no decision: do not dispatch run 1 (a small test that cannot be torn down is stuck for 90 days, then unrecoverable by script) |
| 1.2 | **Notice to Suvarna before the FIRST governed `5.0` manifest** | steward tells; Stream B runs W1/W2 | none (read-only) | Re-run W1 and W2 (ROLES_AND_SEAL_PROVISIONING_RUNBOOK §4.1) on production, then tell Suvarna in words: from that manifest onward every publication UPDATE/DELETE statement of ANY chart's legacy Gochara build (`ledger.py`, the `ka_gochara_v4_41_candidate` writer, the cutover scripts) takes the CANONICAL chart's lock; it waits while a governed transaction of the canonical chart holds it and is refused at REPEATABLE READ; a governed manifest of another chart would block all of them (POST_SETTLED1_SEQUENCE row 8a, observed in C55) | W1 returns zero rows; W2(c) shows no role or database isolation setting; Suvarna has acknowledged | W1 returns a row, W2(c) shows an isolation setting, or Suvarna has not been told: stop |
| 1.3 | Window courtesy | steward | none | Confirm Suvarna's S-L1/W1 windows are not open and the standing hold on builds for chart 482012f1 is lifted by the steward for this test only | steward's explicit word recorded | hold not lifted: nothing below runs |
| 1.4 | Owner informed that the sitting starts | steward | none | one line to the owner: what will be written, to which chart, and the 90-day teardown clock; **and that the test also writes GLOBAL rows that stay after the teardown** (rule registry and seals, sky convention and bridge, physical objects, sky events for 8 bodies 1998-2085: all empty today, read R2b); they are idempotent and the full build reuses them, but they are not removable by the teardown | recorded | the owner does not want global rows written by a test: stop |

### Row 2 — migration 1304 applied and read back

| # | Step | Who | Cred | Action / readback | Expected | STOP if / told |
|---|---|---|---|---|---|---|
| 2.1 | 1304 applied by the repository's mechanism (never edited after apply; verify, do not trust the deploy log) | steward | per the migration's own mechanism | read the `_migrations_applied` row: `SELECT filename, applied_at FROM public._migrations_applied WHERE filename LIKE '1304_%';` | one row | no row: stop |
| 2.2 | Registry row in the 1304 shape | steward | none | **R1** (below) | exactly the values in R1's expected block. **As of 2026-10-05 production's row is NOT in this shape** (has_substeps false, depends_on empty, target_table kala_gochara_windows, timeout 600): the dispatch refuses by design until 1304 is applied | any field differs: stop (apply 1304; never edit the row by hand) |

### Row 3 — read-only readbacks before anything else

| # | Step | Who | Cred | Action / readback | Expected | STOP if / told |
|---|---|---|---|---|---|---|
| 3.1 | Clean state | steward | none | **R2** and **R2b** (record both) | every count 0 (receipts, freshness, throughput, substep progress, runs naming the asset, every `5.0` output table, manifest, seal, authority naming 5.0, legacy windows/contacts rows of 5.0). Production on 2026-10-05: all 0 | any non-zero: stop; a prior candidate means the dispatch refuses (it refuses ANY prior 5.0 candidate/output/snapshot/inventory/manifest, test or not: always tear down first) |
| 3.2 | Dependencies lit and fresh | steward | none | **R3** | `ga_positions` and `ga_dashas`: state `lit`, freshness `fresh`, for the canonical chart (2026-10-05: both lit/fresh). The build only runs when its declared deps are lit | not lit or not fresh: stop; the writer would be blocked ('BLOCKED: upstream dependency did not complete') |
| 3.3 | Incoming foreign keys | steward | none | **R4** | the nine single-column keys listed in R4 (no composite, none deferrable). The teardown refuses by name any incoming FK shape it does not support and any table that references an owned run or the manifest | a new or composite key appears: report to Stream A before the teardown is relied on |
| 3.4 | Image corpus probe (PR 3102) | steward (needs docker + gcloud read access on the steward's machine) | none on the database | see "Corpus probe" below | `RESULT: all three .se1 digests match the conftest pins` and `SE_EPHE_PATH=/app/ephe` | mismatch or missing file: stop, report; re-run after any change to the image |
| 3.5 | Role privilege check | steward | none | **R5** for the teardown role chosen in row 1.1, and for `data_plane_builder` (dispatch) | R5 prints no missing privilege | a missing privilege: the dry run would fail where an execution would; fix by the owner's decision, not by repair |

### Row 4 — teardown dry run on the EMPTY state

| # | Step | Who | Cred | Action | Expected | STOP if / told |
|---|---|---|---|---|---|---|
| 4.1 | Dry run, nothing to remove | steward | teardown role | from `platform/`: `DATABASE_URL=… python3 scripts/teardown_v5_small_test_job.py` (dry run is the default; it runs the SAME statements as an execution and rolls back; zero commits). **Direct connection to the database host and port, never a pooler** (the orchestrator exclusion lock is a SESSION advisory lock; the script reads `pg_backend_pid()` in three transactions and refuses if it changes) | exit 0; counts all 0; "ROLLED BACK"; no retention lines (no runs); the end-state (N-137) validation passes | any refusal: read it; each is named. A privilege error means row 3.5 was not true. Tell the steward |

### Row 5 — dispatch dry run, run 1

| # | Step | Who | Cred | Action | Expected | STOP if / told |
|---|---|---|---|---|---|---|
| 5.1 | Dry run (the default; the SAME staging transaction runs and ROLLS BACK) | steward | `data_plane_builder` | from `platform/`: `DATABASE_URL=… python3 scripts/dispatch_v5_small_test_job.py --i-am-steward --after-settled-1 --run all_classes_1y --classes all --horizon-start 2025-04-17T00:00:00+00:00 --horizon-end 2026-04-17T00:00:00+00:00` | prints the staged plan as JSON: `plan_manifest` (with `gochara_v5_test_slice`: classes in scored order, `+00:00` timestamps, digest), `plan_manifest_digest`, `existing_small_test_runs: none`, admission notes. **Record `plan_manifest_digest` and the marker digest** (evidence folder). Rolled back: nothing written | a named refusal (frozen generation, registry shape, N-137 conditions, receipts exist, existing candidate, active run): fix the cause first. Marker refusals come from the WRITER's own validator |
| 5.2 | Re-read the dry-run counts | steward | none | **R2** again | still all 0 (a dry run leaves no run row, no throughput row, no freshness change) | any non-zero: stop, report |

### Row 6 — dispatch execute, then the Cloud Run command WITHIN 10 MINUTES

| # | Step | Who | Cred | Action | Expected | STOP if / told |
|---|---|---|---|---|---|---|
| 6.1 | Steward's explicit go; owner informed | steward | — | the owner's ruling covers a small test; tell the owner the moment the run is staged | recorded | — |
| 6.2 | Stage the run | steward | `data_plane_builder` | the same command as 5.1 plus `--execute` | prints the run id, the **EXECUTE WITHIN 10 MINUTES** cut-off, the **TEARDOWN DEADLINE** (90 days out) and the Cloud Run command. **The cut-off and deadline printed at head `508561b7e` come from the CLIENT clock; derive them from the stored `build_runs.created_at` instead** (R6) until Stream A's D4 fix lands | an error after COMMIT: the script says COMMIT CONFIRMED / UNKNOWN; never retry blindly; look the run up (R6) |
| 6.3 | Execute the job | steward | the owner's account (Cloud Run) | `gcloud run jobs execute brahma-build-pipeline-job --region=asia-south1 --project=madhav-astrology --args=--run-id,<run_id>` **within 10 minutes of `created_at`**: the cockpit watchdog fails a planned run that never started after 10 minutes (`watchdog/route.ts`); the failed run has no output and no receipts, so the teardown can remove it, but you must re-stage | execution starts; run state goes planned → running | past 10 minutes: re-stage (a failed run blocks nothing but the one-active-run index while it is still planned or running) |

### Row 7 — watching the run

What to read (all read-only; times in UTC):

| Read | Command / query | Meaning |
|---|---|---|
| Run and asset state, and THE VERDICT | **R7a** and **R7c** (the verdict; never the Cloud Run status) | `build_runs.state`, `current_asset_id`, `last_error`; `build_run_assets.state`, `started_at`, `ended_at` |
| Progress | **R7b** | `build_substep_progress` rows for the asset accumulate as substeps commit; the substep keys are the phases (below). The full-class plan is 298 static substeps |
| Cloud Run execution and logs | `gcloud run jobs executions list --job=brahma-build-pipeline-job --region=asia-south1 --project=madhav-astrology --limit=3`; logs in Cloud Logging for the job; the writer's per-substep notes and the in-build verification lines are in the log | exit code and per-substep text |

**HARD RULE (steward CHECKLIST-ADD; Stream A found it with the real runner entry point; the orchestrator is frozen and is not changed): the runner process EXITS 0 even when the run ends FAILED.** The Cloud Run execution status (`Succeeded`, exit code 0) therefore proves NOTHING. Success or failure is read ONLY from the database, with **R7c** below, and the result is recorded verbatim in the evidence folder before anything else is done. **A run is a SUCCESS only if ALL of these hold:** `build_runs.state = 'completed'`; the asset's `build_run_assets.state = 'complete'` **and** `disposition = 'build'` (`skip_no_delta` means the writer did NOT run; `blocked_dependency` means a dependency did not complete); `asset_throughput.state = 'lit'` (`incomplete` = the plan completeness could not be proven, `dormant` = nothing written, `error`/`building` = not finished); the manifest is `candidate` with `stored_scope = test_slice`; and the inventory and output counts match the slice (all classes for run 1, one class for run 2). Anything else is a FAILED run whatever Cloud Run says: stop, keep the evidence, tell the steward.

**R7c — THE VERDICT (read-only; read this, never the Cloud Run status):**
```sql
SELECT r.state AS run_state, left(coalesce(r.last_error,''), 400) AS run_error,
       a.state AS asset_state, a.disposition, left(coalesce(a.error,''), 400) AS asset_error,
       (SELECT t.state FROM asset_throughput t WHERE t.asset_id = 'ka_gochara_v5' AND t.chart_id = r.chart_id) AS throughput_state,
       (SELECT p.status FROM kala_gochara_publication p WHERE p.chart_id = r.chart_id AND p.generation = '5.0') AS manifest_status,
       (SELECT p.input_generation_vector ->> 'stored_scope' FROM kala_gochara_publication p WHERE p.chart_id = r.chart_id AND p.generation = '5.0') AS stored_scope,
       (SELECT count(*) FROM ka_gochara_search_inventory i WHERE i.chart_id = r.chart_id AND i.generation = '5.0') AS inventories,
       (SELECT count(*) FROM ka_gochara_search_inventory i WHERE i.chart_id = r.chart_id AND i.generation = '5.0' AND i.finalized_at IS NOT NULL) AS finalised_inventories,
       (SELECT count(*) FROM build_substep_progress s WHERE s.chart_id = r.chart_id AND s.asset_id = 'ka_gochara_v5') AS substeps_done
  FROM build_runs r LEFT JOIN build_run_assets a ON a.run_id = r.id AND a.asset_id = 'ka_gochara_v5' WHERE r.id = '<run id>';
```
Expected for a success: `completed | | complete | build | | lit | candidate | test_slice | 26 | 26 | <substeps>` for run 1 (`1 | 1` inventories for run 2). Run states seen in production: planned, running, paused, completed, failed, stopped; build_run_assets states: queued, building, complete, error, aborted; dispositions: build, skip_no_delta, blocked_dependency.

**Known fast failures and the first completion.** With no ephemeris path configured (the variable unset) the run now fails in under a second, by name, at the first substep (the fallback fix refuses at `rules`, not after the 8 body substeps): that is the environment fault, read in R7c as `failed` with the asset error naming the ephemeris path; nothing was written. **The first slice that ever completes through the real runner is the production small test itself** (the stubbed L1 used in tests cannot pass the P1 grain), so a failure in the P1 grain is the most likely first real finding and must be read as such (table below).

Phases and what a failure in each means (writer plan order: `rules` → `convention` → `body:<Body>` ×8 → `manifest` → `snapshot` → per class `inventory:<c>`, `coverage:<c>`, records, `verify:<c>`):

| Phase | If it fails | Meaning |
|---|---|---|
| exit before any substep (the process may still report exit 0: read R7c) | frozen-manifest validation or the writer-gap check or the sidecar code digest | image/checkout skew (row 0.3), tampered manifest, or registry row missing `has_writer`. Run is terminalised `failed`. No output written |
| exit 3 | chart locked / too many runs | another run holds the chart lock; the run stays planned; if it is not started within 10 minutes the watchdog fails it |
| `rules`, `convention` | rule registry / convention row | global-key work; no chart output yet |
| `body:*` | sky substrate (boundary events and stations); **built from EMPTY in production: the global tables are all 0 today, so run 1 solves 87 years for 8 bodies inside the 7200 s budget (unknown cost; the largest single completion risk).** If the asset times out the substeps already committed stay (idempotent insert-if-absent), so after the teardown a re-dispatch resumes the body phase cheaply | the Swiss library uses `SE_EPHE_PATH` from the image environment when no path is configured; a Moshier-fallback refusal (retflag) means the corpus is not being read |
| `manifest` | `InputDrift` | **ephemeris: no ephe_path configured** (the known gap, until the fix is deployed); a registry/rule/L0/ephemeris identity that the writer derives two ways and that disagree; a marker the writer refuses. **Nothing past this has run** |
| `snapshot` | replaces the WHOLE chart x generation chain (candidate-only) | a failure here leaves the manifest stamped and possibly the previous chain; teardown refuses an "interrupted replacement" (stamped manifest, snapshot of another vector) by name: re-dispatch the slice, then tear down |
| `inventory`/`coverage`/records | per class | a partial chain: manifest + snapshot + some inventories. The teardown can remove it (every inventory header must carry the snapshot's input digest, the manifest horizon and a stamped class) |
| `verify:<class>` | in-build self-checks | in-build verification disagreeing with the build; record which class and path |
| `verify:<class>` under the test slice **(graze interim, PR 3143, if merged)** | the in-build certification REPORTS in-band intervals with no exact crossing (grazes) in the substep notes and the job log (line text `GRAZES REPORTED, NOT RAISED (validated test slice; N)`: planet, relation, point, level, interval, closest approach, peak activity) instead of failing | a graze is not a failure of the slice; **count them for the report** (research G11; the real chart is expected to have about 24 over 1998-2026 for the P3/P4 point obligations, computed read-only). Without PR 3143, or in any full build, the first graze FAILS `verify:<class>` by name ('expected contact ... is not in the ledger') |
| **a P1 anchor failure** (any record or verification failure on grain `P1`, in the records phase or in `verify:<class>`; the asset error names path P1 / an anchor) | **STOPS THE SITTING** | P1 is the grain of anchor records (the natal-placement and daśā-anchor readings the writer derives from L1 facts). This is the first time the writer meets the real production L1 inputs through the real runner, so a P1 failure is a **writer-versus-L1 finding, not an environment fault**: either the writer's P1 derivation or its in-build check disagrees with what production's L1 holds. Do not retry and do not run 2. Keep the logs and R7c/R8 outputs, tear the partial chain down (row 9 dry run first), and report to Stream A and the owner: the full build would fail the same way |
| asset timeout | **7200 s** (`writer_timeout_seconds`, 1304) | the asset is marked timed out as the root cause; downstream (none) blocked. Cloud Run task timeout is 86400 s, memory 16Gi |
| the watchdog | marks a `has_substeps` asset whose plan completeness cannot be proven as **incomplete**, not lit | `incomplete` is not a pass |

**Whole-build replay on retry.** The orchestrator passes no `completed_keys`: every dispatch re-runs from substep 1, and a failed build restarts from zero (the `snapshot` substep replaces the whole candidate chain). A failed run cannot be re-executed (`execute_run` claims only a `planned` row). **A retry is: teardown (removes the partial chain, runs, receipts), then re-dispatch.**

### Row 8 — measurements to record, and where

Record under `/Users/Dev/pravaha/run/smalltest-<date>/` (raw outputs, one file per query, with the run id and the time read) and summarise in `00_ARCHITECTURE/briefs/pravaha/measurement/SMALL_TEST_RESULTS_v1_0.md` (steward names the final file). Stream B writes the summary from the raw files.

| What | Source | Why |
|---|---|---|
| Wall time per run, per asset, and per phase (rules, convention, each body, manifest, snapshot, each class) | **R7a** and **R8a** (`completed_at` gaps) plus the Cloud Run execution times | capacity: how long the full build will take; compare with the 7200 s asset timeout (the full build, 26 classes x 10,334 days, may exceed it: that is a finding, not a failure of the test) |
| Per-class time and row counts (windows, records, contacts, coverage, inventory, obligations, intervals) | **R8b** counts per table and per class; per-class gaps from R8a | cost per class; scale to the full horizon (run 2 gives the full-horizon cost of one class, run 1 the all-class cost of one year) |
| Peak memory and CPU | Cloud Run execution metrics | the job is 16Gi / 4 cpu |
| **Grazes** (research G11) | the Cloud Run job log lines `GRAZES REPORTED, NOT RAISED`, per class | the count and the list the owner needs for the near-miss decision |
| **In-build verification results** (the `verify:<class>` substeps) | the Cloud Run log lines of those substeps; rows in `ka_gochara_search_inventory_verification` and `ka_gochara_eval_window_verification` if the in-build checks wrote any (R8c counts by status) | whether the build agrees with its own independent derivation |
| **Certification cost** (contact certification time as a share of the run) | the log durations of the substeps that certify contacts; if not separable, the difference between the contact-writing and coverage substeps in R8a | the cost the full build will pay for certification (open question 8) |
| Counts of what a test leaves behind and what the teardown removes | **R2** before dispatch, after the build, after the teardown | proves the teardown is complete |
| The dry-run teardown listing (counts, retention lines, stamp proof source) | the teardown dry run output, saved verbatim | evidence |

### Row 9 — teardown after run 1

| # | Step | Who | Cred | Action | Expected | STOP if / told |
|---|---|---|---|---|---|---|
| 9.1 | Read what exists and the verdict | steward | none | **R2**, **R7a**, **R7c** (record the verdict BEFORE tearing down: the teardown deletes the evidence) | the run is terminal (completed/failed/stopped), no planned/running/paused run on the chart | a run still active: stop it first (the teardown refuses active runs) |
| 9.2 | Teardown dry run | steward | teardown role | `DATABASE_URL=… python3 scripts/teardown_v5_small_test_job.py` (direct connection) | lists would-delete counts (receipts, freshness, run assets, runs, throughput, the output chain, inventory, snapshot, manifest), **each owned run's creation time and the days of the 90-day retention remaining**, how the stamp was proved (ORIGINAL marker of run X, or RECONSTRUCTION when no run row survives); end state N-137 validated; ROLLED BACK | any refusal: it is named. **A receipt with NO run link is refused for good**: it means the run was pruned (the cockpit watchdog deletes terminal runs after 90 days, `asset_provenance_receipts.build_id` is ON DELETE SET NULL). That is why this row runs well inside the window; the recovery in the teardown runbook section 3 is NOT FOR USE and not needed for a timely teardown |
| 9.3 | Teardown execute | steward | teardown role | the same command plus `--execute --i-am-steward` | "COMMITTED"; exit 0. If it says COMMIT OUTCOME UNKNOWN: do not run again; run the dry run and read the counts | an error: the script states rollback confirmed / not confirmed / commit unknown; act on that sentence |
| 9.4 | End-state readback | steward | none | **R1** (registry row inert, 1304 shape), **R2** (everything 0), **R2b** (the global rows REMAIN: expected, recorded), **R3** (deps still lit/fresh), **R9** (leftovers the teardown does not delete) | row `is_active = false`; all zero; deps unchanged | anything left: report before run 2 |
| 9.5 | Monitor reading | steward | none | read the Nirmana monitor/cockpit for the asset (open question 4: Stream A names the screen); rule N-137 excludes an unsealed test candidate only while: catalog_status is not RETIRED, nothing depends on the asset, and no receipt or run-asset row of the asset on ANY chart comes from a non-test run (a NULL run link counts as non-test) | the asset reads as an excluded unsealed test candidate, then, after the teardown, as the inert registered asset it was | the monitor reports the asset as a defect: report, do not act |

### Row 10 — run 2 (one class, marriage, full horizon): rows 5 to 9 again

| # | Step | Who | Cred | Action | Expected | STOP if / told |
|---|---|---|---|---|---|---|
| 10.1 | Prerequisite | steward | none | row 9 completed: **R2 all zero** (the clean-receipt prerequisite) | all 0 | any receipt: the dispatch refuses |
| 10.2 | Dispatch dry run, execute, Cloud Run within 10 minutes | steward | as rows 5-6 | `python3 scripts/dispatch_v5_small_test_job.py --i-am-steward --after-settled-1 --run one_class_full --classes marriage` (dry run; add `--execute` to stage), then the same `gcloud run jobs execute ... --args=--run-id,<run_id>` | the manifest carries a one-class stamp over the full DEFAULT_HORIZON; if the image or checkout changed since run 1 (for example a writer fix), repeat row 0.3 first | as rows 5-6 |
| 10.3 | Watch and measure | steward / Stream B | none | rows 7 and 8 | one class over 10,334 days: record time and counts | as row 7 |
| 10.4 | Teardown (dry run, execute, end state) | steward | teardown role | rows 9.1 to 9.5 | as row 9 | as row 9 |

### Row 11 — final teardown confirmation and the report to the owner

| # | Step | Who | Cred | Action | Expected | STOP if / told |
|---|---|---|---|---|---|---|
| 11.1 | Final state | steward | none | **R1**, **R2**, **R2b** (global rows remain, unchanged by run 2), **R3**, **R4**, **R9** once more | registry row inert in the 1304 shape; all zero; dependencies lit/fresh; FKs unchanged | anything left: report, do not repair |
| 11.2 | Dry run on the final state | steward | teardown role | the teardown dry run | "nothing to remove"; end state valid | — |
| 11.3 | Report to the owner | steward (Stream B drafts from the measurement files) | none | plain words: what ran, how long it took, what it cost, what the test found, that nothing was sealed, published or served, that the test is fully removed, what changes for the full build (time estimate, whether the 7200 s asset timeout is enough, certification cost) | the owner has the numbers needed to decide the full build after Suvarna's elevation | — |

---

## Stop conditions and who is told

| Condition | Stop? | Who is told |
|---|---|---|
| Any row-0 prerequisite not merged or deployed; image/checkout skew | stop | steward (owner if the sitting date moves) |
| Teardown role undecided; Suvarna not told; W1 row / W2(c) isolation setting | stop | owner; Suvarna |
| Registry row not in the 1304 shape; any non-zero in R2 | stop | steward; Stream A (shape), Stream B (readback) |
| Corpus probe mismatch | stop | steward, Stream A |
| Dispatch refusal | stop, read the named refusal | steward; Stream A if it is a script defect |
| Run not executed within 10 minutes | re-stage | steward |
| Build failure in any phase (read from R7c, NOT from Cloud Run, which reports success even when the run FAILED) | stop; keep the logs; teardown, then re-dispatch if the steward decides | steward; Stream A (writer), owner informed |
| A P1 anchor failure on production | stop the sitting; no run 2 | steward; Stream A; owner informed |
| Teardown refusal (especially a NULL-linked receipt) | stop; no manual repair | steward; owner |
| Anything written outside the pinned chart and generation | stop immediately | owner |

---

## Readback library (read-only SQL; run with a read-only production connection: `psql -X -At -F ' | '`)

**R1 — the registry row (expected values for the 1304 shape):**
```sql
SELECT asset_id, layer, scope, asset_kind, is_active, catalog_status, has_writer, has_substeps, depends_on,
       rebuild_on_probe_fail, coalesce(integrity_check_sql,'') = '' AS no_integrity_sql, coalesce(health_probe::text,'') = '' AS no_health_probe,
       target_table, writer_timeout_seconds, target_floor, estimated_seconds, count_sql
  FROM asset_registry WHERE asset_id = 'ka_gochara_v5';
```
Expected: scope `per_chart`; `is_active` f; `catalog_status` CURRENT; `asset_kind` data; `has_writer` t; `has_substeps` t; `depends_on` `{ga_positions,ga_dashas}`; `rebuild_on_probe_fail` f; `no_integrity_sql` t; `no_health_probe` t (an integrity SQL plus `rebuild_on_probe_fail` true would let the runner mark the asset complete WITHOUT calling the writer: asset_runner probe-green shortcut); `target_table` `ka_gochara_eval_window`; `writer_timeout_seconds` 7200; `target_floor` 0; `estimated_seconds` empty; `count_sql` `SELECT COUNT(*) FROM ka_gochara_eval_window WHERE chart_id=$1 AND generation='5.0'`.

**R2 — zero state (all expected 0):**
```sql
SELECT 'receipts', count(*) FROM asset_provenance_receipts WHERE asset_id='ka_gochara_v5'
UNION ALL SELECT 'freshness', count(*) FROM asset_freshness WHERE asset_id='ka_gochara_v5'
UNION ALL SELECT 'throughput', count(*) FROM asset_throughput WHERE asset_id='ka_gochara_v5'
UNION ALL SELECT 'substep_progress', count(*) FROM build_substep_progress WHERE asset_id='ka_gochara_v5'
UNION ALL SELECT 'runs naming the asset', count(*) FROM build_runs r WHERE r.scope_target LIKE '%ka_gochara_v5%' OR EXISTS (SELECT 1 FROM build_run_assets a WHERE a.run_id=r.id AND a.asset_id='ka_gochara_v5')
UNION ALL SELECT 'run_assets (any run)', count(*) FROM build_run_assets WHERE asset_id='ka_gochara_v5'
UNION ALL SELECT 'manifest 5.0', count(*) FROM kala_gochara_publication WHERE generation='5.0'
UNION ALL SELECT 'seal 5.0', count(*) FROM ka_gochara_generation_seal WHERE generation='5.0'
UNION ALL SELECT 'authority names 5.0', count(*) FROM kala_gochara_authority WHERE authoritative_generation='5.0'
UNION ALL SELECT 'snapshot 5.0', count(*) FROM ka_gochara_search_input_snapshot WHERE generation='5.0'
UNION ALL SELECT 'inventory 5.0', count(*) FROM ka_gochara_search_inventory WHERE generation='5.0'
UNION ALL SELECT 'eval_window 5.0', count(*) FROM ka_gochara_eval_window WHERE generation='5.0'
UNION ALL SELECT 'relationship_record 5.0', count(*) FROM ka_gochara_relationship_record WHERE generation='5.0'
UNION ALL SELECT 'contact 5.0', count(*) FROM ka_gochara_contact WHERE generation='5.0'
UNION ALL SELECT 'coverage event_class 5.0', count(*) FROM kala_gochara_coverage WHERE generation='5.0' AND partition_kind='event_class'
UNION ALL SELECT 'legacy windows 5.0', count(*) FROM kala_gochara_windows WHERE generation='5.0'
UNION ALL SELECT 'legacy contacts 5.0', count(*) FROM kala_gochara_contacts WHERE generation='5.0';
```
(2026-10-05: every row 0.) Note the Moon on-demand coverage partitions (`partition_kind` other than `event_class`) and the global sky-event substrate are KEPT by the teardown by design.

**R2b — GLOBAL tables the sitting populates and the teardown KEEPS (read before run 1 and after each teardown; all `0` in production on 2026-10-05 except the legacy convention row `1`):**
```sql
SELECT 'sky_event', count(*) FROM ka_gochara_sky_event
UNION ALL SELECT 'sky_convention', count(*) FROM ka_gochara_sky_convention
UNION ALL SELECT 'physical_object', count(*) FROM ka_gochara_physical_object
UNION ALL SELECT 'convention_bridge', count(*) FROM ka_gochara_convention_bridge
UNION ALL SELECT 'kala_convention (legacy row expected 1)', count(*) FROM kala_gochara_convention
UNION ALL SELECT 'rule_path', count(*) FROM ka_gochara_rule_path
UNION ALL SELECT 'rule_path_seal', count(*) FROM ka_gochara_rule_path_seal
UNION ALL SELECT 'rule_path_soft_factor', count(*) FROM ka_gochara_rule_path_soft_factor
UNION ALL SELECT 'rule_path_prerequisite', count(*) FROM ka_gochara_rule_path_prerequisite
UNION ALL SELECT 'factor', count(*) FROM ka_gochara_factor
UNION ALL SELECT 'predicate', count(*) FROM ka_gochara_predicate;
```
Why it matters: the `rules` substep seeds the rule registry and its seals (global key), the `convention` substep registers the sky convention and the legacy bridge, and the 8 `body:*` substeps solve and persist the boundary events and stations of Sun, Mercury, Venus, Mars, Jupiter, Saturn, Rahu and Ketu over 1998-01-01 to 2085-01-01 (idempotent insert-if-absent; the Moon is never materialised). **None of this is chart-scoped and the teardown does not remove it**, by design (the full build reuses it); it is a production write that stays. Run 1 therefore builds the substrate from empty, **inside the one 7200 s asset budget**.

**R3 — dependencies lit and fresh (canonical chart):**
```sql
SELECT t.asset_id, t.state, (SELECT string_agg(f.freshness_state, ',') FROM asset_freshness f WHERE f.asset_id=t.asset_id AND f.chart_id=t.chart_id) AS freshness
  FROM asset_throughput t WHERE t.chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND t.asset_id IN ('ga_positions','ga_dashas');
```
Expected `lit` / `fresh` for both.

**R4 — every incoming foreign key of `build_runs` and `kala_gochara_publication`:**
```sql
SELECT c.confrelid::regclass AS parent, c.conrelid::regclass AS child, c.conname,
  (SELECT string_agg(a.attname, ',' ORDER BY k.ord) FROM unnest(c.conkey) WITH ORDINALITY k(attnum, ord) JOIN pg_attribute a ON a.attrelid=c.conrelid AND a.attnum=k.attnum) AS child_cols,
  (SELECT string_agg(a.attname, ',' ORDER BY k.ord) FROM unnest(c.confkey) WITH ORDINALITY k(attnum, ord) JOIN pg_attribute a ON a.attrelid=c.confrelid AND a.attnum=k.attnum) AS parent_cols,
  cardinality(c.conkey) AS ncols,
  CASE c.confdeltype WHEN 'a' THEN 'NO ACTION' WHEN 'r' THEN 'RESTRICT' WHEN 'c' THEN 'CASCADE' WHEN 'n' THEN 'SET NULL' WHEN 'd' THEN 'SET DEFAULT' END AS on_delete, c.condeferrable
FROM pg_constraint c WHERE c.contype='f' AND c.confrelid IN ('public.build_runs'::regclass, 'public.kala_gochara_publication'::regclass) ORDER BY 1,2,3;
```
Expected on 2026-10-05, all `ncols` = 1, none deferrable: `build_run_assets.run_id` CASCADE; `asset_provenance_receipts.build_id` SET NULL; `conversations.archived_by_run_id`, `event_chart_state_index`, `mimamsa_predictions`, `mimamsa_calibration_snapshot`, `brahma_prospective_ledger`, `brahma_mimamsa_prediction_ledger` (all `chart_context_superseded_by_run_id`) SET NULL; `kala_gochara_contacts.input_generation_vector_id` -> `manifest_id` NO ACTION.

**R5 — privileges a role lacks for the teardown (run once per role; `\set r data_plane_builder` or the chosen role).** Prints one row per MISSING privilege; the teardown needs DELETE and SELECT on the listed tables, SELECT on the rest, UPDATE(`is_active`) on `asset_registry` only if the row is found active, and EXECUTE on `ka_gochara_lock_chart(uuid)` and `ka_gochara_generation_is_sealed(uuid, text)`:
```sql
WITH t(tbl, privs) AS (VALUES
 ('asset_provenance_receipts','SELECT,DELETE'),('asset_freshness','SELECT,DELETE'),('build_run_assets','SELECT,DELETE'),('build_runs','SELECT,DELETE,UPDATE'),
 ('asset_throughput','SELECT,DELETE'),('ka_gochara_eval_window','SELECT,DELETE'),('ka_gochara_relationship_record','SELECT,DELETE'),('ka_gochara_contact','SELECT,DELETE'),
 ('kala_gochara_coverage','SELECT,DELETE'),('ka_gochara_search_interval','SELECT,DELETE'),('ka_gochara_search_obligation','SELECT,DELETE'),('ka_gochara_search_path_pin','SELECT,DELETE'),
 ('ka_gochara_search_inventory','SELECT,DELETE'),('ka_gochara_search_input_snapshot','SELECT,DELETE'),('kala_gochara_publication','SELECT,DELETE,UPDATE'),
 ('ka_gochara_generation_seal','SELECT'),('kala_gochara_authority','SELECT'),('asset_registry','SELECT'),('kala_gochara_windows','SELECT'),('kala_gochara_contacts','SELECT'),
 ('conversations','SELECT'),('event_chart_state_index','SELECT'),('mimamsa_predictions','SELECT'),('mimamsa_calibration_snapshot','SELECT'),
 ('brahma_prospective_ledger','SELECT'),('brahma_mimamsa_prediction_ledger','SELECT'))
SELECT tbl, p AS missing_privilege FROM t, unnest(string_to_array(privs, ',')) p
 WHERE to_regclass('public.'||tbl) IS NOT NULL AND NOT has_table_privilege(:'r', 'public.'||tbl, p)
UNION ALL SELECT 'ka_gochara_lock_chart(uuid)', 'EXECUTE' WHERE NOT has_function_privilege(:'r', 'public.ka_gochara_lock_chart(uuid)', 'EXECUTE')
UNION ALL SELECT 'ka_gochara_generation_is_sealed(uuid,text)', 'EXECUTE' WHERE NOT has_function_privilege(:'r', 'public.ka_gochara_generation_is_sealed(uuid,text)', 'EXECUTE');
```
(`UPDATE` on `build_runs` and `kala_gochara_publication` is for the `FOR UPDATE` row locks Codex round 4 asked the teardown to take; drop those two privileges from the list if the final head does not lock.) The dispatch's list for `data_plane_builder`: SELECT on the tables it reads, INSERT/UPDATE on `asset_throughput`, `build_runs`, `build_run_assets`, UPDATE on one `asset_registry` column, EXECUTE on the lock function: all held today.

**R6 — the staged run and its cut-offs (derive both from the stored `created_at`):**
```sql
SELECT id, state, created_at, created_at + interval '10 minutes' AS execute_by, created_at + interval '90 days' AS teardown_by, plan_manifest_digest
  FROM build_runs WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND triggered_by='gochara-v5-small-test' ORDER BY created_at DESC;
```

**R7a — run and asset state:**
```sql
SELECT r.id, r.state, r.current_asset_id, r.created_at, r.started_at, r.ended_at, left(coalesce(r.last_error,''), 300) AS last_error,
       a.state AS asset_state, a.started_at AS asset_started, a.ended_at AS asset_ended, a.ended_at - a.started_at AS asset_duration, a.disposition
  FROM build_runs r LEFT JOIN build_run_assets a ON a.run_id = r.id AND a.asset_id = 'ka_gochara_v5' WHERE r.id = '<run id>';
```
**R7b — progress:** `SELECT count(*), max(completed_at) FROM build_substep_progress WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND asset_id='ka_gochara_v5';`

**R8a — per-substep durations (phase and class timing):**
```sql
SELECT substep_key, rows_written, completed_at, completed_at - lag(completed_at) OVER (ORDER BY completed_at) AS since_previous
  FROM build_substep_progress WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND asset_id='ka_gochara_v5' ORDER BY completed_at;
```
**R8b — counts per table and per class (before the teardown):** the `5.0` counts of R2 plus `SELECT event_class, count(*) FROM ka_gochara_eval_window WHERE generation='5.0' GROUP BY 1 ORDER BY 1;` and the same for `ka_gochara_search_inventory`, `ka_gochara_search_obligation`, `ka_gochara_search_interval`.
**R8c — in-build verification rows, if any were written:** `SELECT status, count(*) FROM ka_gochara_eval_window_verification WHERE generation='5.0' GROUP BY 1;` and `SELECT count(*) FROM ka_gochara_search_inventory_verification WHERE generation='5.0';`

**R9 — what the teardown does not delete (read after it):** `SELECT count(*) FROM build_substep_progress WHERE asset_id='ka_gochara_v5'` (the teardown's delete list does not include these rows; see open question 3), the Moon on-demand coverage partitions, the global sky-event substrate rows written by the `body:*` substeps (kept by design; they are global and idempotent).

### Corpus probe (PR 3102, `platform/scripts/gochara-pipeline-ephe-probe.sh`)

- **Read-only.** It runs on the steward's machine: resolves the job's CURRENT image (`gcloud run jobs describe`, read-only), runs THAT image locally with an entrypoint override (`docker run --rm --entrypoint sha256sum <image> -- /app/ephe/sepl_18.se1 /app/ephe/semo_18.se1 /app/ephe/seas_18.se1`), echoes the image's `SE_EPHE_PATH`, and compares the three digests with the pins READ from `platform/python-sidecar/tests/l3/gochara/conftest.py` (`SE1_CHECKSUMS`: `ca1393ce…` sepl_18, `1ca07bd6…` semo_18, `a2cd8fc3…` seas_18). It never touches the job, a database or a credential, and writes nothing outside the local docker daemon.
- **Default `--print` executes nothing and shows the command sequence**; `--run` executes. From a checkout of the PR branch (no merge needed): `bash platform/scripts/gochara-pipeline-ephe-probe.sh brahma-build-pipeline-job asia-south1 --project madhav-astrology` (print), then the same with `--run`. Needs `gcloud` (read access to the job and the Artifact Registry image), `docker` and `python3` on PATH.
- **After PR 3142 merges the probe as written FAILS to read its pins:** `tests/l3/gochara/conftest.py` then defines `SE1_CHECKSUMS = dict(_PINS)` (an import), while the probe AST-parses a LITERAL dict; it must read `PINNED_SE1_SHA256` from `platform/python-sidecar/services/gochara_kernel/ephemeris_pins.py` (a literal dict) instead. Fix that before relying on the probe.
- **Un-holding:** running it needs no un-holding; the hold is on MERGING PR 3102. Stream B's view: the build-time `sha256sum -c` in `Dockerfile.pipeline` makes a missing corpus very unlikely and the job definition overrides no ephemeris variable, so it is cheap insurance rather than a blocker; but it answers the question for the exact image the printed Cloud Run command will run, so run it once, and again after the ephemeris fix changes the image. (The last production proof that the files were readable is the `bg_ephemeris_engine` self-test, 2026-08-27, an older image.)

### Teardown role: the question for the owner

The teardown must DELETE, and even its dry run performs the DELETEs before rolling back. From the production catalog (2026-10-05):

| Candidate | Holds everything the teardown needs? | What it lacks / what it is |
|---|---|---|
| `amjis_app` | **yes** (it owns every table involved) | the broad application owner role: nothing needs granting, but it is a wide identity for a one-off job |
| `data_plane_builder` (the build job's own identity) | no | DELETE on `asset_freshness`, `asset_provenance_receipts`, `kala_gochara_publication`; SELECT on `conversations`, `event_chart_state_index`, `mimamsa_calibration_snapshot`, `brahma_prospective_ledger`, `brahma_mimamsa_prediction_ledger`; UPDATE(`is_active`) on `asset_registry` only if the row is found active (it is not). Migration 1217 states the builder has NO DELETE on `asset_freshness` by design |
| `role_orchestrator` and the verifier/sealer/migrator roles | no | far short (26 to 36 privileges) |

Options: (1) `amjis_app` for the one-off teardown, from a direct connection, after a dry run: needs no grant change; (2) a one-purpose role holding exactly R5's list, created and revoked by a protected migration (and a real-database test run as that exact role, which PR 3098 has); (3) grant the builder the missing privileges: Stream B advises against widening the standing build identity for a one-time job. **Stream B's recommendation: (1)**, unless the owner wants no use of the application role, then (2). The choice is the owner's.

---

## Open questions

1. **Teardown role** (above): the owner's decision; also how its `DATABASE_URL` is provided to the steward without printing.
2. **How migration 1304 (PR 3101) applies** (routine deploy or the protected-migration mechanism) and when; production's registry row is NOT in the 1304 shape today, so the dispatch and the teardown's end-state check both presuppose it.
3. **`build_substep_progress` rows:** the teardown's delete list does not include them. Production has 0 for the asset now. Stream A to confirm that leftover rows after run 1 cannot affect run 2 (replay ignores them) or the N-137 reading, or add them to the teardown.
4. **The monitor reading** in row 9.5: which cockpit screen or query shows the N-137 classification of the asset; Stream A to name it.
5. **Cut-offs from the stored `created_at`** (Codex dispatch D4) and a **`--lookup` mode** for an uncertain commit (D1) are not at head `508561b7e`; until they land, use R6 and look the run up by SQL.
6. **Where in-build verification results and the certification cost are recorded** (Cloud Run logs only, or tables): Stream A to say; row 8 lists both sources.
7. **Docker and gcloud on the steward's machine** for the corpus probe: available? Otherwise Stream A or Stream B runs it where they are.
8. **Capacity expectation:** the 7200 s asset timeout is the 1304 value; whether one year of 26 classes (run 1) and one class over 10,334 days (run 2) fit is exactly what the test measures. If run 1 times out, the finding is that the full build needs a larger timeout (a registry change, its own review).
9. **Image redeploy after the ephemeris fix:** the writer digest, the dispatch's expected digest, the lock aggregate and PR 3141's lock all move; confirm Stream A's deploy sequence (merge, deploy, then row 0.3) so the printed digest matches the image.
10. **PR 3141 (G8)** stays unmerged until after this test (it changes the vector and the lock); after it merges, a small test cannot be repeated from the older checkout without re-dispatching from the matching one.
11. **Concurrent work on the canonical chart during the sitting:** the orchestrator exclusion lock and the Gochara chart lock make a concurrent build or the teardown refuse by name, but the cockpit watchdog takes no advisory lock; confirm no other build or Suvarna window is scheduled on this chart for the sitting.
12. **Cloud Run status is not a signal** (exit 0 on a FAILED run): should the dispatch or a monitor print R7c's verdict for the run id automatically, so the steward is not left reading logs? (the orchestrator is frozen; a read-only helper script would be a Stream A item)
13. **The 7200 s budget versus the first-ever global substrate build** (8 bodies, 1998-2085, from empty) plus the rule registry seed plus one year of 26 classes: if run 1 times out in the body phase the registry timeout (a 1304 value) is too small for a first build; decide beforehand whether to accept that as the finding or to have the timeout raised by a reviewed registry change before the sitting.
14. **Run 1 needs the P1 exclusion fix** (above); until it lands the all-classes slice cannot complete, so the sitting can start with run 2 (one_class_full, marriage) only if the steward chooses to reorder (the clean-receipt rule makes the order free: each run is torn down before the next). Also: the eight H-unknown classes are scored through P2 only today (P1/P3/P4 excluded, P5 withheld): note it in the report to the owner.
15. **Run 2's class:** `marriage` is the class the tests use; confirm it is the class the owner wants for the full-horizon check.

*End of draft v1.0. Authorises nothing; the steward's explicit word is needed for each production write and for lifting the standing hold.*
