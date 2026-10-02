---
artifact: L1_MV_REFRESH_AFTER_REBUILD
version: 1.1
status: DRAFT_FOR_REVIEW
date: 2026-10-02
lane: suvarna/land/TI-l1-min-fixes-001
decision: SS minimum S-L1 fix set (b): skip the in-writer MV refresh when the writer does not own the view; refresh afterwards as the owner
changelog:
  - "1.1 (2026-10-02): SS decision: W7 records the view as knowingly stale (counts before); the refresh is migration 1256 (ordinary guarded migration as amjis_app), first post-window PR; owner-path executor route withdrawn."
  - "1.0 (2026-10-02): view inventory (live catalog, read as suvarna_reader), what the S-L1 path refreshes, what a stale view affects, the W7 runbook step, the statements, the verification SQL."
---

# W7: refresh the L1 materialized views after an S-L1 rebuild, as their owner

## 1. Why this step exists

The S-L1 job (Cloud Run job `brahma-build-pipeline-job`) runs as `data_plane_builder`. Every materialized view the L1 writers try to refresh is owned by `amjis_app`, and `data_plane_builder` is **not** a member of `amjis_app` (live: `pg_has_role('data_plane_builder','amjis_app','USAGE')` = false; no `pg_auth_members` row for either role). `REFRESH MATERIALIZED VIEW` needs ownership, so any refresh issued from the build job fails with "must be owner of materialized view". The writers swallowed that failure and left the orchestrator's shared transaction **aborted**, which deterministically failed the build.

Fix (this PR): `ga_sade_sati_writer._refresh_mv` now asks the catalog (`pg_has_role(<view's relowner>, 'USAGE')` for `current_user`) and **skips** the refresh, logging at INFO, when the connection does not own the view. The universal guard in `ga_writers/data_plane_runtime.py` turns any remaining swallowed DB error into a named `ContractError`. The consequence of the skip is that `mv_chart_sade_sati_lifetime_summary` is **stale after the rebuild** until its owner refreshes it. That refresh is step W7 below.

## 2. Every materialized view an L1 writer or `build_runner.py` tries to refresh

Measured read-only as `suvarna_reader` (`pg_matviews`, `pg_index`, `pg_depend`, `pg_has_role`), 2026-10-02, production catalog. "S-L1 path" = reached by the orchestrator (`python -m pipeline.orchestrator.main`, the `Dockerfile.pipeline` entrypoint) through the `pipeline/orchestrator/writers/ga_*.py` adapters.

| # | View | Attempted at (file:line) | On the S-L1 path? | Owner (live) | `data_plane_builder` a member of owner? | Unique index (CONCURRENTLY legal?) | Treatment in this PR |
|---|---|---|---|---|---|---|---|
| 1 | `mv_chart_sade_sati_lifetime_summary` | `ga_writers/ga_sade_sati_writer.py` `_refresh_mv` (def `:1935`; pre-fix `:1882`), called unconditionally from `build_ga_sade_sati` (`:2226`; pre-fix `:2147`) on `ctx.db_conn` | **YES** (`ga_sade_sati` adapter passes `conn=ctx.db_conn`) | `amjis_app` | no | yes (`mv_sade_sati_summary_idx`) | **skip when not owner** (INFO), returns `skipped_not_owner`; owner connection still refreshes |
| 2 | `mv_chart_sensitive_points_summary` | `ga_writers/ga_sensitive_writer.py:3018` `_refresh_mv`, called at `:3236` inside `build_ga_sensitive` | **NO.** The `ga_sensitive` adapter calls `build_ga_sensitive_for_ayanamsha` (per-ayanamsha substeps), which never refreshes. `build_ga_sensitive` is reached only from `build_runner.py:225` (row 3). | `amjis_app` | no | yes (`idx_mv_sensitive_points_unique`) | untouched (not on the path). Same latent defect if ever called with `ctx.db_conn` as a non-owner: **finding, not fixed** |
| 3a | `mv_chart_planet_summary` | `ga_writers/build_runner.py:73/84`, `MATERIALIZED_VIEWS` list `:51-61`, `refresh_materialized_views` (def `:64`), called `:289` | **NO.** `build_runner.py` is the legacy CLI path (`scripts/run_l1_ganita_build.py`), not in any Docker entrypoint, and not part of the frozen orchestrator contract (`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md` does not mention it). It opens its own `_conn()` and rolls back on each failure, so it never aborts a shared transaction. | `amjis_app` | no | yes (`mv_chart_planet_summary_idx`) | untouched, listed |
| 3b | `mv_chart_shadbala_summary` | same, `:53` | NO | `amjis_app` | no | yes (`..._shadbala_summary_idx`) | untouched, listed |
| 3c | `mv_chart_ashtakavarga_summary` | same, `:54` | NO | `amjis_app` | no | yes | untouched, listed |
| 3d | `mv_chart_bhava_bala_summary` | same, `:55` | NO | `amjis_app` | no | yes | untouched, listed |
| 3e | `mv_cross_ayanamsha_consensus` | same, `:56` | NO | `amjis_app` | no | **NO unique index** (only `mv_cross_ayanamsha_consensus_chart_idx`, non-unique): `CONCURRENTLY` is illegal, use the plain statement | untouched, listed |
| 3f | `mv_chart_panchanga_birth_summary` | same, `:57` | NO | `amjis_app` | no | yes (`..._pk`) | untouched, listed |
| 3g | (= row 2) `mv_chart_sensitive_points_summary` | same, `:58` | NO | `amjis_app` | no | yes | untouched, listed |
| 3h | `mv_chart_vargas_summary` | same, `:60` | NO | `amjis_app` | no | yes (`mv_chart_vargas_summary_idx`) | untouched, listed |
| 4 | `mv_sensitive_points_cross_ayanamsha` (dependent of row 2) | **no writer, runner or script refreshes it anywhere** | n/a | `amjis_app` | no | **NO unique index** (`idx_mv_spca_divergence` non-unique) | listed for W7 only: it reads `mv_chart_sensitive_points_summary`, so it must be refreshed AFTER it |
| (out of L1) | `bo_pramana_mapa._refresh_mv` (L2 writer, `pipeline/orchestrator/writers/bo_pramana_mapa.py:112`) | L2, not an L1 writer | n/a | n/a | n/a | n/a | out of scope; same swallow pattern (it logs and continues, it does not catch-and-leave-aborted differently), noted only |

