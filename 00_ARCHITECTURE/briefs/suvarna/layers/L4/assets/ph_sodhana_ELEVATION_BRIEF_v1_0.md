---
asset_id: ph_sodhana
layer: L4 Phala (ph_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL - until J1; may register gaps, may not certify"
produced_by: track-a-l4 (worker under Exec Suvarna)
produced_on: 2026-10-03
plan_item: A.L4 (briefs, dispositions, designs)
census_revision_used: "fresh census `/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json` (generated 2026-10-02T10:12:59+05:30, chart 482012f1, inspector 1e5781a at REGISTRY_REVISION 10; outside the repo) compared with the repo's saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json` (2026-09-30T20:23:50+05:30, inspector 2a78ec64d). Main's inspector is now at REGISTRY_REVISION 15: the offline rollup below applies its rules to the fresh census; no live re-measure was run."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L4/L4_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 3de3f8b15"
disposition: "enrich (E) - fix the detectors' silence below 5 anchors and the mismatched ceiling; keep the leakage firewall; rebuild"
disposition_proposal_approver: "Steward (G16); any output change to SS (R5)"
disposition_value: enrich
risk_class: "R3 (what "no anomaly" may be allowed to mean propagates to ph_suddha_sodhana and ph_phaladesa; the code change is small)"
decisions_applied: "none - SS has not answered the A.L4 questions (INDEX section 7); all dispositions and fix designs are proposals"
ss_questions: [Q-L4-01, Q-L4-05, Q-L4-12]
track_i_items: [TI-L4-01, TI-L4-04, TI-L4-15, TI-L4-16, TI-L4-17, TI-L4-18]
ledger_gap_ids: [ph_sodhana-Build.completion, ph_sodhana-Build.dep_liveness, ph_sodhana-Build.history, ph_sodhana-Carr.detector, ph_sodhana-Complete.depth, ph_sodhana-Cost.baseline, ph_sodhana-Dens.served, ph_sodhana-Earn.build_record]
---
# ph_sodhana - Anchor anomaly registry (leakage firewall)

> **PROVISIONAL - until J1; may register gaps, may not certify.** Every figure below comes from a stated read-only query (suvarna_reader SELECTs on 2026-10-03, receipts under `/Users/Dev/suvarna-evidence/A_L4/data/`), from the census, from the repository at main `3de3f8b15` (file:line), or from running the asset's pure engine functions locally with no database. Where something could not be determined it says so. Nothing here certifies a gate, approves a disposition or changes an asset.

## 0 - Identity: what the asset is

`ph_sodhana` writes `phala_sodhana`, an anomaly registry (fewer rows is better: the registry deliberately has no `target_floor`, §N.4). Five per-anchor detectors run over every `phala_anchors` row - `layer_leakage` (confidence_basis must be exactly `structural_not_yet_empirical`; a hit raises `LeakageFirewallError` and halts the build, `platform/python-sidecar/services/ph_sodhana/engine.py:264-297,414-456`), `confidence_inflation` (confidence_high above a G-LADDER ceiling computed from `dasha_consensus_count` and `ayanamsha_robustness`, `:116-164`), `magnitude_drift` (proxy on confidence_high, `:167-216`), `falsifier_absent` (`:219-238`), `ledger_gap` (`:241-261`) - plus two chart-wide detectors added in W3 (`confidence_degenerate`, `ceiling_inputs_degenerate`, `:300-411`). `auto_action` is always `stage_for_review` (DB CHECK). The writer deletes the chart's rows, runs the engine over all anchors and inserts (`platform/python-sidecar/pipeline/orchestrator/writers/ph_sodhana.py:48-98`).

| field | value | source |
|---|---|---|
| kind | registry `asset_kind=artifact`, `asset_type=data`, `scope=per_chart`, `domain=chart`, `rung=R4`; role per L4 layer instance TG-L4-024: not assigned by any tier | `asset_registry` row, read 2026-10-03 |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2714` (live may differ by migration) | seed |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ph_sodhana.py:37`; engine `platform/python-sidecar/services/ph_sodhana/engine.py`; registry `has_writer=True` | code |
| target table(s) | `phala_sodhana` | registry `target_table` / `count_sql` |
| live rows (canonical chart) / floor / build record | 0 / none / `rows_written=97`; rows per chart in the table(s): phala_sodhana: 1c826d5a=41 | `count_sql` run read-only; `asset_throughput`; table group-by |
| state / last built | `stale` / 2026-08-13T01:16:07 UTC (run `cbd6ea44`); `built_against_writer_hash=unknown` | `asset_throughput` |
| catalog_status | CURRENT | registry |
| depends_on (declared, live) | `ph_nimitta`, `bo_laksana` | `asset_registry.depends_on` |
| depends_on vs what the code reads | reads only `phala_anchors` (`ph_nimitta` declared). **`bo_laksana` is declared but nothing it produces is read.** No undeclared read found | code (file:line) + fresh census `Build.dag` |
| blast radius | declared dependents direct 2 / transitive 12 (active assets, every layer) | fresh census `blocking_radius` |
| code readers outside the asset (non-test py/ts/tsx, 13 files) | L5 / other writers (python-sidecar pipeline/orchestrator/writers): ph_phaladesa.py, ph_suddha_sodhana.py; python-sidecar other: bodha_writers/_idempotency.py, brahmagyan/l0_formula_constants.py, services/ph_suddha_sodhana/engine.py; serving (platform-mcp/src): resources/vidhi/dossier_slices/dossier_slices.generated.ts; retrieval + app (platform/src): lib/jyotish/asset_names.ts, lib/retrieval/registry/knowledge/producer_editorial_review.ts, lib/retrieval/registry/knowledge/source_query_availability.ts, lib/retrieval/registry/layers/L4_phala/index.ts, lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts, lib/retrieval/registry/layers/L4_phala/query_predictive_anchors.ts, lib/retrieval/registry/layers/L4_phala/salience_order.ts | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src at `3de3f8b15` (tests, generated and migrations excluded) |
| served surface | `L4_phala/query_phala_calibration.ts` `query_anomaly_flags` (selects the table; no `density_contract`); read by `ph_suddha_sodhana` (flags grouped per anchor) and `ph_phaladesa` (anomaly counts) | code |
| role / scoring mode | manifestation-family asset of L4 Phala (T2 section 6.5); census `scoring: contribution`; 'detectors for inflated confidence, absent falsifiers/derivation, contamination' (T2c label); T2 section 6.5 calls it a purification/provenance kernel | tiers + census |
| invalidation / FK | `anchor_id -> phala_anchors ON DELETE CASCADE` (so the registry is emptied whenever its anchors are) | `pg_constraint` read 2026-10-03 |

## 1 - Measured state and the nine gates

### 1.1 - Live state on the canonical chart (read-only, 2026-10-03)

- **0 rows** on the canonical chart. Build record `rows_written = 97` (census Build.completion FAIL 'empty: live=0'); the other built chart holds 41 rows (34 `confidence_inflation`, 6 `falsifier_absent`, 1 `magnitude_drift`). The 97 vanished with the 135 anchors they cited (CASCADE).
- **0 rows is not a clean bill.** The 4 surviving anchors have identical `confidence_high` (0.372) and an identical `(dasha_consensus_count, ayanamsha_robustness)` pair (0, 3). The two chart-wide detectors built to catch exactly that return nothing because `_DEGENERATE_MIN_ANCHORS = 5` (`engine.py:300,318,373`). Reproduced with the repository's own functions: **4 identical anchors -> `[]`; 5 identical anchors -> `[confidence_degenerate, ceiling_inputs_degenerate]`** (`offline_checks.txt`). `test_ph_wave5.py::test_below_min_anchors_no_flag` pins the silence as intended.
- **The loudest detector measures a different model.** On the other built chart `confidence_inflation` flagged 34 of 56 anchors 'major' against a ceiling of 0.506 for the constant pair (0, 3); the ceiling is the old G-LADDER formula, and the engine says so: the comment at `engine.py:39-52` calls it 'this detector's OWN independent QA ceiling' that 'has not tracked any live ph_nimitta computation for months'. On that chart 36 distinct anchors carry a major or critical flag (34 `confidence_inflation`, 6 `falsifier_absent`), and `phala_suddha_sodhana` reads 36 `staged_revision`, 19 `clean`, 1 `flagged`: the inflation flags drive most of the staging.
- That chart's anchors also show one `(dasha_consensus_count, ayanamsha_robustness)` pair across all 56 anchors (read-only count) and the chart holds no `ceiling_inputs_degenerate` row: it was built before W3-3k added the detector (2026-09-05).
- Build is `stale`; 1 of 2 declared dependencies lit (`ph_nimitta` stale).

Build history for this asset (all charts, `build_run_assets`): 9 aborted, 35 complete, 26 error/blocked_dependency, 2 error, 19 queued; the last complete canonical-chart run is `cbd6ea44` (2026-08-13), and the 26+ `error/blocked_dependency` rows are cascade skips, not writer errors. The only non-cascade errors on record: 2 errors 2026-07-11, both `TypeError: Object of type UUID is not JSON serializable` raised from `asset_runner.py:459` in `_run_data_writer` (the UUID chart_id defect, fixed by `6c0d98614` on 2026-07-12 with `_UUIDEncoder` and `str(ctx.chart_id)`), plus 9 aborts.

### 1.2 - Stored rows versus current code

Commits touching this asset's writer or engine AFTER its last build (2026-08-13 01:16 UTC): `396bde8af` 2026-09-06 L4 W3-3h: ph_sodhana — LEAKAGE-FIREWALL NULL/empty confidence_basis blind spot (#1845); `95bbafaa7` 2026-09-06 L4 W3-3m: ph_sodhana — ayanamsha_robustness=0 silently coerced to the default (F-12) (#1870); `78031d443` 2026-09-05 L4 W3-3k: ph_sodhana — a detector for the G-LADDER ceiling's own degenerate inputs (F-13) (#1857).

Three W3 commits landed after the build: `78031d443` (W3-3k: `ceiling_inputs_degenerate`), `95bbafaa7` (W3-3m: genuine `ayanamsha_robustness=0` no longer coerced to 3) and `396bde8af` (W3-3h: NULL/empty `confidence_basis` is now a leakage hit). The stored table is empty so the visible effect of a rebuild depends entirely on the new anchors.

### 1.3 - Census cells (fresh run, compared with the saved run)

Census used: fresh census `/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json` (generated 2026-10-02T10:12:59+05:30, chart 482012f1, inspector 1e5781a at REGISTRY_REVISION 10; outside the repo) compared with the repo's saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json` (2026-09-30T20:23:50+05:30, inspector 2a78ec64d). Main's inspector is now at REGISTRY_REVISION 15: the offline rollup below applies its rules to the fresh census; no live re-measure was run.

| gate | criterion | fresh verdict | measured (fresh census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Null | Null.schema_default | PARTIAL (saved 2026-09-30: (absent in saved run)) | no schema default on the declared prose column(s) recommendation_text; writer literal fallbacks and constant columns are not measured here, so this is never PASS |
| Null | Null.blank_rows | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | INCONCLUSIVE: no checkable prose rows were read for the declared entries |
| Narr | Narr.checkable | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | INCONCLUSIVE: 0 checkable rows on every declared entry (recommendation_text=0) |
| Narr | Narr.fidelity_test | PARTIAL (saved 2026-09-30: (absent in saved run)) | structural only: 3 test file(s) call the builder and assert in the same test function (test_nar_ph_sodhana.py, test_ph_sodhana_engine.py, test_ph_wave5.py); declared field(s) referenced: recommendation_text; whether the assertion grades the sentence is not read, so this never reads PASS |
| Narr | Narr.lint | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — the narration lints are not applicable to this asset: no chart_facts fact_category selection in its 4-file writer scope and no declared column the raw-token lint covers; a clean scan of code they cannot see is not a pass |
| Dens | Dens.served | FAIL | STRUCTURAL: 1 module(s) reach it by code: L4_phala/query_phala_calibration.ts; 1 served select(s) of its table; no referencing capability that serves it declares density_contract |
| Build | Build.dep_liveness | PARTIAL | 1/2 declared dependencies lit at chart 482012f1 (or global); stale: ['ph_nimitta (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Build | Build.completion | FAIL | empty: live=0 (count_sql over the target table; chart 482012f1) and the registry does not declare zero rows complete (target_floor=none); build record rows_written=97 |
| Build | Build.history | PARTIAL | latest run complete, but 3 error(s) and 9 abort(s) on record (26 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-07-11): TypeError: Object of type UUID is not JSON serializable Traceback (most recent call last): File "/app/platform/python-sidecar/pipeline/orchestrator/asset_runner.py", line 459, in _run_data_writer |
| Complete | Complete.depth | PARTIAL | 41 rows, 14 cols; fully populated 13; NEVER populated ['leakage_class'] |
| Complete | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach | Reach.fields | NOT_GENERIC | reported, not graded — width 9/13 built column(s) (69.2%) selected by 1 capability module(s); dark: ['chart_id', 'computed_at', 'derivation_ledger_jsonb', 'source_citation']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Earn | Earn.service_state | N/A (saved 2026-09-30: (absent in saved run)) | declared kind 'data' is not `service`; Earn.service_state is the service-state check (a service's rows_written cannot tell healthy-and-idle from broken) |

**PASS cells (compact):** Ldgr.source_presence, Idem.pattern, Vocab.identity, Narr.agree, Build.registered, Build.contract, Build.target, Build.dag, Build.exercised, Build.count_integrity.

**Offline rollup** (main `asset_census.py` rollup rules at REGISTRY_REVISION 15 applied to the FRESH census; N/A reads NO_DETECTOR while `NA_RULE_DECISIONS` is empty; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.
Same rules over the SAVED 2026-09-30 census: Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

### 1.4 - Earned-signal (N.8), narration-fidelity (N.7) and honest-null audit of this asset's flags and verdicts

| field / claim | what it claims | what code path could make it read false | finding |
|---|---|---|---|
| 0 rows (clean) | "no anomaly on this chart" | with fewer than 5 anchors the two chart-wide detectors cannot fire (`engine.py:318,373`); `ledger_gap` requires only the key `anchor_source` (`:58,241-261`) which every writer-produced ledger has; `falsifier_absent` passes if EITHER token is present (`any(...)`, `:222`) although its docstring and message say both | **A signal with weak or no detector behind it** (§N.8): 0 rows reads as clean; two of seven detectors are structurally silent at n<5 and two more are near-tautologies |
| `confidence_inflation` (major) | confidence_high exceeds what the evidence supports | real comparison, but against `(0.50 + 0.05 n) x (0.80 + 0.04 rob)` with n = `dasha_consensus_count` (constant 0 -> 1) and rob constant 3 -> ceiling 0.506 (`:116-138`), a ladder from the model the posterior replaced | **Mismatched instrument**: flags 34/56 on the other chart for a reason that is a property of the old formula, not of the anchors |
| `magnitude_drift` (minor) | magnitude label inconsistent with convergence strength | proxy: compares `confidence_high` to a tier threshold x 0.80 (`:186-216`); labelled `check_basis=confidence_high_proxy_not_convergence_score` (narration-honest since SAMAPTI) | honest about being a proxy; still a proxy |
| `layer_leakage` -> halt | no L5 calibration in L4 rows | real: any `confidence_basis` other than the literal (including NULL since F-14) raises `LeakageFirewallError` (`:264-297,450-456`) | earned - the one detector that can plainly read false. Its input is a constant the sibling writer sets |
| `recommendation_text` / `expected_value_text` | a remedy for the anomaly | f-string templates over detector values (`:152-160,202-209`) | deterministic restatements; no LLM |
| `rows_written` | rows inserted | `rows_inserted += 1` follows `ON CONFLICT DO NOTHING` unconditionally (`platform/python-sidecar/pipeline/orchestrator/writers/ph_sodhana.py:85-96`) - the exact counting defect fixed in `ph_nimitta` / `ph_muhurta` / `ph_sankrama` | latent here: the key `(anchor_id, anomaly_type, detected_field)` can collide only if a detector emits twice for one anchor |
| chart-wide records | an anomaly of the whole chart | attached to `ctx.anchors[0]`, the first anchor by `ORDER BY anchor_id` (`engine.py:327,381`), i.e. an arbitrary anchor | the whole-chart finding lands on one random anchor, which `ph_suddha_sodhana` then marks `staged_revision` while its siblings read `clean` |

### 1.5 - UUID chart_id check (the bo_*/ph_* adapter defect)

**Confirmed hit, fixed.** The registry history holds two `TypeError: Object of type UUID is not JSON serializable` errors for this asset (2026-07-11 17:21 and 17:26 UTC, `build_run_assets.error`, traceback through `asset_runner.py:459 _run_data_writer`): the chart-wide detector put `ctx.chart_id` (a `uuid.UUID` on the real path) into `derivation_ledger_jsonb` and the writer called plain `json.dumps`. Fix `6c0d98614`: `str(ctx.chart_id)` in the engine (`services/ph_sodhana/engine.py:347,405`) AND a local `_UUIDEncoder` in the writer (`ph_sodhana.py:28-32,93`); regression test `tests/test_ph_sodhana_engine.py`. Residual: the encoder is copy-pasted (also in `ph_phaladesa.py:36-40`), not shared; the other seven writers have no encoder (CF-L4-09).

## 2 - Gaps: which are real, which are detector or definition gaps

Class vocabulary: **real** = a shortfall in code, rows, registry row or served surface; **real-stored** = the CURRENT code already fixes it but the stored rows predate the fix (cured by a rebuild, not by an edit); **design** = needs an SS or acharya decision; **detector** = the instrument is absent or its definition is the open point; **history** = a recorded past outcome no edit can change; **information** = Count/Cost/Complete/Reach, never a blocker; **opportunity** = beyond the requirement.

| gap id | gate | class | note (evidence) |
|---|---|---|---|
| ph_sodhana-G01 | Earn | real | Two chart-wide detectors return nothing below 5 anchors (`engine.py:300`); 4 identical anchors -> 0 rows. The 0-row table reads as a clean result (and feeds ph_suddha_sodhana `clean`) |
| ph_sodhana-G02 | Earn | real | `confidence_inflation` ceiling is the superseded G-LADDER; flags 34/56 anchors on the other chart (`engine.py:39-52,116-138`) |
| ph_sodhana-G03 | Earn | real | `falsifier_absent` uses `any` of two tokens though it says both (`:222`); `ledger_gap` can only fire if `anchor_source` is missing (`:58`) |
| ph_sodhana-G04 | Build | real-stored | Build record 97 vs live 0 (consequence of the anchors' removal); other chart built before `ceiling_inputs_degenerate` existed |
| ph_sodhana-G05 | Build | real | `rows_inserted += 1` unconditional beside `ON CONFLICT DO NOTHING` (`platform/python-sidecar/pipeline/orchestrator/writers/ph_sodhana.py:85-96`) |
| ph_sodhana-G06 | Narr | real | Chart-wide records are attached to `anchors[0]` (`engine.py:327,381`), an arbitrary anchor |
| ph_sodhana-G07 | Build | real | Declared edge `bo_laksana` with no table read |
| ph_sodhana-G08 | Build | history | Build.history PARTIAL: 3 errors (two UUID TypeErrors 2026-07-11, fixed) + 9 aborts |
| ph_sodhana-G09 | Null / Narr | detector | prose_fields declared (`recommendation_text`) but Null.blank_rows / Narr.checkable INCONCLUSIVE on an empty table (0 checkable rows); Narr.fidelity_test PARTIAL |
| ph_sodhana-G10 | Dens / Earn / Carr | detector | Dens.served FAIL (no `density_contract` on `query_phala_calibration.ts`); Earn, Carr, Vocab.alias NO_DETECTOR |
| ph_sodhana-G11 | Count | information | No `target_floor` by design (a floor would reward fabricating findings, registry note); Count.floor gives no verdict |

## 3 - Disposition

DISPOSITION: enrich

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/ph_sodhana_ELEVATION_BRIEF_v1_0.md (sections 1-4); receipts `_evidence/` (data/, upstream_receipts.json, rollup_L4.json, offline_checks.txt, rect_diag.txt); census `layers/census/census_L4.json` + fresh census `census_fresh/1e5781a/census_L4.json`

**enrich (E) - fix the detectors' silence below 5 anchors and the mismatched ceiling; keep the leakage firewall; rebuild.** Enrich (E): keep the leakage firewall and the five-detector architecture (it is the only place that can plainly read false for the no-calibration rule), and add what is missing so that 'no anomaly' is something the asset has earned: coverage below the 5-anchor floor must read as 'not assessable', not as clean (G01), the ceiling must be tied to the model it checks or retired (G02), and the near-tautological detectors tightened (G03). It is not a consolidation target on evidence: T2 section 6.5 asks for an overlap investigation of this and `ph_suddha_sodhana`; the evidence here is that `ph_suddha_sodhana` is a pure classification of this table's severity counts (see that brief), which would make a merge of the two a candidate - proposed as a question (Q-L4-12), not a disposition.

Approver under Track A brief section 10: **Steward (G16)** for keep/qualify/enrich; **SS** for any output change (R5). No disposition is applied by this brief.

## 4 - Fix designs (one per real gap; anything marked `needs production rebuild` or `needs migration` is a REVIEW item for Strategic Suvarna)

### FD-1 - Make absence of coverage a stated state, not a clean result

- **Answers:** G01; CF-L4-03
- **Change:** When the anchor set is below the degenerate-detector minimum, or the chart-wide detectors cannot run, write ONE informational row (`anomaly_type` extended, or a `phala_sodhana` coverage record) saying "chart-wide checks not run: n anchors < 5", or return the coverage in `WriterResult.notes` and let `ph_suddha_sodhana` read it. Lower `_DEGENERATE_MIN_ANCHORS` to 2 for the "all identical" case (variance of one value is trivially zero, so the guard is meant to avoid a single anchor, not four).
- **Files / declaration / migration:** `platform/python-sidecar/services/ph_sodhana/engine.py:300-411`; `platform/python-sidecar/pipeline/orchestrator/writers/ph_sodhana.py`; CHECK constraint `phala_sodhana_anomaly_type_check` if a new type is written (migration)
- **Failing-first test and mutation:** failing-first: 4 identical anchors -> a flag or a coverage record (today `[]`); mutation: restore the `< 5` guard -> the test fails; amends `test_ph_wave5.py::test_below_min_anchors_no_flag` which pins the opposite
- **Output change:** yes - new rows on small charts
- **Blast radius:** `ph_suddha_sodhana` counts, `ph_phaladesa` anomaly_flag_count, `query_anomaly_flags`
- **Rebuild:** needs production rebuild
- **Gate it moves:** Earn
- **Fix class:** writer code (+ migration if a new type); **risk class:** R3; **buildable before J1:** tier-dependent: what "no anomaly" may mean is TG-L4-017/019 territory
- **Decision:** OPEN - Q-L4-12

### FD-2 - Retire or re-ground the G-LADDER ceiling

- **Answers:** G02
- **Change:** Option A: derive the `confidence_inflation` bound from the same function the writer uses (`compute_posterior` clamp [0.02, 0.95] and band; flag a stored value that differs from its recomputation from `posterior_inputs`) - a D3-style check, no second model. Option B: drop the detector until `ph_nimitta` carries real measured inputs.
- **Files / declaration / migration:** `platform/python-sidecar/services/ph_sodhana/engine.py:39-52,116-164`
- **Failing-first test and mutation:** failing-first: an anchor whose stored `posterior` equals the recomputation is NOT flagged and one whose `lift_vector` was tampered IS; mutation: restore the ladder -> the clean anchor is flagged
- **Output change:** yes - the 34-of-56 inflation flags on the other chart would disappear on rebuild
- **Blast radius:** `ph_suddha_sodhana` status counts (36 `staged_revision` on that chart), `ph_phaladesa` clean counts
- **Rebuild:** needs production rebuild
- **Gate it moves:** Earn
- **Fix class:** writer code (engine); **risk class:** R3; **buildable before J1:** tier-dependent
- **Decision:** OPEN - Q-L4-05, Q-L4-12

### FD-3 - Tighten the near-tautological detectors and the chart-wide anchor choice

- **Answers:** G03, G06
- **Change:** `falsifier_absent`: require BOTH tokens (matches its docstring) - or keep `any` and fix the docstring; `ledger_gap`: require the keys the engine actually writes (`posterior_inputs`, `axes_applied`); chart-wide records: attach to a deterministic sentinel (e.g. the lowest anchor_id) AND say "chart-wide" in `detected_field`, or store with `anchor_id` NULL if the schema allowed it (it does not: NOT NULL).
- **Files / declaration / migration:** `platform/python-sidecar/services/ph_sodhana/engine.py:219-261,327,381`
- **Failing-first test and mutation:** failing-first: a falsifier with only "CONFIRMED" is flagged; a ledger without `posterior_inputs` is flagged; mutation: restore `any` -> not flagged
- **Output change:** yes - new flags on malformed anchors only
- **Blast radius:** none on current data (all four stored falsifiers contain both tokens)
- **Rebuild:** rides FD-1
- **Gate it moves:** Earn
- **Fix class:** writer code (engine); **risk class:** R2; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### FD-4 - Count accepted rows

- **Answers:** G05; CF-L4-06
- **Change:** Increment `rows_inserted` only when `cur.rowcount == 1`, as `ph_nimitta:287-290` does.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_sodhana.py:85-96`
- **Failing-first test and mutation:** failing-first: a duplicate-key flag yields rows_inserted 1 not 2; mutation: restore the unconditional increment -> fails
- **Output change:** none
- **Blast radius:** build record only
- **Rebuild:** none
- **Gate it moves:** Build (completion)
- **Fix class:** writer code; **risk class:** R1; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### FD-5 - Registry edge and declarations

- **Answers:** G07, G09, G10; CF-L4-07, CF-L4-10
- **Change:** Drop or justify the `bo_laksana` edge; declare `prose_fields` evidence for `recommendation_text` and a `null_convention` for `leakage_class`; Dens declaration is CF-L4-11.
- **Files / declaration / migration:** registry migration + `asset_declarations.json`
- **Failing-first test and mutation:** failing-first: Build.dag reads-match PASS after the edge change; mutation: add a `bodha_msr_signals` read without the edge -> FAIL
- **Output change:** none
- **Blast radius:** ordering only
- **Rebuild:** none
- **Gate it moves:** Build, Null
- **Fix class:** registry/declaration; **risk class:** R2; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L4-01** - *this asset:* rebuild wave 8 (after `ph_nimitta`)
- **CF-L4-03** - *this asset:* the silent-clean chain starts here (0 rows -> suddha `clean` -> phaladesa "passed clean sodhana review")
- **CF-L4-04** - *this asset:* ceiling inputs are constants upstream
- **CF-L4-06** - *this asset:* unconditional `rows_inserted += 1`
- **CF-L4-07** - *this asset:* declared-unread `bo_laksana`
- **CF-L4-09** - *this asset:* UUID: confirmed hit 2026-07-11, fixed; encoder copy-pasted
- **CF-L4-10** - *this asset:* Null/Narr INCONCLUSIVE on an empty table
- **CF-L4-11** - *this asset:* Dens FAIL

## 5 - Semantic fingerprint contract (for the rebuild plan)

Natural key `(anchor_id, anomaly_type, detected_field)` (the table's UNIQUE constraint; `chart_id` is not in it, anchors are chart-unambiguous). Fingerprint over `(anchor_id, anomaly_type, anomaly_severity, detected_field, expected_value_text, observed_value_text)`; `sodhana_id` and `computed_at` excluded. Deterministic given the anchor table. The expected rebuild result on a 4-anchor chart is the empty set today (G01) - a fingerprint test must assert the coverage record once FD-1 lands, not the empty set.

## 6 - Preserved kernel, carriage check, opportunities

- **Preserved kernel:** `LeakageFirewallError` build halt, `auto_action = stage_for_review` enforced in DB and engine, the null/empty-basis closure (F-14), the genuine-zero robustness fix (F-12), the `check_basis` tag on the proxy detector, pure DB-free engine.
- **Carriage check (T4 4.1; one only):** D3: re-run the engine over the stored `phala_anchors` of the chart and compare to the table (it is deterministic); seed a leaking anchor and confirm the halt. A D1 check does not apply.
- **By design, stated and not flagged:** The leakage firewall halting the build on an L5 `confidence_basis` is the NO-SCORING constraint made executable and is stated, not flagged. No floor by design. `auto_action` is always `stage_for_review`.
- **Opportunities (never blocking):** record the chart-level coverage (n anchors, detectors run); recompute-and-compare `posterior` instead of a ceiling.

## 7 - Decisions applied, questions for SS, Track I items arising

No decision has been applied: SS has not yet answered the A.L4 questions. This brief raises:

- **Q-L4-01** - Rebuild authority and order (see INDEX).
- **Q-L4-05** - Should an L4 asset recompute and compare a stored score (D3) instead of checking a ceiling from a superseded model?
- **Q-L4-12** - What must `ph_sodhana` write when no chart-wide check can run, and should `ph_sodhana` and `ph_suddha_sodhana` be one asset (T2 6.5 overlap investigation)?

**Track I items arising (see INDEX section 8):** TI-L4-01, TI-L4-04, TI-L4-15, TI-L4-16, TI-L4-17, TI-L4-18.

