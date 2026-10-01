---
artifact: CANONICAL_CHART_REBUILD_PLAN
version: "1.0"
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna
date: 2026-10-01
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
base_commit: origin/main 3311b0a06 (worktree opened at 0250cbade, fast-forwarded before commit)
execution: NONE. This is an analysis document. No build, write, admin action, push or PR was made to produce it.
db_access: read-only, as suvarna_reader (SELECT only). Evidence in /Users/Dev/suvarna-evidence/Rebuild/.
changelog:
  - "1.0 (2026-10-01): first draft for SS review. Includes the P0 builder-grant precondition and smoke build (coordinator addendum 2) and the I-1/I-2 consumer addendum (coordinator addendum 1)."
---

# Canonical-chart rebuild plan (REVIEW document for SS)

Scope asked by SS (2026-10-01): rebuild the stale and errored producers `ph_phaladesa`, `ph_pramana`, `mi_bhavisya`,
`ph_nimitta`, `bo_pratijna`, `ka_yojaka`, plus the I-1/I-2 consumers `ka_avadhi` and `ka_vighnakara`, so that
(a) live rows are corrected once the L3 writer fixes merge and (b) migration 1211 (5 held `depends_on` edges, branch
TI-edges-002) can be applied after its gate (each of `bo_pratijna`, `ka_yojaka`, `mi_bhavisya`, `ph_nimitta` lit and
fresh and proven, "gate_ok").

Every number below was read from the live DB (query in the Evidence appendix) or from the repo at the cited file; estimates
are labelled "estimate". Code-derived predictions (never observed in production) are labelled "code-derived".

## P0. PRECONDITION 0: the builder audit grant is deployed AND one smoke build completes

No governed production build can complete today, and the wave must not start until this precondition is proven. SS added
this on 2026-10-01; Pravāha ships the grant migration, which this plan neither duplicates nor drafts.

### P0.1 What was inspected read-only (as `suvarna_reader`, 2026-10-01T15:04Z, Evidence E7)

| Fact | Observation |
|---|---|
| Last completed build | `build_runs`: 302 `completed`, last created 2026-09-12 01:44, ended 01:47 (single asset `bo_grounding`). 419 `failed`, the latest ended 2026-10-01 15:01 (run 8684032d, `ka_gochara_resonance`, `triggered_by l3-lane-frozen-manifest-rebuild`: the run started at 15:01:18.4 and ended at 15:01:19, one second later, with its one asset still `queued` and `last_error` NULL; this is consistent with the first `asset_throughput` state write being refused, but the cause is not recorded). The earlier 2026-09-19 run 59232059 failed `orphan-watchdog: run never dispatched`. |
| Last audited state change | `asset_throughput_state_audit`: 695 rows, ALL with `db_user = amjis_app`, latest 2026-09-12 01:44; none since. No row has ever been written by `data_plane_builder`. |
| The trigger | `trg_asset_throughput_state_audit` AFTER UPDATE OF state ON `asset_throughput` (enabled, `O`), function `_record_asset_throughput_state_change()`, owner `amjis_app`, **`prosecdef = false`** (not SECURITY DEFINER). Defined by migration 586 (F-152), applied 2026-08-22. No migration numbered 1461 exists in the repo or in `_migrations_applied` (max id 904), so "#1461" is read here as this trigger. |
| Audit-table ACL | `asset_throughput_state_audit` `relacl` = `{amjis_app=arwdDxt, retrieval_census_ro=r, suvarna_reader=r}`; `asset_throughput_state_audit_id_seq` `relacl` = `{amjis_app=rwU}`. `has_table_privilege('data_plane_builder', audit, 'INSERT')` = **false**; `has_sequence_privilege('data_plane_builder', audit_id_seq, 'USAGE')` = **false**. `asset_throughput` itself: `data_plane_builder=arwd` (UPDATE allowed, so the trigger fires and its INSERT is then refused). |
| Who the job runs as | Migration 1070's header states `data_plane_builder` is the dedicated identity of `brahma-build-pipeline-job` since the 2026-09-18 data-plane cutover and that every run failed after it for lack of orchestrator grants; 1070 restored the core grants (`asset_registry` SELECT + 3 probe columns, `asset_provenance_receipts`, `asset_freshness`, `charts`, `asset_output_digest_specs`). **Not visible to the reader:** the job's live runtime DB identity (a secret/Cloud Run setting) and `data_plane_l2_producer_generations` writes (`data_plane_builder` has SELECT only on it; whether L2 writers insert through a SECURITY DEFINER function was not inspected). |

### P0.2 A second, separate gap: the Phala and Mimāṃsā tables (`has_table_privilege`, Evidence E7)

`data_plane_builder` has **no privilege of any kind (SELECT, INSERT, UPDATE, DELETE all false)** on the 8 `phala_*` target
tables (`phala_anchors`, `phala_muhurta`, `phala_mitigation`, `phala_sankrama`, `phala_sodhana`, `phala_suddha_sodhana`,
`phala_pramana`, `phala_phaladesa`) or on `mimamsa_predictions` and `mimamsa_manifestation_sets`. Migration 1070 recorded this
("mimamsa_*/phala_* (0/37 and 0/20 accessible) ... recorded for their owners") and nothing has since granted it. It means that
even after the audit grant lands, waves 7-12 (9 assets: `ph_nimitta` ... `mi_bhavisya`, which carry four of SS's named
assets) cannot write. It is outside "the audit grant" and is a second precondition (P0.5 check 2, Q9). The Bodha and Kāla
target tables, `bg_transit_*` and the orchestrator metadata tables are granted (matrix in Evidence E7; `kala_*` tables with
identity sequences have `USAGE`).

### P0.3 The check (read-only, run by anyone with the reader; this is the verification method)

```sql
-- Check 1: audit grant (PASS if (a) AND (b), or if (c) is true)
SELECT has_table_privilege   ('data_plane_builder','public.asset_throughput_state_audit','INSERT')         AS a_insert,
       has_sequence_privilege('data_plane_builder','public.asset_throughput_state_audit_id_seq','USAGE')   AS b_seq_usage,
       (SELECT prosecdef FROM pg_proc WHERE proname='_record_asset_throughput_state_change')               AS c_trigger_fn_secdef;
-- Check 2: target-table grants for the wave (PASS if every row is true for i,d on the writer's table)
--   re-run the matrix query in Evidence E7 (privs.sql); today the 10 phala_/mimamsa_ rows are all false.
-- Check 3: no active run on the chart
SELECT id, state FROM build_runs WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa' AND state IN ('planned','running','paused');
```

What this check cannot prove: that the job actually connects as `data_plane_builder` today, and that a SECURITY DEFINER
fix (if Pravāha chooses that form) is complete. Only the smoke build (P0.4) proves the end-to-end path.

### P0.4 The smoke build

- **Asset: `ka_tithi_pravesha`** (L3, per-chart, a leaf: nothing depends on it, so no downstream asset can be marked stale).
  Rationale (read-only): 120 canonical rows (`kala_tithi_pravesha`), `asset_throughput` lit (2026-09-07), freshness `fresh`,
  receipt `proven` (output digest prefix `801e0b279283`), one dependency `ga_positions` (lit, latest receipt proven),
  `writer_timeout_seconds` 120, history of 0.0 to 1.8 s per execution (`build_run_assets`), integrity SQL present, and
  `data_plane_builder` holds SELECT/INSERT/DELETE on its table.
- **Why not a service probe:** `bg_panchanga` (a cockpit-dispatchable service probe) is the obvious tiny asset, but a probe
  completion records no `output_changed`, so `staleness.propagate_downstream_staleness` fails open and would mark the 57
  assets downstream of `bg_panchanga` stale for the run's chart (code-derived: `asset_runner.py` sets `output_changed` only on the
  data-writer and delta-skip paths; `runner.py on_complete` always calls the propagation). A leaf asset has no downstream.
- **Request (cockpit POST, owner or super_admin):** `{chart_id:'482012f1-710e-4a25-994a-93821f5871aa', scope:'asset_set',
  scope_target:'ka_tithi_pravesha', action:'rebuild'}`. No `clear_before`.
- **Expected behaviour (estimate):** delta-skip (`disposition = skip_no_delta`, no writer invocation, zero rows replaced):
  the stored receipt's upstream is exactly `ga_positions`' current proven receipt (observed 2026-09-07 08:37:20.895985Z), and the
  09-07 runs skipped the same way. If the writer's code digest has changed since 09-07 it executes instead: delete-then-insert of its
  own 120 chart rows (`DELETE FROM kala_tithi_pravesha WHERE chart_id`), expected identical content (the integrity SQL must be true).
  Either outcome passes; both write `asset_throughput` twice (lit -> building -> lit), which is exactly what the audit trigger needs.
- **Expected duration (estimate from history):** single-asset completed runs since 2026-09-01: median 25 s creation to end
  (min 6 s, max 1675 s, n=128), median 3 s start to end. Allow 5 minutes before calling it hung.
- **"Completes" means ALL of the following (SQL below; syntax tested against the failed run 8684032d, 15:15Z):**
  1. `build_runs.state = 'completed'` for the new run id, `ended_at` not null, `last_error` null.
  2. `build_run_assets.state = 'complete'` for `ka_tithi_pravesha` (disposition `skip_no_delta` or `build`).
  3. `asset_throughput_state_audit` has at least 2 new rows for (`ka_tithi_pravesha`, canonical chart) with `changed_at` >= the run's
     `started_at`, `old_state/new_state` = lit/building and building/lit, and `db_user = 'data_plane_builder'` (this is the proof of
     which identity ran it); zero new audit rows for any other asset.
  4. `asset_provenance_receipts` for (`ka_tithi_pravesha`, canonical chart): `build_id` = the run id, `observed_at` >= the run start,
     `receipt_state = 'proven'`; `asset_freshness` `fresh`; `asset_throughput.state = 'lit'`.
  5. Data unchanged: `count(*)` of `kala_tithi_pravesha` for the chart = 120 and the content digest (section 3, F4) equals the
     pre-smoke digest.
  6. No other row changed: the count of `asset_throughput` rows with `last_built_at` after the run start, excluding the smoke asset, is 0.
```sql
-- :rid = the smoke run id ; asset = ka_tithi_pravesha ; chart = canonical
-- 1 run state
SELECT id, state, started_at, ended_at, last_error FROM build_runs WHERE id = :'rid';
-- 2 run asset
SELECT asset_id, state, disposition, output_changed, error FROM build_run_assets WHERE run_id = :'rid';
-- 3 audit rows since run start, by asset and db_user
SELECT asset_id, old_state, new_state, db_user, triggered_by, changed_at FROM asset_throughput_state_audit
 WHERE changed_at >= (SELECT started_at FROM build_runs WHERE id = :'rid') ORDER BY changed_at;
-- 4 receipt + freshness + throughput
SELECT r.build_id = :'rid'::uuid AS build_id_matches, r.receipt_state, r.observed_at, f.freshness_state, t.state
  FROM asset_provenance_receipts r
  JOIN asset_freshness f ON f.asset_id = r.asset_id AND f.chart_id IS NOT DISTINCT FROM r.chart_id AND f.partition_key = r.partition_key
  JOIN asset_throughput t ON t.asset_id = r.asset_id AND t.chart_id IS NOT DISTINCT FROM r.chart_id
 WHERE r.asset_id = 'ka_tithi_pravesha' AND r.chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
-- 5 data unchanged
SELECT count(*), md5(string_agg((to_jsonb(t) - 'build_id' - 'computed_at' - 'created_at' - 'updated_at' - 'id')::text, E'\n'
       ORDER BY (to_jsonb(t) - 'build_id' - 'computed_at' - 'created_at' - 'updated_at' - 'id')::text))
  FROM kala_tithi_pravesha t WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
-- 6 nothing else moved
SELECT count(*) FROM asset_throughput WHERE last_built_at >= (SELECT started_at FROM build_runs WHERE id = :'rid') AND NOT (asset_id = 'ka_tithi_pravesha' AND chart_id = '482012f1-710e-4a25-994a-93821f5871aa');
```
  Baseline before the smoke (15:16Z): `kala_tithi_pravesha` for the chart = 120 rows, content digest `d9900a93563f2b16226b0a13505bb487` (surrogate `id` excluded; re-capture
  immediately before the smoke).
- **Failure shapes:** an unfixed grant fails the first `asset_throughput` state UPDATE (`permission denied for table
  asset_throughput_state_audit`), the run ends `failed` and the asset stays lit (the state update itself aborts); a missing receipt
  grant fails with `provenance` text in `build_run_assets.error`. Neither touches data. A `failed` smoke is a NO-GO.

### P0.5 Go / no-go gate for starting the wave

GO only when all hold at the moment of launch: (1) P0.3 check 1 passes and the smoke build passed all six criteria within the
last 24 h and no deploy has changed the job image since (re-run the smoke after any deploy); (2) P0.3 check 2 passes for every
target table of the stages being launched (S0-S4 of section 8 need none of the phala_/mimamsa_ grants; S5-S6 do); (3) no `planned/running/paused` run exists;
(4) the section 5 pre-flight list is green. If (2) fails for the Phala/Mimāṃsā tables the wave can still be launched for
S0-S4 only (Bodha and Kāla assets, waves 1-6), with `ph_*` and `mi_bhavisya` deferred; that split is SS's call (Q9).


## 0. What this review needs you to see first

0. **Nothing can complete yet (P0 above).** The audit trigger on `asset_throughput` is not SECURITY DEFINER and `data_plane_builder`
   cannot insert into the audit table or use its sequence, and the same role holds no privilege on any `phala_*` or `mimamsa_*`
   table. The plan therefore starts with a smoke build on a leaf asset (`ka_tithi_pravesha`) and a go/no-go gate.
