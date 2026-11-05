---
asset_id: mi_adhilepa
layer: L5 Mīmāṃsā (mi_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna (lane track-a-l5)
produced_on: 2026-10-03
plan_item: A.L5 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION). Offline rollup under main REGISTRY_REVISION 16. Live registry, row counts, receipts and fact queries re-read 2026-10-03 (read-only)."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L5/L5_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main adb0db29d"
disposition: "qualify"
disposition_proposal_approver: "Strategic Suvarṇa (R5; any retirement of the overlay tables is R5)"
risk_class: "high (largest row count in L5; label removal; possible retirement)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-26, TI-L5-27, TI-L5-28, TI-L5-29]
ledger_gap_ids: ["mi_adhilepa-Build.completion", "mi_adhilepa-Earn.build_record", "mi_adhilepa-Cost.baseline", "mi_adhilepa-Build.history", "mi_adhilepa-Build.dep_liveness", "mi_adhilepa-Carr.detector", "new: adh-N1", "new: adh-N2", "new: adh-N3", "new: adh-N4", "new: adh-N5", "new: adh-N6", "new: adh-N7", "new: adh-N8", "new: adh-N9"]
---

# mi_adhilepa — Calibration overlays on signals, facts, convergences and anchors, plus the load-bearing map

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_adhilepa.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

LIGHT writer (`run(ctx)`, :191). Reads the chart's family multipliers (`mimamsa_multipliers`, :114-124) and expands each applicable family multiplier into one overlay row per matching object: every `bodha_msr_signals` row (family by `_signal_family_key`, :36-80, fallback `fam_msr_signal`), every `chart_facts` row whose category maps to a family (`_fact_family_key`, :83-110), up to 500 `kala_convergence` rows (`LIMIT 500`, no ORDER BY, :297) and every `phala_anchors` row. Rows go to `mimamsa_signal_adjustment`, `_fact_adjustment`, `_convergence_adjustment`, `_anchor_adjustment` (delete-then-insert per chart, :201-210), each carrying the family multiplier (bounded at 2.5, :155), `evidence_n`, `leakage_status = 'not_assessed'` (:163), `applies_to_reading` and `derived_from_pramana_ids = []` (:177). It also writes `mimamsa_load_bearing`: the top five family multipliers >= 1.0, ranked by applied multiplier, labelled `load_bearing` / `supporting` / `redundant` by rank position (:336-358).

