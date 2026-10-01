---
asset_id: ka_sangam
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
decisions_applied: "none; this brief states facts and cites decisions, it makes none"
track_i_items: []
ledger_gap_ids: ["ka_sangam-Build.completion", "ka_sangam-Earn.build_record", "ka_sangam-Cost.baseline", "ka_sangam-Count.floor", "ka_sangam-Dens.served", "ka_sangam-Build.history", "ka_sangam-Build.dep_liveness", "ka_sangam-Carr.detector"]
---

# ka_sangam — Convergence windows: dasha × transit × strength convergence per signal (Saṅgam) (evaluation only)

> **PROVISIONAL — until J1; may register gaps, may not certify.** **EVALUATION ONLY — family asset.** Track F (Saṅgam family): design is Suvarṇa's Track F lane (F1.S, F-2, F-6); implementation owner decided by SS at J1.FO. A.L3f evaluates; this lane writes no disposition and no fix design. This brief proposes no disposition and no fix design: Track A section 6 says Track A writes no Saṅgam/Kṣetra brief itself, and the design of both is Track F's. It exists so the measured state and the facts found while reading the non-family writers are in one place for A.L3f and for the J1.FO decision. Facts come from the repository and the saved evidence (B.10).

## 0 · Identity — what the asset is

`ka_sangam.py` (1,166 lines, heavy writer with substeps, `has_substeps` true) writes `kala_convergence` (21 columns, one row per convergence window: `mode` A/B/C/D, `peak_date`, `window_start/end`, `convergence_score`, `confidence_label`, `orb_strength`, `rarity_years`, `domain`, `horizon_tier`, `signal_id`, `source_citation`, `tier_basis`, …) from the predicate set (`ka_yojaka`), the dasha service (`KaDashaKalaService`, imported at `ka_sangam.py:35`), the Gochara family, `ka_muhurta_seva` and L1/L0 inputs; the engine is `services/ka_sangam/engine.py`. It declares 11 upstream assets. Served by `query_convergence_windows.ts:126` and `query_temporal_activation.ts`; read in code by six L3 writers (`ka_bhavishya_lekha`, `ka_jivana_parva`, `ka_kala_darshana`, `ka_kalasutra`, `ka_taranga`, `ka_vighnakara`; `ka_tulana` declares the edge but does not read the table, CF-23), three L4 (`ph_muhurta`, `ph_nimitta`, `ph_pratikara`) and one L5 (`mi_adhilepa`): declared radius direct 11 / transitive 25 (census), the largest in L3.

