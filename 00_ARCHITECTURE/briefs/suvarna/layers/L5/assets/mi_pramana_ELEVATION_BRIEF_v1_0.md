---
asset_id: mi_pramana
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
disposition: "qualify (Q)"
disposition_proposal_approver: "Strategic Suvarṇa (R5: verdicts and labels change)"
risk_class: "high (output change; rebuild; consumed by the activation gate and four writers)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-17, TI-L5-18, TI-L5-19, TI-L5-20, TI-L5-21]
ledger_gap_ids: ["mi_pramana-Build.completion", "mi_pramana-Earn.build_record", "mi_pramana-Cost.baseline", "mi_pramana-Complete.depth", "mi_pramana-Build.history", "mi_pramana-Build.dep_liveness", "mi_pramana-Carr.detector", "new: pram-N1", "new: pram-N2", "new: pram-N3", "new: pram-N4", "new: pram-N5", "new: pram-N6", "new: pram-N7", "new: pram-N8", "new: pram-N9", "new: pram-N10", "new: pram-N12", "new: pram-N11"]
---

# mi_pramana — Prediction-event matcher and adjudication: the calibration scorecard and reliability curve

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_pramana.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

Matches every prediction (`mimamsa_predictions`, `chart_context_stale_at IS NULL`, :330) to every admissible, non-held-out event (`mimamsa_event_provenance`, :339) whose `event_date` falls inside the prediction's `observation_window` (:352-365) — a date-overlap join with no domain condition. Each pair becomes a `mimamsa_calibration` row: four dimension scores (timing :122, magnitude :144, domain :158, falsifier :162), a fifth (manifestation) held at 0.5 and excluded from the composite (:212-214), a weighted `composite_score` (weights from `brahma_formula_constants`, default `_DEFAULT_WEIGHTS` :60), a verdict by `_verdict_v2` (:221-246: REFUTED if falsifier < 0.1; UNRESOLVED if the window has not passed; CONFIRMED if score >= 0.65; PARTIAL if >= 0.35; else REFUTED), and a Brier pair. The reliability substep bins `composite_score` by 0.1 and publishes `observed_rate = share CONFIRMED`, `brier_score`, `n`, `held_out_validity` and `evidence_grade` per bin into `mimamsa_reliability`. These two tables are the calibration surface that `query_calibration`, `query_insights`, `mi_gunanaka`, `mi_pariksha`, `mi_sambandha` and the Paripraśna activation gate read.

