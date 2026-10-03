---
artifact: ASSET_ELEVATION_BRIEF_INDEX
layer: L5 Mīmāṃsā (mi_* + lel_events)
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify; no SS ruling on L5 yet"
produced_by: exec-suvarna (lane track-a-l5)
produced_on: 2026-10-03
plan_item: A.L5 (briefs, dispositions, designs)
base_commit: "main adb0db29d"
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION). Offline rollup under main REGISTRY_REVISION 16. Registry, row counts, receipts and fact queries re-read read-only 2026-10-03. NOT re-measured by the current inspector."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L5/L5_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
briefs: 15 (14 `mi_*` assets + the no-writer user-data asset `lel_events`; one `<ASSET_ID>_ELEVATION_BRIEF_v1_0.md` each in this directory)
---

# L5 Mīmāṃsā asset briefs — layer index (provisional)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Every figure is from the repository at `main adb0db29d`, the saved census, or a named read-only query (`suvarna_reader`, `default_transaction_read_only=on`; `facts.json`, `facts2.json`, `rollup_saved_L5.json` under `/Users/Dev/suvarna-evidence/A_L5/`) (B.10). No SS decision sheet exists for L5: every disposition is a proposal under Track A brief section 10, items marked (R) change outputs or verdicts, and every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa. **L5 is sealed in STRUCTURAL mode by design** (CLAUDE.md §E, seal `L5_SEAL_AND_SHIP_REPORT_v1_0.md`): empirical calibration values fill in as prediction-to-outcome data accrues. An empty or `prior_only` value is therefore not a finding in this set; a value that *claims* to be measured while nothing measured it is.

## 0 · Scope: what is in this set

- **15 full briefs:** the live registry holds 15 rows with `layer = 'mimamsa'`: 14 `mi_*` assets and `lel_events`. **CLAUDE.md §E and the lane brief say 12 `mi_*` (10 data writers + 2 service verifiers); that count is stale**: the registry has 12 `asset_kind = data` (`mi_jivanaghatana`, `mi_kula`, `mi_bhavisya`, `mi_pramana`, `mi_gunanaka`, `mi_adhilepa`, `mi_pariksha`, `mi_sambandha`, `mi_darshana`, `mi_vistara`, `mi_bhara`, `mi_sankalpa`, of which `mi_vistara` writes nothing and behaves as a verifier) and 2 `asset_kind = service` (`mi_seva`, `mi_abhilekha`), plus `lel_events` (no writer). `mi_bhara` and `mi_sankalpa` were added later and register through a constant (`@register(ASSET_ID)`), which is why an earlier skeleton counted 12 (layer instance 1.1, R43). Table `lel_events` has no writer by decision N-14.R236 and is included because the lane brief names the LEL data contract.
- **Excluded:** none of the 15. Out of scope and reported only where a brief reads it: `ph_*` (A.L4, sibling lane), `ka_*` (A.L3), `bo_*` (A.L2), `ga_*` (A.L1). Tables in the L5 namespace with no owning asset (`mimamsa_snapshot_cosign`, `mimamsa_adjudication_log`, `mimamsa_resonance_feedback`, `mimamsa_pool_contributions`; TG-L5-020) and the two `brahma_*` prediction ledgers (TG-L5-006) are named where they matter and are not given briefs.

## 1 · What this index rests on, and what is stale

- **Census used:** saved `census_L5.json` (inspector 2a78ec64d, 2026-09-30, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). Main is at **REGISTRY_REVISION 16**. The repo's own rollup code (`asset_census.py`, `rollup_census`) was run offline over the saved measurements (`offline_rollup_L5.py` -> `rollup_saved_L5.json`): mixed old measurements with new rules, labelled so everywhere. No live census re-measure was run (read-only lane; the inspector writes).
- **Criteria whose definition changed since the saved run:** Build.dag rev 1 -> 2 (reads-match, any-layer dep, cycle); Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5 (contract AND a tier column in the served select; label-vs-select repair); Null.* and Narr.* did not exist (declarations 1.12.0 give `prose_fields` for `mi_darshana` and `mi_pariksha` only: all other Null/Narr cells read NO_DETECTOR); Carr.detector was retired (E6 item i).
- **Re-read live on 2026-10-03 (read-only):** registry rows, throughput, build runs, row counts, receipts, freshness, digest specs, table profiles (columns, constraints, per-column non-null counts), and the fact queries behind every number in the briefs (`facts.py`, `facts2.py`).
- **Layer-instance figures** (EGATE blockers, T2c codes, F-01..F-12) are quoted from `L5_LAYER_INSTANCE_v1_0.md` and marked as such where used; the ones this lane re-measured (row counts, F-05, F-06, F-10, F-12) agree with it.
- **Gap ids** are ledger ids from `/Users/Dev/suvarna-census/00_ARCHITECTURE/control/asset_gaps.jsonl` @ 2a78ec64d (99 inspector-emitted L5 rows, all OPEN at 2026-09-27); that ledger is not on main. New gaps are `new:` and named `<asset>-N<k>`.
- **Not executed:** no test, writer, exporter or write-class tool (`mimamsa_outcome_record`) was run. Statements marked 'by code reading' were not exercised.

## 2 · Rollup counts

**Dispositions proposed (15 briefs):** keep (P) 2, qualify (Q) 12, retire (R) 1. (The layer instance assigns none, TG-L5-023.)

**Gap rows across the 15 briefs (221):** real 81 (of which 10 carry an SS or acharya question) · detector 45 · Dens rev-1 reading 2 · stale 28 · history 15 · information 50 · other 0. These count the 99 ledger rows (classed by criterion) plus 122 gaps found in this lane.

**Saved census cells over the 15 assets (284):** PASS 125 · NO_DETECTOR 53 · NOT_GENERIC 30 · N/A 29 · FAIL 28 · PARTIAL 19. FAIL by criterion: Build.completion 10 · Build.dep_liveness 10 · Build.history 8.

**Nine-gate cells, offline rollup of the saved measurements under main's rules (REGISTRY_REVISION 16; not a re-measure, not a certification):**

| gate | Ldgr | Idem | Earn | Null | Vocab | Carr | Narr | Dens | Build |
|---|---|---|---|---|---|---|---|---|---|
| rollup | NO_DETECTOR 14 · PASS 1 | PASS 11 · PARTIAL 3 · NO_DETECTOR 1 | NO_DETECTOR 15 | NO_DETECTOR 15 | NO_DETECTOR 15 | NO_DETECTOR 15 | NO_DETECTOR 15 | PASS 9 · NO_DETECTOR 6 | FAIL 12 · PARTIAL 2 · NO_DETECTOR 1 |

Reading notes: Ldgr reads NO_DETECTOR except `mi_sambandha` (PASS: citation presence, not correspondence); Earn/Null/Vocab/Carr/Narr read NO_DETECTOR on every asset (no census cell or no declaration); Idem PASS 11 / PARTIAL 3 / NO_DETECTOR 1; Dens: the saved rev-1 PASS cells are re-read by the rev-4/5 static scan as PARTIAL for 9 assets (no tier column in the served select) and FAIL for `mi_bhara` (see CF-L5-14); Build is FAIL for 12 assets: 8 are recorded `error` as upstream-blocked cascades from L3/L4 (`mi_bhavisya`, `mi_pramana`, `mi_gunanaka`, `mi_adhilepa`, `mi_pariksha`, `mi_sambandha`, `mi_darshana`, `mi_bhara`), `mi_sankalpa` is `dormant`, `lel_events` has no build record, and `mi_seva` / `mi_abhilekha` fail on history and dependency liveness. **None of these cells measures any of the findings below** (chronology, circularity, dangling references, stale generations): the instrument has no detector for them (T1 section 14: 'a rule with no detector is a wish').

## 3 · Assets × disposition × gaps × fix class × rebuild

Columns: **real** = shortfalls in rows/writer/registry/served surface (including stale and dangling content where a code path is the cause); **SS q** = of those, rows that change output or rest on a ruling; **Dens** = saved rev-1 FAIL/PASS cells whose meaning changed; **detector** = NO_DETECTOR or definition-open; **other** = stale + history + information + ledger rows; **rebuild** y = a fix needs a production rebuild (REVIEW for SS). Counts are computed from each brief's section 2 tables (ledger rows classed by criterion).

