---
asset_id: mi_sambandha
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
disposition_proposal_approver: "Steward (G16); prior-table and band changes to Strategic Suvarṇa (R5)"
risk_class: "medium (output change on 24 rows; served insight units change)"
decisions_applied: "none for L5 yet (no L5 decision sheet answered). L0-L3 rulings are cited by analogy only where a brief says so, PROVISIONAL until J1"
track_i_items: [TI-L5-35, TI-L5-36, TI-L5-37, TI-L5-38]
ledger_gap_ids: ["mi_sambandha-Build.completion", "mi_sambandha-Earn.build_record", "mi_sambandha-Cost.baseline", "mi_sambandha-Build.history", "mi_sambandha-Build.dep_liveness", "mi_sambandha-Carr.detector", "new: samb-N1", "new: samb-N2", "new: samb-N3", "new: samb-N4", "new: samb-N5", "new: samb-N6", "new: samb-N7", "new: samb-N8", "new: samb-N9"]
---

# mi_sambandha — Manifestation grammar: per-native channel propensity from outcomes, seeded from priors

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository at `main adb0db29d`, the saved census, and read-only database queries (`suvarna_reader`, `default_transaction_read_only=on`, canonical chart 482012f1) named in the section they appear in (B.10); no figure here was invented. No SS ruling has been given on L5 yet: every disposition below is a proposal under Track A brief section 10, items marked (R) change outputs or define a verdict and are provisional until the J1 review, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa. L5 is sealed in STRUCTURAL mode by design (CLAUDE.md §E; empirical calibration values fill in as prediction-to-outcome data accrues): an empty or `prior_only` calibration value is not a defect here; a value that claims to be measured without evidence behind it is.

## 0 · Identity — what the asset is

*Line citations: `file:N`; a bare `:N` is a line of the asset's own writer, `platform/python-sidecar/pipeline/orchestrator/writers/mi_sambandha.py`, at `main adb0db29d`. Lower-case ids in backticks such as `le_basic`, `cal_retro`, `pred_window`, `gun_n` are query ids in `_evidence/facts.json` / `facts2.json` (each holds its SQL and the rows read on 2026-10-03).*

LIGHT writer (`run(ctx)`, :110). Joins `mimamsa_manifestation_sets` (one default channel per prediction) to `mimamsa_calibration` on `prediction_id` (:114-124), counts per `(domain, channel)` the opportunities, scored matches (verdict CONFIRMED / PARTIAL / REFUTED) and firings (CONFIRMED / PARTIAL and `manifestation_channel == channel`), and emits `channel_propensity = fire / opportunity` only when at least one row recorded a channel (otherwise NULL, F-147, :163). It then seeds every channel of the hard-coded `_PRIOR_PROPENSITIES` table (:88-97) that has no row, as `prior_only`. `evidence_grade` is `empirical` if scored >= 5, `assignment_only` if opportunities >= 5, else `prior_only` (:167-171). Per-chart delete-then-insert (:245).

**Canonical chart state (read-only, 2026-10-03).** **24 grammar rows: 7 `empirical` + 17 `prior_only`** (`gram`). The 7 `empirical` rows are the 7 default channels `ch_<domain>_verbal`, each with `fire_count = 0`, `scored_count = 0`, **`channel_propensity = 0` (non-NULL)**, `propensity_delta = prior - 0`, `confidence_band` of the prior +-0.1 and `citation_ref` `{"method": "fire_over_opportunity"}` (`gram_prior`, a query of this lane). The stored opportunity counts sum to **183 over 139 manifestation sets** (e.g. `ch_relationship_verbal` 49 opportunities for 18 relationship predictions; `mset_vs_opp`): the join to `mimamsa_calibration` repeats a set once per matched event. Prior propensities: 0.5 on 6 of the 7 populated channels (the `.get(channel, 0.5)` default, :164), 0.4 only on `ch_career_verbal`. The deployed rows are v1.0 output: the integer-grade `empirical` on opportunity count and the 0.0 propensity are what F-147 (v1.2) removed in code.

