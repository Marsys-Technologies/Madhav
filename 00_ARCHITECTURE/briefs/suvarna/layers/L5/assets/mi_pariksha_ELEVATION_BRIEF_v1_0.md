---
asset_id: mi_pariksha
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
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16); lift-key fix (output change) to Strategic Suvarṇa (R5)"
risk_class: "medium (one output-changing bug fix; rebuild needed for the stale generation anyway)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-30, TI-L5-31, TI-L5-32, TI-L5-33, TI-L5-34]
ledger_gap_ids: ["mi_pariksha-Build.completion", "mi_pariksha-Earn.build_record", "mi_pariksha-Cost.baseline", "mi_pariksha-Build.history", "mi_pariksha-Build.dep_liveness", "mi_pariksha-Carr.detector", "new: par-N1", "new: par-N2", "new: par-N3", "new: par-N4", "new: par-N5", "new: par-N6", "new: par-N7", "new: par-N8", "new: par-N9", "new: par-N10"]
---

# mi_pariksha — Attribution engine, QA harness and retrodiction suite (seven substeps)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

Seven substeps into three tables. (1) `retrodiction` (:135): for each admissible, non-held-out dated event, up to 3 `phala_anchors` in the event's domain whose `window_start <= event_date`, written as `discovery_class = 'retrodiction'` into `mimamsa_discoveries`. (2) `control_windows` (:287): each event shifted by +365, -365, +730 days, status `control_baseline` or `FAIL_event_too_close`, into `mimamsa_qa_eval`. (3) `ablation` (:361): per-family `structural_proxy` rows. (4) `attribution` (:445): for each calibration match x driving signal x 5 dimensions, `credit = signal_strength x dimension_score x weight x lift_factor` into `mimamsa_attribution`. (5) `neg_control` (:567): 4 `not_implemented` rows plus a `degenerate_distribution` check. (6) `discovery` (:664): `(signal, dimension)` pairs with n >= 3 and mean credit >= 0.15, first 20, as `emergent_law` candidates. (7) `tail_only` (:788): one `structural_proxy` row. Of the five L5 writers touched by the honesty campaigns this is the most candid in its own comments (it states in the docstring and the stored statement what each substep does not do), which makes the remaining defects easy to isolate.