Other `mv_chart_*` views that are chart_facts/chart_divisionals aggregates and that NO writer, runner or script refreshes at all (`mv_chart_aspect_matrix`, `mv_chart_super_vargottama_bodies`, `mv_chart_t1_composite_strengths`, `mv_chart_yogas_fired_summary`) are out of scope here; they are already refreshed by no code path, S-L1 or otherwise.

Dependents and readers (git grep of `platform/src`, `platform-mcp/src`, `platform/python-sidecar`, `platform/scripts`; `pg_depend` and `pg_proc.prosrc` in the live catalog): **no served or planning reader reads any of rows 1-3 or 4 by name.** The retrieval layer reads `chart_facts` directly. The only references are: the writers' own REFRESH, `build_runner.py`, `platform/scripts/governance/drift_detector.py:941-948,1049-1056` (existence checks), one comment in `get_dasha_lord_capability.ts:21`, and one live dependent object, `mv_sensitive_points_cross_ayanamsha` (row 4, itself unread). So a stale view today affects only ad-hoc SQL and the drift detector's presence check, not a served answer. `suvarna_reader` holds no SELECT on these views (verified: `information_schema.role_table_grants` empty), so row counts below must be read as the owner.

## 3. The runbook step (SS decision 2026-10-02: no owner-path executor; migration 1256, post-window)

> **W7: record `mv_chart_sade_sati_lifetime_summary` as KNOWINGLY STALE after the S-L1 rebuild, with its row counts BEFORE (section 5, read as the owner or any role with SELECT; `suvarna_reader` has none). Do not refresh it in the window. The post-window check records the counts AFTER. Migration 1256 is the first post-window PR and does the refresh.**

