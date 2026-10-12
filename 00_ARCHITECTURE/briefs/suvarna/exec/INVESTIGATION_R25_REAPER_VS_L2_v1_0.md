---
artifact: INVESTIGATION_R25_REAPER_VS_L2
version: 1.1
status: DRAFT_FOR_REVIEW
date: 2026-10-01
lane: suvarna/land/TI-r25-reaper-001
decision: R-25 (build-pipeline "15-minute reaper" versus slow L2 writers)
mode: READ-ONLY investigation. No code, config, infra, build or DB write. DB reads as `suvarna_reader` only (measured 2026-10-01 ~18:35Z); code read at origin/main ee12eab8c.
changelog:
  - "1.1 (2026-10-02): added section 7 Decision (SS ruling R-25: options 1 + 3 taken, migration 1218 sets bo_grounding and bo_laksana_rerank to 1800 (first-form 10800 superseded); options 2, 4, 5 and the keep-alive freeze exception not taken; S-L2 stop rule, lit-flip artefact rule and reporting). No change to sections 0-6 or the appendix."
  - "1.0 (2026-10-01): first cut. Four independent liveness/timeout mechanisms mapped with file:line; L2 writer shape and registry budgets; measured per-asset durations; option matrix; verdict on whether the frozen orchestrator must change (it need not)."
---

# R-25: the 15-minute reaper versus slow L2 writers

## 0. Verdict (10 lines)