**Canonical chart state (read-only, 2026-10-03).** **1,664 rows = qa_eval 168 + attribution 1,425 + discoveries 71.** QA: control_window 153 (92 `control_baseline` + 61 `FAIL_event_too_close`), ablation 9 `structural_proxy`, tail_only 1 `structural_proxy`, negative_control 4 `not_implemented`, degenerate_distribution 1 `pass` (`qa`). Attribution: 57 matches, 15 signals, 2 families, credit 0 .. 0.64. Discoveries: 20 `emergent_law` (strength 0.2161 .. 0.3734) and 51 `retrodiction` (43 of them with 0 matched anchors); all `candidate`. **These rows were written by `mi_pariksha_v2.0` code** (`discovery_formula_ver`, 71/71): the stored `retrodiction` statements read "Blind retrodiction for <event> (<domain>) with T−90d cutoff <date>. Top-k anchors matched: 3." (51/51) — the sentence the F-143 / F-148 fix removed because the cutoff is not applied; `evidence_refs` carries no `cutoff_enforced` / `n_scored_matches` keys (0/71). The 153 control windows = 51 events x 3: the build saw 51 clean non-held-out events; the LEL now has 50 (CF-L5-02).

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / per_chart / postgres_table | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2988` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_pariksha.py:90` `@register("mi_pariksha")`; heavy writer, 7 substeps (`plan_substeps` :100); registry `has_substeps` = t | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_qa_eval`; count_sql tables: `mimamsa_qa_eval`, `mimamsa_attribution`, `mimamsa_discoveries` | registry / census |
| count_sql (live) | `SELECT (SELECT count(*) FROM mimamsa_qa_eval WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_attribution WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_discoveries WHERE chart_id = $1) AS count` | registry |
| live rows (canonical chart) / floor | 1664 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / True / 10800s | registry |
| registry build state (canonical chart) | throughput `error`, rows_written 1664, last_built_at 2026-08-21T02:36:53Z; recent canonical runs: complete 2026-08-13; complete 2026-08-07; complete 2026-08-07; complete 2026-07-28 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `mi_pramana`, `mi_kula`, `bg_formula_constants`, `bo_laksana`, `mi_jivanaghatana` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | `mi_darshana`, `mi_sambandha` (registry); census transitive blocking radius 2 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Declared (live): `mi_pramana`, `mi_kula`, `bg_formula_constants`, `bo_laksana`, `mi_jivanaghatana`. Actual: `mimamsa_event_provenance`, `mimamsa_calibration`, `mimamsa_predictions` (`mi_bhavisya`, undeclared), `mimamsa_signal_families`, `mimamsa_negative_controls`, `brahma_formula_constants`, `phala_anchors` (:189, :478 — **an L4 read with no declared `ph_*` edge**), `bodha_msr_signals` (:795). | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | Served: `query_calibration.ts:192` (`mimamsa_qa_eval`: qa_results, fail count with the disclosed `FAIL` prefix rule), `query_attribution.ts:84`, `query_mimamsa_discoveries.ts:89`; writers: `mi_darshana.py:349` (discoveries -> insight units), `mi_sambandha` (no direct read). Census reach: 6/8 columns; Dens.served: 3 modules declaring a contract. | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `tests/test_mi_pariksha_context_stale_filter.py`, `tests/test_mi_pariksha_discovery_scored.py`, `tests/test_mi_pariksha_retrodiction_disclosure.py` (the three that pin the F-143 / F-148 disclosures), `L5_mimamsa/__tests__/query_attribution.test.ts`, `query_mimamsa_discoveries.test.ts`, `query_calibration_qa_fail_count.test.ts`; none exercises `anchor_lift` keying, the discovery cap order, or the degenerate-distribution proxy | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | no receipt, no freshness row for the canonical chart; digest spec present (reviewed 2026-09-09T13:18Z); natural-key partition migration 999; throughput `error` 2026-08-21 (BLOCKED on `mi_pramana`), rows_written 1,664 = live 1,664; the earliest recorded run was reaped ('manual reap: parent run stopped; orchestrator died mid-build', 2026-07-11) | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (60) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): mimamsa_discoveries (mi_pariksha.py:170), mimamsa_qa_eval (mi_pariksha.py:305), mimamsa_qa_eval (mi_pariksha.py:384), mimamsa_attribution (mi_pariksha.py:480), mimamsa_qa_eval (mi_pariksha.py:589), mimamsa_discoveries (mi_pariksha.py:682), mimamsa_qa_eval (mi_pariksha... |
| Build | Build.target † | PASS | target_table=mimamsa_qa_eval |
| Build | Build.dag † | PASS | 3 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | FAIL | build record state='error' is not a completed build (rows_written=1664, live=1664, chart 482012f1) — see Build.history; target_table mimamsa_qa_eval alone: 174 row(s), whole table — context, not the compared figure |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=1664) |
| Complete (information) | Complete.depth | PASS | 174 rows, 8 cols; fully populated 7; NEVER populated [] |
| Dens | Dens.served † | PASS | 3 module(s): query_attribution.ts, query_calibration.ts, query_mimamsa_discoveries.ts; declaring density_contract: 3 |
| Build | Build.history | FAIL | most recent run error (2026-08-21); 30 error(s), 9 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-08-21): BLOCKED: upstream dependency(ies) mi_pramana did not complete in this run; skipped to avoid building on incomplete data |
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
| mi_pariksha-Build.completion | Build.completion | stale | measured: build record state='error' is not a completed build (rows_written=1664, live=1664, chart 482012f1) — see Build.history; target_table mima... |
| mi_pariksha-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_pariksha-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_pariksha-Build.history | Build.history | history | measured: most recent run error (2026-08-21); 30 error(s), 9 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-0... |
| mi_pariksha-Build.dep_liveness | Build.dep_liveness | stale | measured: 2/3 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_pramana (error, chart 482012f1)'] — a DEP-ASSERT trap if no w... |
| mi_pariksha-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: par-N1 | Narr / deployed-vs-code | stale (served false claim) | 51 stored retrodiction statements assert a blind T-90d backtest ("Blind retrodiction ... with T−90d cutoff ..."); the code now states the opposite (:225-229, "NOT a blind backtest"). The old sentences are served: `mi_darshana` copies them into 51 `retrodiction` insight units graded `prior_only` (so numerics are suppressed, but the sentence is not) and `query_mimamsa_discoveries` serves them raw. Cleared only by a rebuild (CF-L5-01) |
| new: par-N2 | Narr / deployed-vs-code | stale | 20 stored `emergent_law` statements read "(mean=0.32, n=41)" with `n_support` = 41 attribution assignments and no `n_scored_matches`; downstream `mi_darshana` v1.0 graded all 20 `empirical` on `n >= 5` (the F-35/F-143 defect), served unsuppressed (see mi_darshana). Code on main would demote them to `assignment_only` |
| new: par-N3 | real bug | real | `lv = anchor_lift.get(signal_id)` (:523): `anchor_lift` is keyed by **anchor_id** (:482) while `signal_id` is an **MSR signal id**, so the lookup misses for every driving signal (0 of 15 signal ids resolve to a key), `lift_factor` is always 1.0 and the "lift vector contribution" described in the comment never applies. The attribution is `salience x dimension score x weight`, with two of the five dimension scores constant (0.5 magnitude, 0.5 manifestation) in `mi_pramana` |
| new: par-N4 | Earn (credit_blame) | real | `credit_blame` is a product of numbers, not a counterfactual: it assigns the same share of a match score to every driving signal in proportion to its salience, whatever the outcome; the discovery step then reports "consistent {dimension}-dimension credit" as a candidate law (:731-751). With n = pairs of the same repeated matches (pram-N1) the mean credit cannot disagree with its inputs. The label is honest (`candidate`, not `law`); the sentence "Candidate emergent calibration law" is the only claim |
| new: par-N5 | determinism | real | discoveries are the first 20 `(signal_id, dimension)` groups in `ORDER BY a.signal_id, a.dimension, a.match_id` order (:763) after thresholds n >= 3 and mean >= 0.15 (:715-718): the cap keeps alphabetically-first uuids, not the strongest; ties and order depend on uuid values |
| new: par-N6 | Earn (degenerate check) | real | `degenerate_distribution` is `FAIL` iff the mean composite is >= 0.95 or <= 0.05 (:639); it is named a distribution check and measures a mean. A bimodal 0/1 distribution with mean 0.5 reads `pass`. It reads `pass` on the stored mean (a proxy; there is no variance or support test) |
| new: par-N7 | constants | information | control-window `result_score` is the literal 0.5 for every row (:334); the offsets (+365, -365, +730) and the 90-day "no event" test are unlabelled constants; "FAIL_event_too_close" (61 of 153) describes how crowded the LEL is, not a QA failure, yet `query_calibration` counts all `FAIL*` statuses as failures by the disclosed prefix rule |
| new: par-N8 | honest proxies (kept) | information | `ablation` and `tail_only` rows are written `structural_proxy` with `marginal_skill` exactly 0.0 and the note "structural_proxy only; full ablation requires serve-time R-pipeline rerun" (:421, :841); `negative_control` rows are `not_implemented` with the reason (JL-019, :630). These are the correct form. Residual: their `result_score` is a number (the mean composite) on rows that measured nothing; a consumer reading `result_score` without `status` would take it as a result |
| new: par-N9 | Build.dag | real | reads `phala_anchors` with no `ph_*` edge, `mimamsa_predictions` with no `mi_bhavisya` edge; `mi_jivanaghatana` and `bo_laksana` edges are real (CF-L5-07) |
| new: par-N10 | style | information | `import math` at the foot of the module (:864) serves a use at :215; it works because import runs before `run`, but a reader (or a lint) cannot tell |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| retrodiction `statement` / `evidence_refs` | a blind backtest with T-90d cutoff | deployed: old template; main: "NOT a blind backtest" + `cutoff_enforced: false` flags | main **earned** (explicit false flags and semantics text); deployed rows **false claim** |
| `n_support` (emergent_law) | number of supporting outcomes | count of attribution assignments | main discloses the semantics (`n_support_semantics`) and records `n_scored_matches`; deployed rows do not |
| `credit_blame` | credit / blame for the outcome | salience x score x weight x lift (lift never applied) | arithmetic, not attribution |
| `strength` (retrodiction) | strength of the retrodictive match | the top anchor's `posterior` | a restatement of an L4 value; 0 when no anchor matched (43 rows) — a 0 standing for "no anchor", not "measured zero" |
| QA `status` values | which checks passed | six literals, only `pass` x1 | `structural_proxy` / `not_implemented` are honest non-results; `pass` (degenerate) is a proxy; `control_baseline` is a construction label |
| `activation_status = candidate` | not activated | literal | earned (nothing activates autonomously) |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD: no autonomous research activation; empty lift vectors excluded rather than defaulted (BA-P6); each proxy substep says it is a proxy in its status and note; `n_scored_matches` and the three retrodiction disclosure flags are recorded as explicit false/null rather than omitted (F-143, F-148).
- BAD (deployed): the 51 stored statements and 20 grades are the older, less honest generation. BAD (code): `strength = 0` for no-anchor retrodiction rows and the constant `result_score` on proxy rows read as numbers.

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** `self._chart_id = str(ctx.config["chart_id"])` (:101) — this writer already coerces to `str`, so the `chart_id[:8]` slices at :408, :623, :642, :830 are safe (contrast `mi_gunanaka` before SV-6). `json.dumps` calls carry dicts built from strings/floats (:219, :336, :422, :631, :647, :743, :842). **Not exposed.**
- **Outcome-leakage guard:** `retrodiction` explicitly does NOT enforce the T-90d cutoff (the `cutoff_enforced: false` flag) and says so; `control_windows` use event dates only. The attribution and discovery steps read `mimamsa_calibration`, so they inherit the retrospective-match problem of `mi_pramana` (CF-L5-03).
- **People-entered data (N-46) / LEL data contract:** all three tables are regenerable derived outputs (INV: `_qa_eval`, `_discoveries`; `mimamsa_attribution` is in the INV 'neither list' group — reported, not classified here). No people-entered data touched.

## 3 · Disposition

**keep (P)** — the closest-to-honest writer in the layer: its proxies are labelled and its false claims have been removed in code. What remains is one real bug (the lift key), two proxy checks, and the stale generation in production. Keep and fix.

Approver under Track A brief section 10: **Steward (G16); lift-key fix (output change) to Strategic Suvarṇa (R5)**. Risk class: **medium (one output-changing bug fix; rebuild needed for the stale generation anyway)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Fix the lift-vector key (R)

- **Answers:** par-N3
- **Change:** key `anchor_lift` by the anchor that the prediction was built from (`predictions.source_pramana_id`), not by MSR signal id; apply the lift to that prediction's attribution rows; or drop the lift and the lv_* variables if SS prefers the arithmetic-only attribution
- **Files / declaration / migration:** `mi_pariksha.py:478-483,515-528`
- **Failing-first test and mutation:** failing-first: a prediction whose anchor has a `lift_vector_jsonb` gets `lift_factor != 1.0`; mutation: restore the signal-id key -> the factor is 1.0
- **Output change:** yes: `credit_blame` changes on rows whose prediction has a lift vector (4 live anchors today; more after rebuild) -> SS (R5)
- **Blast radius:** mi_darshana emergent_law units
- **Rebuild:** needs production rebuild (REVIEW)
- **Gate it moves:** Earn
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-independent once SS rules (Q-L5-21)
- **Track I item:** TI-L5-30

### FD-2 · Deterministic, strongest-first discovery cap

- **Answers:** par-N5; CF-L5-05
- **Change:** order by mean credit descending then signal id; name the thresholds (n >= 3, mean >= 0.15, cap 20) in `brahma_formula_constants`
- **Files / declaration / migration:** `mi_pariksha.py:715-763`
- **Failing-first test and mutation:** failing-first: the cap keeps the highest mean credit; mutation: restore alphabetical order -> FAIL
- **Output change:** yes: which 20 of the candidates are kept may change -> SS (R5)
- **Blast radius:** mi_darshana
- **Rebuild:** needs rebuild (REVIEW)
- **Gate it moves:** Idem (determinism)
- **Fix class:** writer code; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-31

### FD-3 · Make the degenerate-distribution check measure a distribution

- **Answers:** par-N6; CF-L5-04
- **Change:** test variance / support (e.g. share of rows at 0 or 1, or the number of distinct scores) rather than the mean; or relabel the check `mean_range`
- **Files / declaration / migration:** `mi_pariksha.py:636-645`
- **Failing-first test and mutation:** failing-first: a 0/1 bimodal set with mean 0.5 reads FAIL or `not_assessed`; mutation: restore the mean test -> reads pass
- **Output change:** label change on 1 row
- **Blast radius:** query_calibration qa_results
- **Rebuild:** needs rebuild
- **Gate it moves:** Earn
- **Fix class:** writer code; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-32

### FD-4 · Stop numbers on non-results

- **Answers:** par-N7, N8
- **Change:** set `result_score` NULL for `structural_proxy`, `not_implemented` and `control_window` rows (the constant 0.5 and the mean carry no result); keep the disclosure in `detail`
- **Files / declaration / migration:** `mi_pariksha.py:334,408-421,630,828-841`
- **Failing-first test and mutation:** failing-first: proxy rows have NULL result_score; mutation: restore -> FAIL
- **Output change:** yes: 168 rows' result_score -> NULL -> SS (R5)
- **Blast radius:** query_calibration qa_results (reads status first)
- **Rebuild:** needs rebuild
- **Gate it moves:** Null, Earn
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-33

### FD-5 · Declare the real reads

- **Answers:** par-N9; CF-L5-07
- **Change:** add `ph_nimitta` (phala_anchors) and `mi_bhavisya` (predictions) edges, or remove the reads
- **Files / declaration / migration:** registry migration
- **Failing-first test and mutation:** reads-match PASS; mutation: remove edge -> FAIL
- **Output change:** none
- **Blast radius:** DAG
- **Rebuild:** none
- **Gate it moves:** Build.dag
- **Fix class:** registry; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-34

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-01** — par-N1, N2: the served false claims are production rows from the older generation
- **CF-L5-02** — events 51 vs 50; MSR signals dangle (15 of 15 attribution signal ids)
- **CF-L5-03** — inherits retrospective matches
- **CF-L5-04** — degenerate proxy, constant scores
- **CF-L5-05** — thresholds and offsets
- **CF-L5-07** — par-N9
- **CF-L5-10** — insight units copy the stored statements
- **CF-L5-11** — no canonical receipt
- **CF-L5-12** — Build.history: one reaped run; cascade

## 5 · Semantic fingerprint contract (for E5.5)

Chart-scoped. Stable: `qa_eval(check_id, check_type, target, status, detail)` excluding `result_score` until FD-4; `attribution` all columns; `discoveries(discovery_id, discovery_class, statement, evidence_refs, strength, n_support, confidence_band)`. Pin the calibration generation and the weights row `mi_pariksha_attribution_weights`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the labelled-proxy convention (`structural_proxy`, `not_implemented`, `candidate`), the F-143 distinction between attribution assignments and adjudicated matches, the explicit disclosure flags on retrodiction rows, the per-substep inclusion-scoped deletes (B-F-09).
- **Carriage check chosen (T4 §4.1; one only):** D3: recompute attribution credits from the stored calibration rows, driving signals and weights with a second implementation; recompute the control-window dates and the no-event test from the event dates.
- **Opportunities (never blocking):** when chronology-clean matches exist, replace the attribution arithmetic by drop-one ablation against them (the honest definition behind `load_bearing` too); implement the four negative controls as the shuffled-birth / future-leak harness their ids describe.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-01** — Chronology gate: may a prediction/event match enter calibration (`mimamsa_calibration`, `mimamsa_reliability`, learned multipliers, the activation-gate sample) only if the event's `recorded_at` and `event_date` are on or after the prediction's `emitted_at`, with earlier matches kept as a separately labelled retrodiction class? (53 of 53 resolvable matches today pre-date emission.) *Recommendation:* Yes. On the canonical chart this takes calibration rows 57 -> 0 and bins 6 -> 0, which is the honest STRUCTURAL state; real values then fill in as prospective outcomes accrue. (R)
- **Q-L5-03** — Authorise the production rebuild of the L5 chain (after the L3/L4 rebuild lands) so that main's corrected code replaces the 2026-08-13 rows (stale labels served today: 31 `empirical` insight units, 51 "Blind retrodiction" statements, `base_rate = 0.1` x57, 7 grammar rows at 0.0 propensity); and mark the old rows stale before the rebuild. Order: jivanaghatana -> bhavisya -> pramana -> (gunanaka, pariksha) -> sambandha -> adhilepa -> darshana. *Recommendation:* Yes, as one REVIEW-gated Track B wave after Q-L5-01/02 are ruled (otherwise the rebuild re-creates the retrospective calibration under cleaner labels). (R)
- **Q-L5-04** — Constants: ratify as named documented approximations (in `brahma_formula_constants`) the engineering thresholds and weights (verdict 0.65 / 0.35, composite weights, bin width 0.1, n >= 5, k = 5, cap 3, n >= 3 promotion, discovery 3 / 0.15 / 20) — and drop (NULL) the invented priors and missing-term defaults (mi_sambandha channel priors and the 0.5 default, +-0.1 bands, 0.5 / 1.0 fallbacks)? *Recommendation:* Thresholds and weights: ratify as named constants (ask the L3 Q-L3-01 precedent: option 1). Invented priors, bands and defaults: option 2, NULL / `unsourced`. (R)
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
- **Q-L5-21** — Attribution lift key: fix the `anchor_lift` lookup (anchor id vs signal id) so the lift factor applies, or remove the lift term? Also make the discovery cap deterministic and strongest-first. *Recommendation:* Fix the key against the prediction's source anchor; deterministic strongest-first cap. (R)
