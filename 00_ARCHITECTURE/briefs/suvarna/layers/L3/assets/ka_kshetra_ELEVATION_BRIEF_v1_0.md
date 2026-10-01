---
asset_id: ka_kshetra
layer: L3 Kāla (ka_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L3 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L3/L3_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 066c58587"
disposition: "none proposed (evaluation only; family asset: Track F / A.L3f)"
disposition_proposal_approver: "n/a (no disposition written here; Track A section 6)"
decisions_applied: "Q-L3-17 (SS 2026-10-01): this evaluation-only brief is kept as an evidence input to A.L3f; it still makes no decision of its own. ARGALA OUTCOME consequence (SS 2026-10-02): recorded below as a ruling note, TI-L3-38"
track_i_items: [TI-L3-38]
ledger_gap_ids: ["ka_kshetra-Idem.pattern", "ka_kshetra-Build.completion", "ka_kshetra-Earn.build_record", "ka_kshetra-Cost.baseline", "ka_kshetra-Count.floor", "ka_kshetra-Complete.depth", "ka_kshetra-Build.history", "ka_kshetra-Build.dep_liveness", "ka_kshetra-Carr.detector"]
---

# ka_kshetra — Kṣetra field: segmented, class-by-class temporal field over the event classes (15 tables) (evaluation only)

> **PROVISIONAL — until J1; may register gaps, may not certify.** **EVALUATION ONLY — family asset.** Track F (Kṣetra family): design is Suvarṇa's Track F lane (F1.K, F-1, F-4); implementation owner decided by SS at J1.FO. A.L3f evaluates; this lane writes no disposition and no fix design. This brief proposes no disposition and no fix design: Track A section 6 says Track A writes no Saṅgam/Kṣetra brief itself, and the design of both is Track F's. It exists so the measured state and the facts found while reading the non-family writers are in one place for A.L3f and for the J1.FO decision. Facts come from the repository and the saved evidence (B.10).

## 0 · Identity — what the asset is

`services/ka_kshetra/` (14,067 lines across 25 python files; heavy writer, `has_substeps` true, one substep per event class, per-substep commits; shim `pipeline/orchestrator/writers/ka_kshetra.py`) computes the field over 25 event classes × 343,991 segments (the registry floor 8,599,775 = 25 × 343,991, the arithmetic `volume_explanation` gives, per the I-9 diagnosis) into `kala_field` and 14 further tables (layer instance 1.1: `kala_field_null`, `…_windows`, `…_provenance`, `…_salience`, `…_kinematics`, `…_primitives`, `…_promise_nodes`, `…_promise_edges`, `…_routes`, `…_clocks`, `…_boundaries`, `…_snapshots`, `kala_insights`, `kala_timeline_spec`); the registry's structured fields name one table. Its replacement rule is deliberately closed: a rebuild of a populated chart is refused before any DELETE (`KshetraReplacementHeld`, `writer.py:186`, raised at `:545`), because the schema has no immutable candidate/publication generation until W7 (module header). No capability module serves `kala_field` by a served select (saved census: 0 modules; the offline rev-7 scan finds 8 modules that reach `kala_field` / `ka_kshetra` by code, none with a served select it can attribute); it is read by two L5 assets (`mi_bhara`, `mi_sankalpa`) and in code by `kala_ritual_resonance.ts`, `kala_views/ahead.ts` / `ritual.ts` and the `mi_bhara` services (`field.py`, `weights.py`, `db.py`); it reads `phala_rectification` itself (an upward read, Appendix A.3).

**Canonical chart: `error`, 8,570,075 rows (partial).** Throughput `error` with `last_error = worker_crash: OperationalError: the connection is lost`, `rows_written` 1,183,134 (that last attempt's own writes), `last_built_at` 2026-09-11 03:31:31. (Abhinandan's `ka_kshetra` row, a different chart, reads `stale` with `rows_written` 837,992 at 08-12 22:26: not a comparison for this chart.) The table holds 29,700 rows fewer than the floor (8,570,075 vs 8,599,775: 8,599,775 − 8,570,075 = 29,700), consistent with one unfinished final stage (I-9). Between 2026-09-10 and 09-11 there were 24 consecutive `l3-lane-kill-redispatch-ka_kshetra` runs, each `orphaned_by_crash`, ending in `6e47cae4` (01:49-03:31). I-9 diagnosis (job logs and Cloud SQL logs, read-only): the CLIENT side of the job's connections was reset (two connector sockets at 03:26:37Z, the ka_kshetra worker connection lost at 03:31:31Z), not a database restart (no admin operation that day) and not container memory pressure (no OOM signature; 4 CPU / 16 GiB, `maxRetries 0`); the traceback sits in `_run_stage5dhara_windows` (`writer.py:851`, dispatched at `:505`) → `load_legacy_crosscheck` (`stage4_field.py:1381`), a long single-connection substep. I-10 (SS ruling 2026-10-01, not started): split that stage-5 work into smaller substeps through `plan_substeps`/`run_substep` so a connection loss costs one small substep and the orchestrator's per-substep savepoint and resume handle it (writers must not manage connections). Dependencies 7 of 9 lit (`bo_pratijna`, `bo_upaya` stale). Downstream-not-in-plan `error` (a cascade victim, rebuild plan 1.4); not in the plan's 12 waves: plan v1.1.1 gives it its own stage S7, run last after the held `phala_rectification` grant gets its own review. Not Nirmāṇa-frozen. PR #2731 (`285bff17c`) changed this package after the census inspector commit.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:3087` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/services/ka_kshetra/writer.py:268`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_field`; count_sql tables: kala_field | census |
| live rows / floor | 8,570,075 / 8,599,775 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `error`; freshness no freshness row; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ka_dasha_kala`, `ka_gochara_resonance`, `ka_vedha_gochara`, `ga_panchanga`, `bo_pratijna`, `bo_sangati`, `bo_upaya`, `bg_cohort`, `bg_class_lifetime_counts` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 2 / transitive 2 (census blocking_radius, every layer); named (REG 2026-09-30): L5 `mi_bhara`, `mi_sankalpa` | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/lib/kala_ritual_resonance.ts`, `platform-mcp/src/tools/kala_views/ahead.ts`, `platform-mcp/src/tools/kala_views/ritual.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): `pipeline/orchestrator/writers/mi_bhara.py`, `services/mi_bhara/db.py`, `services/mi_bhara/field.py`, `services/mi_bhara/weights.py`, `scripts/governance/asset_census.py`, `scripts/governance/ekv_controls.py`, `scripts/repair_ka_kshetra_snapshot.py` | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | no capability module serves `kala_field` by a served select: saved census 0 modules; the offline rev-7 scan finds 8 modules that reach it by code and no served select it can attribute (NO_DETECTOR); `density_contract` not assessable (`INDEX.md` section 9.1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | not frozen (not in the L3 list of NIRMANA_SUPERSESSION_RECORD §2.3) | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | FAIL | rebuild refused when target is populated: services/ka_kshetra/writer.py:545 (raise KshetraReplacementHeld after the output-existence probe _populated_owned_table) — the delete-then-insert path runs only on an output-empty chart, so a rebuild of a populated chart does not replace (§N.3 'rebuild replaces' not met) |
| Build | Build.completion | FAIL | build record state='error' is not a completed build (rows_written=1183134, live=8570075, chart 482012f1) — see Build.history |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 6e47cae4 error/no disposition (2026-09-11) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 6e47cae4 error/no disposition (2026-09-11) |
| Count (information, D3) | Count.floor | FAIL | live=8570075, floor=8599775, delta=-29700 |
| Complete (information, D3) | Complete.depth | PARTIAL | 10982957 rows, 23 cols; fully populated 22; NEVER populated ['refinement_residual'] |
| Dens | Dens.served † | N/A | 0 module(s): none; declaring density_contract: 0 |
| Build | Build.history | FAIL | most recent run error (2026-09-11); 98 error(s), 12 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-09-11): worker_crash: OperationalError: the connection is lost |
| Build | Build.dep_liveness | PARTIAL | 7/9 declared dependencies lit at chart 482012f1 (or global); stale: ['bo_pratijna (stale, chart 482012f1)', 'bo_upaya (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Build.target †; Build.dag †; Build.count_integrity; Vocab.identity; Build.exercised.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr NO_DETECTOR · Idem FAIL · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build FAIL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **NO_DETECTOR** — NO_DETECTOR — 8 module(s) reach it by code: L4_phala/query_predictive_anchors.ts, L5_mimamsa/query_insights.ts, platform-mcp/src/tools/kala_views/priority.ts, platform-mcp/src/tools/kala_views/ritual.ts, platform-mcp/src/lib/kala_e8_register.ts, platform-mcp/src/lib/kala_envelope.ts (+2 more), but no served `SELECT ... FROM` its table was found (no served select): whether it is served cannot be told by code

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **FAIL** — 9 declared edge(s); exists: all 9 are active registry assets (every layer); cycle: ka_kshetra is on no dependency cycle (registry-wide graph); reads-match: FAIL — missing depends_on edge: ka_kshetra -> bo_karanajala (reads bodha_cgm_edges at services/ka_kshetra/stage2_promise.py:336, via services/ka_kshetra/writer.py → services/ka_kshetra/stage4_field.py:load_promise_prior → services/ka_kshetra/stage2_promise.py:promise_prior; the producer is reachable tr…

## 2 · Facts relevant to the evaluation (not gaps of this lane, not dispositions)

- Measured (saved census): Idem.pattern FAIL (rebuild refused when populated, the design above), Build.completion FAIL (error state), Count.floor FAIL (−29,700), Complete.depth PARTIAL (`refinement_residual` never populated), Reach.fields 0 of 22 columns selected by any module, Dens.served N/A (0 modules), Build.history FAIL (98 errors, 12 aborts), Build.dep_liveness PARTIAL, Carr/Earn/Cost NO_DETECTOR.
- Declared vs read (layer instance Appendix A.3, GRP at 2a78ec64d and e2352f881): 4 declared edges are never read in code (`bo_upaya`, `bo_sangati`, `ka_dasha_kala`, `ka_vedha_gochara`) and 10 owning assets are read but undeclared (`ka_gochara`, `ga_dashas`, `bo_laksana`, `bo_karanajala`, `bo_bimba`, `ph_rectification` — an upward read from L3 into L4 — `bg_ephemeris`, `bg_transit_rules`, `bg_kp_sublord_division`, `bg_ghatana`); the E6 reads-match detector reports FAIL for `bo_karanajala`, `bo_bimba`, `bo_arudha` and `ka_gochara` (the last deliberately held by migration 1084). An orchestrated build through the declared `bo_upaya` edge is the "phantom edge" exposure the focus document describes.
- Writes beyond its registry row: 15 tables written, one declared (`count_sql` over `kala_field` only, `clear_tables` empty); `kala_insights` has a second inserting writer in L5 (`services/mi_bhara/db.py:380`). The registry cockpit count (8.57M, "mostly built") and the throughput state (`error`) therefore tell different stories (I-9 evidence).
- Open decisions on record (plan model): F-1 "Kṣetra: build W7 first, or an interim clear", F-4 "stay at 6 classes", J1.FO. T2 §6.4 (layer instance 3.2): `ka_kshetra` should contribute its search/temporal-integration engineering as a mechanism-qualified candidate substrate, not become a universal authority.
- Write-scope note: `ka_kshetra` is Suvarṇa's own writer for I-10 ("a writer-code change in Suvarna's own ka_kshetra, Track I"), but its design and ownership follow J1.FO; the I-10 change is therefore recorded here and not designed.

## 3 · Shared fixes that touch this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* floor and `count_sql` scope (multi-table declaration)
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* N/A (no served module)
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* Track F decides
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 98 / 12
- **CF-23** — depends_on audit: declared edges the writer never reads, and the bhavishya back-read. *This asset:* four unread edges, ten undeclared reads (Appendix A.3)
- **CF-24** — L2 -> L3 cascade keys and rebuild order (F-3 / migration 1214): four emptied tables and the dangling predicate set. *This asset:* cascade victim; not emptied

## 4 · Ownership and what this lane did not do

- Owner: Track F (Kṣetra family): design is Suvarṇa's Track F lane (F1.K, F-1, F-4); implementation owner decided by SS at J1.FO. A.L3f evaluates; this lane writes no disposition and no fix design.
- Not written here: disposition, fix designs, semantic-fingerprint contract, carriage choice (Track F's sealed brief and A.L3f own them).
- Not touched: no code, no registry row, no database write; no message to Pravāha or a family session (P11).
- **SS ruling (2026-10-01), Q-L3-17 — accepted.** This evaluation-only brief is kept in the set as an evidence input to A.L3f; the variance (7) of `INDEX.md` section 12 is acknowledged. Nothing else changes: no disposition and no fix design are written here.

## 5 · SS ruling note: ARGALA OUTCOME consequence and the build state (SS 2026-10-02)

Recorded as ruled by SS; this brief still writes no disposition and no fix design (the design stays with Track F / J1.FO), and the L1 change, G-EPH and PR #2830 below are not in this branch and were not read here.

- **Argala edge outcome (R, provisional until J1).** L1 now emits a canonical `outcome_by_count` of `unobstructed` / `argala_prevails` / `undetermined` (there is no `obstructed`), and L2's `cancelled_flag` for argala ends. `ka_kshetra` `stage2_promise` is the one real behaviour change: `_fetch_cgm_edges` selects `... FROM bodha_cgm_edges WHERE ... AND cancelled_flag = FALSE` (`services/ka_kshetra/stage2_promise.py:336-340`) and reads no edge outcome, so if it only dropped `cancelled_flag` it would treat EVERY argala edge as active. It must read the edge's outcome: `unobstructed` and `argala_prevails` = active argala; `undetermined` = its own state that does NOT contribute as active argala until a strength basis exists. Named Track I item: **TI-L3-38** (writer code, output change; it rebuilds at stage S7 anyway).
- **Ephemeris fix.** `ka_kshetra` is exposed to the ephemeris fix (it is a decorated writer) and waits for G-EPH.
- **I-10 substep split.** PR #2830 (the I-10 split of the stage-5 work into smaller substeps, section 0) is in the merge train, last, rebased over the line-pin test.
