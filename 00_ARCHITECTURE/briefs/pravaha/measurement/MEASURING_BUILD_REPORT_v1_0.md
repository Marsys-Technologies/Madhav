---
artifact: MEASURING_BUILD_REPORT
version: "1.0"
status: WRITTEN — J-3d step report_written; independent acceptance pending
produced_on: 2026-10-19
changelog: v1.0 — first commit of the measuring-build report (MEASURING_BUILD_CONTRACT v1.0 MB-7; J3_MEASURING_PREBUILD_v1_0). Mechanical fill of the report template (D-G9 template PR #3731) plus the post-fill evidence: the D-G9 outcome, the invented/anomaly trace, the a53 golden measurement, the F-SHARED-GEOMETRY recomputation and the a53/a54/a55 residual files. Public-repository edition — counts, class names, digests, receipt ids and code citations only.
owner_step: J-3d report_written (plan model item J-3d owns this path)
contract: 00_ARCHITECTURE/briefs/pravaha/decisions/MEASURING_BUILD_CONTRACT_v1_0.md (MB-7)
---

# J-3d measuring build report

`ky.j3d_report/1` · filled report generated 2026-10-19T00:00:00Z · stamp 20261018T061409Z · constants: pack files BOUNDS.json, t45.json, EXPECTED_CENSUS.json

Every figure shows its source receipt; **NULL** = not readable (never 0), cause in the NULL register of section 16. Identifiers, counts, digests and booleans only; no personal data (section 16).

## 1. Run identity

- **run_id**: 9b8a3c01-6eb9-4679-9434-680c29cf7492
- **execution**: brahma-build-pipeline-job-lzl87
- **main**: 1078dd1cfea606cf913d3a9f9258c46aafa232fa
- **writer_digest**: 0758f4ec99197cfe2140410c481575cbc0132cd22f9f1a31251e2ef6b1c6a167
- **plan_digest**: be25dee391e5c7277688d0d7f9082abf5fd2d83b1a2c9030c3f65e2295d1e31d
- **plan_digest_equals_run_row**: True
- **image_commit**: 640c8c1e273e9474066c87dd69e545f288c32d96

## 2. Timings

- execution outcome: SUCCEEDED · **total 25625.645 s** · head 487.7 s · tail 4.455 s
- projection 34592.7 s → ratio 0.7408 (delta -8967.1 s) · re-projection 22721.1 s → ratio 1.1278 (delta 2904.5 s)
- incident bound 43300 s crossed: **False** (by: none seen) · max elapsed at a watch pass 26187.241 s · within the 72000 s cap: True
- longest substep: verify:bereavement 1086.788 s · substeps over 600 s: 8
- watch ledger: 29 passes {'NO_STALL': 29}

| class | seconds |
|---|---:|
| achievement_recognition | 320.04 |
| bereavement | 2117.109 |
| business_launch | 128.246 |
| career_advancement | 1417.884 |
| career_change | 1422.699 |
| career_entry | 1423.51 |
| career_setback | 1286.712 |
| childbirth | 1074.779 |
| chronic_onset | 1540.567 |
| education_milestone | 1440.349 |
| exam_outcome | 1484.026 |
| financial_deception | 33.963 |
| foreign_settlement | 135.172 |
| illness_acute | 1556.838 |
| major_gain | 1103.44 |
| major_loss | 1106.971 |
| marriage | 793.433 |
| parental_event | 30.334 |
| property_acquisition | 134.342 |
| psychological_arc | 2.797 |
| relocation | 1344.329 |
| romantic_start | 776.303 |
| separation | 1571.74 |
| spiritual_turn | 4.728 |
| surgery | 1516.944 |
| travel_event | 1366.238 |

## 3. Verify share

- sum of verify seconds 11568.622 (reference 13400, SR-W3-SHAPE) · share of total 0.4514

| class | verify s | class s | share |
|---|---:|---:|---:|
| achievement_recognition | 233.642 | 320.04 | 0.73 |
| bereavement | 1086.788 | 2117.109 | 0.5133 |
| business_launch | 47.224 | 128.246 | 0.3682 |
| career_advancement | 577.075 | 1417.884 | 0.407 |
| career_change | 571.36 | 1422.699 | 0.4016 |
| career_entry | 576.55 | 1423.51 | 0.405 |
| career_setback | 544.132 | 1286.712 | 0.4229 |
| childbirth | 339.729 | 1074.779 | 0.3161 |
| chronic_onset | 807.138 | 1540.567 | 0.5239 |
| education_milestone | 604.989 | 1440.349 | 0.42 |
| exam_outcome | 600.235 | 1484.026 | 0.4045 |
| financial_deception | 7.978 | 33.963 | 0.2349 |
| foreign_settlement | 46.394 | 135.172 | 0.3432 |
| illness_acute | 809.012 | 1556.838 | 0.5197 |
| major_gain | 606.954 | 1103.44 | 0.5501 |
| major_loss | 544.314 | 1106.971 | 0.4917 |
| marriage | 350.812 | 793.433 | 0.4421 |
| parental_event | 7.899 | 30.334 | 0.2604 |
| property_acquisition | 47.161 | 134.342 | 0.3511 |
| psychological_arc | 0.316 | 2.797 | 0.113 |
| relocation | 585.386 | 1344.329 | 0.4354 |
| romantic_start | 347.341 | 776.303 | 0.4474 |
| separation | 840.232 | 1571.74 | 0.5346 |
| spiritual_turn | 0.385 | 4.728 | 0.0814 |
| surgery | 803.789 | 1516.944 | 0.5299 |
| travel_event | 581.787 | 1366.238 | 0.4258 |

## 4. Leanness (SR-J3D-LEANNESS-ROW)

- median seconds per search_interval 0.188232 · flag threshold 0.376464 · flagged (J-4c findings): ['achievement_recognition', 'business_launch', 'financial_deception', 'foreign_settlement', 'parental_event', 'property_acquisition']
- (I) INTERPRETATION I-3: distinct contact ids referenced by the class's relationship records in 31-golden-capture (the readbacks carry no per-class contact table); alternative: a per-obligation contact join, which needs a new read-only SQL

| class | substep s | intervals | contacts | s / interval | s / contact | flag |
|---|---:|---:|---:|---:|---:|---|
| achievement_recognition | 320.04 | 38 | 2063 | 8.422105 | 0.155133 | True |
| bereavement | 2117.109 | 7817 | 8025 | 0.270834 | 0.263814 | False |
| business_launch | 128.246 | 38 | 2063 | 3.374895 | 0.062165 | True |
| career_advancement | 1417.884 | 7768 | 5488 | 0.182529 | 0.258361 | False |
| career_change | 1422.699 | 7768 | 5488 | 0.183149 | 0.259238 | False |
| career_entry | 1423.51 | 7768 | 5488 | 0.183253 | 0.259386 | False |
| career_setback | 1286.712 | 7743 | 4561 | 0.166177 | 0.282112 | False |
| childbirth | 1074.779 | 7732 | 4407 | 0.139004 | 0.24388 | False |
| chronic_onset | 1540.567 | 7779 | 5933 | 0.198042 | 0.259661 | False |
| education_milestone | 1440.349 | 7768 | 5794 | 0.185421 | 0.248593 | False |
| exam_outcome | 1484.026 | 7768 | 5794 | 0.191044 | 0.256132 | False |
| financial_deception | 33.963 | 13 | 464 | 2.612538 | 0.073196 | True |
| foreign_settlement | 135.172 | 38 | 2063 | 3.557158 | 0.065522 | True |
| illness_acute | 1556.838 | 7779 | 5933 | 0.200133 | 0.262403 | False |
| major_gain | 1103.44 | 7768 | 5421 | 0.142049 | 0.203549 | False |
| major_loss | 1106.971 | 7743 | 4549 | 0.142964 | 0.243344 | False |
| marriage | 793.433 | 7734 | 3989 | 0.10259 | 0.198905 | False |
| parental_event | 30.334 | 13 | 464 | 2.333385 | 0.065375 | True |
| property_acquisition | 134.342 | 38 | 2063 | 3.535316 | 0.06512 | True |
| psychological_arc | 2.797 | **NULL** | 0 | **NULL** | **NULL** | NULL |
| relocation | 1344.329 | 7786 | 5899 | 0.17266 | 0.227891 | False |
| romantic_start | 776.303 | 7734 | 3989 | 0.100375 | 0.194611 | False |
| separation | 1571.74 | 7781 | 5774 | 0.201997 | 0.27221 | False |
| spiritual_turn | 4.728 | **NULL** | 0 | **NULL** | **NULL** | NULL |
| surgery | 1516.944 | 7779 | 5933 | 0.195005 | 0.255679 | False |
| travel_event | 1366.238 | 7786 | 5899 | 0.175474 | 0.231605 | False |

## 5. Stretch sink

- counts taken from: **summary** (finding F-SINK-READER proved; summary lines digest-bound: 26)
- records 13140 (distinct record ids read 1966) · by kind {'anomaly': 12, 'horizon_clipped': 312, 'invented': 12, 'multi_episode_stretch': 294, 'near_miss': 303, 'station_seam': 12045, 'wrap': 162}
- by kind/reason {'anomaly/boundary_pairing_mismatch': 12, 'horizon_clipped/clipped_at_end': 168, 'horizon_clipped/clipped_at_start': 144, 'invented/ledger_contact_not_reconstructed': 12, 'multi_episode_stretch/multiple_ledger_episodes': 294, 'near_miss/certified_positive_clearance': 303, 'station_seam/arc_index_station_inside': 12045, 'wrap/ray_band_contains_wrap_cut': 162}
- summary lines 26 · classes without a summary [] · consistent False

## 6. Census, totals, horizon, run verdict

- class_census_exact True · per-class rows 52 · inexact []
- manifest_rows: measured 1 expected 1 equal True
- snapshot_rows: measured 1 expected 1 equal True
- seal_rows: measured 0 expected 0 equal True
- window_verifications: measured 0 expected 0 equal True
- inventory_verifications: measured 0 expected 0 equal True

| object | rows |
|---|---:|
| ka_gochara_eval_window | 6629 |
| ka_gochara_relationship_record | 174974 |
| ka_gochara_contact | 14912 |
| kala_gochara_coverage | 26 |
| ka_gochara_search_interval | 139979 |
| ka_gochara_search_obligation | 3035 |
| ka_gochara_search_path_pin | 130 |
| ka_gochara_search_inventory | 26 |
| ka_gochara_search_input_snapshot | 1 |
| kala_gochara_publication | 1 |
| ka_gochara_eval_window_record | 109831 |
| ka_gochara_record_prerequisite | 312016 |
| ka_gochara_eval_window_verification | 0 |
| ka_gochara_search_inventory_verification | 0 |
| kala_gochara_windows | 0 |
| kala_gochara_contacts | 0 |
| asset_provenance_receipts | 1 |
| asset_freshness | 1 |
| asset_throughput | 1 |
| build_substep_progress | 0 |
| build_runs | 1 |
| build_run_assets | 1 |
| seal_5_0 | 0 |
| authority_5_0 | 0 |

- horizon: stored_scope test_slice · status candidate · basis ruled_horizon · rule ruled_scope+birth_centenary · rows_total 0 · three-way equal to the ruled pair True; derived horizon (value in the local decision ledger)
- run verdict: completed / complete / build / lit · last substep {'index': 298, 'total': 298} · **MB-4.7 success True**
- db cutoff: cutoff_after_completion True, no_heartbeat_after_completion True, no_asset_end_after_completion True, no_output_row_after_completion True
- authority before teardown: rows 1, generations ['3.0'], seal rows 0
- global retained rows: ka_gochara_sky_event 50124; ka_gochara_sky_convention 1; ka_gochara_physical_object 2405; ka_gochara_convention_bridge 1; kala_gochara_convention 1; ka_gochara_rule_path 5; ka_gochara_rule_path_seal 5; ka_gochara_rule_path_soft_factor 9; ka_gochara_rule_path_prerequisite 7; ka_gochara_factor 11; ka_gochara_predicate 8; moon_non_event_class_coverage 0
- golden capture sections: {'binding': 1, 'contact': 14912, 'manifest': 1, 'published': 1, 'record': 174974, 'sealed': 1, 'window': 6629} · sealed 0 · published 0

## 7. D-G9 dispositions (template PR #3731; filled mechanically; outcome in section 11)

Report draft supplied: True · used: True · run id matches dispatch: True · draft sha256 5c382a7841582381 · golden manifest sha256 0926425f99dd1886 · proposals on file: none

| OD | disposition | reasons | fields read |
|---|---|---|---|
| OD-1 | DEFAULT_RETAINED | all_null_candidate/1 and the scope statement equals CANNOT_ESTABLISH: the final build keeps all_null_candidate/1; endpoints vacuous under policy, never green | RB-SQL.manifest.input_generation_vector.result_policy (31-golden-capture); RB-REPORT.numbers[13].data.cannot_establish (report draft) |
| OD-2.1 | DEFAULT_RETAINED | no stored window precedes the horizon start: a question dated before it returns a named refusal, never a silent empty | RB-SQL.manifest.lo; RB-SQL.window[*].lo/hi; RB-SQL.manifest.input_generation_vector.scored_until; RB-SQL.sealed.n; RB-SQL.published.n |
| OD-2.2 | NOT_APPLICABLE | scored_until_not_pinned: carried to J-4d (the final build must pin it) | RB-SQL.manifest.lo; RB-SQL.window[*].lo/hi; RB-SQL.manifest.input_generation_vector.scored_until; RB-SQL.sealed.n; RB-SQL.published.n |
| OD-2.3 | BOUND_TO_D-FLIP | mechanism (reader/projection, 1236 replacement, flip and rollback, near-miss display) is not measurable on a test slice | RB-SQL.manifest.lo; RB-SQL.window[*].lo/hi; RB-SQL.manifest.input_generation_vector.scored_until; RB-SQL.sealed.n; RB-SQL.published.n |
| OD-4 | DEFAULT_RETAINED | run the final-rules candidate (FB-66); the DVI guard and eight-class density are decided there; DVI equality proves the guard cannot be computed on this build, not that it holds | RB-REPORT.numbers[9].data[eight][P1|P3|P4]; RB-REPORT.numbers[5].data.classes[c].admitted_days.P4_with_dvi / P4_without_dvi (26); RB-REPORT.numbers[5].data.classes[c].admitted_share.class_union (18-class band flags) |
| OD-5 | NOT_APPLICABLE | no unresolved stretch; G9-0.3 input, reported not decided: omission/invented/anomaly counts {'omission': 0, 'invented': 12, 'anomaly': 12} are not all 0 (G9-0.3 pass rule: all three 0) | stretch sink counts from STRETCH_SINK/1 lines (31-cloudrun-logs sink block); kind unresolved by reason {clearance_below_min_approach, no_crossing_unproved, extension_unsettled} |
| OD-6 | NOT_APPLICABLE | equal by construction on this build (every record has via=base); the default (karakatva limited to the eight) is DEFAULT_RETAINED for the candidate | RB-REPORT.numbers[5].data.classes[c].admitted_days.P1_with_karakatva / P1_base (26); RB-REPORT.numbers[9].data[eight].P1 |
| OD-7 | DEFAULT_RETAINED | K-B as ruled (FB-45); K-B added density is carried to the final-rules candidate | RB-REPORT.numbers[14].data.{scored_share,budget_share,label}; RB-REPORT.numbers[5].data.classes.bereavement.admitted_days.kb_only |
| OD-10 | DEFAULT_RETAINED | literal reading, scored-horizon denominator; NOT_DECISIVE_ON_THIS_BUILD: the guard is evaluated with DVI members on the final-rules candidate | RB-REPORT.numbers[5].data.classes.financial_deception.admitted_share.{P4_without_dvi,class_union}; RB-REPORT.numbers[5].data.{horizon_days,convention} |

Roll-up: unfilled [] · readback_inconsistent [] · out_of_template [] · OD rows would allow approved: **True** · G9-0.3 sink input (omission, invented, anomaly all 0): **False** (G9-0.1..7 and Q-G9-0 are NOT computed here (they need the five step receipts, the MB-6 view and the golden bundle); an OD roll-up that allows 'approved' is necessary, not sufficient)
- (I) OD-1: result_policy = all_null_candidate/1 with a cannot_establish text that differs from CANNOT_ESTABLISH reads READBACK_INCONSISTENT (G9-0.6 fails); the template states only the equal case
- (I) OD-2.1: no window row in the capture reads UNFILLED (vacuous), not DEFAULT_RETAINED
- (I) OD-6: the readback disposition is NOT_APPLICABLE; DEFAULT_RETAINED is recorded as candidate_default
- (I) OD-10: P4_without_dvi greater than class_union reads READBACK_INCONSISTENT (P4 is one path of the class)
- (I) report draft: the draft-fed ODs read numbers[5], [9], [13].cannot_establish and [14] only, all derived from the golden bundle; the draft is built with observations limited to the bundle's binding and manifest digest, so its own refusals (steward observations, teardown, acceptance) stay in the draft and are not OD inputs; alternative: wait for the full observations
- (I) report draft binding: a draft whose binding.run_id differs from the dispatch's run id is not used (its ODs read UNFILLED); an unreadable binding is used and recorded as run_id_matches_dispatch null
- (I) OD-5 (--sink-source summary): the unresolved total and reasons are summed from the 26 STRETCH_SINK_SUMMARY/1 lines because F-SINK-READER is proved; a kind or reason absent from every summary reads 0, which is supported because each class's kind counts sum to its records; counts are emissions per class (a shared record id counts once per class); alternative: keep OD-5 UNFILLED until the reader is fixed and the run re-read

## 8. BOLD-09 (SR-BOLD-09, SR-W3-SHAPE item 5)

- status **PLACEHOLDER** · job shape: cpu 4, memory 16Gi, task timeout 86400 s
- CPU utilisation peak **NULL** / mean **NULL** · memory peak **NULL** GiB · DB wait **NULL** s (**NULL** of the run; over 30% **NULL**)
- if not single-thread CPU-bound size the century task larger (up to 8 vCPU / 32 GiB); if single-thread bound say so and leave the shape; DB wait > 30% -> report the exact tier change and its downtime (owner console action via the surrogate). The verdict is the cockpit's; this block records numbers only.

## 9. Sources

| source | operation | accepted by | receipt sha256 | output sha256 | status |
|---|---|---|---|---|---|
| J-3c.dispatch | J-3c.dispatch | v1 | 45a07b6154717ddb | 0f7abae4c157773b | OK |
| J-3c.cloudrun-execution | J-3c.cloudrun-execution-20261018T061409Z-a29 | executor-mechanical | e5dea7e706aa6c8f | ecd8da689e5ad22c | OK |
| J-3d.cloudrun-logs | J-3d.cloudrun-logs-20261018T061409Z-a30 | executor-mechanical | b414213723839236 | 87ebeadb86572e21 | OK |
| J-3d.terminal | J-3d.terminal-20261018T061409Z | executor-mechanical | 624101e817a1d5f5 | 95adc9e49a960099 | OK |
| J-3d.substep-cutoff | J-3d.substep-cutoff-20261018T061409Z | executor-mechanical | 1a3fb5328fb19d3a | a26b50ebc6f32199 | OK |
| J-3d.census | J-3d.census-20261018T061409Z | executor-mechanical | e6fe86ca52c80c2d | 1c46f91148b17ea9 | OK |
| J-3d.horizon-basis | J-3d.horizon-basis-20261018T061409Z | executor-mechanical | 1c19b7649f885a1d | e1a315de49dc2134 | OK |
| J-3d.totals | J-3d.totals-20261018T061409Z | executor-mechanical | 7ef73fcc59b6f9d6 | 14c1dbeafc7182a4 | OK |
| J-3d.authority-before-teardown | J-3d.authority-before-teardown-20261018T061409Z | executor-mechanical | ba7a1db0aeee0824 | f15281262d0589fb | OK |
| J-3d.global-before-teardown | J-3d.global-before-teardown-20261018T061409Z | executor-mechanical | 4bfff6b88878ecba | 8c0fb99e99777790 | OK |
| J-3d.golden-capture | J-3d.golden-capture-20261018T061409Z | executor-mechanical | 4ac514d6afbb6756 | 5ca401650ee8d4ad | OK |

## 10. Findings (recorded, not gating)

- **F-SINK-READER** (SR-STRETCH-SINK-COUNTS): emitted 13,140 = read 13,140 (gap 0); 1,966 unique ids; 11,174 cross-class duplicates; 23 of 26 classes read differently from their summary (17 read zero); 5,775 duplicates are implied by identical id sets, 5,399 remain (partial overlap, inferred). Reader: cloudrun_readback.py:503-506 (origin/main reader, ref/ copy): `elif record["record_id"] in records: duplicates += 1` - the dedup key is record_id alone. Fix: SR-STRETCH-SINK-COUNTS item 2: key by (event_class, record_id) and export read-by-kind per class (separate reader PR, rank 1).
- **F-SHARED-GEOMETRY** (SR-STRETCH-SINK-COUNTS item 3): 18 of 24 non-empty classes share their full stretch-record id set with another class, in 7 sets; empty classes ['psychological_arc', 'spiritual_turn']; inventory-digest sharing: **NULL in the template fill, measured afterwards from the golden: section 12**. report only, for J-4c and post-campaign design; no W3W4 change.

| set (digest12) | classes | records each | same kind counts |
|---|---|---:|---|
| e63e2e899bbf | achievement_recognition, business_launch, foreign_settlement, property_acquisition | 341 | True |
| 19bdb3a61fb4 | career_advancement, career_change, career_entry | 704 | True |
| e9ca853aea42 | chronic_onset, illness_acute, surgery | 645 | True |
| 016cd15ae67b | education_milestone, exam_outcome | 697 | True |
| af5167ac788d | financial_deception, parental_event | 66 | True |
| c9a8068376eb | marriage, romantic_start | 546 | True |
| e40ed7cde20e | relocation, travel_event | 745 | True |
- **F-LEANNESS** (SR-J3D-LEANNESS-ROW): FLAGGED; flagged ['achievement_recognition', 'business_launch', 'financial_deception', 'foreign_settlement', 'parental_event', 'property_acquisition'] at seconds per interval above 0.376464 (2 x median 0.188232) -> J-4c finding(s) to fix before the century build; not a reason to hold J-3d. Classes not judged: ['psychological_arc', 'spiritual_turn']. Descriptive: flagged classes have at most 38 intervals, unflagged at least 7732.

## 11. D-G9 outcome and the invented/anomaly trace

- **D-G9 was posted APPROVED** (execution record, 2026-10-19T01:49:04Z) on the conditional approval PRE-D-G9-v2, under SR-DG9-DECIDE clause (c), with the OD dispositions of section 7 as read. The derived horizon it approves is recorded in the local decision ledger only (value not restated here).
- **Blocking findings attached** (SR-DG9-DECIDE c): **F-INVENTED** and **F-ANOMALY**, both J-4c items. They are preconditions of D-CLOUD, not of D-G9.
- **G9-0.3 failing is the expected shape of a measuring build** (contract OS-2; SR-DG9-DECIDE b): the gate stays at zero and is not relaxed.
- The J-4d slice may start as pre-build; its qualification counts only after D-G9 was posted, and its three classes must include at least one class carrying an F-INVENTED or F-ANOMALY id (SR-DG9-DECIDE e).

### 11.1 Trace of the 12 invented + 12 anomaly emissions (job X-20261019T005038Z-g903-trace)

Verdict: **`certifier_findings`** (SR-DG9-DECIDE d not triggered: no writer defect shown).

- The 24 emissions are **3 distinct problem spots, counted four times** per kind, because the record id carries no event class and several classes reuse the same stretch geometry (`stretch_sink.py` `record_id`; F-SINK-READER / F-SHARED-GEOMETRY). Show the gate by distinct id (3 + 3) next to emissions (12 + 12) so the fix target is not overstated four-fold.
- Mechanism: `invented / ledger_contact_not_reconstructed` is a recorded contact period that no independently reconstructed stretch agrees with (`contact_certify.py` `_compare_sink_all`, lines 306-311); `anomaly / boundary_pairing_mismatch` is a stretch touched by a recorded contact that agrees with no recorded period, or two sequences failing to pair overall (same function, lines 290-293 and 312-315). One boundary disagreement yields one of each; the repository test `test_mb_stretch_sink.py` (half-covered stretch) pins exactly that pair. Anomaly equals invented in every class.
- Nothing is malformed or mis-labelled: every kind/reason is in the closed vocabulary the writer enforces before logging (`stretch_sink.py` `_check_record`); the build commit's certifier files equal main's.

| event class | invented | anomaly | shares ids with | basis |
|---|---:|---:|---|---|
| chronic_onset | 2 | 2 | illness_acute, surgery | proven (identical full id set) |
| illness_acute | 2 | 2 | chronic_onset, surgery | proven |
| surgery | 2 | 2 | chronic_onset, illness_acute | proven |
| major_loss | 2 | 2 | the same 2 ids | inferred |
| marriage | 1 | 1 | romantic_start | proven pair |
| romantic_start | 1 | 1 | marriage | proven pair |
| major_gain | 1 | 1 | the same 1 id | inferred |
| separation | 1 | 1 | the same 1 id | inferred |
| **total** | **12** | **12** | 3 distinct ids each | |

- (I) INTERPRETATION: the 3 distinct ids are 2 shared by the four two-per-class classes and 1 shared by the four one-per-class classes. Alternative: some one-per-class classes carry one of the two ids; the totals (12 and 3) are the same either way.
- **Not established (NULL, with cause):** which 3 spots they are, and their path, body and target. The raw sink lines were deliberately not kept (privacy ruling) and the receipt holds counts only; an offline replay of the checker on the saved contacts was starved by machine load (3 of 37 likely candidates examined in about nine minutes, none flagged) and was stopped. Whether the mismatch lies in the builder's contact periods or in the checker's reconstruction is therefore undecided; the contract assigns the fix to the builder (OS-2).
- Next (builder, J-4c): save raw sink lines per class and id on the next measuring run, or replay the checker on an idle machine, then fix as the evidence shows.

## 12. F-SHARED-GEOMETRY recomputed from the golden (job X-20261019T025023Z-shared-geom-golden)

Source: the local golden bundle, manifest sha256 `0926425f99dd1886bd1f69b5f970fee6f27428856da7e6fecf494b56253a2d32` (all six manifest files verified). The production rows are gone by design, so this is a recomputation (SR-J3-RESIDUALS 3). SQL mirrored: `platform/scripts/readbacks/class_inventory_digest.sql` (`rec_rows` / `rec` CTEs). The golden's `source_commit_attested` is null: its source commit is as recorded, not attested.

- **Record sets: confirmed.** 7 groups of classes carry byte-identical record content, 18 of the 24 classes that have records (26 classes in the slice; `psychological_arc` and `spiritual_turn` have 0 records, and an empty set is not a share). The 6 other classes with records are each unique: bereavement, career_setback, childbirth, major_gain, major_loss, separation.
- Inside a group the record sets differ only by the class name baked into `record_id` (`record_set_digest` is distinct for every member; `record_content_digest` is equal).
- **Stored inventory and ledger digests do not share, by construction** (read from the definitions in code, not measured on rows): the `inventory_digest` preimage holds `ob=<canonical_bytes>` lines and the `ledger_digest` rows hold `ob_id`; both start from the event class (`inventory.py` `Obligation.canonical_bytes` / `ob_id`; migration 1206 `ka_gochara_search_inventory_preimage`, `…_ledger_digest`). The stored `input_digest` (the per-chart, per-generation input snapshot, migration 1206) carries no class name, so classes of one generation are expected to share it (schema reading, not measured).
- **Not computable from the golden (NULL, N.7.6):** `obligation_count`, `obligation_content_digest`, `pin_count`, `pin_content_digest` and the three stored digests. The golden holds records, contacts, windows and the input vector only. Whether the groups also share obligation and pin content is **unmeasured**; identical records are strong indirect evidence of the same enumerated edge geometry, not proof (an obligation with no contact in the horizon leaves no record). Closing it needs an offline `enumerate_edges` run per class, or a rebuilt candidate generation read back with the same SQL.
- Verification: per-(class, path) record counts recomputed from the golden equal the digest file for all 78 pairs (0 mismatches; 174,974 records). A hand check on `financial_deception` (464 records) by three independent routes (a Python script; a `jq` / `sort` / `shasum` chain; the SQL's own expressions in a session-only temporary table on the local disposable cluster) gave equal digests.
- Ruling: J-4c leanness finding and post-campaign design input; no W3 change (SR-A53-NARROW).

| size | classes | records each | record_content_digest | records per path |
|---|---|---|---|---|
| 4 | achievement_recognition, business_launch, foreign_settlement, property_acquisition | 2063 | `1027b7976939d66b20b9938cf6dbf63b32b06cdb532a112134366437ef37efb5` | P2=2063 |
| 3 | career_advancement, career_change, career_entry | 10161 | `c9e4d1e01f42ed72c3e841a35c3bcc60844b1022dbee26de11f496b58f7ec05b` | P1=4542, P2=2063, P3=3275, P4=281 |
| 3 | chronic_onset, illness_acute, surgery | 9264 | `027b48a8b57ff11f8852449690f1fdb2a5d5e2aa7510fbf1cc2d0ecf3edf91e5` | P1=3440, P2=464, P3=4929, P4=431 |
| 2 | education_milestone, exam_outcome | 10380 | `6b1858452853ee9b3cda12144895ba696e9c429e1eed53dbaf8798e7f21a8afa` | P1=4726, P2=2063, P3=3304, P4=287 |
| 2 | financial_deception, parental_event | 464 | `719483f8dba36bbbb75acd7d502fba1dde95ea86d7c8d30b182ad46cb79f1f94` | P2=464 |
| 2 | marriage, romantic_start | 6478 | `b7d5fe8bfeacf2e80ac9786a08327bc95dbcb059b0dc5520c9e80917aeb81f75` | P1=2637, P2=2063, P3=1638, P4=140 |
| 2 | relocation, travel_event | 10211 | `f380b74b8270cacf7400d8b13ad9b49f9b67c1cde6494490770e1d01a704b45e` | P1=3695, P2=2063, P3=4092, P4=361 |

## 13. A5.3 (J-3d-a53) golden measurement

Job X-20261019T024918Z-a53-measure, with the day-tier dependency job X-20261019T030741Z-daytier-dep; code read at the pinned head `a0520d04ceca8706c109bef2a70bebfd48ee3460`. Evidence file: `00_ARCHITECTURE/briefs/kalayantra/evidence/residuals/J-3d-a53.json`, sha256 `844510a7427d154e48ed0cbe99f0091cdc455fc069cbc67c23d2bf1144968cc5`. Production rows are gone by design: every count below is from the local golden (stored scope `test_slice`, 26 classes, 24 with records, result policy `all_null_candidate/1`), not from a database readback. Rulings: SR-J3-RESIDUALS (2), SR-A53-NARROW, SR-A53-ARTIFACT.

| claim | status | measured (golden) | code |
|---|---|---|---|
| C1 three objects | **measured true** | contacts 14,912 (all distinct ids; 0 without a record); relationship records 174,974 in 78 grains, equal to the digest per grain; windows 6,629; 8 records without a contact (all `unqualified`, 0 supports, path P3) | `record_store.py:809,939`; `window_store.py:170,181`; `ka_gochara_v5.py:1043-1053` |
| C2 per-path pruning | **measured true** | not admitted: P1 63,068 of 68,521; P2 45 of 35,121; P3 0 (8 unqualified); P4 1,304 of 5,698; P5/P6 records 0; window exclusion ledger 48,708 not_admitted + 17,615 testimony + 0 no_support | `record_store.py:1008-1022`; `window_sweep.py:760-770`; `ka_gochara_v5.py:152` |
| C3 interval sweep | **measured true** | independent re-union reproduces the stored windows in 78 of 78 grains, 6,629 of 6,629 windows; 0 extra, 0 missing grains, 0 zero-length windows | `window_sweep.py:792-803,549,565` |
| C4 interior extrema | **narrowed, not measured (NULL)** | "implemented and unit-tested, not exercised by the measuring run (all_null policy)": 0 windows carry a peak or score field; all 13,258 window edges equal a member support edge, so 0 by construction, not a finding of absence | `window_sweep.py:455,824,888`; `ka_gochara_v5.py:1559`; `test_a53_window_sweep.py:333,349,354` |
| C5a day tier, no stored rows | **measured true** | Moon contacts 0; records with Moon as agent 0; P6 records 0; stretch sink 0 bytes; 15 windows of at most one day are span unions (P3 14, P4 1), not a day tier | specs v1.4:408; migrations 1153:684, 1155:729 |
| C5b day tier on demand | **narrowed, not measured (NULL)** | "implemented and unit-tested; no writer step and no non-test caller"; dependency check: **no** served Kala read model in CLOSURE_v3 (187 closure items scanned) reads a P6 / Moon record, so the day tier is not a blocking finding | `moon_on_demand.py:183`; `ka_gochara_v5.py:999-1058`; `candidate_boundary.py:30` |
| C6 coarse-to-fine cost | **carried, not measured (NULL)** | the golden records no timing or skipped-work counts | specs v1.4:806 |
| C7 closes Disclosure 3 | **carried, not measured (NULL)** | "carried to J-7a-a62 (deferred)" — closed at A6.2, J-7a family deferred under A9 D-53; a note on the item, not an a53 acceptance condition | specs v1.4:816; `J7_PREBUILD_v1_0.md:86` |

Re-entry of the narrowed and carried claims: C4 at the first `window_qualification/1` build (the J-4d slice) and again in the J-4e readback, with a measured row counting windows with peak fields set and `maximise_earliest` edges, both greater than 0 wherever the rules admit them (0 is a defect, not a pass); C5b at the P6 promotion gate (B5.4), post-campaign; C6 at the J-4e readback (substep timings); C7 at J-7a-a62. No narrowed or carried claim is asserted green.

(I) INTERPRETATION (evidence file): C5 is split in two (5a stored rows are none; 5b computed on demand) because the golden can prove the first and cannot prove the second. Alternative: one "day tier" claim, which would have to read either false (no writer step) or green on absence alone.

## 14. Residual evidence files (SR-J3-RESIDUALS 4, SR-A53-ARTIFACT)

| item | file under `00_ARCHITECTURE/briefs/kalayantra/evidence/residuals/` | sha256 |
|---|---|---|
| J-3d-a53 | `J-3d-a53.json` | `844510a7427d154e48ed0cbe99f0091cdc455fc069cbc67c23d2bf1144968cc5` |
| J-3d-a54 | `J-3d-a54.json` | `42e80dc0bdfa66802c4ba579d96ff11ba34b1532c2eae7ef3a4be2a8b9331a95` |
| J-3d-a55 | `J-3d-a55.json` | `bce65aab131644d3ef394abebe9d545efe6229eec01816bd3cf92c909aa082ca` |

Each file is copied by the cockpit to the run folder's `residuals/` directory, where its plan-model detector reads it. a53 changed from an operation item to an artifact item because no executor operation can produce a golden-measured bundle (SR-A53-ARTIFACT). A file's existence is not acceptance: the typed, digest-bound independent review receipt for each item is separate.

## 15. What this report does not assert

- MB-7 numbers 4 to 9, 13 (the verbatim cannot-establish text and the acceptance verdict) and 14 (share grids, window lengths, per-agent days, the near-miss and sink counts beyond section 5, the eight-class census, the bereavement share beside its budget) are carried by the golden bundle's report draft (sha256 prefix in section 7), not restated here. Sections 5 and 6 carry the sink and census counts that the filled template read.
- Teardown outcome and end state (MB-7 number 12), the absence proof, and the independent acceptance of every J-3d step (`readback_accepted`, `golden_capture`, `report_written`, `teardown`, `absence_proof_accepted`) are separate steps and receipts. This document is the `report_written` artifact only.
- BOLD-09 (section 8) is a PLACEHOLDER: the Cloud Run metrics were not produced by any receipt kind.
- The measuring run is a test slice with result policy `all_null_candidate/1`. Scores, endpoints, retrodiction, sealing, publication and serving are outside what it can show (MB-5.5).

## 16. NULL register and personal-data statement

NULL figures (a ratio per zero or a count not readable is never written as 0):

| figure | cause |
|---|---|
| leanness rows for `psychological_arc` and `spiritual_turn`: interval count, seconds per interval, seconds per contact | no interval count for the class; the contact count is 0, so a ratio per zero is not defined |
| F-SHARED-GEOMETRY obligation and pin content digests | not present in the golden (section 12) |
| OD-2.2 scored-until pin | `scored_until_not_pinned` (carried to J-4d) |
| BOLD-09: CPU peak and mean, memory peak, DB wait and its share | no receipt kind produces the Cloud Run metrics; filled by the cockpit's metrics read |
| the 3 distinct invented/anomaly spots: id, path, body, target | raw sink lines not kept (privacy ruling); replay starved (section 11.1) |
| C4, C5b, C6, C7 results | narrowed or carried with re-entry (section 13) |

**Personal data: none.** This public-repository document holds counts, event-class names from the engine's fixed vocabulary, digests, receipt and run identifiers, and code citations only. It holds no life-event rows, no event dates or event-derived dates (the derived horizon is recorded in the local decision ledger and not restated here), no chart-binding content and no targets. The timestamps that appear are build, run and decision-record times.