| asset | disposition | real | SS q | Dens | detector | other | fix class | rebuild | shared fixes |
|---|---|---|---|---|---|---|---|---|---|
| [lel_events](lel_events_ELEVATION_BRIEF_v1_0.md) | keep (P) | 5 | 1 | 0 | 4 | 3 | registry/declaration; writer code | n | CF-L5-06, CF-L5-07, CF-L5-08, CF-L5-12, CF-L5-13, CF-L5-14 |
| [mi_jivanaghatana](mi_jivanaghatana_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 5 | 1 | 0 | 3 | 5 | data (output change); writer code; migration/DDL; registry/declaration | y | CF-L5-01, CF-L5-03, CF-L5-04, CF-L5-06, CF-L5-07, CF-L5-11, CF-L5-14 |
| [mi_kula](mi_kula_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 2 | 0 | 0 | 4 | 6 | data (output change); writer code; registry/declaration; served surface (TS) | y | CF-L5-04, CF-L5-06, CF-L5-07, CF-L5-11, CF-L5-12, CF-L5-14 |
| [mi_bhavisya](mi_bhavisya_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 9 | 1 | 0 | 2 | 6 | data (output change); writer code; migration/DDL; registry/declaration | y | CF-L5-01, CF-L5-02, CF-L5-03, CF-L5-04, CF-L5-06, CF-L5-07, CF-L5-08, CF-L5-11, CF-L5-12 |
| [mi_pramana](mi_pramana_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 9 | 2 | 0 | 2 | 8 | data (output change); writer code; migration/DDL; vocabulary | y | CF-L5-01, CF-L5-02, CF-L5-03, CF-L5-04, CF-L5-05, CF-L5-06, CF-L5-07, CF-L5-10, CF-L5-11, CF-L5-12 |
| [mi_gunanaka](mi_gunanaka_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 7 | 0 | 0 | 2 | 6 | data (output change); writer code; migration/DDL; test | y | CF-L5-01, CF-L5-03, CF-L5-04, CF-L5-05, CF-L5-06, CF-L5-07, CF-L5-11, CF-L5-12 |
| [mi_adhilepa](mi_adhilepa_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 5 | 1 | 1 | 2 | 7 | writer code; data (output change); registry/declaration | y | CF-L5-01, CF-L5-02, CF-L5-03, CF-L5-04, CF-L5-07, CF-L5-10, CF-L5-11, CF-L5-12, CF-L5-13 |
| [mi_pariksha](mi_pariksha_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 5 | 0 | 0 | 2 | 9 | data (output change); writer code; registry/declaration | y | CF-L5-01, CF-L5-02, CF-L5-03, CF-L5-04, CF-L5-05, CF-L5-07, CF-L5-10, CF-L5-11, CF-L5-12 |
| [mi_sambandha](mi_sambandha_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 6 | 1 | 1 | 2 | 6 | data (output change); writer code; migration/DDL; rebuild only; registry/declaration | y | CF-L5-01, CF-L5-03, CF-L5-04, CF-L5-05, CF-L5-06, CF-L5-07, CF-L5-10, CF-L5-11, CF-L5-14 |
| [mi_darshana](mi_darshana_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 7 | 1 | 0 | 3 | 6 | served surface (TS); writer code; registry/declaration | y | CF-L5-01, CF-L5-03, CF-L5-04, CF-L5-07, CF-L5-10, CF-L5-11, CF-L5-12, CF-L5-14 |
| [mi_vistara](mi_vistara_ELEVATION_BRIEF_v1_0.md) | keep (P) | 3 | 0 | 0 | 4 | 5 | writer code; test; registry/declaration | n | CF-L5-09, CF-L5-08, CF-L5-11, CF-L5-12, CF-L5-13 |
| [mi_seva](mi_seva_ELEVATION_BRIEF_v1_0.md) | retire (R) proposed | 5 | 1 | 0 | 4 | 5 | registry/declaration | n | CF-L5-09, CF-L5-07, CF-L5-10, CF-L5-11, CF-L5-12 |
| [mi_abhilekha](mi_abhilekha_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 5 | 1 | 0 | 4 | 5 | writer code; migration/DDL; registry/declaration | n | CF-L5-07, CF-L5-08, CF-L5-09, CF-L5-11, CF-L5-12 |
| [mi_bhara](mi_bhara_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 6 | 0 | 0 | 3 | 7 | writer code; served surface (TS); migration/DDL; test; registry/declaration | y | CF-L5-04, CF-L5-07, CF-L5-08, CF-L5-10, CF-L5-11, CF-L5-12, CF-L5-13 |
| [mi_sankalpa](mi_sankalpa_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 2 | 0 | 0 | 4 | 9 | writer code; registry/declaration; test | n | CF-L5-07, CF-L5-08, CF-L5-11, CF-L5-12, CF-L5-14 |

Arithmetic check: gap rows 221 = real 81 + Dens 2 + detector 45 + other 93.

## 4 · Cross-asset fixes, ordered by value for J1 (Tracks I, B, E)

Ids are namespaced `CF-L5-nn` because the L1 and L2 sets both define CF-13..CF-20 with different meanings and L3 starts at CF-21 (see the L3 index, section 12, 'Id collision'); a layer-neutral renumbering at J1 would remove the ambiguity.

### 1. CF-L5-03 — Calibration chronology: retrodiction scored as prediction; circular bins; unresolved counted as misses; selective denominators

- **Gate:** Earn, Null; **assets:** mi_pramana, mi_jivanaghatana, mi_bhavisya, mi_gunanaka, mi_sambandha, mi_darshana, mi_pariksha, mi_abhilekha
- **Evidence:** Read-only: all 53 prediction/event pairs that still join have `event_date` and `recorded_at` before the prediction's `emitted_at` (`cal_retro`: 53/53; 50 of the 53 pairs carry the 2000-01-01 sentinel `recorded_at`, so the `event_date` half carries the conclusion); 12 of 139 prediction windows had ended and 8 straddle the emission date (`pred_window`); `mimamsa_calibration` 57 rows over 13 distinct predictions and 24 distinct events, 25 UNRESOLVED, 32 adjudicated; `CONFIRMED` is `composite_score >= 0.65` (`mi_pramana.py:241`) and the reliability bins are keyed by that same score (:523-528): the four bins entirely below 0.65 have observed rate 0 by construction, bin n = 4, 13, 12, 18, 7, 3 includes the 25 unresolved as non-hits; `pred_prob` falls back to the match score because `mimamsa_predictions` has no `posterior` / `confidence_high` column (:436); `leakage_status = clean` on 57/57 means `admissible_clean AND NOT held_out` (:422); the leakage routing in `mi_jivanaghatana` is computed in memory only and `prediction_snapshot_at` is never supplied. Downstream: `mi_gunanaka` promotes `fam_graha_natal` (n = 271 pairs from 13 predictions) and `fam_transit` (n = 14 from 2 predictions); `total_matches = 57` feeds the Paripraśna activation gate (>= 30 by code reading). By design L5 is STRUCTURAL; the defect is rows carrying `empirical` / `pass` / `clean` while 0 are prospective.
- **Design:** Q-L5-01 (chronology gate in `mi_pramana`, `recorded_at` persisted by `mi_jivanaghatana`, stable `emitted_at` from `mi_bhavisya`), reliability over adjudicated outcomes binned by the stated `confidence_band`, UNRESOLVED excluded and counted separately, independent observations in `mi_gunanaka`; retrodiction kept as its own labelled class (already how `mi_pariksha` labels it).
- **Failing-first test and mutation:** fixture with an event recorded before emission -> 0 calibration rows, 1 retrodiction row; mutation: remove the gate.
- **Blast radius:** on the canonical chart calibration 57 -> 0 rows, 6 -> 0 bins, 2 -> 0 promoted multipliers (the honest STRUCTURAL state)
- **Rebuild:** needs production rebuild (REVIEW for SS)

### 2. CF-L5-01 — Production rows predate main's honesty fixes; version labels do not move when behaviour does

- **Gate:** Earn, Narr, Null; **assets:** mi_pramana, mi_pariksha, mi_sambandha, mi_darshana, mi_gunanaka, mi_adhilepa, mi_bhavisya
- **Evidence:** Read-only: `base_rate = 0.1` on 57/57 `mimamsa_calibration` rows under `mi_pramana_v2.0` while `mi_pramana.py` writes NULL since A-F-24 (:82-110); `mimamsa_discoveries` are `mi_pariksha_v2.0` (main v2.1 / v2.2), 0/71 rows carry `n_scored_matches` or `cutoff_enforced`, 51/51 retrodiction statements read "Blind retrodiction ... with T-90d cutoff"; `mimamsa_insight_units` are `mi_darshana_v1.0` (main v1.2): 31 units graded `empirical` (20 emergent_law, 7 grammar, 4 calibrated_outlook), 0/115 carry `grade_basis`, 115/115 `leakage_status = clean`; `mimamsa_manifestation_grammar` is `mi_sambandha_v1.0` (main v1.2): 7 rows `empirical` with 0 scored and propensity 0.0, rendered "fires with 0% propensity (n=55, empirical learning)". `asset_throughput.built_against_writer_hash` is "unknown" for 10 and empty for 1 of the 12 chart-scoped assets (only `mi_jivanaghatana` has a real hash), so which code built a row cannot be proven from the registry. The serving suppression (`suppressIfNotCalibrated`, `query_insights.ts:81`) passes `empirical` rows through unsuppressed, and the stored grade is the thing that is wrong. The 11 chart-scoped assets other than `mi_jivanaghatana` last executed on or before 2026-08-13 and eight of them were recorded `error` (BLOCKED, not run) on 2026-08-21; the only L5 assets rebuilt since are `mi_jivanaghatana`, `mi_kula`, `mi_vistara` (2026-09-06).
- **Design:** No code change: the corrections are on main. (1) rebuild the chain in level order after the upstream (L3 `ka_kshetra` / `ka_sangam`, L4 `ph_*`) rebuild lands (Track B; Q-L5-03); (2) mark old rows stale first so served text cannot outlive its generation; (3) rule: every behaviour change bumps the writer's `*_FORMULA_VERSION` constant (B.8), and the orchestrator's `built_against_writer_hash` is populated (Track E); (4) a post-rebuild assertion: no `empirical` unit lacks `grade_basis`, no served statement contains "Blind retrodiction".
- **Failing-first test and mutation:** post-rebuild SQL assertions (`ins_versions`, `disc_versions` queries in `facts.py` / `facts2.py` are the templates); mutation: re-insert one old-generation row -> the assertion fails.
- **Blast radius:** rewrites the derived L5 rows of the canonical chart (about 114,500 rows; `mi_adhilepa` accounts for 112,270 by its registry `count_sql` = 112,266 rows in the four overlay tables + 4 `mimamsa_load_bearing` rows) and, if the other chart is rebuilt too, its 56 predictions and 35 insight units; no entered data touched.
- **Rebuild:** needs production rebuild (REVIEW for SS)

### 3. CF-L5-02 — Dangling cross-layer references: no foreign keys, 100% of the largest tables reference objects that no longer exist

- **Gate:** Build.completion, Complete, Dens; **assets:** mi_adhilepa, mi_bhavisya, mi_pariksha, mi_pramana, mi_jivanaghatana
- **Evidence:** Read-only joins against the live tables (2026-10-03, facts2.json): `mimamsa_signal_adjustment` 0 of 50,104 origin ids resolve in `bodha_msr_signals` (50,678 rows, latest 2026-09-11, the L3 index records that `bo_laksana` replaced the MSR set on 2026-09-08); `mimamsa_fact_adjustment` 0 of 61,523 in `chart_facts` (143,299 rows); `mimamsa_convergence_adjustment` 0 of 500 (the chart has 0 `kala_convergence` rows); `mimamsa_anchor_adjustment` 0 of 139 (4 anchors exist); `mimamsa_predictions` 4 of 139 `source_pramana_id` resolve in `phala_anchors`; `driving_signals` 0 of 695 references (25 ids) resolve; `mimamsa_attribution` 0 of 15 signal ids resolve; 4 `mimamsa_calibration` rows reference event `5278d97c-…` absent from `life_events` and `mimamsa_event_provenance` (the build saw 51 clean non-held-out events: 153 control windows = 51 x 3; the LEL now gives 50). The L3 index (CF-24) records a cascade mechanism (`ON DELETE CASCADE` keys from `kala_*` and, via `kala_convergence`, `phala_anchors`) that is consistent with the emptying observed here (inference; not traced) and that empties upstream tables when `bo_laksana` replaces its rows; none of it is traced here.
- **Design:** A read-only referential detector for L5 (the `msr_dangling_signal_refs.py` pattern): per L5 table, rows whose origin id no longer resolves; surfaced in the census as Build.completion "stale: N% dangling" so an `error`/`lit` state cannot hide it. No foreign keys are added without SS (cross-layer cascade is the cause of the loss). Rebuild order in CF-L5-01 clears the existing rows.
- **Failing-first test and mutation:** fixture: delete one MSR row -> the detector reports its overlay rows; mutation: disable the join -> 0 reported.
- **Blast radius:** detector only; no data change
- **Rebuild:** none for the detector; clearing needs the CF-L5-01 rebuild

### 4. CF-L5-04 — Constant or proxy status flags (earned-signal register)

- **Gate:** Earn, Null, Narr; **assets:** mi_jivanaghatana, mi_pramana, mi_gunanaka, mi_adhilepa, mi_pariksha, mi_darshana, mi_kula, mi_bhara
- **Evidence:** Register (asset: flag, producer): mi_jivanaghatana `admissible_clean` / `shaped_predictor` (constants over columns that do not exist, :310, :305); mi_pramana `score_magnitude` 0.5 and `score_falsifier` 1.0 on 57/57, `held_out_validity` / `evidence_grade` by `n >= 5` (:541-542), `leakage_status` clean, `n_for_stratum` 1, `evidence_admissibility` clean; mi_gunanaka `held_out_validity = pass`, `gate_passed = True`, `neg_control_clear = True` (:226-230, :273) with the controls `not_implemented`, `confidence_high = n >= 5`, `promoted = n >= 3`; mi_adhilepa `role` (rank of prior weights), `applies_to_reading`; mi_pariksha `degenerate_distribution` (mean test), proxy rows carrying a numeric `result_score`; mi_darshana rank_consequence 0.5 fallbacks, bands +-0.1; mi_kula `evidence_tier = CLASSICAL_CITED` and `calibration_status` literals; mi_bhara `skill_score` float noise on `underpowered` rows (|x| < 6e-15) passed to every kala envelope. Earned examples to copy: mi_jivanaghatana `event_class_id` declared NULL with a reason; mi_pramana `base_rate` NULL (code); mi_sambandha NULL propensity with a machine-readable reason; mi_adhilepa `not_assessed`; mi_pariksha `structural_proxy` / `not_implemented`; mi_darshana `grade_basis`.
- **Design:** For each flag either a detector that can read false (golden-value test + mutation) or NULL / `not_assessed`. DDL: relax NOT NULL where the honest value is NULL (`shaped_predictor`, `skill_score`, `skill_lo/hi`, `ks_p`), additive basis columns elsewhere. Quote the rule once in the layer declarations (`earned_signals`).
- **Failing-first test and mutation:** one golden-value test per flag; mutation: restore the constant -> the test fails.
- **Blast radius:** derived L5 rows; consumers: query_calibration, query_insights, kala envelopes
- **Rebuild:** needs production rebuild (REVIEW for SS)

### 5. CF-L5-08 — People-entered data (N-46): agent writes over or around entered rows

- **Gate:** N-46, Idem; **assets:** lel_events, mi_sankalpa, mi_abhilekha, mi_bhavisya, mi_vistara, mi_gunanaka
- **Evidence:** LEL: `brahmagyan/mimamsa/lel_intake.py:1342/1386/1421` and `lel_event_writer.ts:178` upsert over `event_date` / `description` (8 rows have `date_tightened_at`); ids are `uuid5(chart:class:date:description)`. `mi_sankalpa.py:161-162` deletes and re-inserts native-filed `elected_pending` rows (0 rows now). `mi_abhilekha.py:58-76` writes irreversible `confirmed` / `denied` from a substring of native text. `mi_bhavisya.py:228` deletes manifestation sets of moved predictions; its INSERT collides with any non-pending row. `export_to_bigquery.py --include-life-events` is a manual path by which entered rows leave the DB. `mi_gunanaka` only inserts snapshots; `mimamsa_snapshot_cosign`, `mimamsa_adjudication_log`, `mimamsa_resonance_feedback` (0 rows each) have no owning asset (TG-L5-020). **No entered row is proposed for change or deletion anywhere in this set.**
- **Design:** Q-L5-15, Q-L5-16, Q-L5-12, Q-L5-02: guards that leave entered rows alone (skip / in-place update of derived columns only), structured additive answer codes, content-hash versioning for candidates.
- **Failing-first test and mutation:** disposable-DB interleaving tests (concurrent native update during a build); mutation: remove the guard.
- **Blast radius:** writers only; no data change
- **Rebuild:** none

### 6. CF-L5-10 — Served-surface honesty (consumer side of the same labels)

- **Gate:** Earn, Narr, Dens; **assets:** mi_darshana, mi_pramana, mi_adhilepa, mi_bhara
- **Evidence:** (1) `mimamsa_insight_get` wraps every response with `calibration_status: 'prior_only'` and `mode: 'STRUCTURAL'` as constants (`register_p1_synthesis.ts:642-643`; `calibration_mode: 'STRUCTURAL'` also at :931), beside units that say `empirical` (31 today). (2) The activation gate `gateOpen = sampleSize >= 30` (`activation_gate.ts`) is fed `COUNT(*) FROM mimamsa_calibration` (`query_insights.ts:239-250`) = 57 (32 adjudicated, 13 distinct predictions, 0 prospective). (3) `mimamsa_outcome_record` is an alias to `record_outcome`, whose sidecar and TS implementations are RETIRED (CR-115/CR-128; `outcome.py`, `mimamsa_outcome.ts:196`) and whose HTTP writes route is an inert no-op since migration 471; what the alias returns live was not determined here (a write-class tool: not called). (4) `query_calibration` doc and the tool enum still use the retired `confirmed|partial|denied` vocabulary. (5) kala envelopes serve `skill_score` without `skill_state`. (6) `query_load_bearing` description promises "which signals actually carry the weight". (7) `standing_predictions_read` serves `brahma_prospective_ledger` (18 open), not L5 tables.
- **Design:** Q-L5-09, Q-L5-10, Q-L5-11: compute the labels; change the gate basis; remove or implement the retired alias; correct the descriptions.
- **Failing-first test and mutation:** tool-level tests with a response containing only non-empirical units; mutation: restore the constants.
- **Blast radius:** served envelope fields
- **Rebuild:** none (TS); the labels settle after CF-L5-01

### 7. CF-L5-09 — Service and verifier assets with no consumer path

- **Gate:** Earn, Build; **assets:** mi_seva, mi_abhilekha, mi_vistara
- **Evidence:** `mimamsa_journal`: no writer in the repository (0 rows, 0 charts); `mimamsa_preferences`: no reader or writer (0 rows); `services/mi_seva/handler.py` named in the docstring does not exist; `mimamsa_export_log`: the only inserter targets columns the live table lacks (0 rows); `mi_seva` and `mi_abhilekha` are `DRAFT`, have no digest spec, no self-test, `service_health` NULL; `mi_seva` history 28 errors / 10 aborts, `mi_abhilekha` 26 / 9; the repo's own effect contract marks `mi_abhilekha` "source_observed_unratified ... disposable_fixture_only_until_product_review ... must never be probed against real user outcomes" while the orchestrator runs it in every chart build.
- **Design:** Q-L5-12, Q-L5-13: retire `mi_seva`; qualify `mi_abhilekha`; align or declare `not_built` for the export ledger; one layer self-test that raises when any relation the served tools read is absent.
- **Failing-first test and mutation:** self-test fixture: drop a relation in a disposable DB -> raises; mutation: remove the check.
- **Blast radius:** registry rows; no data
- **Rebuild:** none

### 8. CF-L5-06 — Vocabulary drift inside L5

- **Gate:** Vocab; **assets:** mi_pramana, mi_bhavisya, mi_sambandha, mi_jivanaghatana, lel_events, mi_kula, mi_gunanaka
- **Evidence:** Lifecycle statuses: `pending` / `due` (mi_bhavisya delete), `expired` (sweep), `confirmed` / `denied` (mi_abhilekha), `partial` (tool enum); composite verdicts: `CONFIRMED` / `PARTIAL` / `REFUTED` / `UNRESOLVED` / `FALSE_ALARM` (mi_pramana) vs tool enum `confirmed|partial|denied` (`register_p1_aliases.ts:2102`); promotion / status words: `promoted`/`earning`/`prior_only`, `pass`/`insufficient_n`, `empirical`/`prior_only`, `active`/`suspended_divergence`; domains: prediction {transition, wealth, spirituality, character, career, relationship, health} vs LEL {career, education, spiritual, relationship, health, family, residential+travel, psychological, loss, creative, other, finance, travel} (10 of 53 matched pairs have equal domain); channel ids `ch_<domain>_verbal` vs the prior table's ids; event class absent from `life_events`; holdout rules: md5 20% vs sealed `< 2020-01-01` vs `recorded_at` partition.
- **Design:** Q-L5-06, Q-L5-07, Q-L5-20: one status vocabulary per concept, one domain/event-class map in L0 with class-aware resolvers, one holdout rule.
- **Failing-first test and mutation:** Vocab.identity extended to the status columns; mutation: add a status literal outside the vocabulary.
- **Blast radius:** derived rows + tool enums
- **Rebuild:** rides the CF-L5-01 rebuild

### 9. CF-L5-07 — depends_on audit: declared-but-unread and read-but-undeclared edges

- **Gate:** Build.dag; **assets:** all
- **Evidence:** Unread declared edges (code reading, 2026-10-03): mi_jivanaghatana -> bg_ghatana; mi_kula -> bg_rules; mi_bhavisya -> ph_pramana, ph_phaladesa (and mi_kula, mi_jivanaghatana: it takes family ids by importing `mi_adhilepa._signal_family_key`, :23); mi_pramana -> bg_ghatana; mi_pariksha -> (none unread, but reads `phala_anchors` undeclared); mi_sambandha -> mi_pariksha; mi_darshana -> mi_kula, mi_jivanaghatana, mi_gunanaka (reached transitively); mi_adhilepa -> ga_positions (it reads `chart_facts`, all L1); mi_seva -> mi_adhilepa; mi_bhara -> ka_kshetra is real (reads `kala_field`); mi_sankalpa -> ka_kshetra (reads no `kala_*`). Undeclared reads: `life_events` by mi_jivanaghatana, mi_bhara, mi_sankalpa (+ L4 ph_pramana, ph_rectification); `phala_anchors` by mi_pariksha; `mimamsa_predictions` by mi_gunanaka and mi_pariksha (mi_bhavisya); `brahma_prospective_ledger` by mi_bhara and mi_sankalpa (no asset). A code import runs upstream-from-downstream: mi_bhavisya imports from mi_adhilepa. Migration 691 recorded 32 DAG corrections (19 undeclared-but-read, 13 declared-but-unread), none applied (quoted from the layer instance, not re-measured).
- **Design:** Q-L5-17: one reviewed registry migration with the edge additions/removals above; move `_signal_family_key` to a shared helper; give `brahma_prospective_ledger` an asset or a declared external-source kind.
- **Failing-first test and mutation:** `dag_edge_guard` reads-match PASS for all 15; mutation: remove one edge -> FAIL naming it.
- **Blast radius:** DAG order; Nirmāṇa manifests (not frozen) go stale
- **Rebuild:** none

### 10. CF-L5-05 — Documented-approximation constants and invented priors/defaults

- **Gate:** Null, Vocab; **assets:** mi_pramana, mi_gunanaka, mi_sambandha, mi_darshana, mi_pariksha, mi_bhavisya, mi_kula
- **Evidence:** Constants: mi_pramana verdict 0.65 / 0.35 (:241-246), `_DEFAULT_WEIGHTS` (:60), bin 0.1, n >= 5, `0.5` timing fallback; mi_gunanaka k = 5, cap 3, [0.1, 3.0], n >= 3 / 5, `posterior * 2.0`; mi_pariksha n >= 3, mean >= 0.15, cap 20, offsets +365 / -365 / +730, 90 days; mi_sambandha `_PRIOR_PROPENSITIES` (hand-typed, unsourced) and `.get(channel, 0.5)`; mi_darshana +-0.1 and grade-tier bands, `or 0.5`; mi_bhavisya `or 0.4` / `or 0.7` / `or "moderate"` / `date.today()`; activation_gate.ts `MIN_SAMPLE_SIZE = 30` (disclosed placeholder). Weights already live in `brahma_formula_constants` for pramana / gunanaka / pariksha, with literal fallbacks that could differ (mi_kula fallback `fam_yoga` 0.9 vs registry 1.4).
- **Design:** Q-L5-04: name and ratify engineering constants in `brahma_formula_constants` (one row each, with the "documented approximation" flag as in L3 CF-27 option 1); NULL the priors/defaults that stand in for an unknown; fail loudly (not silently fall back) when a registry constant cannot be read.
- **Failing-first test and mutation:** a lint that finds numeric literals in L5 writers outside a declared constants block; mutation: add a literal.
- **Blast radius:** none until the NULL-ing; then derived rows
- **Rebuild:** rides the CF-L5-01 rebuild

### 11. CF-L5-13 — Registry corrections (surgical migration + seed literals)

- **Gate:** Build.target, Build.count_integrity; **assets:** lel_events, mi_adhilepa, mi_bhara, mi_jivanaghatana, mi_vistara, mi_seva, mi_abhilekha
- **Evidence:** Seed vs live (layer instance 0.3): `mi_jivanaghatana.scope` seed `global` / live `per_chart`; `mi_adhilepa.target_table` seed `mimamsa_signal_adjustment` / live `mimamsa_load_bearing`; `mi_bhara.target_table` seed `kala_field_weight_versions` / live `kala_field_skill` (and the writer touches five tables); `lel_events.catalog_status` seed `DRAFT` / live `CURRENT`. `mi_vistara` kind not declared; `mi_seva` / `mi_abhilekha` `DRAFT`. `mi_gunanaka` `count_sql` counts two tables so `rows_written` 9 != live 13 by design (F-188). `integrity_check_sql` couplings that bind fixes to the registry: `mi_pramana`'s SQL requires `leakage_status`/`evidence_admissibility` = clean, `SUM(reliability.n) = COUNT(calibration)` and the n >= 5 labels (pram-N12); `mi_bhavisya`'s and `ph_nimitta`'s SQL require every prediction's anchor to exist (bhav-N10; A.L4 CF-L4-02(a)); `mi_vistara`'s SQL already encodes the live export DDL. Mixed-table INV classification is missing for `mimamsa_export_log`, `mimamsa_attribution`, `mimamsa_pool_contributions` and the `mi_bhara` `kala_*` writes (reported, not classified).
- **Design:** One surgical, verified migration plus seed edits (migration authored surgically, verified applied, never edited after apply, per section N.4); declarations for kinds.
- **Failing-first test and mutation:** registry census check.
- **Blast radius:** registry rows
- **Rebuild:** none

### 12. CF-L5-14 — Declarations: prose_fields, Carr, Ldgr, Dens/Reach for platform-mcp readers

- **Gate:** Null, Narr, Carr, Ldgr, Dens; **assets:** all
- **Evidence:** declarations 1.12.0 give `prose_fields` for `mi_darshana` and `mi_pariksha` (`["statement"]`) only; the others are `null` (Null / Narr NO_DETECTOR); Carr NO_DETECTOR 15/15 (per-asset semantics unassigned, TG-L5-013); Ldgr measured for `mi_sambandha` only (PASS 47/47, presence not correspondence); offline Dens rev-4 scan: PASS -> PARTIAL for 9 assets (no tier column in the served select), `mi_kula` PASS, `mi_bhara` N/A -> FAIL, the platform-mcp readers (`mi_bhara`, `mi_sankalpa`) are outside the census roots so Dens/Reach under-state their use.
- **Design:** Declare `prose_fields` for the generated-text columns (`mi_jivanaghatana.admissibility_reason`, `mi_pariksha.statement`, `mi_darshana.statement`) with golden-value tests; Carr assignments: D1 for `mi_kula` once citations are verified, D3 for `mi_pramana` / `mi_gunanaka` / `mi_bhara`, N/A by cause for user data and services; extend the census roots to platform-mcp.
- **Failing-first test and mutation:** declarations validation; golden-value tests.
- **Blast radius:** declarations only
- **Rebuild:** none

### 13. CF-L5-11 — Receipts, freshness and digest specs

- **Gate:** Earn, Build; **assets:** all
- **Evidence:** `asset_provenance_receipts`: canonical-chart receipts exist only for `mi_jivanaghatana` (`proven`, 2026-09-06); global `proven` receipts for `mi_kula`, `mi_vistara`; none for the other 12 (every chart asset); `asset_freshness`: the same three rows (`fresh`); `asset_output_digest_specs`: 12 specs (all but `mi_seva`, `mi_abhilekha`, `lel_events`), reviewed 2026-09-05 .. 2026-09-09; `asset_throughput.built_against_writer_hash` unknown (10) or empty (1) for 11 of the 12 chart-scoped assets. A spec exists for `mi_vistara`, which writes nothing.
- **Design:** Receipts and freshness follow the CF-L5-01 rebuild (they are written by the orchestrator); specs for the two services only after Q-L5-13; do not hold a spec for a no-output asset.
- **Failing-first test and mutation:** receipt state `proven` on the canonical chart for each rebuilt asset.
- **Blast radius:** registry rows
- **Rebuild:** rides the rebuild

### 14. CF-L5-12 — Earn.build_record and Cost.baseline instrument absent; Build.history and dep_liveness are cascade records

- **Gate:** Earn, Cost, Build; **assets:** all
- **Evidence:** Saved census: Earn.build_record and Cost.baseline NO_DETECTOR 15/15 (instrument absent, migration 1094); Build.history FAIL 8 / PARTIAL 5 / PASS 1 / N/A 1; Build.dep_liveness FAIL 10 (all because an upstream is `error`); Build.completion FAIL 10 (error state: BLOCKED cascades from `ph_phaladesa` / `ph_pramana` (L4), `ka_kshetra` (L3, `worker_crash`), then within L5). `mi_bhara` and `mi_sankalpa` messages name `timeout:600s` as the failed upstream (not an asset id). `lel_events`: Build.completion FAIL for a no-writer asset (N-14.R236 says N/A).
- **Design:** Shared with CF-05/CF-10 of L1-L3: instrument absent; history is a record no edit changes; the cascade cells clear on a coherent rebuild. `lel_events`: SS approval for the `user_data` N/A rule (Q-L5-19).
- **Failing-first test and mutation:** n/a
- **Blast radius:** none
- **Rebuild:** none

## 5 · Canonical-chart state per asset (chart 482012f1)

Row counts: each asset's registry `count_sql` run read-only on the canonical chart (whole table for the global assets). 'Last writer run' is the latest finished `build_run_assets` row for the chart (`lastrun` fact). The eight assets recorded `error` all errored on 2026-08-21 as upstream-blocked without executing; for seven of them the last writer execution is the 2026-08-13 complete, while `mi_bhara`'s last writer executions (2026-08-12/13) errored with a TypeError.

| asset | live rows | throughput | last writer run | content state |
|---|---|---|---|---|
| lel_events | 63 | no row | no writer run (no writer) | native-entered; 63 rows |
| mi_jivanaghatana | 63 | lit | 2026-09-06 complete | rebuilt 2026-09-06; current |
| mi_kula | 15 | no row | 2026-09-06 complete | global; current (2026-09-06) |
| mi_bhavisya | 278 | error | 2026-08-13 complete | 4/139 anchors, 0/695 signals resolve |
| mi_pramana | 63 | error | 2026-08-13 complete | 57 rows retrospective; base_rate 0.1 (old code); 4 rows -> vanished event |
| mi_gunanaka | 13 | error | 2026-08-13 complete | 2 promoted families on pseudo-replicated n |
| mi_adhilepa | 112270 | error | 2026-08-13 complete | 112,266 / 112,270 rows dangling |
| mi_pariksha | 1664 | error | 2026-08-13 complete | v2.0 rows: "Blind retrodiction" x51; 15/15 signals dangle |
| mi_sambandha | 24 | error | 2026-08-13 complete | v1.0 rows: 7 x "0% propensity (empirical)"; opp 183 vs 139 |
| mi_darshana | 115 | error | 2026-08-13 complete | v1.0 rows: 31 empirical units; 0 embeddings |
| mi_vistara | 0 | no row | 2026-09-06 complete | 0 rows; no writer path for the live DDL |
| mi_seva | 0 | stale | 2026-08-13 complete | 0 rows; stub of an unbuilt handler |
| mi_abhilekha | 0 | stale | 2026-08-13 complete | 0 journal rows; no journal writer |
| mi_bhara | 7 | error | 2026-08-21 error | 7 skill rows (2026-08-09), float-noise scores |
| mi_sankalpa | 0 | dormant | 2026-08-13 complete | 0 rows; dormant |

**Predictions and outcomes on the canonical chart:** `mimamsa_predictions` 139 `pending`, 0 resolved; `brahma_prospective_ledger` 18 `open`; `brahma_mimamsa_prediction_ledger` 5 (1 `unverifiable`, 4 `dismissed`); `mimamsa_calibration_snapshot` 4 `proposed`, 0 two-key complete; `mimamsa_intervention_ledger` 0; `mimamsa_journal` 0 (all charts); `mimamsa_export_log` 0; `mimamsa_preferences` 0. The empty states are consistent with STRUCTURAL mode. The non-empty calibration rows (57), reliability bins (6), multipliers (9) and overlays (112,266 dangling) are the ones this index is about.

## 6 · Nīrmāṇa-frozen assets: what a rebuild or a registry edit does to their manifests

None of the 15 is frozen. EGATE (layer instance 1.1 section 0.3, definition revision `t3-2026-09-11-8b884eac`, 2026-09-30; not re-run here): 13 `BLOCKED-ANCESTORS` (unfrozen ancestors: mi_jivanaghatana 1, mi_kula 6, mi_bhara 35, mi_sankalpa 35, mi_bhavisya 57, mi_abhilekha 58, mi_pramana 59, mi_gunanaka 60, mi_pariksha 60, mi_adhilepa 61, mi_sambandha 61, mi_seva 62, mi_darshana 64) and 2 `BLOCKED-NO-ROUTE` (`lel_events`, `mi_vistara`). The campaign is OFF: a registry edit (CF-L5-07, CF-L5-13) or a rebuild does not invalidate any frozen manifest; it does stale the L5 digest specs (12 specs reviewed 2026-09-05..09).

## 7 · Rebuild consequences Track B needs (facts found while reading the writers)

- **Do not rebuild L5 first.** The chain appears stale: L1-L4 moved after the 2026-08-13 L5 build (fact ids differ, MSR set replaced 2026-09-08 per the L3 index, `kala_convergence` empty, `phala_anchors` 139 -> 4; that these account for the dangling L5 rows is inferred, not traced) and the L5 build was recorded `error` (BLOCKED) on 2026-08-21. A rebuild of L5 before L3/L4 re-create dangling references under new labels. Order: L1 -> L2 (`bo_*`, no `bo_laksana` run afterwards) -> L3 (`ka_sangam` ... `ka_kshetra`) -> L4 (`ph_nimitta` ... ) -> L5: `mi_jivanaghatana` -> `mi_bhavisya` -> `mi_pramana` -> (`mi_gunanaka`, `mi_pariksha`) -> `mi_sambandha` -> `mi_adhilepa` -> `mi_darshana`.
- **A rebuild of `mi_bhavisya` after any prediction has left `pending` fails on the primary key** (DELETE scoped to `pending`/`due`, INSERT without ON CONFLICT, `mi_bhavisya.py:230,243`; by code reading). Nothing has left `pending` yet (139/139 pending, 0 `expired`), so it has not happened; the sweep (`prediction_lifecycle_sweep.ts:348`) or `mi_abhilekha` can make it happen. Land mi_bhavisya FD-1 before any such transition.
- **`mi_bhavisya` re-stamps `emitted_at` on every rebuild**, so a rebuild moves every claim's emission time forward and can turn a prospective claim into a post-hoc one relative to events recorded in between (T1 section 7.3). Land mi_bhavisya FD-1 before the production rebuild, not after.
- **`mi_kula` is global:** its delete-all-and-reseed runs once per global dispatch; rebuilding a chart does not need it. Its fallback to hard-coded weights if `brahma_class_priors` cannot be read is silent (kula FD-2).
- **`mi_gunanaka` appends a snapshot per rebuild** (ratified F-188); 4 exist; each rebuild adds one `proposed` row, none co-signed. `count_sql` counts both tables, so `rows_written` never equals live for this asset by design.
- **`mi_pramana` verdicts depend on the build date** (`date.today()`, `mi_pramana.py:257-270`): two rebuilds on different days can differ with no input change; record the as-of in the receipt (pram FD-4).
- **`mi_adhilepa` converts the 112k-row overlay set whose rows nothing reads**; rebuilding it first spends the largest write in L5 for no consumer (Q-L5-08). Decide before the wave.
- **`lel_intake seed` and `lel_event_writer` must not be re-run against the canonical chart** until the write-path guards land (`lel_events` FD-3): both overwrite `event_date` / `description` on conflict, and 8 rows carry native date tightening.
- **`mi_bhara` last failed in production with a NULL-window `TypeError` (2026-08-12/13)**; main has the guard (`db.py:181`). Whether the container ran it is not established (the latest record is the upstream-blocked error).
- **The Abhinandan chart** (1c826d5a) also holds L5 rows (56 predictions, 35 insight units, 0 calibration, 0 provenance); the same stale-generation labels apply and a rebuild there is a separate REVIEW. It has no LEL, which is the structural state `lel_calibration` calls `structural`.

## 7b · Cross-layer cycle with A.L4 (found when reading the registry integrity SQL)

`ph_nimitta`'s `integrity_check_sql` contains a global term over `mimamsa_predictions` (`source_pramana_id` must resolve in `phala_anchors`); `mi_bhavisya`'s own SQL has the same term. 135 of the 139 canonical-chart predictions fail it today, so an L4 `ph_nimitta` rebuild cannot be accepted while L5 holds them (the A.L4 index records this as CF-L4-02(a)), and an L5 rebuild needs the L4 anchors first. The L5 half of the resolution is `mi_bhavisya` FD-5 (stale marker instead of a hard cross-layer term); it must land together with the A.L4 FD-2 migration, before either chain is rebuilt.

## 8 · Dispositions and the layer instance

The layer instance assigns no disposition (TG-L5-023); it reproduces T2c's provisional codes (`P/E/I/Q` and so on) as unevidenced candidates. This index proposes: **keep (P)** for `lel_events` and `mi_vistara` only, each with an explicit justification in its brief (no rebuild, no output change, no must-fix inside the asset's own rows); **qualify (Q)** for the other twelve (`mi_jivanaghatana`, `mi_kula`, `mi_bhavisya`, `mi_pramana`, `mi_gunanaka`, `mi_adhilepa`, `mi_pariksha`, `mi_sambandha`, `mi_darshana`, `mi_bhara`, `mi_abhilekha`, `mi_sankalpa`), including `mi_kula`, `mi_pariksha` and `mi_bhara`, which each carry a stated must-fix with a rebuild or data migration (unverified `CLASSICAL_CITED` labels; the wrong lift key; float-noise skill scores served on underpowered rows); and **retire (R) proposed** for `mi_seva`. The T2c codes for the qualify assets (Q with E/I/H) are consistent with these proposals. 'Qualify' here means keep the asset and make its labels say what is established.

**Approval under Track A section 10:** keep, qualify and enrich go to the Steward (G16); integrate, retire, consolidate, historical, unresolved and **any output change** go to Strategic Suvarṇa (R5), batched per layer. Almost every L5 fix changes an output or a label, so nearly all of this set is R5. Provisional approval before J1 covers only tier-independent designs.

## 9 · Questions for Strategic Suvarṇa (consolidated; none answered yet)

(R) = raises or defines a verdict or changes outputs: provisional until the J1 review. Ordered by how many assets or gates the answer unblocks; each line keeps the question and appends a recommendation (the default if unanswered is to do nothing).

1. **Q-L5-01** — *mi_pramana, mi_jivanaghatana, mi_bhavisya, mi_gunanaka, mi_sambandha, mi_abhilekha, mi_pariksha*: Chronology gate: may a prediction/event match enter calibration (`mimamsa_calibration`, `mimamsa_reliability`, learned multipliers, the activation-gate sample) only if the event's `recorded_at` and `event_date` are on or after the prediction's `emitted_at`, with earlier matches kept as a separately labelled retrodiction class? (53 of 53 resolvable matches today pre-date emission.) *Recommendation:* Yes. On the canonical chart this takes calibration rows 57 -> 0 and bins 6 -> 0, which is the honest STRUCTURAL state; real values then fill in as prospective outcomes accrue. (R)
2. **Q-L5-02** — *mi_bhavisya, mi_pramana*: Issuance authority: is `mimamsa_predictions` a rebuildable candidate store (as T2 section 9.1 says) whose first `emitted_at` must be preserved by insert-if-absent and whose hash must cover content, or should calibration read the two `brahma_*` ledgers (18 open + 5 rows) as the issuance authority? Also: a rebuild currently collides with any row that has left `pending` (unique key, no ON CONFLICT). *Recommendation:* Keep the table as candidates with insert-if-absent, content hash and versioned supersession; link each candidate to its ledger id; calibrate only candidates that have a ledger linkage for the "prospective" stratum. (R)
3. **Q-L5-03** — *all 13 chart-scoped mi_* assets, lel readers*: Authorise the production rebuild of the L5 chain (after the L3/L4 rebuild lands) so that main's corrected code replaces the 2026-08-13 rows (stale labels served today: 31 `empirical` insight units, 51 "Blind retrodiction" statements, `base_rate = 0.1` x57, 7 grammar rows at 0.0 propensity); and mark the old rows stale before the rebuild. Order: jivanaghatana -> bhavisya -> pramana -> (gunanaka, pariksha) -> sambandha -> adhilepa -> darshana. *Recommendation:* Yes, as one REVIEW-gated Track B wave after Q-L5-01/02 are ruled (otherwise the rebuild re-creates the retrospective calibration under cleaner labels). (R)
4. **Q-L5-04** — *mi_pramana, mi_gunanaka, mi_sambandha, mi_darshana, mi_pariksha, mi_kula*: Constants: ratify as named documented approximations (in `brahma_formula_constants`) the engineering thresholds and weights (verdict 0.65 / 0.35, composite weights, bin width 0.1, n >= 5, k = 5, cap 3, n >= 3 promotion, discovery 3 / 0.15 / 20) — and drop (NULL) the invented priors and missing-term defaults (mi_sambandha channel priors and the 0.5 default, +-0.1 bands, 0.5 / 1.0 fallbacks)? *Recommendation:* Thresholds and weights: ratify as named constants (ask the L3 Q-L3-01 precedent: option 1). Invented priors, bands and defaults: option 2, NULL / `unsourced`. (R)
5. **Q-L5-05** — *mi_jivanaghatana, mi_pramana, mi_gunanaka, mi_bhara*: Status flags: replace the constant / proxy flags (`admissible_clean`, `shaped_predictor`, `held_out_validity`, `gate_passed`, `confidence_high`, `neg_control_clear`, `leakage_status = clean`, `skill_score` on underpowered rows) by detectors or NULL / `not_assessed`; allow the DDL changes this needs (nullable columns, additive basis columns)? *Recommendation:* Yes; unverified admissibility stays calibration-eligible but labelled `unverified_inputs`. (R)
6. **Q-L5-06** — *mi_pramana, mi_bhavisya, mi_sambandha, lel_events*: Vocabulary authority: which L0 map joins prediction domains (transition, wealth, spirituality, character, ...) to LEL categories (finance, spiritual, psychological, residential+travel, ...) and channel ids to domains? Class-aware resolvers (L0 Q4 precedent) or a new map? *Recommendation:* One L0 map in `bg_ontology` with class-aware resolvers; unmapped = NULL (not 0). (R)
7. **Q-L5-07** — *mi_jivanaghatana, lel_events*: One holdout rule: the hash split `md5(event_id) mod 10 >= 8` (13 events, not chronological), the sealed date split `event_date < 2020-01-01` used by `mechanism_retrodiction_get`, and the `recorded_at` partition exist side by side. Which is THE pre-registered holdout? *Recommendation:* The sealed date split; the hash split is retired or renamed `sample_split`. (R)
8. **Q-L5-08** — *mi_adhilepa*: Overlay expansion: 112,266 per-signal / fact / convergence / anchor overlay rows exist, are GATED (no reader) and are 100% dangling. Keep materialising them or stop and keep only the family table? *Recommendation:* Stop (option A); per-object weights, if ever served, are a serve-time join. Existing rows are derived and regenerable. (R)
9. **Q-L5-09** — *mi_adhilepa, mi_darshana*: Remove the counterfactual sentence "Removing this signal would materially alter the reading" and rename `role` (rank position of the classical prior) until a real ablation exists? *Recommendation:* Yes. (R)
10. **Q-L5-10** — *mi_darshana (served)*: Compute `calibration_status` / `mode` in `mimamsa_insight_get` from the returned units and the gate basis instead of the constants `prior_only` / `STRUCTURAL` (`register_p1_synthesis.ts:642-643`, also `register_p1_synthesis.ts:931`)? *Recommendation:* Yes; STRUCTURAL remains the default until a chronology-clean `empirical` unit exists. (R)
11. **Q-L5-11** — *mi_pramana, mi_darshana (consumers: activation gate)*: Activation-gate sample basis: `total_matches = COUNT(*) FROM mimamsa_calibration` (57 = 32 adjudicated = 13 distinct predictions = 0 prospective) opens the `empirically_calibrated` gate at >= 30 by code reading. Should the sample be distinct, adjudicated, chronology-clean predictions? (Paripraśna code; the data comes from L5.) *Recommendation:* Yes; coordinate with the Paripraśna owner. Until then the gate's own note says its 30 is a placeholder. (R)
12. **Q-L5-12** — *mi_abhilekha*: Journal adjudication: replace the substring rule ("yes"/"confirmed" -> confirmed, else denied) by a structured additive answer code, leave ambiguous text `pending`, scope the read to the chart, and build the missing journal intake (no writer exists)? Or retire the journal path in favour of the learning API's adjudication (`mimamsa_adjudication_log`)? *Recommendation:* Structured code + chart scope; choose one adjudication path (the API) and retire the other. (R)
13. **Q-L5-13** — *mi_seva, mi_vistara, mi_abhilekha*: Service assets: retire `mi_seva` (a four-table existence check describing a handler that does not exist and that, as described, would apply learned multipliers at serve time against the collect-only doctrine)? Keep `mi_vistara` and bind it to a working exporter? Mark `mi_abhilekha` per Q-L5-12? *Recommendation:* Retire mi_seva; keep mi_vistara with an exporter aligned to the live ledger DDL; qualify mi_abhilekha. (R)
14. **Q-L5-14** — *mi_darshana*: Embeddings: implement the deterministic embedding write for `mimamsa_insight_embeddings` (CLAUDE.md section N.4 permits embeddings as a deterministic transform) or declare the half out of scope (`not_built`) and say so in the served capability? *Recommendation:* Implement if the semantic-search capability is wanted; otherwise `not_built`. Not blocking.
15. **Q-L5-15** — *lel_events, mi_vistara*: LEL write-path guards (N-46): `lel_intake seed` and `lel_event_writer` use ON CONFLICT DO UPDATE over event_date / description; ids are content-derived. Accept code-only guards (never overwrite a tightened/corrected row; correction ids derived from the original id; no seed re-run on a populated chart without a flag), with no data change? *Recommendation:* Yes. No entered row is changed or deleted by this lane or by the proposed fixes.
16. **Q-L5-16** — *mi_sankalpa*: Replace the delete-then-reinsert of native-filed `elected_pending` rows by an in-place UPDATE of the outcome link (N-46)? The table is empty now, so the change costs nothing today. *Recommendation:* Yes.
17. **Q-L5-17** — *all 15*: depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
18. **Q-L5-18** — *lel_events (consumer: L4 ph_pramana)*: L4 `ph_pramana.py:190` loads every `life_events` row, unscoped, to emit `life_event_match` / `life_event_miss` evidence on anchors. Is the LEL (outcome ground truth) allowed to feed prospective L4 posteriors at all (T1 section 8.1, T2 section 6.6)? If yes, scope it to the chart; if no, remove the read. *Recommendation:* Owner is the A.L4 brief; recommend scoping now and a doctrine ruling on whether outcome evidence may enter L4. (R)
19. **Q-L5-19** — *all 15*: Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
20. **Q-L5-20** — *mi_kula, mi_pramana, mi_gunanaka, mi_darshana*: Tier vocabulary (TG-L5-014): adopt `structural / prior_only / assignment_only / empirical` (the vocabulary `mi_darshana` already stores with a `grade_basis`) as the layer vocabulary, with a named detector for each tier and one meaning of "empirical" (chronology-clean, adjudicated, independent, n >= ratified minimum)? *Recommendation:* Yes. (R)
21. **Q-L5-21** — *mi_pariksha*: Attribution lift key: fix the `anchor_lift` lookup (anchor id vs signal id) so the lift factor applies, or remove the lift term? Also make the discovery cap deterministic and strongest-first. *Recommendation:* Fix the key against the prediction's source anchor; deterministic strongest-first cap. (R)

### 9.1 Dens re-measured offline with the current scanner

Static `capability_scan` + `_grade_dens` (REGISTRY_REVISION 16) over the real source tree, no database (`offline_rollup_L5.py`; `dens_rev4_static` in `rollup_saved_L5.json`): saved -> offline: lel_events N/A -> PARTIAL; mi_jivanaghatana N/A -> NO_DETECTOR; mi_kula PASS -> PASS; mi_bhavisya PASS -> PARTIAL; mi_pramana PASS -> PARTIAL; mi_gunanaka PASS -> PARTIAL; mi_adhilepa PASS -> PARTIAL; mi_pariksha PASS -> PARTIAL; mi_sambandha PASS -> PARTIAL; mi_darshana PASS -> PARTIAL; mi_vistara N/A -> NO_DETECTOR; mi_seva N/A -> NO_DETECTOR; mi_abhilekha PASS -> PARTIAL; mi_bhara N/A -> FAIL; mi_sankalpa N/A -> NO_DETECTOR. The platform-mcp readers of `mi_bhara` and `mi_sankalpa` are outside the census roots.

### 9.2 Context from SS N-97 / N-99 / N-102 (per Exec Suvarṇa, 2026-10-03; not verified by this lane)

- The L4/L5 integrity cycle (section 7b; bhav-N10) is addressed by migration **1259**, which moves `ph_nimitta`'s integrity term out of L4 (post-window, **HELD**); migration **1260** replaces the L3 -> L4 cascades. If 1259 lands as described, `mi_bhavisya` FD-5 narrows to adding the L5-side stale marker and re-homing the anchor-existence check; re-read both migrations before relying on this.
- Dispositions here are proposals; each Track A lane will later write one machine-validated entry per asset into `asset_dispositions.jsonl` (N-97). Each brief carries exactly one `DISPOSITION:` and one `EVIDENCE_POINTER:` line in section 3.

## 10 · Track I items arising (from the per-asset designs)

| id | asset | FD | title | fix class | rebuild | output change |
|---|---|---|---|---|---|---|
| TI-L5-01 | lel_events | FD-1 | Declare the readers' edges; declare the asset's kind | registry/declaration | n | none |
| TI-L5-02 | lel_events | FD-2 | Scope the L4 read of the LEL (owner A.L4) and decide whether the LEL may feed L4 at all | writer code (L4) | n | none today (one chart has events); becomes real as soon as a second ch |
| TI-L5-03 | lel_events | FD-3 | Write-path guards for entered rows (N-46) | writer code (TS + Python) | n | none for existing data |
| TI-L5-04 | lel_events | FD-4 | Declarations: user data, not generated prose | registry/declaration | n | none |
| TI-L5-05 | mi_jivanaghatana | FD-1 | Make admissibility say what it establishes (R) | data (output change) + writer code + additive migration | y | yes: reason text on 63 rows; `shaped_predictor` NULL on 63 rows; `admi |
| TI-L5-06 | mi_jivanaghatana | FD-2 | Persist the recorded-at partition so the firewall can be applied from stored data (R) | writer code + additive migration | y | additive column; no existing value changes |
| TI-L5-07 | mi_jivanaghatana | FD-3 | One holdout rule (R) | data (output change) + writer code | y | yes: `held_out` membership changes for some of the 63 events -> SS (R5 |
| TI-L5-08 | mi_jivanaghatana | FD-4 | Remove dead code, declare the real reads | writer code + registry | n | none |
| TI-L5-09 | mi_kula | FD-1 | Label the citations honestly (R) | data (label) + writer code + declaration | y | yes: `evidence_tier` text on up to 7 rows -> SS (R5) |
| TI-L5-10 | mi_kula | FD-2 | Fail loudly when the priors cannot be read | writer code | n | none while the registry is readable |
| TI-L5-11 | mi_kula | FD-3 | Derive family calibration status from the multipliers | writer code + served surface (TS) | n | served label changes for `fam_graha_natal`, `fam_transit` -> SS (R5) |
| TI-L5-12 | mi_bhavisya | FD-1 | Insert-if-absent: keep the first `emitted_at`, hash the content (R) | data (output change) + writer code + additive migration | y | yes: the stored `frozen_bundle_hash` values change once (content hash) |
| TI-L5-13 | mi_bhavisya | FD-2 | Keep manifestation sets for moved predictions | writer code | n | none for current data (all pending) |
| TI-L5-14 | mi_bhavisya | FD-3 | Do not turn silence into numbers (R) | writer code | y | none on current data (defaults did not fire); behaviour change for fut |
| TI-L5-15 | mi_bhavisya | FD-4 | Break the L4 <-> L5 integrity cycle with a stale marker (R) | registry/declaration + migration (CHECK) + writer code | n | none to stored claim content; adds a marker to 135 rows -> SS (R5) |
| TI-L5-16 | mi_bhavisya | FD-5 | Declare the real reads; remove the downstream import | writer code + registry | n | none |
| TI-L5-17 | mi_pramana | FD-1 | Chronology gate in the match substep (R) | data (output change) + writer code + additive migration | y | yes: on the canonical chart all 53 resolvable pairs leave calibration  |
| TI-L5-18 | mi_pramana | FD-2 | Honest denominators and a non-circular reliability definition (R) | data (output change) + writer code | y | yes: the 6 bins change; `observed_rate` becomes NULL where no adjudica |
| TI-L5-19 | mi_pramana | FD-3 | Replace proxy status flags by detectors or null (R) | data (output change) + writer code | y | yes: dimension scores, composite, verdicts and bin labels change -> SS |
| TI-L5-20 | mi_pramana | FD-4 | Pin the clock and the code version | writer code | y | adds a column / label; verdicts unchanged under the same `as_of` |
| TI-L5-21 | mi_pramana | FD-5 | Join domains through one vocabulary (R) | writer code + vocabulary | y | yes -> SS (R5) |
| TI-L5-22 | mi_gunanaka | FD-1 | Replace the status literals by detectors or NULL (R) | data (output change) + writer code (+ possibly a migration if columns are NOT NULL booleans) | y | yes: 9 rows' flags and the 2 promotions change -> SS (R5) |
| TI-L5-23 | mi_gunanaka | FD-2 | Count independent observations (R) | data (output change) + writer code | y | yes: n 271 -> at most 13, 14 -> at most 2 -> SS (R5) |
| TI-L5-24 | mi_gunanaka | FD-3 | No invented neutral values | writer code | n | none on current data |
| TI-L5-25 | mi_gunanaka | FD-4 | A failed snapshot publish fails the step; test the UUID path | writer code + test | n | none |
| TI-L5-26 | mi_adhilepa | FD-1 | Stop calling a prior ranking a sensitivity (R) | writer code (two assets) + served description | y | yes: 4 stored rows + 4 served insight units change text/labels -> SS ( |
| TI-L5-27 | mi_adhilepa | FD-2 | Decide whether to materialise the overlays at all (R) | data (retirement) or writer code | y | A: 112,266 rows retired (R5); B: none beyond the fixes |
| TI-L5-28 | mi_adhilepa | FD-3 | `applies_to_reading` means learned | writer code | y | yes: 174 + more rows flip -> SS (R5) |
| TI-L5-29 | mi_adhilepa | FD-4 | Provenance, naming and reads | writer code + registry | y | origin_asset_id text changes on 61,523 rows (derived) -> SS if the tab |
| TI-L5-30 | mi_pariksha | FD-1 | Fix the lift-vector key (R) | data (output change) + writer code | y | yes: `credit_blame` changes on rows whose prediction has a lift vector |
| TI-L5-31 | mi_pariksha | FD-2 | Deterministic, strongest-first discovery cap | writer code | y | yes: which 20 of the candidates are kept may change -> SS (R5) |
| TI-L5-32 | mi_pariksha | FD-3 | Make the degenerate-distribution check measure a distribution | writer code | y | label change on 1 row |
| TI-L5-33 | mi_pariksha | FD-4 | Stop numbers on non-results | data (output change) + writer code | y | yes: 168 rows' result_score -> NULL -> SS (R5) |
| TI-L5-34 | mi_pariksha | FD-5 | Declare the real reads | registry | n | none |
| TI-L5-35 | mi_sambandha | FD-1 | Count predictions, not join rows | data (output change) + writer code | y | yes: `opportunity_count` 183 -> 139 and the n >= 5 gates -> SS (R5) |
| TI-L5-36 | mi_sambandha | FD-2 | Source or drop the priors; stop defaulting to 0.5 (R) | data (output change) + writer code + additive migration | y | yes: prior and band columns on up to 24 rows -> SS (R5) |
| TI-L5-37 | mi_sambandha | FD-3 | Rebuild on current code and bump the version label | rebuild only | y | stored rows change (7 rows lose the 0.0 and the grade) |
| TI-L5-38 | mi_sambandha | FD-4 | Declare the real reads | registry | n | none |
| TI-L5-39 | mi_darshana | FD-1 | Rebuild on current code after the upstream chain; bump the version label | rebuild | y | yes: 31 units lose `empirical`; 51 retrodiction units regraded -> SS ( |
| TI-L5-40 | mi_darshana | FD-2 | Compute the served calibration status instead of a constant (R) | served surface (TS) | n | yes: served envelope fields -> SS (R5) |
| TI-L5-41 | mi_darshana | FD-3 | Remove narration without a detector; no 0.5 fallbacks (R) | writer code | y | yes: some units change text or lose a number -> SS (R5) |
| TI-L5-42 | mi_darshana | FD-4 | Stable insight ids | writer code | y | id strings change once |
| TI-L5-43 | mi_darshana | FD-5 | Decide the embedding half (R) | writer code or declaration | y | A adds rows; B changes a label |
| TI-L5-44 | mi_vistara | FD-1 | Align the exporter with the live ledger or retire the exporter log | writer code (manual CLI) + test | n | none (0 rows) |
| TI-L5-45 | mi_vistara | FD-2 | Make completion mean something | declaration/registry | n | none |
| TI-L5-46 | mi_seva | FD-1 | Retire the asset (R) | registry/declaration (retirement) | n | none (no rows) |
| TI-L5-47 | mi_seva | FD-2 | If kept: say what it is | declaration/registry | n | none |
| TI-L5-48 | mi_abhilekha | FD-1 | Structured adjudication, no guessing (R) | writer code + additive migration + (new) intake | n | none on current data (0 rows); behaviour change for future answers ->  |
| TI-L5-49 | mi_abhilekha | FD-2 | Scope the journal read to the chart being built | writer code | n | none on current data |
| TI-L5-50 | mi_abhilekha | FD-3 | Declare the real edges and the service contract | registry/declaration | n | none |
| TI-L5-51 | mi_bhara | FD-1 | Underpowered skill is null (R) | writer code + DDL + served surface (TS) | y | yes: 7 + 6 stored values and the envelope field -> SS (R5) |
| TI-L5-52 | mi_bhara | FD-2 | Per-class prospective counts | writer code | n | none on current data (0) |
| TI-L5-53 | mi_bhara | FD-3 | Regression test and verification for the NULL-window failure | test | n | none |
| TI-L5-54 | mi_bhara | FD-4 | Register what the writer writes; declare its reads | registry/declaration | n | none |
| TI-L5-55 | mi_sankalpa | FD-1 | Update in place; never delete a filed row (N-46) | writer code | n | none on current data (0 rows) |
| TI-L5-56 | mi_sankalpa | FD-2 | Declare the real reads | registry | n | none |
| TI-L5-57 | mi_sankalpa | FD-3 | Pin the matcher on interval windows with a regression test | test | n | none |

Shared fixes (section 4) are carried by the per-asset items above; CF-L5-02 (the referential detector) and CF-L5-14 (declarations) have no per-asset FD of their own and are Track E / declarations items.

## 11 · Decisions applied

None. No L5 decision sheet has been answered. The L0 rulings of 2026-10-01 (Q1, Q2, Q11, Q13) and the L3 carry-over (Q-L3-16) are the precedent and are cited by analogy only; Q-L5-19 asks whether they carry. The SS citations rule (an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only passage-level verified citations count toward Ldgr PASS) is applied to `mi_kula` and `mi_sambandha`.

## 12 · Notes on method and path

- **Path:** per Track A brief section 8: `00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/<ASSET_ID>_ELEVATION_BRIEF_v1_0.md`. Fix designs live inside each brief (section 4), as in the L0-L3 sets; `INDEX.md` sits beside the briefs; evidence scripts and outputs are committed under `_evidence/`.
- **Line citations** were produced from the files at `main adb0db29d` (`git worktree` at `/Users/Dev/suvarna-al5`); a bare `:N` in a brief is a line of that asset's own writer. A script re-checks each cited pattern (see REPORT).
- **Defect classes of the L0-L3 reviews, and how this set avoids them:** stale premises (every premise under a line citation was re-read; where the premise was false it is corrected: the '12 mi_* assets' count, the `ph_pramana` docstring that says `life_events` has no `chart_id`, the `mi_vistara` docstring that names an inserter that does not exist); `count_sql` scope (CF-L5-13 and the `mi_gunanaka` note); consumer lists traced in code (section 0 of each brief; declared-vs-actual stated per asset); rebuild flags consistent across brief, section 3 and section 10 (computed by script from the FD rebuild fields); real per-fix blast radius; arithmetic that adds up (section 3 check line); no invented numbers (every number is a quoted query or a cited line).
- **Variance from Track A section 5/8 (SS approved the variance for L0-L3; the same format is used here):** sections 0-7 rather than the T4 template's 0-9; no separate DISPOSITIONS file or `designs/` directory; the gate table is per criterion with a rollup line; plus three sections added at the lane brief's request (2.3 earned-signal and narration audit, 2.4 honest nulls, 2.5 UUID / leakage / N-46 checks).
- **Facts not established here:** why `phala_anchors` fell from 139 to 4 (the L3 CF-24 cascade is the probable mechanism, untraced); why LEL event `5278d97c-…` is gone; what the served alias `mimamsa_outcome_record` returns live; whether the production container ran main's `mi_bhara` NULL-window guard; the activation gate's live output (derived from code and the 57 count); the content of `mimamsa_attribution`'s INV class; whether `brahma_class_priors` v1.0 values are sourced (A.L0 question).

## 13 · Format used (shared with the L0-L3 sets)

Each brief is `<ASSET_ID>_ELEVATION_BRIEF_v1_0.md` with: frontmatter (asset_id, layer, artifact, version, status banner, produced_by, produced_on, plan_item, census_revision_used, template_revision, layer_instance, base_commit, disposition, disposition_proposal_approver, risk_class, decisions_applied, track_i_items, ledger_gap_ids); **section 0 Identity** (what the asset is with file:line, canonical-chart state, field table incl. consumers, tests, receipts, dependencies); **section 1 Measured state and the nine gates**; **section 2 Gaps** (2.1 ledger rows, 2.2 gaps found, 2.3 earned-signal and narration audit, 2.4 honest nulls, 2.5 UUID / leakage / N-46); **section 3 Disposition**; **section 4 Fix designs** (FD-n); **section 5 Semantic fingerprint**; **section 6 Preserved kernel, carriage, opportunities**; **section 7 Decisions and open questions**.