| field | value | source |
|---|---|---|
| kind / scope / storage (live registry) | data / per_chart / postgres_table | `asset_registry` (read-only SELECT, 2026-10-03) |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:3008` | seed (live may differ by migration; differences listed in section 2) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/mi_sambandha.py:100` `@register("mi_sambandha")`; registry `has_writer` = t | writers dir / census `Build.registered` |
| target table(s) (live registry) | `mimamsa_manifestation_grammar`; count_sql tables: `mimamsa_manifestation_grammar` | registry / census |
| count_sql (live) | `SELECT count(*) FROM mimamsa_manifestation_grammar WHERE chart_id = $1` | registry |
| live rows (canonical chart) / floor | 24 / 0 | count_sql run read-only ($1 = 482012f1); target_floor from registry |
| catalog_status / has_substeps / timeout | CURRENT / False / 10800s | registry |
| registry build state (canonical chart) | throughput `error`, rows_written 24, last_built_at 2026-08-21T02:36:53Z; recent canonical runs: complete 2026-08-13; complete 2026-08-07; complete 2026-08-07; complete 2026-07-28 | `asset_throughput`, `build_run_assets` (read-only) |
| depends_on (live) | `mi_pramana`, `mi_pariksha`, `mi_bhavisya` | registry (includes migration 1210 edges) |
| dependents (registry `depends_on`) | `mi_darshana` (registry); census transitive blocking radius 1 | registry (read-only `unnest(depends_on)`) |
| declared-vs-actual reads | Declared: `mi_pramana`, `mi_pariksha`, `mi_bhavisya`. Actual: `mimamsa_manifestation_sets` (`mi_bhavisya`) and `mimamsa_calibration` (`mi_pramana`). `mi_pariksha` is declared and not read. | code reading of the writer and its services (grep; run 2026-10-03) |
| code readers / served surface | Served: `query_manifestation_grammar.ts:108` (`marsys://tool/L5/query_manifestation_grammar`), `query_manifestation_sets.ts`; writer `mi_darshana.py:255-265` (top 20 `empirical`/`assignment_only` rows -> insight units). Census reach: 15/17 columns (0.8824, among the widest); `Ldgr.source_presence` PASS 47/47 on the saved census (presence of `citation_ref`, not correspondence). | git grep over `platform/src`, `platform-mcp/src`, `platform/python-sidecar` (tests excluded) |
| tests that name it | `tests/test_mi_sambandha.py` (14 tests: verdict vocabulary, honest-null propensity), `L5_mimamsa/__tests__/query_manifestation_sets.test.ts`; none covers the join duplication or the prior-table keys | git ls-files + test-name read (not executed) |
| receipts / freshness / digest spec | no receipt, no freshness row for the canonical chart; digest spec present (reviewed 2026-09-08T23:50Z); natural-key partition migration 953; throughput `error` 2026-08-21 (BLOCKED on `mi_bhavisya`, `mi_pariksha`, `mi_pramana`); last writer execution complete 2026-08-13T01:16:35Z; stored `grammar_formula_version` `mi_sambandha_v1.0` (main: v1.2) | `asset_provenance_receipts`, `asset_freshness`, `asset_output_digest_specs` (read-only) |
| Nirmāṇa freeze | not frozen; EGATE BLOCKED-ANCESTORS (61) (layer instance 1.1, 2026-09-30; not re-run here) | L5 layer instance section 0.3 |
| role / scoring mode | contribution (CEN `L5.scoring`); not a reference layer | census |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: saved census `census_L5.json` (generated 2026-09-30T20:24:11+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured by the current inspector (main is at REGISTRY_REVISION 16); the live registry and row counts in section 0 were re-read read-only on 2026-10-03.

`†` marks a criterion whose definition changed on main since the saved run: Build.dag rev 1 -> 2; Build.target rev 1 -> 2; Idem.pattern rev 1 -> 2; Dens.served rev 1 -> 5.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Idem | Idem.pattern † | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): mimamsa_manifestation_grammar (mi_sambandha.py:245) |
| Build | Build.target † | PASS | target_table=mimamsa_manifestation_grammar |
| Build | Build.dag † | PASS | 3 edge(s), all resolvable |
| Build | Build.count_integrity | PASS | count_sql=yes, integrity_check_sql=yes |
| Build | Build.completion | FAIL | build record state='error' is not a completed build (rows_written=24, live=24, chart 482012f1) — see Build.history |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13) |
| Count (information, D3) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=24) |
| Complete (information) | Complete.depth | PASS | 47 rows, 17 cols; fully populated 14; NEVER populated [] |
| Dens | Dens.served † | PASS | 2 module(s): query_manifestation_grammar.ts, query_manifestation_sets.ts; declaring density_contract: 2 |
| Build | Build.history | FAIL | most recent run error (2026-08-21); 29 error(s), 9 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-08-21): BLOCKED: upstream dependency(ies) mi_bhavisya, mi_pariksha, mi_pramana did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | FAIL | 0/3 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_pramana (error, chart 482012f1)', 'mi_pariksha (error, chart 482012f1)', 'mi_bhavisya (error, chart 482012f1)'] — a DEP-ASSERT trap if no writer can light them |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |

