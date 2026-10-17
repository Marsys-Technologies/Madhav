---
artifact: S_L2_REHEARSAL_PLAN
version: 1.1
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna (bo-uuid-fix worker, S-L2 PREP lane, SS decision N-96)
produced_on: 2026-10-03
decision: N-91 conditions 7 (S-L2 preparation is the top priority from S-L1 close, "the rehearsal") and ruling 3 (the clock; day-7 checkpoint requires "S-L2's off-production rehearsal has passed")
scope: documentation only. A plan for an off-production rehearsal on a disposable database. Nothing here is executed, no migration is authored, no production write, no birth data (the canonical chart is referred to by id only; birth inputs are held by the S-L1 runbook, never by this repository).
sources:
  - /Users/Dev/suvarna-evidence/S_L1/REHEARSAL_LINUX_REPORT.md (reconstructed S-L1 Linux rehearsal; the model for this plan)
  - /Users/Dev/suvarna-evidence/OwnerDecisions/N-91_between_state_ruling_v1_0.md, N-93_watchdog_pause_ruling_v1_0.md
  - 00_ARCHITECTURE/briefs/suvarna/exec/s_l2/S_L2_WINDOW_RUNBOOK_v1_0.md (W-steps, acceptance checks A2-xx) and s_l2_attribution_hooks/ (this lane)
  - /Users/Dev/suvarna-evidence/S_L2/work/L2_DATAPLANE_MECHANICS.md and L2_WRITES_MAP.md (this lane's code and reader studies)
changelog:
  - "1.1 (2026-10-03): #3008 is merged; B7 added as measurement M14 (the bo_laksana strict count check, to confirm on real post-S-L1 L1 output); M9 states that 1,340 is a LOWER BOUND; the privilege recipe now includes migrations 1272/1273 (HELD executor, PR #3045) applied on the mirror before pass 1 (they are blockers B3/B4, not a deviation)."
  - "1.0 (2026-10-03): first version."
---

# S-L2 rehearsal plan (Linux, real orchestrator entrypoint, disposable database)

## 1. What a clean pass is, in one paragraph

A clean pass is ONE run of the real entrypoint (`python -m pipeline.orchestrator.main --run-id <id>`, the same command Cloud Run executes) over the 23 `bo_*` assets of the canonical chart, as the builder role, on linux/amd64 Python 3.11 with `SE_EPHE_PATH=/Users/Dev/suvarna-evidence/Se1` mounted (inside the container: the path the image uses), against a disposable PostgreSQL whose L1 content is S-L1's actual output and whose L2 content is the stored production L2 rows (so the generation opens against genuine completed L1 heads and the replace is a real replace), with NO shim: no stubbed gate, no hand-inserted registry row, no forged head or receipt, no edited migration, no skipped check. Every asset ends `lit`, the data-plane records (generation, partition, receipt, head) are written by the real producer path, and every acceptance check A2-xx of the runbook reads its expected value. Anything less is "not a clean pass" and is reported as such with its deviations (the S-L1 rehearsal's own verdict was "NOT a clean pass" for four named deviations; this plan exists to avoid repeating them, section 9).

## 2. Why this rehearsal is different from S-L1's

1. The L2 contract opens a generation only against COMPLETED L1 (and completed upstream L2) generation heads (`bodha_writers/data_plane_contracts.py` `_resolve_upstream_context`; migration 1036). A rehearsal database without real L1 heads cannot run a single `bo_*` asset, and heads cannot be forged without being a shim. The heads come from a real producer run (section 4) or from an owner-path restore of S-L1's actual production output.
2. Every `bo_*` adapter is wrapped by `@l2_producer`; on the real path `ctx.config['chart_id']` is a `uuid.UUID`. PR #3008 normalises it in the wrapper. The rehearsal must therefore run the real entrypoint (not a hand-built `ContextSpec` with a str chart_id), so the UUID reaches every wrapper exactly as in production (section 6).
3. The stored L2 rows cite OLD fact ids (71,401 of 73,049 MSR constituent cites orphaned after S-L1, per S_L1_BETWEEN_STATE section 3). The rehearsal's second pass replaces exactly those rows: it is the only place the replace-with-new-ids behaviour, the MSR delete guard and the 1,340 stranded vargottama signal ids can be observed before production.
4. S-L2 touches no L1 row. The rehearsal proves that with the flip detector's L1 comparison (hook `s_l2_l1_untouched`).

