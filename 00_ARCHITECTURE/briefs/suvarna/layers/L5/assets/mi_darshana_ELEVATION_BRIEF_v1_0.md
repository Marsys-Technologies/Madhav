---
asset_id: mi_darshana
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
disposition_proposal_approver: "Strategic Suvarṇa (R5: served labels and templates change)"
risk_class: "high (served surface; 115 rows rewritten; consumer wrapper in platform-mcp)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-39, TI-L5-40, TI-L5-41, TI-L5-42, TI-L5-43]
ledger_gap_ids: ["mi_darshana-Build.completion", "mi_darshana-Earn.build_record", "mi_darshana-Cost.baseline", "mi_darshana-Complete.depth", "mi_darshana-Build.history", "mi_darshana-Build.dep_liveness", "mi_darshana-Carr.detector", "new: dar-N1", "new: dar-N2", "new: dar-N3", "new: dar-N4", "new: dar-N5", "new: dar-N6", "new: dar-N7", "new: dar-N8", "new: dar-N9"]
---

# mi_darshana — Insight retrieval surface: calibrated outlooks, grammar, discoveries, load-bearing and verdict objects

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

Synthesises the other L5 tables into `mimamsa_insight_units` rows: `calibrated_outlook` from `mimamsa_reliability` strata (:208-257), `manifestation_grammar` from the top 20 `empirical`/`assignment_only` grammar rows (:259-335), `emergent_law` and `retrodiction` from `mimamsa_discoveries` with the F-143 per-class grading (`_discovery_evidence_grade`, :83-139), `load_bearing` from `mimamsa_load_bearing` (:386-412), and `verdict_object` rows from L2 (`bodha_pratijna` joined to `brahma_event_ontology`, ranked evidence from `bodha_msr_signals`, contradictions from `bodha_contradictions`, concordance from `bodha_triangulation`; up to 40, :425-680). Replaces the chart's insight units and embeddings (:684-685). The `embeddings` substep logs `[EXTERNAL_COMPUTATION_REQUIRED]` and inserts nothing (:718-740); `views_verify` queries four serving views and raises if one fails (A10, :743-780). This is the only L5 table family the six named MCP tools reach directly (`mimamsa_insight_get`).