**Canonical chart: `stale`, 0 rows (cascade-shaped).** `kala_convergence` holds 0 canonical rows while `asset_throughput` reads `stale`, `rows_written` 14,868 (08-13 01:07); Abhinandan holds 17,957, the third chart 2,540 (I-6; 17,957 + 2,540 = 20,497 is the saved census's table-wide denominator for Ldgr/Complete.depth). 10 of 11 declared dependencies lit (`ka_yojaka` stale). Wave 3 of the rebuild plan (v1.0 numbering, v1.1.1 keeps the order) (after `ka_gochara` and `ka_yojaka`; median 8.0 and maximum 73.2 minutes, the longest Kāla writer; one 75-minute reserve slot for a retry). **Blocked by B-2 (rebuild plan):** its two declared services have receipts with no `output_digest`, so its upstream digest is NULL and its receipt 'unknown' (I-5 / migration 1213, PR #2826, NOT merged at base, closes it once both services have rebuilt). Its own rebuild also needs F-3 (CF-24) before any MSR wave. Not Nirmāṇa-frozen.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2325` | seed (live may differ by migration; see CF-03) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py:224`; registry `has_writer` = True | writers dir / census `Build.registered` |
| target table(s) | `kala_convergence`; count_sql tables: kala_convergence | census |
| live rows / floor | 0 / 14,868 | census `live_rows` (chart-scoped count_sql); floor from layer instance 1.1 (REG 2026-09-30) |
| catalog_status | CURRENT | census |
| registry state read for the rebuild plan (2026-10-01 14:5x) | throughput `stale`; freshness no freshness row; output-digest spec present; service_health n/a (not a service) | `/Users/Dev/suvarna-evidence/Rebuild/reg_state.json` (outside the repo) |
| depends_on (live, + migration 1210) | `ka_yojaka`, `ka_dasha_kala`, `ka_gochara`, `ka_muhurta_seva`, `ka_vedha_gochara`, `bo_laksana`, `ga_dashas`, `ga_strength`, `ga_positions`, `ga_tajaka`, `bg_transit_rules` | layer instance 3.4 (REG 2026-09-30); migration 1210 |
| blast radius | direct 11 / transitive 25 (census blocking_radius, every layer); named (REG 2026-09-30): L3 `ka_bhavishya_lekha`, `ka_jivana_parva`, `ka_kala_darshana`, `ka_kalasutra`, `ka_taranga`, `ka_tulana`, `ka_vighnakara`; L4 `ph_muhurta`, `ph_nimitta`, `ph_pratikara`; L5 `mi_adhilepa` | census `blocking_radius`; names from REG |
| code readers (declared-vs-actual) | serving / TS modules that name the table: `platform-mcp/src/tools/retrieval/kala_temporal.ts`, `src/lib/retrieval/registry/knowledge/source_query_availability.ts`, `registry/layers/L3_kala/index.ts`, `registry/layers/L3_kala/query_convergence_windows.ts`; python modules that name it other than the asset's own writer (a name hit, not always a read: for example `bodha_writers/_idempotency.py:102` is a comment): `bodha_writers/_idempotency.py`, `brahmagyan/kala/convergence.py`, `pipeline/orchestrator/asset_runner.py`, `pipeline/orchestrator/dag_edge_guard.py`, `pipeline/orchestrator/kala_derivation_completeness_guard.py`, `pipeline/orchestrator/writers/ka_bhavishya_lekha.py`, `pipeline/orchestrator/writers/ka_jivana_parva.py`, `pipeline/orchestrator/writers/ka_kala_darshana.py`, `pipeline/orchestrator/writers/ka_kalasutra.py`, `pipeline/orchestrator/writers/ka_taranga.py`, `pipeline/orchestrator/writers/ka_vighnakara.py`, `pipeline/orchestrator/writers/mi_adhilepa.py`, `pipeline/orchestrator/writers/mi_kula.py`, `pipeline/orchestrator/writers/ph_muhurta.py`, `pipeline/orchestrator/writers/ph_nimitta.py`, `pipeline/orchestrator/writers/ph_pratikara.py`, `services/ka_temporal/date_resolver.py`, `services/ka_tulana/__init__.py`, `services/ka_tulana/ranker.py`, `services/ph_nimitta/dasha_consensus.py`, `services/ph_nimitta/engine.py`, `services/ph_sodhana/engine.py`, `services/taranga_kernel/kernel.py`, `scripts/governance/v13_production_gate.py` | `grep -rlw <table>` over `platform/python-sidecar`, `platform/src`, `platform-mcp/src` (runtime code; census/preflight/seed scaffolding excluded; run 2026-10-01) |
| served surface | `platform/src/lib/retrieval/registry/layers/L3_kala/query_convergence_windows.ts:126` reads `kala_convergence`; `density_contract` declared on 0 of the L3 capability modules (offline rev-7 scan, `INDEX.md` section 9.1) | declarations 1.6.0; offline Dens scan |
| Nirmāṇa freeze | not frozen (not in the L3 list of NIRMANA_SUPERSESSION_RECORD §2.3) | `NIRMANA_SUPERSESSION_RECORD_v1_0.md` §2.3 |
| role / scoring mode | contribution (CEN `L3.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L3.json` (generated 2026-09-30T20:25:37+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 7 and this lane used no database read.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.completion | FAIL | empty: live=0 (count_sql over the target table; chart 482012f1) and the registry does not declare zero rows complete (target_floor=14868); build record rows_written=14868 |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | FAIL | live=0, floor=14868, delta=-14868 |
| Dens | Dens.served † | FAIL | 2 module(s): query_convergence_windows.ts, query_temporal_activation.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 32 error(s) and 8 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) ka_gochara did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 10/11 declared dependencies lit at chart 482012f1 (or global); stale: ['ka_yojaka (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | declarations file 1.6.0: `prose_fields` = null (undeclared: Null/Narr read NO_DETECTOR) |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Complete.depth; Vocab.identity; Build.exercised; Ldgr.source_presence.

**Reported, not graded (NOT_GENERIC):** Complete.width, Reach.fields.

**Offline rollup** (main's `rollup_asset` rules, registry rev 7, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L3/rollup_saved_L3.json`): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

**Offline Dens re-measure** (main's `capability_scan` + `_grade_dens`, rev 7; `_evidence/dens_remeasure_L3.py`; saved populated-column lists stand in for the database column catalog): **FAIL** — STRUCTURAL: 3 module(s) reach it by code: L3_kala/query_convergence_windows.ts, L3_kala/query_temporal_activation.ts, platform-mcp/src/tools/retrieval/kala_temporal.ts; 2 served select(s) of its table; no referencing capability that serves it declares density_contract; a tier column is selected without a contract in: L3_kala/query_convergence_windows.ts

**Build.dag re-read offline at rev 2** (E6 recompute over the pre-1210 registry, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`): **PASS** — 11 declared edge(s); exists: all 11 are active registry assets (every layer); cycle: ka_sangam is on no dependency cycle (registry-wide graph); reads-match: 6 read(s) of other assets' tables, every one covered by a declared edge; static scan of 69 code unit(s), 18 SQL string(s), hops<=3, every relation named; reads through views and DB functions are not followed

## 2 · Facts relevant to the evaluation (not gaps of this lane, not dispositions)

- Measured (saved census): Build.completion FAIL (empty: live 0, floor 14,868, `rows_written` 14,868), Count.floor FAIL, Dens.served FAIL (2 modules, no contract), Build.history PARTIAL (32 errors, 8 aborts; latest error 2026-08-12 cascade `BLOCKED` on `ka_gochara`), Build.dep_liveness PARTIAL (10/11), Carr NO_DETECTOR, Earn/Cost NO_DETECTOR, Idem PASS, Ldgr PASS on `source_citation` 20,497/20,497 (table-wide; a build tag).
- Facts read in the sibling writers that an evaluation of this asset should carry: `ka_kala_darshana` records that the top-750 intake of this table is 100% Mode C (`ka_kala_darshana.py:197`) and `ka_bhavishya_lekha` that `kala_convergence.tier_basis` is `relative_uncalibrated` on 100% of rows (`ka_bhavishya_lekha.py:545`); `kala_convergence` holds 793 rows with `convergence_score = 0` (M9 comment, `ka_kala_darshana.py:82`). The convergence score is a documented structural score with a low ceiling (the F-SANGAM-1 reference in the `ka_jivana_parva` comment); it is not a probability and the writers downstream already say so.
- Downstream coupling (declared vs real): the declared readers are real except as noted in CF-23 (the L3 readers `ka_bhavishya_lekha`, `ka_kala_darshana`, `ka_taranga`, `ka_jivana_parva`, `ka_kalasutra`, `ka_vighnakara` each read `kala_convergence`; `ka_tulana`'s edge is unread). `ka_taranga` reads `kala_convergence.domain`, `ka_bhavishya_lekha` prefers it (migration 361): those two columns are load-bearing for domain labelling.
- Open decisions on record (plan model): F-2 "Saṅgam: elevate, or retire into kala_field", F-6 "the Mode D design", F-3 (done by principle N-32: cascades handled by rebuilding in wave order; migration 1214, PR #2828), J1.FO (implementation owner). The sealed Saṅgam final brief (SEAL-S) is Track F's, not this lane's.
- Ownership of `ka_yojaka`: `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` section 2.3 item 6 states Saṅgam's rebuild needs `ka_yojaka` rebuilt first; Track A section 6 says a prerequisite a family brief claims moves from the 16 briefs to evaluation. This lane wrote a normal brief for `ka_yojaka` and flags the question (Q-L3-15).

## 3 · Shared fixes that touch this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* seed carries no `catalog_status` literal
- **CF-04** — Dens (serving density) on the L3 served modules. *This asset:* offline FAIL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* D2/D3 (Track F decides the carriage)
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors; no edit changes it. *This asset:* 32 / 8
- **CF-24** — L2 -> L3 cascade keys and rebuild order (F-3 / migration 1214): four emptied tables and the dangling predicate set. *This asset:* emptied table; wave 3; B-2
- **CF-26** — Service self-test assets: output-digest specs, source_paths and builder grants (I-4 / I-5 and the same class left open). *This asset:* B-2 is the services' missing digest specs

## 4 · Ownership and what this lane did not do

- Owner: Track F (Saṅgam family): design is Suvarṇa's Track F lane (F1.S, F-2, F-6); implementation owner decided by SS at J1.FO. A.L3f evaluates; this lane writes no disposition and no fix design.
- Not written here: disposition, fix designs, semantic-fingerprint contract, carriage choice (Track F's sealed brief and A.L3f own them).
- Not touched: no code, no registry row, no database write; no message to Pravāha or a family session (P11).
