---
asset_id: mi_gunanaka
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
disposition_proposal_approver: "Strategic Suvarṇa (R5)"
risk_class: "high (output change: promotions, labels, applied multipliers on 2 families and every overlay built on them)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-22, TI-L5-23, TI-L5-24, TI-L5-25]
ledger_gap_ids: ["mi_gunanaka-Build.completion", "mi_gunanaka-Earn.build_record", "mi_gunanaka-Cost.baseline", "mi_gunanaka-Complete.depth", "mi_gunanaka-Build.history", "mi_gunanaka-Build.dep_liveness", "mi_gunanaka-Carr.detector", "new: gun-N1", "new: gun-N2", "new: gun-N3", "new: gun-N4", "new: gun-N5", "new: gun-N6", "new: gun-N7", "new: gun-N8"]
---

# mi_gunanaka — Learned-weight register: hierarchical-shrinkage family multipliers and proposed calibration snapshots

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_gunanaka.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

LIGHT writer (`run(ctx)`, :97). Reads every `mimamsa_calibration` row of the chart left-joined to its prediction's `driving_signals` (:105-125) and the active, non-control `mimamsa_signal_families` (:128-134). For each family it averages the composite scores of all (calibration row x driving signal of that family) pairs (:151-160) and shrinks that mean toward a family and a global mean with weights n and k = 5 (`_hierarchical_posterior`, :62-79; k and a 3x divergence cap read from `brahma_formula_constants`, defaults :36-37), converts `posterior * 2.0` to a multiplier (:201), caps divergence (:203-208) and clamps to [0.1, 3.0]. Families with no evidence get their classical prior (`prior_only`, :251-282). It replaces `mimamsa_multipliers` per chart (:305) and appends one `mimamsa_calibration_snapshot` (`snap_<chart8>_<unix time>`, `two_key_complete = false`, `publication_status = 'proposed'`, :357-393) — the ratified F-188 accretion exception. Output feeds `mi_adhilepa` (overlays), `mi_darshana` and `query_calibration`.

