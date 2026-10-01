---
artifact: CANONICAL_CHART_REBUILD_PLAN
version: "1.2"
status: DRAFT-FOR-REVIEW
produced_by: exec-suvarna
date: 2026-10-01
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
base_commit: origin/main 3311b0a06 (worktree opened at 0250cbade, fast-forwarded before commit)
execution: NONE. This is an analysis document. No build, write, admin action, push or PR was made to produce it.
db_access: read-only, as suvarna_reader (SELECT only). Evidence in /Users/Dev/suvarna-evidence/Rebuild/.
revised_against: "branches read via git show origin/<branch>: suvarna/land/grant-plan-001 (PR #2825, BUILDER_GRANT_PLAN v1.3), suvarna/land/incident-divisionals-001 (PR #2833), suvarna/land/TI-i45-provenance-001 (PR #2826), suvarna/land/TI-i8-avadhi-integrity-001 (PR #2827), suvarna/land/F3-msr-fk-drop-001 (PR #2828), suvarna/land/TI-i10-kshetra-substeps-001 (PR #2830); all open and unmerged when read, 2026-10-01 about 16:20Z. v1.2 re-read (E13, 17:40-17:56Z): PR states by gh pr view: #2823 MERGED 15:37:54Z (066c58587), #2828 MERGED 16:49:57Z (9f02ed504), #2834 MERGED 17:00:24Z (4eb40bec1, migration 1211 audit grant); #2825, #2826, #2827, #2830, #2833 still OPEN"
changelog:
  - "1.2 (2026-10-01, SS/Pravaha facts of the same day): (1) P0 grant gate met: Pravaha's builder audit grant migration 1211 is applied (17:35:43Z) and verified, the S0 smoke build (ka_tithi_pravesha) is unblocked and pre-approved; two further builder write-path gaps found read-only (asset_freshness, bg_transit_moorti); (2) our held 5-edge migration renumbered 1211 -> 1216 (every mention); (3) new stage S0b `bg_transit_rules` (global L0) first after S0: it will not delta-skip, it will record output_changed TRUE and flip three canonical lit assets stale; new optional stage S0L for the other non-fresh L0 assets (bg_vedha_malefic_scale becomes required in effect); new conditional stage S0c (Gochara trio refresh); (4) Trap 103 added to the post-deploy verification; (5) order, P0 status, gating tables, risks R-17 to R-20 and questions Q16 to Q19 updated; live re-read in Evidence E13. Docs only: no build, no DB write."
  - "1.1.1 (2026-10-01, SS rulings): v1.1 approved as the working plan; launch set 27, P0b gates S2 and bo_laksana, ka_kshetra (S7) runs last after the held phala_rectification grant gets its own REVIEW, stop rules 15 min no progress / 6 h total accepted; F3 section 5 prerequisite recorded (see the L2 FK drop row). Stage launches still come to SS per stage after P0."
  - "1.1 (2026-10-01, SS rulings): (1) new P0b precondition: chart_divisionals readable and writable by the builder/app roles (the table is RLS-blind since migration 1035), with the ga_vargas decision stated; (2) ka_dasha_kala added to the launch set and ordered ahead of ka_sangam; (3) ka_kshetra gets its own stage S7 with a pre-check, a stop rule and a single-redispatch rule; (4) MSR-before-Kala/Phala ordering invariant (F-3) with the detector scripts, incl. the v4-id charts; (5) grant gates per stage from BUILDER_GRANT_PLAN v1.3 (corrects v1.0 P0.5: S1 and S4 DO need grants); (6) migration gates 1212/1213/1214/1215 mapped to stages; (7) production build remains a REVIEW to SS, no execution authority here. Live values re-read 2026-10-01 about 16:20Z are in Evidence E12; sections changed are listed in the v1.1 box below."
  - "1.0 (2026-10-01): first draft for SS review. Includes the P0 builder-grant precondition and smoke build (coordinator addendum 2) and the I-1/I-2 consumer addendum (coordinator addendum 1)."
---

# Canonical-chart rebuild plan (REVIEW document for SS)

Scope asked by SS (2026-10-01): rebuild the stale and errored producers `ph_phaladesa`, `ph_pramana`, `mi_bhavisya`,
`ph_nimitta`, `bo_pratijna`, `ka_yojaka`, plus the I-1/I-2 consumers `ka_avadhi` and `ka_vighnakara`, so that
(a) live rows are corrected once the L3 writer fixes merge and (b) migration 1216 (5 held `depends_on` edges, branch
TI-edges-002) can be applied after its gate (each of `bo_pratijna`, `ka_yojaka`, `mi_bhavisya`, `ph_nimitta` lit and
fresh and proven, "gate_ok").

Every number below was read from the live DB (query in the Evidence appendix) or from the repo at the cited file; estimates
are labelled "estimate". Code-derived predictions (never observed in production) are labelled "code-derived".

> **v1.1 box (2026-10-01, SS rulings; read this first).** The filename keeps `v1_0`; the frontmatter version is 1.1.
> - **Authority:** this document is still a REVIEW to SS. It carries no execution authority; any production build, grant, migration or access fix named here is a separate act that SS reviews and the owner/executor performs.
> - **Sections added:** P0b (`chart_divisionals` access precondition and the `ga_vargas` decision), P0c (grant and migration gates by stage), 1.5 (MSR-before-Kala/Phala ordering invariant, detector scripts), 1.6 (`ka_dasha_kala` ordering), 8.2 (stage S7 `ka_kshetra`), Evidence E12.
> - **Sections amended:** P0.5 (GO conditions, correction of the "S0-S4 need no grants" claim), 0 (items 1-2 notes), 0.1 (row 1c), 1.3 (wave 0 and wave 1), section 5 (rows 5 and 14-19), 7 (risks R-12 to R-16), 8 (stage table with gates, S0v, S0m, S7), 9 (Q1, Q2, Q9 notes; Q12-Q15 new).
> - **Numbers:** every figure not re-read in v1.1 stays as v1.0 (attributed to its Evidence block); figures taken from the other PRs' documents are attributed to them; live values re-read 2026-10-01 about 16:20-16:28Z are in E12. Where v1.0 says "the 26", it means the v1.0 computed set; the v1.1 launch set adds `ka_dasha_kala` (27).
> - **State when read:** none of PRs #2825 (grants), #2826 (1212, 1213), #2827 (1215), #2828 (1214), #2830 (`ka_kshetra`), #2833 (incident fix, ON HOLD) was merged or applied; P0, P0b and every P0c gate are red (section 5 rows 1, 14-16).