**Migration 1256 (NOT written in this PR; do not write it now).** An ordinary guarded migration run by `migrate` as `amjis_app` (the view's owner), idempotent, `lock_timeout` set first:

```sql
SET LOCAL lock_timeout = '10s';
REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_chart_sade_sati_lifetime_summary;  -- unique index mv_sade_sati_summary_idx exists
```

Views WITHOUT a unique index use the plain statement (`mv_cross_ayanamsha_consensus`, `mv_sensitive_points_cross_ayanamsha`); `CONCURRENTLY` runs inside a transaction block (proven on a disposable Postgres 15 in this PR's tests). Only row 1 is attempted (and now skipped) on the S-L1 path. Rows 2, 3a-3h and 4 are not refreshed by the S-L1 job at all, before or after this PR, so they go stale after any rebuild regardless; whether 1256 also covers them is SS's call (a refresh touches no table data and changes no stored `chart_facts` value: it recomputes a derived view from rows the build already committed). Order if several: parents before dependents (`mv_chart_sensitive_points_summary` before `mv_sensitive_points_cross_ayanamsha`).

Superseded draft (kept for the record, not to be run): an owner-path executor route (`SET LOCAL ROLE amjis_app` through the D6 in-process pattern of `reader_grants.py` with SS's `APPROVED <plan hash>`). SS replaced it with migration 1256.

## 4. Locking and failure behaviour

`REFRESH ... CONCURRENTLY` needs a unique index and does not block `SELECT` on the view; the plain statement (rows 3e and 4) takes `ACCESS EXCLUSIVE` for the duration. With no served reader of any of these views, the plain refresh blocks nothing in production serving. If a refresh fails, the migration transaction rolls back and the view simply stays stale; it is safe to re-run.

## 5. Verification (read-only SQL; run as the owner or any role with SELECT on the views; `suvarna_reader` has none)

The views carry no `computed_at` except `mv_chart_panchanga_birth_summary` and `mv_chart_vargas_summary`, so use row counts and build coverage, plus a definition-exact freshness diff.

Before W7 (recorded as the knowingly-stale baseline) and after 1256 (post-window check), per view:

```sql
SELECT 'mv_chart_sade_sati_lifetime_summary' AS mv, count(*) AS n_rows,
       count(DISTINCT chart_id) AS n_charts, count(DISTINCT build_id) AS n_builds
FROM public.mv_chart_sade_sati_lifetime_summary;
-- the two views that carry computed_at:
SELECT 'mv_chart_panchanga_birth_summary', count(*), max(computed_at) FROM public.mv_chart_panchanga_birth_summary;
SELECT 'mv_chart_vargas_summary',          count(*), max(computed_at) FROM public.mv_chart_vargas_summary;
```

Expected movement for a rebuilt chart: `n_builds` and the set of `build_id` change to the new `build_id` (the views group by `build_id`), and `n_rows` equals the rebuilt count. Sade Sati specifically, build coverage (both result sets must be empty after W7):

```sql
SELECT DISTINCT chart_id, build_id FROM public.mv_chart_sade_sati_lifetime_summary
EXCEPT SELECT DISTINCT chart_id, build_id FROM public.chart_facts WHERE fact_category = 'sade_sati_cycle';   -- stale builds still in the view
SELECT DISTINCT chart_id, build_id FROM public.chart_facts WHERE fact_category = 'sade_sati_cycle'
EXCEPT SELECT DISTINCT chart_id, build_id FROM public.mv_chart_sade_sati_lifetime_summary;                  -- builds missing from the view
```

Definition-exact freshness for any view (0 differing rows = fresh; tested on a disposable Postgres 15 in this lane: 1 differing row while stale, 0 after refresh):

```sql
SELECT format('SELECT %L AS mv, count(*) AS differing_rows FROM ((TABLE %s EXCEPT %s) UNION ALL (%s EXCEPT TABLE %s)) d',
              mv, mv, rtrim(pg_get_viewdef(mv::regclass), ';'), rtrim(pg_get_viewdef(mv::regclass), ';'), mv)
FROM (VALUES ('public.mv_chart_sade_sati_lifetime_summary'),
             ('public.mv_chart_sensitive_points_summary'),
             ('public.mv_sensitive_points_cross_ayanamsha')) v(mv)
\gexec
```

Acceptance for the post-window check: `differing_rows = 0` for every view refreshed, and the `build_id` sets above empty. If the `\gexec` diff cannot compare a view (a column type without equality), fall back to the row-count and build-coverage reads.

## 6. What was and was not verified

Verified here: the live owner/index/dependency/membership facts in section 2 (read-only, as `suvarna_reader`); the non-owner skip, the owner refresh, the absent-view skip and the pre-fix abort on a disposable Postgres 15 with the production role structure (`amjis_app` owner, `data_plane_builder` LOGIN non-member); the `CONCURRENTLY`-in-a-transaction and `\gexec` freshness statements on the same disposable cluster.

Not verified: any production refresh (none was run: this lane takes no production action), migration 1256 itself (not written), `SELECT` access of any role to the views in production (only the absence of a `suvarna_reader` grant was read), and the view row counts (`reltuples` estimates only: sade_sati 60, sensitive_points 1515, planet 50, shadbala 42, ashtakavarga 520, bhava_bala 60, panchanga 386, vargas 1550, cross_ayanamsha 20043).