## 3. Environment (fixed in advance, recorded in the report)

| item | value | note |
|---|---|---|
| host / image | linux/amd64, Python 3.11 (`se-ci311v`, 3.11.16) or a `Dockerfile.pipeline` build (3.11.17); record which | S-L1: equivalent on the numeric path (IMAGE_GAP.md). L2 has no ephemeris math, but `SE_EPHE_PATH` is set |
| ephemeris | `SE_EPHE_PATH` = the pinned `.se1` directory (host: `/Users/Dev/suvarna-evidence/Se1`) | never unset |
| database | disposable PostgreSQL **15** (production is 15.18; pgvector image), started and removed by the operator by its exact container name or recorded PID, data directory deleted at the end | never the production proxy; the reader proxy on 127.0.0.1:5433 is read-only and used only to READ schema, ACLs and reference rows |
| **privileges: production-mirrored, NO superuser at run time (SS ruling 2026-10-03)** | the pipeline session is `data_plane_builder` (LOGIN, NOINHERIT, not super, no CREATE on schema public, no role config). The migration role `amjis_app` holds USAGE but NOT CREATE on schema `public`. Schema `public` is owned by `data_plane_schema_owner`; the protected L1 tables by `data_plane_l1_owner`, the 29 L2 active tables and the L2 history tables by `data_plane_l2_owner`; `data_plane_migrator` is a member of the three owner roles; ACLs of every protected table and function equal production's. The superuser exists ONLY for the one-time bootstrap (roles, extensions, the dump load, fixture rows) and is never the run session | verified by comparing, through the reader, `pg_namespace.nspacl`, `pg_class.relowner/relacl` of the 41 protected tables and `pg_proc.proacl` of the data-plane functions with the disposable database (R5); a mismatch is "not clean" |
| roles | the production role set with production attributes (read from `pg_roles`): `amjis_app`, `data_plane_{builder,migrator,verifier,l1_owner,l2_owner,schema_owner}`, `role_orchestrator`, `role_web_serve`, `role_jobs`, `role_ledger_write`, `role_sidecar`, `utkarsha_builder`, `nirmana_*`, `purna_inquiry_owner`, `suvarna_reader`, `retrieval_census_ro`; Cloud SQL administrative roles as NOLOGIN stubs | script: `platform/python-sidecar/tests/l2/realpg/00_bootstrap_roles.sql` |
| migrations | the repository's migration history cannot be replayed from an empty database (it assumes a legacy base schema: the first run failed at `002_ganita_divisionals` with `relation public.charts does not exist`), so the schema is the production schema as dumped through the reader; every migration that production does NOT yet have (SS's B3/B4/B5/B7/B8 changes, 1219, 1222, the TI-L2 batch, 1226 if authorised) is applied as its REAL file, in order, by the roles that will apply it in production | record each file's sha256 and compare with the file production will apply |
| code | the exact git SHA that production will run for S-L2 (writers, wrapper including #3008 and #3029, registry seed), recorded; the L2 fix batch is IN or OUT as SS decides and the rehearsal runs the same set | a rehearsal of different code is not a rehearsal |
| watchdog | not applicable on the disposable database | N-93 applies to the production window only (runbook section 8); the rehearsal measures the margins (M2) |
| operator | a builder-role session; the superuser only as above | S-L1: "as the builder role" |

## 4. Database construction (no shims)

The recipe was exercised in this lane (evidence `/Users/Dev/suvarna-evidence/S_L2/realpg/`; scripts and README in PR #3008 under `platform/python-sidecar/tests/l2/realpg/`); it produced a database on which the wrapper reached the first statement of an adapter body as `data_plane_builder`. Steps:

R0. Start the container; as the superuser run `00_bootstrap_roles.sql` (roles with production attributes; extensions `pgcrypto`, `uuid-ossp`, `vector`, `pg_trgm` in schema `public` as in production; schema `public` temporarily owned by `amjis_app` for the dump load).
R1. Stubs for the tables a reader cannot dump (`01_stubs_pre_dump.sql`: `charts`, `chart_grants` and the FK targets). Their production ACLs are read from `pg_class.relacl` through the reader and replayed. **Deviation to record:** the stubs are not the production DDL; `charts` mirrors `platform/migrations/001_baseline.sql` plus the columns `fetch_birth_params` reads.
R2. `pg_dump -s -n public` through the reader, excluding every table the reader cannot SELECT (89 tables; pg_dump takes ACCESS SHARE locks), load as superuser. This carries the production owners, ACLs, functions, triggers, the 29 L2 active tables and the 12 L1 protected tables. The data-plane history tables the reader cannot dump (22 relations: `l1_data_plane_*`, `l2_data_plane_*`, `data_plane_l2_producer_generations`) are created from the verbatim statements of migrations 1035/1036 by `extract_history_ddl.py`, with the migrations' own GRANT/REVOKE statements.
R3. Role memberships and the preflight grants (migrator in the three owner roles; owners SELECT on `charts`); reference rows copied through the reader (`asset_registry`, `l2_data_plane_asset_outputs`, `fact_category_ownership` or its 1219 equivalent: **without 1219 the L1 guard refuses `ga_positions` categories, `cannot mutate chart_facts category`; the S-L1 rehearsal DB must carry 1219**).
R4. L1 content, one of two variants (SS chooses; variant A is the pass of record once S-L1 has closed):
- **Variant A (after S-L1 close, preferred).** Restore S-L1's actual production output for the canonical chart (L1 tables, L1 generation/partition/head records, `asset_provenance_receipts` for the 18 `ga_*` assets) through the owner path the S-L1 rehearsal used; the reader cannot export tables it cannot SELECT (all L1 history tables), so for those the restore needs a privileged export; a table that cannot be restored makes the rehearsal NOT RUN for it, never simulated.
- **Variant B (before S-L1 close, finds defects early; does not satisfy the day-7 checkpoint).** Build L1 on the disposable database by running the real S-L1 chain (18 `ga_*` lanes, one orchestrator run, 567 s in the S-L1 rehearsal) from the S-L1 integration head, so the heads and receipts are produced by the real producer; the L1 data plane writes the heads when each writer's last partition completes (1035:1305-1515).
R5. Stored production L2 rows (pass 2 only): the canonical chart's rows of every table in `l2_data_plane_asset_outputs` (reader `\copy` where SELECT is granted; the 12 L1 protected tables, `charts` and the history tables are not readable). Snapshot row counts and the privilege comparison of section 3 BEFORE pass 1; verify the L1 head and generation rows exist for the 12 closure assets (G-3).
R6. **Prerequisite: the real B3/B4/B5 changes.** Until SS's migrations exist as files, the only possible run is an EXPERIMENT (patches applied in the disposable database only, labelled as such: `bind_patched_EXPERIMENT.sql`, `20_EXPERIMENT_grants.sql`); an experiment can find defects but is never a clean pass. **B3 and B4 now exist as the HELD owner-path executor of PR #3045 (migration numbers 1272/1273):** the clean pass applies them to the mirror THROUGH THE EXECUTOR (dry run, apply, with the non-superuser administrator and the production owners; the executor's own mirror tests and rollback proof are in that PR) before pass 1, never by hand. B5 (`chart_fact_identity`, migration 1262) is still a prerequisite that must exist as a file (or be applied through its own executor) before a clean pass.

## 5. The passes

| pass | database state at start | what it proves | expected |
|---|---|---|---|
| P1 fresh | L1 present, NO L2 rows and no L2 generation records for the chart | all 23 assets run in DAG order from nothing; the generation open against real L1 heads works; every wrapper converts the UUID | all 23 `lit`, 9 waves in order, partitions: 1 per light asset, 5 per heavy asset (`bo_laksana`, `bo_samskara`: one per ayanamsha) |
| P2 over stored L2 | L1 + the restored stored production L2 rows (old cites) + their data-plane records | the replace: delete-then-insert per chart (N.3), MSR delete guard (`assert_l2_msr_delete_safe`), cross-layer dependents (FK children of the MSR rows), correction/replay semantics against an existing head, the id moves | all 23 `lit`; orphans 0; the id-move counts of the hooks; a new generation per asset with the previous as `previous_generation_id` |
| P3 second rebuild | the end state of P2 | determinism/idempotency: a second rebuild reproduces the same row identities and semantic digests (the replay rule of the data plane: identical output). Skipped only if the production plan says L2 is built once; the S-L1 rehearsal did the same (T6 "re-running gives identical ids") | per-asset `semantic_output_digest` equal to P2's; row counts equal; `signal_id` sets equal |

P1 and P2 are independent databases (restore P2 from the R4 snapshot; do not run P2 on P1's output). Each pass is ONE `--run-id` run of the whole plan, retries only as the orchestrator itself does them.

## 6. Every `bo_*` adapter is driven by the real wrapper with a real `uuid.UUID`

This is satisfied by the entrypoint itself (`runner.load_run` reads `build_runs.chart_id` through `dict_row`, a `uuid.UUID`; `asset_runner._run_data_writer` puts it into `ctx.config` unconverted; the `@l2_producer` wrapper converts it). The rehearsal report must show, per asset, evidence that the wrapper ran and the asset reached its own body: the `l2_generation=... partition=... temporal=UNAVAILABLE_AT_L2` suffix in `WriterResult.notes` (appended by the wrapper after the body returns; its presence for all 23 assets is the proof) and the generation row in `data_plane_l2_producer_generations`. In addition, before P1, run the unit regression `platform/python-sidecar/tests/l2/test_l2_uuid_chart_id_real_path.py` (PR #3008) on the same Linux image (53 cases: all 23 adapters, real UUID, direct and through `_run_data_writer`). A rehearsal that constructs its own `ContextSpec` with a str chart_id does not satisfy this section.

## 7. Measurements (all recorded, none optional)

| id | what | how | why |
|---|---|---|---|
| M1 | per-asset wall clock, rows inserted/updated/skipped, per-substep wall clock for `bo_laksana` (5) and `bo_samskara` (5) | orchestrator rows (`asset_throughput`, `build_run_assets`) and the job log | window length; the S-L1 report's T9 equivalent |
| M2 | longest watchdog-visible silent interval per asset (time between `asset_throughput.last_built_at` heartbeats; light writers heartbeat once at the end) | engine events / `last_built_at` samples every 5 s | the production watchdog (`watchdog-reaper`) reaps a run with no heartbeat; N-93 paused it for S-L1 and item 11 allows reuse for later S-stage windows; M2 decides whether S-L2 needs the same pause. S-L1 measured 61-64 s for `ga_structural`; `bo_laksana` owns 50,529 MSR rows per chart |
| M3 | the exact set and order of waves actually run, and every asset's `depends_on` as read at run time | `build_run_assets` ordering | the runbook's wave table (9 waves) must equal the observed order |
| M4 | the data-plane record per asset: generation id, state, partitions expected/complete, head promoted, `semantic_output_digest`, `correction_of_generation_id` | SELECT on the L2 data-plane tables | acceptance A2-01..A2-05 |
| M5 | production-scale margin: the rehearsal chart is the canonical chart's own row volume (variant A) so M1/M2 ARE production-scale; with variant B they are also production-scale for L2 (stored rows restored). State plainly if the disposable instance is smaller than production | machine spec recorded | S-L1's rehearsal could NOT show production-scale margin (ga_structural 34 s here vs 658-1,323 s in production); do not repeat the claim |
| M6 | MSR / embeddings / nodes / edges counts after P2 and the hook derivations (A2-10..A2-24) | the runbook's SQL | proves the counts are rule-derived |
| M7 | the L1 flip-detector compare, before vs after P2 | `flip_detector.py --compare` with `--hooks-dir .../s_l2_attribution_hooks` (lane `s_l2_l1_untouched`) | S-L2 changes no L1 row; verdict NOT_CHECKED (standing registry), failure classes all 0 |
| M8 | the disclosure detector's verdict before and after (the served `l2_receipts_predate_l1` computation: L2 receipts older than L1 receipts for the chart) evaluated by the same SQL the served detector uses, against the disposable DB | the receipt comparison from L2_DATAPLANE_MECHANICS section 5 | clearing criterion "the detector reads 0 stale" (runbook section 10) |
| M9 | stored vs new `signal_id`: the 1,340 chart_divisionals-embedding signals (the certain part) AND the total number of signals whose id moved, against the prediction rule of runbook section 9 item 3 | the A2-14 query | the I-20 move, observed not assumed; 1,340 is a LOWER BOUND |
| M10 | logs: no `ContractError`, no `TypeError`, no "not JSON serializable"; warnings listed | job log grep | the PR #3008 class of defects |
| M11 | **an integrity check that can go red:** after pass 2, for ONE light asset corrupt its output inside a rolled-back transaction (e.g. set a value outside the check's allowed set through the builder session within an admitted generation, or run the check against a copy) and show that the asset's registry `integrity_check_sql` evaluated by the orchestrator's own `_probe_asset` turns false; repeat for a heavy asset's last-substep check | a deliberately wrong row + the probe | B6: a detector that has never been shown to fail is not a detector (CLAUDE.md N.8) |
| M12 | the stop conditions fire: for each of `missing completed selected L2 dependencies` (run a dependent before its upstream), `reported N inserts + M updates but protected capture contains K rows` (a writer that miscounts) and `replay changed output` (a second run with changed input) show the failure text and that the asset is `error`, not `lit` | three controlled failures on the disposable DB | runbook W2 stop list |
| M13 | first heartbeat: for every light asset record `asset_throughput.last_built_at` at the start stamp and at completion, and the longest transaction age seen by `pg_stat_activity` | sampled every 5 s | B10 |
| M14 | **B7: the `bo_laksana` strict count check** (`inserted != len(signal_rows)` raises "refusing a partial root generation"): on real post-S-L1 L1 output record, per ayanamsha substep, the number of signal rows built, the number inserted, the number skipped by `ON CONFLICT ... DO NOTHING`, and whether the check raised; if it raises, record the colliding `(signal_type_id, configuration_jsonb)` groups by category | the job log of `bo_laksana` and a rolled-back count of the colliding groups | B7 is inferred from code and counts, never executed; the three remedies (dedupe before the check, discriminator in the configuration, relax the check) move signal ids and counts, so the decision (runbook G-5) needs this measurement |

## 8. Pass criteria (what the final clean pass must show)

All of the following, in the final pass of record (variant A, after S-L1 close; or variant B if SS accepts it for the day-7 checkpoint with the difference stated):

1. P1: 23 of 23 assets `lit`; no asset errored, retried by hand, or skipped; wave order equal to M3's table.
2. P2: 23 of 23 `lit`; every acceptance check A2-01 to A2-30 of the runbook reads its expected value (the runbook table gives the SQL, the expected value and its derivation); zero orphan constituent cites in every L2 table that carries them.
3. P3 (or the P2 re-run): identical semantic digests and identical `signal_id` sets.
4. M7: the L1 compare reports all failure classes 0 (verdict NOT_CHECKED, never FAIL).
5. M8: the detector computation reads zero stale L2 generations after P2 and at least one stale generation per `bo_*` asset before P2 (otherwise the detector was never shown to be able to read stale).
6. M2: the longest silent interval per asset is recorded, and the runbook's pause decision (pause `watchdog-reaper` or not) is justified by it against the watchdog thresholds (L2_DATAPLANE_MECHANICS section 6), not by feeling.
7. Section 6 evidence for all 23 assets.
8. M11 and M12 each show the failure they are meant to show (a check that cannot fail is a finding, not a pass).
9. The report lists every deviation from section 3 or 4, even harmless ones, with a verdict "clean / clean with deviations / not clean". A deviation from the list in section 9 (or an applied experiment patch) is "not clean".

## 9. Deviations to avoid (from the S-L1 rehearsal's "Problems" and "Deviations")

| S-L1 deviation | S-L2 rule |
|---|---|
| a writer registered in Python with no `asset_registry` row failed the writer-gap preflight; the run needed the registry row inserted | rows come from the migrations/seed; the preflight passes with the variable UNSET. All 23 `bo_*` rows exist in production today (`has_writer=true`); check that any lane head adds none unregistered |
| a writer fix from an unmerged PR copied into a copy of the tree | the rehearsal tree is the exact production SHA; no copied files |
| `str(chart_id)` shim in two L1 adapters | none: PR #3008 is in the tree. A shim at the adapter level is "not clean" |
| (new) a superuser or owner session used to run the assets, or a GRANT applied by hand to make an asset run | not clean. The rehearsal runs as `data_plane_builder` only; any missing privilege is a finding for SS (B3/B4/B5), applied only as a real migration file |
| (new) stub tables for the undumpable base tables (`charts` ...) | allowed only because the reader cannot dump them; recorded as a deviation with the reason; the rehearsal never claims their DDL is production's |
| the D6 executor deploy-gate mirror stubbed and the writer-first check skipped because the disposable DB had no L2 attestation tables | the real attestation tables exist (R0); nothing stubbed. If a D6 plan rides S-L2 (TI-L2-01 reader grant), its executor runs for real with its real gate |
| canonical chart id used inside the disposable DB because a writer's non-vacuity conjunct is a canonical-id literal | the canonical chart id is the disposable chart id (it is the chart being rebuilt); this is not a deviation. A synthetic chart is NOT used |
| six W1 migrations taken as real SQL from held lane heads | allowed only for migrations that will be applied in production before S-L2 (record the hash; compare it to the file production applies) |
| "production-scale margin NOT demonstrated" | state it per measurement (M5) |
| image 3.11.16 vs the Dockerfile build 3.11.17 | record; acceptable only with the S-L1 IMAGE_GAP argument repeated for L2 (no numeric path) |

Additional S-L2 hazards, each a "not clean" if it occurs: any bypass of `l2_data_plane_mutation_guard` (superuser writes to L2 tables are a bypass); an L2 table written by a role other than the builder session; a generation or head created outside the wrapper; running P2 on P1's end state; a run whose assets were started by hand outside the orchestrator.

## 10. Evidence layout and handling

`/Users/Dev/suvarna-evidence/S_L2/rehearsal/<UTC date>/`: run ledger (commands, SHAs, image digest, PIDs/containers started), the three pass logs, M1..M10 outputs, the flip-detector JSON reports, the acceptance results with expected vs actual, and `REHEARSAL_REPORT.md` (read-only after writing). Processes and containers are stopped only by the exact name or PID recorded when they were started; the disposable data directory is deleted at the end. No `/tmp` for reports.

## 11. What I could not settle (for SS)

0. The privileged export path for the L1 history tables and the L1 protected tables (R4/R5): the reader cannot read them.

1. Which restore path (the owner-path "stored production rows" restore of the S-L1 rehearsal) is available for L2 tables and the L2 data-plane records, and which L2 tables the reader role cannot read (the reader lacks SELECT on some `bodha_*` tables, TI-L2-01). Without a restore for a table, P2 for it is NOT RUN.
2. Whether the L2 fix batch (TI-L2 D items 25-43, "the ONE rebuild", N-59) is in the S-L2 code. The hook derivations in `s_l2_attribution_hooks/l2/` are for main's CURRENT writers; if the batch is in, the affected entries are re-derived (list in the hooks record).
3. Whether the held edges migration (TI-L2-05, `bo_laksana -> ga_yoga`, `bo_upaya -> bo_bimba`) is applied before S-L2: it changes the wave table only in that `bo_laksana` additionally waits for `ga_yoga` (already built in S-L1) and `bo_upaya` for `bo_bimba` (already wave 1; `bo_upaya` is wave 5).
4. Variant A vs B for the day-7 checkpoint.