**PASS cells (compact):** Build.registered, Build.contract, Vocab.identity, Ldgr.source_presence, Build.exercised.

**Reported, not graded (NOT_GENERIC):** Reach.fields, Complete.width.

**Offline rollup** (main's `rollup_asset` rules, REGISTRY_REVISION 16, applied to the SAVED measurements; N/A reads NO_DETECTOR when no rule is declared; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L5/rollup_saved_L5.json`): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build FAIL.

**Offline Dens rev-4 static scan** (`capability_scan` + `_grade_dens` over the real source tree, no database; `offline_rollup_L5.py`): saved PASS -> PARTIAL.



## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a state a coherent rebuild in level order clears, not an asset defect; **history** = a recorded past run outcome no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **Dens rev-1 reading** = the saved Dens verdict whose meaning changed at rev 4/5; **+ SS question** = the fix changes output or rests on a ruling. Ids beginning `new:` were found by reading code and data in this lane and are in no ledger.

**2.1 Ledger rows (inspector-emitted, all OPEN at 2026-09-27) and this lane's class for each**

| ledger gap id (`asset_gaps.jsonl` @ 2a78ec64d) | criterion | class | note |
|---|---|---|---|
| mi_sambandha-Build.completion | Build.completion | stale | measured: build record state='error' is not a completed build (rows_written=24, live=24, chart 482012f1) — see Build.history / required: the Build ... |
| mi_sambandha-Earn.build_record | Earn.build_record | detector | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_sambandha-Cost.baseline | Cost.baseline | information | measured: NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run cbd6ea44 complete/no disposit... |
| mi_sambandha-Build.history | Build.history | history | measured: most recent run error (2026-08-21); 29 error(s), 9 abort(s), 0 blocked_dependency (cascade, not counted as failure). latest error (2026-0... |
| mi_sambandha-Build.dep_liveness | Build.dep_liveness | stale | measured: 0/3 declared dependencies lit at chart 482012f1 (or global); not live: ['mi_pramana (error, chart 482012f1)', 'mi_pariksha (error, chart ... |
| mi_sambandha-Carr.detector | Carr.detector | detector | measured: no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics / required: the Carr gate's claim |

**2.2 Gaps found in this lane (code and read-only data)**

| gap id | gate | class | note |
|---|---|---|---|
| new: samb-N1 | Narr / deployed-vs-code | stale (served false claim) | 7 stored rows grade `empirical` with `scored_count = 0` and propensity 0.0, and `mi_darshana` v1.0 turned them into 7 insight units served unsuppressed: "For transition events, the 'ch_transition_verbal' channel fires with 0% propensity (n=55, empirical learning)." The channel was never measured (`manifestation_channel` is NULL on 57/57 calibration rows). Code on main writes NULL and `assignment_only`; production has the older rows (CF-L5-01) |
| new: samb-N2 | counting | real | `counts[key]["opp"] += 1` per joined row (:140): a manifestation set joined to k calibration rows is counted k times, and an unmatched set once (LEFT JOIN). Opportunities are rows of a join, not predictions: 183 stored vs 139 sets. `n_support`, the `>= 5` grade tests and the confidence-band gate all inherit the inflation |
| new: samb-N3 | invented priors | real + SS question | `_PRIOR_PROPENSITIES` (:88-97) is a hand-typed table of channel probabilities (e.g. career verbal 0.40 / material 0.35 / relational 0.25; health bodily 0.50) with no source, citation or derivation; `prior_propensity` is NOT NULL, so the schema forces a number on every row, and `.get(channel, 0.5)` (:164) invents 0.5 for any channel the table does not list — 6 of the 7 channels `mi_bhavisya` actually produces. The registry already holds a different, unread constant for this purpose: `brahma_formula_constants.mi_sambandha_channel_priors` (per-domain dasha / signal / transit propensities, e.g. career 0.35 / 0.40 / 0.25; `git grep` finds no reader), so two prior tables exist and the writer uses neither. Under the SS citations rule the hand table is `unsourced` (Q-L5-04) |
| new: samb-N4 | vocab | real | channel ids written by `mi_bhavisya` (`ch_{domain}_verbal`) do not match the ids in the prior table (`ch_career_verbal` / `ch_career_material`, `ch_fin_income`, `ch_spirit_practice`, ...): 17 `prior_only` rows are priors for channels no prediction was ever assigned; domains `transition`, `wealth`, `character` have no entry (CF-L5-06) |
| new: samb-N5 | Earn (confidence_band) | real | `confidence_band` = prior or propensity +-0.1 whenever n >= 5 (:176-199): an invented interval width, present on rows whose propensity is 0 by default; no interval method |
| new: samb-N6 | structural dependency | real | the grammar cannot become measured until `manifestation_channel` is ever populated: `mi_pramana._score_manifestation` is a stub returning (0.5, None) (:212-214). The asset is structurally unable to leave `prior_only` / `assignment_only` — correct for STRUCTURAL mode, but only if the rows say so (F-147 does; the deployed rows do not) |
| new: samb-N7 | Build.dag | real | declared `mi_pariksha` unread; the writer's real inputs are `mi_bhavisya` and `mi_pramana` (CF-L5-07) |
| new: samb-N8 | Dens | Dens rev-1 reading | saved PASS (2 modules with a contract); rev-4/5 offline PARTIAL |
| new: samb-N9 | Ldgr | information | `citation_ref` is a method note (`{"method": "fire_over_opportunity"}`), not a source; Ldgr presence PASS 47/47 on the saved census measures non-NULL, not correspondence (CF-L5-14) |

**2.3 Earned-signal (§N.8) and narration-fidelity (§N.7) audit of this asset's flags, verdicts and numbers**

Question asked of each: what does the signal claim, and what code path would have to run and fail for it to read false? A calibration or status value with no outcome or detector behind it must be null, not a default.

| flag / value | what it claims | what actually produces it | reading |
|---|---|---|---|
| `channel_propensity` | the channel's firing rate | main: `fire/opp` only if a channel was ever recorded, else NULL (:163); deployed: 0.0 | main **earned null**; deployed **invented 0.0** |
| `evidence_grade = empirical` | learned from outcomes | main: scored >= 5; deployed: opportunity count >= 5 | main: a count of adjudicated rows (still pseudo-replicated by the join); deployed: **unearned** |
| `prior_propensity` | the classical prior for the channel | hand-typed table, default 0.5 | **unsourced / invented** for 6 of 7 channels |
| `confidence_band` | interval around the propensity | +-0.1 around prior or rate (:176-199) | **invented width** |
| `fire_count`, `scored_count`, `opportunity_count` | counts | join row counts | opportunity inflated (183 vs 139); fire structurally 0 |
| `propensity_delta` | learned minus prior | `propensity - prior` or NULL (:165) | deployed rows: -0.4 / -0.5 from an invented 0.0 vs an invented prior |

**2.4 Honest-null cases (where the asset already tells the truth, and where it does not)**

- GOOD (main): NULL propensity with a machine-readable reason (`propensity_null_reason = no_manifestation_channel_recorded`, :188-190), `is not None` rather than `or` (a real 0.0 survives), an explicit comment explaining why.
- BAD (deployed + schema): production still holds the invented 0.0; `prior_propensity NOT NULL` forces a number where none is sourced.

**2.5 Known-defect checks requested by the lane brief**

- **UUID `chart_id` into `canonical_json` / `json.dumps` / `stable_uuid` (the ga_* and bo_* class):** `chart_id: str = ctx.config["chart_id"]` (:113) is a `uuid.UUID` on the real path; used only as a SQL parameter and in the row tuples. `json.dumps(citation)` (:201) carries a dict of strings/ints (no chart id). **Not exposed.**
- **Outcome-leakage guard:** no leakage handling: the grammar consumes `mimamsa_calibration` as is (retrospective matches, CF-L5-03); the only filter is verdict vocabulary.
- **People-entered data (N-46) / LEL data contract:** regenerable derived table; no people-entered data.

## 3 · Disposition

**qualify (Q)** — the logic is already mostly honest on main (v1.2), but the production rows are the dishonest generation, the opportunity count is inflated by a join, and the priors are an unsourced hand table. Qualify = fix the count, source or drop the priors, rebuild.

Approver under Track A brief section 10: **Steward (G16); prior-table and band changes to Strategic Suvarṇa (R5)**. Risk class: **medium (output change on 24 rows; served insight units change)**. SS decision: none yet (provisional proposal; the layer instance assigns no disposition, TG-L5-023).

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Count predictions, not join rows

- **Answers:** samb-N2
- **Change:** aggregate opportunities as `COUNT(DISTINCT prediction_id)` per `(domain, channel)` and scored/fired as distinct adjudicated predictions
- **Files / declaration / migration:** `mi_sambandha.py:114-150`
- **Failing-first test and mutation:** failing-first: a set joined to 5 calibration rows counts once; mutation: restore per-row increments -> 5
- **Output change:** yes: `opportunity_count` 183 -> 139 and the n >= 5 gates -> SS (R5)
- **Blast radius:** mi_darshana grammar units
- **Rebuild:** needs production rebuild (REVIEW)
- **Gate it moves:** Earn
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-35

### FD-2 · Source or drop the priors; stop defaulting to 0.5 (R)

- **Answers:** samb-N3, N4, N5; CF-L5-05; Q-L5-04
- **Change:** either (a) cite each prior (A.L0 text index; state `unsourced` / `sourced_ocr_unverified` per the citations rule) and derive default channel ids from the same table `mi_bhavisya` uses, or (b) write `prior_propensity` NULL for channels without a source (needs `prior_propensity` nullable — an additive migration); drop the +-0.1 band or compute a Wilson interval from distinct predictions
- **Files / declaration / migration:** `mi_sambandha.py:88-97,164,176-199`; `mi_bhavisya.py:202`; additive migration
- **Failing-first test and mutation:** failing-first: an unlisted channel gets NULL, not 0.5; mutation: restore `.get(..., 0.5)` -> FAIL
- **Output change:** yes: prior and band columns on up to 24 rows -> SS (R5)
- **Blast radius:** mi_darshana, query_manifestation_grammar
- **Rebuild:** needs production rebuild (REVIEW)
- **Gate it moves:** Null, Ldgr
- **Fix class:** data (output change) + writer code + additive migration; **buildable before J1:** tier-independent once SS rules
- **Track I item:** TI-L5-36

### FD-3 · Rebuild on current code and bump the version label

- **Answers:** samb-N1; CF-L5-01
- **Change:** the code on main (v1.2) is already correct for the propensity; the fix is the rebuild after the upstream chain, and a version bump whenever behaviour changes
- **Files / declaration / migration:** none in code beyond FD-1/2
- **Failing-first test and mutation:** the existing v1.2 tests; add a test that a 0-scored group never grades `empirical`
- **Output change:** stored rows change (7 rows lose the 0.0 and the grade)
- **Blast radius:** mi_darshana units
- **Rebuild:** needs production rebuild (REVIEW)
- **Gate it moves:** Earn
- **Fix class:** rebuild only; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-37

### FD-4 · Declare the real reads

- **Answers:** samb-N7; CF-L5-07
- **Change:** drop `mi_pariksha`, add nothing (the writer reads only mi_bhavisya and mi_pramana outputs)
- **Files / declaration / migration:** registry migration
- **Failing-first test and mutation:** reads-match; mutation: re-add edge -> unread-edge report
- **Output change:** none
- **Blast radius:** DAG
- **Rebuild:** none
- **Gate it moves:** Build.dag
- **Fix class:** registry; **buildable before J1:** tier-independent
- **Track I item:** TI-L5-38

### Landed or in flight (not designs of this lane)

No Track I I-item touches this asset (checked against the L5 layer instance and the L0-L3 INDEX files).

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L5-01** — samb-N1: the served false claims are the v1.0 rows
- **CF-L5-03** — inherits retrospective matches
- **CF-L5-04** — grade / band / propensity
- **CF-L5-05** — invented priors and band width
- **CF-L5-06** — channel id vocabulary
- **CF-L5-07** — samb-N7
- **CF-L5-10** — insight units copy the sentence
- **CF-L5-11** — no canonical receipt
- **CF-L5-14** — citation_ref is a method note

## 5 · Semantic fingerprint contract (for E5.5)

Chart-scoped. Stable: all columns except `updated_at`. Depends on `manifestation_sets` and `calibration` generations; pin both. The `_PRIOR_PROPENSITIES` table is code: any change must bump `GRAMMAR_FORMULA_VERSION`.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the fire / opportunity / scored decomposition, the NULL-propensity-with-reason rule (v1.2), the verdict vocabulary fix (F-147), the separation of `assignment_only` from `empirical`.
- **Carriage check chosen (T4 §4.1; one only):** D3: recompute fire / opportunity / scored per channel from `mimamsa_manifestation_sets` and `mimamsa_calibration` with a second implementation using distinct predictions; D1 does not apply to the hand priors until they carry sources.
- **Opportunities (never blocking):** record the manifestation channel at adjudication time (it is the only way this table can ever hold a measured rate); the prior table could be the `unsourced` baseline that is replaced channel by channel.

## 7 · Decisions applied and open questions

No SS ruling exists for L5 at the time of writing. The L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A) and the L3 carry-over ruling (Q-L3-16) are the nearest precedent and are cited **by analogy only**; whether they carry to L5 is Q-L5-19 in the INDEX. Citations rule (SS, all layers, 2026-10-01): an OCR hit not checked against print is `sourced_ocr_unverified`; a passage not found is `unsourced`; only a citation verified at passage level counts toward Ldgr PASS.

Questions put to Strategic Suvarṇa (consolidated in `INDEX.md` section 9):

- **Q-L5-01** — Chronology gate: may a prediction/event match enter calibration (`mimamsa_calibration`, `mimamsa_reliability`, learned multipliers, the activation-gate sample) only if the event's `recorded_at` and `event_date` are on or after the prediction's `emitted_at`, with earlier matches kept as a separately labelled retrodiction class? (53 of 53 resolvable matches today pre-date emission.) *Recommendation:* Yes. On the canonical chart this takes calibration rows 57 -> 0 and bins 6 -> 0, which is the honest STRUCTURAL state; real values then fill in as prospective outcomes accrue. (R)
- **Q-L5-03** — Authorise the production rebuild of the L5 chain (after the L3/L4 rebuild lands) so that main's corrected code replaces the 2026-08-13 rows (stale labels served today: 31 `empirical` insight units, 51 "Blind retrodiction" statements, `base_rate = 0.1` x57, 7 grammar rows at 0.0 propensity); and mark the old rows stale before the rebuild. Order: jivanaghatana -> bhavisya -> pramana -> (gunanaka, pariksha) -> sambandha -> adhilepa -> darshana. *Recommendation:* Yes, as one REVIEW-gated Track B wave after Q-L5-01/02 are ruled (otherwise the rebuild re-creates the retrospective calibration under cleaner labels). (R)
- **Q-L5-04** — Constants: ratify as named documented approximations (in `brahma_formula_constants`) the engineering thresholds and weights (verdict 0.65 / 0.35, composite weights, bin width 0.1, n >= 5, k = 5, cap 3, n >= 3 promotion, discovery 3 / 0.15 / 20) — and drop (NULL) the invented priors and missing-term defaults (mi_sambandha channel priors and the 0.5 default, +-0.1 bands, 0.5 / 1.0 fallbacks)? *Recommendation:* Thresholds and weights: ratify as named constants (ask the L3 Q-L3-01 precedent: option 1). Invented priors, bands and defaults: option 2, NULL / `unsourced`. (R)
- **Q-L5-06** — Vocabulary authority: which L0 map joins prediction domains (transition, wealth, spirituality, character, ...) to LEL categories (finance, spiritual, psychological, residential+travel, ...) and channel ids to domains? Class-aware resolvers (L0 Q4 precedent) or a new map? *Recommendation:* One L0 map in `bg_ontology` with class-aware resolvers; unmapped = NULL (not 0). (R)
- **Q-L5-17** — depends_on corrections (Track I D-1 class): add `lel_events` to the three LEL readers; add / remove the edges listed in INDEX CF-L5-07 (including the unread `ph_pramana`, `ph_phaladesa`, `bg_ghatana`, `bg_rules`, `ka_kshetra`, `mi_pariksha` edges and the unread-declared reads of `phala_anchors`, `mimamsa_predictions`); move `_signal_family_key` out of `mi_adhilepa`. Accept the batch as one registry migration? *Recommendation:* Yes, as one reviewed batch; precedent Q-L3-08 (unread build-time edges are removed).
- **Q-L5-19** — Do the L0 rulings of 2026-10-01 (Q1 completion by count, Q2 Dens applicability, Q11 Build.history window, Q13 Carr D1 / N-A by cause) and the L3 carry-over (Q-L3-16) carry to L5, provisionally until J1? Several L5 cells (Dens on platform-mcp readers, Build.history cascades, Carr N/A for user data) depend on it. *Recommendation:* Yes, by analogy, provisionally; with `user_data` and `ratified_judgment` as N/A causes for SS approval.
