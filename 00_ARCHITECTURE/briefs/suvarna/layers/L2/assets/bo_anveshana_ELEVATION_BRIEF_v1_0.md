---
asset_id: bo_anveshana
layer: L2 Bodha (bo_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L2 (briefs, dispositions, designs)
census_revision_used: "after-grant census `00_ARCHITECTURE/briefs/suvarna/layers/census/after_reader_grant/census_L2.json` (generated 2026-09-30T20:30:56+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). It differs from the first run (`census/census_L2.json`, 20:23:30) in exactly six cells (bo_anveshana, bo_sangati, bo_upaya: Build.completion and Count.floor, ERRORED then). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L2/L2_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16); FD-1 and FD-2 are output changes: SS (R5)"
nirmana_freeze: "t2, 2026-09-10"
decisions_applied: "SS decision N-59 (2026-10-01) on DECISION_SHEET_L2_v1_0.md (PR #2841); items marked (R) provisional until J1; section 8 lists the rulings for this asset"
track_i_items: [TI-L2-10, TI-L2-13, TI-L2-14, TI-L2-25, TI-L2-29]
ledger_gap_ids: [bo_anveshana-Earn.build_record, bo_anveshana-Cost.baseline, bo_anveshana-Complete.depth, bo_anveshana-Build.history, bo_anveshana-Build.dep_liveness, bo_anveshana-Carr.detector]
---
# bo_anveshana — Discovery Engine: ranked non-obvious discoveries and anomalies

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Mines the other Bodha assets at build time for consequential non-obvious patterns, with four deterministic primitives (no LLM): non-obviousness scoring (high structural consequence × low surface salience), embedding-outlier detection against the ayanamsha centroid (reads `bodha_signal_embeddings`, i.e. `bo_samskara`), within-chart Nσ distributional anomalies (σ threshold 2.0) and broker detection on CGM nodes (`bo_anveshana.py` docstring and constants `:37-39`). "ANTI-DRIFT ABSOLUTE: every discovery REFERENCES substrate ids — never restates values". `@register("bo_anveshana")` at `bo_anveshana.py:782`, chart deletes of `bodha_discoveries` and `bodha_anomalies` at `:821-822`. Live count 4,437 is the two-table `count_sql` (floor 500, seed 5,770); `bodha_discoveries` alone holds 3,695 rows table-wide, 30 columns, 28 fully populated. Served by `query_discoveries.ts` and `query_contradictions.ts` (21 of 28 built columns); the discovery's own `epistemic_jsonb`, `falsifier_jsonb`, `reasoning_chain_jsonb`, `provenance` and `engine_version` are dark by default. Dependents `bo_chart_gestalt`, `bo_pramana_mapa`, `ph_nimitta`. Frozen under the t2 definition (2026-09-10).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1908` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_anveshana.py:782`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_discoveries`; count_sql tables: `bodha_discoveries`, `bodha_anomalies` | census CEN-R |
| live rows / floor | 4437 / 500 (chart 482012f1, count_sql scope) — count_sql names `bodha_discoveries` + `bodha_anomalies` (4,437 on the chart) | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_sangati`, `bo_karanajala`, `bo_samskara`, `bo_drishti`, `bo_bimba`, `bo_laksana` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 3 / transitive 21; seed-derived closure (post-1210): direct 3 / transitive 21; direct dependents: `bo_chart_gestalt`, `bo_pramana_mapa`, `ph_nimitta` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_discoveries`: 17 non-test py/ts/tsx files reference it (14 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `ph_nimitta.py`, `engine.py`, `route.ts`, `fixtures.ts`, `assetClearSpec.ts`, `register_d8_assess_domain.ts` +8 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 2 capability module(s): `L2_bodha/query_contradictions.ts`, `L2_bodha/query_discoveries.ts`; `density_contract` declared on 1 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t2, 2026-09-10; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 684b404f complete/build (2026-09-10) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_discoveries (bo_anveshana.py:821), bodha_anomalies (bo_anveshana.py:822) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Build | Build.history | PARTIAL | latest run complete, but 24 error(s) and 11 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) bo_samskara did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 5/6 declared dependencies lit at chart 482012f1 (or global); stale: ['bo_drishti (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 684b404f complete/build (2026-09-10) |
| Complete (information) | Complete.depth | PARTIAL | 3695 rows, 30 cols; fully populated 28; NEVER populated ['calibration_hook', 'novelty_class_id'] |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 21/28 built column(s) (75.0%) selected by 2 capability module(s); dark: ['chart_id', 'cross_subsystem_root', 'engine_version', 'epistemic_jsonb', 'falsifier_jsonb', 'provenance', 'reasoning_c… |

Census emits **no cell** (absent, not N/A) for: Ldgr.source_presence (MF-L2-003, register R128).

**PASS cells (compact):** Vocab.identity (declared key (discovery_id): 0 duplicate(s)); Dens.served† (2 module(s): query_contradictions.ts, query_discoveries.ts; declaring density_contract: 1); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=4437 = live=4437 (count_sql total over 2 table(s): bodha_discoveries, bodha_anomalies; chart 4820…); Build.exercised (38 executed run(s) of 93 build_run_assets row(s), scope(s): asset, asset_set, global, layer, last executed 202…); Count.floor (count_sql total=4437, floor=500, delta=+3937).

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **PARTIAL** — 4 module(s) reach it by code: L2_bodha/query_contradictions.ts, L2_bodha/query_discoveries.ts, L5_mimamsa/query_mimamsa_discoveries.ts, register_d8_assess_domain.ts; a referencing capability declares density_contract but L2_bodha/query_discoveries.ts: tier carriage not established (a run; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** PASS (not in the recompute's L2 gate-diff list; no change from the saved rev-1 PASS) The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| code: `bo_anveshana.py:416-430` | Null / Narr | real-or-SS-question | every discovery stores `epistemic_jsonb = {"confidence": round(min(consequence + 0.1, 1.0), 3), "ayanamsha_fragility": "low"}` and `falsifier_jsonb = {"falsifier": "Compare against L3 Kāla LEL event outcomes for predicted domain", "calibration_hook": "empty — L4/L5 fill with observed outcome"}`: the confidence is the consequence score plus a constant, `ayanamsha_fragility` is the literal `low` on every row, and the falsifier is one constant sentence for every hypothesis. T1 §13 (no invented confidence or score) and CLAUDE.md §N.7 item 6 / §N.8 (a flag without a detector is null, not green) bear on all three; the census has no Null check on them (both columns are dark in the served view). FD-1. |
| code: `bo_anveshana.py:509`, `:585`, `:648`, `:732`; declarations `prose_fields` (4) | Narr | real-or-SS-question | `why_an_acharya_misses_it` is composed by f-string at four sites; its numeric parts restate computed scores (`sal_norm`, `consequence_score`, `dist`, `sigma`), but the claims "falls below acharya's attentional threshold", "invisible to pattern-matching" and "easy to miss when chart is read holistically" are not derived from any cited fact or stated threshold. CLAUDE.md §N.7 items 1 and 6: restate the cited numbers, drop or define the claim. The column is the engine's headline output, so the ruling matters. FD-2. |
| census: no `Ldgr.source_presence` cell (MF-L2-003) | Ldgr | detector | the table has no recognised citation column; its provenance is `constituent_refs_jsonb` (signal ids) and `provenance`/`reasoning_chain_jsonb` (dark). Declare the carrying column. CF-08. |
| census: registry `natural_key_partition` | Idem | real (registry) | blank (MF-L2-009), though the writer replaces two tables chart-wide. CF-03. |
| census cell Dens.served † (offline rev 4 PARTIAL) | Dens | detector (rev 4 PARTIAL) | saved rev-1 PASS (1 of 2 modules declares a contract); the offline rev-4 scan reads PARTIAL for `query_discoveries.ts`: contract declared, "tier carriage not established (a run-time select)". CF-04. |
| census cell Complete.depth (information) | Complete (information) | information | NEVER populated: `calibration_hook`, `novelty_class_id` (L5 and a novelty vocabulary; NULL by design at L2). CF-17. |
| `bo_anveshana-Build.dep_liveness` | Build (dep_liveness) | history/ordering | 5 of 6 declared dependencies lit; `bo_drishti` stale (built, upstream moved since). CF-10 / §7. |
| `bo_anveshana-Build.history` | Build (history) | history | latest run complete; 24 errors and 11 aborts on record (latest error 2026-08-12, `BLOCKED: upstream bo_samskara did not complete`). CF-10. |
| `bo_anveshana-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |

## 3 · Disposition

**keep (P)** — the engine is complete on the census; its real shortfalls are two honesty questions on stored text and numbers (an invented-looking confidence/fragility/falsifier and an acharya-attention claim) which are bounded writer changes and output changes (SS), not reasons to reshape the asset. The primitives and their substrate-id references are the preserved kernel.

Approver under Track A brief §10: **Steward (G16); FD-1 and FD-2 are output changes: SS (R5)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Earn or null the stored confidence, fragility and falsifier

- **SS ruling (N-59, 2026-10-01):** `confidence`, `ayanamsha_fragility` and `falsifier` are NULL now; the acharya-attention claim in `why_an_acharya_misses_it` is dropped or defined (numbers kept). Computing fragility (does the discovery hold in all five ayanamshas) is a post-J1 improvement item. Batched. TI-L2-25, TI-L2-29.
- **Answers:** the Null/Narr observation on `epistemic_jsonb` and `falsifier_jsonb`; T1 §13; CLAUDE.md §N.8
- **Change:** either (a) store NULL (or omit the keys) for `confidence`/`ayanamsha_fragility` until a detector exists, and let the served layer say "not computed"; or (b) compute them from something measured (for `ayanamsha_fragility`, the discovery's presence across the five ayanamshas, `corroboration_count`, which the writer already holds; for the confidence, a documented monotone function with its decision id, never `consequence + 0.1`); give each discovery class its own falsifier text naming the L3/L4 outcome class it would be compared to, or NULL
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/bo_anveshana.py` (`:416-430`)
- **Failing-first test and mutation:** failing-first: no stored `ayanamsha_fragility` literal equals `low` on a discovery present in one ayanamsha only; the confidence is NULL or equals the documented function; mutation: restore the constants → the test fails
- **Output change:** yes: `epistemic_jsonb`, `falsifier_jsonb` values change on every discovery row: SS (R5)
- **Blast radius:** output change: this asset's registry dependents see new values after the rebuild (direct 3: `bo_chart_gestalt`, `bo_pramana_mapa`, `ph_nimitta`; transitive 21)
- **Rebuild:** needs production rebuild of `bo_anveshana` (idempotent per-chart delete-then-insert) and then `bo_chart_gestalt` and `bo_pramana_mapa`, which read it: REVIEW item for SS
- **Gate it moves:** Null (NO_DETECTOR → measured)
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-dependent: the Null rule for a derived confidence (SS 2026-10-01) and the ruling
- **Question for SS:** Null the stored confidence/fragility/falsifier until earned, or define them (and by what measured function)?

### FD-2 · State only what the cited numbers support in `why_an_acharya_misses_it`

- **SS ruling (N-59, 2026-10-01):** `confidence`, `ayanamsha_fragility` and `falsifier` are NULL now; the acharya-attention claim in `why_an_acharya_misses_it` is dropped or defined (numbers kept). Computing fragility (does the discovery hold in all five ayanamshas) is a post-J1 improvement item. Batched. TI-L2-25, TI-L2-29.
- **Answers:** the Narr observation on the four template sites
- **Change:** keep the numeric restatement (surface salience, consequence, distance, σ, subsystem count, edge count) and replace the claim about acharya attention by a defined, stated criterion (for example the salience percentile below which a signal counts as low-salience, named in the string) or drop the clause; the broker string (`:732`) already states counts and a property of the graph, which is derivable
- **Files / declaration / migration:** `bo_anveshana.py` (`:509`, `:585`, `:648`)
- **Failing-first test and mutation:** golden-value test (CF-14): each template's expected string for a fixture row is written by hand and contains only values from the row; mutation: reintroduce "acharya's attentional threshold" → the lint flags an ungrounded claim
- **Output change:** yes: the text of `why_an_acharya_misses_it` changes: SS (R5)
- **Blast radius:** output change: this asset's registry dependents see new values after the rebuild (direct 3: `bo_chart_gestalt`, `bo_pramana_mapa`, `ph_nimitta`; transitive 21)
- **Rebuild:** needs production rebuild of `bo_anveshana` and its readers (REVIEW item for SS)
- **Gate it moves:** Narr
- **Fix class:** writer code (+ SS ruling); **buildable before J1:** tier-dependent: the Narr verdict on an ungrounded claim
- **Question for SS:** Is a sentence asserting what an acharya would miss acceptable as templated narration over scores, or must the claim be defined or dropped?

### FD-3 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** a golden fixture for each of the four `why_an_acharya_misses_it` templates and the `surface_reading`/`depth_reading`/`surface_depth_delta` strings (`_make_discovery` `:414-423`): every number in the string must equal the stored score it cites
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 3: `bo_chart_gestalt`, `bo_pramana_mapa`, `ph_nimitta`; transitive 21); the touched surface is a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can f
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-4 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): re-run the non-obviousness score and the σ anomaly detector from `bodha_msr_signals` and `bodha_cgm_nodes` and compare the top-N discoveries and flagged anomalies to the stored rows; the broker degree counts are set arithmetic.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 3: `bo_chart_gestalt`, `bo_pramana_mapa`, `ph_nimitta`; transitive 21); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* blank `natural_key_partition`; seed floor 5,770 vs live 500
- **CF-08** — Ldgr: assets with no recognised citation column (no census cell). *This asset:* no Ldgr reading
- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* Dens PARTIAL (run-time select); 7 dark columns
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* declared prose (4 columns)
- **CF-17** — Complete.depth: never-populated columns (declare, populate or drop). *This asset:* never-populated columns
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL and stale upstream
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `discovery_id` (the census identity key; the registry partition is blank): the id must be a deterministic function of `(chart_id, ayanamsha_id, discovery_class, constituent signal ids)` for E5.5 (confirm with `stable_semantic_uuid` use in the writer before relying on it). Fingerprint: `discovery_class`, `non_obviousness_score`, `consequence_score`, `composite_discovery_rank`, `constituent_refs_jsonb` (signal ids resolved to signal natural keys), `affected_domains_array`, the four prose columns, `corroborating_methods_array`. **Volatile:** `discovery_id` if not deterministic, `build_id`, `computed_at`, `engine_version`. Embedding outliers depend on the embedding values (see `bo_samskara`'s equivalence policy).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the four deterministic primitives and the rule that a discovery references substrate ids and never restates values.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-4)
- **Opportunities (never blocking):** serve `reasoning_chain_jsonb`, `falsifier_jsonb` and `epistemic_jsonb` (the hypothesis's own evidence and falsifier) by default; populate `novelty_class_id` when a vocabulary exists.

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t2 on 2026-09-10 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 added no edge to this row. Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (`bo_chart_gestalt`, `bo_pramana_mapa`, `ph_nimitta`) re-run after it in DAG order; seed-derived transitive closure 21 assets. Idempotent per-chart delete-then-insert of two tables. It reads `bodha_signal_embeddings`, so it follows `bo_samskara`.

## 8 · Questions for Strategic Suvarṇa

1. FD-1: null the stored confidence/fragility/falsifier until earned, or define them with a measured function and decision id?
2. FD-2: may a templated sentence claim what an acharya would miss, or must the claim be defined or dropped?

**SS rulings (N-59, 2026-10-01; decision sheet `DECISION_SHEET_L2_v1_0.md` (PR #2841); (R) = provisional until the J1 review). The questions above are kept for the record.**

- **Q-L2-05 (R) - accepted.** `confidence`, `ayanamsha_fragility` and `falsifier` are NULL now; the acharya-attention claim in `why_an_acharya_misses_it` is dropped or defined (numbers kept). Computing fragility (does the discovery hold in all five ayanamshas) is a post-J1 improvement item. Batched. TI-L2-25, TI-L2-29.
- **Q-L2-12 - accepted.** This asset is in the CF-03 batch: the registry migration and the seed alignment (seed TO live) are pre-approved now; its floor is restated to the achieved count AFTER the one rebuild. TI-L2-10, TI-L2-24.
- **Layer-wide (Q-L2-18, Q-L2-19, sequencing).** Build.history counts only runs since the last writer or registry change (L0 Q11 carried; TI-L2-13) and Carr uses a D3 stratified sample with the section N.5 resolver, PASS only if every sampled row re-derives (L0 Q13 grading; TI-L2-14); both are read after the one coherent L2 rebuild on main's code, in which no asset is rebuilt twice.