**Canonical chart state (read-only, 2026-10-03).** **112,270 rows = signal 50,104 + fact 61,523 + convergence 500 + anchor 139 + load-bearing 4.** Signal overlays: `fam_graha_natal` 47,059 (x0.9924, evidence_n 271), `fam_transit` 2,871 (x0.9643, n 14), `fam_yoga` 80 (x1.4, n 0), `fam_divisional` 49 (x0.95, n 0), `fam_msr_signal` 45 (x1.4, n 0). Fact overlays: divisional 35,209, graha_natal 16,721, ashtakavarga 9,360, dasha 145, yoga 88; `origin_asset_id = 'ga_facts'` on 61,523/61,523. `applies_to_reading` is true on all (including the 174 signal rows whose multiplier is an unlearned prior, n = 0, 1.4). **Referential state (read-only joins): 0 of 50,104 signal origin ids resolve in the current `bodha_msr_signals` (50,678 rows computed 2026-09-11); 0 of 61,523 fact ids resolve in the current `chart_facts` (143,299 rows); 0 of 500 convergence ids (the chart has 0 `kala_convergence` rows now); 0 of 139 anchor ids (4 anchors exist, none among them).** 112,266 of 112,270 rows (100% of the overlay rows) reference objects that no longer exist (`adh_*_live`; CF-L5-02).

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / per_chart / postgres_table | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2971` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_adhilepa.py:182` `@register("mi_adhilepa")`; registry `has_writer` = t | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_load_bearing`; count_sql tables: `mimamsa_load_bearing`, `mimamsa_convergence_adjustment`, `mimamsa_anchor_adjustment`, `mimamsa_signal_adjustment`, `mimamsa_fact_adjustment` | registry / census |
| count_sql (live) | `SELECT   (SELECT count(*) FROM mimamsa_load_bearing           WHERE chart_id = $1) +   (SELECT count(*) FROM mimamsa_convergence_adjustment WHERE chart_id = $1) +   (SELECT count(*) FROM mimamsa_anchor_adjustment      WHERE chart_id = $1) +   (SELECT count(*) FROM mimamsa_signal_adjustment      WHERE chart_id = $1) +   (SELECT count(*) FROM mimamsa_fact_adjustment        WHERE chart_id = $1) AS count` | registry |
| live rows (canonical chart) / floor | 112270 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / False / 10800s | registry |
| registry build state (canonical chart) | throughput `error`, rows_written 112270, last_built_at 2026-08-21T02:36:53Z; recent canonical runs: complete 2026-08-13; complete 2026-08-07; error 2026-08-07; complete 2026-07-28 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `mi_gunanaka`, `bo_laksana`, `ka_sangam`, `ph_nimitta`, `ga_positions` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | `mi_darshana`, `mi_seva` (registry); census transitive blocking radius 2 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Declared (live registry): `mi_gunanaka`, `bo_laksana`, `ka_sangam`, `ph_nimitta`, `ga_positions`. Actual reads: `mimamsa_multipliers`, `bodha_msr_signals` (`bo_laksana`), `chart_facts` (:271; produced by many L1 assets — `ga_positions` alone is not the source), `kala_convergence` (`ka_sangam`), `phala_anchors` (`ph_nimitta`). Writes `origin_asset_id = 'ga_facts'` (:284) — **no such asset exists in the registry** (0 rows). | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | **No served reader of the four overlay tables**: `query_load_bearing.ts` and `index.ts` only mention them in comments; they are classed GATED (TABLE_CONCEPT_DISPOSITIONS_v2_0.md §6, per the `query_load_bearing.ts` header) and `grep` finds no select of them in `platform/src`, `platform-mcp/src` or the sidecar. `mimamsa_load_bearing` is served by `query_load_bearing.ts:84` and read by `mi_darshana.py:392`. `mi_seva.py:39-43` checks that `mimamsa_signal_adjustment` exists. | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `writers/tests/test_mi_adhilepa_leakage.py` (14 tests: the label is `not_assessed`, not None, not `clean`; source-text), `tests/l5/test_mi_adhilepa_b7.py` (52 tests), `L5_mimamsa/__tests__/query_load_bearing.test.ts`; no test of the load-bearing rank semantics | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | no receipt, no freshness row for the canonical chart; digest spec present (reviewed 2026-09-09T04:01Z); natural-key partition migration 989; throughput `error` 2026-08-21 (BLOCKED on `mi_gunanaka`), rows_written 112,270 = live 112,270; last writer execution complete 2026-08-13T01:16:30Z | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (61) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). Line numbers inside quoted census text are as of the saved run (older code), not main. NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): mimamsa_anchor_adjustment (mi_adhilepa.py:208), mimamsa_convergence_adjustment (mi_adhilepa.py:208), mimamsa_fact_adjustment (mi_adhilepa.py:208), mimamsa_load_bearing (mi_adhilepa.py:208), mimamsa_signal_adjustment (mi_adhilepa.py:208) |
| Build | Build.target † | PASS | target_table=mimamsa_load_bearing |
| Build | Build.dag † | PASS | 5 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | FAIL | build record state='error' is not a completed build (rows_written=112270, live=112270, chart 482012f1) — see Build.history; target_table mimamsa_load_bearing alone: 9 row(s), whole table — context, not the compared figure |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=112270) |
| Complete (information) | Complete.depth | PASS | 9 rows, 6 cols; fully populated 6; NEVER populated [] |
| Dens | Dens.served † | PASS | 1 module(s): query_load_bearing.ts; declaring density_contract: 1 |
| Build | Build.history | FAIL | most recent run error (2026-08-21); 31 error(s), 10 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-08-21): BLOCKED: upstream dependency(ies) mi_gunanaka did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | FAIL | 2/5 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_gunanaka (error, chart 482012f1)']; stale: ['ka_sangam (stale, chart 482012f1)', 'ph_nimitta (stale, chart 482012f1)'] — a DEP-ASSERT trap if no writer can light them |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |

**PASS cells (compact):** Build.registered, Build.contract, Vocab.identity, Build.exercised.

**Reported, not graded (NOT_GENERIC):** Reach.fields, Complete.width.

**Offline rollup** (main's `rollup_asset` rules, REGISTRY_REVISION 16, applied to the SAVED measurements; N/A reads NO_DETECTOR when no rule is declared; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L5/rollup_saved_L5.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build FAIL.

**Offline Dens rev-4 static scan** (`capability_scan` + `_grade_dens` over the real source tree, no database; `offline_rollup_L5.py`): saved PASS -> PARTIAL.



## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens verdict whose meaning changed at rev 4/5; **+ SS question** = the fix changes output or rests on a ruling. Ids beginning `new:` were found by reading code and data in this lane and are in no ledger.

**2.1 Ledger rows (inspector-emitted, all OPEN at 2026-09-27) and this lane's class for each**

| ledger gap id (`asset_gaps.jsonl` @ 2a78ec64d) | criterion | class | note |
|---|---|---|---|
| mi_adhilepa-Build.completion | Build.completion | stale | measured: build record state='error' is not a completed build (rows_written=112270, live=112270, chart 482012f1) — see Build.history; target_table ... |
| mi_adhilepa-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_adhilepa-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_adhilepa-Build.history | Build.history | history | measured: most recent run error (2026-08-21); 31 error(s), 10 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-... |
| mi_adhilepa-Build.dep_liveness | Build.dep_liveness | stale | measured: 2/5 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_gunanaka (error, chart 482012f1)']; stale: ['ka_sangam (stale... |
| mi_adhilepa-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: adh-N1 | Earn / narration | real (central) | `mimamsa_load_bearing` ranks **family prior weights**, not signal sensitivity: the 4 rows are `fam_yoga` (0.7, `load_bearing`), `fam_msr_signal` (0.7, `supporting`), `fam_convergence` (0.6, `supporting`), `fam_dasha_period` (0.575, `redundant`), i.e. `sensitivity = applied_multiplier / 2` (:346) of the n = 0 classical priors 1.4 / 1.4 / 1.2 / 1.15; the `signal_id` column holds a family id; `role` is the rank position (:347); the two 0.7 are a tie broken by dict order. `mi_darshana.py:402` then serves this as "Signal 'fam_yoga' is load_bearing for conclusion 'concl_fam_yoga' ... Removing this signal would materially alter the reading." No ablation, perturbation or sensitivity run exists behind it (the `mi_pariksha` ablation is a `structural_proxy`). A causal sentence with no detector (§N.7 item 5, §N.8) |
| new: adh-N2 | dangling | stale + real | 100% of overlay rows reference ids that no longer resolve (CF-L5-02). Observed: the live MSR set is dated 2026-09-11 (the L3 index records that `bo_laksana` replaced it on 2026-09-08), the live `chart_facts` ids differ from the stored ones, the chart has 0 `kala_convergence` rows, `phala_anchors` holds 4 rows against 139 at build time. That these changes (and the cascade keys the L3 index describes) are what orphaned the overlay is an inference from timestamps and counts, not traced. There are no foreign keys, so nothing failed. The overlay is stale relative to its sources until a coherent rebuild (CF-L5-01) |
| new: adh-N3 | design / consumer | real + SS question | the four overlay tables hold 112,266 rows with no served reader (GATED) and a per-object expansion of what is a 9-row family table: every signal of a family receives the same scalar. As materialised data it adds no information beyond `mimamsa_multipliers` + a join at serve time (Q-L5-08) |
| new: adh-N4 | Earn (applies_to_reading) | real | `applies_to_reading` = `kill_switch_state == "active"` (:164) is true for prior-only multipliers (n = 0) as well as learned ones; "applies to reading" reads as "a learned calibration applies", while 174 signal rows apply an unlearned 1.4 and the learned ones are 0.9924 / 0.9643 (within 1% of neutral) |
| new: adh-N5 | honest label (the model case) | information | `leakage_status = "not_assessed"` (:163) — an honest named state replacing a former `clean`; the writer comment records why (migration 547). The tests pin the label. The label is not a detector: it states that none ran |
| new: adh-N6 | determinism | real | `SELECT convergence_id FROM kala_convergence WHERE chart_id = %s LIMIT 500` has no ORDER BY (:297): which 500 rows are kept can change between runs (a CF-22-class cap); the table now holds 0 rows so a rebuild writes 0 convergence overlays (an honest zero produced by upstream loss, not a decision) |
| new: adh-N7 | provenance column | information | `derived_from_pramana_ids` is `[]` on every row ("full backfill in later version", :177): a provenance column that is always empty; `n_pramana` is always passed as 0 |
| new: adh-N8 | Build.dag | real | facts are read from `chart_facts` (all L1 assets) under a single `ga_positions` edge; `origin_asset_id` names a non-asset (`ga_facts`); `mi_bhavisya` imports this module's helper (CF-L5-07) |
| new: adh-N9 | Dens | Dens rev-1 reading | saved Dens PASS (1 module, contract declared); rev-4/5 offline scan reads PARTIAL (no tier column in the served select) |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| `role = load_bearing / supporting / redundant` | the signal carries / helps / does not matter for the conclusion | rank position of the family's classical prior (:343-347) | **unearned**: ordinal label presented as sensitivity analysis |
| `sensitivity` | how much the conclusion depends on the signal | `min(applied_multiplier / 2, 1)` (:346) | **a rescaled prior weight** |
| served sentence "Removing this signal would materially alter the reading" | a counterfactual | fixed template in `mi_darshana.py:402` | **narration without a detector** (§N.7 item 5) |
| `leakage_status = not_assessed` | no leakage detector has run | literal (:163) | **earned**: says exactly that |
| `applies_to_reading` | the overlay is applied to the reading | `kill_switch_state == active` (:164) | proxy; true for unlearned priors |
| `multiplier` / `applied_bound` | learned calibration of the object | family multiplier, bound 2.5 (:155) | earned as a copy of the family value; the family value is the question (mi_gunanaka) |
| `derived_from_pramana_ids` | the calibration rows the overlay derives from | `[]` constant (:177) | empty by omission, not by finding |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD: `leakage_status` was moved from a false `clean` to `not_assessed`; no multiplier -> zero overlay rows with a note (:213-216); the fact selection is deterministic (`ORDER BY fact_id`, :272).
- BAD: `load_bearing` rows and their served sentence assert an analysis that was not done; the empty `derived_from_pramana_ids` hides that the provenance link was never built.

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** `chart_id: str = ctx.config["chart_id"]` (:194) is a `uuid.UUID` on the real path and is a SQL parameter and an element of insert tuples (`_overlay_row` returns it as the first tuple element; psycopg adapts it); the `json.dumps` calls are `json.dumps([])` (:177). Origin ids are `str()`-ed (:247, :284, :305, :325). **Not exposed.**
- **Outcome-leakage guard:** all overlay rows carry `leakage_status = 'not_assessed'` by design; the multipliers they apply are trained on retrospective matches (CF-L5-03); nothing in this writer can detect or prevent a learned personal multiplier from re-entering prospective generation (T2 section 6.6) — the overlays are GATED (unread) today, which is the only thing that keeps them out of generation.
- **People-entered data (N-46) / LEL data contract:** all five tables are regenerable derived outputs (INV). No people-entered data is read or written.

## 3 · Disposition

DISPOSITION: qualify

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/data/mi_adhilepa.json

EVIDENCE_EXTRA: this brief sections 0-4; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts2.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/rollup_saved_L5.json; 00_ARCHITECTURE/briefs/suvarna/layers/census/census_L5.json

**qualify (Q)** — the expansion is mechanical and idempotent, but the asset materialises 112k rows nothing reads, labels a prior-weight ranking as sensitivity, and is 100% dangling. Qualify with a retire-the-expansion option for SS (Q-L5-08): keep the family table, derive per-object weights at serve time if ever served, and keep or remove `mimamsa_load_bearing` depending on whether a real sensitivity method is built.

Approver under Track A brief section 10: **Strategic Suvarṇa (R5; any retirement of the overlay tables is R5)**. Risk class: **high (largest row count in L5; label removal; possible retirement)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023). No disposition is applied by this brief.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Stop calling a prior ranking a sensitivity (R)

- **Answers:** adh-N1; CF-L5-04, CF-L5-10; Q-L5-09
- **Change:** remove the sentence "Removing this signal would materially alter the reading" from `mi_darshana` for `load_bearing` units; rename `role` to a rank-position vocabulary or NULL it until a real ablation exists; do not store a family id in a `signal_id` column
- **Files / declaration / migration:** `mi_adhilepa.py:336-358`; `mi_darshana.py:395-412`; `query_load_bearing.ts` description
- **Failing-first test and mutation:** failing-first: no served unit contains the counterfactual sentence while `role` derives from priors; golden-value test for the template; mutation: restore the sentence -> FAIL
- **Output change:** yes: 4 stored rows + 4 served insight units change text/labels -> SS (R5)
- **Blast radius:** mi_darshana load_bearing units, query_load_bearing
- **Rebuild:** needs production rebuild of mi_adhilepa + mi_darshana (REVIEW)
- **Gate it moves:** Narr, Earn
- **Fix class:** writer code (two assets) + served description; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-26

### FD-2 · Decide whether to materialise the overlays at all (R)

- **Answers:** adh-N2, N3, N8; Q-L5-08
- **Change:** option A (recommended): stop writing the four per-object tables; keep `mimamsa_multipliers` and apply at serve time if a consumer appears. Option B: keep, but (1) give the convergence read a total ORDER BY and no cap, (2) fix `origin_asset_id`, (3) add the referential detector of CF-L5-02 so dangling overlays read as stale. The existing rows are derived and regenerable; deleting them is a Track B rebuild step, not a data-loss question
- **Files / declaration / migration:** `mi_adhilepa.py:191-330`; registry `count_sql`, seed target table (live registry says `mimamsa_load_bearing`, seed says `mimamsa_signal_adjustment`)
- **Failing-first test and mutation:** failing-first (B): ids resolve to live objects or the row is marked stale; mutation: change an MSR id -> detector reports
- **Output change:** A: 112,266 rows retired (R5); B: none beyond the fixes
- **Blast radius:** no served reader; mi_seva existence check names `mimamsa_signal_adjustment`
- **Rebuild:** needs production rebuild or truncate (REVIEW; the registry carries `clear_tables`)
- **Gate it moves:** Dens, Build.completion, Complete
- **Fix class:** data (retirement) or writer code; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-27

### FD-3 · `applies_to_reading` means learned

- **Answers:** adh-N4
- **Change:** set true only when the family multiplier is `promoted` (after mi_gunanaka FD-1); otherwise false/NULL
- **Files / declaration / migration:** `mi_adhilepa.py:164`
- **Failing-first test and mutation:** failing-first: prior-only multiplier -> `applies_to_reading` false; mutation: restore -> FAIL
- **Output change:** yes: 174 + more rows flip -> SS (R5)
- **Blast radius:** none served
- **Rebuild:** needs rebuild (REVIEW)
- **Gate it moves:** Earn
- **Fix class:** writer code; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-28

### FD-4 · Provenance, naming and reads

- **Answers:** adh-N6, N7, N8; CF-L5-07
- **Change:** fill `derived_from_pramana_ids` from the family's evidence rows or drop the column; use real asset ids in `origin_asset_id`; add a total ORDER BY; declare `chart_facts` producers honestly (the L1 assets that produce the mapped categories)
- **Files / declaration / migration:** `mi_adhilepa.py:177,284,297`; registry migration
- **Failing-first test and mutation:** failing-first: `origin_asset_id` is a registry asset id; deterministic row set; mutation: remove ORDER BY -> row set varies
- **Output change:** origin_asset_id text changes on 61,523 rows (derived) -> SS if the tables are kept
- **Blast radius:** none
- **Rebuild:** needs rebuild if kept
- **Gate it moves:** Ldgr, Build.dag
- **Fix class:** writer code + registry; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-29

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-01** — overlays are from the 2026-08-13 build
- **CF-L5-02** — adh-N2: 100% dangling
- **CF-L5-03** — multipliers trained on retrospective matches
- **CF-L5-04** — role / sensitivity / applies_to_reading
- **CF-L5-07** — adh-N8
- **CF-L5-10** — served sentence
- **CF-L5-11** — no canonical receipt
- **CF-L5-12** — Build.history cascade
- **CF-L5-13** — seed target table differs from live

## 5 · Semantic fingerprint contract (for E5.5)

Chart-scoped. Overlay tables: stable columns `origin_layer, origin_asset_id, origin_id, weight_id, multiplier, raw_multiplier, applied_bound, evidence_n, leakage_status, applies_to_reading`; exclude `created_at`; the row set depends on the live MSR / fact / convergence / anchor generations, so pin them. `mimamsa_load_bearing`: all columns.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the family-to-object mapping helpers (`_signal_family_key`, `_fact_family_key`) as classification code, the `not_assessed` honesty, the per-chart delete-then-insert.
- **Carriage check chosen (T4 §4.1; one only):** D3 (independent re-derivation): recompute each overlay's multiplier from `mimamsa_multipliers` and the family key from the signal's class fields with an independent mapping; sample by family.
- **Opportunities (never blocking):** if a real sensitivity method is wanted, drop-one-signal re-scoring against the adjudicated matches is the honest definition of `load_bearing`; it needs chronology-clean matches first.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-03** — Authorise the production rebuild of the L5 chain (after the L3/L4 rebuild lands) so that main's corrected code replaces the 2026-08-13 rows (stale labels served today: 31 `empirical` insight units, 51 "Blind retrodiction" statements, `base_rate = 0.1` x57, 7 grammar rows at 0.0 propensity); and mark the old rows stale before the rebuild. Order: jivanaghatana -> bhavisya -> pramana -> (gunanaka, pariksha) -> sambandha -> adhilepa -> darshana. *Recommendation:* Yes, as one REVIEW-gated Track B wave after Q-L5-01/02 are ruled (otherwise the rebuild re-creates the retrospective calibration under cleaner labels). (R)
- **Q-L5-04** — Constants: ratify as named documented approximations (in `brahma_formula_constants`) the engineering thresholds and weights (verdict 0.65 / 0.35, composite weights, bin width 0.1, n >= 5, k = 5, cap 3, n >= 3 promotion, discovery 3 / 0.15 / 20) — and drop (NULL) the invented priors and missing-term defaults (mi_sambandha channel priors and the 0.5 default, +-0.1 bands, 0.5 / 1.0 fallbacks)? *Recommendation:* Thresholds and weights: ratify as named constants (ask the L3 Q-L3-01 precedent: option 1). Invented priors, bands and defaults: option 2, NULL / `unsourced`. (R)
- **Q-L5-08** — Overlay expansion: 112,266 per-signal / fact / convergence / anchor overlay rows exist, are GATED (no reader) and are 100% dangling. Keep materialising them or stop and keep only the family table? *Recommendation:* Stop (option A); per-object weights, if ever served, are a serve-time join. Existing rows are derived and regenerable. (R)
- **Q-L5-09** — Remove the counterfactual sentence "Removing this signal would materially alter the reading" and rename `role` (rank position of the classical prior) until a real ablation exists? *Recommendation:* Yes. (R)
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