**Canonical chart state (read-only, 2026-10-03).** **57 calibration rows = 13 predictions x 24 events; 6 reliability bins (n = 4, 13, 12, 18, 7, 3)** (`cal_summary`, `rel`). Verdicts: UNRESOLVED 25, PARTIAL 23, REFUTED 7, CONFIRMED 2 (the two CONFIRMED have composite 0.679 and 0.681). `score_magnitude` is exactly 0.5 and `score_falsifier` exactly 1.0 on 57/57; `manifestation_channel` NULL on 57/57; `n_for_stratum` = 1 and `evidence_admissibility` = 'clean' on 57/57; `leakage_status` = 'clean' on 57/57. **`base_rate = 0.1` on 57/57 and `brier_vs_null` populated on 57/57** although the code on main writes NULL for both (A-F-24, #1738): the deployed rows predate that fix, under the unchanged label `mi_pramana_v2.0` (F-12 of the layer instance; CF-L5-01). `ece`, `ci_low`, `ci_high`, `log_loss` are NULL on 6/6 bins (honest). **Chronology: all 53 prediction/event pairs that still join have `event_date` and `recorded_at` before the prediction's `emitted_at`** (53/53; `cal_retro`; 4 further rows point at event `5278d97c-…`, which no longer exists). Only 10 of the 53 pairs have equal prediction and event domain (`cal_domain_pair`); 13 of the 139 predictions appear at all.

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / per_chart / postgres_table | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2921` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_pramana.py:272` `@register("mi_pramana")`; heavy writer (`plan_substeps` :284: match, score, reliability); registry `has_writer` = t, `has_substeps` = t | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_calibration`; count_sql tables: `mimamsa_calibration`, `mimamsa_reliability` | registry / census |
| count_sql (live) | `SELECT (SELECT count(*) FROM mimamsa_calibration WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_reliability WHERE chart_id = $1) AS count` | registry |
| live rows (canonical chart) / floor | 63 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / True / 10800s | registry |
| registry build state (canonical chart) | throughput `error`, rows_written 63, last_built_at 2026-08-21T02:36:53Z; recent canonical runs: complete 2026-08-13; complete 2026-08-07; complete 2026-08-07; complete 2026-07-28 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `mi_bhavisya`, `mi_jivanaghatana`, `bg_ghatana`, `bg_formula_constants` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | `mi_darshana`, `mi_gunanaka`, `mi_pariksha`, `mi_sambandha` (registry); census transitive blocking radius 6 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Declared: `mi_bhavisya`, `mi_jivanaghatana`, `bg_ghatana`, `bg_formula_constants`. Actual: `mimamsa_predictions`, `mimamsa_event_provenance`, `mimamsa_manifestation_sets`, and `brahma_formula_constants` (:68-78). `bg_ghatana` is not read here. It reads neither `brahma_prospective_ledger` nor `brahma_mimamsa_prediction_ledger` (the issuance authorities, layer instance F-06). | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | Served: `query_calibration.ts:166-192` (`mimamsa_calibration_get`: verdict distribution, reliability curve, multipliers, QA), `query_insights.ts:239-250` (`calibration_summary.total_matches` = `COUNT(*)` of this table), `compute_spine_bundle.ts:215`; consumers of those: `pariprashna/confidence/activation_gate.ts` (sample size), `receipt/assemble.ts:423-461`. Writers: `mi_gunanaka.py:108`, `mi_pariksha.py` (ablation `mi_pariksha.py:377`, attribution :455, neg_control `mi_pariksha.py:606`, tail_only), `mi_sambandha.py:114`, `mi_darshana.py:206` (reliability). Census reach: 5/18 built columns selected by 2 modules; 13 dark including `base_rate`, `brier_vs_null`, `leakage_status`, `evidence_admissibility`, `n_for_stratum`. | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `writers/tests/test_b04_mi_honesty.py` (source-text), `tests/test_mi_pramana_context_stale_filter.py`, `L5_mimamsa/__tests__/query_calibration_context_stale.test.ts`, `query_calibration_qa_fail_count.test.ts`, `f27_calibration_domain_filter.test.ts`; no test of the verdict thresholds, of unresolved matches in the reliability denominator, or of match chronology | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | no receipt, no freshness row for the canonical chart; digest spec present (reviewed 2026-09-09T13:06Z); throughput `error` 2026-08-21 (BLOCKED on `mi_bhavisya`); last writer execution complete 2026-08-13T01:16:30Z; version label `mi_pramana_v2.0` on all 57 rows | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (59) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): mimamsa_calibration (mi_pramana.py:374), mimamsa_reliability (mi_pramana.py:490) |
| Build | Build.target † | PASS | target_table=mimamsa_calibration |
| Build | Build.dag † | PASS | 4 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | FAIL | build record state='error' is not a completed build (rows_written=63, live=63, chart 482012f1) — see Build.history; target_table mimamsa_calibration alone: 57 row(s), whole table — context, not the compared figure |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=63) |
| Complete (information) | Complete.depth | PARTIAL | 57 rows, 20 cols; fully populated 18; NEVER populated ['manifestation_channel', 'base_rate_adjusted_skill'] |
| Dens | Dens.served † | PASS | 2 module(s): query_calibration.ts, query_insights.ts; declaring density_contract: 2 |
| Build | Build.history | FAIL | most recent run error (2026-08-21); 27 error(s), 9 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-08-21): BLOCKED: upstream dependency(ies) mi_bhavisya did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | FAIL | 3/4 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_bhavisya (error, chart 482012f1)'] — a DEP-ASSERT trap if no writer can light them |
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
| mi_pramana-Build.completion | Build.completion | stale | measured: build record state='error' is not a completed build (rows_written=63, live=63, chart 482012f1) — see Build.history; target_table mimamsa_... |
| mi_pramana-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_pramana-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_pramana-Complete.depth | Complete.depth | information | measured: 57 rows, 20 cols; fully populated 18; NEVER populated ['manifestation_channel', 'base_rate_adjusted_skill'] / required: the Complete gate... |
| mi_pramana-Build.history | Build.history | history | measured: most recent run error (2026-08-21); 27 error(s), 9 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-0... |
| mi_pramana-Build.dep_liveness | Build.dep_liveness | stale | measured: 3/4 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_bhavisya (error, chart 482012f1)'] — a DEP-ASSERT trap if no ... |
| mi_pramana-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: pram-N1 | Earn (leakage / chronology) | real (central; SS question R) | the calibration rows are retrodiction scored as prediction: 53/53 matched events were known (event_date and recorded_at) before the prediction was emitted. `leakage_status = clean` (:422) is `admissible_clean AND NOT held_out`, an admissibility flag, not a comparison of event time with emission time. T1 section 7.2-7.3 and T2 section 3.1 ("retrospective fit as prediction" must not be claimed) are not met; no detector in L5 would read false (CF-L5-03, Q-L5-01). By design L5 is STRUCTURAL; this finding is about rows that carry `empirical`/`pass`/`clean` labels while being retrospective |
| new: pram-N2 | Earn (circular verdict) | real | `observed_rate` of a bin is the share of rows whose verdict is `CONFIRMED`, and `CONFIRMED` is defined as `composite_score >= 0.65` (:241) over the same score the rows are binned by (:523-528). The four bins lying entirely below 0.65 have observed_rate 0 by construction; the one bin that straddles 0.65 ([0.6,0.7), n = 7) holds the only 2 CONFIRMED rows (0.2857); the bin above ([0.8,0.9), n = 3) is all UNRESOLVED and reads 0. The curve cannot disagree with its own x-axis; it is not a reliability curve of a stated forecast probability. The predictions' own stated probability (`confidence_band`) is never used: `pred_prob = pred.get("posterior") or pred.get("confidence_high") or composite` (:436) and `mimamsa_predictions` has neither column, so the Brier term scores the match score against itself |
| new: pram-N3 | denominator | real | UNRESOLVED rows (25 of 57, window not yet passed) enter the reliability bins as non-hits (`verdict == "CONFIRMED"` False, :528): e.g. bin [0.8,0.9) has n=3, observed 0, all three still unresolvable. A pending adjudication is counted as a miss (T1 section 14: "correct denominators"). The match join also drops every prediction with no event in its window (126 of 139): non-events are not counted either way (selective denominators) |
| new: pram-N4 | Earn (held_out_validity / evidence_grade) | real | `held_out_validity = "pass"` and `evidence_grade = "empirical"` whenever a bin holds n >= 5 (:541-542): a size test, not a check that the rows are frozen, independent or held out. 4 of 6 bins read `pass`/`empirical`: three of them with observed rate 0 and one with 0.286. Same finding as layer-instance F-05 |
| new: pram-N5 | constants / dimensions | real | two of four scored dimensions are constants: `score_magnitude` = 0.5 (the event magnitude is NULL on 63/63, :144-148 returns 0.5) and `score_falsifier` = 1.0 (no falsifier is evaluable: `magnitude_floor` reads a missing `event_magnitude`, `attestation_required` reads `admissible_clean`, which is always true, :162-210). They carry 22.2% + 16.7% of the default composite weight, so the composite is a function of timing and exact-string domain equality only; `_score_timing` returns 0.5 on any parse failure (:132-155) and `_score_domain` is string equality on vocabularies that do not match (pram-N6) |
| new: pram-N6 | vocab | real + SS question | prediction domains {transition, wealth, spirituality, character, career, relationship, health} vs event domains {career, education, spiritual, relationship, health, family, residential+travel, psychological, loss, creative, other, finance, travel}: `_score_domain` (:158) is `pred == event`; `wealth` never equals `finance`, `spirituality` never equals `spiritual`, `transition` and `character` have no counterpart (Q-L5-06) |
| new: pram-N7 | determinism | real | `_window_passed` and thus UNRESOLVED vs CONFIRMED/PARTIAL/REFUTED depend on `date.today()` at build time (:257-270): a rebuild a day later can change verdicts with no input change, and no `as_of` column records the clock. The fingerprint must pin it |
| new: pram-N8 | deployed-vs-code | stale | `base_rate = 0.1` x57 (invented default removed in code, A-F-24); `brier_vs_null` derived from it; label unchanged (`mi_pramana_v2.0`) — a behaviour change without a version bump (CF-L5-01) |
| new: pram-N9 | dark columns | information | `base_rate_adjusted_skill` and `manifestation_channel` never populated; `n_for_stratum` constant 1; `evidence_admissibility` constant "clean" (census Complete.depth; CF-L5-04) |
| new: pram-N10 | dangling | stale | 4 calibration rows reference an event id absent from `life_events` and `mimamsa_event_provenance` (CF-L5-02) |
| new: pram-N12 | integrity_check_sql pins the proxy flags | real (blocks the fixes) | the live `integrity_check_sql` of `mi_pramana` fails the asset unless every calibration row has `leakage_status = 'clean'` AND `evidence_admissibility = 'clean'`, `composite_verdict` in the four values (no FALSE_ALARM), `n_for_stratum >= 0`, `SUM(reliability.n) = COUNT(calibration)`, `held_out_validity = pass` and `evidence_grade = empirical` exactly when `n >= 5`, and `hit_rate_by_tier = observed_rate`. The check enshrines pram-N3 (unresolved rows inside the bins), pram-N4 (the size-test labels) and the constant flags; FD-1..FD-3 change the written values, so the integrity SQL must change in the same migration or the rebuilt asset rolls back (CF-L5-13) |
| new: pram-N11 | Build.dag | real | declared `bg_ghatana` unread; ledgers unread (CF-L5-07) |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| `composite_verdict` | the prediction was CONFIRMED / PARTIAL / REFUTED by the event | `_verdict_v2` thresholds 0.65 / 0.35 over a composite that is timing + string-equal domain (+ two constants) | **proxy**: a match-quality grade, not an adjudication; UNRESOLVED is honest; REFUTED can be reached by an event of another domain that merely falls in the window |
| `leakage_status = clean` | no outcome leakage into the prediction | `admissible_clean and not held_out` (:422) | **unearned**: true on 57/57 while 53/53 events pre-date emission |
| `held_out_validity = pass`, `evidence_grade = empirical` | the bin is validated on held-out, independent data | `n >= 5` (:541-542) | **proxy of bin size** (earned only as "n >= 5") |
| `observed_rate` | share of predictions in the bin that came true | share CONFIRMED among rows binned by the CONFIRMED-defining score | **circular + wrong denominator** (pram-N2, N3) |
| `base_rate`, `brier_vs_null` | climatology null and skill against it | deployed: literal 0.1; main: NULL | **deployed value invented**, code value honest (F-12) |
| `score_magnitude` 0.5, `score_falsifier` 1.0 | dimension scores | constants (missing magnitude; missing falsifier evaluation) | **constants wearing a score's clothes**; `score_manifestation` = 0.5 is at least excluded from the composite |
| `ece`, `ci_low`, `ci_high`, `log_loss` | — | NULL | **earned nulls** |
| `n_for_stratum` = 1, `evidence_admissibility` = clean | sample size / admissibility of the stratum | constants (:459-460) | dark, constant, and read by the activation gate's docblock as if real (activation_gate.ts:15) |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD: `base_rate`/`brier_vs_null` NULL in code (A-F-24) with the reason in the docstring; `ece` NULL with a stated reason (A-F-30); missing-table now raises (A7); the manifestation dimension was dropped from the composite rather than fabricated (JL-018).
- BAD: the same discipline stops at the dimensions: the 0.5 / 1.0 constants and the `or 0.5` timing fallback present a number where the truth is 'not measurable'.
- The activation gate downstream (`activation_gate.ts`, `gateOpen = sampleSize >= 30`) is fed `total_matches` = 57 = `COUNT(*) FROM mimamsa_calibration` (`query_insights.ts:239-250`): by code reading the 'empirically_calibrated' gate opens on 57 retrospective matches (25 unresolved, 13 distinct predictions). This is a consumer effect of pram-N1; the gate itself documents its 30 as a placeholder.

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** `self._chart_id = ctx.config["chart_id"]` (:285) is a `uuid.UUID` on the real path and is passed only as a SQL parameter (:331, :340, :380, :392, :491, :496) and into log text and f-strings; no `[:8]` slice, `json.dumps`, `canonical_json` or `stable_uuid` receives it. **Not exposed** (compare `mi_pariksha`, which `str()`-es it, and `mi_gunanaka`, whose `chart_id[:8]` crash was fixed by SV-6).
- **Outcome-leakage guard:** see pram-N1 and CF-L5-03. The only control is `held_out` (a hash) and the `chart_context_stale_at` filter. `mi_adhilepa`'s tests assert the label `not_assessed`; they do not detect leakage. The Paripraśna `calibration_leak_guard.ts` blocks calibration-shaped keys from served envelopes (collect-only) and cannot see that these rows are retrospective.
- **People-entered data (N-46) / LEL data contract:** Derived, regenerable tables (`mimamsa_calibration`, `mimamsa_reliability`): rebuilt freely under N-46. No people-entered data is written. Verdicts are NOT native adjudications (the native's adjudication path is `mimamsa_adjudication_log` via the learning API, which no L5 asset reads).

## 3 · Disposition

**qualify (Q)** — keep the matching/scoring machinery, but the headline labels (`clean`, `empirical`, `pass`, observed rate, base rate) are not earned and the calibration rows are not prospective. Qualify = restrict what these rows may claim to what the chronology and denominators support, and fix the denominators.

Approver under Track A brief section 10: **Strategic Suvarṇa (R5: verdicts and labels change)**. Risk class: **high (output change; rebuild; consumed by the activation gate and four writers)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Chronology gate in the match substep (R)

- **Answers:** pram-N1; CF-L5-03; Q-L5-01
- **Change:** a pair is a calibration match only if `event.recorded_at >= prediction.emitted_at` AND `event_date >= emitted_at::date`; pairs that fail are written, if at all, with `calibration_class = 'retrodiction'` and excluded from `mimamsa_reliability`, `mi_gunanaka` evidence and `total_matches`; requires `recorded_at` on the provenance row (mi_jivanaghatana FD-2) and a stable `emitted_at` (mi_bhavisya FD-1)
- **Files / declaration / migration:** `mi_pramana.py:352-365`, `:422`; additive column `calibration_class`; **`integrity_check_sql` (registry migration, same change: it requires `leakage_status = clean` and `SUM(reliability.n) = COUNT(calibration)`)**; digest spec re-review
- **Failing-first test and mutation:** failing-first: a fixture with an event recorded before emission yields zero calibration rows and one retrodiction row; mutation: remove the gate -> the fixture row enters calibration
- **Output change:** yes: on the canonical chart all 53 resolvable pairs leave calibration (57 -> 0 calibration rows, 6 -> 0 bins) — the honest STRUCTURAL state -> SS (R5)
- **Blast radius:** mi_gunanaka, mi_pariksha, mi_sambandha, mi_darshana, query_calibration, query_insights, activation gate sample size
- **Rebuild:** needs production rebuild (REVIEW; after mi_jivanaghatana / mi_bhavisya)
- **Gate it moves:** Earn (chronology), Null
- **Fix class:** data (output change) + writer code + additive migration; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-17

### FD-2 · Honest denominators and a non-circular reliability definition (R)

- **Answers:** pram-N2, N3
- **Change:** exclude UNRESOLVED from reliability bins (report them as a separate count); define `observed_rate` over adjudicated outcomes and bin by the prediction's stated `confidence_band` midpoint, not by the match score; when no stated probability exists, write NULL and `evidence_grade = prior_only`
- **Files / declaration / migration:** `mi_pramana.py:436-440,486-570`
- **Failing-first test and mutation:** failing-first: three UNRESOLVED rows in a bin leave n and observed_rate untouched; a bin can disagree with its x-axis; mutation: restore `verdict == CONFIRMED` over all rows -> FAIL
- **Output change:** yes: the 6 bins change; `observed_rate` becomes NULL where no adjudicated outcome exists -> SS (R5)
- **Blast radius:** mi_darshana calibrated_outlook units, query_calibration reliability_curve
- **Rebuild:** needs production rebuild (REVIEW)
- **Gate it moves:** Earn
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-18

### FD-3 · Replace proxy status flags by detectors or null (R)

- **Answers:** pram-N4, N5, N9; CF-L5-04; Q-L5-05
- **Change:** `held_out_validity` = pass only if every row of the bin is chronology-clean, non-held-out and independent (else `not_assessed`); `evidence_grade = empirical` only for such bins with n >= the ratified minimum; drop or null the constant dimensions (`score_magnitude` when event magnitude is NULL, `score_falsifier` when not evaluable) and renormalise the composite weights over the evaluable dimensions; stop writing `n_for_stratum = 1` and `evidence_admissibility = clean` as measurements
- **Files / declaration / migration:** `mi_pramana.py:144-214,459-460,541-542`
- **Failing-first test and mutation:** failing-first: no magnitude -> NULL score and weight renormalised; a bin with one chronology-unclean row is `not_assessed`; mutation: restore the constants -> FAIL. Golden-value tests (CF-L5-04)
- **Output change:** yes: dimension scores, composite, verdicts and bin labels change -> SS (R5)
- **Blast radius:** all consumers above
- **Rebuild:** needs production rebuild (REVIEW)
- **Gate it moves:** Earn, Null
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-19

### FD-4 · Pin the clock and the code version

- **Answers:** pram-N7, N8; CF-L5-01
- **Change:** write the build `as_of` date on each row (or in the receipt) and use it in `_window_passed`; bump `SCORING_FORMULA_VERSION` whenever behaviour changes (A-F-24 changed behaviour under an unchanged label)
- **Files / declaration / migration:** `mi_pramana.py:257-270`, `:55-56`
- **Failing-first test and mutation:** failing-first: two builds with the same `as_of` are byte-identical; mutation: use `date.today()` -> differs
- **Output change:** adds a column / label; verdicts unchanged under the same `as_of`
- **Blast radius:** fingerprint contract
- **Rebuild:** needs production rebuild (REVIEW)
- **Gate it moves:** Earn (build record)
- **Fix class:** writer code; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-20

### FD-5 · Join domains through one vocabulary (R)

- **Answers:** pram-N6; Q-L5-06
- **Change:** map prediction domains and LEL categories through one authoritative L0 map with class-aware resolvers (as the L0 Q4 ruling for two-class ids); `domain` score from that map, NULL when unmapped
- **Files / declaration / migration:** `mi_pramana.py:158-160`; L0 `bg_ontology` consumer
- **Failing-first test and mutation:** failing-first: `wealth` vs `finance` scores 1.0 under the map; unmapped pairs NULL; mutation: restore string equality -> FAIL
- **Output change:** yes -> SS (R5)
- **Blast radius:** composite scores and verdicts
- **Rebuild:** needs production rebuild (REVIEW)
- **Gate it moves:** Vocab
- **Fix class:** writer code + vocabulary; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-21

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-01** — deployed rows carry the invented base rate main no longer writes
- **CF-L5-02** — 4 rows with a vanished event
- **CF-L5-03** — the central chronology / circularity finding
- **CF-L5-04** — constants and proxy flags
- **CF-L5-05** — thresholds and weights are engineering constants to be named and ratified
- **CF-L5-06** — domain vocabulary and verdict vocabulary
- **CF-L5-07** — pram-N11
- **CF-L5-10** — consumer effect: activation gate and insight_get
- **CF-L5-11** — no canonical receipt; writer hash unknown
- **CF-L5-12** — Build.history cascade

## 5 · Semantic fingerprint contract (for E5.5)

Chart-scoped. Stable: `match_id, prediction_id, event_id, score_*, composite_score, composite_verdict` once the clock is pinned (`as_of`); `scored_at` excluded; verdicts depend on `date.today()` today (pram-N7). Reliability: all columns, same pin. The fingerprint must also pin the weights row `mi_pramana_scoring_weights` in `brahma_formula_constants`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the temporal-window match, the dimension decomposition idea, the verdict vocabulary (UNRESOLVED is the honest state), the A-F-24 and A-F-30 honest nulls, the Decimal bin fix (A-F-34, :508-523), the stale-prediction exclusion.
- **Carriage check chosen (T4 §4.1; one only):** D3 (independent re-derivation): the reliability bins are recomputable from `mimamsa_calibration` (the writer's own comment records a bin-boundary defect found by exactly that recomputation, :503-518); a second implementation recomputing verdicts from stored scores catches threshold drift. Also run it on the pre-fix rows to reproduce 0.1.
- **Opportunities (never blocking):** adjudicate against the `brahma_prospective_ledger` (matched/confirmed/falsified rows, with the mandatory falsifier) instead of a window-overlap join; that is the structure T2 section 9.3 describes and is where real empirical values will come from.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-01** — Chronology gate: may a prediction/event match enter calibration (`mimamsa_calibration`, `mimamsa_reliability`, learned multipliers, the activation-gate sample) only if the event's `recorded_at` and `event_date` are on or after the prediction's `emitted_at`, with earlier matches kept as a separately labelled retrodiction class? (53 of 53 resolvable matches today pre-date emission.) *Recommendation:* Yes. On the canonical chart this takes calibration rows 57 -> 0 and bins 6 -> 0, which is the honest STRUCTURAL state; real values then fill in as prospective outcomes accrue. (R)
- **Q-L5-02** — Issuance authority: is `mimamsa_predictions` a rebuildable candidate store (as T2 section 9.1 says) whose first `emitted_at` must be preserved by insert-if-absent and whose hash must cover content, or should calibration read the two `brahma_*` ledgers (18 open + 5 rows) as the issuance authority? Also: a rebuild currently collides with any row that has left `pending` (unique key, no ON CONFLICT). *Recommendation:* Keep the table as candidates with insert-if-absent, content hash and versioned supersession; link each candidate to its ledger id; calibrate only candidates that have a ledger linkage for the "prospective" stratum. (R)
- **Q-L5-03** — Authorise the production rebuild of the L5 chain (after the L3/L4 rebuild lands) so that main's corrected code replaces the 2026-08-13 rows (stale labels served today: 31 `empirical` insight units, 51 "Blind retrodiction" statements, `base_rate = 0.1` x57, 7 grammar rows at 0.0 propensity); and mark the old rows stale before the rebuild. Order: jivanaghatana -> bhavisya -> pramana -> (gunanaka, pariksha) -> sambandha -> adhilepa -> darshana. *Recommendation:* Yes, as one REVIEW-gated Track B wave after Q-L5-01/02 are ruled (otherwise the rebuild re-creates the retrospective calibration under cleaner labels). (R)
- **Q-L5-04** — Constants: ratify as named documented approximations (in `brahma_formula_constants`) the engineering thresholds and weights (verdict 0.65 / 0.35, composite weights, bin width 0.1, n >= 5, k = 5, cap 3, n >= 3 promotion, discovery 3 / 0.15 / 20) — and drop (NULL) the invented priors and missing-term defaults (mi_sambandha channel priors and the 0.5 default, +-0.1 bands, 0.5 / 1.0 fallbacks)? *Recommendation:* Thresholds and weights: ratify as named constants (ask the L3 Q-L3-01 precedent: option 1). Invented priors, bands and defaults: option 2, NULL / `unsourced`. (R)
- **Q-L5-05** — Status flags: replace the constant / proxy flags (`admissible_clean`, `shaped_predictor`, `held_out_validity`, `gate_passed`, `confidence_high`, `neg_control_clear`, `leakage_status = clean`, `skill_score` on underpowered rows) by detectors or NULL / `not_assessed`; allow the DDL changes this needs (nullable columns, additive basis columns)? *Recommendation:* Yes; unverified admissibility stays calibration-eligible but labelled `unverified_inputs`. (R)
- **Q-L5-06** — Vocabulary authority: which L0 map joins prediction domains (transition, wealth, spirituality, character, ...) to LEL categories (finance, spiritual, psychological, residential+travel, ...) and channel ids to domains? Class-aware resolvers (L0 Q4 precedent) or a new map? *Recommendation:* One L0 map in `bg_ontology` with class-aware resolvers; unmapped = NULL (not 0). (R)
- **Q-L5-10** — Compute `calibration_status` / `mode` in `mimamsa_insight_get` from the returned units and the gate basis instead of the constants `prior_only` / `STRUCTURAL` (`register_p1_synthesis.ts:642-643`, also `register_p1_synthesis.ts:931`)? *Recommendation:* Yes; STRUCTURAL remains the default until a chronology-clean `empirical` unit exists. (R)
- **Q-L5-11** — Activation-gate sample basis: `total_matches = COUNT(*) FROM mimamsa_calibration` (57 = 32 adjudicated = 13 distinct predictions = 0 prospective) opens the `empirically_calibrated` gate at >= 30 by code reading. Should the sample be distinct, adjudicated, chronology-clean predictions? (Paripraśna code; the data comes from L5.) *Recommendation:* Yes; coordinate with the Paripraśna owner. Until then the gate's own note says its 30 is a placeholder. (R)
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
- **Q-L5-20** — Tier vocabulary (TG-L5-014): adopt `structural / prior_only / assignment_only / empirical` (the vocabulary `mi_darshana` already stores with a `grade_basis`) as the layer vocabulary, with a named detector for each tier and one meaning of "empirical" (chronology-clean, adjudicated, independent, n >= ratified minimum)? *Recommendation:* Yes. (R)