1. **The wave SS named is not a launchable set.** A run for exactly those eight assets is refused by the planner
   (`UPSTREAM_BLOCKED`): 12 out-of-plan direct dependencies are not lit and fresh (Evidence E3). Closing that
   set under the rule the planner and the runner both enforce (every declared dependency of a planned asset must be
   lit and fresh, or be planned earlier in the same run) gives a **26-asset minimal plan: 24 per-chart assets plus two
   global assets, `bg_transit_rules` (L0) and `ka_muhurta_seva` (L3 service)** (section 1, Evidence E4). The minimal plan is computed, not guessed; it is the
   smallest set for which the planner accepts the run (simulation of the planner's preflight on all 26: no out-of-plan blocker remains).
2. **Two structural blockers stop `gate_ok` for the four 1211 producers. Both are code-derived, not yet observed.**
   - **B-1 `ka_vighnakara` can never be 'proven'.** It has no output-digest spec (`asset_output_digest_specs` has no row;
     migration 1034's header calls it an explicit blocked contract: `kala_obstruction` has no stable non-null unique key).
     After a rebuild its receipt is 'unknown', so its freshness is 'unknown', and `asset_runner.deps_unsatisfied`
     (default mode `enforce`) refuses its direct dependents `ka_kala_darshana`, `ka_bhavishya_lekha`, `ph_muhurta`,
     `ph_pratikara`, which cascade-blocks `ph_nimitta`, `ph_pramana`, `ph_phaladesa`, `mi_bhavisya` and three more (`ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`; 11 in plan).
   - **B-2 `ka_sangam` will also receipt as 'unknown'.** `compute_upstream_hash` returns NULL when any declared
     dependency has no `output_digest`. `ka_sangam` declares `ka_muhurta_seva` (no receipt row at all) and `ka_dasha_kala`
     (receipt without `output_digest`). A NULL upstream digest makes the receipt 'unknown'. `ka_sangam` has 7 direct in-plan
     dependents including `ph_nimitta`. No receipt with `upstream_digest_unavailable` exists in the live table today, so this
     path has never been exercised in production.
   - Consequence (code-derived): on today's code a full run lands the Bodha assets, `ka_gochara`, `ka_yojaka`, `ka_avadhi` and
     `ka_sangam` (lit, receipt 'unknown'); then `ka_kalasutra`, `ka_vighnakara`, `ka_kala_darshana`, `ka_bhavishya_lekha`, all 8 `ph_*` and
     `mi_bhavisya` end as `blocked_dependency` errors (their old rows untouched). No 1211 producer reaches gate_ok. The 1211 gate cannot be met until B-1 and B-2 are decided (section 9, Q1-Q2). Only a spec (B-1) or a
     contract change to the service receipts (B-2) fixes it; running with `ORCHESTRATOR_DEP_ASSERT=warn` would run the
     consumers but still leave their receipts 'unknown' (not gate_ok), so it does not meet the 1211 gate either.
3. **The active-run slot was occupied minutes before this review.** `build_runs` 8684032d (asset_set `ka_gochara_resonance`,
   action rebuild, `triggered_by = l3-lane-frozen-manifest-rebuild`) was created 2026-10-01 14:57:39Z as `planned`; at
   15:04Z it reads `failed` (started 15:01:18, ended 15:01:19, its one asset still `queued`, `last_error` NULL). Another lane is evidently trying to
   dispatch on this chart today, so the active-run check (section 5) must be repeated at launch. `ka_gochara_resonance` is
   upstream of `ka_gochara`, which is in this plan.
4. **No launch path exists for this session today** (section 8). The broker and builder (E5.3, E7.1-E7.3) are
   superseded by the S0.C6 scratch build/publisher, which is not built; `suvarna_level_wave.py` is not on main; N-1 is not in
   the decisions log. The only existing paths are the cockpit `POST /api/cockpit/runs` by a logged-in owner/super_admin, or
   the native's `dispatch_*.py` pattern with production write credentials. Both are native acts.
5. **Current live data is degenerate, so the rebuild replaces little and inserts a lot.** For the canonical chart
   `kala_convergence`, `kala_obstruction`, `kala_activation`, `kala_darshana`, `kala_bhavishya`, `phala_sodhana` hold 0
   rows (other charts hold rows: `kala_convergence`, `kala_obstruction`, `kala_activation` on 1c826d5a and cb73cd3d; `kala_darshana`, `kala_bhavishya`, `phala_sodhana` on 1c826d5a only; Evidence E5) and `phala_anchors` holds 4 rows against 139 at the last real build
   (`asset_throughput.rows_written`), while `mimamsa_predictions` still holds 139 'pending' predictions whose anchors
   (`pred_<anchor_id>`) no longer exist in `phala_anchors` (139 of 139 orphaned). Why the canonical L3 rows are empty is
   not established here (open question Q7).
6. **`ka_avadhi` is a hard error, not a cascade.** Three runs on 2026-09-10 failed `post-write integrity check failed:
   integrity_check_sql -> False`. Running that SQL read-only on the live table today returns false on conjuncts (c)
   (all 1169 canonical rows have empty `lord_condition_fact_refs`) and (e) (4129 `activated_pratijna_ids` do not resolve
   to `bodha_pratijna`). The writer on main now normalises the lord subject (M4), so a rebuild should pass (c); this is
   untested. `ka_avadhi` must run after `bo_pratijna` (it consumes `bodha_pratijna` ids) and after the I-1 fix is deployed.

## 0.1 Summary table (minimal 26-asset plan, canonical chart)

"Rows today" = the registry's own chart-scoped `count_sql` at 2026-10-01T14:54:40Z (Evidence E5). "Last real" =
`asset_throughput.rows_written` (last completed build; a reference for the expected insert count, not a promise).
"Est. min" = median / maximum of completed runs for this chart (`build_run_assets`, skip rows excluded; Evidence E6).
Frozen: Nirmāṇa-frozen definition (tier), source `NIRMANA_SUPERSESSION_RECORD_v1_0.md` section 2.

| # | Asset | Why in the plan | Wave | Rows today | Last real | Est. min (med/max) | Frozen | Canary (section 4) |
|---|---|---|---|---|---|---|---|---|
| 1 | bg_transit_rules (GLOBAL L0) | `ka_yojaka` dep; receipt stale `registry_changed` | 1 | 76 | 104 | 0 / 0 (skip) | t0 | 4.1 L0 note |
| 1b | ka_muhurta_seva (GLOBAL L3 service) | lit but no `asset_freshness` row: planner service exception fails, blocks `ka_sangam`, `ka_vighnakara` (B-3) | 1 | 0 (no data table) | 0 | 0.0 / 0.0 | t0 | 4.2 note |
| 2 | bo_karanajala | receipt stale `registry_changed` (1210 edge); dep of `bo_anveshana`, `bo_cgm_paths` | 1 | 849 | 864 | 0.3 / 18.2 | t3 | 4.1 SQL; bodha_graph_traverse_get |
| 3 | bo_drishti | dep of `bo_anveshana`; throughput stale | 2 | 60 | 60 | 1.2 / 2.9 | t1 | 4.1 SQL |
| 4 | bo_anveshana | dep of `ph_nimitta`; throughput stale | 3 | 4437 | 4437 | 0.4 / 6.2 | t2 | 4.1 SQL |
| 5 | bo_cgm_motifs | dep of `bo_upaya`; throughput stale | 2 | 600 | 600 | 0.1 / 1.7 | t1 | 4.1 SQL |
| 6 | bo_cgm_paths | dep of `ph_nimitta`; throughput stale | 2 | 45 | 45 | 0.0 / 0.4 | t1 | 4.1 SQL |
| 7 | **bo_pratijna** | SS wave; stale; 1210 edge `ga_vargas` | 1 | 135 | 135 | 0.3 / 0.9 | t1 | 4.1 SQL; bodha_pratijna_get |
| 8 | bo_upaya | dep of `ph_pratikara`; throughput stale | 3 | 180 | 240 | 0.2 / 1.3 | t1 | 4.1 SQL; bodha_remedies_get |
| 9 | **ka_avadhi** | I-1 consumer; hard error | 2 | 1169 | 1169 | 0.2 / 1.0 | no | 4.2 I-1 note; kala_bundle_get |
| 10 | ka_gochara | dep of `ka_sangam`; receipt stale (1091) | 2 | 0 (count_sql misdirected; own table 87) | 87 | 0.0 / 2.4 | t1 | 4.2 SQL |
| 11 | **ka_yojaka** | SS wave; stale; 1210 edge `ga_yoga` | 2 | 50678 | 50678 | 0.6 / 1.6 | t2 | 4.2 SQL; kala_windows_get |
| 12 | ka_sangam | dep of `ph_nimitta`, `ka_vighnakara`; stale | 3 | 0 | 14868 | 8.0 / 73.2 | no | 4.2 SQL; kala_bundle_get |
| 13 | ka_kalasutra | dep of `ka_kala_darshana`; stale | 4 | 0 | 335403 | 0.8 / 10.8 | no | 4.2 SQL |
| 14 | **ka_vighnakara** | I-2 consumer; stale; B-1 | 4 | 0 | 536 | 0.3 / 1.4 | no | 4.2 I-2 reason; kala_bundle_get |
| 15 | ka_kala_darshana | reads `kala_obstruction`; dep of `ka_bhavishya_lekha` | 5 | 0 | 750 | 0.0 / 0.1 | no | 4.2 SQL; kala_bundle_get |
| 16 | ka_bhavishya_lekha | dep of `ph_nimitta`; stale | 6 | 0 | 100 | 0.0 / 0.0 | no | 4.2 SQL; kala_projections_get |
| 17 | **ph_nimitta** | SS wave; stale; 1211 producer | 7 | 4 | 139 | 0.0 / 1.0 | no | 4.3 SQL |
| 18 | ph_muhurta | reads `kala_obstruction`; dep of `ph_pramana` | 8 | 134 | 139 | 0.0 / 0.3 | no | 4.3 SQL |
| 19 | ph_pratikara | reads `kala_obstruction`; dep of `ph_pramana` | 8 | 536 | 536 | 0.0 / 0.9 | no | 4.3 SQL |
| 20 | ph_sankrama | dep of `ph_pramana` | 8 | 155 | 2510 | 0.0 / 3.5 | no | 4.3 SQL |
| 21 | ph_sodhana | dep of `ph_pramana` | 8 | 0 | 97 | 0.0 / 0.2 | no | 4.3 SQL |
| 22 | ph_suddha_sodhana | dep of `ph_pramana` | 9 | 4 | 139 | 0.0 / 0.3 | no | 4.3 SQL |
| 23 | **ph_pramana** | SS wave; stale | 10 | 4 | 139 | 0.0 / 0.4 | no | 4.3 SQL |
| 24 | **ph_phaladesa** | SS wave; stale | 11 | 13 | 13 | 0.0 / 0.1 | no | 4.3 SQL |
| 25 | **mi_bhavisya** | SS wave; throughput 'error' (cascade skip) | 12 | 278 (139 + 139) | 278 | 0.0 / 0.3 | no | 4.4 SQL |

Totals (estimate, from history): sum of medians 755 s (12.6 min); sum of maxima 7749 s (129 min); `ka_sangam` alone is
8 min median and 73 min maximum. Waves 1-12 run in dependency order; same-wave assets may run in parallel
(worker width `ORCHESTRATOR_WORKER_LIMIT`, value in the job env not readable here). Conservative wall time: 130 min plus
one retry of `ka_sangam` if its first attempt times out (see section 6).

## 1. ORDER of assets, dependency closure and cascade

### 1.1 What a rebuild run actually is (code read, main 3311b0a06)

| Step | Where | Behaviour |
|---|---|---|
| Request | `platform/src/app/api/cockpit/runs/route.ts` POST | Body `{chart_id, scope, scope_target, action, clear_before?}`. For this wave: `scope='asset_set'`, `scope_target='<comma list>'`, `action='rebuild'`, no `clear_before` (the route's clear path is not wanted: the writers do their own delete-then-insert). |
| Authorization | same, `requireChartPermission(access:'write')` | A logged-in Firebase user who is the chart owner or `super_admin`. Non-super-admins cannot plan any `scope='global'` asset (`computeNonCandidateAssetIds`), so `bg_transit_rules` needs `super_admin`. |
| Active-run guard | same, `findActiveRun` + unique index `build_runs_one_active_per_chart_idx` | Any `planned/running/paused` run for the chart returns 409 `RUN_ACTIVE`. |
| Planning | `runPreparation.ts loadPlanningInputs` + `plan.ts resolveBuildPlan` | `asset_set` plans exactly the named, registry-resolved assets: no upstream is added, no downstream expansion for `rebuild`. Out-of-plan direct dependencies are pre-flighted: each must be `asset_throughput.state` in (`lit`,`service_ok`) AND its latest `asset_freshness` row `fresh` (a healthy service with the two exact unknown-reason shapes is the only exception). Else HTTP 422 `UPSTREAM_BLOCKED` with a blocker list. Protected assets (`build_protected_assets`: only `ka_gochara_sweep` for this chart) are withheld. |
| Freeze | `freezeRunManifest` | Waves, per-asset `depends_on`, `natural_key_partition`, `has_cowriters`, and `expected_code_digest` read from `platform/src/generated/nirmana-writer-digests.json` are frozen into `build_runs.plan_manifest` and its sha256. |
| Persist | `persistPreparedRun` | One transaction inserts `build_runs` (state `planned`) and one `build_run_assets` row per asset (`queued`). |
| Dispatch | `runDispatch.ts` -> `jobInvoker.ts invokeRunJob` | Cloud Run Job `brahma-build-pipeline-job` (region asia-south1, project `madhav-astrology` unless env overrides) with args `--run-id <id>`, env `MARSYS_RUN_ID`. On failure `terminalizeFailedRun` marks the run failed. `BUILD_EXECUTOR=local` instead spawns `python -m pipeline.orchestrator.main --run-id` locally. |
| Run | `orchestrator/runner.py execute_run` | Validates the frozen manifest and that the sidecar code digest equals the manifest's; per-asset registry-divergence check (a diverged asset fails and its dependents are blocked); chart advisory lock; wave-parallel dependency-gated scheduler. |
| Per asset | `asset_runner.py run_asset` | (1) DEP-ASSERT, default `enforce` (`ORCHESTRATOR_DEP_ASSERT`): every declared dep must be `lit`/`service_ok` AND freshness `fresh` (services exempt from freshness); else the asset is marked error `DEP-ASSERT ...`. (2) throughput `building`. (3) Delta-skip gate unless `NIRMANA_FORCE_EXECUTE` (the cockpit does not set it): if a proven stored receipt matches current code, config, upstream and partition digests, the writer is NOT run, the receipt is re-stamped, disposition `skip_no_delta`, zero rows replaced. (4) Writer in the run's transaction (light writers: one transaction, rolled back if the integrity SQL is false; heavy writers with substeps commit per substep). (5) Post-write `integrity_check_sql` must be true. (6) Receipt + freshness persisted, throughput `lit` (0 rows with `target_floor`>0 becomes `dormant`). (7) If `output_changed` is TRUE or unknown, every downstream asset NOT in the plan and currently `lit`/`service_ok` is set `stale`. |
| Failure | `runner.py _mark_asset_blocked/_mark_asset_error_terminal` | A dependent of a failed asset is NOT executed; it is recorded `state='error'` with `disposition='blocked_dependency'`, `blocked_by_asset_id`. |

Delta-skip detail that matters here: the upstream digest hashes each declared dependency's whole receipt including its
`observed_at`. A re-stamped or rebuilt dependency therefore changes every consumer's digest, so consumers execute. Only the
upstream-most assets whose inputs did not change can skip. Migration 1210 added a declared dependency to `bo_karanajala`
(`ga_vichara`), `bo_pratijna` (`ga_vargas`), `ka_yojaka` (`ga_yoga`) and `ka_vighnakara` (`ga_dashas`); their stored receipts
list the old upstream sets (checked: `bo_pratijna` receipt upstreams are `bo_laksana, bo_sangati`; `ka_yojaka` has no
`ga_yoga`), so these four will EXECUTE, not skip. `bg_transit_rules` (no dependencies) is the one asset likely to skip
(estimate: code and config unchanged; its stale flag reads `registry_changed` only).

### 1.2 Closure and minimal plan (computed from the live registry, 127 active assets)

- Upstream closure of the eight named assets: 71 assets. Not lit-and-fresh today: 27, or 28 once the planner's rule for services is applied to `ka_muhurta_seva` (`fixpoint.py`, `fixpoint_v2.py`, Evidence E4).
- The runner only asserts the DIRECT dependencies of an asset it runs, so the minimal plan is the fixpoint: start from the
  eight; add any direct dependency that is not lit-and-fresh; repeat. Result: 26 assets (the 8 named + 18 added).
- Added assets and why: `bg_transit_rules` (dep of `ka_yojaka`; global L0; receipt `registry_changed`), `ka_muhurta_seva` (global L3 service
  with a writer self-test, lit, but it has NO `asset_freshness` row: the planner's service exception needs a freshness row in the writer-self-test
  shape, so it blocks `ka_sangam` and `ka_vighnakara` as `UPSTREAM_BLOCKED` unless it is planned; B-3), `bo_karanajala`
  (receipt `registry_changed` after 1210; dep of `bo_anveshana`, `bo_cgm_paths`), `bo_drishti`, `bo_anveshana`,
  `bo_cgm_motifs`, `bo_cgm_paths`, `bo_upaya` (throughput `stale`), `ka_gochara` (receipt `registry_changed`, migration 1091;
  dep of `ka_sangam`), `ka_sangam`, `ka_kalasutra`, `ka_kala_darshana`, `ka_bhavishya_lekha` (stale, no receipt; chain to
  `ph_nimitta`), `ph_muhurta`, `ph_pratikara`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana` (stale; deps of `ph_pramana`
  / `ph_phaladesa`).
- Not added (already lit and fresh, direct deps only): `bo_laksana`, `bo_bimba`, `bo_samskara`, `bo_sangati`, `ga_*`,
  `bg_ghatana`, `bg_dignity_reference`, `mi_kula`, `mi_jivanaghatana`, `ka_muhurta_seva` (service, lit).
  `bg_vedha_malefic_scale` (global, stale) is NOT needed: only `ka_vedha_gochara`, which is not rebuilt, consumes it.

### 1.3 Order (a valid linearisation; the scheduler runs same-wave assets in parallel)

| Wave | Assets |
|---|---|
| 1 | bg_transit_rules and ka_muhurta_seva (both global, need super_admin, see Q3), bo_karanajala, bo_pratijna |
| 2 | bo_drishti, bo_cgm_motifs, bo_cgm_paths, ka_avadhi, ka_gochara, ka_yojaka |
| 3 | bo_anveshana, bo_upaya, ka_sangam |
| 4 | ka_kalasutra, ka_vighnakara |
| 5 | ka_kala_darshana |
| 6 | ka_bhavishya_lekha |
| 7 | ph_nimitta |
| 8 | ph_muhurta, ph_pratikara, ph_sankrama, ph_sodhana |
| 9 | ph_suddha_sodhana |
| 10 | ph_pramana |
| 11 | ph_phaladesa |
| 12 | mi_bhavisya |

Hard ordering reasons: `ka_avadhi` after `bo_pratijna` (reads `bodha_pratijna` ids, section 0 item 6) and only after the
I-1 fix is merged and deployed (the digest inventory and the job image must carry the fixed writer; see section 5);
`ka_vighnakara` after the I-2 fix (PR #2823) and after `ka_sangam` and `ka_yojaka`; `ka_kala_darshana`, `ph_pratikara`,
`ph_muhurta` read `kala_obstruction` so they must follow `ka_vighnakara`; `mi_bhavisya` strictly last (it freezes one
prediction per `phala_anchors` row: run before `ph_nimitta` is rebuilt and it would replace 139 predictions with about 4).

### 1.4 Cascade: what the orchestrator does to dependents

Assets downstream of the plan and NOT in it (25 of them, from the live registry): 11 `stale`
(bo_cdlm_summary, bo_chart_gestalt, bo_pramana_mapa, bo_samvada, bo_yantra_mechanism, ka_jivana_parva, ka_taranga, ka_tulana,
mi_abhilekha, mi_seva, ph_rectification), 8 `error` that are cascade victims (ka_kshetra, mi_adhilepa, mi_bhara,
mi_darshana, mi_gunanaka, mi_pariksha, mi_pramana, mi_sambandha), 1 `dormant` (mi_sankalpa) and **5 currently `lit`**:
`bo_laksana_rerank`, `bo_sangati`, `ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_vedha_gochara`.

- If a plan asset completes with `output_changed` TRUE (or not recorded), the 5 lit ones that are downstream of it flip to
  `stale`. Two are direct dependencies of planned assets and would then fail DEP-ASSERT: **`bo_sangati`** (downstream of
  `bo_karanajala`; direct dep of `bo_pratijna`, `bo_drishti`, `bo_anveshana`, `bo_upaya`, `ka_yojaka`, `ph_nimitta`, `ph_sankrama`) and
  **`ka_vedha_gochara`** (downstream of `bg_transit_rules`; direct dep of `ka_sangam`). `ka_gochara_resonance` and
  `ka_moorti_nirnaya` (deps of `ka_gochara`) likewise follow `bg_transit_rules`.
- Mitigation built into the plan: run `bo_karanajala` first (S1 in section 8), read `build_run_assets.output_changed` for it,
  and only continue if it is FALSE or the contingency set (`bo_laksana_rerank`, `bo_sangati`, with `ka_vedha_gochara`,
  `ka_gochara_resonance`, `ka_moorti_nirnaya` for the L0 asset) has been added. The writers are deterministic
  (estimate: output unchanged on an unchanged input), but 1210 changed the upstream set, so this is checked, not assumed.
- The 8 `error` cascade victims stay `error` until their own rebuild; `mi_gunanaka` and `mi_pariksha` are the consumers of
  the 1211 edges and are outside this wave. After the wave they remain blocked by `mi_bhavisya`/`mi_pramana` state, which is
  the pre-existing condition (Track I item I-3), not a regression.
- No lit asset outside the 5 above changes state through this wave.

## 2. EXPECTED ROWS REPLACED

Method. For each asset: (a) tables written, from the registry `target_table` and from every `INSERT/UPDATE/DELETE`
statement in the writer (`platform/python-sidecar/pipeline/orchestrator/writers/<asset>.py`, read in full for the delete
sites); (b) the delete predicate; (c) live row counts for the canonical chart (the registry's own `count_sql` for the
registry table, plus a direct `count(*) ... WHERE chart_id=` for the other tables, Evidence E5). Counts at
2026-10-01T14:54Z-15:03Z. `n/r` = table not readable by `suvarna_reader` (permission denied; not worked around). Expected
inserted = the last real `asset_throughput.rows_written` (a reference, estimate: it assumes unchanged inputs; values for
assets with an unproven or changed upstream can differ).

| Asset | Tables written | Delete predicate (all chart-scoped) | Rows today (deleted) | Reference inserted |
|---|---|---|---|---|
| bg_transit_rules (global) | `bg_transit_engine`, `bg_transit_rules` | none: `seed_transit_rules` upserts, `ON CONFLICT DO UPDATE` (L0 standard); shared by every chart | 76 (`bg_transit_rules`) | 104 (rows_written, both tables) |
| ka_muhurta_seva (global) | none: `services/ka_muhurta_seva/writer.py` does a FORENSIC self-test and a service-health write, `rows_inserted = 0` | none | n/a | 0 |
| bo_karanajala | `bodha_cgm_edges`, `bodha_contradictions`; UPDATEs 4 centrality columns on `bodha_cgm_nodes` (bo_bimba's table) | `replace_prior_cgm_edges` / `replace_prior_contradictions`: `chart_id` + `ayanamsha_id` (5 ayanamshas) | edges 849; contradictions n/r | 864 |
| bo_drishti | `bodha_question_lenses` | `chart_id` | 60 | 60 |
| bo_anveshana | `bodha_discoveries`, `bodha_anomalies` | `chart_id` each | 1161 + 3276 = 4437 | 4437 |
| bo_cgm_motifs | `bodha_cgm_motifs`, `bodha_cgm_sub_graphs`, `bodha_cgm_chart_topology_summary` | `chart_id` each | 600; other two n/r | 600 |
| bo_cgm_paths | `bodha_cgm_paths` | `chart_id` | 45 | 45 |
| bo_pratijna | `bodha_pratijna` | `chart_id` | 135 | 135 |
| bo_upaya | `bodha_rm_resonances`, `bodha_rm_remedy_prescriptions`, `bodha_rm_dasha_windowed_prescriptions`, `bodha_rm_chart_summary`, `bodha_rm_dosha_remedy_bundles`, `bodha_rm_pattern_remedies` | `chart_id` (+ ayanamsha, snapshot_type for the first three) | 45 + 135 = 180; four tables n/r | 240 |
| ka_avadhi | `kala_avadhi` | `chart_id`, only after the full candidate set is assembled (empty candidate: prior rows preserved) | 1169 | 1169 |
| ka_gochara | `kala_gochara_windows_v2` (+ its build-state table upsert) | `chart_id` AND `event_class` AND generation `2.0` | 87 of the chart's 1001 rows (the other 914, generation `g3_utkarsha`, belong to `ka_gochara_v3_century_materialize` and are not matched). The registry `count_sql` reads `kala_gochara_windows` generation 4.0 and returns 0: the cockpit count does not measure this writer's table. | 87 |
| ka_yojaka | `kala_activation_predicates` | `chart_id` | 50678 | 50678 |
| ka_sangam | `kala_convergence`, `build_substep_progress` (own rows) | `chart_id` (full) or per `horizon_tier` / `signal_id` per substep; `build_substep_progress WHERE chart_id AND asset_id='ka_sangam'` | 0 | 14868 |
| ka_kalasutra | `kala_activation` | `chart_id` | 0 | 335403 |
| ka_vighnakara | `kala_obstruction` | `chart_id` | 0 | 536 |
| ka_kala_darshana | `kala_darshana` | `chart_id` | 0 | 750 |
| ka_bhavishya_lekha | `kala_bhavishya` | `chart_id AND id IN (...)` (a computed subset) plus an UPDATE | 0 | 100 |
| ph_nimitta | `phala_anchors` | `chart_id` | 4 | 139 (anchor ids are uuid5, deterministic) |
| ph_muhurta | `phala_muhurta` | `chart_id` | 134 | 139 |
| ph_pratikara | `phala_mitigation` | `chart_id` | 536 | 536 |
| ph_sankrama | `phala_sankrama` | `chart_id` | 155 | 2510 |
| ph_sodhana | `phala_sodhana` | `chart_id` | 0 | 97 |
| ph_suddha_sodhana | `phala_suddha_sodhana` | `chart_id` | 4 | 139 |
| ph_pramana | `phala_pramana` | `chart_id` | 4 | 139 |
| ph_phaladesa | `phala_phaladesa` | `chart_id` | 13 | 13 |
| mi_bhavisya | `mimamsa_manifestation_sets`, `mimamsa_predictions` | sets: `chart_id`; predictions: `chart_id AND lifecycle_status IN ('pending','due')` (confirmed/denied/partial outcome rows are never deleted) | 139 + 139 (all 139 predictions are `pending`; 0 outcome-bearing rows) | 278 if `phala_anchors` is restored to 139 |

Totals (canonical chart, live today, readable tables only): 59,368 rows deleted across the per-chart assets, dominated by
`kala_activation_predicates` (50,678); the reference insert total is 413,962, dominated by `kala_activation` (335,403) and
`ka_sangam` (14,868). Both figures are estimates (the deleted figure excludes the 7 unreadable tables and the 104 global rows).

### 2.1 Protected-table statement (verified against the writer source and `pg_tables`)

- **No L1 table is written.** No plan writer names `chart_facts`, `chart_dashas`, `chart_divisionals`, `chart_vichara`,
  `ga_*`, or `bodha_msr_signals` in any INSERT/UPDATE/DELETE (grep of the INSERT/UPDATE/DELETE statements in all 24 per-chart writers, plus the two
  `replace_prior_*` helpers `bo_karanajala` and `bo_upaya` import from `bodha_writers/_idempotency.py`).
- **Other charts' rows are not touched.** Every delete in the table above carries `chart_id = <canonical>`. Other charts hold
  `kala_obstruction` 1c826d5a=741 / cb73cd3d=6, `kala_convergence` 1c826d5a=17957 / cb73cd3d=2540, `kala_activation` 1c826d5a=336093
  / cb73cd3d=1055, and so on (`counts_all_charts_before.txt`); none is a delete target.
- **Shared tables:** `bg_transit_engine`/`bg_transit_rules` (global, upsert) is the only shared table in the plan.
  `kala_gochara_windows_v2` is shared with another writer but the predicate `generation = '2.0'` excludes its rows.
  `build_protected_assets` for this chart names only `ka_gochara_sweep` (not in the plan; its v1 corpus is untouched).
- **`data_plane_*_owner` tables ARE written, by design.** All `bodha_*` tables are owned by `data_plane_l2_owner` (45 tables
  in `pg_tables`); the 14 `bodha_*` tables above belong to it. They are written through the L2 producer-generation contract
  (`bodha_writers/data_plane_contracts.py`, migration 1036: immutable generation history per chart/asset); `bo_pratijna` is
  one of SS's named assets. `suvarna_reader` cannot read `data_plane_l2_producer_generations` (permission denied), so the
  generation rows a rebuild adds, and the rollback-by-generation the migration describes, are not verified here. If SS counts
  `data_plane_l2_owner` tables as protected for this wave, the 7 `bo_*` assets and the plan shrink; see open question Q4 in section 9.
- **Non-reversible effect:** delete-then-insert replaces rows in place (section 7); the before-state must be captured
  (section 3) because no table dump of protected data is taken.

## 3. BEFORE / AFTER FINGERPRINTS

### 3.1 What exists today (read from the DB and repo)

- `asset_provenance_receipts` (98 rows, 90 assets): per (asset, chart, partition) `code_digest`, `config_digest`,
  `upstream_digest`, `partition_digest`, `output_digest`, `receipt_state` (`proven`/`unknown`), `observed_at`, `build_id`. The
  `output_digest` is content-sensitive over the target table per the reviewed spec in `asset_output_digest_specs` (126 specs); it
  is the closest thing to a row-set fingerprint. Receipts for the plan today: `bo_pratijna` ee3dc90b4f3d (proven 09-09),
  `ka_yojaka` 3fd3b490ecc1 (proven 09-10), `bo_karanajala` 9ba68fbd0300, `bo_drishti` cb74fbd73e70, `bo_anveshana` cf80b5607541,
  `bo_cgm_motifs` 2855202f6200, `bo_cgm_paths` 107dc732278f, `bo_upaya` 56d707fc4dc8, `ka_gochara` f9ca0e1c8527,
  `bg_transit_rules` (global) 1983611685a8. **No receipt exists** for `ka_avadhi`, `ka_vighnakara`, `ka_sangam`, `ka_kalasutra`,
  `ka_kala_darshana`, `ka_bhavishya_lekha`, any `ph_*` or `mi_bhavisya` (not built since 2026-08-13, before receipts).
- `asset_freshness` (98 rows): `fresh`/`stale`/`unknown` plus `reasons`; the planner and DEP-ASSERT read the latest-observed row per asset.
- `asset_throughput`: `state`, `last_built_at`, `rows_written`, `duration_seconds`. `build_run_assets.output_changed` and `disposition`
  record, per run, whether a rebuild changed output or skipped.
- **E5.5 semantic fingerprints / stale-certification detector: NOT built.** `platform/scripts/governance/nikasha_*.py` does not exist on
  main (0 files); plan item E5.5 is not met. `asset_provenance_receipts.output_digest` and the per-table digest below are what is available.
- Caveat: a receipt digest cannot exist for `ka_vighnakara` (no spec) and is not 'proven' for several upstream assets (section 0).

### 3.2 Read-only SQL set to capture BEFORE and AFTER (store outputs in the evidence dir, with `date -u`)

```sql
-- F1  state of every plan asset (per chart; the bg_transit_rules row is global)
SELECT t.asset_id, t.state, t.last_built_at, t.rows_written,
       f.freshness_state, f.reasons, r.receipt_state, left(r.output_digest,12) AS output_digest, r.observed_at, r.build_id
FROM asset_throughput t
LEFT JOIN LATERAL (SELECT freshness_state, reasons FROM asset_freshness a WHERE a.asset_id=t.asset_id AND (a.chart_id IS NOT DISTINCT FROM t.chart_id)
                    ORDER BY observed_at DESC LIMIT 1) f ON true
LEFT JOIN LATERAL (SELECT receipt_state, output_digest, observed_at, build_id FROM asset_provenance_receipts p WHERE p.asset_id=t.asset_id
                    AND (p.chart_id IS NOT DISTINCT FROM t.chart_id) ORDER BY observed_at DESC LIMIT 1) r ON true
WHERE (t.chart_id='482012f1-710e-4a25-994a-93821f5871aa' OR (t.chart_id IS NULL AND t.asset_id='bg_transit_rules'))
  AND t.asset_id = ANY(string_to_array('<the 26 ids of section 1.3>',','))
ORDER BY 1;

-- F2  the 1211 gate (verify SQL Q4, /Users/Dev/suvarna-evidence/TrackI/1211_asset_registry_direct_edges_held_verify.sql): gate_ok per producer
-- F3  row counts: the registry's own count_sql per asset (script counts.py) + the extra tables of section 2
-- F4  per-table content digest (chart-scoped; excludes volatile columns; a table with a surrogate/uuid key needs that key added to the exclusion list first)
SELECT count(*), md5(string_agg((to_jsonb(t) - 'build_id' - 'computed_at' - 'created_at' - 'updated_at' - 'id')::text, E'\n'
                        ORDER BY (to_jsonb(t) - 'build_id' - 'computed_at' - 'created_at' - 'updated_at' - 'id')::text))
FROM <target_table> t WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';   -- tested on phala_phaladesa: 13 rows, md5 db95205ce6f203de74824e07d9f7451a
-- F5  other-chart canary (must be identical before/after): the same F3/F4 for charts 1c826d5a and cb73cd3d on kala_activation_predicates, kala_avadhi, bodha_pratijna
-- F6  state of everything downstream (section 1.4): SELECT asset_id,state FROM asset_throughput WHERE chart_id=... AND asset_id = ANY(<the 25 downstream ids of section 1.4>)
-- F7  run record: build_runs / build_run_assets for the run id (state, disposition, output_changed, error), and asset_throughput_state_audit rows since run start
```

The before-state F1 and F3 for the plan assets were captured now for reference (Evidence E5, `state_wave.sql`, `counts_before.txt`,
`counts_tables_before.txt`, `throughput_before.txt`); they will be stale by launch and must be re-captured in the pre-flight.

### 3.3 Expected AFTER state

Target state for the 1211 gate (and for every asset that has a spec): `asset_throughput.state = 'lit'`, latest `asset_freshness` =
`fresh`, receipt `proven`, `output_digest` written, `build_run_assets.state = 'complete'`.

| Asset group | Target after | Predicted on today's code |
|---|---|---|
| `bg_transit_rules` | lit, fresh, proven, digest 1983611685a8 unchanged (re-stamped, `skip_no_delta`) | as target (estimate) |
| Bodha assets (7) | lit, fresh, proven; new `output_digest` only if rows changed | as target if `bo_karanajala` is output-unchanged; else contingency (section 1.4) |
| `ka_avadhi`, `ka_yojaka`, `ka_gochara` | lit, fresh, proven | as target (`ka_avadhi` integrity risk, section 7) |
| `ka_sangam` | lit, fresh, proven | **lit but receipt 'unknown'** (B-2) |
| `ka_kalasutra`, `ka_kala_darshana`, `ka_bhavishya_lekha`, `ka_vighnakara` | lit, fresh, proven (`ka_vighnakara`: impossible, no spec) | all four blocked (`DEP-ASSERT ... ka_sangam(receipt:unknown)`; `ka_vighnakara` additionally cannot be proven) |
| `ph_*` (8) and `mi_bhavisya` | lit, fresh, proven | blocked by `ka_sangam`/`ka_vighnakara` (`blocked_dependency`) |
| Downstream outside the plan | the 5 lit ones stay lit; the stale/error ones unchanged | unchanged |

If B-1 and B-2 are resolved before launch, the target column is the expectation; the 1211 gate (`gate_ok` = state lit AND freshness fresh,
per the 1211 verify SQL's query Q4) additionally requires, for the new consumers' own later builds, that each producer's receipt is proven (that query prints `receipt_state`).

## 4. CANARY READS

Principle: the DB queries below are the authoritative canaries (read-only, runnable with the reader today where the table is
readable). The named MCP tools are the served readers; the mapping to tables was read from the registry/MCP source, and where it was
NOT verified that is said. No MCP call was made for this review.

### 4.1 Bodha assets

| Asset | Before/after SQL (canonical chart) | Expected change | Served reader |
|---|---|---|---|
| bo_pratijna | `SELECT count(*), md5(string_agg(...)) FROM bodha_pratijna WHERE chart_id=...` (F4); `SELECT event_class_id, status, round(grade::numeric,3) FROM bodha_pratijna WHERE chart_id=... ORDER BY 1,2` | 135 rows before and after; content unchanged if inputs unchanged (estimate); new `output_digest` only if content differs | `bodha_pratijna_get` (maps to `query_pratijna`, verified) |
| bo_karanajala | `SELECT count(*) FROM bodha_cgm_edges WHERE chart_id=...` (849) | 849 edges, same digest; `output_changed` FALSE is the gate for continuing | `bodha_graph_traverse_get` (`traverse_chart_graph`, verified) |
| bo_drishti, bo_anveshana, bo_cgm_motifs, bo_cgm_paths, bo_upaya | counts in section 2; F4 digests | unchanged counts (60 / 4437 / 600 / 45 / 180+) | `bodha_remedies_get` -> `query_remedies` (verified, for `bo_upaya`); the others: SQL only (tool mapping not verified) |
| bg_transit_rules | `SELECT count(*) FROM bg_transit_rules` (76) + digest | unchanged | none (L0, shared by every chart) |

### 4.2 Kāla assets (include the I-1/I-2 consumers named by the coordinator)

- **ka_avadhi, I-1 (changes).** Before (live, 2026-10-01): `kala_avadhi.dossier.sublord_modulation.note` is non-null on 1043 of
  1169 canonical rows; e.g. vimshottari level 2, `lord_graha = Venus`, `sublord_modulation.graha = Moon`, period_start 1950-01-01, reads
  **`AD lord Moon modulates MD lord Venus`**, i.e. the MD and AD lords are swapped (the same swap is the coordinator's `AD lord Dhanya
  modulates MD lord Bhadrika` example). After the I-1 fix (expected, from the defect description: roles corrected) the same row reads
  `AD lord Venus modulates MD lord Moon`. Canary SQL:
  `SELECT system_id, level_n, lord_graha, period_start, dossier->'sublord_modulation'->>'graha' AS parent_md_lord, dossier->'sublord_modulation'->>'note' AS note FROM kala_avadhi WHERE chart_id='482012f1-...' AND system_id='vimshottari' AND level_n=2 ORDER BY period_start LIMIT 5`.
  Expected: all 1043 notes change text; `md5(string_agg(note ORDER BY system_id, level_n, period_start))` is `a041ac2f18c66a677e52b168518fec25`
  today and must differ after. **Must not change:** row count 1169; `(system_id, level_n, lord_graha, period_start, period_end)` per row (verified
  by integrity conjunct (a)); `lord_condition_fact_refs` becomes non-empty on all nine-graha-lord rows (today empty on 1169 of 1169, a defect the
  integrity SQL conjunct (c) is built to catch). Served reader: `kala_bundle_get` (timeline = `kala_avadhi`, per its description; verified).
- **ka_vighnakara, I-2 (canonical output unchanged except two additive keys).** Today `kala_obstruction` has 0 canonical rows (741 and 6 on
  the other two charts), so there is no live canonical "before" to diff. The hard-coded text sits in `obstruction_detail->>'reason'` of the
  `malefic_transit` detector (`ka_vighnakara.py:589-592`: "adversarial to native lagna (Aries) / moon (Aquarius)"). Expected after the I-2 fix
  (coordinator, pinned by a test): for the canonical Aries-lagna / Aquarius-Moon chart the reasons and scores equal what the pre-fix code
  produces (the literal text happens to be true for this chart), and `obstruction_detail` gains two additive keys `natal_lagna_sign` and
  `natal_moon_sign`. Canary SQL: `SELECT obstruction_type, count(*), count(*) FILTER (WHERE obstruction_detail ? 'natal_lagna_sign') AS with_keys,
  min(obstruction_detail->>'natal_lagna_sign') AS lagna, min(obstruction_detail->>'natal_moon_sign') AS moon FROM kala_obstruction WHERE
  chart_id='482012f1-...' GROUP BY 1` (expect total about 536, estimate from the last real count; `with_keys` = total; lagna Aries, Moon Aquarius per
  the fix's own derivation from `chart_facts`). **Non-canonical charts (`1c826d5a`, `cb73cd3d`) must not change at all in this wave:** their
  obstruction scores change only when THEY are rebuilt, which this plan does not do; check `kala_obstruction` counts 741 and 6 and an F4 digest
  before/after. Served reader: `kala_bundle_get` (obstructions are `kala_obstruction`, not date-filtered; verified).
- **ka_kala_darshana, ph_pratikara, ph_muhurta (read `kala_obstruction`; go stale until rebuilt).** They carry obstruction detail/severity
  through; after their rebuild the canonical output is expected to equal the pre-fix text for score fields and gain the additive keys where they
  pass `obstruction_detail` through (estimate; the passthrough was reported by the reviewer, not read here). Canaries: `kala_darshana`
  (0 rows today, 750 last real), `phala_mitigation` (536) and `phala_muhurta` (134) counts + F4 digests. They are NOT Nirmāṇa-frozen.
- **ka_yojaka:** `SELECT count(*) FROM kala_activation_predicates WHERE chart_id=...` = 50678 before and after; digest equal if `bo_pratijna` is
  unchanged; other charts 50171 (`1c826d5a`) and 49875 (`cb73cd3d`) must not change. Reader: `kala_windows_get` (`query_temporal_activation`, verified).
- **ka_sangam / ka_kalasutra / ka_bhavishya_lekha / ka_gochara:** `kala_convergence`, `kala_activation`, `kala_bhavishya` count 0 today for the
  canonical chart (other charts hold theirs); after: about 14868 / 335403 / 100 (reference); `kala_gochara_windows_v2` generation `2.0` = 87 and
  `g3_utkarsha` = 914 must stay 87 and 914. Readers: `kala_bundle_get` (convergence), `kala_projections_get` (`query_projections`, verified for
  `kala_bhavishya`).

### 4.3 Phala assets

| Asset | Before | Expected after | Reader |
|---|---|---|---|
| ph_nimitta | `SELECT count(*) FROM phala_anchors WHERE chart_id=...` = 4 | about 139 (uuid5 anchor ids: `SELECT anchor_id FROM phala_anchors ...` are deterministic, so the 4 existing ids must survive) | `phala_predictive_anchors_get` (`query_predictive_anchors`, verified to exist); `phala_anchors_get` calls a sidecar compute route (`/api/compute/phala/event_anchors`), NOT verified to read `phala_anchors`, so SQL is authoritative |
| ph_pramana | 4 | about 139, exactly one per anchor (the asset's integrity SQL asserts it) | SQL; `query_phala_calibration` capabilities exist but no 1:1 MCP alias was verified |
| ph_phaladesa | 13 (13 domains) | 13; `anchor_count` per domain equals the true anchor population | `phala_outlook_get` (alias exists; capability mapping not verified); SQL authoritative |
| ph_muhurta, ph_pratikara, ph_sankrama, ph_sodhana, ph_suddha_sodhana | 134 / 536 / 155 / 0 / 4 | about 139 / 536 / 2510 / 97 / 139 (reference) | `phala_mitigation_get` (alias to `mitigation_map`, a platform primitive; table mapping not verified); SQL authoritative |

### 4.4 Mimāṃsā and the "must not change" set

- **mi_bhavisya:** `SELECT lifecycle_status, count(*) FROM mimamsa_predictions WHERE chart_id=... GROUP BY 1` = `pending` 139;
  orphan check `SELECT count(*) FROM mimamsa_predictions p WHERE chart_id=... AND NOT EXISTS (SELECT 1 FROM phala_anchors a WHERE 'pred_'||a.anchor_id=p.prediction_id AND a.chart_id=p.chart_id)`
  = **139 today** (every prediction is orphaned) and must be 0 after. Reader: the L5 capability `marsys://tool/L5/query_predictions` reads
  `mimamsa_predictions`; the MCP `standing_predictions_read` reads `brahma_prospective_ledger`, not this table (verified), so it is NOT a canary.
- **Must not change (before/after identical, counts and digest):** `chart_facts` (143,299 rows), `chart_dashas` (483,870), `bodha_msr_signals`
  (50,678), all L1 `ga_*` assets' throughput state, every non-canonical chart's rows in every table above, `bodha_pratijna` for the other two charts
  (135 each), `kala_gochara_windows` generation `v1` (16,297, protected), `build_protected_assets` (1 row), and the global `bg_*` tables other than
  `bg_transit_rules` / `bg_transit_engine`.

## 5. PRE-FLIGHT CHECKS (all read-only; repeat at launch)

| # | Check | How | State at review time (2026-10-01) |
|---|---|---|---|
| 1 | P0 passed (audit grant, phala/mimamsa grants as needed, smoke build) | section P0.3-P0.5 | **FAIL**: audit INSERT and sequence USAGE false; 10 phala_/mimamsa_ tables unreadable/unwritable for the builder; no smoke |
| 2 | Deploy idle: no `Deploy to Cloud Run` run with event `workflow_run` or `workflow_dispatch` in progress or pending | `gh run list --workflow deploy.yml --json status,conclusion,headSha,createdAt,event` (the `pull_request` runs are build-checks only and do not deploy) | **NOT idle**: a `workflow_run` deploy for main 3311b0a06 was `in_progress` at 15:04:39Z; the previous one (0250cbade) succeeded 14:25:28Z. Re-check, and re-run the smoke after it lands (image change). |
| 3 | No in-flight runs for the chart | `SELECT id,state FROM build_runs WHERE chart_id='482012f1-...' AND state IN ('planned','running','paused')` (the unique index enforces this server-side) | 0 at 15:04Z (8684032d failed 15:01); another lane dispatched at 14:57, so repeat at launch (Q8) |
| 4 | Registry unchanged since this plan | `SELECT count(*), md5(string_agg(asset_id\|\|'>'\|\|coalesce(depends_on::text,''),',' ORDER BY asset_id)) FROM asset_registry WHERE is_active` | 127 assets, md5 `fb7a1090d5aa3c7dabafc9f9daf1ae6a` (2026-10-01T14:49Z); latest `_migrations_applied` filename = `1210_asset_registry_direct_edges.sql` (applied 14:37:09Z); no 1211. The runner also re-checks each planned asset against the frozen manifest at start (a diverged asset fails and blocks its dependents). |
| 5 | Planner preflight clean for the exact request | simulation `preflight_sim.sql` with the 26 ids (Evidence E4) | 0 blockers; the only out-of-plan direct deps not 'fresh' are services `ka_dasha_kala` (freshness `unknown`, the exact writer-self-test shape, accepted) |
| 6 | Upstream state of out-of-plan deps | rows lit AND fresh for `bo_laksana`, `bo_bimba`, `bo_samskara`, `bo_sangati`, `ga_dashas`, `ga_positions`, `ga_vargas`, `ga_yoga`, `bg_ghatana`, `bg_dignity_reference`, `mi_kula`, `mi_jivanaghatana` | all lit and latest-row fresh at 14:49Z. Caveat: `bo_laksana` and `ga_positions` also carry older partition rows that are stale/unknown; both the planner and DEP-ASSERT read only the latest-observed row, so they pass, but a new observation row would change that. |
| 7 | Job image tag = a commit that contains the L3 fixes (I-1, I-2: PR #2823) and the regenerated writer-digest inventory | the cockpit POST response returns `job_image_tag`; or `gcloud run jobs describe brahma-build-pipeline-job --region asia-south1 --format='value(spec.template.spec.template.spec.containers[0].image)'` (a native/CI act; the reader cannot see it). Compare with `git log -1 -- platform/src/generated/nirmana-writer-digests.json` and `git merge-base --is-ancestor <fix sha> <image sha>` | not readable by this lane. The runner refuses the whole run if the job's writer sources do not hash to the manifest's `expected_code_digest` (`_verify_sidecar_code_matches_manifest`), so a stale image fails closed rather than writing old text. |
| 8 | I-1/I-2 merged | PR #2823 on `suvarna/land/TI-i12-narration-001` | not merged at the time `origin/main` was read (branch has no commits ahead of main at 14:51Z; the coordinator reports ACCEPT and merge imminent). `ka_avadhi` and `ka_vighnakara` must not run before the merge AND the deploy. |
| 9 | Held migration 1211 not applied; its gate SQL ready | `1211_asset_registry_direct_edges_held_verify.sql` 1211-verify Q4/Q6 | 1211 held (branch TI-edges-002, commit 086a0fcc5) |
| 10 | Before-state captured (F1, F3, F4, F5) and stored | section 3 | not yet (re-capture at launch) |
| 11 | Protected set unchanged | `SELECT * FROM build_protected_assets WHERE chart_id=...` | 1 row: `ka_gochara_sweep` (not in plan) |
| 12 | No Nirmāṇa campaign wave running | native decision 2026-09-28: campaign OFF; `NIRMANA_SUPERSESSION_RECORD_v1_0.md` section 3 | off (not independently re-verified) |
| 13 | The L1 `ga_dashas` replacement fence is not set | 1070's header mentions a stuck `ga_dashas_replacement_in_progress` guard on the canonical chart; the signal is raised by `ganita_dashas_get` (not a table the reader can see) | unknown; check with one `ganita_dashas_get` call after the smoke |

**Post-run checks:** the run is `completed` with every asset `complete` (or `error` only as predicted in section 3.3); F1 expected states;
F3/F4 counts and digests against section 2 and section 4 canaries; audit rows for each state change (`db_user`); no asset left `building`;
`ph_nimitta`, `bo_pratijna`, `ka_yojaka`, `mi_bhavisya` gate SQL (1211-verify Q4) printed; other-chart canaries (F5) identical; the 25 downstream assets
(F6) in the states of section 1.4; the 1211 gate decision recorded.

## 6. EXPECTED DURATION

Source: `build_run_assets` for this chart (state `complete`, `skip_no_delta` rows excluded, started/ended recorded), medians and
maxima; Evidence E6 (`timing_out.txt`); `writer_timeout_seconds` from `asset_registry`.

| Group | Assets | Sum of medians | Sum of maxima | Per-asset budget (`writer_timeout_seconds`) |
|---|---|---|---|---|
| G1 Bodha (+ L0/service first) | bg_transit_rules, ka_muhurta_seva, bo_karanajala, bo_pratijna, bo_drishti, bo_cgm_motifs, bo_cgm_paths, bo_anveshana, bo_upaya | 2.6 min | 31.6 min | 10800 s each (`bo_laksana_rerank` 600 s is not in the plan) |
| G2 Kāla core | ka_avadhi, ka_gochara, ka_yojaka, ka_sangam, ka_kalasutra, ka_vighnakara, ka_kala_darshana, ka_bhavishya_lekha | 9.8 min | 90.6 min (`ka_sangam` alone 73.2) | 10800 s; `ka_gochara` 1800 s |
| G3 Phala | 8 assets | 0.2 min | 6.7 min | 10800 s |
| G4 Mimāṃsā | mi_bhavisya | 0.02 min | 0.3 min | 10800 s |
| Total (serial sum) | 26 | **12.6 min** | **129 min** | |
| Critical path (parallel, dependency-gated) | 12 waves | **9.7 min** | **92 min** | |

Estimates only: they assume the history is representative (22 runs per asset for most; `ka_sangam` 22 completed, median 478 s, maximum 4390 s;
none of the L3/L4/L5 assets has run since 2026-08-13 and the Kāla tables are currently empty for this chart, so a first full `ka_sangam` rebuild
is the least certain number). The worker width (`ORCHESTRATOR_WORKER_LIMIT`) is not readable; if it is 1 the serial sum applies. Add Cloud Run job
start-up and the freeze: single-asset runs since 2026-09-01 took a median 25 s from creation to end (n=128). **Conservative total: 130 minutes
plus the smoke build (about 5 minutes) and one reserve slot of 75 minutes for a `ka_sangam` retry, so plan a window of about 4 hours.**
Watchdog exposure (15 minutes, section 7): `bo_karanajala` (maximum 1091 s), `ka_kalasutra` (650 s) and `bo_anveshana` (374 s) are light writers; a
single transaction longer than 15 minutes without a heartbeat is at risk (section 7, R-7).

## 7. RISKS AND ROLLBACK

### 7.1 Risk register

| # | Risk | Evidence / mechanism | Impact | Mitigation in this plan |
|---|---|---|---|---|
| R-1 | The builder cannot complete any run (audit trigger) or write phala_/mimamsa_ tables | P0.1, P0.2 | No data changes; runs end `failed`; Stages 4-6 impossible | P0 gate; smoke build first |
| R-2 | **B-1 / B-2 / B-3: the wave cannot reach 'proven' for the Phala/Mimāṃsā half** | section 0 items 1-2 (code-derived) | Predicted partial result: S0-S3 land except `ka_kalasutra`; `ka_sangam` lit with receipt 'unknown'; `ka_kalasutra`, `ka_vighnakara`, `ka_kala_darshana`, `ka_bhavishya_lekha`, `ph_*`, `mi_bhavisya` end `error` with `blocked_dependency` (their old rows untouched); the 1211 gate stays closed | Decide Q1/Q2 before S4; rehearse off production (E5.6 style) or run Stages 1-3 only |
| R-3 | A delete-then-insert replaces rows in place and is not reversible by this lane | writers (section 2) | If new rows are wrong, old rows are gone | before-state digests (section 3) prove WHAT changed but are not a backup; need a native-held restore point (Q6) |
| R-4 | `ka_avadhi` integrity failure again | 3 failures on 2026-09-10; conjuncts (c),(e) false on today's data | asset `error`; light writer rolls back, so prior 1169 rows are preserved | run after `bo_pratijna` and after I-1/M4 is deployed; if it fails read `build_run_assets.error` before retry |
| R-5 | `bo_karanajala` output changes, staling `bo_sangati` etc. mid-plan | section 1.4 | S2 assets (`bo_pratijna`, `bo_drishti`, `bo_anveshana`, `bo_upaya`, then `ka_yojaka`, `ph_nimitta`, `ph_sankrama`) fail DEP-ASSERT `bo_sangati(stale)` | S1 isolates `bo_karanajala`; read `output_changed` before Stage 2; contingency set pre-computed |
| R-6 | `mi_bhavisya` run before `ph_nimitta` is restored | 139 pending predictions replaced by about 4 | loss of 135 rebuildable predictions (ids `pred_<anchor_id>` are deterministic so a later rebuild restores them) | strict last position; S6 gate: `phala_anchors` count about 139 |
| R-7 | Orphan watchdog kills a long light writer | `watchdog/route.ts`: a `running` run older than 30 min with no building asset whose `last_built_at` advanced in 15 min and no substep completed in 15 min is marked `failed`; a `building` asset with `last_built_at` older than 15 min is set `error` (heavy writers with a completed substep plan are handled separately). Light writers have no mid-run heartbeat. | `bo_karanajala` (max 1091 s), `ka_kalasutra` (650 s) could be reaped mid-transaction; the transaction is not committed so no partial rows, but the asset reads `error` | S1 runs `bo_karanajala` with the two global assets and is watched; `ka_sangam` has substeps (heartbeat per substep) so it is covered; native decides on the watchdog cadence for the window |
| R-8 | Another lane dispatches on the chart | run 8684032d at 14:57Z | 409 `RUN_ACTIVE` for us, or a collision if checked late | check #3 at launch; coordinate (Q8) |
| R-9 | Global assets: `bg_transit_rules` (upsert) is shared by every chart | section 2 | a changed seed would reach all charts | expected `skip_no_delta` (estimate); if it executes, diff `bg_transit_rules` and `bg_transit_engine` (76 / unknown rows) before continuing; `super_admin` only; Q3 |
| R-10 | `ka_gochara` is Gochara-family adjacent: its registry `count_sql` is misdirected (reads generation 4.0 of `kala_gochara_windows`, 0 rows; the writer's table is `kala_gochara_windows_v2` generation 2.0, 87 rows) | section 2 | the cockpit count cannot confirm it; a run is blocked by the Pravāha lane if it holds the chart | include only if SS confirms ownership (Q5); needed because `ka_sangam` depends on it |
| R-11 | Code/image skew | check #7 | run fails closed (`code digest` mismatch) | confirm image tag before launch |

### 7.2 What a failed mid-wave state looks like, and how to resume

- Each light writer is ONE transaction on the run's connection: if its integrity SQL is false or it raises, the whole write rolls back, the
  asset's throughput is set `error` with the text in `last_error` and `build_run_assets.error`, and the old rows remain. Heavy writers (`ka_sangam`,
  `ka_gochara`) commit per substep (`build_substep_progress`), so a failure leaves a partial new generation for that asset and a
  resumable plan (a rerun with the same fingerprint skips completed substeps).
- A dependent of a failed asset is not executed: `state='error'`, `disposition='blocked_dependency'`, `blocked_by_asset_id` set (Track I item I-3: the
  throughput row reads `error`, indistinguishable from a root cause unless `disposition` is joined). A writer over its budget is recorded as its own
  `TIMEOUT` error, not as a block.
- The mid-wave database is a PREFIX of the order with new rows and a suffix with old rows; consumers reading across the boundary see mixed
  generations (for example new `phala_anchors` with old `phala_pramana`). Hence the stage boundaries in section 8: stop lines where every asset
  upstream of the next stage is complete.
- Resume: dispatch a new run for the unfinished set. `action='build'` selects assets that are not lit-and-fresh (including `error`, `incomplete`,
  `dormant`); `action='rebuild'` forces all named. A new run is a new frozen manifest, so the registry/digest checks run again. A stuck `running` run
  is reaped by the watchdog after its thresholds (R-7) and by `orphan-cleanup` at the next dispatch (assets `building` become `error`
  `orphaned_by_crash`).
- Stop: `build_runs.stop_requested_at` / pause are honoured between assets (`check_signals`), not mid-asset.

### 7.3 What is NOT reversible

Delete-then-insert for every table in section 2. For the 14 `bodha_*` tables the L2 producer-generation contract (migration 1036) keeps immutable
generation history and describes selection/rollback, but `data_plane_l2_producer_generations` is not readable by the reader and the rollback path
was not exercised here. For all other tables recovery means a native-held database restore point (Q6); nothing in the repository restores them.
The before-state method is: F1/F3/F4 stored in the evidence directory (row counts and per-table md5 of ordered content; no table dump, in
particular none of protected data).

### 7.4 Consequences for consumers during the window

- Only the canonical chart's builds are affected. The orchestrator takes the chart advisory lock and the unique index allows one active run per chart;
  while a producer is not lit-and-fresh, any other build that declares it fails DEP-ASSERT `deps_unsatisfied` (enforce). The window is the run time
  (section 6: critical path about 10 min median to 92 min maximum, plus stage gaps if staged).
- Assets that flip lit to stale because of this wave: up to the 5 in section 1.4 (conditional on a changed output). Assets that flip stale or error to lit:
  the plan assets themselves.
- Served reads continue throughout; they see old rows until a writer's transaction commits, then new rows. `kala_*` and `phala_*` for this chart are
  largely empty today, so served readers currently return empty/degenerate Kāla and Phala; after the wave they return populated rows.
- **Nirmāṇa-frozen assets in the plan** (`NIRMANA_SUPERSESSION_RECORD_v1_0.md` section 2): `bg_transit_rules` t0, `ka_muhurta_seva` t0, `bo_karanajala` t3,
  `bo_pratijna` t1, `bo_drishti` t1, `bo_anveshana` t2, `bo_cgm_motifs` t1, `bo_cgm_paths` t1, `bo_upaya` t1, `ka_gochara` t1, `ka_yojaka` t2.
  The frozen manifests of `bo_karanajala`, `bo_pratijna`, `ka_yojaka` are already stale after migration 1210 (their `depends_on` changed; the freeze
  contract includes it), so their `asset_analysis_accepted` evidence no longer matches the registry fingerprint (per the 1210 header). A rebuild changes
  their live output (or re-stamps it), so the frozen/accepted state describes data that will no longer exist. The cockpit planner and runner read
  here do not consult Nirmāṇa definitions, so frozen status does not stop this run; the Nirmāṇa campaign is OFF (native 2026-09-28), so no dispatcher
  will contest it. NOT frozen: `ka_avadhi`, `ka_vighnakara`, `ka_sangam`, `ka_kalasutra`, `ka_kala_darshana`, `ka_bhavishya_lekha`, every `ph_*`,
  `mi_bhavisya`. `ka_tulana` (t2, frozen) is downstream of `ka_vighnakara`, outside the plan, and stays stale.

## 8. LAUNCH METHOD (needs SS REVIEW) and who executes

**Does a launch path exist for this lane today? No.**

- E5.3 (level-wave script through the build broker) and E7.1-E7.3 (builder identity, provisioning, `builder_scope` monitor) are marked superseded in
  `plan_model.json` by S0.C6 ("the scratch build, validator and publisher", `done_by: event`, stage >= 2, depends on S0.DG) and the broker/builder by
  `X.publish.contract`; none exists on main (no `suvarna_level_wave.py`, no `nikasha_*.py`, no `expect_job_image_tag` or `builder_scope` anywhere in
  `platform/`); N-1 (the activation decision) is not in `DECISIONS.jsonl`; `P.1` (publisher DB identity) is unprovisioned.
- What exists is the product's own path: (A) the cockpit `POST /api/cockpit/runs`, executed by a signed-in chart owner or `super_admin`; (B) the
  native's `platform/scripts/dispatch_*.py` pattern (a Cloud SQL Auth Proxy session inserting `build_runs`, then `gcloud run jobs execute
  brahma-build-pipeline-job`), which needs production write credentials and bypasses the planner's preflight. This lane holds neither.

**Recommended method: (A), staged, by the native (or an owner/super_admin SS designates), after the P0 gate.** Each stage is its own run, so the
unique-index guard serialises them and the planner's preflight becomes the gate between stages.

| Run | Request body (`POST /api/cockpit/runs`, `scope:"asset_set"`, `action:"rebuild"`, `chart_id:"482012f1-710e-4a25-994a-93821f5871aa"`) `scope_target` | Gate before next run |
|---|---|---|
| S0 smoke | `ka_tithi_pravesha` | P0.4 criteria 1-6 |
| S1 | `bg_transit_rules,ka_muhurta_seva,bo_karanajala` (`super_admin` required: two global assets) | all three `complete`; `bo_karanajala.output_changed` FALSE (else add the contingency set); F1 |
| S2 | `bo_pratijna,bo_drishti,bo_cgm_motifs,bo_cgm_paths,bo_anveshana,bo_upaya` | all `complete`; 1211-verify Q4 for `bo_pratijna` |
| S3 | `ka_gochara,ka_yojaka,ka_sangam` (+ `ka_avadhi` only after the I-1 fix is merged and deployed) | `ka_yojaka` lit/fresh/proven; `ka_sangam` freshness recorded (B-2: needs `fresh`, else S4+ cannot pass) |
| S4 | `ka_kalasutra,ka_vighnakara,ka_kala_darshana,ka_bhavishya_lekha` | needs Q1 and Q2 resolved (B-1, B-2) and the I-2 fix deployed |
| S5 | `ph_nimitta,ph_muhurta,ph_pratikara,ph_sankrama,ph_sodhana,ph_suddha_sodhana,ph_pramana,ph_phaladesa` | needs the phala_ grants (P0.2) and B-1/B-2 resolved; `phala_anchors` about 139 |
| S6 | `mi_bhavisya` | `mimamsa_*` grants; orphan check = 0; 1211-verify Q4 for all four producers, then 1211 may be proposed |

Clicks (if the cockpit UI is used instead of a raw call): Nirmāṇa cockpit page for the chart -> select the asset list of the stage -> action
"Rebuild" -> confirm the plan preview (it shows `plan`, `asset_count`, `job_image_tag`) -> submit; do not tick "clear before build". The response
`run_id` is then followed in `build_runs` / `build_run_assets` with the F7 queries. If the planner answers `UPSTREAM_BLOCKED`, the `blockers` list is the
exact set to add or the exact gate that failed; do not retry blindly.

Who executes: the native, or an owner/`super_admin` session SS designates; this lane cannot launch a production build and must not. Before any
launch SS reviews this document and records the decision (REVIEW) and the pre-flight in section 5 is run by the executor.

## 9. OPEN QUESTIONS FOR SS

1. **B-1.** `ka_vighnakara` has no output-digest spec (migration 1034 calls it a blocked contract: no stable non-null unique key in `kala_obstruction`). Decide:
   design a key and spec (a migration; not drafted here), or change the contract so `ka_bhavishya_lekha` and the consumers need not hold a proven
   `ka_vighnakara` (which also changes 1211's premise). Without one of these `ph_nimitta`, `ph_pramana`, `ph_phaladesa`, `mi_bhavisya` cannot become proven.
2. **B-2.** `ka_sangam` declares services `ka_muhurta_seva` and `ka_dasha_kala` whose receipts carry no `output_digest`, so its upstream digest is NULL and its
   receipt 'unknown'. Is the intended contract that a healthy writer-backed service yields a probe digest (the `compute_upstream_hash` comment says so)? If yes, those two
   service receipts need to be produced; if no, the gate for `ka_sangam` consumers must be re-stated. A one-asset rehearsal of this path off production is cheap.
3. **Global assets in a canonical-chart wave.** `bg_transit_rules` and `ka_muhurta_seva` are global and need `super_admin`; the campaign plan keeps L0 as separate
   global-grant waves. Is a global re-stamp inside this wave acceptable, or should the registry-changed receipts of the L0 assets be cleared by the L0 wave first (S1 then shrinks to `bo_karanajala`)?
4. **Protected-table definition.** `bodha_*` tables are `data_plane_l2_owner` tables and 7 plan assets write them (through the L2 generation contract). Does "no protected table"
   cover them? If yes, S2 and `bo_pratijna` itself fall out of this wave.
5. **Ownership of `ka_gochara`** (Gochara/Pravāha family adjacency; the 8684032d run on `ka_gochara_resonance` suggests an L3 lane is active there). May this wave rebuild `ka_gochara`, or does that lane do it first?
6. **Restore point.** Is a native-held Cloud SQL backup/PITR marker taken before S1 (this lane cannot see or create one)? Without it every stage is irreversible.
7. **Why are the canonical L3 rows empty?** `kala_convergence`, `kala_obstruction`, `kala_activation`, `kala_darshana`, `kala_bhavishya`, `phala_sodhana` hold 0 canonical rows while their last real builds wrote 14868, 536, 335403, 750, 100 and 97. Cleared by a lane, a correction, or lost? The plan assumes "cleared, to be rebuilt".
8. **Coordination.** Another lane planned a canonical-chart run today (8684032d, 14:57Z). Who holds the chart's build slot during the window, and is Pravāha's grant migration the only fix on the way?
9. **Split decision.** If the phala_/mimamsa_ grants are not coming soon, do we launch Stages S0-S3 (Bodha and Kāla core) and defer S4-S6, or hold the whole wave?
10. **Timing vs deploy.** The wave must not straddle a deploy (the image changes mid-run; the digest check then fails closed). Is the window to be scheduled after the L3 fix PR #2823 deploys, with a deploy freeze for about 4 hours?
11. **Action semantics.** `rebuild` (explicit) vs `build` (planner picks non-fresh): equal for this set by construction; `rebuild` is used. Confirm, and confirm `NIRMANA_FORCE_EXECUTE` stays unset so unchanged inputs delta-skip rather than rewrite.

## Evidence appendix

All queries were run as `suvarna_reader` through the approved wrapper (`( source <pgenv> ; psql -X -A -F'|' -c ... )`), SELECT only; no credential was
printed. Files are under `/Users/Dev/suvarna-evidence/Rebuild/` (outputs are reproduced below, trimmed where long). Timestamps are UTC, 2026-10-01.
Tables the reader could not read (permission denied, not worked around): `bodha_contradictions`, `bodha_cgm_sub_graphs`,
`bodha_cgm_chart_topology_summary`, `bodha_rm_dasha_windowed_prescriptions`, `bodha_rm_chart_summary`, `bodha_rm_dosha_remedy_bundles`,
`bodha_rm_pattern_remedies`, `data_plane_l2_producer_generations`. Repo evidence is from `origin/main` 3311b0a06 (worktree
`/Users/Dev/suvarna-lane-rebuildplan`).

### E1. Identity and clock (14:48:11Z)
```
select now(), current_user  ->  2026-10-01 14:48:11.96+00 | suvarna_reader
```

### E2. Registry, migrations (14:49Z)
```sql
select count(*), md5(string_agg(asset_id||'>'||coalesce(depends_on::text,''),',' order by asset_id)) from asset_registry where is_active;
-- 127 | fb7a1090d5aa3c7dabafc9f9daf1ae6a
select filename, applied_at from _migrations_applied order by applied_at desc limit 2;
-- 1210_asset_registry_direct_edges.sql | 2026-10-01 14:37:09.977838+00 ; 1203_ai_metering_receipt_fk_permission.sql | 2026-10-01 10:47:25
select asset_id, depends_on, writer_timeout_seconds from asset_registry where asset_id in (<the 8 named>);   -- live depends_on as read; held 1211 edges are NOT present
```

### E3. State of the 8 named assets and the planner-preflight simulation for exactly those 8 (2026-10-01T15:13:05Z)
```sql
select t.asset_id, t.state, to_char(t.last_built_at,'YYYY-MM-DD HH24:MI') lb, t.rows_written rw, round(t.duration_seconds::numeric,1) dur, f.freshness_state fr, to_char(f.observed_at,'MM-DD HH24:MI') fobs, r.receipt_state rs, to_char(r.observed_at,'MM-DD HH24:MI') robs, left(r.output_digest,10) od
from asset_throughput t
left join asset_freshness f on f.asset_id=t.asset_id and f.chart_id=t.chart_id
left join asset_provenance_receipts r on r.asset_id=t.asset_id and r.chart_id=t.chart_id
where t.chart_id='482012f1-710e-4a25-994a-93821f5871aa' and t.asset_id in ('ph_phaladesa','ph_pramana','mi_bhavisya','ph_nimitta','bo_pratijna','ka_yojaka','ka_avadhi','ka_vighnakara') order by 1
```
```
asset_id|state|lb|rw|dur|fr|fobs|rs|robs|od
bo_pratijna|stale|2026-09-09 16:29|135||stale|10-01 14:37|proven|09-09 16:29|ee3dc90b4f
ka_avadhi|error|2026-09-10 19:10|1169||||||
ka_vighnakara|stale|2026-08-13 01:08|536||||||
ka_yojaka|stale|2026-09-10 17:17|50678||stale|10-01 14:37|proven|09-10 17:49|3fd3b490ec
mi_bhavisya|error|2026-08-21 02:36|278||||||
ph_nimitta|stale|2026-08-13 01:16|139||||||
ph_phaladesa|stale|2026-08-13 01:16|13||||||
ph_pramana|stale|2026-08-13 01:16|139||||||
(8 rows)
```
Preflight simulation (`preflight_sim.sql`: `plan.ts preflight` for asset_set = direct out-of-plan dependencies, using `loadPlanningInputs`' DISTINCT ON latest-row logic;
a dep is ready iff throughput in (lit,service_ok) AND latest freshness 'fresh'). Input: the 8 ids; 2026-10-01T15:13:05Z:
```sql
-- Simulates plan.ts preflight (asset_set => direct out-of-plan deps only) for a candidate set, using loadPlanningInputs' DISTINCT ON logic
with cand(a) as (select unnest(string_to_array(:'cands', ','))),
tp as (select distinct on (asset_id) asset_id, state from asset_throughput where chart_id='482012f1-710e-4a25-994a-93821f5871aa' or chart_id is null order by asset_id, (chart_id='482012f1-710e-4a25-994a-93821f5871aa') desc nulls last),
fr as (select distinct on (asset_id) asset_id, freshness_state fs, reasons from asset_freshness where chart_id='482012f1-710e-4a25-994a-93821f5871aa' or chart_id is null order by asset_id, (chart_id='482012f1-710e-4a25-994a-93821f5871aa') desc nulls last, observed_at desc),
deps as (select c.a cand, d dep from cand c join asset_registry r on r.asset_id=c.a cross join lateral unnest(r.depends_on) d where d not in (select a from cand))
select deps.dep, ar.layer, ar.asset_kind, coalesce(tp.state,'<none>') thr, coalesce(fr.fs,'<none>') fresh, string_agg(deps.cand, ',') required_by
from deps join asset_registry ar on ar.asset_id=deps.dep left join tp on tp.asset_id=deps.dep left join fr on fr.asset_id=deps.dep
group by 1,2,3,tp.state,fr.fs order by (coalesce(tp.state,'<none>')='lit' and coalesce(fr.fs,'<none>')='fresh'), 1
```
```
dep|layer|asset_kind|thr|fresh|required_by
bg_transit_rules|brahmagyan|data|lit|stale|ka_yojaka
bo_anveshana|bodha|data|stale|fresh|ph_nimitta
bo_cgm_paths|bodha|data|stale|fresh|ph_nimitta
bo_karanajala|bodha|data|lit|stale|ph_nimitta
ka_bhavishya_lekha|kala|artifact|stale|<none>|ph_nimitta
ka_muhurta_seva|kala|service|lit|<none>|ka_vighnakara
ka_sangam|kala|artifact|stale|<none>|ph_nimitta,ka_vighnakara
ph_muhurta|phala|artifact|stale|<none>|ph_phaladesa,ph_pramana
ph_pratikara|phala|artifact|stale|<none>|ph_phaladesa,ph_pramana
ph_sankrama|phala|artifact|stale|<none>|ph_pramana,ph_phaladesa
ph_sodhana|phala|artifact|stale|<none>|ph_pramana
ph_suddha_sodhana|phala|artifact|stale|<none>|ph_pramana,ph_phaladesa
bg_dignity_reference|brahmagyan|data|lit|fresh|ka_vighnakara
bg_ghatana|brahmagyan|data|lit|fresh|ka_yojaka,ka_avadhi
bo_bimba|bodha|data|lit|fresh|ph_nimitta,ka_yojaka
bo_laksana|bodha|data|lit|fresh|ka_yojaka,ph_nimitta,ph_phaladesa,bo_pratijna,mi_bhavisya
bo_samskara|bodha|data|lit|fresh|ph_nimitta
bo_sangati|bodha|data|lit|fresh|ka_yojaka,ph_nimitta,bo_pratijna
ga_dashas|ganita|data|lit|fresh|ka_avadhi,ka_vighnakara,ka_yojaka
ga_positions|ganita|data|lit|fresh|ka_vighnakara
ga_vargas|ganita|data|lit|fresh|bo_pratijna
ga_yoga|ganita|data|lit|fresh|ka_yojaka
mi_jivanaghatana|mimamsa|data|lit|fresh|mi_bhavisya
mi_kula|mimamsa|data|lit|fresh|mi_bhavisya
(24 rows)
```
Not ready (first 12 rows): bg_transit_rules, bo_anveshana, bo_cgm_paths, bo_karanajala, ka_bhavishya_lekha, ka_muhurta_seva, ka_sangam, ph_muhurta,
ph_pratikara, ph_sankrama, ph_sodhana, ph_suddha_sodhana. (`ka_muhurta_seva` is a service with no freshness row, B-3.)

### E4. Upstream closure and the minimal plan
Closure (recursive CTE over `asset_registry.depends_on`, 71 assets) and its state (2026-10-01T15:13:06Z; 47 of 71 have no `lit` chart-scoped row, of which 19 are global
assets with no chart-scoped row at all (17 L0 `bg_*`, `ka_muhurta_seva`, `mi_kula`), so 28 are non-lit by state alone; section 1.2's 27/28 counts 'not lit-and-fresh', which also includes lit assets with stale receipts):
```sql
with recursive w(a) as (select unnest(array['ph_phaladesa','ph_pramana','mi_bhavisya','ph_nimitta','bo_pratijna','ka_yojaka','ka_avadhi','ka_vighnakara'])),
up(a, d, depth) as (
 select w.a, w.a, 0 from w
 union
 select up.a, x.dep, up.depth+1 from up join asset_registry r on r.asset_id=up.d cross join lateral unnest(coalesce(r.depends_on,'{}')) x(dep)
)
select distinct d as asset from up order by 1;
```
Minimal-plan fixpoint (Python over a read-only export of `asset_registry` + latest throughput/freshness + spec existence, `reg_state.json`; `fixpoint_v2.py`
`ready()` and `fixpoint2_v2.py`):
```
start P = the 8; repeat: for a in P, for each direct dep p not in P and not ready(p): add p.
ready(p) = throughput in (lit, service_ok) and latest freshness == fresh; services: freshness row must exist (fresh, or unknown in the writer-self-test shape).
```
Result, 26 assets in dependency order (`Pstar26.json`):
```
bg_transit_rules, bo_karanajala, bo_drishti, bo_anveshana, bo_cgm_motifs, bo_cgm_paths, bo_pratijna, bo_upaya, ka_avadhi, ka_gochara, ka_muhurta_seva, ka_yojaka, ka_sangam, ka_kalasutra, ka_vighnakara, ka_kala_darshana, ka_bhavishya_lekha, ph_nimitta, ph_muhurta, ph_pratikara, ph_sankrama, ph_sodhana, ph_suddha_sodhana, ph_pramana, ph_phaladesa, mi_bhavisya
```
Same-plan preflight simulation (P26): 0 out-of-plan blockers (only the accepted service `ka_dasha_kala`); file `preflight_sim_P26.txt`.
Assets with no output-digest spec in the closure (`closure_spec.sql`): `ka_vighnakara` (artifact), and the services `ka_dasha_kala`, `ka_muhurta_seva`, `bg_panchanga`.

### E5. Row counts (registry `count_sql` with `$1` = the canonical chart; and direct `count(*) ... WHERE chart_id=`)
`counts_before.txt` (2026-10-01T14:54:40Z), registry `count_sql` per asset:
```
/Users/Dev/suvarna-evidence/Rebuild/counts.py:8: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
  print(datetime.datetime.utcnow().isoformat()+'Z', file=sys.stderr)
2026-10-01T14:54:40.780572Z
bg_transit_rules | 76
bo_karanajala | 849
bo_drishti | 60
bo_anveshana | 4437
bo_cgm_motifs | 600
bo_cgm_paths | 45
bo_pratijna | 135
bo_upaya | 180
ka_avadhi | 1169
ka_gochara | 0
ka_yojaka | 50678
ka_sangam | 0
ka_kalasutra | 0
ka_vighnakara | 0
ka_kala_darshana | 0
ka_bhavishya_lekha | 0
ph_nimitta | 4
ph_muhurta | 134
ph_pratikara | 536
ph_sankrama | 155
ph_sodhana | 0
ph_suddha_sodhana | 4
ph_pramana | 4
ph_phaladesa | 13
mi_bhavisya | 278
```
`counts_tables_before.txt`:
```
2026-10-01T15:02:49Z
bodha_cgm_edges|849
bodha_contradictions|ERROR:  permission denied for table bodha_contradictions
bodha_question_lenses|60
bodha_discoveries|1161
bodha_anomalies|3276
bodha_cgm_motifs|600
bodha_cgm_sub_graphs|ERROR:  permission denied for table bodha_cgm_sub_graphs
bodha_cgm_chart_topology_summary|ERROR:  permission denied for table bodha_cgm_chart_topology_summary
bodha_cgm_paths|45
bodha_pratijna|135
bodha_rm_resonances|45
bodha_rm_remedy_prescriptions|135
bodha_rm_dasha_windowed_prescriptions|ERROR:  permission denied for table bodha_rm_dasha_windowed_prescriptions
bodha_rm_chart_summary|ERROR:  permission denied for table bodha_rm_chart_summary
bodha_rm_dosha_remedy_bundles|ERROR:  permission denied for table bodha_rm_dosha_remedy_bundles
bodha_rm_pattern_remedies|ERROR:  permission denied for table bodha_rm_pattern_remedies
kala_avadhi|1169
kala_gochara_windows_v2|1001
kala_activation_predicates|50678
kala_convergence|0
kala_activation|0
kala_obstruction|0
kala_darshana|0
kala_bhavishya|0
phala_anchors|4
phala_muhurta|134
phala_mitigation|536
phala_sankrama|155
phala_sodhana|0
phala_suddha_sodhana|4
phala_pramana|4
phala_phaladesa|13
mimamsa_predictions|139
mimamsa_manifestation_sets|139
```
Other charts (`counts_all_charts_before.txt`):
```
kala_obstruction: 1c826d5a=741, cb73cd3d=6
kala_convergence: 1c826d5a=17957, cb73cd3d=2540
kala_activation: 1c826d5a=336093, cb73cd3d=1055
kala_darshana: 1c826d5a=750
kala_bhavishya: 1c826d5a=100
kala_activation_predicates: 1c826d5a=50171, 482012f1=50678, cb73cd3d=49875
kala_avadhi: 1c826d5a=1160, 482012f1=1169, cb73cd3d=1291
phala_anchors: 1c826d5a=56, 482012f1=4
phala_sodhana: 1c826d5a=41
phala_muhurta: 1c826d5a=49, 482012f1=134
mimamsa_predictions: 1c826d5a=56, 482012f1=139
bodha_pratijna: 1c826d5a=135, 482012f1=135, cb73cd3d=135
(taken 2026-10-01T14:58:00Z)
```
Other facts read: `mimamsa_predictions` = 139, all `lifecycle_status='pending'`; 139 of 139 predictions have no matching `phala_anchors` row (`'pred_'||anchor_id`);
`kala_gochara_windows_v2` generations: `2.0` = 87, `g3_utkarsha` = 914; `kala_gochara_windows`: `3.0` = 914, `v1` = 16297; `chart_facts` 143299; `chart_dashas` 483870;
`bodha_msr_signals` 50678; `kala_avadhi` notes non-null 1043 of 1169, note digest `a041ac2f18c66a677e52b168518fec25` (15:08:12Z).

### E6. Timing history (`timing.sql`, chart 482012f1, state complete, skip_no_delta excluded)
```sql
select a.asset_id, count(*) n_complete,
 round(percentile_cont(0.5) within group (order by extract(epoch from (a.ended_at-a.started_at)))::numeric,1) med_s,
 round(max(extract(epoch from (a.ended_at-a.started_at)))::numeric,1) max_s,
 to_char(max(a.ended_at),'MM-DD') last_complete
from build_run_assets a join build_runs r on r.id=a.run_id
where r.chart_id='482012f1-710e-4a25-994a-93821f5871aa' and a.state='complete' and coalesce(a.disposition,'build')<>'skip_no_delta' and a.started_at is not null and a.ended_at is not null
 and a.asset_id = any(string_to_array(:'assets',','))
group by 1 order by 1
```
```
asset_id|n_complete|med_s|max_s|last_complete
bg_transit_rules|2|0.0|0.0|09-04
bo_anveshana|20|24.4|373.8|09-10
bo_cgm_motifs|21|8.0|100.0|09-09
bo_cgm_paths|20|1.3|25.5|09-09
bo_drishti|19|74.0|175.7|09-09
bo_karanajala|22|20.6|1091.4|09-11
bo_pratijna|21|15.0|52.1|09-09
bo_upaya|23|12.9|75.7|09-09
ka_avadhi|23|11.3|60.6|08-12
ka_bhavishya_lekha|22|0.3|2.2|08-13
ka_gochara|7|1.0|142.5|09-10
ka_kala_darshana|21|0.3|3.5|08-13
ka_kalasutra|22|46.7|650.5|08-13
ka_sangam|22|477.6|4389.8|08-13
ka_vighnakara|20|15.9|86.5|08-13
ka_yojaka|23|33.6|97.6|09-10
mi_bhavisya|19|1.2|15.6|08-13
ph_muhurta|22|0.7|19.7|08-13
ph_nimitta|23|2.1|58.8|08-13
ph_phaladesa|20|1.1|8.3|08-13
ph_pramana|20|0.5|24.4|08-13
ph_pratikara|22|2.8|55.5|08-13
ph_sankrama|22|2.3|211.7|08-13
ph_sodhana|20|0.3|11.0|08-13
ph_suddha_sodhana|20|0.5|15.3|08-13
(25 rows)
```
(`ka_muhurta_seva`: 3 completed, median 0.2 s, max 1.0 s.) Single-asset completed runs since 2026-09-01: n=128, median 25 s creation-to-end, min 6 s, max 1675 s; median 3 s start-to-end.
Sum of medians 755 s, sum of maxima 7749 s, critical path 581 s median / 5514 s maximum (python over the plan DAG).

### E7. Builder audit grant, privileges, runs (2026-10-01T15:13:20Z)
```
-- run at 2026-10-01T15:13:20Z
-- E7.a trigger
select tgname, tgenabled, pg_get_triggerdef(oid) from pg_trigger where tgrelid='asset_throughput'::regclass and not tgisinternal;
tgname|tgenabled
trg_asset_throughput_state_audit|O
trg_asset_throughput_no_chart_scoped_global|O
(2 rows)
-- E7.b function
select proname, prosecdef, pg_get_userbyid(proowner) from pg_proc where proname='_record_asset_throughput_state_change';
proname|prosecdef|pg_get_userbyid
_record_asset_throughput_state_change|f|amjis_app
(1 row)
-- E7.c ACLs
select relname, relacl::text from pg_class where relname in ('asset_throughput_state_audit','asset_throughput_state_audit_id_seq');
relname|relacl
asset_throughput_state_audit|{amjis_app=arwdDxt/amjis_app,retrieval_census_ro=r/amjis_app,suvarna_reader=r/amjis_app}
asset_throughput_state_audit_id_seq|{amjis_app=rwU/amjis_app}
(2 rows)
-- E7.d privileges
select has_table_privilege('data_plane_builder','public.asset_throughput_state_audit','INSERT'), has_sequence_privilege('data_plane_builder','public.asset_throughput_state_audit_id_seq','USAGE'), has_table_privilege('data_plane_builder','public.asset_throughput','UPDATE');
ins|seq|thr_upd
f|f|t
(1 row)
-- E7.e build_runs by state
select state, count(*), max(created_at), max(ended_at) from build_runs group by 1;
state|count|c|e
failed|419|2026-10-01 14:57|2026-10-01 15:01
completed|302|2026-09-12 01:44|2026-09-12 01:47
stopped|14|2026-08-13 14:09|2026-08-13 16:03
(3 rows)
-- E7.f audit by db_user
select db_user, count(*), max(changed_at) from asset_throughput_state_audit group by 1;
db_user|count|to_char
amjis_app|695|2026-09-12 01:44
(1 row)
-- E7.g run 8684032d
select state, current_asset_id, last_error, created_at, started_at, ended_at from build_runs where id='8684032d-a687-4943-939b-bbc51c53917c';
state|current_asset_id|last_error|c|started_at|e
failed|||14:57:39|2026-10-01 15:01:18.401418+00|15:01:19
(1 row)
-- E7.h active runs
select id,state from build_runs where state in ('planned','running','paused');
id|state
(0 rows)
```
Privilege matrix for `data_plane_builder` (`privs.sql`; `has_table_privilege`, `has_sequence_privilege` on owned sequences; 2026-10-01T15:13:27Z):
```sql
with t(tbl) as (values
('asset_throughput'),('asset_throughput_state_audit'),('build_runs'),('build_run_assets'),('build_substep_progress'),('asset_registry'),('asset_provenance_receipts'),('asset_freshness'),('asset_output_digest_specs'),('charts'),('chart_facts'),('chart_dashas'),
('bg_transit_rules'),('bg_transit_engine'),
('bodha_cgm_edges'),('bodha_cgm_nodes'),('bodha_contradictions'),('bodha_question_lenses'),('bodha_discoveries'),('bodha_anomalies'),('bodha_cgm_motifs'),('bodha_cgm_sub_graphs'),('bodha_cgm_chart_topology_summary'),('bodha_cgm_paths'),('bodha_pratijna'),
('bodha_rm_resonances'),('bodha_rm_remedy_prescriptions'),('bodha_rm_dasha_windowed_prescriptions'),('bodha_rm_chart_summary'),('bodha_rm_dosha_remedy_bundles'),('bodha_rm_pattern_remedies'),
('kala_avadhi'),('kala_gochara_windows_v2'),('kala_activation_predicates'),('kala_convergence'),('kala_activation'),('kala_obstruction'),('kala_darshana'),('kala_bhavishya'),
('phala_anchors'),('phala_muhurta'),('phala_mitigation'),('phala_sankrama'),('phala_sodhana'),('phala_suddha_sodhana'),('phala_pramana'),('phala_phaladesa'),
('mimamsa_predictions'),('mimamsa_manifestation_sets'))
select tbl,
 has_table_privilege('data_plane_builder', 'public.'||tbl, 'SELECT') s,
 has_table_privilege('data_plane_builder', 'public.'||tbl, 'INSERT') i,
 has_table_privilege('data_plane_builder', 'public.'||tbl, 'UPDATE') u,
 has_table_privilege('data_plane_builder', 'public.'||tbl, 'DELETE') d,
 coalesce((select string_agg(has_sequence_privilege('data_plane_builder', s.oid, 'USAGE')::text, ',') from pg_class s join pg_depend dp on dp.objid=s.oid and dp.deptype in ('a','i') join pg_class tc on tc.oid=dp.refobjid where s.relkind='S' and tc.oid=('public.'||tbl)::regclass),'-') seq_usage
from t order by 1
```
```
tbl|s|i|u|d|seq_usage
asset_freshness|t|f|f|f|-
asset_output_digest_specs|t|f|f|f|-
asset_provenance_receipts|t|t|t|f|-
asset_registry|t|f|f|f|-
asset_throughput|t|t|t|t|-
asset_throughput_state_audit|f|f|f|f|false
bg_transit_engine|t|t|t|t|true
bg_transit_rules|t|t|t|t|true
bodha_anomalies|t|t|t|t|-
bodha_cgm_chart_topology_summary|t|t|t|t|-
bodha_cgm_edges|t|t|t|t|-
bodha_cgm_motifs|t|t|t|t|-
bodha_cgm_nodes|t|t|t|t|-
bodha_cgm_paths|t|t|t|t|-
bodha_cgm_sub_graphs|t|t|t|t|-
bodha_contradictions|t|t|t|t|-
bodha_discoveries|t|t|t|t|-
bodha_pratijna|t|t|t|t|-
bodha_question_lenses|t|t|t|t|-
bodha_rm_chart_summary|t|t|t|t|-
bodha_rm_dasha_windowed_prescriptions|t|t|t|t|-
bodha_rm_dosha_remedy_bundles|t|t|t|t|-
bodha_rm_pattern_remedies|t|t|t|t|-
bodha_rm_remedy_prescriptions|t|t|t|t|-
bodha_rm_resonances|t|t|t|t|-
build_run_assets|t|t|t|t|-
build_runs|t|t|t|t|-
build_substep_progress|t|t|t|t|-
chart_dashas|t|t|t|t|-
chart_facts|t|t|t|t|-
charts|t|f|f|f|-
kala_activation|t|t|t|t|true
kala_activation_predicates|t|t|t|t|true
kala_avadhi|t|t|t|t|-
kala_bhavishya|t|t|t|t|true
kala_convergence|t|t|t|t|true
kala_darshana|t|t|t|t|true
kala_gochara_windows_v2|t|t|t|t|true
kala_obstruction|t|t|t|t|true
mimamsa_manifestation_sets|f|f|f|f|-
mimamsa_predictions|f|f|f|f|-
phala_anchors|f|f|f|f|-
phala_mitigation|f|f|f|f|-
phala_muhurta|f|f|f|f|-
phala_phaladesa|f|f|f|f|-
phala_pramana|f|f|f|f|-
phala_sankrama|f|f|f|f|-
phala_sodhana|f|f|f|f|-
phala_suddha_sodhana|f|f|f|f|-
(49 rows)
```
(`asset_registry` UPDATE is column-level for `service_health`, `last_invoked_at`, `last_selftest_at` only: `has_column_privilege` true for those three, false for `depends_on`.)
Smoke-asset facts (`ka_tithi_pravesha`, `ka_sudarshana_varsha`): lit 2026-09-07 21:18, fresh, receipt proven (801e0b279283 / dfdcd5ca43f6), 120 rows each, leaf assets,
`depends_on = {ga_positions}`, `writer_timeout_seconds` 120 / 60; `ga_positions` latest receipt proven 2026-09-07 08:37:20.895985Z, equal to the upstream recorded in
`ka_tithi_pravesha`'s receipt; its last executions: `skip_no_delta` 0.0-0.2 s (09-07), `build` 0.0 s, 1.8 s. Downstream sizes: `bg_panchanga` 57 assets, `bg_ephemeris_engine` 4.

### E8. Deploy state (`gh run list --workflow deploy.yml`, 15:09:36Z)
```
2026-10-01T15:04:39Z in_progress  3311b0a06 workflow_run        <- real deploy of main, in progress
2026-10-01T15:04:37Z in_progress  c3257a0fc pull_request        <- build-check only
2026-10-01T14:57:48Z in_progress  c71fdbc9e pull_request
2026-10-01T14:25:28Z completed success 0250cbade workflow_run   <- previous main deploy (earlier listing, 14:56Z)
```

### E9. `ka_avadhi` integrity SQL run read-only against live data (about 14:56-15:00Z; `ics_ka_avadhi_p0..p4.sql`)
`select integrity_check_sql from asset_registry where asset_id='ka_avadhi'` executed as a SELECT: overall `f`. Conjuncts: (a) L1 spine match = t; (b) coverage = t; (c) `lord_condition_fact_refs`
non-empty for nine-graha lords = **f** (1169 of 1169 canonical rows empty); (d) refs resolve = t; (e) `activated_pratijna_ids` resolve to `bodha_pratijna` = **f** (4129 dangling ids).
Failed runs on 2026-09-10 (`build_run_assets.error`): three x `post-write integrity check failed: integrity_check_sql -> False`.

### E10. Digest specs and receipts
`asset_output_digest_specs` rows exist for: bg_transit_rules, bo_pratijna, ka_avadhi, ka_bhavishya_lekha, ka_sangam, ka_yojaka, mi_bhavisya, ph_muhurta, ph_nimitta, ph_phaladesa, ph_pramana,
ph_pratikara, ph_sankrama, ph_sodhana, ph_suddha_sodhana (126 specs in total); none for `ka_vighnakara`, `ka_dasha_kala`, `ka_muhurta_seva`, `bg_panchanga`.
`asset_provenance_receipts` 98 rows / 90 assets; `asset_freshness` 98 rows (57 for the canonical chart: 44 fresh, 12 stale, 1 unknown). Receipts with reason
`upstream_digest_unavailable`: 0 rows.

### E11. Repository evidence (origin/main 3311b0a06)
`platform/src/app/api/cockpit/runs/route.ts`, `platform/src/lib/build/{plan,runPreparation,runDispatch,jobInvoker}.ts`, `platform/src/lib/cloud_run/jobs.ts`,
`platform/python-sidecar/pipeline/orchestrator/{runner,asset_runner,provenance,staleness,output_digest}.py`, `platform/src/app/api/cockpit/watchdog/route.ts`,
`platform/migrations/{1034,1070,1210}_*.sql`, `platform/supabase/migrations/{586,1036}_*.sql`, writers `platform/python-sidecar/pipeline/orchestrator/writers/<asset>.py`
(`grep -E 'DELETE FROM|INSERT INTO|UPDATE'` per file, list in `writer_files.txt`), `00_ARCHITECTURE/briefs/nirmana/NIRMANA_SUPERSESSION_RECORD_v1_0.md`,
`00_ARCHITECTURE/control/suvarna/plan_model.json` (E5.3, E7.1-E7.3 superseded by S0.C6), branches `suvarna/land/TI-edges-002` (1211 held, 086a0fcc5) and
`suvarna/land/TI-i12-narration-001` (no commits ahead of main at 14:51Z), `00_ARCHITECTURE/briefs/suvarna/exec/TRACK_I_FIX_ITEMS.md` (I-1, I-2, I-3).

*End of document.*