**Canonical chart state (read-only, 2026-10-03).** **9 multiplier rows + 4 snapshots = 13.** Two families are `promoted`: `fam_graha_natal` (n_observations 271, applied 0.9924) and `fam_transit` (n_observations 14, applied 0.9643); seven are `prior_only` with n = 0 and applied = the classical prior (`mult`). The 4 snapshots are all `proposed`, `two_key_complete = false` (`snap`). **Where n comes from (read-only recomputation, `facts` q 'gun_n'):** the 271 = 271 (calibration row x driving-signal) pairs from 57 matches, 13 predictions and 24 events; the 14 for `fam_transit` = 7 matches x 2 signals from **2 predictions**. n counts pairs, not independent observations. Only 2 families (graha_natal, transit) ever appear in the driving signals, so only 2 can earn evidence. The evidence admitted includes the 25 UNRESOLVED matches (only `leaked` rows are excluded, :144-149; 0 rows are `leaked`).

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / per_chart / postgres_table | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2941` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_gunanaka.py:87` `@register("mi_gunanaka")`; registry `has_writer` = t | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_multipliers`; count_sql tables: `mimamsa_multipliers`, `mimamsa_calibration_snapshot` | registry / census |
| count_sql (live) | `SELECT (SELECT COUNT(*) FROM mimamsa_multipliers WHERE chart_id = $1) + (SELECT COUNT(*) FROM mimamsa_calibration_snapshot WHERE chart_id = $1) AS count` | registry |
| live rows (canonical chart) / floor | 13 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / False / 10800s | registry |
| registry build state (canonical chart) | throughput `error`, rows_written 9, last_built_at 2026-08-21T02:36:53Z; recent canonical runs: complete 2026-08-13; complete 2026-08-07; complete 2026-08-07; complete 2026-08-07 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `mi_pramana`, `mi_kula`, `bg_formula_constants` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | `mi_adhilepa`, `mi_darshana` (registry); census transitive blocking radius 3 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Declared: `mi_pramana`, `mi_kula`, `bg_formula_constants`. Actual: `mimamsa_calibration` (`mi_pramana`), `mimamsa_predictions` (`mi_bhavisya`, undeclared), `mimamsa_signal_families` (`mi_kula`), `brahma_formula_constants`. `mi_bhavisya` is a real input (driving signals and family ids) with no edge. | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | Served: `query_calibration.ts:185` (multipliers; `promoted_only` filter on `gate_passed`), `compute_spine_bundle.ts:128-157`, L4 `query_predictive_anchors.ts:199` (comment only: reads n_observations from L5), `chartContextStaleness.ts`; writers: `mi_adhilepa.py:114` (`_load_multipliers`). The snapshot table is read/written by the learning API `platform/src/app/api/clients/[id]/learning/route.ts:247` (`mimamsa_snapshot_cosign`, the native co-sign path). Census reach: 11/19 columns selected by 1 module; dark `held_out_validity`, `confidence_high`, `neg_control_clear`, `audit_trail`, `domain`. | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `tests/test_mi_gunanaka.py` (2 tests), `tests/test_mi_gunanaka_context_stale_filter.py`, `tests/test_f188_mi_gunanaka_count_sql.py`, `writers/tests/test_mi_adhilepa_leakage.py` (the gunanaka half: `not_assessed` rows are admitted, `leaked` excluded; source-text) | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | no receipt, no freshness row for the canonical chart; digest spec present (reviewed 2026-09-09T17:29Z); throughput `error` 2026-08-21 (BLOCKED on `mi_pramana`), rows_written 9 vs count_sql 13; last writer execution complete 2026-08-13T01:16:30Z | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (60) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): mimamsa_multipliers (mi_gunanaka.py:300) |
| Build | Build.target † | PASS | target_table=mimamsa_multipliers |
| Build | Build.dag † | PASS | 3 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | FAIL | build record state='error' is not a completed build (rows_written=9, live=13, chart 482012f1) — see Build.history; target_table mimamsa_multipliers alone: 18 row(s), whole table — context, not the compared figure |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=13) |
| Complete (information) | Complete.depth | PARTIAL | 18 rows, 20 cols; fully populated 19; NEVER populated ['domain'] |
| Dens | Dens.served † | PASS | 1 module(s): query_calibration.ts; declaring density_contract: 1 |
| Build | Build.history | FAIL | most recent run error (2026-08-21); 28 error(s), 9 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-08-21): BLOCKED: upstream dependency(ies) mi_pramana did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | FAIL | 2/3 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_pramana (error, chart 482012f1)'] — a DEP-ASSERT trap if no writer can light them |
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
| mi_gunanaka-Build.completion | Build.completion | stale | measured: build record state='error' is not a completed build (rows_written=9, live=13, chart 482012f1) — see Build.history; target_table mimamsa_m... |
| mi_gunanaka-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_gunanaka-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_gunanaka-Complete.depth | Complete.depth | information | measured: 18 rows, 20 cols; fully populated 19; NEVER populated ['domain'] / required: the Complete gate's claim |
| mi_gunanaka-Build.history | Build.history | history | measured: most recent run error (2026-08-21); 28 error(s), 9 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-0... |
| mi_gunanaka-Build.dep_liveness | Build.dep_liveness | stale | measured: 2/3 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_pramana (error, chart 482012f1)'] — a DEP-ASSERT trap if no w... |
| mi_gunanaka-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: gun-N1 | Earn (promotion / gate) | real (central) | `held_out_validity = "pass"` (:226), `gate_passed = True` (:228), `neg_control_clear = True` (:230, :273) are literals written on every evidence row, and on the prior-only rows `neg_control_clear = True` too. `neg_control_clear` asserts the family survived a negative-control battery; no such harness exists (`mi_pariksha` writes `not_implemented` x4) — 9/9 rows read `t`. `confidence_high = n >= 5` (:229) and `promotion_status = promoted if n >= 3` (:212) are size tests on a count that is pseudo-replicated (gun-N2). `query_calibration` serves the `promoted_only` filter on `gate_passed` |
| new: gun-N2 | Earn (n) | real (central) | `n_observations` counts (match x driving signal) pairs: 271 from 13 predictions / 24 events; 14 from 2 predictions. One match contributes up to 5 "observations" for the same family and the same match score; the effective sample is the number of distinct predictions or events (13 / 2), not 271 / 14. `promoted` on n = 14 from two predictions is a size test on duplicates |
| new: gun-N3 | Earn (what is learned) | real | the "likelihood" averaged is the mean composite match score (timing + string-equal domain + two constants, see `mi_pramana`), not the probability that the family's claims came true; and 53/53 of its source matches are retrospective (CF-L5-03). The learned multiplier therefore measures how well dates and domain strings overlapped, and feeds back as a personal weight (T2 section 6.6 forbids a derived personal multiplier re-entering the prospective generation it is evaluated on; see `mi_adhilepa`, `mi_seva` for where it would apply) |
| new: gun-N4 | Null / defaults | real | `score = ... or 0.5` (:157: a genuine 0.0 composite becomes 0.5), `global_likelihood = 0.5` when no evidence (:168), `fam = families.get(family_id, {"prior_weight": 1.0})` and `float(fam.get("prior_weight") or 1.0)` (:190, :256: an unknown family or a zero prior becomes 1.0 — the neutral multiplier invented for a missing term), `evidence_factor = prior / 2.0` on prior-only rows (:262) |
| new: gun-N5 | kill switch | real | `kill_switch_state = "suspended_divergence"` (:207) is set when the 3x divergence cap trips, yet the row still carries a capped `applied_multiplier`, and `mi_adhilepa` writes its overlays regardless and only sets `applies_to_reading` false for a non-`active` state (:164): the label says suspended while the number is capped rather than withheld; no row currently trips it (max divergence 0.0978) |
| new: gun-N6 | snapshot (F-188) | information | the snapshot is accretion by ratified exception (docstring :342-356); `_publish_snapshot` swallows any failure and logs a warning (:393), so a failed publish returns a successful build (Earn: the claim "snapshot published" has no failing path; before SV-6 this hid a `UUID[:8]` crash on every real-path build). `snap_<chart8>_<unix>` ids make ids non-reproducible; 4 `proposed` rows exist, none co-signed. The registry `count_sql` counts both tables (F-188 fix), so `rows_written` 9 never equals `live` 13 (census Build.completion FAIL: a cascade-shaped cell) |
| new: gun-N7 | Build.dag | real | `mi_bhavisya` read with no edge; `bg_formula_constants` read through `brahma_formula_constants` (CF-L5-07) |
| new: gun-N8 | vocab | real | `promotion_status` (promoted / earning / prior_only), `held_out_validity` (pass / insufficient_n), `kill_switch_state`, and the family table's `calibration_status` (prior_only) are four status vocabularies for one idea (CF-L5-06). The `domain` column is NULL on 9/9 (`compute_spine_bundle.ts:128` notes it) |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| `held_out_validity = pass` | the multiplier was validated on held-out data | literal (:226) on every evidence row | **constant**; no held-out evaluation exists |
| `gate_passed = true` | the family passed the promotion gate | literal True (:228) for evidence rows | **constant**; the gate is `n >= 3` pairs |
| `neg_control_clear = true` | the family beat the negative controls | literal True (:230, :273), including prior-only rows | **constant, and contradicted**: the controls are `not_implemented` (`mi_pariksha.py:630`) |
| `confidence_high` | high confidence in the multiplier | `n >= 5` (:229) | proxy of a pair count |
| `promotion_status = promoted` | learned beyond the prior | `n >= 3` (:212) | proxy; n = pairs (gun-N2) |
| `n_observations` | number of independent outcomes | count of match x signal pairs | **overstated** (271 vs 13 predictions) |
| `applied_multiplier` on prior-only rows | the classical prior | prior copied through (:256-282) | earned as a restatement of `mi_kula`'s prior; `evidence_factor = prior/2` is a unit conversion, not evidence |
| snapshot `proposed`, `two_key_complete = false` | not yet co-signed | literals (:380-381) | **earned**: honest about the missing second key |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD: prior-only rows are written as prior-only with n = 0 (no learned value is claimed); snapshots are proposed, not published; leakage `not_assessed` rows are explicitly admitted with a logged count instead of a filter that can never pass (§N.8 comment :135-141).
- BAD: the status columns are written as measured (gun-N1) where `NULL`/`not_assessed` would be honest; `or 0.5` / `or 1.0` defaults (gun-N4).

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** `chart_id: str = ctx.config["chart_id"]` (:100) is a `uuid.UUID` on the real path. It is a SQL parameter everywhere except the snapshot id, where `chart_id[:8]` raised `'UUID' object is not subscriptable` and was **swallowed** by the except at :388-393 (SV-6, fixed on main: `str(chart_id)[:8]`, :365). This is the one mi_* instance of the ga_*/bo_* class and it is already fixed on main; the deployed snapshots (`snap_482012f1_…`) were written, so the 08-13 build did not hit it. The `json.dumps` at :233 and :276 carry dicts of floats and strings. A regression test for a UUID `chart_id` through `_publish_snapshot` was not found (the existing test file has 2 tests).
- **Outcome-leakage guard:** the only leakage test is `leakage_status == 'leaked'` -> exclude (:144-149), and no writer in L5 ever writes `leaked` (0 rows); `not_assessed` is admitted (correctly, per the §N.8 comment). Result: the learned weights are trained on matches no one has checked for leakage, and 53/53 are retrospective (CF-L5-03).
- **People-entered data (N-46) / LEL data contract:** `mimamsa_multipliers` is regenerable. `mimamsa_calibration_snapshot` is a **mixed** table (INV: human cosign state): this writer only inserts (never updates/deletes), and the `acharya_pratinidhi_key` / `two_key_complete` columns are the native's. Nothing proposed touches a snapshot row. The cosign table `mimamsa_snapshot_cosign` (0 rows) belongs to no asset (TG-L5-020).

## 3 · Disposition

DISPOSITION: qualify

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/data/mi_gunanaka.json

EVIDENCE_EXTRA: this brief sections 0-4; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts2.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/rollup_saved_L5.json; 00_ARCHITECTURE/briefs/suvarna/layers/census/census_L5.json

**qualify (Q)** — the shrinkage machinery is sound and properly shrinks to the prior at n = 0 (which is the right STRUCTURAL-mode behaviour), but it promotes and labels families on pseudo-replicated retrospective scores and writes three status literals as measurements. Qualify = count independent outcomes, stop writing constants, and withhold promotion until the chronology gate yields real evidence.

Approver under Track A brief section 10: **Strategic Suvarṇa (R5)**. Risk class: **high (output change: promotions, labels, applied multipliers on 2 families and every overlay built on them)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023). No disposition is applied by this brief.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Replace the status literals by detectors or NULL (R)

- **Answers:** gun-N1, gun-N5; CF-L5-04; Q-L5-05
- **Change:** `held_out_validity`, `gate_passed`, `confidence_high`, `neg_control_clear` become: NULL / `not_assessed` until a real check exists; `gate_passed` true only if the evidence rows are chronology-clean (mi_pramana FD-1) and n counts distinct predictions >= the ratified minimum; `neg_control_clear` NULL while the harness is `not_implemented`; a tripped divergence cap withholds the learned value (applied = prior) rather than labelling a capped number `suspended`
- **Files / declaration / migration:** `mi_gunanaka.py:203-232,251-282`; additive nullable column types if the NOT NULL columns block NULL (check `mimamsa_multipliers` DDL, migration 349)
- **Failing-first test and mutation:** failing-first: no harness -> `neg_control_clear` IS NULL; promotion needs >= m distinct predictions; mutation: restore `True` -> FAIL. Golden-value tests (CF-L5-04)
- **Output change:** yes: 9 rows' flags and the 2 promotions change -> SS (R5)
- **Blast radius:** mi_adhilepa (applies only `active`), mi_darshana, query_calibration `promoted_only`
- **Rebuild:** needs production rebuild (REVIEW)
- **Gate it moves:** Earn, Null
- **Fix class:** data (output change) + writer code (+ possibly a migration if columns are NOT NULL booleans); **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-22

### FD-2 · Count independent observations (R)

- **Answers:** gun-N2, gun-N3
- **Change:** aggregate per distinct (prediction, event) pair once per family (not per driving signal), report `n_observations` = distinct predictions and add `n_pairs` for the old count; use the adjudicated outcome (CONFIRMED / PARTIAL / REFUTED) rather than the match composite as the likelihood once Q-L5-01 yields chronology-clean rows; exclude UNRESOLVED
- **Files / declaration / migration:** `mi_gunanaka.py:107-170`
- **Failing-first test and mutation:** failing-first: two signals of one family on one match count once; UNRESOLVED excluded; mutation: restore per-signal appends -> n changes back
- **Output change:** yes: n 271 -> at most 13, 14 -> at most 2 -> SS (R5)
- **Blast radius:** mi_adhilepa, query_calibration
- **Rebuild:** needs production rebuild (REVIEW)
- **Gate it moves:** Earn
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-23

### FD-3 · No invented neutral values

- **Answers:** gun-N4; CF-L5-05
- **Change:** `composite_score` NULL stays NULL (skip the row, do not use 0.5); unknown family -> skip and count, not prior 1.0; `global_likelihood` None when no evidence
- **Files / declaration / migration:** `mi_gunanaka.py:157,168,190,256`
- **Failing-first test and mutation:** failing-first: a 0.0 composite counts as 0.0; an unknown family is skipped; mutation: restore `or` -> FAIL
- **Output change:** none on current data
- **Blast radius:** this asset
- **Rebuild:** none unless defaults fired
- **Gate it moves:** Null
- **Fix class:** writer code; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-24

### FD-4 · A failed snapshot publish fails the step; test the UUID path

- **Answers:** gun-N6; UUID check
- **Change:** re-raise (or return a non-success note the orchestrator reads) when the snapshot insert fails; add a regression test passing a real `uuid.UUID` through `_publish_snapshot`
- **Files / declaration / migration:** `mi_gunanaka.py:357-393`; `tests/test_mi_gunanaka.py`
- **Failing-first test and mutation:** failing-first: a UUID chart id publishes `snap_<8 hex>_…`; a forced insert failure fails the build; mutation: restore the swallow -> FAIL
- **Output change:** none
- **Blast radius:** this asset
- **Rebuild:** none
- **Gate it moves:** Earn (build record)
- **Fix class:** writer code + test; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-25

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-01** — multipliers on disk predate nothing in this writer's code; they are stale only through their inputs
- **CF-L5-03** — trained on retrospective matches
- **CF-L5-04** — three status literals + n
- **CF-L5-05** — k = 5, cap = 3, n >= 3 / 5 are engineering constants to be named and ratified
- **CF-L5-06** — four status vocabularies
- **CF-L5-07** — gun-N7
- **CF-L5-11** — no canonical receipt
- **CF-L5-12** — rows_written 9 vs live 13: cascade-shaped Build.completion

## 5 · Semantic fingerprint contract (for E5.5)

Chart-scoped. Multipliers: stable columns `weight_id, target_ref, n_observations, raw_multiplier, applied_multiplier, promotion_status, kill_switch_state, audit_trail`; deterministic given calibration rows and constants. Snapshots: append-only, `snapshot_id` embeds `time.time()` — exclude `snapshot_id` and `snapshot_at`, hash `cells_jsonb` instead.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the hierarchical-shrinkage form with n = 0 returning the prior, the divergence cap and clamp, prior-only rows for families without evidence, the proposed-then-cosigned snapshot protocol (F-188).
- **Carriage check chosen (T4 §4.1; one only):** D3 (independent re-derivation): recompute posterior and multiplier for each family from the stored calibration rows and the constants with a second implementation (the function is pure: `_hierarchical_posterior`).
- **Opportunities (never blocking):** surface the effective sample size (distinct predictions) next to n so that consumers cannot read pairs as outcomes; let the co-signed snapshot, not the live multiplier, be the only thing `mi_adhilepa` applies.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-01** — Chronology gate: may a prediction/event match enter calibration (`mimamsa_calibration`, `mimamsa_reliability`, learned multipliers, the activation-gate sample) only if the event's `recorded_at` and `event_date` are on or after the prediction's `emitted_at`, with earlier matches kept as a separately labelled retrodiction class? (53 of 53 resolvable matches today pre-date emission.) *Recommendation:* Yes. On the canonical chart this takes calibration rows 57 -> 0 and bins 6 -> 0, which is the honest STRUCTURAL state; real values then fill in as prospective outcomes accrue. (R)
- **Q-L5-04** — Constants: ratify as named documented approximations (in `brahma_formula_constants`) the engineering thresholds and weights (verdict 0.65 / 0.35, composite weights, bin width 0.1, n >= 5, k = 5, cap 3, n >= 3 promotion, discovery 3 / 0.15 / 20) — and drop (NULL) the invented priors and missing-term defaults (mi_sambandha channel priors and the 0.5 default, +-0.1 bands, 0.5 / 1.0 fallbacks)? *Recommendation:* Thresholds and weights: ratify as named constants (ask the L3 Q-L3-01 precedent: option 1). Invented priors, bands and defaults: option 2, NULL / `unsourced`. (R)
- **Q-L5-05** — Status flags: replace the constant / proxy flags (`admissible_clean`, `shaped_predictor`, `held_out_validity`, `gate_passed`, `confidence_high`, `neg_control_clear`, `leakage_status = clean`, `skill_score` on underpowered rows) by detectors or NULL / `not_assessed`; allow the DDL changes this needs (nullable columns, additive basis columns)? *Recommendation:* Yes; unverified admissibility stays calibration-eligible but labelled `unverified_inputs`. (R)
- **Q-L5-08** — Overlay expansion: 112,266 per-signal / fact / convergence / anchor overlay rows exist, are GATED (no reader) and are 100% dangling. Keep materialising them or stop and keep only the family table? *Recommendation:* Stop (option A); per-object weights, if ever served, are a serve-time join. Existing rows are derived and regenerable. (R)
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
- **Q-L5-20** — Tier vocabulary (TG-L5-014): adopt `structural / prior_only / assignment_only / empirical` (the vocabulary `mi_darshana` already stores with a `grade_basis`) as the layer vocabulary, with a named detector for each tier and one meaning of "empirical" (chronology-clean, adjudicated, independent, n >= ratified minimum)? *Recommendation:* Yes. (R)