> **v1.2 box (2026-10-01 about 17:40-17:56Z; read this first).** Docs only; no build, no write; DB reads as `suvarna_reader`. Authority unchanged: a REVIEW to SS, no execution authority.
> - **Facts supplied by SS/Pravāha (2026-10-01), taken as given and cross-checked read-only where the DB can show them:** (a) Pravāha's builder audit grant migration 1211 is deployed and verified; the S0 smoke build (`ka_tithi_pravesha`, P0.4) is unblocked and pre-approved; Pravāha pipeline run 1865991c passed its first state change at 17:37Z. (b) Our held 5-edge migration is renumbered 1211 -> 1216. (c) `bg_transit_rules` (global L0) moves to the front as stage S0b; Pravāha's pipeline is blocked on its stale receipt. (d) Other non-fresh global receipts: `bg_ephemeris_engine`, `bg_formula_constants`, `bg_vedha_malefic_scale`, `bg_vidhi_primitives` stale, `bg_panchanga` unknown; only `bg_transit_rules` blocks Pravāha today. (e) SS's L0 ruling: before any wave touches `bg_ephemeris` or `bg_texts`, SS notifies Pravāha; `bg_ephemeris_engine` is the service, not the table, but is flagged. (f) Trap 103: a `success` deploy run listed for a merge sha may have run a different `DEPLOY_SHA`; verify before treating a migration as applied.
> - **Sections added:** P0.6 (P0 status and the verification steps incl. Trap 103), S0b (`bg_transit_rules`), S0L (L0 freshness stage, optional), Evidence E13. **Amended:** P0.5, P0b.1, P0b.3-4, P0c.1-2, 0 (items 0-1), 0.1 (row 1), 1.1, 1.3, 1.4, 1.6, 2 (bg_transit_rules row), 3.3, 4.1, 5 (rows 1, 8, 9, 14-18; new rows 20-25), 6, 7 (R-9; new R-17 to R-20), 8 (table: S0, S0b, S0L, S0c, S1), 9 (Q3; new Q16-Q19).
> - **What the order looks like now:** S0 smoke -> **S0b** `bg_transit_rules` -> **S0L** (optional; `bg_vedha_malefic_scale` is required in effect, the rest is not needed by the wave) -> **S0c** (conditional: the Gochara trio `ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_vedha_gochara`, forced by S0b) -> S0v/S0m (conditional) -> S1 (now `ka_muhurta_seva,ka_dasha_kala,bo_karanajala`) -> S2 -> ... -> S7. `bg_transit_rules` is no longer in S1.
> - **Three findings that change what v1.1 predicted** (each with evidence in S0b, P0.6 and E13): (1) **`bg_transit_rules` will NOT delta-skip**: its writer source digest and its table content both moved since the 2026-09-04 receipt (L0 repair #2727; migration 1078), so the writer executes and records `output_changed` TRUE; v1.1's "expected `skip_no_delta`" (1.1, R-9, 3.3) is withdrawn. (2) The builder cannot write `bg_transit_moorti` (SELECT only; the writer upserts it) and cannot INSERT/UPDATE `asset_freshness` (the receipt path writes it on every completion and every delta-skip): code-derived and catalog-verified, not exercised. (3) Because S0b flips `ka_vedha_gochara` (and `ka_moorti_nirnaya`, `ka_gochara`) stale on the canonical chart, `ka_sangam` is blocked until the Gochara trio is rebuilt, and `ka_vedha_gochara` in turn needs `bg_vedha_malefic_scale` fresh.
> - **Observed in the same re-read, not in SS's message (flagged, evidence E13):** migration 1214 is APPLIED (17:16:06Z); the five `kala_*` MSR keys are gone; between about 17:48Z and 17:55Z the grant-plan grants appeared on `data_plane_builder` (phala/mimamsa tables, `selftest_detail`, `bg_combustion_orbs`, `phala_anchor_identity*`, `life_events`) and the three L2 foreign keys disappeared, with no new `_migrations_applied` row and PR #2825 still OPEN (applied outside a migration, by whom and how not read); `chart_divisionals` RLS is OFF and the reader sees 71,476 rows; #2823 (I-1/I-2) is merged; the pipeline-job image build was SKIPPED in the deploy run that carried 1211; `ka_gochara_resonance` is `error` (set by run 1865991c). 1212, 1213, 1215 are not applied; `phala_rectification` SELECT is still false.
> - **State when read (17:55Z):** P0 audit-grant gate MET; S0 smoke pre-approved and not yet run; P0b access restored (catalog) with verification items 3-7 not done by this lane; the P0c migration gates 1212/1213/1215 are red; grant gates S1/S4/S5/S6 read true, S7 false; the two new gaps above are red.

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
target table of the stages being launched (**v1.1 correction:** v1.0 said S0-S4 need none of the phala_/mimamsa_ grants; BUILDER_GRANT_PLAN v1.3 shows S1 needs `asset_registry.selftest_detail` UPDATE for `ka_muhurta_seva` and `ka_dasha_kala`, and S4 needs `phala_anchors` SELECT for `ka_bhavishya_lekha`; the per-stage list is P0c.2; S5-S6 need the full phala/mimamsa set); (3) no `planned/running/paused` run exists;
(4) the section 5 pre-flight list is green; (5) **v1.1:** P0b holds for any stage it gates (P0b.2: `ga_vargas`, `bo_pratijna` and everything after it) and the P0c migration/grant gates of each stage hold. If (2) fails for the Phala/Mimāṃsā tables the wave can still be launched for
S0-S4 only (Bodha and Kāla assets, waves 1-6), with `ph_*` and `mi_bhavisya` deferred; that split is SS's call (Q9). **v1.2:** condition (1)'s audit-grant half is met (P0.6); the other half (the smoke) is pre-approved and not yet run, and P0.6 lists two further write-path gaps to clear or consciously accept before launching any stage.

### P0.6 Status update (v1.2, 2026-10-01 about 17:40-17:56Z; Evidence E13)

**P0 audit-grant gate: MET.** P0.1's statements that the builder cannot insert into the audit table and that no audit row was ever written by `data_plane_builder` are superseded.

| Check | Observation (read 17:40-17:55Z) |
|---|---|
| Migration | `_migrations_applied`: `1211_asset_throughput_state_audit_builder_grants.sql`, 2026-10-01 17:35:43.051967Z. It sits inside the "Apply Routine DB Migrations" job (17:29:03-17:35:54Z) of deploy run 36898400004 for main 4eb40bec1 (PR #2834, merged 17:00:24Z). |
| Privileges | `has_table_privilege('data_plane_builder','public.asset_throughput_state_audit','INSERT')` = true; `has_sequence_privilege(..._id_seq,'USAGE')` = true. |
| Used | The first audit row ever written by the builder: `ka_gochara_resonance` lit -> error, `db_user = data_plane_builder`, `triggered_by = asset_runner`, 17:36:56.984Z. It is Pravāha's run 1865991c (`l3-lane-frozen-manifest-rebuild`, started 17:36:55Z, `failed` 17:36:57Z) ending in `DEP-ASSERT: ... bg_transit_rules(receipt:stale)`; the state write passed, as SS reported. |

**S0 smoke (P0.4): unblocked and pre-approved by SS.** The executor runs it as written (asset, request, criteria 1-6 unchanged); no further SS act is needed to start it. Active runs on any chart: 0 at 17:58Z (read).

**What "the audit grant is deployed" does not prove (two further builder write-path gaps, read-only, E13 block D; both code-derived outcomes, neither exercised):**

1. **`asset_freshness` (affects the smoke and every stage).** The builder has SELECT only: INSERT and UPDATE are false at table level and at column level. `provenance.py` `_upsert_freshness_row` (`INSERT INTO asset_freshness ... ON CONFLICT DO UPDATE`, present since 2026-08-25, commit cfa098d33) runs from `persist_successful_receipt` (every completed data writer and probe) and from `reattribute_unchanged_receipt` (every delta-skip, which is what the smoke is expected to do). Migration 1070's verb map lists the table as "SELECT (asset_runner.py, provenance.py: read only)", which does not match the code. If no other path writes it, a run as `data_plane_builder` raises `permission denied for table asset_freshness` at the receipt step: a light writer's receipt capture sits in a try/except that rolls back (data unchanged) and sets the asset `error`. The delta-skip path, which is what the smoke is expected to take, is messier: `_skip_no_delta` is called inside the delta-skip gate's try/except in `_run_data_writer`, which logs and falls through to normal execution, but the failed statement has already aborted the transaction (no savepoint around it), so the next statement raises and the worker's crash handler (`runner.py` `worker`) tries to write `error` on the same aborted connection. Code-derived and only partly traced: the run fails and the smoke asset `ka_tithi_pravesha` ends `error` or is left `building` until the watchdog (15 min) or the next dispatch's orphan cleanup reaps it; no data change either way (recoverable by one later successful build). What this lane cannot see: whether the job writes receipts through another role or a function. The smoke is the only end-to-end proof; to avoid spending it on a known-red check, run the P0.3 check 1b below and ask Pravāha first. SS may still fire the pre-approved smoke and expect that outcome.
2. **`bg_transit_moorti` (affects S0b only).** Builder SELECT only (migration 1073 granted the read for Kāla); the `bg_transit_rules` writer upserts it. See S0b.

```sql
-- P0.3 check 1b (read-only): the builder write path beyond the audit table
SELECT has_table_privilege('data_plane_builder','public.asset_freshness','INSERT')  AS freshness_ins,
       has_table_privilege('data_plane_builder','public.asset_freshness','UPDATE')  AS freshness_upd,
       has_table_privilege('data_plane_builder','public.bg_transit_moorti','INSERT') AS moorti_ins,
       has_table_privilege('data_plane_builder','public.bg_transit_moorti','UPDATE') AS moorti_upd;
-- 17:55Z: f | f | f | f. The first two gate the S0 smoke and every stage; the last two gate S0b.
```

**Post-deploy verification, with Trap 103 (v1.2).** A `success` deploy run listed for a merge sha is not proof that the sha (or its migration) was deployed: the run may have used a different `DEPLOY_SHA`. In this repo `DEPLOY_SHA` is `github.event.workflow_run.head_sha || github.sha` (`.github/workflows/deploy.yml:95`), each deploy job re-checks out `ref: DEPLOY_SHA` and compares `ACTUAL_SHA`, and changed-path gating can skip whole jobs. Before treating any migration, grant or writer change as applied:

1. read the run's own record (`gh run view <id> --json headSha,event,jobs`): which `DEPLOY_SHA` it ran, whether "Apply Routine DB Migrations" ran and succeeded, and which of "Build & Deploy Web / Pipeline Job Image / Sidecar / MCP" ran or were skipped;
2. for a migration: the `_migrations_applied` row (filename, `applied_at`) AND the migration's own post-apply SQL or the `has_*_privilege` result (CLAUDE.md N.4);
3. for a writer change: the pipeline-job image tag (the cockpit POST response `job_image_tag`, or the job description) contains the commit, and the runner's code-digest check (`expected_code_digest`) passes;
4. when a run list shows two `workflow_run` deploys for one sha, treat neither as proof until 1-3 hold.

Read now (not a full audit): two `workflow_run` deploys are listed for 4eb40bec1, 36896658202 (17:04:16Z) and 36898400004 (17:18:25Z), both `success`; the second applied the routine migrations and deployed the web service, and its **"Build & Deploy Pipeline Job Image" job was skipped**, so the job image was not rebuilt by it. 1211 was verified here by catalog (rows 2 above), not by the run list. Which commit the current job image carries was not readable by this lane (S0b pre-check).


## P0b. PRECONDITION 0b: `chart_divisionals` is readable and writable by the builder/app roles (v1.1, SS ruling)

**Precondition P0b (verbatim ruling):** `chart_divisionals` readable and writable by the builder/app roles (Option D,
`ALTER TABLE ... DISABLE ROW LEVEL SECURITY` via the D6 owner path, or equivalent), verified by an exact owner-path count and the
`chart_snapshot` canary on the 3 charts (`482012f1-710e-4a25-994a-93821f5871aa`, `1c826d5a-41cb-4450-b4dc-59d440e5f75a`,
`cb73cd3d-9eba-4220-9902-0de91566e980`).

**Rule (kept and restated): NO `ga_vargas` rebuild, and no refresh of the two `amjis_app`-owned materialized views
(`mv_chart_vargas_summary`, `mv_chart_super_vargottama_bodies`), before P0b holds.** A `ga_vargas` rebuild under the current blindness
would probably swallow the per-row insert errors, finish `lit` with 0 rows written and pass its integrity check (inferred from
code by the incident review, Part III F1: `ga_vargas_writer.py:2762-2776` logs and continues, the four integrity conjuncts are all
`NOT EXISTS`; not exercised). A refresh of the two views would read through RLS and could bake in zero rows.

### P0b.1 Why this is a precondition and not an option (observed 2026-10-01 about 16:20Z as `suvarna_reader`, Evidence E12)

| Fact | Observation |
|---|---|
| Table state | `chart_divisionals`: owner `data_plane_l1_owner` (migration 1035, applied 2026-09-18), `relrowsecurity` true, `relforcerowsecurity` false, **0 policies**, `row_security_active` true for the reader. `SELECT count(*)` as the reader returns **0**. |
| Builder has the privilege, not the visibility | `has_table_privilege('data_plane_builder','public.chart_divisionals','SELECT')` and `'INSERT'` are both true; RLS default-deny is what blinds it (a non-owner with no policy sees and writes nothing). So the grant plan cannot fix this; the privilege is already there. |
| Product symptom | per the incident review (PR #2833), observed with `chart_snapshot`: D1 and D9 grids are empty for all three charts. |
| Status of the fix | The incident review's plan hashes (count `6d9745dd8005fa2a1845aa2326c101472f3d3db12794478db9f08e6ddf02953f`, apply Option D `531c0940ae6eb654972e3401fd317f95cf2051cca10ae7249ff44e420a741aad`) are SS-APPROVED, and the fix is **ON HOLD**: after the owner told Pravaha "don't worry about it, any which way, we will rebuild it" the execution was ordered held. Nothing has been applied (table state above). |

**What the hold means for this plan.** The owner's sentence is correct that no restore is needed (the data is probably intact, below). It
cannot be read as "rebuild instead of fixing access": **a rebuild cannot succeed while the table is RLS-blind.** The builder is the role
that runs every writer, so under the current state it neither reads nor lands rows in this table. The access fix is therefore the
rebuild's precondition, not an optional follow-up. While the hold stands, the stages that touch the table (below) are NOT launchable;
lifting the hold for the access fix only (not for any rebuild) is the SS/owner decision that unblocks them.

**v1.2 status (read 17:40-17:55Z, E13 block E).** The access fix is in place: `chart_divisionals` now reads `relrowsecurity` false, `row_security_active` false, 0 policies (owner `data_plane_l1_owner` unchanged), and the reader sees **71,476 rows** (canonical 24,392; `1c826d5a` 23,542; `cb73cd3d` 23,542), the figure the incident review read as `reltuples`. This is Option D's catalog end state. No `_migrations_applied` row accounts for it, the incident-review PR #2833 is still OPEN, and who applied it and how (the D6 owner path, per the ruling) was not read, so "the hold is lifted" is inferred from the catalog, not recorded. It was not in SS's message of 2026-10-01 and is reported here because P0b gates S2. Not established: the owner-path count (so "intact" is a reading, not a proof), the builder/app-role probe, the `chart_snapshot` canary, the ownership-status gate (checks 3-7 of P0b.3).

### P0b.2 What is gated by P0b

| Stage / asset | Why | Gate |
|---|---|---|
| any `ga_vargas` rebuild (stage S0v, conditional, P0b.4) | writes the table | **P0b holds, then the owner-path count decides whether it runs at all** |
| S2 `bo_pratijna` (an SS-named asset, in the plan) | its writer reads `chart_divisionals` through `ChartReaderV4` (`bo_pratijna.py:15,143-154`; `brahmagyan/chart_reader_v4.py`: D9/varga placements and house occupants live only in `chart_divisionals`, `fact_category='varga_house_occupant'`) | P0b holds (code-read; what the writer does on a blind read, error or silently degraded rows, was not exercised) |
| S1a `bo_laksana` (MSR producer, only if it enters a run, section 1.5) | reads D9 dignity from `chart_divisionals` (`bo_laksana.py:2660-2662`) | P0b holds |
| everything downstream of S2 in the order (`ka_yojaka`, `ka_avadhi`, `ka_kshetra`, S5-S6) | consume `bodha_pratijna`, which would be built from a blind read | inherits the S2 gate |
| S0 smoke, S0b (`bg_transit_rules`), S0L (L0 assets), S1 (`ka_muhurta_seva`, `ka_dasha_kala`, `bo_karanajala`) | none of these writers names `chart_divisionals` (grep of `pipeline/orchestrator/writers`; v1.2: also `l0_transit.py`, `l0_phaladeepika_vedha.py`, the vidhi and formula writers and `service_probes.py`; `ka_dasha_kala` reads `ga_dashas`) | not gated by P0b |

This is wider than the ruling's wording ("precondition of the `ga_vargas` stage"): I extend it to `bo_pratijna` because the
plan's own asset reads the table (disagreement recorded in the report that accompanies this revision).

### P0b.3 Verification (all must pass before any gated stage launches; the executor does the in-transaction probe, the analysis lane does V1-V3 read-only)

1. **Exact owner-path count** (the incident review's Part II.A statements C1-C5, rolled back, never committed; plan hash
   `6d9745dd...953f`): per chart, per `(chart, ayanamsha)`, per `(chart, ayanamsha, varga)`, with `build_id` provenance. This settles whether the data is intact. Not run by this lane.
2. **Catalog (reader):** `SELECT relrowsecurity, row_security_active('public.chart_divisionals') FROM pg_class WHERE relname='chart_divisionals'` must read `false, false` (Option D), or, for an equivalent fix, the reader and the builder-role probe must see rows.
3. **Reader count equals the owner-path count** per chart and per `(chart, ayanamsha, varga)` (statements C1-C3 run as `suvarna_reader` after the fix).
4. **Builder/app probe** (executor, in-transaction as the real roles): `count(*)` as `amjis_app`, `data_plane_builder`, `data_plane_verifier` equals the owner count and is > 0 for each of the three charts. Write-side visibility for the builder is only proven by a real writer landing rows, so the first gated stage doubles as the write-side proof: for `ga_vargas` (if S0v runs) the post-run count of `chart_divisionals` for the chart must equal the writer's reported rows written and be > 0; for `bo_pratijna` the post-run read of `bodha_pratijna` is the proof its input was not empty.
5. **Canary:** `chart_snapshot` for each of the three charts shows non-empty D1 and D9 grids (every graha present in some sign; canonical: Sun in Capricorn, Lagna in Aries in D1, the FORENSIC anchors).
6. **Gate:** `data-plane-ownership-status.ts` prints `marked` (Option D adds no policy and needs no attestation row; Option P would).
7. **Nothing moved:** the owner-path count re-run after the commit equals the pre-commit count.

An equivalent to Option D is acceptable only if checks 3, 4 and 5 hold for all three charts; Option P (three policies) leaves
`data_plane_migrator`, `data_plane_l2_owner` and `suvarna_reader` blind and adds oid-pinned attestation rows (incident review Part II.B).

**v1.2 status of the seven checks.** (1) owner-path count: not run by this lane. (2) catalog: PASS (`false, false`). (3) reader count equals the owner-path count: only half observable, reader 71,476 total and per chart as above, owner-path side not run. (4) builder/app probe: not run (`has_table_privilege` for the builder was already true; visibility is what changed, and the builder role cannot be probed by the reader). (5) `chart_snapshot` canary on the 3 charts: not run (no MCP/app call was made). (6) `data-plane-ownership-status.ts` gate: not run. (7) nothing-moved re-count: not run. So P0b is "access restored, verification incomplete"; the first gated stage (S2, `bo_pratijna`) still doubles as the write-side proof.

### P0b.4 The `ga_vargas` stage: does it belong in the minimal plan? (decision, stated honestly)

- **Today it is not in the plan, and the planner does not need it.** `ga_vargas` is an out-of-plan direct dependency of `bo_pratijna` (migration 1210 edge), `bo_laksana`,
  `bo_vargottama_dhana`, `ga_condition`, `ga_sade_sati`, `ga_strength`, `ga_structural` (live `depends_on`, Evidence E12). Its state: `lit`, freshness `fresh`, 24,400 rows written at
  2026-09-07 11:03Z (`asset_throughput.rows_written`; a landed count after the F-A3 fix per the incident review), so the planner's pre-flight
  (lit and fresh) accepts it and the minimal-plan fixpoint of section 1.2 does not add it. That test reads throughput and freshness
  metadata, **not row visibility**, which is why a blind table passes it.
- **Decision.** (a) If the owner-path count shows the table intact (the incident review's reading of `reltuples` 71,476, 6,247 heap pages, populated derived columns, no delete path; still a reading), **the `ga_vargas` stage is not needed**: P0b alone unblocks the plan, nothing is rebuilt for this reason, and
  the 61-asset closure of `ga_vargas` is not rebuilt. (b) If any chart reads 0, the total is far below about 71k, or a single ayanamsha/varga is missing, P0b still comes first, then a `ga_vargas` rebuild
  for the affected chart(s) becomes a **separate production build with its own REVIEW to SS** (it would stale the downstream closure: `bo_laksana`, `bo_vargottama_dhana`, `ga_condition`, `ga_strength` and the rest, so the MSR-before-Kala rule of section 1.5 binds it), and the delete must be explained before the rebuild. **The owner-path count settles which branch applies; it has not been run, so the branch is open.**
- The incident review's F-A3 note matters if (b): `rows_written` for the other two charts (38,620 each) is a pre-fix attempted count, about 23.5k live was the expected landed figure; compare with the owner-path count, not with throughput.
- **v1.2:** the reader now sees 71,476 rows with all three charts present (24,392 / 23,542 / 23,542), which supports branch (a) (table intact, `ga_vargas` stage not needed). It does not settle it: the canonical figure is 8 below the 24,400 `rows_written` of 2026-09-07 (unexplained here; `rows_written` may count updates or conflicts rather than landed rows), the owner-path count was not run, and per-(ayanamsha, varga) coverage was not compared. S0v stays "conditional, probably not needed".


## P0c. Dependency gates by stage: grants and migrations (v1.1; v1.2 status per row)

Sources: BUILDER_GRANT_PLAN v1.3 (PR #2825, `suvarna/land/grant-plan-001`), the migration headers of PRs #2826, #2827, #2828, the
`F3_MSR_FK_DROP_v1_0.md` v1.1 on `suvarna/land/F3-msr-fk-drop-001`, and PR #2830. **Live state read 2026-10-01 about 16:20Z (Evidence E12): none of
migrations 1212, 1213, 1214, 1215 is applied (`_migrations_applied` latest = 1210); no active output-digest spec exists for `ka_vighnakara`, `ka_dasha_kala`
or `ka_muhurta_seva`; all eight `bodha_msr_signals` foreign keys still exist; for `data_plane_builder`: `asset_throughput_state_audit` INSERT false,
`phala_anchors` SELECT false, `bg_combustion_orbs` SELECT false, `asset_registry.selftest_detail` UPDATE false, `phala_rectification` SELECT false.**
All six PRs (#2826, #2827, #2828, #2830, #2825, #2833) were OPEN and unmerged at that time. "Deployed and verified" below means: the migration's file
is in `_migrations_applied` AND its own post-apply SQL returns the stated result (CLAUDE.md N.4: never trust a silent no-op), or, for a grant, the
`has_*_privilege` check in the table is true for `data_plane_builder`.

**v1.2 re-read (17:40-17:56Z, E13 blocks B-E).** Migrations: 1214 and 1211 (Pravāha's audit grant) are applied; 1212, 1213, 1215 are not; the held 5-edge migration is now numbered **1216** (not applied; the number 1211 in v1.0-v1.1 meant this one). Grants: between about 17:48Z and 17:55Z the grant-plan grants appeared (see P0c.2) and the three L2 foreign keys vanished, with no new `_migrations_applied` row and PR #2825 still OPEN; applied outside a migration, the apply record was not read. Trap 103 applies to every "deployed" claim (P0.6).

### P0c.1 Migrations

| Migration (PR) | What it does | Gates which stage | Verify (read-only) |
|---|---|---|---|
| **1212** (#2826, I-4) | one `asset_output_digest_specs` row for `ka_vighnakara` (resolves B-1: the asset can then be 'proven') | **S4** (`ka_vighnakara` and its four direct dependents `ka_kala_darshana`, `ka_bhavishya_lekha`, `ph_muhurta`, `ph_pratikara`, hence all of S5-S6). Without it S4 ends `blocked_dependency` exactly as section 0 item 2 predicts. | `SELECT spec_sha256 FROM asset_output_digest_specs WHERE asset_id='ka_vighnakara' AND retired_at IS NULL` = `a731cb0c49546583b12dd24f1366389b99eb695aed4142f16560cea08b88f117` (1 row) |
| **1213** (#2826, I-5) | two spec rows, for the services `ka_dasha_kala` and `ka_muhurta_seva` (resolves B-2: `ka_sangam`'s NULL upstream digest) | **S1** (it must be deployed BEFORE S1 runs: the services' receipts only gain a digest when they REBUILD under it; applying it changes no receipt by itself) and therefore **S3** (`ka_sangam`) and everything after | `SELECT asset_id, spec_sha256 FROM asset_output_digest_specs WHERE asset_id IN ('ka_dasha_kala','ka_muhurta_seva') AND retired_at IS NULL` = 2 rows (`c5dfe575...681d`, `dbcdba8a...9ed4`); after S1, the latest receipt of both has `receipt_state='proven'` and a non-null `output_digest` |
| **1215** (#2827, I-8) | rewrites `ka_avadhi`'s `integrity_check_sql`: scoped to the canonical chart, `chara_karaka` vocabulary fix, non-vacuity conjunct (f) | **S3, `ka_avadhi` only** (the failure it cures, `post-write integrity check failed`, is the 2026-09-10 error of section 0 item 6). It updates `integrity_check_sql`, which fires `nirmana_registry_receipt_invalidation`, so `ka_avadhi`'s receipt reads `registry_changed` afterwards (it is in the plan anyway). | its own `$post$` assertions (canonical-chart literal and `'chara_karaka'` present, `'chara',` absent, conjunct (f) present): `SELECT position('482012f1-710e-4a25-994a-93821f5871aa' IN integrity_check_sql) > 0, position('''chara_karaka''' IN integrity_check_sql) > 0 FROM asset_registry WHERE asset_id='ka_avadhi'` |
| **1214** (#2828, F-3) **APPLIED 2026-10-01 17:16:06.208Z (v1.2, observed; its carrying deploy run was not traced, Trap 103)** | drops the five `kala_*` `signal_id` foreign keys into `bodha_msr_signals` | **No stage in this plan.** The plan contains no MSR writer, so nothing in it triggers the cascade the keys carry. It governs the **lifetime of the MSR-before-Kala/Phala rule (section 1.5)** and is the pre-condition for any later MSR regeneration; if an MSR producer is added (S0m) with the keys still present, its replace CASCADE-deletes `kala_*` rows (F-3 proof: 4 rows to 0). Its own pre-merge gates (F3 doc section 2: no in-flight run on any chart, an idle deploy window, no long read on `bodha_msr_signals`) apply to the deploy that carries it. | the five constraint names absent from `pg_constraint`; `msr_dangling_signal_refs.py --require-nonvacuous` post-wave; note the migration lives in `platform/supabase/migrations/` while 1210 lives in `platform/migrations/` (F3 doc open question 4): confirm the deploy actually applied it |
| **L2 FK drop** (grant plan v1.3 Part A, owner-path, PR #2825) **DONE (v1.2, observed 17:55Z): none of the three constraint names exists in `pg_constraint`; applied outside a migration** | drops `bodha_contradictions_signal_{a,b}_id_fkey` and `bodha_signal_embeddings_signal_id_fkey` (owner `data_plane_l2_owner`) | **No stage.** Same role as 1214: ends the cascade into `bodha_signal_embeddings`/`bodha_contradictions`. F3 doc section 5 records a PREREQUISITE (the L2 writers' child deletes are scoped by `pg_temp.bodha_msr_signals`, a snapshot that is empty for a root writer such as `bo_laksana`, so dropping the keys without scoping the child deletes strands 4 embeddings and 1 contradiction in its proof); SS ruling (2026-10-01): the grant plan's three L2 FK drops are the owner-path step; the section 5 prerequisite (the L2 writers delete their own embeddings and contradictions before rebuilding) is the code fact already established, and recording it here is sufficient. Residual caveat kept: for a root writer such as `bo_laksana` the snapshot-scoped child deletes were observed to strand 4 embeddings and 1 contradiction in the F3 proof, so the MSR-before-Kala/Phala ordering rule (1.5) still applies until both drops are deployed and the post-wave detector reads zero. | `pg_constraint` shows none of the three names |
| **1211** (#2834, Pravāha B6.0, v1.2) | grants `data_plane_builder` INSERT on `asset_throughput_state_audit` and USAGE on its sequence (the P0 audit grant) | **P0** (all stages): MET, see P0.6 | `has_table_privilege(...,'INSERT')` and `has_sequence_privilege(...,'USAGE')` true; row in `_migrations_applied` (17:35:43Z); first builder audit row 17:36:56Z. Verified by catalog, not by the run list (Trap 103). |
| **1216** (held; renumbered from 1211 in v1.2) | the 5 held `depends_on` edges (branch `TI-edges-002`, commit 086a0fcc5 as recorded in v1.0; not re-verified, the branch is not on origin) | **No stage.** Applied only after its own gate: each of `bo_pratijna`, `ka_yojaka`, `mi_bhavisya`, `ph_nimitta` lit, fresh and proven (the "1216 gate") | `1211_asset_registry_direct_edges_held_verify.sql` Q4/Q6 (the on-disk evidence file still carries the old number); `_migrations_applied` must show no `1216_` row until the gate is met |

### P0c.2 Grants (all `data_plane_builder`; the audit-table grant is Pravaha's and is P0, not repeated)

| Grant (BUILDER_GRANT_PLAN v1.3 Part B unless noted) | Needed by | Gates | Today |
|---|---|---|---|
| `GRANT UPDATE (selftest_detail) ON asset_registry` | the four service writers `ka_dasha_kala`, `ka_muhurta_seva`, `ka_tulana`, `ka_graha_sancara`: the first two are in the launch set (`ka_dasha_kala` unguarded write: permission denied, asset error; `ka_muhurta_seva`'s write is outside any try and its exception fails the asset; both code-derived, grant plan section 3.1) | **S1 and S0m-onward**: this is a **correction to v1.0 P0.5**, which said S0-S4 needed no grant beyond the audit grant; `ka_muhurta_seva` already sits in S1 | **true at 17:55Z (v1.2)**; was false at about 17:47Z; applied outside a migration |
| `GRANT SELECT ON bg_combustion_orbs` | `ka_vighnakara.py:302`, which falls back silently to constants when it cannot read the table (grant plan: the 8 table values equal the 8 fallback constants today, observed there) | **S4**, soft: not blocking, but without it the output silently depends on the fallback | **true at 17:55Z (v1.2)** |
| `GRANT SELECT ... ON phala_anchors` | `ka_bhavishya_lekha.py:249-280` reads `phala_anchors.bhavishya_id` to refuse deleting referenced stale projection ids; the read runs only when `kala_bhavishya` already holds rows for the chart (0 on the canonical chart today), so the first S4 pass may not touch it but **any retry or later run does** | **must precede S4** (the stage that builds `ka_bhavishya_lekha`): the phala grant is not only an S5 need | **true at 17:55Z (v1.2)** (SELECT, INSERT, DELETE; UPDATE false) |
| `phala_*` x8 tables (`phala_anchors`, `_muhurta`, `_mitigation`, `_sankrama`, `_sodhana`, `_suddha_sodhana`, `_pramana`, `_phaladesa`), `EXECUTE` on `phala_anchor_identity(...)` and `phala_anchor_identity_namespace()`, `life_events` (5 columns), `brahma_activity_ontology` SELECT | the eight `ph_*` writers | **S5** | **true at 17:55Z (v1.2)**: S, I, D on all eight; UPDATE only on `phala_phaladesa` and `phala_suddha_sodhana`; `EXECUTE` on both `phala_anchor_identity*` functions true; `life_events` any-column SELECT true (the five specific columns not checked); `brahma_activity_ontology` SELECT true. Whether any `ph_*` writer UPDATEs a table whose UPDATE is false was not re-derived. |
| `mimamsa_predictions`, `mimamsa_manifestation_sets` (SELECT, INSERT, DELETE) with the N-46 `BEFORE INSERT OR DELETE` guard (Part A2) | `mi_bhavisya` | **S6** | **true at 17:55Z (v1.2)**: S, I, D on both (UPDATE false); trigger `mimamsa_predictions_builder_guard` enabled on `mimamsa_predictions` (none seen on `mimamsa_manifestation_sets`; the N-46 guard's specification was not re-read) |
| `kala_*` target tables | every `ka_*` writer in the plan | none outstanding: grant plan section 3.2 re-measured all 18 distinct `ka_*` target tables as fully granted (S, I, U, D) and the identity sequences as USAGE; 41 of 47 `kala_*`/`gochara_*` tables fully writable; the gochara-kernel tables are Pravaha's and no registered S0-S4 writer names them | none |
| `phala_rectification` SELECT | `ka_kshetra` (`uncertainty.py:185-196` via `stage3_clocks.py:1012`) | **S7**: **held** by migration 1073 on a design ruling and not part of the grant plan | false at 17:55Z (v1.2): still held |
| `INSERT, UPDATE ON asset_freshness` (v1.2; NOT in the grant plan or 1070) | the receipt path of every run: `provenance.py` `_upsert_freshness_row`, called by `persist_successful_receipt` and `reattribute_unchanged_receipt` | **P0 smoke and every stage** (P0.6 item 1) | **false** (table and column level) at 17:55Z |
| `INSERT, UPDATE ON bg_transit_moorti` (v1.2; NOT in the grant plan or 1073, which granted SELECT only) | `seed_transit_rules` (the `bg_transit_rules` writer upserts 27 moorti rows) | **S0b** (section S0b) | **false** (table and column level) at 17:55Z |

The grant plan's own verification and rollback are its; this plan only consumes the post-apply `has_*_privilege` results. P0.5 check 2 is amended: S0 needs the audit grant only; **S1 needs the audit grant plus `selftest_detail`**; S2-S3 need the same;
**S4 needs `phala_anchors` SELECT** (and `bg_combustion_orbs` for a non-fallback run); S5 needs the full phala set; S6 the mimamsa set and guard; S7 the held `phala_rectification` ruling. Q9 (split decision) is restated in section 9.


## S0b. STAGE S0b: `bg_transit_rules` (GLOBAL L0), first stage after the S0 smoke (v1.2, SS ordering)

REVIEW section; no execution authority. Every figure was read at 2026-10-01 17:40-17:58Z as `suvarna_reader` (E13) or recomputed from `origin/main` (4eb40bec1) sources; "code-derived" means read from code and not exercised in production.

**Why it moves to the front.** Pravāha's pipeline run 1865991c failed with `DEP-ASSERT ... bg_transit_rules (receipt:stale)`. The same predicate blocks any build of the six direct dependents (`ka_gochara`, `ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_sangam`, `ka_vedha_gochara`, `ka_yojaka`) on every chart. The asset is global, so one rebuild clears it for all charts.

### S0b.1 Before-state (read-only, E13 blocks C, F, G)

| Item | Value |
|---|---|
| Registry | `bg_transit_rules`: layer `brahmagyan`, `scope` global, `domain` shared, `asset_kind` data, `has_writer` true, `depends_on` `{}`, `target_floor` 76, `writer_timeout_seconds` 10800, `natural_key_partition` NULL, integrity SQL present (pins 9 / 76 / 27 rows and three content hashes) |
| Rows (table, live) | `bg_transit_rules` 76 (69 writer-owned: 43 favourable + 26 unfavourable; 7 migration-owned `double_transit`), `bg_transit_engine` 9, `bg_transit_moorti` 27 |
| Throughput (global row, `chart_id` NULL) | `lit`, `last_built_at` 2026-09-04 20:07:52.531797Z, `rows_written` 104 (= 9 + 68 + 27, before the 69th rule existed) |
| Freshness | `__whole_asset__` **stale**, reasons `["registry_changed"]`, `observed_at` 2026-09-23 21:17:23.869511Z |
| Receipt | `proven`, version `nirmana-provenance-receipt-v2`, `build_id` 440c1ae6 (the 2026-09-04 20:07 run), `observed_at` 2026-09-04 20:07:52.531797Z; code digest `9812db139d56`, output digest `1983611685a8`, spec `b704673aa584` (three components: rules, engine, moorti), upstream `dbdd6eea6880`, config `c15fddb4f943`, partition `595f36c1f29d` |
| Last builds | `build_run_assets`: 2 completed, both on the canonical chart as `asset_set` runs of L0 assets (2026-09-04 19:42:12 and 20:07:52Z), dispositions `build` / `build`, `output_changed` true then false, 0.04 s and 0.03 s. None since. |
| Integrity SQL today | executed read-only: **true** |
| `bg_transit_engine` | a registry asset of its own (`has_writer` false, lit 2026-08-02, no freshness row); it is written by this same writer and digested inside this asset's spec; it is not separately dispatchable |

### S0b.2 What makes the receipt stale (registry_changed): what exactly changed

The trigger `nirmana_registry_receipt_invalidation` fires on an UPDATE of `depends_on`, `natural_key_partition`, `health_probe`, `integrity_check_sql`, `target_floor`, `asset_kind`, `asset_type`, `scope`, `has_writer`, `is_active` or `target_table`, and sets every `asset_freshness` row of the asset to `stale` with reason `registry_changed` (it does not touch the receipt). The freshness `observed_at` equals the `applied_at` of migration **1078** (2026-09-23 21:17:23.869Z). 1078 (L0 repair, PR #2727) updated the registry row: `target_floor` 75 -> 76 and `integrity_check_sql` re-pinned (both are trigger columns), plus `english_description` and `volume_explanation` (not trigger columns). Migration 1079 (22:03:22Z) changed `english_description` only, so it did not fire the trigger and did not touch the flag. No other registry event touched this row since 2026-09-04.

**The flag is not a false alarm; three things moved under the 09-04 receipt:**

| What | Receipt (09-04) | Now | How known |
|---|---|---|---|
| Writer source (code digest) | `9812db139d56` | `824c6d7d7237` (`origin/main` digest inventory; recomputed locally with `get_writer_source_hash`: equal) | `l0_transit.py` changed in #2727 (b6690928f) |
| Table content (output digest) | `1983611685a8` | `ca19407a3e37` (replica of `compute_output_digest`, E13) | L0 repair items 1-3: 35 rows re-cited, 3 Venus `vedha_house` values corrected, the Mercury 8th->1st pair inserted (75 -> 76 rows), 6 Rahu/Ketu rows marked unsourced |
| Registry contract | 75 rows, old hash | 76 rows, new hash (1078) | migration 1078 |

The content change was applied outside any build run (no `build_run_assets` row after 09-04 for this asset; how the repair writer ran is not recorded in the tables read). Upstream, config and partition digests recompute to the stored values exactly, so the writer source and the content are the only differences.

### S0b.3 What a rebuild writes (writer read in full)

`writers/bg_transit_rules.py` -> `brahmagyan/l0_transit.py seed_transit_rules` (registered for both `bg_transit_rules` and `bg_transit_engine`). One transaction, `ON CONFLICT DO UPDATE` upserts on natural keys (L0 standard, no delete-then-insert because `bg_transit_rules.id` is serial and `gochara_resonance_map.source_rule_id` references it):

| Table | Upserted rows | Key |
|---|---|---|
| `bg_transit_engine` | 9 | `graha` |
| `bg_transit_rules` | 69 (writer-owned categories) | `(graha, rule_type, primary_house)` |
| `bg_transit_moorti` | 27 | `nakshatra_offset` |

Total 105 (reference `rows_written` 105; last real 104). A retirement sweep (F-145) deletes owned-category rows absent from the source; the 7 migration-owned `double_transit` rows are never candidates. **Read-only comparison of the source lists against the live rows (E13): 0 engine rows, 0 rule rows, 0 moorti rows would change, 0 rows would be retired, 0 inserted.** So the rebuild changes no table content; what it changes is the receipt, the freshness and the throughput. Side effect: the serial sequence of `bg_transit_rules.id` advances by 69 (ids already assigned do not change). No L1 table, no per-chart table, no other global table is written.

### S0b.4 BLOCKER found read-only: the builder cannot write `bg_transit_moorti`

`has_table_privilege('data_plane_builder','public.bg_transit_moorti', 'INSERT' | 'UPDATE')` = false (also false at column level; ACL has `data_plane_builder=r`); migration 1073 granted SELECT only, for Kāla reads. The writer's third upsert is `INSERT INTO bg_transit_moorti ... ON CONFLICT DO UPDATE`, which needs INSERT and UPDATE. **Code-derived outcome (not exercised):** the writer raises `permission denied for table bg_transit_moorti`, the light writer's transaction rolls back (engine and rules upserts included), the asset ends `error` and its throughput row goes **lit -> error**, which makes Pravāha's block worse (their DEP-ASSERT would then read `bg_transit_rules(error)`). No data change. The other L0 data writers' tables are fully granted to the builder (`bg_vedha_malefic_scale`, `brahma_formula_constants`, `vidhi_primitives`: S, I, U, D). The grant needed is `INSERT, UPDATE ON public.bg_transit_moorti TO data_plane_builder` (the table has no sequence); it is not in the grant plan v1.3 or in 1073; not drafted here (a separate act, Pravāha/grant owner). The `asset_freshness` gap of P0.6 item 1 applies on top of this.

### S0b.5 Effect on other charts and on per-chart assets (live registry)

- **Downstream closure of `bg_transit_rules`: 34 per-chart assets, 0 global.** 16 are in the 27-asset launch set (`ka_gochara`, `ka_yojaka`, `ka_sangam`, `ka_kalasutra`, `ka_vighnakara`, `ka_kala_darshana`, `ka_bhavishya_lekha`, 8 `ph_*`, `mi_bhavisya`), 18 are outside it (`ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_vedha_gochara`, `ka_jivana_parva`, `ka_kshetra`, `ka_taranga`, `ka_tulana`, `mi_abhilekha`, `mi_adhilepa`, `mi_bhara`, `mi_darshana`, `mi_gunanaka`, `mi_pariksha`, `mi_pramana`, `mi_sambandha`, `mi_sankalpa`, `mi_seva`, `ph_rectification`).
- **Mechanism (code-derived):** after the asset completes, `runner.py on_complete` calls `staleness.propagate_downstream_staleness` with **the run's `chart_id`**; it reads `build_run_assets.output_changed` and, if TRUE (or unrecorded), sets every downstream asset not in the run's plan and currently `lit`/`service_ok` to `stale` **for that chart only** (`WHERE chart_id = <run chart>`). For a global asset the run's chart is just the chart the request was made on.
- **Expected `output_changed` TRUE**: the new output digest (`ca19407a3e37`) differs from the stored one (`1983611685a8`). v1.1's "expected `skip_no_delta`, digest unchanged" (1.1, R-9, 3.3) is **withdrawn**: the code digest differs, so the delta-skip gate cannot pass and the writer executes.
- **Canonical chart, states of the 34 now:** 3 `lit` (`ka_gochara`, `ka_moorti_nirnaya`, `ka_vedha_gochara`), 20 `stale`, 10 `error`, 1 `dormant`. **Run on the canonical chart, S0b flips exactly those 3 lit rows to `stale`** (the S0b plan contains only `bg_transit_rules`; `ka_gochara` is rebuilt later in S3 anyway). The other 31 stay as they are.
- **Other charts are not touched by a canonical-chart run.** `1c826d5a` holds 4 `lit` rows among the 34 (`ka_gochara`, `ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_yojaka`), `cb73cd3d` holds 1 (`ka_gochara_resonance`); they stay `lit` although built against the old receipt (propagation is run-chart-scoped), so for them `lit` is no evidence of currency. Their next build recomputes the upstream digest (a rebuilt dependency changes the receipt's `observed_at`), so those consumers will execute, not delta-skip. Running S0b under another chart would instead flip that chart's rows and leave the canonical chart's stale-by-content rows marked `lit`: not recommended (S0b.8).
- **What S0b forces next (not in v1.1).** `ka_sangam` declares `ka_vedha_gochara` (direct), and `ka_gochara` declares `ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_vedha_gochara` (direct). Live fixpoint with the planner's rule (E13): **today** the 27-asset set needs 1 addition (`ka_gochara_resonance`, `error` since 17:36:56Z, set by run 1865991c); **after S0b** it needs 4: `ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_vedha_gochara` and, through `ka_vedha_gochara`, **`bg_vedha_malefic_scale`** (stale; section S0L). With `bg_vedha_malefic_scale` fresh first it needs the Gochara trio only. These are Gochara-family assets (Pravāha's lane, Q5, Q18); the plan carries them as stage S0c (conditional).

### S0b.6 Expected result, canaries, rollback

**Expected (estimate for run mechanics, code-derived for digests):** `build_run_assets` disposition `build`, `output_changed` TRUE; `asset_throughput` `lit`, `rows_written` 105; receipt `proven`, code digest `824c6d7d7237`, **output digest `ca19407a3e37`** (checkable: it must equal the live replica digest, because the rebuild changes no row), spec `b704673aa584`, `build_id` the new run; `asset_freshness` `fresh`, reasons `[]`, `observed_at` the run time. The receipt reads fresh/proven because the digests are all available (no declared dependency, spec present).

| Canary (read-only) | Before (17:40-17:55Z) | After (expected) |
|---|---|---|
| `SELECT count(*) FROM bg_transit_rules / bg_transit_engine / bg_transit_moorti` | 76 / 9 / 27 | 76 / 9 / 27 |
| Replica of `compute_output_digest` (E13) | `ca19407a3e374505...` | identical, and equal to the new receipt's `output_digest` |
| Registry integrity SQL (`\gexec`) | true | true |
| Receipt / freshness / throughput (F1 query, global row) | proven `1983611685a8` / stale `registry_changed` / lit 104 | proven `ca19407a3e37` / fresh `[]` / lit 105 |
| Canonical rows of the 34 (state) | 3 lit, 20 stale, 10 error, 1 dormant | `ka_gochara`, `ka_moorti_nirnaya`, `ka_vedha_gochara` `stale`; the other 31 unchanged |
| Other charts, the 34 (state counts) | `1c826d5a` 4 lit, `cb73cd3d` 1 lit | identical |
| `asset_throughput_state_audit` | one builder row (17:36:56Z) | rows for `bg_transit_rules` (lit -> building -> lit) and the 3 flips, `db_user` of the job |
| Served reader `ref_transit_rules_get` (tool-to-table mapping not verified) | not called by this lane (production MCP call; the DB canary above is authoritative) | the same 76-row content |

**Rollback / what it cannot undo.** Data: nothing to roll back (0 rows change). A failed run rolls back whole (light writer, single transaction; integrity SQL gates success) and leaves the old receipt, but sets the asset `error` (S0b.4). Cannot be undone by this lane: the replaced receipt (old values recorded above and in E13), the overwritten freshness and throughput rows, append-only `build_runs` / audit rows, the serial sequence advance, and the **three canonical lit -> stale flips**, which only a rebuild of those assets reverses.

**Duration.** The writer took 0.03-0.04 s in both completed builds; run-level overhead dominates: single-asset completed runs since 2026-09-01 took a median 25 s from creation to end (min 6 s, max 1675 s, n=128; E6). Allow 5 minutes before calling it hung. The run takes the global-assets lock; a concurrent run holding global assets defers it (exit 3).

### S0b.7 The exact request (global asset rebuild)

`POST /api/cockpit/runs` by a signed-in **super_admin who also has write access to the chart** (code: `route.ts`, `computeNonCandidateAssetIds`, `plan.ts`):

```json
{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa","scope":"asset_set","scope_target":"bg_transit_rules","action":"rebuild"}
```

No `clear_before`, no `force_l0`. This is the shape the 2026-09-04 L0 runs used (`asset_set` on the canonical chart naming the L0 assets). Other shapes do not reach it: `scope:'asset'` on a global asset is refused for everyone (403 `FORBIDDEN_L0`, "Global assets must be built at scope=global"); `scope:'global'` excludes `brahmagyan`-layer assets from the candidates; `scope:'layer'`+`brahmagyan` sweeps skip `domain='shared'` assets (this one is shared) and need super_admin; a non-super_admin sees global assets as non-candidates (planner error). `action:'build'` would also select it (receipt not fresh) but `rebuild` is used for consistency. Planner pre-flight: no dependencies, so no blockers. The one-active-run-per-chart index and the chart advisory lock apply to the canonical chart; the global-assets lock applies to the run.

### S0b.8 Gate before launching S0b (all read-only, repeat at launch)

1. P0 audit grant met (P0.6); **the S0 smoke has run and its outcome is known**, in particular that the `asset_freshness` write path works (P0.6 item 1).
2. **`INSERT, UPDATE ON bg_transit_moorti` granted** (P0c.2; S0b.4). Check: the P0.6 SQL, columns `moorti_ins`, `moorti_upd` true.
3. The pipeline-job image carries #2727 (b6690928f) and `platform/src/generated/nirmana-writer-digests.json`'s entry for `bg_transit_rules` (`824c6d7d7237...`); otherwise the runner's manifest code-digest check refuses the run (fail closed, no write). Read the cockpit response's `job_image_tag` (or the job description); the deploy run that carried 1211 skipped the job-image build (P0.6, Trap 103), so this is not assured.
4. No `planned/running/paused` run on any chart (0 at 17:58Z); global-assets lock free.
5. **Pravāha is told before the run**: they are the beneficiary, their run will need the same chart slot, and S0b flips three of their canonical assets stale (`ka_moorti_nirnaya`, `ka_vedha_gochara`, `ka_gochara`). S0b does not touch `bg_ephemeris` or `bg_texts`, so SS's L0 notification rule is not triggered by this stage itself.
6. Chart for the run: canonical (S0b.5).
7. Before-state captured: S0b.6 canaries, F1 for the 34.

**Not verified here (S0b):** the job's actual DB role path for the receipt writes; the job image content; that the repair writer's run left the content exactly as the source lists (compared: yes, equal); the behaviour of the runner on the permission-denied exceptions; the exact `ref_transit_rules_get` payload.


## S0L. STAGE S0L (optional): L0 freshness for `bg_vedha_malefic_scale`, `bg_vidhi_primitives`, `bg_formula_constants`, `bg_ephemeris_engine`, `bg_panchanga` (v1.2)

REVIEW section. For each asset: whether the 27-asset wave (and what S0b forces) needs it fresh, what a rebuild touches, whether a digest-spec fix must come first. "Needed" is computed with the planner and DEP-ASSERT rule (only **direct** declared dependencies of an asset that runs are asserted; the live registry; E13) and the live fixpoint of S0b.5.

| Asset | Kind | Receipt / freshness now (reason, since) | Needed by the 27? | Rebuild touches | Canonical lit flips | Digest-spec fix first? |
|---|---|---|---|---|---|---|
| `bg_vedha_malefic_scale` | data, writer | proven 2026-09-03 / **stale** `registry_changed`, 2026-09-23 21:17:23.507Z (migration 1077) | **Not directly; required in effect once S0b flips `ka_vedha_gochara`** (it is a direct dep of `ka_vedha_gochara` only) | 5 rows of `bg_vedha_malefic_scale` (source = live, 0 rows change) | `ka_gochara`, `ka_vedha_gochara` (already flipped by S0b) | no (spec `16a4946da003` exists) |
| `bg_vidhi_primitives` | data, writer | proven 2026-09-04 / **stale** `registry_changed`, 2026-09-06 19:52:18.78Z (migration 706), partition `primitive_id` | no (only consumer is `bg_vidhi_floors`, global, outside the closure) | 60 rows of `vidhi_primitives` (source = live, 0 rows change, 0 deleted) | none | no (spec `179ab2c22fad`) |
| `bg_formula_constants` | data, writer | `constant_id` partition **fresh** (2026-09-07); legacy `__whole_asset__` row (receipt v1, 2026-08-25) **stale** `registry_changed`, 2026-08-26 04:08:54.54Z (migration 615) | no (consumers `mi_gunanaka`, `mi_pariksha`, `mi_pramana`, all outside the plan) | nothing: delta-skip expected | none | no (spec `126465c083e5`) |
| `bg_ephemeris_engine` | **service**, legacy health probe, `has_writer` false | `unknown` receipt (08-27) / **stale** `output_digest_spec_unavailable` + `registry_changed`, 2026-09-23 21:07:36.17Z (migration 1075) | no (direct dependent `bg_cohort`, global; `ka_kshetra`, `mi_bhara`, `mi_sankalpa` through it) | no table; registry `service_health`/`last_invoked_at`/`last_selftest_at`, receipt, freshness, throughput | none (the 3 per-chart dependents are `error`/`dormant`) | **yes, and a spec alone is not enough** (below) |
| `bg_panchanga` | **service**, legacy health probe, `has_writer` false | `unknown` / **unknown** `output_digest_spec_unavailable`, 2026-08-27 | no (only transitively, through `ga_panchanga`) | same as above | **15** (`bo_laksana`, `bo_sangati`, `bo_karanajala`, `bo_bimba`, `bo_arudha`, `bo_nakshatra_semantic`, `bo_samskara`, `bo_grounding`, `bo_laksana_rerank`, `ga_panchanga`, `ga_yoga`, `ga_structural`, `ga_sade_sati`, `ga_vichara`, `ka_gochara`) | yes (same) |

**Does the 27-asset wave need any of them fresh?** Direct L0 dependencies of the 27 (E13 blocks I-K, from `asset_registry.depends_on`): `bg_transit_rules` (by `ka_gochara`, `ka_sangam`, `ka_yojaka`), `bg_ephemeris` (the table asset, by `ka_gochara`; lit and fresh), `bg_ghatana` (`ka_avadhi`, `ka_yojaka`; fresh), `bg_dignity_reference` (`ka_vighnakara`; fresh). None of the five assets above is a direct dependency of any of the 27. Transitive closure only: `bg_panchanga` (24 of the 27, through `ga_*`) and `bg_vedha_malefic_scale` (15 of the 27, through `ka_vedha_gochara`); the runner does not assert transitive dependencies. The one real need arises from S0b: **`bg_vedha_malefic_scale` is required in effect** (S0b.5).

**Per asset.**

1. **`bg_vedha_malefic_scale`** (writer `bg_phaladeepika_vedha.py`, `seed_vedha_malefic_scale`, 5-row upsert on `(table_version, malefic_count)`). The registry flag comes from 1077 (integrity reseal after repair item 5's `effect_description` correction). Code digest moved (stored `9170aa9ea036`, `origin/main` inventory `2e3a372e2df6`), output digest moved (live `b1d78defec70`, stored `e76e087dbaf7`): it executes, `output_changed` TRUE, 0 rows change; integrity SQL true today. Builder grants complete. Propagation (canonical): `ka_gochara`, `ka_vedha_gochara` lit -> stale (both already stale after S0b, or being rebuilt in S0c/S3). It is a global asset: same request shape as S0b (`scope_target:'bg_vedha_malefic_scale'`, or `bg_transit_rules,bg_vedha_malefic_scale` in one run if SS wants a single slot). Duration: 0.04-0.06 s writer.
2. **`bg_vidhi_primitives`** (writer `bg_vidhi_primitives.py`: upsert-if-distinct, then `DELETE ... WHERE NOT primitive_id = ANY(source)`; source 60 = live 60, so 0 inserted/updated/deleted). Flag from 706. Code digest moved (stored `93469b4c6394`, inventory `63f0a35a4be7`), output digest moved (live `28eeb20c6abb`, stored `93bc7a13c3cc`): executes, `output_changed` TRUE; its only dependent `bg_vidhi_floors` is global, and propagation is chart-scoped, so no flip is recorded. Not needed by the wave; cheap and safe; optional. Grants complete.
3. **`bg_formula_constants`**: **nothing to rebuild.** The planner and DEP-ASSERT read the latest-observed freshness row per asset (`runPreparation.ts`, `asset_runner.deps_unsatisfied`), which is the `constant_id` partition row: **fresh**. The stale row is a legacy `__whole_asset__` partition (receipt version v1, observed 2026-08-25/26, before partitions were declared). The current receipt's code digest equals the inventory (`54c8bbee62cb`), its output digest equals the live replica (`2c6ebbe3e7a4`), and upstream/config/partition recompute equal, so a rebuild would delta-skip and re-stamp only `constant_id`; **it cannot clear the legacy row** (the writer's partition is `constant_id`). Clearing it is a data decision (delete the orphan receipt and freshness row), not a build; not drafted here.
4. **`bg_ephemeris_engine`** (SS's flagged asset). It is the engine **service**, not the table `bg_ephemeris` (`ephemeris_daily`, 825,084 rows per its integrity contract, lit and fresh, consumed by `ka_gochara`, `ka_moorti_nirnaya`, `ka_vedha_gochara`). A rebuild runs `service_probes.run_health_probe` (migration 1075's degree-level mean-node anchor; the probe source changed with it, stored code digest `fa59f213376c` is the old probe digest, the digest inventory's `probe_digest` `997985c1d56a`, presumed to be the same quantity, not recomputed) and writes no table. Risks: the probe needs the pinned Swiss Ephemeris files in the job container (not verifiable here); a red probe sets the asset `error`. A GREEN probe leaves `unknown` / `output_digest_spec_unavailable` (the registry_changed reason is cleared; the state is not `fresh`). **SS's L0 rule: notify Pravāha before this stage runs**, even though it does not touch `ephemeris_daily`; the wave does not need it, so the recommendation is not to run it as part of this plan.
5. **`bg_panchanga`**: **do not rebuild in this wave.** A probe records no `output_changed`; propagation then fails open and would mark 15 canonical lit assets stale (list above), including the MSR producer `bo_laksana` and `bo_sangati`, which would break the MSR-before-Kala/Phala invariant (section 1.5) and the DEP-ASSERT of S2/S3. This is the reason P0.4 avoids it for the smoke. Code-derived, not exercised.

**The digest-spec gap (services with `output_digest_spec_unavailable`).** Of the five, exactly two: `bg_ephemeris_engine` (stale) and `bg_panchanga` (unknown). Both are legacy health-probe services (no `WriterBase` writer), unlike 1213's `ka_dasha_kala` and `ka_muhurta_seva` (writer-backed services, whose receipts take `compute_output_digest`). The gap is three links, all code-derived:

1. **No spec row** in `asset_output_digest_specs` for either asset (E13 block F).
2. **A spec row alone changes nothing:** `_persist_probe_receipt` (`asset_runner.py:430-470`) calls `capture_and_persist_receipt` without `output_digest_spec_sha256` and with a probe digest that embeds `run_id`; `compute_output_digest` is never called on this path. The receipt would still carry `output_digest_spec_unavailable`. Making it `proven` needs a change to that function in the FROZEN orchestrator (the authorized-exception route used by SATYA-DĪPA, CLAUDE.md N.8), not only a migration.
3. **The planner's legacy-probe exception is unreachable:** `plan.ts` accepts a service dependency with exactly `{output_digest_spec_unavailable}` only when its throughput state is `service_ok`, but the probe path writes `lit` and **no `asset_throughput` row holds `service_ok`** (live histogram: lit 162, stale 73, error 29, dormant 3, incomplete 1). So a plan that lists either service as an out-of-plan direct dependency is refused at pre-flight, while DEP-ASSERT at run time exempts services from freshness. Only `bg_cohort` (global) and `ga_panchanga` depend directly on them; none is in the 27.

**Proposed spec shape (not a migration; not written):** one component over the service's own registry row, excluding the volatile timestamps and mirroring 1213's pattern, but digesting the pinned probe contract because probes do not write `selftest_detail` (NULL on both rows, observed):

```json
{"version":"nirmana-output-digest-spec-v1","components":[{"name":"service_probe_contract","relation":"asset_registry","key_columns":["asset_id"],"where_equals":{"asset_id":"bg_ephemeris_engine"},"value_columns":["asset_id","service_health","health_probe"]}]}
```

(and the same with `bg_panchanga`). `spec_sha256` must be `canonical_digest` of that object (the author computes it, as 1213 did). It would make a changed probe contract or a non-healthy state visible in the digest. Combined with the orchestrator change in link 2 it would let both receipts reach `proven`; without it, nothing changes. Neither is needed by the 27-asset wave.

**Recommendation.** Minimal S0L = `bg_vedha_malefic_scale` only (required in effect). Optional: `bg_vidhi_primitives` (cheap, no flips). Do not run `bg_panchanga`; do not run `bg_ephemeris_engine` unless SS wants the probe re-recorded (and then notify Pravāha first, and expect `unknown`, not `fresh`). `bg_formula_constants` needs no build. Gate for S0L: S0b complete; the S0 smoke passed; `asset_freshness` write path proven; no active run; super_admin; the global-assets lock free. Rollback/limits as S0b.6 (no row changes; flag changes are not undoable).

**Not verified here (S0L):** whether the job container can run the ephemeris probe; the runner's handling of exceptions on the receipt path; the SS/Pravāha-side meaning of "stale" for `bg_formula_constants` (the legacy row is the only stale one I can find); any consumer reading `bg_panchanga` beyond the registry.


## 0. What this review needs you to see first

0. **Nothing can complete yet (P0 above).** The audit trigger on `asset_throughput` is not SECURITY DEFINER and `data_plane_builder`
   cannot insert into the audit table or use its sequence, and the same role holds no privilege on any `phala_*` or `mimamsa_*`
   table. The plan therefore starts with a smoke build on a leaf asset (`ka_tithi_pravesha`) and a go/no-go gate.
   **v1.2:** the audit-grant half is fixed (migration 1211, applied 17:35:43Z; P0.6); the smoke is pre-approved and not yet run; the `phala_*`/`mimamsa_*` grants appeared at about 17:48-17:55Z (P0c.2). Two other builder write-path gaps remain (`asset_freshness`, `bg_transit_moorti`; P0.6, S0b.4), both code-derived and unexercised.
1. **The wave SS named is not a launchable set.** A run for exactly those eight assets is refused by the planner
   (`UPSTREAM_BLOCKED`): 12 out-of-plan direct dependencies are not lit and fresh (Evidence E3). Closing that
   set under the rule the planner and the runner both enforce (every declared dependency of a planned asset must be
   lit and fresh, or be planned earlier in the same run) gives a **26-asset minimal plan: 24 per-chart assets plus two
   global assets, `bg_transit_rules` (L0) and `ka_muhurta_seva` (L3 service)** (section 1, Evidence E4). The minimal plan is computed, not guessed; it is the
   smallest set for which the planner accepts the run (simulation of the planner's preflight on all 26: no out-of-plan blocker remains). **v1.1:** the launch set is these 26 plus `ka_dasha_kala` (27: 25 per-chart, 2 global), section 1.6; every later reference to "the 26" means the v1.0 computed set. `ga_vargas` is not added (P0b.4); `ka_kshetra` is a separate last stage (section 8.2). **v1.2:** `bg_transit_rules` is no longer in S1: it is stage S0b (first after the smoke). After S0b flips three canonical assets stale, the live fixpoint adds `ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_vedha_gochara` and, through the last, `bg_vedha_malefic_scale` (S0b.5, S0L): the set grows from 27 to 31 assets, of which 3 are Gochara-family Kāla assets (stage S0c, Q18) and 1 is L0 (stage S0L). Live today the set already needs 1 addition, `ka_gochara_resonance` (`error` since 17:36:56Z).
2. **Two structural blockers stop `gate_ok` for the four 1216 producers. Both are code-derived, not yet observed.**
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
     `mi_bhavisya` end as `blocked_dependency` errors (their old rows untouched). No 1216 producer reaches gate_ok. The 1216 gate cannot be met until B-1 and B-2 are decided (section 9, Q1-Q2). **v1.1 update:** PR #2826 (migrations 1212, 1213) is the proposed fix for B-1 and B-2 (a digest spec for `ka_vighnakara`; digest specs for the services `ka_dasha_kala` and `ka_muhurta_seva`); it is open and not applied (Evidence E12), so both blockers stand until it is deployed, verified (P0c.1) and the two services have rebuilt (S1). B-1 and B-2 stay code-derived, not observed. Only a spec (B-1) or a
     contract change to the service receipts (B-2) fixes it; running with `ORCHESTRATOR_DEP_ASSERT=warn` would run the
     consumers but still leave their receipts 'unknown' (not gate_ok), so it does not meet the 1216 gate either.
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
| 1 | bg_transit_rules (GLOBAL L0) | `ka_yojaka`, `ka_sangam`, `ka_gochara` dep; receipt stale `registry_changed`; **stage S0b (v1.2)** | S0b (was 1) | 76 | 104 (v1.2: 105 expected) | 0.04 / 0.04 s writer (2 builds); **executes, not skip** (S0b.2) | t0 | S0b.6 |
| 1b | ka_muhurta_seva (GLOBAL L3 service) | lit but no `asset_freshness` row: planner service exception fails, blocks `ka_sangam`, `ka_vighnakara` (B-3) | 1 | 0 (no data table) | 0 | 0.0 / 0.0 | t0 | 4.2 note |
| 1c | **ka_dasha_kala (per-chart L3 service; v1.1)** | declared dep of `ka_sangam`; receipt `unknown` (no output digest) makes `ka_sangam` unprovable; must rebuild under 1213 before `ka_sangam` (section 1.6) | 1 | 0 (no data table) | 0 | not read (service self-test) | not read | 4.2 note: after S1 its latest receipt is `proven` with a digest |
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
| 17 | **ph_nimitta** | SS wave; stale; 1216 producer | 7 | 4 | 139 | 0.0 / 1.0 | no | 4.3 SQL |
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
`ga_yoga`), so these four will EXECUTE, not skip. `bg_transit_rules` (no dependencies) was predicted in v1.0/v1.1 as the one asset likely to skip
(estimate: code and config unchanged; its stale flag reads `registry_changed` only). **v1.2 correction:** that prediction is withdrawn. The writer source digest differs from the 09-04 receipt (stored `9812db139d56`, `origin/main` `824c6d7d7237`) and the table content moved too (S0b.2), so the pre-execution gate cannot pass and the writer executes; `bg_vedha_malefic_scale` and `bg_vidhi_primitives` likewise execute, `bg_formula_constants` would skip (S0L).

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
| 0 (conditional, v1.1; not part of the 26) | `ga_vargas` only if P0b.4 branch (b); then the six MSR producers `bo_laksana`, `bo_arudha`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`, `bo_nakshatra_semantic` only if any of them must run (section 1.5). Neither is in the v1.0 plan: all six MSR producers read `lit`/`fresh` today (Evidence E12). |
| 1 | ka_muhurta_seva (global, needs super_admin), **ka_dasha_kala (v1.1, per-chart service; must precede `ka_sangam`, section 1.6)**, bo_karanajala, bo_pratijna. **v1.2: `bg_transit_rules` moved out to stage S0b, before this wave; stages S0L and S0c (conditional) also come before S3, see section 8.** |
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

v1.1 ordering additions: (i) `ka_dasha_kala` strictly before `ka_sangam` and `ka_kshetra` (section 1.6); (ii) every MSR producer, if it runs at all, strictly before
every Kala and Phala asset and before the L2 consumers of its signal ids (section 1.5); (iii) `ka_kshetra` is NOT in these 12 waves: it is a separate last stage S7 (section 8.2);
(iv) `bo_pratijna` (wave 1) is gated on P0b, so wave 1 splits operationally: the assets that do not read `chart_divisionals` (`ka_muhurta_seva`, `ka_dasha_kala`,
`bo_karanajala`, and the L0 stages S0b/S0L) may run before P0b holds, `bo_pratijna` and everything after it may not (P0b.2).

### 1.4 Cascade: what the orchestrator does to dependents

Assets downstream of the plan and NOT in it (25 of them, from the live registry): 11 `stale`
(bo_cdlm_summary, bo_chart_gestalt, bo_pramana_mapa, bo_samvada, bo_yantra_mechanism, ka_jivana_parva, ka_taranga, ka_tulana,
mi_abhilekha, mi_seva, ph_rectification), 8 `error` that are cascade victims (ka_kshetra, mi_adhilepa, mi_bhara,
mi_darshana, mi_gunanaka, mi_pariksha, mi_pramana, mi_sambandha), 1 `dormant` (mi_sankalpa) and **5 currently `lit`**:
`bo_laksana_rerank`, `bo_sangati`, `ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_vedha_gochara`.
**v1.2 (17:55Z):** 4 are `lit` now: `ka_gochara_resonance` is `error` (Pravāha's run 1865991c, 17:36:56Z, `DEP-ASSERT ... bg_transit_rules(receipt:stale)`), which makes the `error` cascade-victim count 9.

- If a plan asset completes with `output_changed` TRUE (or not recorded), the 5 lit ones that are downstream of it flip to
  `stale`. Two are direct dependencies of planned assets and would then fail DEP-ASSERT: **`bo_sangati`** (downstream of
  `bo_karanajala`; direct dep of `bo_pratijna`, `bo_drishti`, `bo_anveshana`, `bo_upaya`, `ka_yojaka`, `ph_nimitta`, `ph_sankrama`) and
  **`ka_vedha_gochara`** (downstream of `bg_transit_rules`; direct dep of `ka_sangam`). `ka_gochara_resonance` and
  `ka_moorti_nirnaya` (deps of `ka_gochara`) likewise follow `bg_transit_rules`. **v1.2: for the L0 asset this is expected, not contingent**: its `output_changed` is TRUE (S0b.2), so after S0b `ka_moorti_nirnaya`, `ka_vedha_gochara` (and `ka_gochara`, which S3 rebuilds) read `stale` on the canonical chart and `ka_gochara_resonance` is already `error`; all must be lit and fresh again before S3 (stage S0c).
- Mitigation built into the plan: run `bo_karanajala` first (S1 in section 8), read `build_run_assets.output_changed` for it,
  and only continue if it is FALSE or the contingency set (`bo_laksana_rerank`, `bo_sangati`, with `ka_vedha_gochara`,
  `ka_gochara_resonance`, `ka_moorti_nirnaya` for the L0 asset) has been added. The writers are deterministic
  (estimate: output unchanged on an unchanged input), but 1210 changed the upstream set, so this is checked, not assumed. **v1.2:** for `bg_transit_rules` the contingency set is the planned stage S0c, not an if.
- The 8 `error` cascade victims stay `error` until their own rebuild; `mi_gunanaka` and `mi_pariksha` are the consumers of
  the 1216 edges and are outside this wave. After the wave they remain blocked by `mi_bhavisya`/`mi_pramana` state, which is
  the pre-existing condition (Track I item I-3), not a regression.
- No lit asset outside the 5 above changes state through this wave.

### 1.5 Ordering invariant: MSR writers strictly before the Kala and Phala assets (v1.1; F-3 cascade, SS decision 4 of the F-3 review)

**Invariant.** The six MSR producers (`bo_laksana`, `bo_arudha`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`, `bo_nakshatra_semantic`; the six assets
in `bodha_msr_signals_producer_asset_check`, migration 1036) run **strictly before** the Kala and Phala assets that carry their signal ids, and no MSR writer
rebuilds the same chart again in the same window (from the first such dependent's start until the wave ends). "Strictly before" means an earlier wave: the same wave
is a violation because same-wave assets run in parallel. This is a ledger-level rule, not only a cosmetic order.

**Who is bound (derived from `msr_signal_bearing_tables.json` on PR #2828, not hand-listed).** The 5 Kala assets whose keys 1214 drops (`ka_sangam`, `ka_kalasutra`, `ka_vighnakara`,
`ka_kala_darshana`, `ka_bhavishya_lekha`), `ka_yojaka`, and the Phala assets: `ph_nimitta` plus the 6 reached through `phala_anchors`'s own cascade keys
(`ph_pramana`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`, `ph_pratikara`, `ph_muhurta`), 7 Phala in all; also the L2 consumers that store signal ids
(`bo_karanajala`, `bo_bimba`, `bo_samskara`, `bo_sangati`, `bo_cdlm_summary`, `bo_pratijna`). `ph_phaladesa` and `mi_bhavisya` are not in the map. Of the launch set, 15 assets are bound: 2 L2 consumers (`bo_karanajala`, `bo_pratijna`), `ka_yojaka`, the 5 Kala assets, and the 7 Phala assets
(`bo_karanajala`, `bo_pratijna`, `ka_yojaka`, `ka_sangam`, `ka_kalasutra`, `ka_vighnakara`, `ka_kala_darshana`, `ka_bhavishya_lekha`, `ph_nimitta`, `ph_muhurta`, `ph_pratikara`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`, `ph_pramana`).

**Why it holds today (mechanism).** Until 1214 is deployed an MSR regeneration CASCADE-deletes the `kala_*` rows (and, through `kala_convergence` and `phala_anchors`, the Phala rows)
(F-3 proof: 4 rows to 0 on the disposable cluster). After 1214 the same order keeps references valid instead of merely un-deleted: dependents rebuilt AFTER the MSR set see the final ids.

**It applies to the v4-id charts too.** `signal_id` is uuid v5 (deterministic, `bodha_signal_identity`, migration 661) on the canonical chart (50,678 signals, all v5; F-3 measurement),
but **all uuid v4 on `1c826d5a` (50,171) and `cb73cd3d` (49,875)**: the first v5 regeneration of either chart changes EVERY id and, once 1214 removes the keys, strands 100% of that chart's Kala rows
silently (1c826d5a: 336,093 `kala_activation` rows). So for those two charts the order guard and the pre-wave check are MANDATORY, and per the F-3 review MSR regeneration for them
stays frozen until their Kala rows are re-keyed (F3 open question 3, unanswered). This plan rebuilds the canonical chart only; the statement is recorded so a copy of this plan for another chart is not launched blind.

**How long the rule stays.** Until BOTH (a) migration 1214 (PR #2828) AND (b) the L2-owner-path drop of the 3 L2 foreign keys (grant plan v1.3 Part A, PR #2825) are deployed, because
embeddings and contradictions still cascade until (b) runs. Read live 2026-10-01 about 16:20Z: all 8 keys still exist, neither is deployed (Evidence E12). (Whether (b) is itself safe is
the F3 section 5 prerequisite flagged in P0c.1; if (b) is not made safe, the rule has no end date.)

**Where it sits in this plan.** The v1.0 plan has no MSR writer: all six read `lit` and `fresh` (Evidence E12), so the rule binds only if one must run. Triggers that would make one run:
a `ga_vargas` rebuild (P0b.4 branch (b)) stales `bo_laksana` and `bo_vargottama_dhana`, which are direct dependents of `ga_vargas`; `bo_laksana` is then not lit-and-fresh and `bo_pratijna`'s planner
pre-flight would block on it. Such a run is stage **S0m** (before S1), a separate REVIEW; the six MSR producers go first, then S1 onward as written. A run that contained an MSR producer
**after** `bo_karanajala` or `bo_pratijna` is exactly the violation the guard prints.

**Detector scripts (PR #2828; read-only; not run against production by this lane).**
- `platform/scripts/governance/msr_rebuild_order_guard.py` (order guard): `--manifest FILE` checks a plan (`build_runs.plan_manifest` JSON with `waves`, or a bare list of lists) and exits 1 on any violation; `--require-nonvacuous` exits 1 for a plan that orders nothing; `--chart-id UUID` with `DATABASE_URL`
  runs PF-1 (no in-flight run for the chart) PRE-wave, and with `--post-wave` also PF-2 (every dependent must postdate the last MSR regeneration); `--verify-map` re-reads the live catalog and fails if the dependents map is missing a signal-bearing column.
  **Because this plan stages its runs separately, each run's own manifest orders only that run: the cross-stage check is the guard run on the CONCATENATED waves of all stages** (I ran that DB-free on a copy of the script: the concatenation S0m, then 1.3 waves 1-12, passes with the six MSR producers listed; the same list with `bo_laksana` placed last prints `MSR_NOT_BEFORE_DEPENDENT` against `bo_karanajala`, `bo_pratijna`, `ka_sangam` and the rest; the 1.3 waves alone print VACUOUS).
- `platform/scripts/governance/msr_dangling_signal_refs.py` (post-wave detector): per chart and site, rows referencing a signal that no longer exists (`dangling`), another chart's signal (`cross_chart`) or with a NULL `chart_id` (`unattributable`); tiers `fk_dropped` (the five `kala_*` tables; broken rows fail), `l2_internal`, `unconstrained` (`kala_activation_predicates`, `phala_anchors`; advisory); run with `--chart-id` and `--require-nonvacuous` after the wave (a site with zero referencing rows proves nothing and exits 1 under that flag; default exit 3 INCONCLUSIVE).
  **Limit:** a DELETED referencing row leaves no trace, so the detector cannot see it; that is what the before-state row counts and digests of section 3 (PF-2 of the F-3 review) are for. Live baseline per the F-3 review: 0 dangling over 359k rows on `1c826d5a` and `cb73cd3d`; the canonical chart has zero Kala rows for those tables so every `fk_dropped` site reads vacuous today; `kala_activation_predicates` (never keyed) shows 79 dangling on the canonical chart.

**Pre-flight and post-run additions.** Pre-flight (section 5 rows 14-16): order guard on the concatenated waves, `--verify-map`, PF-1 per chart. Post-run: `msr_rebuild_order_guard.py --chart-id <C> --post-wave` and `msr_dangling_signal_refs.py --chart-id <C> --require-nonvacuous`; on the canonical chart the second is expected to be INCONCLUSIVE/vacuous for the `kala_*` sites until S3-S4 have rebuilt them, and meaningful after.

### 1.6 Ordering constraint: `ka_dasha_kala` precedes the assets that read its output (v1.1)

- **What it is.** `ka_dasha_kala` is a per-chart writer-backed SERVICE (`asset_kind='service'`, `depends_on = {ga_dashas}`, no target table; its writer records a self-test verdict onto its own `asset_registry` row). It is `lit`, `service_health` healthy, last built 2026-09-10 19:26Z, but its latest receipt is `unknown` and its freshness is `unknown` with reasons `output_digest_spec_unavailable` and `output_digest_unavailable` (read 2026-10-01 about 16:20Z, Evidence E12): it has no output-digest spec yet.
- **Who reads its output (declared `depends_on`, live registry).** `ka_sangam` (in the plan), `ka_kshetra` (stage S7), and `ka_jivana_parva` (outside the plan, stale). `ka_vighnakara` does not declare it directly but declares `ka_sangam`.
- **The constraint.** `ka_dasha_kala` must be rebuilt, after migration 1213 is deployed and the `selftest_detail` grant exists, **strictly before `ka_sangam`** (and before `ka_kshetra`). Reason (code-derived, per the 1213 header): `compute_upstream_hash` returns NULL when any declared dependency's receipt has no `output_digest`; `ka_sangam` declares both services; a NULL upstream digest makes `ka_sangam`'s receipt `unknown`, which then DEP-ASSERT-blocks its seven in-plan dependents. 1213 gives each service a digest spec, but receipts only change when the services REBUILD; applying 1213 alone changes none. It must also not be re-stamped again after `ka_sangam` builds, because the upstream digest hashes each dependency's whole receipt including `observed_at`.
- **Where it sits.** Wave 1 of section 1.3, **stage S1** (with `ka_muhurta_seva` and `bo_karanajala`; v1.2: `bg_transit_rules` moved to S0b), i.e. two runs before `ka_sangam` (S3). Consequently **the launch set is 27 assets (26 of v1.0 plus `ka_dasha_kala`): 25 per-chart and 2 global**; the v1.0 pre-flight row 5 ("`ka_dasha_kala` freshness unknown, accepted") is superseded: the planner accepts that shape for a simulation, but accepting it is what leaves `ka_sangam` unprovable.
- **If it is skipped.** The v1.0 prediction stands for `ka_sangam` (lit, receipt `unknown`) and for everything behind it.


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
| bg_transit_rules (global) | `bg_transit_engine`, `bg_transit_rules`, **`bg_transit_moorti` (v1.2)** | none: `seed_transit_rules` upserts, `ON CONFLICT DO UPDATE` (L0 standard); shared by every chart; v1.2: source = live, 0 rows would change, 0 retired (S0b.3) | 76 + 9 + 27 (the registry `count_sql` counts the first only) | 105 (9 + 69 + 27; last real 104) |
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
- **Shared tables:** `bg_transit_engine`/`bg_transit_rules`/`bg_transit_moorti` (global, upsert) are the only shared tables in the plan (v1.2: stage S0L would add `bg_vedha_malefic_scale` and `vidhi_primitives`, also upserts).
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

-- F2  the 1216 gate (verify SQL Q4, /Users/Dev/suvarna-evidence/TrackI/1211_asset_registry_direct_edges_held_verify.sql): gate_ok per producer
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

Target state for the 1216 gate (and for every asset that has a spec): `asset_throughput.state = 'lit'`, latest `asset_freshness` =
`fresh`, receipt `proven`, `output_digest` written, `build_run_assets.state = 'complete'`.

| Asset group | Target after | Predicted on today's code |
|---|---|---|
| `bg_transit_rules` (S0b) | lit, fresh, proven; receipt output digest `ca19407a3e37` (the content already moved since the 09-04 receipt `1983611685a8`); `output_changed` TRUE. **v1.2 withdraws "unchanged, `skip_no_delta`"** | as target if the builder can write `bg_transit_moorti` and `asset_freshness`; otherwise the asset ends `error` (S0b.4, P0.6) |
| Bodha assets (7) | lit, fresh, proven; new `output_digest` only if rows changed | as target if `bo_karanajala` is output-unchanged; else contingency (section 1.4) |
| `ka_avadhi`, `ka_yojaka`, `ka_gochara` | lit, fresh, proven | as target (`ka_avadhi` integrity risk, section 7) |
| `ka_sangam` | lit, fresh, proven | **lit but receipt 'unknown'** (B-2) |
| `ka_kalasutra`, `ka_kala_darshana`, `ka_bhavishya_lekha`, `ka_vighnakara` | lit, fresh, proven (`ka_vighnakara`: impossible, no spec) | all four blocked (`DEP-ASSERT ... ka_sangam(receipt:unknown)`; `ka_vighnakara` additionally cannot be proven) |
| `ph_*` (8) and `mi_bhavisya` | lit, fresh, proven | blocked by `ka_sangam`/`ka_vighnakara` (`blocked_dependency`) |
| Downstream outside the plan | the 5 lit ones stay lit; the stale/error ones unchanged | unchanged |

If B-1 and B-2 are resolved before launch, the target column is the expectation; the 1216 gate (`gate_ok` = state lit AND freshness fresh,
per the 1216 verify SQL's query Q4) additionally requires, for the new consumers' own later builds, that each producer's receipt is proven (that query prints `receipt_state`).

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
| bg_transit_rules | counts 76 / 9 / 27 of the three tables and the content digest (S0b.6) | rows unchanged; receipt digest `1983611685a8` -> `ca19407a3e37`; 3 canonical assets lit -> stale | `ref_transit_rules_get` (mapping not verified); S0b.6 |

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
| 1 | P0 passed (audit grant, phala/mimamsa grants as needed, smoke build) | section P0.3-P0.6 | **PARTIAL (v1.2, 17:55Z)**: audit grant MET (1211 applied, builder audit row written); phala/mimamsa grants true (about 17:48-17:55Z); smoke pre-approved, NOT run; `asset_freshness` and `bg_transit_moorti` write gaps open (rows 21-22) |
| 2 | Deploy idle: no `Deploy to Cloud Run` run with event `workflow_run` or `workflow_dispatch` in progress or pending | `gh run list --workflow deploy.yml --json status,conclusion,headSha,createdAt,event` (the `pull_request` runs are build-checks only and do not deploy) | **v1.2 (18:02Z): idle**: the `workflow_run` deploys listed (36896658202 17:04Z, 36898400004 17:18Z, both for 4eb40bec1; 36893699387 16:40Z for ce52cd5c3) are `completed success`; only `pull_request` build-checks run. Trap 103 (row 20) applies before any of them is read as proof; re-check at launch and re-run the smoke after any deploy that rebuilds the job image. (v1.0: not idle at 15:04Z.) |
| 3 | No in-flight runs for the chart | `SELECT id,state FROM build_runs WHERE chart_id='482012f1-...' AND state IN ('planned','running','paused')` (the unique index enforces this server-side) | 0 at 15:04Z (8684032d failed 15:01); another lane dispatched at 14:57; **v1.2: 0 at 17:58Z** (1865991c, Pravāha, ended 17:36:57Z `failed`); repeat at launch (Q8) |
| 4 | Registry unchanged since this plan | `SELECT count(*), md5(string_agg(asset_id\|\|'>'\|\|coalesce(depends_on::text,''),',' ORDER BY asset_id)) FROM asset_registry WHERE is_active` | 127 assets, md5 `fb7a1090d5aa3c7dabafc9f9daf1ae6a` (2026-10-01T14:49Z; **v1.2: identical at 18:02Z**); latest `_migrations_applied` filename = `1210_asset_registry_direct_edges.sql` (applied 14:37:09Z; v1.2: latest is now `1211_asset_throughput_state_audit_builder_grants.sql`, 17:35:43Z, with `1214` at 17:16:06Z; neither changes `depends_on`); no 1216. The runner also re-checks each planned asset against the frozen manifest at start (a diverged asset fails and blocks its dependents). |
| 5 | Planner preflight clean for the exact request | simulation `preflight_sim.sql` with the 26 ids (Evidence E4); **v1.2: re-run with the live closure, 28 assets today and 30 after S0b (section S0b.5, E13 block K)** | 0 blockers; the only out-of-plan direct deps not 'fresh' are services `ka_dasha_kala` (freshness `unknown`, the exact writer-self-test shape, accepted). **v1.1:** accepted by the planner, but it leaves `ka_sangam` unprovable, so `ka_dasha_kala` is now IN the launch set (section 1.6) and this row is re-run with the 27 ids |
| 6 | Upstream state of out-of-plan deps | rows lit AND fresh for `bo_laksana`, `bo_bimba`, `bo_samskara`, `bo_sangati`, `ga_dashas`, `ga_positions`, `ga_vargas`, `ga_yoga`, `bg_ghatana`, `bg_dignity_reference`, `mi_kula`, `mi_jivanaghatana` | all lit and latest-row fresh at 14:49Z. Caveat: `bo_laksana` and `ga_positions` also carry older partition rows that are stale/unknown; both the planner and DEP-ASSERT read only the latest-observed row, so they pass, but a new observation row would change that. |
| 7 | Job image tag = a commit that contains the L3 fixes (I-1, I-2: PR #2823) and the regenerated writer-digest inventory | the cockpit POST response returns `job_image_tag`; or `gcloud run jobs describe brahma-build-pipeline-job --region asia-south1 --format='value(spec.template.spec.template.spec.containers[0].image)'` (a native/CI act; the reader cannot see it). Compare with `git log -1 -- platform/src/generated/nirmana-writer-digests.json` and `git merge-base --is-ancestor <fix sha> <image sha>` | not readable by this lane. The runner refuses the whole run if the job's writer sources do not hash to the manifest's `expected_code_digest` (`_verify_sidecar_code_matches_manifest`), so a stale image fails closed rather than writing old text. |
| 8 | I-1/I-2 merged | PR #2823 on `suvarna/land/TI-i12-narration-001` | **v1.2: MERGED 2026-10-01 15:37:54Z (066c58587)**. The deploy that carries it to the job image is not established (the deploy run for 4eb40bec1 skipped the pipeline-job image build, P0.6); `ka_avadhi` and `ka_vighnakara` must not run before the job image contains it (row 7, Trap 103). |
| 9 | Held migration 1216 not applied; its gate SQL ready | `1211_asset_registry_direct_edges_held_verify.sql` 1216-verify Q4/Q6 | 1216 held (renumbered from 1211 in v1.2; branch TI-edges-002, commit 086a0fcc5 as recorded in v1.0, not re-verified: the branch is not on origin); `_migrations_applied` shows no `1216_` row (17:55Z). 1211 is now Pravāha's applied audit grant. |
| 10 | Before-state captured (F1, F3, F4, F5) and stored | section 3 | not yet (re-capture at launch) |
| 11 | Protected set unchanged | `SELECT * FROM build_protected_assets WHERE chart_id=...` | 1 row: `ka_gochara_sweep` (not in plan) |
| 12 | No Nirmāṇa campaign wave running | native decision 2026-09-28: campaign OFF; `NIRMANA_SUPERSESSION_RECORD_v1_0.md` section 3 | off (not independently re-verified) |
| 13 | The L1 `ga_dashas` replacement fence is not set | 1070's header mentions a stuck `ga_dashas_replacement_in_progress` guard on the canonical chart; the signal is raised by `ganita_dashas_get` (not a table the reader can see) | unknown; check with one `ganita_dashas_get` call after the smoke |
| 14 | **P0b holds** (v1.1): `chart_divisionals` readable/writable by builder/app roles; owner-path count per chart recorded; `chart_snapshot` canary on 3 charts | section P0b.3 | **v1.2 PARTIAL**: RLS OFF (`relrowsecurity` false), 0 policies, reader count 71,476 (E13); owner-path count, builder probe, `chart_snapshot` canary and ownership gate NOT done (P0b.3). v1.1: FAIL (RLS on, reader 0, fix on hold). |
| 15 | Migration gates for the stages being launched (1212, 1213, 1215; 1214 + L2 drop for the end of the MSR rule) | section P0c.1 verify SQL | **v1.2 (17:55Z)**: 1214 APPLIED (17:16:06Z), the 3 L2 FKs gone (owner path); **1212, 1213, 1215 NOT applied**; no output-digest spec for `ka_vighnakara`/`ka_dasha_kala`/`ka_muhurta_seva`; 0 of 8 MSR FKs present. (v1.1, E12: none applied, 8 FKs present.) |
| 16 | Grant gates per stage (`selftest_detail` for S1, `phala_anchors` for S4, full phala set for S5, mimamsa set for S6, `phala_rectification` for S7) | section P0c.2 `has_*_privilege` | **v1.2 (17:55Z)**: `selftest_detail` UPDATE true, `phala_anchors` SELECT true, `bg_combustion_orbs` SELECT true, phala x8 and mimamsa x2 S/I/D true, functions EXECUTE true; **`phala_rectification` SELECT false (S7)**; plus the two new gaps (rows 21-22). (v1.1, E12: all false.) |
| 17 | MSR order: `msr_rebuild_order_guard.py --manifest <concatenated waves of all stages> --require-nonvacuous`; `--verify-map`; PF-1 on every chart; MSR producers `lit`/`fresh` or S0m planned | section 1.5 | producers lit/fresh (E12); scripts are on PR #2828, not main |
| 18 | `ka_dasha_kala` and `ka_muhurta_seva` ordering: both scheduled in S1, 1213 deployed first | section 1.6 | 1213 not applied (17:55Z) |
| 19 | S7 only: the section 8.2 pre-check (image carries #2830, instance/connector health, ledger state, dependencies, `phala_rectification` ruling) | section 8.2 | #2830 open; `phala_rectification` SELECT false; instance not restarted since 2026-08-17 |
| 20 | **Trap 103 (v1.2): a "deployed" claim is verified, not read off the run list** (migration, grant, writer change) | P0.6, "Post-deploy verification" | two `workflow_run` deploys listed for 4eb40bec1, both `success`; the carrying run skipped the pipeline-job image build; 1211 verified by catalog |
| 21 | **Builder write path for receipts (v1.2): `asset_freshness` INSERT and UPDATE for `data_plane_builder`** (gates the S0 smoke and every stage) | P0.3 check 1b | **false** (17:55Z); code-derived outcome: `error` (or stuck `building` on the delta-skip path) at the receipt step; ask Pravāha whether another path writes it |
| 22 | **S0b only (v1.2): `INSERT, UPDATE ON bg_transit_moorti`** | P0.3 check 1b, S0b.4 | **false** (17:55Z); S0b would end `error` |
| 23 | **S0b only (v1.2): the job image carries #2727 (b6690928f) and the digest-inventory entry `824c6d7d7237...` for `bg_transit_rules`** | cockpit `job_image_tag` / job description; S0b.8 item 3 | not readable by this lane; the 1211-carrying deploy skipped the job-image build |
| 24 | **S0b / S0L (v1.2): no active run on any chart, global-assets lock free, Pravāha told before the run, `super_admin` session** | `SELECT ... FROM build_runs WHERE state IN ('planned','running','paused')`; S0b.8 items 4-5 | 0 active at 17:58Z |
| 25 | **S0c / S3 (v1.2): the Gochara trio `ka_gochara_resonance`, `ka_moorti_nirnaya`, `ka_vedha_gochara` lit AND fresh, and `bg_vedha_malefic_scale` fresh, before S3** | F1 query for the four ids | `ka_gochara_resonance` error; the other two lit today but flip stale at S0b; `bg_vedha_malefic_scale` stale |

**Post-run checks:** the run is `completed` with every asset `complete` (or `error` only as predicted in section 3.3); F1 expected states;
F3/F4 counts and digests against section 2 and section 4 canaries; audit rows for each state change (`db_user`); no asset left `building`;
`ph_nimitta`, `bo_pratijna`, `ka_yojaka`, `mi_bhavisya` gate SQL (1216-verify Q4) printed; other-chart canaries (F5) identical; the 25 downstream assets
(F6) in the states of section 1.4; the 1216 gate decision recorded.

## 6. EXPECTED DURATION

Source: `build_run_assets` for this chart (state `complete`, `skip_no_delta` rows excluded, started/ended recorded), medians and
maxima; Evidence E6 (`timing_out.txt`); `writer_timeout_seconds` from `asset_registry`.

| Group | Assets | Sum of medians | Sum of maxima | Per-asset budget (`writer_timeout_seconds`) |
|---|---|---|---|---|
| G1 Bodha (+ L0/service first) | ka_muhurta_seva (v1.2: `bg_transit_rules` is S0b, 0.04 s writer), bo_karanajala, bo_pratijna, bo_drishti, bo_cgm_motifs, bo_cgm_paths, bo_anveshana, bo_upaya | 2.6 min | 31.6 min | 10800 s each (`bo_laksana_rerank` 600 s is not in the plan) |
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

**v1.2 additions to the window.** S0b and S0L are global-asset runs: writer time 0.03-0.06 s each, run overhead dominated by job start (median 25 s creation to end for single-asset runs, E6); allow 5 minutes per run. S0c (Gochara trio) durations were not read; they are Pravāha-family assets and sit before S3. The 27-asset serial sum above is unchanged apart from moving `bg_transit_rules` out of G1.

## 7. RISKS AND ROLLBACK

### 7.1 Risk register

| # | Risk | Evidence / mechanism | Impact | Mitigation in this plan |
|---|---|---|---|---|
| R-1 | The builder cannot complete any run (audit trigger) or write phala_/mimamsa_ tables | P0.1, P0.2 | No data changes; runs end `failed`; Stages 4-6 impossible | P0 gate; smoke build first |
| R-2 | **B-1 / B-2 / B-3: the wave cannot reach 'proven' for the Phala/Mimāṃsā half** | section 0 items 1-2 (code-derived) | Predicted partial result: S0-S3 land except `ka_kalasutra`; `ka_sangam` lit with receipt 'unknown'; `ka_kalasutra`, `ka_vighnakara`, `ka_kala_darshana`, `ka_bhavishya_lekha`, `ph_*`, `mi_bhavisya` end `error` with `blocked_dependency` (their old rows untouched); the 1216 gate stays closed | Decide Q1/Q2 before S4; rehearse off production (E5.6 style) or run Stages 1-3 only |
| R-3 | A delete-then-insert replaces rows in place and is not reversible by this lane | writers (section 2) | If new rows are wrong, old rows are gone | before-state digests (section 3) prove WHAT changed but are not a backup; need a native-held restore point (Q6) |
| R-4 | `ka_avadhi` integrity failure again | 3 failures on 2026-09-10; conjuncts (c),(e) false on today's data | asset `error`; light writer rolls back, so prior 1169 rows are preserved | run after `bo_pratijna` and after I-1/M4 is deployed; if it fails read `build_run_assets.error` before retry |
| R-5 | `bo_karanajala` output changes, staling `bo_sangati` etc. mid-plan | section 1.4 | S2 assets (`bo_pratijna`, `bo_drishti`, `bo_anveshana`, `bo_upaya`, then `ka_yojaka`, `ph_nimitta`, `ph_sankrama`) fail DEP-ASSERT `bo_sangati(stale)` | S1 isolates `bo_karanajala`; read `output_changed` before Stage 2; contingency set pre-computed |
| R-6 | `mi_bhavisya` run before `ph_nimitta` is restored | 139 pending predictions replaced by about 4 | loss of 135 rebuildable predictions (ids `pred_<anchor_id>` are deterministic so a later rebuild restores them) | strict last position; S6 gate: `phala_anchors` count about 139 |
| R-7 | Orphan watchdog kills a long light writer | `watchdog/route.ts`: a `running` run older than 30 min with no building asset whose `last_built_at` advanced in 15 min and no substep completed in 15 min is marked `failed`; a `building` asset with `last_built_at` older than 15 min is set `error` (heavy writers with a completed substep plan are handled separately). Light writers have no mid-run heartbeat. | `bo_karanajala` (max 1091 s), `ka_kalasutra` (650 s) could be reaped mid-transaction; the transaction is not committed so no partial rows, but the asset reads `error` | S1 runs `bo_karanajala` with the two global assets and is watched; `ka_sangam` has substeps (heartbeat per substep) so it is covered; native decides on the watchdog cadence for the window |
| R-8 | Another lane dispatches on the chart | run 8684032d at 14:57Z | 409 `RUN_ACTIVE` for us, or a collision if checked late | check #3 at launch; coordinate (Q8) |
| R-9 | Global assets: `bg_transit_rules` (upsert) is shared by every chart | section 2 | a changed seed would reach all charts | **v1.2: it executes, it does not skip** (S0b.2); source = live, so 0 rows change (read-only comparison); `output_changed` TRUE flips 3 canonical assets stale; other charts are not flipped; `super_admin` only; stage S0b; Q3 resolved by SS (L0 first) |
| R-10 | `ka_gochara` is Gochara-family adjacent: its registry `count_sql` is misdirected (reads generation 4.0 of `kala_gochara_windows`, 0 rows; the writer's table is `kala_gochara_windows_v2` generation 2.0, 87 rows) | section 2 | the cockpit count cannot confirm it; a run is blocked by the Pravāha lane if it holds the chart | include only if SS confirms ownership (Q5); needed because `ka_sangam` depends on it |
| R-11 | Code/image skew | check #7 | run fails closed (`code digest` mismatch) | confirm image tag before launch |
| R-12 | **RLS-blind `chart_divisionals`** (v1.1): a writer that reads it under the builder gets 0 rows; a `ga_vargas` rebuild would probably finish `lit` with 0 rows and a green check | P0b; incident review F1 (inferred from code, not exercised) | `bo_pratijna` built from nothing; derived tables stale-correct today but the next build would compute from empty | P0b gate; no `ga_vargas` rebuild and no MV refresh before it; post-run read of `bodha_pratijna` and, if S0v runs, the table count |
| R-13 | **MSR rebuild cascade / dangling ids** (v1.1): an MSR producer after a dependent strands or deletes Kala/Phala rows; the v4-id charts lose everything silently once 1214 lands | section 1.5; F-3 proof (4 rows to 0) | irreversible loss of `kala_*` rows (delete-then-insert class, section 7.3) | order guard on the concatenated waves, S0m placement, detector post-wave, before-state counts (PF-2); do not regenerate MSR for `1c826d5a`/`cb73cd3d` |
| R-14 | **`ka_sangam` unprovable if `ka_dasha_kala`/`ka_muhurta_seva` are not rebuilt under 1213** (v1.1) | section 1.6 | S3-S6 cascade-block | 1213 deployed and verified before S1; both in S1; receipts checked `proven` before S3 |
| R-15 | **`ka_kshetra` connection loss / stall loop** (v1.1): 115 historical run rows, 7+ kill-and-redispatch cycles on 2026-09-11, last run lost its connection | section 8.2 | hours of compute, a partially-written `kala_field`; a repeated loop | own stage S7, last; pre-check; stop rule; ONE redispatch; #2830 bounds the loss to one part but does not prevent the reset |
| R-16 | **Migrations/grants not yet deployed** (v1.1): 1212-1215, the grant plan, #2830, #2823 are all open PRs | P0c, Evidence E12 | stages launched ahead of their gates fail or silently degrade (S1 services, S4 `phala_anchors`) | per-stage gates in the section 8 table; do not launch a stage whose gate row of section 5 is red (v1.2: 1214, 1211 and the grant-plan grants are applied; 1212, 1213, 1215, #2830, #2825 are not) |
| R-17 | **The builder cannot write `asset_freshness` (v1.2)**: receipts persist and delta-skip re-stamp both upsert it | P0.6 item 1; `provenance.py` `_upsert_freshness_row` since 2026-08-25; builder INSERT/UPDATE false (table and column) | every stage, including the S0 smoke, ends `error` at the receipt step (code-derived); light writers roll back, no data change; the smoke asset ends `error` or stuck `building` until reaped | P0.3 check 1b before the smoke; ask Pravāha for the receipt-write path; a grant (not drafted here) clears it |
| R-18 | **The builder cannot write `bg_transit_moorti` (v1.2)**: the `bg_transit_rules` writer upserts 27 rows into it | S0b.4; ACL `data_plane_builder=r` | S0b ends `error`, `bg_transit_rules` throughput lit -> error (worse for Pravāha), no data change | grant `INSERT, UPDATE` first; gate row 22 |
| R-19 | **Job image not rebuilt / not known (v1.2)**: the deploy that carried 1211 skipped "Build & Deploy Pipeline Job Image"; Trap 103 | P0.6, run 36898400004 | the run is refused at the manifest code-digest check (fail closed) or runs a writer older than #2727 | S0b.8 item 3; read `job_image_tag`; row 23 |
| R-20 | **S0b forces follow-on rebuilds (v1.2)**: 3 canonical assets flip stale, `ka_gochara_resonance` is `error`, `ka_vedha_gochara` needs `bg_vedha_malefic_scale` fresh | S0b.5, S0L | `ka_sangam` and `ka_gochara` (S3) blocked until S0c; Gochara-family assets belong to Pravāha's lane | stage S0c, S0L (`bg_vedha_malefic_scale`); tell Pravāha before S0b; Q18 |
| R-21 | **A `bg_panchanga` probe rebuild stales 15 canonical lit assets (v1.2)**, incl. the MSR producer `bo_laksana` and `bo_sangati` | S0L; probe records no `output_changed` (code-derived) | MSR-before-Kala/Phala invariant broken; S2/S3 DEP-ASSERT failures | do not rebuild `bg_panchanga` in this wave |

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

| Run | Request body (`POST /api/cockpit/runs`, `scope:"asset_set"`, `action:"rebuild"`, `chart_id:"482012f1-710e-4a25-994a-93821f5871aa"`) `scope_target` | Gate BEFORE the run (v1.1; v1.2) | Gate before next run |
|---|---|---|---|
| S0 smoke | `ka_tithi_pravesha` | P0 audit grant **MET** (P0.6); smoke **pre-approved by SS**; P0.3 check 1b first (row 21) | P0.4 criteria 1-6 (incl. the `asset_freshness` write path proven) |
| **S0b (v1.2)** | `bg_transit_rules` (**global; `super_admin`**; exact shape in S0b.7) | smoke passed; `bg_transit_moorti` INSERT/UPDATE; job image carries #2727; no active run; Pravāha told (S0b.8) | `bg_transit_rules` lit, fresh, proven, digest `ca19407a3e37`, `output_changed` TRUE; the 3 canonical flips recorded; counts 76/9/27; Pravāha's planner pre-flight re-run |
| **S0L (v1.2, optional)** | `bg_vedha_malefic_scale` (+ optional `bg_vidhi_primitives`); not `bg_panchanga`, not `bg_formula_constants`; `bg_ephemeris_engine` only with Pravāha notified (section S0L) | S0b complete; smoke passed; no active run; `super_admin` | receipts fresh/proven; 0 row changes; the flips of S0L recorded |
| **S0c (v1.2, conditional)** | `ka_gochara_resonance,ka_moorti_nirnaya,ka_vedha_gochara` (Gochara family: Pravāha's lane or this wave, Q18) | S0b complete; `bg_vedha_malefic_scale` fresh (for `ka_vedha_gochara`); their target-table grants (only `gochara_resonance_map` was re-checked) | all three lit AND fresh; `ka_sangam`/`ka_gochara` pre-flight (rows 5, 25) clean |
| S0v (conditional) | `ga_vargas` | P0b holds AND the owner-path count shows the table deleted/partial (P0b.4 branch b); otherwise this stage does not exist. A separate REVIEW (61-asset downstream closure). | owner-path count after equals writer rows written; section 1.5 binds the downstream |
| S0m (conditional) | the MSR producers that must run, in one run | P0b (for `bo_laksana`); order guard on the concatenated waves passes; 1214 + L2 drop NOT yet deployed means cascade risk (section 1.5) | order guard `--post-wave` and detector pass; every producer `complete` |
| S1 | `ka_muhurta_seva,ka_dasha_kala,bo_karanajala` (`super_admin` required: one global asset; v1.2: `bg_transit_rules` moved to S0b) | P0; **1213 deployed and verified**; **`selftest_detail` grant** (P0c.2) | all three `complete`; `bo_karanajala.output_changed` FALSE (else add the contingency set); both services' latest receipt `proven` with `output_digest`; F1 |
| S2 | `bo_pratijna,bo_drishti,bo_cgm_motifs,bo_cgm_paths,bo_anveshana,bo_upaya` | **P0b holds** (`bo_pratijna` reads `chart_divisionals`) | all `complete`; 1216-verify Q4 for `bo_pratijna`; `bodha_pratijna` row count 135-ish, not 0 |
| S3 | `ka_gochara,ka_yojaka,ka_sangam` (+ `ka_avadhi` only after **1215** and the I-1 fix (#2823) are deployed) | S1 receipts as above (else `ka_sangam` cannot be proven); 1215 for `ka_avadhi`; **v1.2: S0c done (the Gochara trio lit and fresh)** | `ka_yojaka` lit/fresh/proven; `ka_sangam` lit AND freshness `fresh` (B-2 fixed by 1213 + S1; else S4+ cannot pass) |
| S4 | `ka_kalasutra,ka_vighnakara,ka_kala_darshana,ka_bhavishya_lekha` | **1212 deployed and verified**; I-2 fix (#2823) deployed; **`phala_anchors` SELECT** before this run; `bg_combustion_orbs` SELECT for a non-fallback `ka_vighnakara` | all four `complete`; `ka_vighnakara` receipt `proven` |
| S5 | `ph_nimitta,ph_muhurta,ph_pratikara,ph_sankrama,ph_sodhana,ph_suddha_sodhana,ph_pramana,ph_phaladesa` | the full phala grant set (P0c.2) and B-1/B-2 resolved | `phala_anchors` about 139 |
| S6 | `mi_bhavisya` | `mimamsa_*` grants + N-46 guard; orphan check = 0 | 1216-verify Q4 for all four producers, then 1216 may be proposed |
| S7 | `ka_kshetra` (own stage, section 8.2) | section 8.2 pre-check; #2830 merged and deployed; the held `phala_rectification` ruling; `bo_pratijna`, `bo_upaya`, `ka_dasha_kala` rebuilt (S1-S2) | section 8.2 stop rule |

Post-run for every stage that contains a bound asset (section 1.5): `msr_rebuild_order_guard.py --post-wave --chart-id <C>` and `msr_dangling_signal_refs.py --chart-id <C> --require-nonvacuous`.

### 8.2 Stage S7: `ka_kshetra` (own stage, pre-check, stop rule, single redispatch) (v1.1)

**Why separate.** `ka_kshetra` (per-chart, `kala_field`, `writer_timeout_seconds` 86400) is a heavy, ledgered writer; nothing in the launch set depends on it (its only dependents are `mi_bhara`
and `mi_sankalpa`, outside the plan), so it runs LAST and its failure cannot strand any 1216 producer. It is not part of the 27-asset launch set. It currently reads `error` (a cascade victim, section 1.4).

**What happened on 2026-09-11 (read live, Evidence E12).** For this chart, `build_run_assets` holds 115 rows for `ka_kshetra` between 2026-08-05 and 2026-09-11 (86 error, 10 aborted, 11 complete, 8 queued). The last run (`6e47cae4`, 01:48 to 03:50Z) ended `worker_crash: OperationalError: the connection is lost`; the
seven runs before it (the most I read; the query was limited to the 8 newest) were kill-and-redispatch cycles for log stalls (one `last_error` reads "29th application" of the recipe). The writer's resume ledger (`build_substep_progress`) holds 279 completed substeps for the chart, the newest `stage5dhara:major_loss:1` at 03:22Z, so
the loss fell inside the next, long per-class windows substep. The instance itself was not restarted that day: `pg_postmaster_start_time()` reads 2026-08-17 17:51Z (the failure was a connection, not a database restart; the exact cause, a connector/proxy reset, is the coordinator's reading and is not recorded in `build_runs`).

**What PR #2830 does and does not do.** It splits each event class's dhara windows substep (`stage5dhara:{ec}:2`) into 20 time-part substeps (`stage5dhara:{ec}:2:{p}`, `WINDOW_PARTS = 20`), each owning one half-open `t_start` slice, written by natural-key upsert with no
per-part delete, and keeps a resume ledger so that a redispatch loses at most ONE part; a legacy receipt `stage5dhara:{ec}:2` counts as "all parts of that class done" and `_RESUME_VERSION` is not bumped, so an in-flight ledger stays valid. It **would NOT have prevented the reset**; it only bounds what a reset costs. It changes the writer file, so the digest inventory (`nirmana-writer-digests.json`) moves and the job image must carry it (section 5 row 7). Whether the existing 279-substep ledger's `build_fingerprint` still matches after the change was not verified.

**Pre-check (all read-only, immediately before dispatch; the instance/connector part is an executor act the reader cannot do).**
1. #2830 merged AND deployed; image tag contains it; the cockpit's `job_image_tag` shown; the fixed writer's digest equals the manifest's.
2. No `planned/running/paused` run on ANY chart (the unique index only guards per chart; a competing job loads the same instance).
3. Instance and connector health, by the executor, from the platform side: the Cloud SQL instance `RUNNABLE`, no maintenance window or failover scheduled inside the next 6 hours, no connector/proxy restart or deploy of the job image in progress, and connection headroom against `max_connections` (read 50 at 16:21Z as the reader; the reader cannot see other roles' sessions, so headroom must be read as an admin). If the Cloud Run job is launched through a proxy session, that proxy is freshly started for this run.
4. Ledger state recorded: count and newest `completed_at` of `build_substep_progress` for (`ka_kshetra`, chart), and the decision resume-vs-replan written down (a resume is only valid if the stored `build_fingerprint` matches; unverified).
5. Dependencies lit and fresh: `ka_dasha_kala`, `ka_gochara_resonance`, `ga_panchanga`, `bo_pratijna`, `bo_sangati`, `bo_upaya`, `bg_cohort`, `bg_class_lifetime_counts`, `ka_vedha_gochara`. `bg_transit_rules` re-stamp or a changed `bo_karanajala` can stale `ka_gochara_resonance`, `ka_vedha_gochara`, `bo_sangati` (section 1.4): re-read after S3.
6. `phala_rectification` SELECT resolved (held by migration 1073, grant plan section 3.2): without it the writer's uncertainty stage cannot read it; behavior on denial is not verified, so this is a go/no-go item.

**Stop rule** (the thresholds below, 15 minutes and 6 hours, are this lane's proposals for SS to set, not read from any system). Evaluate at fixed intervals while the run is `running`. STOP (request the run's stop; section 7.2 records that the orchestrator honours stop between assets, not mid-asset, and whether it honours it between substeps of a heavy writer was not verified, so a stop may wait for the current part) and report to SS if ANY holds: (a) no new row in `build_substep_progress` for 15 minutes while the run is `running` (an in-flight part should finish in far less; the 2026-09-11 recipe used a 240 s log-silence bar); (b) the run ends `failed` or `error`; (c) a part's rows or the stage-5 class completeness check (`_verify_class_windows_complete`, run by the last part of each class) fails; (d) the instance/connector pre-check regresses mid-run. **No kill-and-redispatch on a stall**: the 09-11 pattern of 29 cycles is exactly what this rule forbids.

**Single-redispatch rule.** At most ONE redispatch of `ka_kshetra` per stage, and only when the failure is a connection loss (the run's error is `OperationalError` / "connection is lost" / `orphaned_by_crash` after such a loss) AND the pre-check items 2, 3 and 5 are re-passed AND the ledger shows progress. The redispatch resumes from the ledger and so loses at most one part (#2830). A second failure of any kind, or a first failure of any other kind (integrity check, `UpstreamStageIncomplete`, timeout, grant error), ends the stage: no third attempt, no re-plan, the state is handed to SS with the ledger count, `build_run_assets.error` and the audit rows.

Clicks (if the cockpit UI is used instead of a raw call): Nirmāṇa cockpit page for the chart -> select the asset list of the stage -> action
"Rebuild" -> confirm the plan preview (it shows `plan`, `asset_count`, `job_image_tag`) -> submit; do not tick "clear before build". The response
`run_id` is then followed in `build_runs` / `build_run_assets` with the F7 queries. If the planner answers `UPSTREAM_BLOCKED`, the `blockers` list is the
exact set to add or the exact gate that failed; do not retry blindly.

Who executes: the native, or an owner/`super_admin` session SS designates; this lane cannot launch a production build and must not. Before any
launch SS reviews this document and records the decision (REVIEW) and the pre-flight in section 5 is run by the executor.

## 9. OPEN QUESTIONS FOR SS

1. **B-1.** `ka_vighnakara` has no output-digest spec (migration 1034 calls it a blocked contract: no stable non-null unique key in `kala_obstruction`). Decide:
   design a key and spec (a migration; not drafted here), or change the contract so `ka_bhavishya_lekha` and the consumers need not hold a proven
   `ka_vighnakara` (which also changes 1216's premise). Without one of these `ph_nimitta`, `ph_pramana`, `ph_phaladesa`, `mi_bhavisya` cannot become proven. **v1.1:** PR #2826 migration 1212 is the first option (a spec over the whole projection); it is open, unapplied; SS decides whether to land it.
2. **B-2.** `ka_sangam` declares services `ka_muhurta_seva` and `ka_dasha_kala` whose receipts carry no `output_digest`, so its upstream digest is NULL and its
   receipt 'unknown'. Is the intended contract that a healthy writer-backed service yields a probe digest (the `compute_upstream_hash` comment says so)? If yes, those two
   service receipts need to be produced; if no, the gate for `ka_sangam` consumers must be re-stated. A one-asset rehearsal of this path off production is cheap. **v1.1:** PR #2826 migration 1213 is the 'produce the digest' option (specs over each service's own `asset_registry` row); it only takes effect after both services rebuild, so `ka_dasha_kala` joins S1 (section 1.6). Two caveats it records itself: `ka_muhurta_seva` declares no `source_paths`, so a change to the panchang/muhurta engines is not hashed into its code digest (a stale 'healthy' is possible), and the canonical-chart pin on the 1212 spec means other charts' `ka_vighnakara` receipts digest the canonical chart's rows.
3. **Global assets in a canonical-chart wave.** `bg_transit_rules` and `ka_muhurta_seva` are global and need `super_admin`; the campaign plan keeps L0 as separate
   global-grant waves. Is a global re-stamp inside this wave acceptable, or should the registry-changed receipts of the L0 assets be cleared by the L0 wave first (S1 then shrinks to `bo_karanajala`)? **v1.2: decided by SS 2026-10-01: L0 first. `bg_transit_rules` is stage S0b; S1 keeps `ka_muhurta_seva` (global), `ka_dasha_kala`, `bo_karanajala`.**
4. **Protected-table definition.** `bodha_*` tables are `data_plane_l2_owner` tables and 7 plan assets write them (through the L2 generation contract). Does "no protected table"
   cover them? If yes, S2 and `bo_pratijna` itself fall out of this wave.
5. **Ownership of `ka_gochara`** (Gochara/Pravāha family adjacency; the 8684032d run on `ka_gochara_resonance` suggests an L3 lane is active there). May this wave rebuild `ka_gochara`, or does that lane do it first?
6. **Restore point.** Is a native-held Cloud SQL backup/PITR marker taken before S1 (this lane cannot see or create one)? Without it every stage is irreversible.
7. **Why are the canonical L3 rows empty?** `kala_convergence`, `kala_obstruction`, `kala_activation`, `kala_darshana`, `kala_bhavishya`, `phala_sodhana` hold 0 canonical rows while their last real builds wrote 14868, 536, 335403, 750, 100 and 97. Cleared by a lane, a correction, or lost? The plan assumes "cleared, to be rebuilt".
8. **Coordination.** Another lane planned a canonical-chart run today (8684032d, 14:57Z). Who holds the chart's build slot during the window, and is Pravāha's grant migration the only fix on the way?
9. **Split decision.** If the phala_/mimamsa_ grants are not coming soon, do we launch Stages S0-S3 (Bodha and Kāla core) and defer S4-S6, or hold the whole wave? **v1.1 restatement:** the clean split is by gate, not by layer: S0, S1 (needs `selftest_detail`, 1213), S2-S3 (need P0b, 1215 for `ka_avadhi`) can run without the phala/mimamsa grants; S4 needs `phala_anchors` SELECT and 1212; S5-S6 need the full set; S7 needs the held `phala_rectification` ruling.
10. **Timing vs deploy.** The wave must not straddle a deploy (the image changes mid-run; the digest check then fails closed). Is the window to be scheduled after the L3 fix PR #2823 deploys, with a deploy freeze for about 4 hours?
11. **Action semantics.** `rebuild` (explicit) vs `build` (planner picks non-fresh): equal for this set by construction; `rebuild` is used. Confirm, and confirm `NIRMANA_FORCE_EXECUTE` stays unset so unchanged inputs delta-skip rather than rewrite.
12. **(v1.1) The incident-fix hold.** The `chart_divisionals` access fix (Option D, approved hashes in P0b.1) is ON HOLD after the owner's "any which way, we will rebuild it". Is the hold lifted for the access fix only (not for any rebuild), so that P0b can hold before S2? Without it S2 and everything behind it are not launchable. And does SS want the owner-path COUNT (read-only, rolled back, hash `6d9745dd...953f`) run first, which alone decides whether S0v exists?
13. **(v1.1) `ga_vargas`.** If the count shows deleted/partial data, is a `ga_vargas` rebuild plus the downstream closure a separate REVIEW (as drafted), and who explains the delete first?
14. **(v1.1) Order guard wiring.** Run the guard on the concatenated stage waves as a manual pre-flight (as drafted), or wire it to the cockpit plan step (not on main; PR #2828 ships scripts only)? And the F3 section 5 prerequisite for the L2 FK drop (child-delete scope for root MSR writers) and F3 open question 3 (v4-id charts: re-key or freeze) remain unanswered.
15. **(v1.1) `ka_kshetra`.** Resume from the existing 279-substep ledger (fingerprint match unverified) or re-plan? Is the held `phala_rectification` grant (1073) lifted for S7, or does S7 stay out of this wave? Are the stop-rule thresholds (15 min no-progress, 6 h maintenance look-ahead) acceptable?
16. **(v1.2) Two builder write-path grants.** `INSERT, UPDATE ON asset_freshness` (the receipt path of every run) and `INSERT, UPDATE ON bg_transit_moorti` (S0b) are false for `data_plane_builder`, and neither is in the grant plan, 1070 or 1073. Who ships them (Pravāha, as the grant owner), and does SS hold the pre-approved smoke until the `asset_freshness` question is answered (P0.6 item 1), or fire it as the proof and accept an `error` on a leaf asset?
17. **(v1.2) S0b request and effect.** Confirm the shape (`asset_set`, canonical chart, `super_admin`, S0b.7) and accept its effect: `output_changed` TRUE, three canonical lit assets flipped stale (`ka_gochara`, `ka_moorti_nirnaya`, `ka_vedha_gochara`), other charts untouched.
18. **(v1.2) Gochara trio ownership (Q5 restated).** After S0b, `ka_gochara_resonance` (`error`), `ka_moorti_nirnaya` and `ka_vedha_gochara` must be lit and fresh before S3, and `ka_vedha_gochara` needs `bg_vedha_malefic_scale` fresh. Does Pravāha's lane rebuild them (it is already trying `ka_gochara_resonance`), or is this stage S0c of this wave (31 assets in total)?
19. **(v1.2) L0 freshness scope.** Run S0L as `bg_vedha_malefic_scale` only (required in effect), optionally `bg_vidhi_primitives`; skip `bg_formula_constants` (nothing to build; the stale row is a legacy partition), `bg_panchanga` (stales 15 canonical assets) and `bg_ephemeris_engine` (needs Pravāha notified, ends `unknown`, not `fresh`)? And is the probe-path digest fix (spec row plus an orchestrator change, S0L) wanted at all, as a separate freeze-exception review? Not needed by the 27.

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
select asset_id, depends_on, writer_timeout_seconds from asset_registry where asset_id in (<the 8 named>);   -- live depends_on as read; held 1216 edges are NOT present
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
`00_ARCHITECTURE/control/suvarna/plan_model.json` (E5.3, E7.1-E7.3 superseded by S0.C6), branches `suvarna/land/TI-edges-002` (1216 held, 086a0fcc5) and
`suvarna/land/TI-i12-narration-001` (no commits ahead of main at 14:51Z), `00_ARCHITECTURE/briefs/suvarna/exec/TRACK_I_FIX_ITEMS.md` (I-1, I-2, I-3).

### E12. v1.1 live re-read and branch evidence (2026-10-01T16:27:49Z, `suvarna_reader`, SELECT and catalog reads only)

Branch heads read with `git show origin/<branch>:<path>` (all PRs OPEN, none merged, when read): `suvarna/land/grant-plan-001` 51f55f095 (BUILDER_GRANT_PLAN v1.3, PR #2825); `suvarna/land/incident-divisionals-001` e9231cd7c (INCIDENT_CHART_DIVISIONALS_REVIEW v1.0, status SS-APPROVED-ON-HOLD, PR #2833);
`suvarna/land/TI-i45-provenance-001` 83826bbc7 (migrations 1212, 1213, PR #2826); `suvarna/land/TI-i8-avadhi-integrity-001` c56e58ee2 (migration 1215, PR #2827); `suvarna/land/F3-msr-fk-drop-001` cef41cd10 (migration 1214, `msr_dangling_signal_refs.py`, `msr_rebuild_order_guard.py`, `F3_MSR_FK_DROP_v1_0.md` v1.1, PR #2828);
`suvarna/land/TI-i10-kshetra-substeps-001` 39012df06 (ka_kshetra writer, PR #2830). PR states from `gh pr view`. Not re-verified here: any figure those documents carry that this lane did not re-read (for example the 71,476 `reltuples`, 6,247 pages, the F-3 proof outcomes, the 359k-row detector baseline, the 41-of-47 `kala_*` table grant count) stays attributed to its document.

Local DB-free run (no database, copy of the PR #2828 scripts in the scratchpad): `msr_rebuild_order_guard.py --self-test` PASS; `--manifest` on (S0m six MSR producers, then section 1.3 waves 1-12 with `ka_dasha_kala` in wave 1): PASS, 0 violations, six MSR writers listed; the same with `bo_laksana` moved to the last wave: `MSR_NOT_BEFORE_DEPENDENT` against `bo_karanajala`, `bo_pratijna`, `ka_bhavishya_lekha`, `ka_kala_darshana`, `ka_kalasutra`, `ka_sangam` and others; section 1.3 waves without any MSR producer: PASS but VACUOUS ("no MSR writer in the plan").

Live reads, statements:
```sql
-- B  chart_divisionals
select c.relname, pg_get_userbyid(c.relowner) own, c.relrowsecurity, c.relforcerowsecurity, (select count(*) from pg_policy p where p.polrelid=c.oid) policies, row_security_active(c.oid) rsa from pg_class c where c.relname='chart_divisionals' and c.relkind='r';
select count(*) as reader_count from public.chart_divisionals;
select has_table_privilege('data_plane_builder','public.chart_divisionals','SELECT') b_select, has_table_privilege('data_plane_builder','public.chart_divisionals','INSERT') b_insert;
-- C  state (canonical chart, latest freshness row per asset)
select t.asset_id,t.state,to_char(t.last_built_at,'YYYY-MM-DD HH24:MI') lb,t.rows_written rw,f.freshness_state fr from asset_throughput t left join lateral (select freshness_state from asset_freshness a where a.asset_id=t.asset_id and a.chart_id is not distinct from t.chart_id order by observed_at desc limit 1) f on true where t.chart_id='482012f1-710e-4a25-994a-93821f5871aa' and t.asset_id in ('ga_vargas','bo_laksana','bo_arudha','bo_special_lagna','bo_sudarshana','bo_vargottama_dhana','bo_nakshatra_semantic','ka_dasha_kala','ka_kshetra') order by 1;
-- D  registry edges
select asset_id, depends_on from asset_registry where is_active and 'ga_vargas'=any(depends_on) order by 1;
select asset_id, depends_on from asset_registry where is_active and 'ka_dasha_kala'=any(depends_on) order by 1;
select asset_id, asset_kind, scope, depends_on from asset_registry where asset_id in ('ka_dasha_kala','ka_kshetra');
-- E  ka_dasha_kala receipt and freshness
select asset_id, receipt_state, left(coalesce(output_digest,''),12) od, observed_at from asset_provenance_receipts where asset_id in ('ka_dasha_kala','ka_muhurta_seva');
select asset_id, freshness_state, reasons, observed_at from asset_freshness where asset_id='ka_dasha_kala' order by observed_at desc limit 1;
-- F  migrations, specs, keys
select filename, applied_at from _migrations_applied order by applied_at desc limit 1;
select count(*) from asset_output_digest_specs where asset_id in ('ka_vighnakara','ka_dasha_kala','ka_muhurta_seva') and retired_at is null;
select count(*) from pg_constraint where conname in ('kala_convergence_signal_id_fkey','kala_activation_signal_id_fkey','kala_obstruction_signal_id_fkey','kala_darshana_signal_id_fkey','kala_bhavishya_signal_id_fkey','bodha_contradictions_signal_a_id_fkey','bodha_contradictions_signal_b_id_fkey','bodha_signal_embeddings_signal_id_fkey');
-- G  builder privileges
select has_table_privilege('data_plane_builder','public.asset_throughput_state_audit','INSERT'), has_table_privilege('data_plane_builder','public.phala_anchors','SELECT'), has_table_privilege('data_plane_builder','public.bg_combustion_orbs','SELECT'), has_column_privilege('data_plane_builder','public.asset_registry','selftest_detail','UPDATE'), has_table_privilege('data_plane_builder','public.phala_rectification','SELECT'), has_table_privilege('data_plane_builder','public.mimamsa_predictions','SELECT');
-- H  ka_kshetra history, ledger, instance
select count(*), min(r.created_at)::date, max(r.created_at) from build_runs r join build_run_assets a on a.run_id=r.id where a.asset_id='ka_kshetra' and r.chart_id='482012f1-710e-4a25-994a-93821f5871aa';
select a.state, count(*) from build_run_assets a join build_runs r on r.id=a.run_id where a.asset_id='ka_kshetra' and r.chart_id='482012f1-710e-4a25-994a-93821f5871aa' group by 1 order by 1;
select left(r.id::text,8), r.state, r.created_at, r.ended_at, left(a.error,70) from build_runs r join build_run_assets a on a.run_id=r.id where a.asset_id='ka_kshetra' and r.chart_id='482012f1-710e-4a25-994a-93821f5871aa' order by r.created_at desc limit 1;
select count(*), max(completed_at) from build_substep_progress where asset_id='ka_kshetra' and chart_id='482012f1-710e-4a25-994a-93821f5871aa';
select pg_postmaster_start_time(), current_setting('max_connections');
select count(*) from build_runs where state in ('planned','running','paused');
```

Outputs, verbatim (block labels A-H are the `\echo` markers of the run; E and F carry the section 1.6 and P0c.1 facts):
```
-- A. identity and clock
now|current_user
2026-10-01 16:27:49.82387+00|suvarna_reader
(1 row)
-- B. chart_divisionals catalog and reader count
relname|own|relrowsecurity|relforcerowsecurity|policies|rsa
chart_divisionals|data_plane_l1_owner|t|f|0|t
(1 row)
reader_count
0
(1 row)
b_select|b_insert
t|t
(1 row)
-- C. ga_vargas, MSR producers, services, ka_kshetra state (canonical chart)
asset_id|state|lb|rw|fr
bo_arudha|lit|2026-09-10 00:18|25|fresh
bo_laksana|lit|2026-09-08 18:22|50529|fresh
bo_nakshatra_semantic|lit|2026-09-11 12:09|45|fresh
bo_special_lagna|lit|2026-09-11 12:09|20|fresh
bo_sudarshana|lit|2026-09-10 00:18|45|fresh
bo_vargottama_dhana|lit|2026-09-11 12:09|14|fresh
ga_vargas|lit|2026-09-07 11:03|24400|fresh
ka_dasha_kala|lit|2026-09-10 19:26|0|unknown
ka_kshetra|error|2026-09-11 03:31|1183134|
(9 rows)
-- D. registry depends_on (ga_vargas dependents, ka_dasha_kala dependents, ka_kshetra deps)
asset_id|depends_on
bo_laksana|{bg_rules,ga_positions,ga_strength,ga_sensitive,ga_panchanga,ga_sade_sati,ga_structural,ga_nakshatra,ga_condition,ga_vargas,ga_vichara}
bo_pratijna|{bo_laksana,bo_sangati,ga_vargas}
bo_vargottama_dhana|{ga_vargas,ga_positions}
ga_condition|{ga_positions,ga_vargas,ga_dashas}
ga_sade_sati|{ga_positions,ga_strength,ga_panchanga,ga_vargas,ga_dashas,ga_structural,ga_nakshatra}
ga_strength|{ga_positions,ga_vargas}
ga_structural|{ga_dashas,ga_nakshatra,ga_panchanga,ga_positions,ga_sensitive,ga_strength,ga_vargas}
(7 rows)
asset_id|depends_on
ka_jivana_parva|{ka_kala_darshana,ka_dasha_kala,ka_sangam,ka_yojaka,ga_dashas}
ka_kshetra|{ka_dasha_kala,ka_gochara_resonance,ga_panchanga,bo_pratijna,bo_sangati,bo_upaya,bg_cohort,bg_class_lifetime_counts,ka_vedha_gochara}
ka_sangam|{ka_yojaka,ka_dasha_kala,ka_gochara,ka_muhurta_seva,bo_laksana,ga_dashas,ga_strength,ga_positions,ga_tajaka,bg_transit_rules,ka_vedha_gochara}
(3 rows)
asset_id|asset_kind|scope|depends_on
ka_kshetra|data|per_chart|{ka_dasha_kala,ka_gochara_resonance,ga_panchanga,bo_pratijna,bo_sangati,bo_upaya,bg_cohort,bg_class_lifetime_counts,ka_vedha_gochara}
ka_dasha_kala|service|per_chart|{ga_dashas}
(2 rows)
-- E. ka_dasha_kala receipt and freshness
asset_id|receipt_state|od|observed_at
ka_dasha_kala|unknown||2026-09-10 19:26:34.768958+00
(1 row)
asset_id|freshness_state|reasons|observed_at
ka_dasha_kala|unknown|["output_digest_spec_unavailable", "output_digest_unavailable"]|2026-09-10 19:26:34.768958+00
(1 row)
-- F. migrations, digest specs, foreign keys
filename|applied_at
1210_asset_registry_direct_edges.sql|2026-10-01 14:37:09.977838+00
(1 row)
active_specs_for_3_assets
0
(1 row)
msr_fk_present_of_8
8
(1 row)
-- G. builder privileges
audit_insert|phala_anchors_sel|bg_combustion_orbs_sel|selftest_detail_upd|phala_rectification_sel|mimamsa_predictions_sel
f|f|f|f|f|f
(1 row)
-- H. ka_kshetra history (canonical chart)
runs|first_run|last_run
115|2026-08-05|2026-09-11 01:48:40.529634+00
(1 row)
state|count
aborted|10
complete|11
error|86
queued|8
(4 rows)
run|state|created|ended|asset_error
6e47cae4|failed|2026-09-11 01:48:41|2026-09-11 03:50:05|worker_crash: OperationalError: the connection is lost
(1 row)
ledger_rows|newest
279|2026-09-11 03:22:12
(1 row)
postmaster_start|max_connections
2026-08-17 17:51:30|50
(1 row)
active_runs_any_chart
0
(1 row)
```

### E13. v1.2 live re-read (2026-10-01 17:40-18:04Z, `suvarna_reader`, SELECT and catalog reads only; repo reads from `origin/main` 4eb40bec1; `gh` read-only)

Supersedes E12 where the two differ (E12 stays as the 16:27Z record). Credentials were never printed. The helper scripts (read-only Python over `psql`) lived in the session scratchpad and are reproduced below, not archived. The numbers in S0b and S0L can be re-derived from the statements and scripts here.

**Blocks A-H** (script `e13.sql`, run 17:55:15Z; statements are the `select` lines visible in the output labels; `\gexec` blocks execute each asset's own `integrity_check_sql` as a read-only SELECT). Between about 17:48Z and 17:55Z the grant-plan grants appeared and the three L2 FKs disappeared (a read at about 17:47Z showed `selftest_detail`, `phala_anchors`, `bg_combustion_orbs` false; block D shows them true):
```
-- A. identity and clock
now|current_user
2026-10-01 17:55:15.478538+00|suvarna_reader
(1 row)
-- B. migrations applied since 12:00Z; latest
filename|applied_at
1210_asset_registry_direct_edges.sql|2026-10-01 14:37:09.977838+00
1214_f3_drop_kala_msr_signal_fks.sql|2026-10-01 17:16:06.208274+00
1211_asset_throughput_state_audit_builder_grants.sql|2026-10-01 17:35:43.051967+00
(3 rows)
m1212_1213_1215_1216_applied
0
(1 row)
-- C. audit grant and the first builder audit row
ins|seq
t|t
(1 row)
asset_id|old_state|new_state|db_user|triggered_by|changed_at
ka_gochara_resonance|lit|error|data_plane_builder|asset_runner|2026-10-01 17:36:56.984149+00
(1 row)
run|state|scope_target|triggered_by|created_at|started_at|ended_at
1865991c|failed|ka_gochara_resonance|l3-lane-frozen-manifest-rebuild|2026-10-01 17:36:25.934937+00|2026-10-01 17:36:55.032961+00|2026-10-01 17:36:57.078162+00
(1 row)
asset_id|state|err
ka_gochara_resonance|error|DEP-ASSERT: declared dependency(ies) not lit before run: bg_transit_rules(receipt:stale) — refused to build on incomplete/missing upstream data
(1 row)
-- D. builder grants on the tables the receipt path and the L0 writers use
t|s|i|u|d|any_col_ins|any_col_upd
asset_freshness|t|f|f|f|f|f
asset_provenance_receipts|t|t|t|f|t|t
asset_throughput|t|t|t|t|t|t
bg_transit_engine|t|t|t|t|t|t
bg_transit_moorti|t|f|f|f|f|f
bg_transit_rules|t|t|t|t|t|t
bg_vedha_malefic_scale|t|t|t|t|t|t
brahma_formula_constants|t|t|t|t|t|t
vidhi_primitives|t|t|t|t|t|t
(9 rows)
svc_health_upd|selftest_upd
t|t
(1 row)
phala_anchors_sel|mimamsa_sel|orbs_sel|rect_sel
t|t|t|f
(1 row)
-- E. chart_divisionals, specs, foreign keys
relname|own|relrowsecurity|relforcerowsecurity|policies|rsa
chart_divisionals|data_plane_l1_owner|f|f|0|f
(1 row)
reader_count
71476
(1 row)
chart_id|count
1c826d5a-41cb-4450-b4dc-59d440e5f75a|23542
482012f1-710e-4a25-994a-93821f5871aa|24392
cb73cd3d-9eba-4220-9902-0de91566e980|23542
(3 rows)
active_specs_3
0
(1 row)
conname
(0 rows)
-- F. the six non-fresh L0 assets: registry kind, throughput, freshness (all partitions), receipt
asset_id|asset_kind|has_writer|natural_key_partition|target_table|target_floor|service_health
bg_ephemeris_engine|service|f||||healthy
bg_formula_constants|data|t|constant_id|brahma_formula_constants|17|
bg_panchanga|service|f||||healthy
bg_transit_rules|data|t||bg_transit_rules|76|
bg_vedha_malefic_scale|data|t||bg_vedha_malefic_scale|5|
bg_vidhi_primitives|data|t|primitive_id|vidhi_primitives|60|
(6 rows)
asset_id|state|last_built_at|rows_written
bg_ephemeris_engine|lit|2026-08-27 06:09:30.00249+00|0
bg_formula_constants|lit|2026-09-07 20:28:41.051122+00|10
bg_panchanga|lit|2026-08-27 12:07:18.473855+00|0
bg_transit_rules|lit|2026-09-04 20:07:52.531797+00|104
bg_vedha_malefic_scale|lit|2026-09-04 01:19:09.057713+00|5
bg_vidhi_primitives|lit|2026-09-04 20:07:56.018983+00|0
(6 rows)
asset_id|partition_key|freshness_state|reasons|observed_at
bg_ephemeris_engine|__whole_asset__|stale|["output_digest_spec_unavailable", "registry_changed"]|2026-09-23 21:07:36.166003+00
bg_formula_constants|constant_id|fresh|[]|2026-09-07 20:28:41.051122+00
bg_formula_constants|__whole_asset__|stale|["registry_changed"]|2026-08-26 04:08:54.542971+00
bg_panchanga|__whole_asset__|unknown|["output_digest_spec_unavailable"]|2026-08-27 12:07:18.473855+00
bg_transit_rules|__whole_asset__|stale|["registry_changed"]|2026-09-23 21:17:23.869511+00
bg_vedha_malefic_scale|__whole_asset__|stale|["registry_changed"]|2026-09-23 21:17:23.507304+00
bg_vidhi_primitives|primitive_id|stale|["registry_changed"]|2026-09-06 19:52:18.782971+00
(7 rows)
asset_id|partition_key|receipt_version|receipt_state|code|out|spec|observed_at|build_id
bg_ephemeris_engine|__whole_asset__|nirmana-provenance-receipt-v2|unknown|fa59f213376c|e5b75504595b||2026-08-27 06:09:30.00249+00|cd79def6-c40d-42c5-9414-7d40895bac5c
bg_formula_constants|constant_id|nirmana-provenance-receipt-v2|proven|54c8bbee62cb|2c6ebbe3e7a4|126465c083e5|2026-09-07 20:28:41.051122+00|10182981-c4c0-4a07-91a0-45cb520bf578
bg_formula_constants|__whole_asset__|nirmana-provenance-receipt-v1|proven|6441652129a1|16ac38966ff8||2026-08-25 14:57:06.992267+00|7db8aca3-1d63-4184-8131-553b1bbcf200
bg_panchanga|__whole_asset__|nirmana-provenance-receipt-v2|unknown|fa59f213376c|cabe9f5ff28c||2026-08-27 12:07:18.473855+00|759b43c7-b2d6-40a9-b9ef-8d1987ac898d
bg_transit_rules|__whole_asset__|nirmana-provenance-receipt-v2|proven|9812db139d56|1983611685a8|b704673aa584|2026-09-04 20:07:52.531797+00|440c1ae6-c1bb-4c25-ab74-3af414139850
bg_vedha_malefic_scale|__whole_asset__|nirmana-provenance-receipt-v2|proven|9170aa9ea036|e76e087dbaf7|16a4946da003|2026-09-03 14:29:18.472927+00|fed384b4-ec89-40de-86bd-2ce2e41f34ae
bg_vidhi_primitives|primitive_id|nirmana-provenance-receipt-v2|proven|93469b4c6394|93bc7a13c3cc|179ab2c22fad|2026-09-04 20:07:56.018983+00|440c1ae6-c1bb-4c25-ab74-3af414139850
(7 rows)
asset_id|spec
bg_formula_constants|126465c083e5
bg_transit_rules|b704673aa584
bg_vedha_malefic_scale|16a4946da003
bg_vidhi_primitives|179ab2c22fad
(4 rows)
-- G. integrity SQL of the four L0 data assets (executed read-only via gexec)
?column?
t
(1 row)
?column?
t
(1 row)
?column?
t
(1 row)
?column?
t
(1 row)
-- H. throughput state histogram (no row holds service_ok)
state|count
dormant|3
error|29
incomplete|1
lit|162
stale|73
(5 rows)
```
Block D was re-read at 17:55:36Z for the full phala/mimamsa matrix and the grant-plan extras: `phala_anchors|t|t|f|t`, `phala_mitigation|t|t|f|t`, `phala_muhurta|t|t|f|t`, `phala_pramana|t|t|f|t`, `phala_sankrama|t|t|f|t`, `phala_sodhana|t|t|f|t`, `phala_phaladesa|t|t|t|t`, `phala_suddha_sodhana|t|t|t|t`, `mimamsa_predictions|t|t|f|t`, `mimamsa_manifestation_sets|t|t|f|t` (columns S, I, U, D), `life_events` any-column SELECT true (table-level false), `brahma_activity_ontology` S true, `bg_combustion_orbs` S true, `phala_rectification` all false; `EXECUTE` true on `phala_anchor_identity_namespace()` and `phala_anchor_identity(uuid,text,text,text,text,text,date,date,date,text)`; trigger `mimamsa_predictions_builder_guard` enabled on `mimamsa_predictions`; `_migrations_applied` latest = 1211 (17:35:43Z), 1214 (17:16:06Z); `pg_constraint` shows none of the three L2 FK names.

**Block I: direct bg_ dependencies of the 27-asset launch set, and the transitive closure restricted to the six L0 assets** (script `q1.sql`, 18:04Z):
```
-- direct bg_ deps of the 27
dep|consumers|count
bg_dignity_reference|ka_vighnakara|1
bg_ephemeris|ka_gochara|1
bg_ghatana|ka_avadhi,ka_yojaka|2
bg_transit_rules|ka_gochara,ka_sangam,ka_yojaka|3
(4 rows)
-- transitive closure of 27 restricted to the 6 L0
dep|n_roots|roots
bg_panchanga|24|bo_anveshana,bo_cgm_motifs,bo_cgm_paths,bo_drishti,bo_karanajala,bo_pratijna,bo_upaya,ka_avadhi,ka_bhavishya_lekha,ka_gochara,ka_kala_darshana,ka_kalasutra,ka_sangam,ka_vighnakara,ka_yojaka,mi_bhavisya,ph_muhurta,ph_nimitta,ph_phaladesa,ph_pramana,ph_pratikara,ph_sankrama,ph_sodhana,ph_suddha_sodhana
bg_transit_rules|17|bg_transit_rules,ka_bhavishya_lekha,ka_gochara,ka_kala_darshana,ka_kalasutra,ka_sangam,ka_vighnakara,ka_yojaka,mi_bhavisya,ph_muhurta,ph_nimitta,ph_phaladesa,ph_pramana,ph_pratikara,ph_sankrama,ph_sodhana,ph_suddha_sodhana
bg_vedha_malefic_scale|15|ka_bhavishya_lekha,ka_gochara,ka_kala_darshana,ka_kalasutra,ka_sangam,ka_vighnakara,mi_bhavisya,ph_muhurta,ph_nimitta,ph_phaladesa,ph_pramana,ph_pratikara,ph_sankrama,ph_sodhana,ph_suddha_sodhana
(3 rows)
```
**Block J: replica of `output_digest.compute_output_digest` (read-only) and the source-versus-live comparisons.** The replica reproduces the stored receipt digest of `bg_formula_constants` (`constant_id` partition) exactly (`2c6ebbe3e7a4904c...`), which validates it; it then gives, for the other three assets, digests that differ from their stored receipts (bg_transit_rules stored `1983611685a84b76eabe90baf20746bbefd4f4914afdd7f2e7d73fbf454dcc33`; bg_vedha_malefic_scale stored `e76e087dbaf7da4600a9879851060fc8157ee746cf353018959b3263fd4266c3`; bg_vidhi_primitives stored `93bc7a13c3ccccd67c5ad355529e939572f983bc72e36ec2660e289c153c4628`). Output (18:04Z):
```
bg_transit_rules live_output_digest= ca19407a3e374505d4342b208c383250ef2c6517cbc7c9aa62c1ce1160737a26 spec= b704673aa584 {'bg_transit_rules': 76, 'bg_transit_engine': 9, 'bg_transit_moorti': 27}
bg_vedha_malefic_scale live_output_digest= b1d78defec700f0614b223fb56cd6144bc260aad33874162577b6c1a4254ae2e spec= 16a4946da003 {'bg_vedha_malefic_scale': 5}
bg_vidhi_primitives live_output_digest= 28eeb20c6abb95dc7699023e727a9fe13811e264b9518b16bc828bda318572c5 spec= 179ab2c22fad {'vidhi_primitives': 60}
bg_formula_constants live_output_digest= 2c6ebbe3e7a4904ca65ba3e46a60ae83cb47b92655d78d4b7d40c2a8c394e3fe spec= 126465c083e5 {'brahma_formula_constants': 17}
```
```python
#!/usr/bin/env python3
"""Read-only replica of pipeline/orchestrator/output_digest.compute_output_digest.
Runs SELECTs through psql as the already-sourced suvarna_reader; never prints credentials."""
import hashlib, json, subprocess, sys

def psql(sql):
    out = subprocess.run(["/opt/homebrew/bin/psql", "-X", "-A", "-t", "-c", sql],
                         capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise SystemExit("psql error: " + out.stderr[:300])
    return out.stdout

def digest_for(asset_id):
    row = psql(f"select spec_sha256 || '|' || spec::text from asset_output_digest_specs where asset_id='{asset_id}' and retired_at is null").strip()
    sha, spec_text = row.split("|", 1)
    spec = json.loads(spec_text)
    d = hashlib.sha256()
    d.update(b"nirmana-output-content-v1\\0")
    d.update(sha.encode("ascii"))
    counts = {}
    for comp in spec["components"]:
        d.update(comp["name"].encode("ascii"))
        d.update(b"\\0")
        pairs = []
        for c in comp["value_columns"]:
            pairs += [f"'{c}'", f'source."{c}"']
        order = ", ".join(f'source."{c}"' for c in comp["key_columns"])
        sql = f'SELECT jsonb_build_object({", ".join(pairs)})::text AS row_json FROM public."{comp["relation"]}" AS source ORDER BY {order}'
        # psql -A -t prints one row per line; row_json text has no raw newlines (jsonb escapes them)
        lines = [l for l in psql(sql).split("\n") if l != ""]
        n = 0
        for l in lines:
            e = l.encode("utf-8")
            d.update(len(e).to_bytes(8, "big"))
            d.update(e)
            n += 1
        d.update(n.to_bytes(8, "big"))
        counts[comp["relation"]] = n
    return d.hexdigest(), sha, counts

if __name__ == "__main__":
    for a in sys.argv[1:]:
        h, sha, counts = digest_for(a)
        print(a, "live_output_digest=", h, "spec=", sha[:12], counts)
```
Source-versus-live comparisons (import the seed lists from `origin/main` modules, compare to the live rows, SELECT only):
```
source counts: engine 9 rules 69 moorti 27
engine rows that would change: 0 | db-only keys: []
rules: source 69 db 76 | rows the upsert would change: 0 | rows it would INSERT: 0 | owned rows it would RETIRE (DELETE): 0
changed sample: [] missing sample: [] stale sample: []
db rows outside src (not owned, kept): 7
moorti: source 27 db 27 rows that would change: 0
vedha: source rows 5 db rows 5 rows the upsert would change: 0
vidhi: source 60 db 60 would change: 0 [] would delete: []
```
Code digests: local `get_writer_source_hash('bg_transit_rules')` = `824c6d7d7237ae812cff52b98473228e0c8fc6233d23f976351420a2b63470e1` = the `origin/main` inventory entry (`platform/src/generated/nirmana-writer-digests.json`, `probe_digest` `997985c1d56a3027...`); stored receipt `code_digest` `9812db139d568ba645c67c3c920d22bb6fac6c08a6222731a59b07bc2593f1aa`. Inventory entries versus stored: `bg_vedha_malefic_scale` `2e3a372e2df64199...` vs `9170aa9ea0368e6f...`; `bg_vidhi_primitives` `63f0a35a4be711d2...` vs `93469b4c639431b9...`; `bg_formula_constants` `54c8bbee62cbe3ff...` = stored (`constant_id` partition). Upstream, config and partition digests of all four recompute (via `provenance.canonical_digest` / `build_receipt` with `config={'chart_id': None, 'birth_params': {}}`) to the stored values: upstream `dbdd6eea68` / `ee8e86b0b2` / `353a683acb` / `29ed81d5ac`, config `c15fddb4f9` (all), partition `595f36c1f2` / `595f36c1f2` / `419b80f86e` / `04ede568fa` for transit, vedha, vidhi, formula.

**Block K: planner fixpoint against the live registry** (script below; readiness = throughput in `lit`/`service_ok` AND latest-observed freshness `fresh`, with the planner's service exception; "after S0b" is a modelled scenario: `bg_transit_rules` fresh, `ka_gochara`/`ka_moorti_nirnaya`/`ka_vedha_gochara` stale; 18:04Z):
```
## NOW (live), start=BASE27: plan size 28; added beyond start: 1
   + ka_gochara_resonance (required by ka_gochara; throughput=error, freshness=fresh)
## AFTER S0b (bg_transit_rules fresh; ka_gochara/ka_moorti_nirnaya/ka_vedha_gochara stale), start=BASE27 minus bg_transit_rules: plan size 30; added beyond start: 4
   + ka_gochara_resonance (required by ka_gochara; throughput=error, freshness=fresh)
   + ka_vedha_gochara (required by ka_gochara; throughput=stale, freshness=fresh)
   + ka_moorti_nirnaya (required by ka_gochara; throughput=stale, freshness=fresh)
   + bg_vedha_malefic_scale (required by ka_vedha_gochara; throughput=lit, freshness=stale)
## AFTER S0b + bg_vedha_malefic_scale fresh: plan size 29; added beyond start: 3
   + ka_gochara_resonance (required by ka_gochara; throughput=error, freshness=fresh)
   + ka_vedha_gochara (required by ka_gochara; throughput=stale, freshness=fresh)
   + ka_moorti_nirnaya (required by ka_gochara; throughput=stale, freshness=fresh)
direct deps of the gochara-family assets:
   ka_gochara [('bg_ephemeris', 'lit', 'fresh'), ('bg_transit_rules', 'lit', 'stale'), ('ka_gochara_resonance', 'error', 'fresh'), ('ka_vedha_gochara', 'lit', 'fresh'), ('ka_moorti_nirnaya', 'lit', 'fresh')]
   ka_gochara_resonance [('bg_transit_rules', 'lit', 'stale')]
   ka_moorti_nirnaya [('bg_ephemeris', 'lit', 'fresh'), ('bg_transit_rules', 'lit', 'stale')]
   ka_vedha_gochara [('bg_ephemeris', 'lit', 'fresh'), ('bg_transit_rules', 'lit', 'stale'), ('bg_sarvatobhadra_grid', 'lit', 'fresh'), ('bg_vedha_malefic_scale', 'lit', 'stale'), ('bg_phaladeepika_latta', 'lit', 'fresh')]
   ka_sangam [('ka_gochara', 'lit', 'stale'), ('bg_transit_rules', 'lit', 'stale'), ('ka_vedha_gochara', 'lit', 'fresh')]
   ka_yojaka [('bg_transit_rules', 'lit', 'stale'), ('bg_ghatana', 'lit', 'fresh')]
```
```python
#!/usr/bin/env python3
"""Read-only minimal-plan fixpoint (planner preflight rule) against LIVE registry/throughput/freshness.
ready(dep) = throughput in (lit, service_ok) AND latest freshness == fresh (planner: latest-observed row,
chart-scoped preferred, else global), with the planner's service exception. Optionally apply scenario overrides."""
import json, subprocess, sys
CH = "482012f1-710e-4a25-994a-93821f5871aa"

def q(sql):
    o = subprocess.run(["/opt/homebrew/bin/psql", "-X", "-A", "-t", "-c", sql], capture_output=True, text=True, timeout=60)
    if o.returncode: raise SystemExit(o.stderr[:300])
    return [json.loads(l) for l in o.stdout.split("\n") if l.strip()]

reg = {r["asset_id"]: r for r in q("select row_to_json(t)::text from (select asset_id, layer, scope, asset_kind, has_writer, service_health, coalesce(depends_on,'{}') depends_on from asset_registry where is_active) t")}
thr = {}
for r in q(f"select row_to_json(t)::text from (select distinct on (asset_id) asset_id, state from asset_throughput where chart_id='{CH}' or chart_id is null order by asset_id, (chart_id='{CH}') desc nulls last) t"):
    thr[r["asset_id"]] = r["state"]
fr = {}
for r in q(f"select row_to_json(t)::text from (select distinct on (asset_id) asset_id, freshness_state fs, reasons from asset_freshness where chart_id='{CH}' or chart_id is null order by asset_id, (chart_id='{CH}') desc nulls last, observed_at desc) t"):
    fr[r["asset_id"]] = (r["fs"], r["reasons"])

BASE27 = "bg_transit_rules,ka_muhurta_seva,ka_dasha_kala,bo_karanajala,bo_pratijna,bo_drishti,bo_cgm_motifs,bo_cgm_paths,bo_anveshana,bo_upaya,ka_avadhi,ka_gochara,ka_yojaka,ka_sangam,ka_kalasutra,ka_vighnakara,ka_kala_darshana,ka_bhavishya_lekha,ph_nimitta,ph_muhurta,ph_pratikara,ph_sankrama,ph_sodhana,ph_suddha_sodhana,ph_pramana,ph_phaladesa,mi_bhavisya".split(",")

def ready(a, thr, fr):
    t = thr.get(a); f = fr.get(a)
    if t not in ("lit", "service_ok"): return False
    if f and f[0] == "fresh": return True
    e = reg[a]
    reasons = set(f[1]) if f else set()
    if e["asset_kind"] == "service" and e["service_health"] == "healthy" and f and f[0] == "unknown":
        if not e["has_writer"] and t == "service_ok" and reasons == {"output_digest_spec_unavailable"}: return True
        if e["has_writer"] and t == "lit" and reasons == {"output_digest_unavailable", "output_digest_spec_unavailable"}: return True
    if e["asset_kind"] == "service" and f is None: return False
    return False

def fixpoint(start, thr, fr):
    P = list(start); added = []
    changed = True
    while changed:
        changed = False
        for a in list(P):
            for d in reg[a]["depends_on"]:
                if d in P: continue
                if not ready(d, thr, fr):
                    P.append(d); added.append((d, a, thr.get(d), fr.get(d, (None,))[0])); changed = True
    return P, added

def show(title, start, thr_, fr_):
    P, added = fixpoint(start, thr_, fr_)
    print(f"## {title}: plan size {len(P)}; added beyond start: {len(added)}")
    for d, a, t, f in added:
        print(f"   + {d} (required by {a}; throughput={t}, freshness={f})")

show("NOW (live), start=BASE27", BASE27, thr, fr)

# scenario: after S0b alone (bg_transit_rules fresh; canonical downstream lit -> stale)
thr2 = dict(thr); fr2 = dict(fr)
fr2["bg_transit_rules"] = ("fresh", [])
for a in ("ka_gochara", "ka_moorti_nirnaya", "ka_vedha_gochara"):
    thr2[a] = "stale"
show("AFTER S0b (bg_transit_rules fresh; ka_gochara/ka_moorti_nirnaya/ka_vedha_gochara stale), start=BASE27 minus bg_transit_rules",
     [a for a in BASE27 if a != "bg_transit_rules"], thr2, fr2)

# scenario: S0b + bg_vedha_malefic_scale fresh
fr3 = dict(fr2); fr3["bg_vedha_malefic_scale"] = ("fresh", [])
show("AFTER S0b + bg_vedha_malefic_scale fresh", [a for a in BASE27 if a != "bg_transit_rules"], thr2, fr3)

print("direct deps of the gochara-family assets:")
for a in ("ka_gochara", "ka_gochara_resonance", "ka_moorti_nirnaya", "ka_vedha_gochara", "ka_sangam", "ka_yojaka"):
    print("  ", a, [(d, thr.get(d), fr.get(d, (None,))[0]) for d in reg[a]["depends_on"] if d.startswith(("bg_", "ka_gochara", "ka_moorti", "ka_vedha"))])
```
**Block L: downstream closure of `bg_transit_rules` with canonical and other-chart states, and of each L0 asset with its canonical lit members** (scripts `q3.sql`, `q4.sql`; 18:04Z):
```
-- bg_transit_rules downstream closure with canonical-chart throughput state, in-plan flag, and the two other charts
a|canon|c1c82|ccb73|in_plan
ka_bhavishya_lekha|stale|stale|error|t
ka_gochara|lit|lit|-|t
ka_kala_darshana|stale|stale|stale|t
ka_kalasutra|stale|stale|stale|t
ka_sangam|stale|stale|stale|t
ka_vighnakara|stale|stale|stale|t
ka_yojaka|stale|lit|error|t
mi_bhavisya|error|stale|-|t
ph_muhurta|stale|stale|-|t
ph_nimitta|stale|stale|error|t
ph_phaladesa|stale|stale|error|t
ph_pramana|stale|stale|-|t
ph_pratikara|stale|stale|-|t
ph_sankrama|stale|stale|-|t
ph_sodhana|stale|stale|-|t
ph_suddha_sodhana|stale|stale|-|t
ka_gochara_resonance|error|lit|lit|f
ka_jivana_parva|stale|stale|stale|f
ka_kshetra|error|stale|error|f
ka_moorti_nirnaya|lit|lit|-|f
ka_taranga|stale|stale|error|f
ka_tulana|stale|stale|stale|f
ka_vedha_gochara|lit|dormant|-|f
mi_abhilekha|stale|stale|-|f
mi_adhilepa|error|stale|error|f
mi_bhara|error|error|-|f
mi_darshana|error|stale|error|f
mi_gunanaka|error|stale|-|f
mi_pariksha|error|stale|error|f
mi_pramana|error|stale|-|f
mi_sambandha|error|stale|-|f
mi_sankalpa|dormant|-|-|f
mi_seva|stale|stale|-|f
ph_rectification|stale|stale|-|f
(34 rows)
-- summary: canonical chart, outside the plan, by state
state|count|string_agg
dormant|1|mi_sankalpa
error|9|ka_gochara_resonance,ka_kshetra,mi_adhilepa,mi_bhara,mi_darshana,mi_gunanaka,mi_pariksha,mi_pramana,mi_sambandha
lit|2|ka_moorti_nirnaya,ka_vedha_gochara
stale|6|ka_jivana_parva,ka_taranga,ka_tulana,mi_abhilekha,mi_seva,ph_rectification
(4 rows)
```
```
-- per L0 asset: downstream closure, per-chart count, canonical lit/service_ok members (would flip if output_changed true or unknown), other 2 charts lit counts (NOT flipped by a canonical-chart run)
root|total|per_chart|global_|canon_lit|canon_lit_ids
bg_ephemeris_engine|4|3|1|0|
bg_formula_constants|7|7|0|0|
bg_panchanga|57|57|0|15|bo_arudha,bo_bimba,bo_grounding,bo_karanajala,bo_laksana,bo_laksana_rerank,bo_nakshatra_semantic,bo_samskara,bo_sangati,ga_panchanga,ga_sade_sati,ga_structural,ga_vichara,ga_yoga,ka_gochara
bg_transit_rules|34|34|0|3|ka_gochara,ka_moorti_nirnaya,ka_vedha_gochara
bg_vedha_malefic_scale|31|31|0|2|ka_gochara,ka_vedha_gochara
bg_vidhi_primitives|1|0|1|0|
(6 rows)
-- global downstream members
root|a|scope|asset_kind|glob_state
bg_ephemeris_engine|bg_cohort|global|data|lit
bg_vidhi_primitives|bg_vidhi_floors|global|data|lit
(2 rows)
-- bg_ephemeris_engine per-chart downstream
a|scope|canon
bg_cohort|global|
ka_kshetra|per_chart|error
mi_bhara|per_chart|error
mi_sankalpa|per_chart|dormant
(4 rows)
-- bg_formula_constants downstream
a|scope|canon
mi_adhilepa|per_chart|error
mi_darshana|per_chart|error
mi_gunanaka|per_chart|error
mi_pariksha|per_chart|error
mi_pramana|per_chart|error
mi_sambandha|per_chart|error
mi_seva|per_chart|stale
(7 rows)
-- global-row freshness of other L0 assets in thepsql:/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/8201ea38-2c77-469c-afac-0d364a9fae85/scratchpad/rb12/q4.sql:25: error: unterminated quoted string

asset_id|freshness_state|reasons
bg_class_lifetime_counts|fresh|[]
bg_cohort|fresh|[]
bg_dignity_reference|fresh|[]
bg_ephemeris|fresh|[]
bg_ghatana|fresh|[]
bg_phaladeepika_latta|fresh|[]
bg_rules|fresh|[]
bg_sarvatobhadra_grid|fresh|["empty_by_ruling:ADJUDICATION-11", "conductor_ruling:#2393"]
bg_vidhi_floors|fresh|[]
(9 rows)
```
**Block M: repo and CI facts (`gh`, read-only).** PR states: #2823 MERGED 2026-10-01T15:37:54Z (066c58587); #2828 MERGED 16:49:57Z (9f02ed504); #2834 MERGED 17:00:24Z (4eb40bec1); #2825, #2826, #2827, #2830, #2833 OPEN; #2824 (this plan) OPEN. Deploy runs with event `workflow_run`: 36898400004 (4eb40bec1, created 17:18:25Z, `completed success`; jobs: Gate and detect 17:24:34-17:25:22Z success, Inspect DB Migration State 17:25:27-17:29:01Z success, **Apply Routine DB Migrations 17:29:03-17:35:54Z success**, Build and Deploy Web 17:35:59-17:43:34Z success, **Build and Deploy Pipeline Job Image skipped (17:35:55Z)**, Build and Deploy Sidecar skipped, Build and Deploy MCP skipped, Require earned deployment outcome success 17:43:59Z); 36896658202 (4eb40bec1, 17:04:16Z, success); 36893699387 (ce52cd5c3, 16:40:01Z, success). `deploy.yml:95`: `DEPLOY_SHA: ${{ github.event.workflow_run.head_sha || github.sha }}`; checkout steps compare `ACTUAL_SHA` to `DEPLOY_SHA`.

**Block N: attribution of the `registry_changed` flags** (`_migrations_applied.applied_at` against `asset_freshness.observed_at`; the trigger writes `now()` of the migration transaction, slightly earlier than the row insert): 1075 (21:07:36.370Z) <-> `bg_ephemeris_engine` (21:07:36.166Z, health probe re-anchored); 1077 (21:17:23.507Z) <-> `bg_vedha_malefic_scale` (21:17:23.507Z); 1078 (21:17:23.869Z) <-> `bg_transit_rules` (21:17:23.869Z); 1079 (22:03:22.783Z, `english_description` only) fired nothing; 706 (2026-09-06 19:52:18.783Z) <-> `bg_vidhi_primitives` (19:52:18.783Z); 615 (2026-08-26 04:08:54.543Z) <-> `bg_formula_constants` legacy `__whole_asset__` row (04:08:54.543Z). Run history of the six L0 assets: `build_run_assets` completed rows, 2026-07-04 to 2026-09-07; `bg_transit_rules` 2 (build, build; 0.04/0.04 s), `bg_vedha_malefic_scale` 4 (two `skip_no_delta`), `bg_vidhi_primitives` 7, `bg_formula_constants` 6 (two `skip_no_delta`, writer 0.03-0.06 s), `bg_ephemeris_engine` 1 and `bg_panchanga` 1 (2026-08-27, 0.03-0.04 s). The two 2026-09-04 `bg_transit_rules` runs were `asset_set` runs on the canonical chart with `triggered_by nirmana-elevation:t0-2026-09-01-0e5b06fb:L0:wave-0:...` naming 16-17 L0 assets.

**What v1.2 could not verify (consolidated).** (1) Whether the pipeline job writes receipts and freshness through a role or path other than `data_plane_builder`; the runner's handling of the permission-denied exceptions; (2) the content of the current pipeline-job image and which deploy built it (the 1211-carrying run skipped that job); (3) who applied the grant-plan grants, the L2 FK drop and the `chart_divisionals` access fix at about 17:48-17:55Z and earlier, and that none of it was a migration; (4) P0b.3 checks 1, 3 (owner side), 4-7 (owner-path count, builder probe, `chart_snapshot` canary, ownership gate); (5) whether the `ph_*`/`mi_bhavisya` writers need UPDATE on tables where UPDATE is false, the N-46 guard's specification, and the five-column `life_events` grant; (6) target-table grants for `ka_moorti_nirnaya` and `ka_vedha_gochara` (only `gochara_resonance_map` was re-checked); (7) whether the job container can run the ephemeris probe (pinned Swiss Ephemeris files); (8) the run durations of the Gochara trio; (9) `ref_transit_rules_get` and any MCP/app reader (no production MCP call was made); (10) every code-derived outcome above (S0b.4, P0.6 item 1, S0L `bg_panchanga` flips, the probe-path spec gap) was derived from code and catalog state, none exercised; (11) which commit the held 1216 branch sits on (not on origin); (12) E1-E12 figures not named in the v1.2 box remain as of their original read times.

*End of document.*