1. "The reaper" is three different things. (a) The **watchdog** `POST /api/cockpit/watchdog` (amjis-web, Cloud Scheduler `*/5`): per-asset stale-heartbeat reaper, 15 min, hard-coded in SQL, NOT read from the registry. (b) The **in-process per-writer timeout** in `runner.py::execute_dag`: wall clock per asset, read from `asset_registry.writer_timeout_seconds` (default 600). (c) The **startup orphan cleanup** in `runner.py` (marks leftover `building` rows `orphaned_by_crash`). The Cloud Run task timeout is 86400 s and is not a lever.
2. The watchdog keys on `asset_throughput.last_built_at` of a `state='building'` row older than 15 min (clause 2), and on a run `running` > 30 min whose chart has no `last_built_at` and no `build_substep_progress.completed_at` newer than 15 min (clause 1). Not on substep count, not on the registry budget, not on the Cloud Run task.
3. Heartbeat is one `UPDATE last_built_at = NOW()` per **committed substep** in `asset_runner._drive_substeps`. `NOW()` is transaction start, so a heartbeat understates by one substep: the real gap between visible heartbeats is the sum of two consecutive substeps. A **light** writer (single `run(ctx)`) gets one stamp at start and none after, so its reap window is its whole wall time. All 21 non-substep bo_* writers carry an `integrity_check_sql`, so since 2026-08-26 they also run as ONE uncommitted transaction.
4. Shape of the 23 bo_* assets: **2 plan substeps** (`bo_laksana`, `bo_samskara`, 5 ayanamsha substeps each); **21 are light `run(ctx)`** (incl. `bo_laksana_rerank`, `bo_grounding`). `has_substeps` in the registry matches. None of the 23 writes `build_substep_progress`.
5. Live `writer_timeout_seconds`: 15 assets = 10800, 8 assets = 600 (`bo_arudha`, `bo_grounding`, `bo_laksana_rerank`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`, `bo_yantra_mechanism`). `bo_samskara` and `bo_laksana` are 10800, not the 1800 that migration 417 set; no migration sets 10800 (applied directly to the registry).
6. **At risk (by history):** `bo_laksana_rerank` (light, 600 s budget, canonical max 1233 s), `bo_grounding` (light, 600 s budget, a 2026-09-11 run sat 1157 s before being cancelled), `bo_karanajala` (light, max 1091 s). `bo_samskara` (p50 828, max 1468 s) and `bo_laksana` (max 1286 s) heartbeat per ayanamsha substep, so they are exposed only if two consecutive substeps total > 900 s.
7. **At risk NOW (current code, post-2026-08-26): none measured.** Latest single-asset runs: `bo_samskara` 530 s cold / 2 s skip, `bo_grounding` 166 s, `bo_laksana` ~119 s, `bo_laksana_rerank` ~76 s, every other asset that has a recent run < 35 s. The 776 / 1286 s figures are July-August code; both heavy writers sped up since. No bo_* asset has a recorded watchdog reap or in-process TIMEOUT.
8. A 23-asset serial run: p50 sum 1793 s (30 min), critical path 981 s (pre-2026-08-26 canonical); current-code estimate 1154 s serial (cold samskara), critical path 707 s. Sum of per-asset p95 is ~6000 s (conservative bound, not a p95 of the sum).
9. Options NOT touching `runner.py`/`asset_runner.py`, ranked: (1) change nothing now plus a cold-chart re-measure gate; (2) a per-asset threshold in the watchdog route (`route.ts`, amjis-web, not frozen) if a light writer ever legitimately exceeds 15 min; (3) registry `writer_timeout_seconds` edit for `bo_grounding` / `bo_laksana_rerank` (fixes only the in-process budget, NOT the watchdog); (4) convert light writers to substeps (in-contract but changes atomicity, touches FROZEN writers); (5) writer-side heartbeat on a side connection (contract deviation). Job task timeout: no effect.
10. **The only fix is NOT in the frozen orchestrator.** If a heartbeat ever must come from the engine, the exact change is a keep-alive thread around `writer.run_substep` in `asset_runner.py::_drive_substeps` (lines 888-905) using `clock_timestamp()` on a separate autocommit connection, which is a freeze exception and goes to the owner through SS. Nothing measured justifies it today.

## 1. What reaps what (file:line, thresholds, end state)

| # | Mechanism | Where | Trigger (exact) | Reads registry budget? | End state it writes |
|---|---|---|---|---|---|
| W1 | Watchdog clause 1, orphan **run** | `platform/src/app/api/cockpit/watchdog/route.ts:133-167` (30 min at :138, 15 min at :142 and :146) | `build_runs.state='running'` AND `started_at` < now-30 min AND NO `asset_throughput` row for the chart with `last_built_at` > now-15 min AND NO `build_substep_progress` row for the chart with `completed_at` > now-15 min | No | `build_runs` -> `failed`, `last_error='orphan-watchdog: run orphaned...'`; its `queued` bra rows -> `aborted`, its `building` bra rows -> `error` |
| W2 | Watchdog clause 2, stuck **asset** | `route.ts:216-394` (15 min at :231 and :373); decision `classifyStuckCandidate.ts:62-74` | `asset_throughput.state='building'` AND `last_built_at` < now-15 min (any chart, any run) | No (`has_substeps`, `target_floor`, `count_sql` only) | rows present and `has_substeps` false (or `target_floor=0`): **rescue to `lit`** (+ bra `complete`); rows present and `has_substeps` true: **`incomplete`**; no rows: **`error`** `orphan-watchdog: writer never reported back` (+ bra `error`) |
| W3 | Watchdog clause 3, undispatched | `route.ts:429-447` | `planned`, `started_at IS NULL`, created > 10 min ago | No | `failed` / bra `aborted` (49 live rows; plan-time only, not an execution reaper) |
| P1 | In-process per-writer timeout | `runner.py:111` (`WRITER_TIMEOUT_SECONDS` default 600), `:679` (`_timeout_for`), `:705` (deadline at dispatch), `:726-743` (check), `:558-582` (`_mark_asset_timeout`), `:882-893` (loads `writer_timeout_seconds`) | wall clock (`time.monotonic`) from dispatch of THIS asset > `asset_registry.writer_timeout_seconds` | **Yes, the only one that does** | asset `error` `TIMEOUT: writer exceeded its writer_timeout_seconds budget`, asset joins `failed`, its dependents are BLOCKED. Worker thread is not cancelled |
| P2 | Startup orphan cleanup | `runner.py:1368-1392` | at the start of the NEXT run on the chart (holds the chart advisory lock): any `building` row | No | `error` `orphaned_by_crash` (asset_throughput and other runs' bra) |
| P3 | SIGTERM drain | `runner.py:117-123` (`_shutdown`, `_handle_sigterm`) | Cloud Run SIGTERM | No | run `stopped`, in-flight substeps finish |
| J | Cloud Run job task timeout | `.github/workflows/deploy.yml:2194` `--task-timeout=86400` on `brahma-build-pipeline-job` | 24 h per task | n/a | task killed; transactions roll back. Dispatch only overrides args/env (`platform/src/lib/build/jobInvoker.ts:82-91`) |
| X | `/api/build/reap` + `infra/cloud_scheduler/build_reaper.tf` (`*/15`) | `platform/src/app/api/build/reap/route.ts` | returns **410 ENDPOINT_GONE** ("superseded by /api/cockpit/watchdog") | n/a | no-op. This is the other "15-minute reaper" by name; the Terraform job is still declared; whether it still exists in GCP is unverified |

Watchdog cadence: Cloud Scheduler `*/5` (`platform/scripts/provision_watchdog_scheduler.sh`; `00_ARCHITECTURE/CONDUCTOR/go-live/PHASE_LOG.md:197`), so a stale row is hit between 900 s and 1200 s after its last visible heartbeat. The file header (`route.ts:21-35`) states the doctrine: thresholds "MUST hold"; heavy assets are kept alive by the per-substep heartbeat, not by relaxing the reaper.

### 1.1 Heartbeat mechanics (why substeps matter, and the `NOW()` catch)

- Initial stamp: `asset_runner.py:1552-1579` upserts `state='building', last_built_at=NOW()` and **commits**. The comment at `:1534-1548` states the design assumption: single-substep writers "complete well under 15 min".
- Per-substep heartbeat: `asset_runner.py:906-915` (`UPDATE asset_throughput SET last_built_at = NOW(), rows_written = ...` then `conn.commit()` unless `defer_commits`). The substep itself runs between `SAVEPOINT writer_exec` (`:888`) and `RELEASE`.
- `NOW()` is the START of the current transaction, so substep k's stamp equals substep k's start, committed at its end. At the instant just before substep k+1 commits, the visible stamp is `E(k-1)`: the visible silence is `d(k) + d(k+1)`, not `d(k+1)`. The same transaction-start semantics mean `build_run_assets.ended_at` and `asset_throughput_state_audit.changed_at` (`DEFAULT now()`, migration 586:72) understate duration for any writer that does not commit per substep (see 3.1).
- Light writer with a detector: `asset_runner.py:1177` `defer_writer_commits = has_integrity_check and not writer.has_substeps`. All 21 non-substep bo_* writers have `integrity_check_sql` (query in appendix), so each runs as one transaction; its heartbeat UPDATE and every row it writes are invisible to the watchdog until completion. Introduced 2026-08-26 (`5f47906bc`, #1553); before that a light writer committed at its end anyway, so the visible silence was the same.
- Completion: `asset_runner.py:1350-1367` sets the final state with **no `state='building'` predicate**, so a worker that finishes after a reap overwrites it (`lit` / `complete`).

### 1.2 What survives a reap (transaction / savepoints / state)

- **The watchdog never touches the worker.** It UPDATEs `asset_throughput` / `build_runs` / `build_run_assets` from the web app's connection. The orchestrator polls only `stop_requested_at` / `pause_requested_at` (`runner.py:451-463`), so a `failed` run state is invisible to it. The worker's connection, open transaction, `writer_exec` savepoint and committed substeps all survive.
- A live process therefore **self-heals**: the worker's own completion UPDATE restores `lit`/`complete`, the `queued`->`aborted` bra rows are revived by the `ON CONFLICT (run_id, asset_id) DO UPDATE SET state='building'` upsert (`asset_runner.py:1566-1572`), and `mark_run_state` (`runner.py:1444-1450`) overwrites the `failed` run state. The chart advisory lock keeps a second run out meanwhile (`runner.py:1313-1318`).
- **Harm window is the interval, not the end state:** a false `error`/`incomplete` badge, a false run `failed`, notifications, and a **false `lit` (rescue path)**: a light writer re-running over existing data passes the `count_sql > 0` probe from the watchdog's snapshot, so it is promoted to `lit`/`complete` while still mid-transaction. If the process then dies, the transaction rolls back and the stale `lit` stays over the OLD rows.
- If the process dies after a reap: light writer loses its whole transaction (old rows survive); heavy writer keeps committed substeps (resumable), asset ends `incomplete`/`error`, next run's P2 cleanup rewrites any leftover `building`.
- In-process timeout P1 differs: it fails the asset AND blocks its dependents for the rest of that run even though the thread keeps running and may still land data.

## 2. The 23 bodha writers: shape, budget, measured duration

`asset_registry` (`suvarna_reader`, 2026-10-01): 23 active bo_* rows, all `asset_kind='data'`, all `rebuild_on_probe_fail=false`, all with `integrity_check_sql`. Code: `platform/python-sidecar/pipeline/orchestrator/writers/bo_*.py`. `bo_pratijna_karyatva.py` and `bo_pratijna_v4_engine.py` are helper modules, not assets; `bo_laksana_rerank` is a second `@register` in `bo_laksana.py:3821`.

Duration source: `build_run_assets` `state='complete'`, chart `482012f1` (canonical), `started_at` < 2026-08-26, rows with elapsed >= 1 s ("exec"), because before the 2026-08-26 defer change `ended_at` ~ true end. After it, light-writer bra durations read ~0 (transaction-start `NOW()`), so "current" uses `build_runs.ended_at - started_at` of completed **single-asset** runs created >= 2026-08-26 (includes 3-25 s dispatch overhead; 2 s = delta-skip no-op).

| asset | kind (has_substeps) | `writer_timeout_seconds` | pre-8/26 canonical n_exec / p50 / p95 / max (s) | current single-asset runs (s) | verdict |
|---|---|---|---|---|---|
| bo_samskara | **heavy**, 5 aya substeps | 10800 | 18 / 828 / 1185 / 1218 (all charts max 1468) | 530 (cold), 2 (skip) | heartbeats per substep; exposed only if 2 consecutive substeps > 900 s |
| bo_laksana_rerank | light | **600** | 10 / 395 / 1210 / 1233 | 78, 75 | pre: exceeded 600 and 900. Now 7.9x margin |
| bo_laksana | **heavy**, 5 aya substeps | 10800 | 21 / 120 / 1272 / 1286 | 122, 149, 115 (+2 skip) | as samskara |
| bo_drishti | light | 10800 | 18 / 81 / 136 / 176 | none | ok |
| bo_anveshana | light | 10800 | 18 / 28 / 241 / 374 (all charts 511) | 34, 27 | ok |
| bo_karanajala | light | 10800 | 19 / 25 / 310 / **1091** (1 of 19 > 900) | 20, 19, 12 | pre: one breach; now ok |
| bo_upaya | light | 10800 | 20 / 24 / 71 / 76 | 22, 22 | ok |
| bo_bimba | light | 10800 | 19 / 19 / 45 / 55 | 13 | ok |
| bo_pratijna | light | 10800 | 20 / 16 / 38 / 52 | none | ok |
| bo_sangati | light | 10800 | 19 / 14 / 38 / 43 | 14, 6 | ok |
| bo_yantra_mechanism | light | 600 | 11 / 13 / 127 / 138 | 4 | ok |
| bo_sudarshana | light | 600 | 4 / 10 / 10 / 10 | 3, 3, 2 | ok |
| bo_nakshatra_semantic | light | 600 | 4 / 9 / 11 / 11 | 8, 3, 3, 2 | ok |
| bo_cgm_motifs | light | 10800 | 18 / 9 / 90 / 100 | 4 | ok |
| bo_vargottama_dhana | light | 600 | 3 / 7 / 8 / 8 | 3, 2, 2 | ok |
| bo_cgm_paths | light | 10800 | 11 / 6 / 19 / 26 | none | ok |
| bo_arudha | light | 600 | 4 / 6 / 7 / 8 | 3, 2 | ok |
| bo_special_lagna | light | 600 | 2 / 6 / 9 / 9 | 3, 2, 2, 2, 2 | ok |
| bo_pramana_mapa | light | 10800 | 19 / 4 / 23 / 28 | 25 | ok |
| bo_cdlm_summary | light | 10800 | 16 / 4 / 13 / 17 | none | ok |
| bo_chart_gestalt | light | 10800 | 17 / 2 / 10 / 12 | 18 | ok |
| bo_samvada | light | 10800 | 6 / 1 / 2 / 2 | 3 | ok |
| bo_grounding | light | **600** | no rows (asset added after) | 166 (n=1); **2026-09-11 run: 1157 s before cancel** | in-process budget margin 3.6x now; the 1157 s was the integrity step, cancelled by "user request" (fixed since by migration 1032 set-based integrity) |

Which exceed which threshold:

- **> 600 s in-process budget (P1):** `bo_laksana_rerank` (4 of 10 canonical rows), `bo_grounding` (one observed run). Currently neither. Caveat: the rerank history shows runs of 1133-1233 s that finished `completed` with `bo_sangati` complete under a registry default of 600 (migration 446 sets no budget), so the budget must have been raised ad hoc at the time or P1 did not fire; there is no registry history to tell (unverified).
- **> 900 s watchdog (W2), light writers:** `bo_laksana_rerank` (3 of 10), `bo_karanajala` (1 of 19), `bo_grounding` (1157 s). None currently.
- **> 900 s watchdog, heavy writers:** not directly measurable (no per-substep durations: no bo_* writer writes `build_substep_progress`; bra timestamps are transaction-start). Per-substep average at the pre-8/26 p95 is ~240 s (samskara) / ~255 s (laksana), pair ~480-510 s, below 900 s unless a substep is badly skewed.
- **Run-level (W1):** needs a run > 30 min and 15 min of chart-wide silence. Not reached on any measured L2 run; the worst-case serial sum is only past 30 min at the pre-optimization p95 level.
- **Statement / idle limits (separate from the reaper):** `amjis_app` has `statement_timeout=1800s`, `idle_in_transaction_session_timeout=600s` (`pg_db_role_setting`); the build job runs as `data_plane_builder`, which has NO role-level setting, and `bo_laksana.py` notes a 30 s role-default `statement_timeout` (writers use `SET LOCAL`). Seven `QueryCanceled: statement timeout` rows (3 bo_, July) are this class, not the reaper.

### 2.1 History of reaped / aborted L2 runs (build_runs / build_run_assets, all charts)

- bra states for bo_*: complete 764, queued 405, error 381, aborted 156.
- Of the 381 errors, 331 are `BLOCKED:` cascades. Non-cascade bo_* errors: `orphaned_by_crash` 20 (P2, July, local-proxy era), `worker_crash: OperationalError connection is lost` 10 (July-August, the cloud-sql-proxy drops documented in `infra/monitoring/alerts/local_proxy_drop_detection.json`), `DEP-ASSERT` 6, post-write integrity 4, `QueryCanceled` 3.
- Of the 156 aborted: 72 NULL error, 83 `guardian_cleanup` / `manual reap:` (zero source hits in the repo, `00_ARCHITECTURE/briefs/nirmana/engine/STATE.md:66`: external/operator SQL), 1 frozen-manifest.
- **Zero** build_run_assets rows anywhere carry `orphan-watchdog: writer never reported back` or `orphan-watchdog: run orphaned`, and zero carry `TIMEOUT:`. Caveat: pre-Packet-A2 the watchdog never wrote bra and the worker's completion overwrites an in-flight reap, so a missing mark in bra is weak evidence.
- Stronger evidence: `asset_throughput_state_audit` (2026-08-22..2026-09-12, 170 bo_* transitions): the watchdog's signature is a transition with `triggered_by IS NULL` from the web app role. 15 NULL-triggered rows exist (9 app-role, 6 `psql`), **none on a bo_* asset**. One real watchdog reap of a heavy writer is visible on a non-bo asset: `ga_structural` `building -> incomplete`, `triggered_by NULL`, 2026-09-07 23:10:13, then overwritten by the writer's own `lit`. So the route does fire, and the self-heal behaviour in 1.2 is observed, not just read.
- Run-level: `build_runs.last_error` has 49 `orphan-watchdog: run never dispatched` (W3) and none for W1. Many September runs (mostly ka_kshetra) were cancelled by conductor cycles on a 240 s unchanged-log-line stall bar: an agent-level rule, not product code, and shorter than 15 min.

## 3. Options that do not touch `runner.py` / `asset_runner.py`

| # | Option | What it changes | Approval | Risk | Rank |
|---|---|---|---|---|---|
| 1 | **No change now; add a cold-chart re-measure gate** | Nothing in code. Before the next NEW chart's L2 build, take the single-asset durations of `bo_samskara` (cold embeddings), `bo_grounding`, `bo_laksana_rerank`, `bo_karanajala`; act only if a light writer > ~600 s or a heavy substep pair > ~600 s | None (measurement) | Cold samskara is the one real unknown: 530 s on the canonical chart is a total across 5 substeps with warm reuse partly disabled | **1** |
| 2 | **Per-asset threshold inside the watchdog route** (`route.ts` clause 2 + 1, mirror `orphanRunReaperPolicy.ts`, `classifyStuckCandidate` SQL-text tests): e.g. `last_built_at < now() - GREATEST(15 min, ar.writer_timeout_seconds)`-style, or a new `watchdog_stale_seconds` registry column | Lets a declared-slow light writer outlive 15 min without relaxing the global reaper | SS ruling to owner: it alters the doctrine written in `route.ts:21-35` ("thresholds MUST hold"), SAMĀPTI B-WATCHDOG-LIT / DVA Ruling 10 territory; amjis-web deploy. NOT a frozen-orchestrator change | Medium: a 10800 budget would let a truly hung light writer look alive for 3 h in the UI; mitigate by a dedicated, smaller column | 2 (only if needed) |
| 3 | **Edit `writer_timeout_seconds`** for `bo_grounding` and `bo_laksana_rerank` (600 -> larger) | Only the in-process budget P1. **Does NOT affect the 15-min watchdog** (the route never reads it) | Registry data edit on an `amjis_app`-owned table. I found no standing pre-approval for registry VALUE edits (the F3 doc's "ALTER-only, pre-approved" covers DDL on `amjis_app` tables). Precedent: `mi_bhara` 600 -> 10800 under GA-3 packet discipline, owner-delegated (FABLE-5 ruling 2026-08-22, `briefs/parisesa/state/ledger.json`) and the ten-asset packet `F104_F35_TENASSET_REBUILD_PACKET_v1_0.md:173`. So: SS ruling, with before/after image | Low; but each raise widens the hang-detection window; unnecessary today (3.6x and 7.9x margin) | 3 |
| 4 | **Convert light writers to `plan_substeps` / `run_substep`** | In-contract: `WriterBase` supports it and no orchestrator change is needed; also needs registry `has_substeps=true`. Gives a heartbeat every substep and makes a stuck-with-data reap read `incomplete` rather than a false `lit` | L2 writer owner + SS; several L2 writers are FROZEN (`bo_laksana` FROZEN per the 2026-09 cycle commits) and must not be reopened | Highest: breaks the light-writer atomic rollback guarantee (`asset_runner.py:1172-1179` comment), needs per-substep key-scoped replace (`bodha_writers/_idempotency`), new bugs | 4 |
| 5 | **Heartbeat from inside the writer** | A write on `ctx.db_conn` is useless (uncommitted, and writers must never commit: CLAUDE.md §N.2); the only working form is a side autocommit connection updating `asset_throughput.last_built_at` | Contract deviation (§N.2: "orchestrator is the sole build-state writer"); owner | A keep-alive can mask a hung main thread; every writer would need it | 5 |
| 6 | Cloud Run job task timeout | Already 86400 s; independent of the reaper | Infra owner; no change needed | n/a | not a lever |
| 7 | "Split the batch so no statement exceeds the threshold" | The reaper keys on heartbeat AGE, not statement length (`statement_timeout` is the statement bound). Splitting statements without committing between them changes nothing. Splitting into committed substeps = option 4. Dispatching assets as separate single-asset runs (what the L2 campaign does) avoids clause 1 but not clause 2 | n/a | n/a | not a lever |

Run-level versus asset-level: clause 1 spares a run if ANY asset of the chart wrote a heartbeat or any substep committed in the last 15 min, so a long light writer is run-protected whenever a sibling is progressing; it is exposed at the asset level (clause 2) regardless.

## 4. Is the only fix in the frozen orchestrator?

No. The reaper is `platform/src/app/api/cockpit/watchdog/route.ts` (web app), and its two relevant knobs (threshold and evidence signal) live there; option 2 is entirely outside `runner.py` / `asset_runner.py`. There is also no measured breach under the current code. If the owner nevertheless wants the engine itself to prove liveness, the exact change is:

- File: `platform/python-sidecar/pipeline/orchestrator/asset_runner.py`, `_drive_substeps`, around the `writer.run_substep(ctx, step)` call (lines 888-905).
- Change: run a daemon keep-alive thread for the duration of each `run_substep` that, every <= 300 s, executes on a **separate autocommit connection** `UPDATE asset_throughput SET last_built_at = clock_timestamp() WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = %s AND state = 'building'`, and stops when the substep returns or raises. Use `clock_timestamp()`, not `NOW()`, because of the transaction-start semantics in 1.1. Nothing else in the contract changes (`WriterBase`, `ctx.db_conn`, savepoints untouched).
- Cost: a freeze exception of the same class as the SATYA-DĪPA `asset_runner.py` change (`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` §7.1), so owner approval through SS, plus a mutation-proofed test that a hung writer (keep-alive thread alive, main thread blocked) is still caught by the P1 budget.

## 5. Serial duration of a 23-asset L2 run

Per-asset n, p50 and p95 are in the table in section 2 (canonical chart, pre-2026-08-26, rows >= 1 s; `bo_grounding` from the single-asset run). Sums use the p50 / p95 columns plus `bo_grounding` (166 s p50, 1157 s observed worst):

| basis | serial sum | critical path (DAG, bo_* edges from `asset_registry.depends_on`) |
|---|---|---|
| pre-2026-08-26 canonical p50 (22 assets n=2..21 + grounding 166) | 1793 s (~30 min) | 981 s |
| pre-2026-08-26 canonical sum-of-p95 (upper bound, not a p95 of the sum) | ~6030 s (~100 min) | 3277 s |
| current code, latest single-asset runs (samskara cold 530; drishti, pratijna, cgm_paths, cdlm_summary taken from pre-8/26 p50 as they have no newer run) | 1154 s (~19 min) | 707 s |

The dispatch width is `ORCHESTRATOR_WORKER_LIMIT` (code default 4, `runner.py:101`; the 2026-08 ten-asset packet reported 2 on the live job), so wall-clock is between the critical path and the serial sum. Run age exceeds the 30-min W1 gate only under the pre-optimization p95 case.

## 6. Unverified items

1. Live Cloud Scheduler state: the `watchdog-reaper` cadence (`*/5` from the provision script and PHASE_LOG, not read from GCP) and whether the stale `build-reaper` job (`*/15`, `/api/build/reap` returns 410) still exists.
2. Historical `writer_timeout_seconds` per run (no registry audit table). The 600 default would have TIMEOUT-failed `bo_laksana_rerank` runs of 1133-1233 s; they completed, so the budget was different at the time, or P1 behaves differently than read.
3. Live Cloud Run job `maxRetries` and `ORCHESTRATOR_WORKER_LIMIT` (not in `deploy.yml`; the packet quotes 2 / 86400), and the `data_plane_builder` role's effective `statement_timeout` / `idle_in_transaction_session_timeout` (no role-level setting found; cluster flags not readable).
4. Per-substep durations of `bo_samskara` / `bo_laksana` (not recorded anywhere), so the 2-consecutive-substeps > 900 s exposure is inferred from an even split, not measured; the same for cold (new-chart) `bo_samskara`.
5. Who cancelled `bo_grounding`'s integrity statement on 2026-09-11 23:36:07 ("canceling statement due to user request"), and why that run ended 23:55:06, 19 min later.
6. No watchdog hit on a bo_* asset before 2026-08-22 (audit table start) or before Packet A2 (~2026-09-26) can be excluded.

## 7. Decision (SS, R-25, ruling of 2026-10-01; value revised and recorded 2026-10-02)

**Taken**

- **Option 1 (no change to the orchestrator, the watchdog or the writers now).** The cold-chart re-measure idea stays as a measurement, not a gate on code.
- **Option 3 (registry `writer_timeout_seconds` edit), for `bo_grounding` and `bo_laksana_rerank` ONLY**, 600 -> **1800** (30 min). Reason: the in-process per-writer timeout (`runner.py:679` `_timeout_for`, `:726` deadline check) is the one mechanism that can actually fail an asset and block its dependents for the run, and the N-59 L2 fixes add work to the rerank. Why 1800: it covers the worst recorded runs with margin (`bo_laksana_rerank` 1233 s, `bo_grounding` 1157 s, section 2); it bounds a real hang at 30 minutes instead of 3 hours, and `bo_sangati` sits directly behind `bo_laksana_rerank` (blocked until the rerank finishes or times out); and it matches the 30-minute idle-in-transaction cap the orchestrator sets (`pipeline/orchestrator/db.py:49-76`, which also sets `statement_timeout = 0`). Authored as migration **1218** (`platform/migrations/1218_suvarna_bodha_writer_timeouts.sql`, branch `suvarna/land/TI-timeouts-1218-001`, PR #2846, draft, not applied). It is guarded (`WHERE ... writer_timeout_seconds = 600`), idempotent, never overwrites a different value (a target at any other value is left alone with a NOTICE and the migration still succeeds, so the post-apply check that both rows read 1800 must be run), and verifies in-transaction against a snapshot that exactly those two rows changed.
- **Superseded:** the first form of this ruling was 10800 (the value the other 15 bodha assets carry). SS replaced it with 1800 the same day, before anything was applied; 10800 is not what 1218 sets.

**What 1800 does and does not fix (honest trade-offs)**

- It fixes only the in-process budget (P1). It does not change the 15-minute watchdog (section 1, W2; `route.ts:216-394`), which never reads the registry. Any run of either asset longer than 15 minutes remains exposed to W2, and a light writer re-running over existing data can be falsely flipped to `lit` while its worker is still running (section 1.2).
- A larger budget lengthens hang detection for these two assets from 10 minutes to up to 30 minutes.
- Neither asset has substeps (both are light writers), so substep-progress monitoring cannot observe them; their wall time must be watched directly.
- The other six bodha assets still at 600 (`bo_arudha`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`, `bo_yantra_mechanism`) are not part of this ruling and are untouched.