**Canonical chart state (read-only, 2026-10-03).** **115 insight units, 0 embeddings** (`ins`, `ins_emb`): calibrated_outlook 6 (4 `empirical`, 2 `prior_only`), emergent_law 20 (`empirical`), load_bearing 4 (`structural`), manifestation_grammar 7 (`empirical`), retrodiction 51 (`prior_only`), verdict_object 27 (`structural`). `leakage_status` is `clean` on 115/115 (main writes `not_assessed`). `provenance_chain.grade_basis` is absent on 115/115 (main writes it). **31 units are graded `empirical` by v1.0 code and are therefore served with numerics unsuppressed** (`query_insights.ts` `suppressIfNotCalibrated` passes `empirical` rows through): e.g. "In predictions scored [0.3, 0.4), the observed outcome rate is 0.0% across 13 events (evidence: empirical)", "For transition events, the 'ch_transition_verbal' channel fires with 0% propensity (n=55, empirical learning)", and 20 "Signal '…' shows consistent … credit (mean=0.32, n=41)" lines. On main's code none of the 20 emergent_law units would be `empirical` (no `n_scored_matches` -> `assignment_only`), none of the 7 grammar units would be `empirical`, and the 51 retrodiction units would be `structural`.

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / per_chart / pgvector | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:3025` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py:169` `@register("mi_darshana")`; heavy writer, 3 substeps (`plan_substeps` :179: insight_units, embeddings, views_verify); registry storage `pgvector` | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_insight_units`; count_sql tables: `mimamsa_insight_units`, `mimamsa_insight_embeddings` | registry / census |
| count_sql (live) | `SELECT (SELECT count(*) FROM mimamsa_insight_units WHERE chart_id = $1) + (SELECT count(*) FROM mimamsa_insight_embeddings WHERE chart_id = $1) AS count` | registry |
| live rows (canonical chart) / floor | 115 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / True / 10800s | registry |
| registry build state (canonical chart) | throughput `error`, rows_written 115, last_built_at 2026-08-21T02:36:53Z; recent canonical runs: complete 2026-08-13; complete 2026-08-07; complete 2026-07-28; complete 2026-07-28 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `mi_pramana`, `mi_adhilepa`, `mi_sambandha`, `mi_pariksha`, `mi_gunanaka`, `mi_kula`, `mi_jivanaghatana`, `bo_pratijna`, `bo_laksana`, `bo_sangati` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | none (no active asset lists `mi_darshana` in `depends_on`); census transitive blocking radius 0 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Declared (live): `mi_pramana`, `mi_adhilepa`, `mi_sambandha`, `mi_pariksha`, `mi_gunanaka`, `mi_kula`, `mi_jivanaghatana`, `bo_pratijna`, `bo_laksana`, `bo_sangati`. Actual reads: `mimamsa_reliability`, `mimamsa_manifestation_grammar`, `mimamsa_discoveries`, `mimamsa_load_bearing` (a subset of the L5 edges), `bodha_pratijna`, `bodha_msr_signals`, `bodha_contradictions`, `bodha_triangulation`, `brahma_event_ontology`. `mi_kula`, `mi_jivanaghatana`, `mi_gunanaka` edges are unread by this writer (they are reached transitively); `bo_sangati` is reached through `bodha_triangulation`. | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | Served: `query_insights.ts:225` (`mimamsa_insight_get`, wrapped by `register_p1_synthesis.ts:609-650`), `query_insight_embeddings.ts:123` (`mimamsa_insight_embeddings` — empty), views `vw_mimamsa_insight_by_domain/_horizon/_lens`, `vw_mimamsa_negative_knowledge`; consumers of `query_insights`: `receipt/assemble.ts` and the activation gate (`total_matches`). Census Dens.served PASS (2 modules with a contract). | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `tests/test_mi_darshana.py` (30 tests), `tests/test_mi_darshana_no_evidence.py`, `L5_mimamsa/__tests__/query_insights_f143_discovery_grades.test.ts`, `query_insights_p3b_suppression.test.ts`, `query_insight_embeddings.test.ts`; none runs the writer against a populated DB | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | no receipt, no freshness row for the canonical chart; digest spec present (reviewed 2026-09-08T23:41Z); natural-key partition migration 951; throughput `error` 2026-08-21 (BLOCKED on five `mi_*` upstreams), rows_written 115 = live 115; last writer execution complete 2026-08-13T01:17:18Z; every stored row carries `surface_formula_version = mi_darshana_v1.0` (main: v1.2) | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (64) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): mimamsa_insight_embeddings (mi_darshana.py:684), mimamsa_insight_units (mi_darshana.py:685) |
| Build | Build.target † | PASS | target_table=mimamsa_insight_units |
| Build | Build.dag † | PASS | 8 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | FAIL | build record state='error' is not a completed build (rows_written=115, live=115, chart 482012f1) — see Build.history; target_table mimamsa_insight_units alone: 150 row(s), whole table — context, not the compared figure |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=115) |
| Complete (information) | Complete.depth | PARTIAL | 150 rows, 18 cols; fully populated 13; NEVER populated ['horizon'] |
| Dens | Dens.served † | PASS | 2 module(s): query_insight_embeddings.ts, query_insights.ts; declaring density_contract: 2 |
| Build | Build.history | FAIL | most recent run error (2026-08-21); 33 error(s), 10 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-08-21): BLOCKED: upstream dependency(ies) mi_adhilepa, mi_gunanaka, mi_pariksha, mi_pramana, mi_sambandha did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | FAIL | 2/8 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_pramana (error, chart 482012f1)', 'mi_adhilepa (error, chart 482012f1)', 'mi_sambandha (error, chart 482012f1)', 'mi_pariksha (error, chart 482012f1)', 'mi_gunanaka (error, chart 482012f1)']; stale: ['bo_pratijna (stale, chart 482012f1)'] — a DEP-ASSE... |
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
| mi_darshana-Build.completion | Build.completion | stale | measured: build record state='error' is not a completed build (rows_written=115, live=115, chart 482012f1) — see Build.history; target_table mimams... |
| mi_darshana-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_darshana-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_darshana-Complete.depth | Complete.depth | information | measured: 150 rows, 18 cols; fully populated 13; NEVER populated ['horizon'] / required: the Complete gate's claim |
| mi_darshana-Build.history | Build.history | history | measured: most recent run error (2026-08-21); 33 error(s), 10 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-... |
| mi_darshana-Build.dep_liveness | Build.dep_liveness | stale | measured: 2/8 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_pramana (error, chart 482012f1)', 'mi_adhilepa (error, chart ... |
| mi_darshana-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: dar-N1 | Narr / Earn (served) | stale (served false claims) | 31 `empirical` units carry statements built from the superseded v1.0/v1.0/v1.0 generations of `mi_pramana`, `mi_pariksha`, `mi_sambandha` (the F-35 / F-143 / F-147 defects) and reach callers unsuppressed through `mimamsa_insight_get`. The serving-side suppression is correct but keys on the stored grade, which is the thing that is wrong. Cleared only by rebuilding the chain (CF-L5-01); until then the served wrapper (dar-N3) says `prior_only` while the rows say `empirical` |
| new: dar-N2 | Narr (fixed template) | real | the `load_bearing` template (:399-403) ends "Removing this signal would materially alter the reading." for rows that rank family prior weights (see `mi_adhilepa` adh-N1); the `calibrated_outlook` template ("the observed outcome rate is X% across N events") narrates a bin whose rate is circular (pram-N2) and whose n includes unresolved rows (pram-N3) |
| new: dar-N3 | Earn (served label) | real (consumer) | `register_p1_synthesis.ts:640-646` wraps every `mimamsa_insight_get` response with `calibration_status: 'prior_only'` and `mode: 'STRUCTURAL'` as **constants**, then spreads the inner result. They cannot read otherwise, whatever the units contain — in the same response 31 units say `evidence_grade: empirical`. STRUCTURAL mode is by design for L5 as a whole, but a per-response flag with no detector behind it is a label, not a status (§N.8); after the rebuild the two will agree only by coincidence |
| new: dar-N4 | invented fallbacks | real | `obs = observed if observed is not None else 0.5` (:238: rank_consequence 0.5 for a stratum with no rate, with a +-0.1 band), `strength = float(r.get("strength") or 0.5)` (:356: a genuine 0 becomes 0.5), `grade = _raw_grade if not None else 5.0` (:540, a neutral invented only when the grade is missing; the no_evidence path handles the common case), confidence bands from grade tiers (`g_norm -0.2/+0.1`, :611-619) — widths with no method; `rank_consequence` for verdict objects is the L2 grade / 10 |
| new: dar-N5 | embeddings | real + SS question | `mimamsa_insight_embeddings` has 0 rows by design: the substep logs `[EXTERNAL_COMPUTATION_REQUIRED]` and writes nothing, while the registry kind is `pgvector` and `query_insight_embeddings.ts` (a served capability) reads the table. CLAUDE.md section N.4 says embeddings are a deterministic transform and permitted; so the empty table is a choice, not a constraint (Q-L5-14). The asset reads `lit` with an empty second table |
| new: dar-N6 | identity | real | `insight_id` embeds the enumeration index (`cal_{stratum}_{i}`, `gram_{dom}_{ch}_{i}`, :237, :313) over queries ordered without a total key (`ORDER BY n_support DESC LIMIT 20`, :263): ids can change between rebuilds, which breaks any stored reference (e.g. `mimamsa_resonance_feedback`, which has 0 rows today) |
| new: dar-N7 | coupling | real | 12 L5-writer inputs and 4 L2 tables: the asset is the L5 summary and the L2 `verdict_object` bridge at once; a failing L2 table (e.g. `bodha_triangulation` absent) silently skips the 27 verdict objects (:424 `_table_exists`) — the one place where a missing upstream table is still a quiet skip in this layer |
| new: dar-N8 | Build.dag | real | 10 declared edges, of which 3 are unread directly (kula, jivanaghatana, gunanaka); no `lel` read; the L2 reads go through `bo_pratijna` / `bo_laksana` / `bo_sangati` (CF-L5-07) |
| new: dar-N9 | Null / Narr | detector | declarations: `prose_fields: ["statement"]` — the right field; no golden-value tests exist for the five templates (CF-L5-14) |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| `evidence_grade` | the tier of evidence behind the unit | main: F-143 per-class rule (`scored_matches_threshold` etc.); deployed: `n >= 5` | main **earned** (basis stored in `grade_basis`); deployed **unearned** for 31 units |
| `leakage_status` | no leakage into the unit | deployed `clean`; main `not_assessed` | deployed **unearned**; main honest |
| `rank_consequence` | how consequential the unit is | observed rate / prop / strength / sensitivity / grade/10 depending on type; 0.5 fallbacks | **heterogeneous**: five meanings in one column; suppressed for non-empirical rows by the server |
| `confidence_band` | interval around the value | +-0.1 or grade-tier widths | **invented widths** |
| served `calibration_status: prior_only` / `mode: STRUCTURAL` | the response is uncalibrated | constants in `register_p1_synthesis.ts:642-643` (and `calibration_mode` STRUCTURAL at `register_p1_synthesis.ts:931`) | **constant label** (dar-N3) |
| `verdict_object` statements | per-event-class verdict with ranked evidence | L2 `bodha_pratijna` grade -> note text; no-evidence branch honest | **earned restatement of an L2 fact**, with the §N.7-6 null branch (grade NULL, `no_evidence`) |
| `is_negative_knowledge` | what does not hold | literal False in this writer | no row is negative knowledge; the type exists in `_INSIGHT_TYPES` and the served enum |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD (main): no_evidence verdict objects carry grade NULL and a statement that says there is no evidence (:497-536); grade 0.0 is a real grade (P0-10 fix); `propensity_source: measured | prior_fallback` is stored; views_verify raises on a failed view (A10).
- BAD: 0.5 fallbacks (dar-N4); the served constant wrapper (dar-N3); stored `clean`.

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** `self._chart_id = ctx.config["chart_id"]` (:180) is a `uuid.UUID` on the real path; used as a SQL parameter throughout and in a log line (:711, :729, :780). `json.dumps` calls carry dicts/lists of strings and floats (`str(s)` is applied to signal ids, :510). **Not exposed.** (`views_verify` reads `r["count"]` from a default-cursor row, which assumes the orchestrator's dict-row connection factory.)
- **Outcome-leakage guard:** every unit is `leakage_status = not_assessed` on main (clean on the stored generation). The `retrodiction` class says in its own grade basis that no T-90d cutoff is applied. The Paripraśna collect-only guard blocks calibration keys from served reading envelopes, not from this tool's own response (which is the declared calibration surface).
- **People-entered data (N-46) / LEL data contract:** regenerable derived table (INV `_insight_*`); no people-entered data. `mimamsa_resonance_feedback` (native feedback, 0 rows, quarantined from weights by `check-resonance-quarantine.ts`) is referenced by insight id: unstable ids (dar-N6) would orphan such feedback.

## 3 · Disposition

DISPOSITION: qualify

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/data/mi_darshana.json

EVIDENCE_EXTRA: this brief sections 0-4; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/facts2.json; 00_ARCHITECTURE/briefs/suvarna/layers/L5/assets/_evidence/rollup_saved_L5.json; 00_ARCHITECTURE/briefs/suvarna/layers/census/census_L5.json

**qualify (Q)** — the grading logic on main is the best-reasoned in the layer, but production holds the older generation, the served wrapper is a constant, templates narrate unearned numbers, and the embedding half of the asset is declared and empty. Qualify = rebuild after the chain, fix the wrapper and templates, decide embeddings.

Approver under Track A brief section 10: **Strategic Suvarṇa (R5: served labels and templates change)**. Risk class: **high (served surface; 115 rows rewritten; consumer wrapper in platform-mcp)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023). No disposition is applied by this brief.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Rebuild on current code after the upstream chain; bump the version label

- **Answers:** dar-N1; CF-L5-01; Q-L5-03
- **Change:** no code change: the F-143 / F-147 logic is on main. Require the build order jivanaghatana -> bhavisya -> pramana -> (gunanaka, pariksha) -> sambandha -> adhilepa -> darshana, and bump `SURFACE_FORMULA_VERSION` for any template change below
- **Files / declaration / migration:** none (rebuild); `mi_darshana.py:36` label
- **Failing-first test and mutation:** the existing F-143 tests plus a post-rebuild assertion: no `empirical` unit lacks `grade_basis`; no served statement contains 'Blind retrodiction'
- **Output change:** yes: 31 units lose `empirical`; 51 retrodiction units regraded -> SS (R5)
- **Blast radius:** mimamsa_insight_get callers
- **Rebuild:** needs production rebuild of the chain (REVIEW)
- **Gate it moves:** Earn, Narr
- **Fix class:** rebuild; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-39

### FD-2 · Compute the served calibration status instead of a constant (R)

- **Answers:** dar-N3; CF-L5-10; Q-L5-10
- **Change:** derive `calibration_status` and `mode` in `mimamsa_insight_get` from the returned units (lowest present grade tier; STRUCTURAL unless at least one `empirical` unit with a chronology-clean `grade_basis` exists) and from the activation-gate sample basis (Q-L5-11)
- **Files / declaration / migration:** `platform-mcp/src/tools/register_p1_synthesis.ts:630-650`
- **Failing-first test and mutation:** failing-first: a response containing only `prior_only` / `structural` units reports STRUCTURAL; one with a verified `empirical` unit does not; mutation: restore constants -> FAIL
- **Output change:** yes: served envelope fields -> SS (R5)
- **Blast radius:** all mimamsa_insight_get callers
- **Rebuild:** none (TS)
- **Gate it moves:** Earn (served)
- **Fix class:** served surface (TS); **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-40

### FD-3 · Remove narration without a detector; no 0.5 fallbacks (R)

- **Answers:** dar-N2, N4; CF-L5-04
- **Change:** drop the counterfactual sentence (with mi_adhilepa FD-1); `rank_consequence` NULL (or the unit is omitted) when the stratum has no rate; `strength` NULL stays NULL; document `rank_consequence` per type or split it
- **Files / declaration / migration:** `mi_darshana.py:215-257,356,399-412`
- **Failing-first test and mutation:** failing-first: no `0.5` rank for a no-rate stratum; golden-value tests for the five templates (CF-L5-14); mutation: restore -> FAIL
- **Output change:** yes: some units change text or lose a number -> SS (R5)
- **Blast radius:** query_insights, suppressIfNotCalibrated
- **Rebuild:** needs rebuild
- **Gate it moves:** Narr, Null
- **Fix class:** writer code; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-41

### FD-4 · Stable insight ids

- **Answers:** dar-N6
- **Change:** build ids from a content key (stratum / channel / discovery id), not the enumeration index; total ORDER BY on every LIMIT
- **Files / declaration / migration:** `mi_darshana.py:237,263,313`
- **Failing-first test and mutation:** failing-first: two builds over unchanged inputs give identical ids; mutation: restore the index -> ids differ when order ties break differently
- **Output change:** id strings change once
- **Blast radius:** resonance feedback references (0 rows)
- **Rebuild:** needs rebuild
- **Gate it moves:** Idem
- **Fix class:** writer code; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-42

### FD-5 · Decide the embedding half (R)

- **Answers:** dar-N5; Q-L5-14
- **Change:** option A: implement the deterministic embedding write (the sidecar embedding service exists for `bg_texts`) so `query_insight_embeddings` has data; option B: declare embeddings out of this asset, mark the table and capability `not_built`, and let the asset read as structural for that half
- **Files / declaration / migration:** `mi_darshana.py:718-740`; registry `storage_type`
- **Failing-first test and mutation:** A: failing-first: every unit has an embedding row, deterministic across runs; B: the capability returns an explicit `not_built` reason
- **Output change:** A adds rows; B changes a label
- **Blast radius:** query_insight_embeddings
- **Rebuild:** A needs rebuild
- **Gate it moves:** Complete, Build.completion
- **Fix class:** writer code or declaration; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-43

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-01** — dar-N1: 31 empirical units from superseded code
- **CF-L5-03** — calibrated_outlook rests on retrospective matches
- **CF-L5-04** — rank_consequence heterogeneity, 0.5 fallbacks
- **CF-L5-07** — dar-N8
- **CF-L5-10** — dar-N3: constant wrapper; activation gate reads total_matches
- **CF-L5-11** — no canonical receipt
- **CF-L5-12** — Build.history cascade
- **CF-L5-14** — prose_fields declared; golden tests

## 5 · Semantic fingerprint contract (for E5.5)

Chart-scoped. Stable: every column except `updated_at` and `last_calibrated_at` (`now()` on grammar and discovery rows, :324, :377); ids are enumeration-dependent until FD-4. Pin all L5 upstream generations and the L2 `bodha_pratijna` generation (`lahiri_chitrapaksha`).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the evidence-grade vocabulary (`prior_only` / `assignment_only` / `structural` / `empirical`) with a stored `grade_basis`, the no_evidence null branch, the verdict-object bridge to L2, the raise-on-failed-view guard.
- **Carriage check chosen (T4 §4.1; one only):** D3: recompute each unit's grade from its source row and `_discovery_evidence_grade` with a second implementation; check `verdict_object` grades against `bodha_pratijna.grade` for the 27 rows.
- **Opportunities (never blocking):** the four-term evidence vocabulary here is the natural layer-wide vocabulary (TG-L5-014); a `not_built` capability state would let a served tool say so without an empty table.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-03** — Authorise the production rebuild of the L5 chain (after the L3/L4 rebuild lands) so that main's corrected code replaces the 2026-08-13 rows (stale labels served today: 31 `empirical` insight units, 51 "Blind retrodiction" statements, `base_rate = 0.1` x57, 7 grammar rows at 0.0 propensity); and mark the old rows stale before the rebuild. Order: jivanaghatana -> bhavisya -> pramana -> (gunanaka, pariksha) -> sambandha -> adhilepa -> darshana. *Recommendation:* Yes, as one REVIEW-gated Track B wave after Q-L5-01/02 are ruled (otherwise the rebuild re-creates the retrospective calibration under cleaner labels). (R)
- **Q-L5-09** — Remove the counterfactual sentence "Removing this signal would materially alter the reading" and rename `role` (rank position of the classical prior) until a real ablation exists? *Recommendation:* Yes. (R)
- **Q-L5-10** — Compute `calibration_status` / `mode` in `mimamsa_insight_get` from the returned units and the gate basis instead of the constants `prior_only` / `STRUCTURAL` (`register_p1_synthesis.ts:642-643`, also `register_p1_synthesis.ts:931`)? *Recommendation:* Yes; STRUCTURAL remains the default until a chronology-clean `empirical` unit exists. (R)
- **Q-L5-11** — Activation-gate sample basis: `total_matches = COUNT(*) FROM mimamsa_calibration` (57 = 32 adjudicated = 13 distinct predictions = 0 prospective) opens the `empirically_calibrated` gate at >= 30 by code reading. Should the sample be distinct, adjudicated, chronology-clean predictions? (Paripraśna code; the data comes from L5.) *Recommendation:* Yes; coordinate with the Paripraśna owner. Until then the gate's own note says its 30 is a placeholder. (R)
- **Q-L5-14** — Embeddings: implement the deterministic embedding write for `mimamsa_insight_embeddings` (CLAUDE.md section N.4 permits embeddings as a deterministic transform) or declare the half out of scope (`not_built`) and say so in the served capability? *Recommendation:* Implement if the semantic-search capability is wanted; otherwise `not_built`. Not blocking.
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
- **Q-L5-20** — Tier vocabulary (TG-L5-014): adopt `structural / prior_only / assignment_only / empirical` (the vocabulary `mi_darshana` already stores with a `grade_basis`) as the layer vocabulary, with a named detector for each tier and one meaning of "empirical" (chronology-clean, adjudicated, independent, n >= ratified minimum)? *Recommendation:* Yes. (R)