**NOT taken, but available if a real reap or timeout is ever observed**

- Option 2 (per-asset threshold in the watchdog route).
- Option 4 (convert light writers to substeps).
- Option 5 (heartbeat from inside the writer).
- The keep-alive freeze exception in `asset_runner.py::_drive_substeps` (section 4). It would go to the owner through SS as a freeze exception, and only with a measured reap or timeout behind it.

**Operating rules for S-L2**

- **Stop rule:** if any asset goes more than 12 minutes without substep progress, stop dispatching further waves and look. Never kill a live worker. For `bo_grounding` and `bo_laksana_rerank`, which have no substeps, watch wall time directly (12 minutes from dispatch) instead of substep progress.
- A watchdog reap during the run is not itself a failure. Judge by final state (section 1.2: a live worker self-heals), and list every reap that occurred.
- Treat any state flip to `lit` while that asset's worker is still running as a watchdog artefact (the rescue path in section 1.2): record it, and verify the final state after the worker ends.
- After S-L2, report per-asset wall times, so section 2's table can be refreshed from the same run.

**Note on the `mi_bhara` precedent.** The 600 -> 10800 change for `mi_bhara` has no migration file in the repository (searched `platform/migrations` and `platform/supabase/migrations`; consistent with item 5 of section 0, "applied directly to the registry"). Migration 1218 is therefore the first checked-in migration that sets a bodha `writer_timeout_seconds` since 420/462, and it deliberately uses a different value (1800) from `mi_bhara`'s.

## Appendix: queries (all read-only, `suvarna_reader`, wrapper sources `~/.config/suvarna/pgenv.sh`, `default_transaction_read_only=on`)

- Registry: `select asset_id, has_substeps, writer_timeout_seconds, is_active, has_writer, target_floor from asset_registry where asset_id like 'bo\_%'` (23 rows); `integrity_check_sql is not null` (23 of 23); `depends_on` for the DAG.
- Durations: `build_run_assets` join `build_runs` on `run_id`, `state='complete'`, `started_at < '2026-08-26'`, `extract(epoch from ended_at-started_at)` with `percentile_cont(0.5/0.95)`, per asset, chart `482012f1-710e-4a25-994a-93821f5871aa`; "current": `build_runs` with `jsonb_array_length(plan)=1 and state='completed' and scope_target like 'bo\_%' and created_at >= '2026-08-26'`, `ended_at - started_at`.
- Reap evidence: `build_run_assets.error` classified by prefix (`orphan-watchdog`, `TIMEOUT:`, `orphaned_by_crash`, `BLOCKED`, ...); `asset_throughput_state_audit` where `triggered_by is null`, and `building -> error` transitions for bo_*; `pg_db_role_setting` for role timeouts.
