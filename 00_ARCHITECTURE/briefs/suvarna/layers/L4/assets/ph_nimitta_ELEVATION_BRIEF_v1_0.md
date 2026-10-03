---
asset_id: ph_nimitta
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
disposition: "qualify (Q) - fix + rebuild; no consolidation or retirement proposed"
disposition_proposal_approver: "Steward (G16); any output change to SS (R5)"
disposition_value: qualify
risk_class: "R4 (touches the L3->L4->L5 chain, an integrity-SQL coupling to frozen L5 rows and several SS-level semantics; the code-only fixes inside it are R1-R2)"
decisions_applied: "none - SS has not answered the A.L4 questions (INDEX section 7); all dispositions and fix designs are proposals"
ss_questions: [Q-L4-01, Q-L4-02, Q-L4-03, Q-L4-05, Q-L4-06, Q-L4-07, Q-L4-08, Q-L4-09]
track_i_items: [TI-L4-01, TI-L4-02, TI-L4-03, TI-L4-04, TI-L4-05, TI-L4-06, TI-L4-07, TI-L4-08, TI-L4-09, TI-L4-10]
ledger_gap_ids: [ph_nimitta-Build.completion, ph_nimitta-Build.dep_liveness, ph_nimitta-Build.history, ph_nimitta-Carr.detector, ph_nimitta-Complete.depth, ph_nimitta-Cost.baseline, ph_nimitta-Count.floor, ph_nimitta-Dens.served, ph_nimitta-Earn.build_record]
---
# ph_nimitta - Predictive anchors (the spine of L4 Phala)

> **PROVISIONAL - until J1; may register gaps, may not certify.** Every figure below comes from a stated read-only query (suvarna_reader SELECTs on 2026-10-03, receipts under `/Users/Dev/suvarna-evidence/A_L4/data/`), from the census, from the repository at main `3de3f8b15` (file:line), or from running the asset's pure engine functions locally with no database. Where something could not be determined it says so. Nothing here certifies a gate, approves a disposition or changes an asset.

## 0 - Identity: what the asset is

`ph_nimitta` writes `phala_anchors`: one row per derived predictive anchor, built from three upstream sources - `kala_convergence` windows (per-domain top 50, overall cap 500; `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py:37-38,306-350`), `kala_bhavishya` projections (all rows; `:352-365`) and the top 100 `bodha_discoveries` by `composite_discovery_rank` (`:39,367-411`). Each anchor carries an event type, direction, domain, horizon tier, a window, a magnitude tier, a 'posterior' (`base_rate x promise_lift x activation_lift x trigger_lift x robustness_mod`, clamped 0.02-0.95; `platform/python-sidecar/services/ph_nimitta/engine.py:289-322`), a confidence band, a falsifier and a derivation ledger. Anchors pass a T-5 clip gate (pre-birth windows rejected; stale 'near' windows rejected; `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py:804-862`), a CR-46 content dedup (`:42-87,207`) and a SPINE-FIRST gate that raises if no anchor has every elevation (`:864-884`). The identity is deterministic (`phala_anchor_identity()` called inline, `:243-245`; migration 680) and the insert is `ON CONFLICT (anchor_id) DO NOTHING` (`:260`) with an accepted-row count (`:287-290`). Delete-then-insert per chart (`:129`). Every other L4 asset reads this table (L4 layer instance 0.3); `mi_bhavisya` freezes predictions from it.

| field | value | source |
|---|---|---|
| kind | registry `asset_kind=artifact`, `asset_type=data`, `scope=per_chart`, `domain=chart`, `rung=R4`; role per L4 layer instance TG-L4-024: not assigned by any tier | `asset_registry` row, read 2026-10-03 |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2678` (live may differ by migration) | seed |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py:111`; engine `platform/python-sidecar/services/ph_nimitta/engine.py`; registry `has_writer=True` | code |
| target table(s) | `phala_anchors` | registry `target_table` / `count_sql` |
| live rows (canonical chart) / floor / build record | 4 / 139 / `rows_written=139`; rows per chart in the table(s): phala_anchors: 1c826d5a=56; 482012f1=4 | `count_sql` run read-only; `asset_throughput`; table group-by |
| state / last built | `stale` / 2026-08-13T01:16:00 UTC (run `cbd6ea44`); `built_against_writer_hash=unknown` | `asset_throughput` |
| catalog_status | CURRENT | registry |
| depends_on (declared, live) | `ka_sangam`, `ka_bhavishya_lekha`, `bo_bimba`, `bo_samskara`, `bo_karanajala`, `bo_sangati`, `bo_anveshana`, `bo_cgm_paths`, `bo_laksana` | `asset_registry.depends_on` |
| depends_on vs what the code reads | reads `kala_convergence` (`ka_sangam` declared), `kala_bhavishya` (`ka_bhavishya_lekha` declared), `bodha_discoveries` (`bo_anveshana` declared), `bodha_msr_signals` (`bo_laksana` declared), `bodha_cgm_paths` (`bo_cgm_paths` declared), `bodha_signal_embeddings` (`bo_samskara` declared), `bodha_contradictions` (producer not identifiable from the registry: no active asset has it as `target_table`), **`bodha_pratijna` at `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py:463` (`bo_pratijna` NOT declared)**, **`kala_activation_predicates` at `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py:477` (`ka_yojaka` NOT declared)** (both are the fresh census `Build.dag` FAIL: reads-match). Declared but no table read found: `bo_bimba` (`bodha_cgm_nodes`), `bo_karanajala` (`bodha_cgm_edges`), `bo_sangati`. Order still holds transitively; the edges are undeclared | code (file:line) + fresh census `Build.dag` |
| blast radius | declared dependents direct 10 / transitive 17 (active assets, every layer) | fresh census `blocking_radius` |
| code readers outside the asset (non-test py/ts/tsx, 63 files) | L5 / other writers (python-sidecar pipeline/orchestrator/writers): bo_anveshana.py, bo_cgm_paths.py, bo_pratijna.py, ka_bhavishya_lekha.py, ka_yojaka.py, mi_adhilepa.py, mi_bhavisya.py, mi_kula.py, mi_pariksha.py, mi_pramana.py, ph_muhurta.py, ph_phaladesa.py, ph_pramana.py, ph_pratikara.py, ph_sankrama.py, ph_sodhana.py, ph_suddha_sodhana.py; python-sidecar other: bodha_writers/_idempotency.py, brahmagyan/domain_vocabulary.py, brahmagyan/l0_formula_constants.py, brahmagyan/mimamsa/multiplier.py, brahmagyan/mimamsa/outcome.py, brahmagyan/phala/anchors.py, brahmagyan/phala/l4_outlook.py, brahmagyan/phala/mitigation.py, ga_writers/ga_sade_sati_writer.py, pipeline/brahma_pipeline.py, run_ka_sangam_prod.py, services/gochara_kernel/legacy_semantics.py, services/gochara_v3/threshold.py, services/kala_permission/permission.py, services/ph_pramana/engine.py, services/ph_sodhana/engine.py; serving (platform-mcp/src): audit.ts, resources/vidhi/dossier_slices/dossier_slices.generated.ts, resources/vidhi/registry_data.ts, server.ts, tools/mimamsa_outcome.ts, tools/phala_event_anchors.ts, tools/phala_mitigation_map.ts, tools/phala_outlook.ts, tools/register_p1_aliases.ts, tools/register_p1_synthesis.ts; retrieval + app (platform/src): app/api/clients/[id]/learning/route.ts, app/api/mcp/db/query/route.ts, lib/jyotish/asset_names.ts, lib/pariprashna/samiksha/outcome_calibration.ts, lib/pipeline/compiled_floor_adapter.ts, lib/retrieval/registry/knowledge/producer_editorial_review.ts, lib/retrieval/registry/knowledge/source_query_availability.ts, lib/retrieval/registry/layers/L2_bodha/query_cgm_paths.ts, lib/retrieval/registry/layers/L4_phala/index.ts, lib/retrieval/registry/layers/L4_phala/query_phala_calibration.ts, lib/retrieval/registry/layers/L4_phala/query_predictive_anchors.ts, lib/retrieval/registry/layers/L4_phala/query_prospective_ledger.ts, lib/retrieval/registry/layers/L4_phala/salience_order.ts, lib/retrieval/registry/layers/L5_mimamsa/query_predictions.ts, lib/retrieval/registry/layers/register_spine_bundle.ts, lib/retrieval/spine/compute_spine_bundle.ts, lib/retrieval/spine/constants.ts, lib/retrieval/spine/types.ts, lib/schools/chart_data_adapter.ts, lib/vidhi/registry_data.ts | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src at `3de3f8b15` (tests, generated and migrations excluded) |
| served surface | `L4_phala/query_predictive_anchors.ts` (umbrella; declares `grounds_to: {l1_fact_ids: false}` honestly, `CALIBRATED_CONFIDENCE_BASES` empty by design so no row is served as calibrated), `platform-mcp/src/tools/phala_event_anchors.ts`, `phala_outlook.ts`, `phala_mitigation_map.ts`, `register_p1_synthesis.ts`; `density_contract` declared on 0 of the L4_phala capability modules except `query_prospective_ledger.ts` | code |
| role / scoring mode | manifestation-family asset of L4 Phala (T2 section 6.5); census `scoring: contribution`; 'manifestation anchors, mechanisms, contradictions, precedents, falsifiers' (T2c label, not a tier); individual contribution unmeasurable (no ablation harness, TG-L4-007) | tiers + census |
| invalidation / FK | `phala_anchors.convergence_id -> kala_convergence ON DELETE CASCADE` and `phala_anchors.bhavishya_id -> kala_bhavishya ON DELETE SET NULL`; five L4 tables FK to `phala_anchors(anchor_id)` (`phala_sodhana`, `phala_suddha_sodhana`, `phala_pramana` and `phala_sankrama` CASCADE; `phala_muhurta` and `phala_mitigation` SET NULL). `phala_anchors.signal_id` has no FK by design (registry note C13) | `pg_constraint` read 2026-10-03 |

## 1 - Measured state and the nine gates

### 1.1 - Live state on the canonical chart (read-only, 2026-10-03)

- **4 rows** on the canonical chart against a floor and a build record of 139 (the other built chart holds 56: 47 convergence, 6 bhavishya, 3 discovery). All 4 are `anchor_source='discovery'`, one per domain (career, character, health, relationship), `horizon_tier='near'`, `magnitude='minor'`, `direction='elevated'` x4, `peak_date` NULL x4, `karmic_frame` / `karmic_note` / `subsystem_source` NULL x4, `ayanamsha_robustness=3` x4, `dasha_consensus_count=0` x4, `window_start` = 2026-08-12 and `window_end` = 2026-11-10 on all four (`phala_anchors` profile, `data/table_phala_anchors.json`).
- **One posterior value.** `posterior` = 0.322 on 4 of 4 (1 distinct), `confidence_low/high` 0.272/0.372; the ledger shows `pratijna_grade=5.0`, `pratijna_status='conditional'` and `lift_vector.promise_lift=1.75` on 4 of 4. That is the pre-W3-3c default (a 75% amplification asserted on no evidence); running the CURRENT `compute_posterior(0.2, 0.0, 'no_evidence', 0, 0.0, 3)` returns **0.184** with every lift 1.0 (local pure-function run, `offline_checks.txt`).
- **Upstream is gone.** For the canonical chart `kala_convergence` = 0 rows and `kala_bhavishya` = 0 rows (L3 `ka_sangam` / `ka_bhavishya_lekha` are `stale`; `ka_sangam` recorded 14,868 rows written); `bodha_discoveries` = 1,161 rows, all `computed_at` 2026-09-10 07:06 UTC, so **none of the 4 stored `discovery_id`s exists any more** (0 of 4 resolve). The other 135 of the 139 anchors the build record counts are absent. The 4 survivors are exactly the rows with `convergence_id` NULL (0 of 4 non-null), which is what an `ON DELETE CASCADE` from the emptied `kala_convergence` would leave; no delete event was read, so the cause is consistent, not proven (TG-L4-023).
- **L5 consumers dangle.** `mimamsa_predictions` holds 139 rows for the canonical chart; **4 resolve** to a `phala_anchors.anchor_id` through `source_pramana_id`, **135 do not** (same 135 across all charts). The 139 frozen predictions are `pending` per the rebuild-plan evidence; their source anchors no longer exist.
- **What a rebuild would produce today (static emulation, not a build).** Applying the writer's own subsystem map and magnitude formula to the current top 100 discoveries (`composite_discovery_rank` 0.1775-1.1223; subsystems `ga_structural` 95, `ga_sensitive` 5 - neither is a key of `_SUBSYSTEM_DOMAIN`, `:637-658`) gives 2 distinct (domain, magnitude) keys, so CR-46 dedup would collapse 100 discoveries to about 2 anchors until L3 is rebuilt. Labelled an emulation: the writer was not run.
- **The asset's own integrity SQL cannot be run by the reader** (`ERROR: permission denied for function phala_anchor_identity`; the namespace function is also denied), so clause (b) 'every stored anchor_id equals its computed identity' is NOT determined here. Clause (a) was evaluated piecewise: referential orphans in the four CASCADE children = 0; the `mimamsa_predictions` orphan term = **135** (must be 0 for the SQL to return true).

Build history for this asset (all charts, `build_run_assets`): 9 aborted, 38 complete, 26 error/blocked_dependency, 1 error, 19 queued; the last complete canonical-chart run is `cbd6ea44` (2026-08-13), and the 26+ `error/blocked_dependency` rows are cascade skips, not writer errors. The only non-cascade errors on record: 1 error 2026-07-10 (`TypeError: can't compare datetime.datetime to datetime.date`, fixed by `3e2657857` / `8c2af1468`) and 9 aborts (last 2026-07-13). None since the 2026-08-13 build.

### 1.2 - Stored rows versus current code

Commits touching this asset's writer or engine AFTER its last build (2026-08-13 01:16 UTC): `968f084af` 2026-09-06 L4 W3-3c: ph_nimitta — two favourable values asserted on no evidence (#1808); `ea2f8a49a` 2026-09-05 L4: deterministic phala_anchors.anchor_id (D-CND-04, ruling #1732) (#1754).

Two post-build commits change what a rebuild writes: `ea2f8a49a` (deterministic `anchor_id`, migration 680) and `968f084af` (W3-3c: `pratijna_grade` default 5.0 -> 0.0 and status 'conditional' -> 'no_evidence', discovery `direction` 'elevated' -> 'mixed', `net_direction` fallback). The 4 stored rows are the OLD output: `direction='elevated'` x4, `promise_lift=1.75` x4. **Deployed writer version is not observable** (`built_against_writer_hash='unknown'`, TG-L4-005), so whether production runs the fixed code is not determined here.

### 1.3 - Census cells (fresh run, compared with the saved run)

Census used: fresh census `/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json` (generated 2026-10-02T10:12:59+05:30, chart 482012f1, inspector 1e5781a at REGISTRY_REVISION 10; outside the repo) compared with the repo's saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json` (2026-09-30T20:23:50+05:30, inspector 2a78ec64d). Main's inspector is now at REGISTRY_REVISION 15: the offline rollup below applies its rules to the fresh census; no live re-measure was run.

| gate | criterion | fresh verdict | measured (fresh census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Null | Null.schema_default | PARTIAL (saved 2026-09-30: (absent in saved run)) | no schema default on the declared prose column(s) falsifier; writer literal fallbacks and constant columns are not measured here, so this is never PASS |
| Null | Null.blank_rows | PARTIAL (saved 2026-09-30: (absent in saved run)) | no blank or placeholder row among the checkable prose rows; schema defaults are read by Null.schema_default and writer literal fallbacks and constant columns are not measured, so this is never PASS |
| Narr | Narr.fidelity_test | PARTIAL (saved 2026-09-30: (absent in saved run)) | structural only: 7 test file(s) call the builder and assert in the same test function (test_d1_5b_b5_completions.py, test_ka_yojaka_multidomain.py, test_ph_a5_fixes.py, test_ph_nimitta_honest_defaults.py…); declared field(s) referenced: falsifier; whether the assertion grades the sentence is not read, so this never reads PASS |
| Narr | Narr.lint | NO_DETECTOR (saved 2026-09-30: (absent in saved run)) | NO_DETECTOR — the narration lints are not applicable to this asset: no chart_facts fact_category selection in its 7-file writer scope and no declared column the raw-token lint covers; a clean scan of code they cannot see is not a pass |
| Dens | Dens.served | NO_DETECTOR (saved 2026-09-30: FAIL) | NO_DETECTOR — 1 serving-root file(s) naming phala_anchors lose the string scanner's sync (an unbalanced quote, a nested template literal, or a regex literal holding a quote desynced it): platform-mcp/src/tools/register_p1_synthesis.ts; its served select and density_contract cannot be read — never FAIL, never the closable N/A |
| Build | Build.dag | FAIL (saved 2026-09-30: PASS) | 9 declared edge(s); exists: all 9 are active registry assets (every layer); cycle: ph_nimitta is on no dependency cycle (registry-wide graph); reads-match: FAIL — missing depends_on edge: ph_nimitta -> bo_pratijna (reads bodha_pratijna at ph_nimitta.py:463; the producer is reachable transitively via ka_bhavishya_lekha, ka_sangam, so ordering holds but the edge is undeclared); missing depends_on edge: ph_nimitta -> ka_yojaka (reads kala_activation_predicates at ph_nimitta.py:477; the producer is reachable transitiv… |
| Build | Build.dep_liveness | PARTIAL | 5/9 declared dependencies lit at chart 482012f1 (or global); stale: ['ka_sangam (stale, chart 482012f1)', 'ka_bhavishya_lekha (stale, chart 482012f1)', 'bo_anveshana (stale, chart 482012f1)', 'bo_cgm_paths (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Build | Build.completion | FAIL | build record rows_written=139 disagrees with live=4 (count_sql over the target table; chart 482012f1) |
| Build | Build.history | PARTIAL | latest run complete, but 1 error(s) and 9 abort(s) on record (26 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-07-10): TypeError: can't compare datetime.datetime to datetime.date Traceback (most recent call last): File "/app/platform/python-sidecar/pipeline/orchestrator/asset_runner.py", line 459, in _run_data_write |
| Count | Count.floor | FAIL | live=4, floor=139, delta=-135 |
| Complete | Complete.depth | PARTIAL | 60 rows, 37 cols; fully populated 29; NEVER populated ['subsystem_source', 'karmic_frame', 'karmic_note'] |
| Complete | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach | Reach.fields | NOT_GENERIC | reported, not graded — width 25/34 built column(s) (73.5%) selected by 2 capability module(s); dark: ['causal_chain_jsonb', 'chart_id', 'computed_at', 'contradiction_jsonb', 'counterfactual_jsonb', 'derivation_ledger_jsonb', 'precedent_refs_jsonb', 'school_consensus_jsonb', 'structured_falsifier_jsonb']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — latest attempt at chart 482012f1: run cbd6ea44 complete/no disposition (2026-08-13): complete with no disposition and not derivable as probe-green (no probe receipt names this run) — unclassified |
| Earn | Earn.service_state | N/A (saved 2026-09-30: (absent in saved run)) | declared kind 'data' is not `service`; Earn.service_state is the service-state check (a service's rows_written cannot tell healthy-and-idle from broken) |

**PASS cells (compact):** Ldgr.source_presence, Idem.pattern, Vocab.identity, Narr.agree, Narr.checkable, Build.registered, Build.contract, Build.target, Build.exercised, Build.count_integrity.

**Offline rollup** (main `asset_census.py` rollup rules at REGISTRY_REVISION 15 applied to the FRESH census; N/A reads NO_DETECTOR while `NA_RULE_DECISIONS` is empty; this is not a re-measure and not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null PARTIAL · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens NO_DETECTOR · Build FAIL.
Same rules over the SAVED 2026-09-30 census: Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

### 1.4 - Earned-signal (N.8), narration-fidelity (N.7) and honest-null audit of this asset's flags and verdicts

| field / claim | what it claims | what code path could make it read false | finding |
|---|---|---|---|
| `posterior` | a Bayesian posterior event probability (`:289-322`) | none for the value: base_rate is a uniform 0.20 age prior for any anchor without an `event_class_id` (`services/ph_nimitta/base_rate.py:66-81`), lifts are 1.0 unless a `bodha_pratijna` row joins, and discovery anchors carry `signal_id = NULL::uuid` (`:381`) so no join is possible: every discovery anchor gets the same number (0.322 stored; 0.184 on current code). `posterior` also has the name of a probability while the engine header says its priors are placeholders (`engine.py:10-12`, JL-009 OPEN) and the writer says JL-009 is CLOSED (`:771`) | **Earned-signal gap, constant on discovery anchors.** Not a calibrated probability; C3/TG-L4-019 names no detector. SS question Q-L4-05 on policy |
| `confidence_low` / `confidence_high` | a confidence interval | none: `posterior - 0.05` / `+ 0.05` clamped to [0.01, 0.75] / [0.01, 0.80] (`engine.py:349-358`) - a decoration of the point value; ph_sodhana's `confidence_inflation` then checks this against a G-LADDER ceiling written for the model the posterior REPLACED (`services/ph_sodhana/engine.py:39-52`) | **Decorative band presented as an interval.** The other readers (ph_sankrama, ph_phaladesa narration "Confidence band spans ...", the serving layer) inherit it |
| `direction` (bhavishya path) | elevated / suppressed / mixed valence of the predicted event | substring test on a probability label: `'high' in prob_tier` -> `elevated` (`engine.py:571-573`). `kala_bhavishya.probability_tier` holds one value, `tier_1_high` (100 of 100 rows, read on the other built chart) so every bhavishya anchor is `elevated` (6 of 6 on that chart) | **Valence assigned from a proxy** (a probability tier is not a valence). Same class as the discovery `elevated` that W3-3c fixed. Q-L4-07 |
| `direction` (discovery path) | neutral when unknown | `direction='mixed'` (`engine.py:745`) after W3-3c; the 4 STORED rows still say `elevated` | real-stored (cured by rebuild) |
| `ayanamsha_robustness`, `dasha_consensus_count`, `av_transit_potency`, `school_consensus_jsonb` | measured cross-ayanamsha robustness (0-5), count of independent dasha systems, AV-transit potency, school consensus | none: written as the constants 3 (`:759`), 0 (`:757`), 0.0 (`:786`), None (`:758`); `derive_dasha_consensus` has no production caller (grep: only `tests/test_u1_dasha_consensus.py`). `rob_mod` is therefore the constant 0.92 on every anchor | **Constants stored as measurements.** ph_sodhana's `ceiling_inputs_degenerate` exists to catch exactly this and cannot fire below 5 anchors (see ph_sodhana brief) |
| `karmic_frame`, `karmic_note` | karmic-arc framing from the root graha | `derive_karmic_frame(root_graha)` looks up lower-cased graha names (`engine.py:175-194`) but receives a CGM path LABEL (`root_graha=cgm['paths'][0]['path_label_human']`, `:751`, e.g. "Saturn -> Venus -> Jupiter (final dispositor)") so the lookup misses every time | NULL on 4 of 4 (census: NEVER populated). **Dead elevation V3**; an honest NULL, but the registry description still advertises it |
| `causal_chain_jsonb` | the graph-causal chain for THIS anchor | `_load_cgm_meta` returns one chart-level aggregate (10 paths, `DISTINCT ON (p.path_id) ... ORDER BY p.path_id`, `:526-534`) used for every anchor; the 4 stored rows carry the identical path-id list | **Chart-level constant in a per-anchor field** |
| `precedent_refs_jsonb` | nearest embedding neighbours (top-3 per signal; docstring `:594`) | returns `{'nearest_signal_ids': [sid]}` - the signal itself (`:615`); `precedent_dates` always `[]` | **Self-reference presented as precedent** |
| `falsifier` / `structured_falsifier_jsonb` | a machine-evaluable refutation condition | text template from domain, magnitude floor and `window_end` (`engine.py:227-246,325-346`); census Narr.fidelity_test PARTIAL (tests call the builder; none grades the sentence) | deterministic restatement of its inputs; the "magnitude >= minor" floor is the lowest tier so any event in the domain satisfies it |
| `magnitude` | rarity x score tier | `rarity_years` is absent for discovery anchors so defaults 1.0 and `effective_score` is the discovery rank (up to 1.2, not bounded to [0,1]): stored basis "rarity_years=1.0yr x effective_score=1.200 = 0.120 -> minor" (`engine.py:153-170`) | all 4 stored are `minor` by construction; the tier cannot reach `moderate` for any discovery anchor while rarity defaults to 1.0 (max combined = 0.12 on the current rank range) |
| window of a discovery anchor | an astrological prediction window | `window_start` = discovery `computed_at` date, `window_end` = +90 days (`:692-696`); `peak_date` from the nearest convergence within 90 days (`:712`) else NULL | **Not astrological timing**: it is a computation timestamp plus 90 days; because `anchor_id` hashes the window and `horizon_tier` is computed against `date.today()` (`engine.py:136`), the identity moves with every L2 rebuild and with the calendar |
| honest nulls | NULL where unknown | `pratijna_status='no_evidence'` / grade 0.0 on a missing row (`:783-785`) is the honest branch since W3-3c; `NimittaContext` dataclass defaults are still 5.0 / `conditional` / 0.10 (`engine.py:389-393`), so any caller that omits the fields gets the amplification back | writer path honest; library default is not (FD-8) |

### 1.5 - UUID chart_id check (the bo_*/ph_* adapter defect)

`ctx.config['chart_id']` arrives as a native `uuid.UUID` on the real path (`asset_runner.py:1121` passes the value `fetch_birth_params` was given; the comment at `asset_runner.py:166-170` says so and #1856 coerced only the provenance capture). In `ph_nimitta` the chart id goes only into psycopg parameters (`:129,226-267`), an f-string log line and the SQL `phala_anchor_identity(%s::uuid,...)`; **no `json.dumps` payload contains it**: the six `json.dumps` sites (`:273-279`) take engine dicts whose ids are `str()`-coerced (`engine.py:512,528,614,634,718-719,736-737`). No `canonical_json`, `stable_uuid` or `uuid5` call exists in any `ph_*` file (grep). **Verdict: the defect is not present in this asset today**; it is one added `chart_id` ledger key away from the `ph_sodhana` failure (see that brief), and this writer has no `_UUIDEncoder`.

## 2 - Gaps: which are real, which are detector or definition gaps

Class vocabulary: **real** = a shortfall in code, rows, registry row or served surface; **real-stored** = the CURRENT code already fixes it but the stored rows predate the fix (cured by a rebuild, not by an edit); **design** = needs an SS or acharya decision; **detector** = the instrument is absent or its definition is the open point; **history** = a recorded past outcome no edit can change; **information** = Count/Cost/Complete/Reach, never a blocker; **opportunity** = beyond the requirement.

| gap id | gate | class | note (evidence) |
|---|---|---|---|
| ph_nimitta-G01 | Build / Dens | real-stored | Stored anchors are the pre-W3-3c output: `direction='elevated'` x4 and `promise_lift=1.75` x4 (posterior 0.322; current code 0.184). Cured by a rebuild, not an edit |
| ph_nimitta-G02 | Build / Carr | real | Orphaned provenance: 0 of 4 stored `discovery_id`s exist in `bodha_discoveries`; 135 of 139 frozen `mimamsa_predictions` cite anchor ids that no longer exist |
| ph_nimitta-G03 | Build | real | The asset's `integrity_check_sql` (registry) has a global term "no `mimamsa_predictions.source_pramana_id` without an anchor" that is false now (135). The orchestrator rolls back and errors a writer whose post-write check is false (`asset_runner.py:1200-1210`), so a rebuild of this asset cannot be accepted while those L5 rows exist - a cross-layer deadlock |
| ph_nimitta-G04 | Null / Earn | real | Constants stored as measurements: `ayanamsha_robustness=3`, `dasha_consensus_count=0`, `av_transit_potency=0.0`; `derive_dasha_consensus` unused in production |
| ph_nimitta-G05 | Earn / Narr | design | Decorative +/-0.05 confidence band and a probability-named `posterior` whose inputs are uniform for discovery anchors (Q-L4-05, TG-L4-019) |
| ph_nimitta-G06 | Earn / Narr | design | bhavishya `direction` from `probability_tier` substring (`engine.py:571-573`); one tier value exists in the data (Q-L4-07) |
| ph_nimitta-G07 | Carr / Null | design | Discovery-sourced anchors have a computation-timestamp window (+90 d), no signal context (`signal_id = NULL::uuid`, `:381`), and an identity that moves with L2 rebuilds and the calendar (Q-L4-08) |
| ph_nimitta-G08 | Null | real | V3 karmic frame is dead (path label vs graha-name lookup, `:751`); `causal_chain_jsonb` is a chart-level constant; `precedent_refs_jsonb` is the signal itself (`:615`) |
| ph_nimitta-G09 | Build | real | Undeclared edges `bo_pratijna` (`:463`) and `ka_yojaka` (`:477`) (fresh census Build.dag FAIL, the saved 2026-09-30 run read PASS under Build.dag revision 1; the reads-match clause arrived at revision 2); declared-unread `bo_bimba`, `bo_karanajala` |
| ph_nimitta-G10 | Build | real | FK `convergence_id ... ON DELETE CASCADE`: any L3 delete of `kala_convergence` rows silently deletes anchors and, through four more CASCADE FKs, their sodhana/suddha/pramana/sankrama rows (TG-L4-023; Q-L4-03) |
| ph_nimitta-G11 | Narr | real | Contradictory documentation inside the asset: `engine.py:10-12` "JL-009 OPEN ... PLACEHOLDER 0.10" vs `ph_nimitta.py:771` "JL-009 CLOSED"; `NimittaContext` defaults still the old inflated values (`engine.py:389-393`) |
| ph_nimitta-G12 | Build | information | Candidate attrition is not persisted: registry note says about 460 candidates derive and 139 survive (~70% rejected) and "logged to stdout only"; the CR-46 / T-5 counts are `logger.info` only (`:207-212,854-861`) |
| ph_nimitta-G13 | Build | information | Build.completion FAIL (record 139 vs live 4), Count.floor FAIL (4 vs 139); both are consequences of G02/G10, not writer over-reporting (the writer counts accepted rows since `:287-290`) |
| ph_nimitta-G14 | Build | history | Build.history PARTIAL: 1 error (2026-07-10, fixed) and 9 aborts on record; CF-L4-15 |
| ph_nimitta-G15 | Earn / Carr / Vocab | detector | Earn.build_record, Carr (no D1/D2/D3), Vocab.alias NO_DETECTOR; Null PARTIAL (declared prose field `falsifier` only, no `null_convention`) |
| ph_nimitta-G16 | Dens | detector | Dens.served NO_DETECTOR: the string scanner desyncs on `platform-mcp/src/tools/register_p1_synthesis.ts`, so the served select and `density_contract` cannot be read (never FAIL) |

## 3 - Disposition

DISPOSITION: qualify

EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/_evidence/data/ph_nimitta.json

EVIDENCE_EXTRA: this brief sections 1-4; 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/_evidence/upstream_receipts.json; 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/_evidence/rollup_L4.json; 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/_evidence/offline_checks.txt; 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/_evidence/rect_diag.txt; 00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json (saved 2026-09-30 census); fresh 2026-10-02 census at /Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json (outside the repo)

**qualify (Q) - fix + rebuild; no consolidation or retirement proposed.** Qualify (Q) rather than keep: the asset is the spine every other L4 asset and the L5 freeze depend on, it has real consumers and a sound skeleton (deterministic identity, accepted-row count, gates, delete-then-insert, honest `no_evidence` default), but several of the values it emits are constants or proxies presented as measurements (G04-G08), its stored state is both stale and orphaned (G01-G03, G10), and one of its own integrity terms makes a rebuild unacceptable (G03). No consolidation candidate: the T2 section 6.5 overlap investigation (`ph_phaladesa`, `ph_nimitta`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`, `ph_pramana`) does not touch the anchor table's grain. Not retire: nine assets and the L5 freeze read it.

Approver under Track A brief section 10: **Steward (G16)** for keep/qualify/enrich; **SS** for any output change (R5). No disposition is applied by this brief.

## 4 - Fix designs (one per real gap; anything marked `needs production rebuild` or `needs migration` is a REVIEW item for Strategic Suvarna)

### FD-1 - Rebuild the chain in the plan order (no code change)

- **Answers:** G01, G13; CF-L4-01
- **Change:** The canonical-chart rebuild plan puts `ph_nimitta` in wave 7, after `ka_sangam` (wave 3), `ka_bhavishya_lekha` (wave 6) and before `ph_muhurta ... ph_phaladesa` (waves 8-11) (`platform/scripts/governance/__tests__/fixtures/f3_canonical_rebuild_plan_waves.json`, copied from the plan on branch rebuild-plan-001). Rebuilding `ph_nimitta` before `ka_sangam` would produce discovery-only anchors (about 2 by the emulation above).
- **Files / declaration / migration:** none (dispatch of the existing asset)
- **Failing-first test and mutation:** failing-first: after the L3 wave, `Build.completion` PASS and `Count.floor` PASS for the new live count; mutation: delete one `kala_convergence` row -> anchors cascade (assert the cascade, FD-5)
- **Output change:** yes - every stored value of the four rows is replaced (`direction`, `posterior`, windows, ids)
- **Blast radius:** every L4 asset and `mi_bhavisya`; anchor ids change, so all 139 frozen predictions lose their source (see FD-2)
- **Rebuild:** needs production rebuild (REVIEW item for SS; Exec Suvarna runs it, not this lane)
- **Gate it moves:** Build (completion, count_integrity), Count
- **Fix class:** data (rebuild); **risk class:** R3; **buildable before J1:** tier-independent for the dispatch; blocked by FD-2
- **Decision:** OPEN - Q-L4-01

### FD-2 - Decouple the integrity SQL from frozen L5 rows

- **Answers:** G03; CF-L4-02
- **Change:** Option A: replace the term `(SELECT count(*) FROM mimamsa_predictions p LEFT JOIN phala_anchors a ... ) = 0` by a chart-scoped term that ignores predictions whose status is not `pending` and counts the rest as a WARN, not a rollback. Option B: keep the term and require `mi_bhavisya` to re-point or retire its rows before this asset is rebuilt (an L5 action; the freeze rule says a rebuild must not reset chronology, T1 7.3). Option C: drop the term from L4 and put the L5->L4 reference check where L5 owns the rows (`mi_bhavisya` integrity SQL).
- **Files / declaration / migration:** registry `integrity_check_sql` (surgical migration, number = max+1 across every head at execution time, verified by production structure) + `platform/scripts/seed/asset_registry_seed.ts`
- **Failing-first test and mutation:** failing-first: the new SQL returns true on the current state (135 pending predictions) and false when a NEW anchor id is referenced by a prediction but absent; mutation: restore the old term -> false
- **Output change:** none
- **Blast radius:** registry row only; other 8 L4 assets' SQL untouched
- **Rebuild:** none for the SQL; unblocks FD-1
- **Gate it moves:** Build (integrity)
- **Fix class:** registry/declaration (migration); **risk class:** R3 (cross-layer coupling, decides what happens to frozen predictions); **buildable before J1:** tier-dependent: which layer owns the L5->L4 reference check is not stated in any tier
- **Decision:** OPEN - Q-L4-02

### FD-3 - Honest nulls for unmeasured numeric fields

- **Answers:** G04, G08; CF-L4-04
- **Change:** Write NULL (not 3 / 0 / 0.0) to `ayanamsha_robustness` and `dasha_consensus_count` when no source row supplies them; make `rob_mod` 1.0 (neutral) when robustness is NULL, or read the real value from the source `kala_convergence` row as the comment at `:759` promises; leave `karmic_frame` NULL by declaration until a per-anchor CGM path exists (FD-4); set `precedent_refs_jsonb.nearest_signal_ids` to `[]` unless a real neighbour is found (`:615`).
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py:757-759,615`, `platform/python-sidecar/services/ph_nimitta/engine.py:309` (rob_mod) + a `null_convention` declaration in `asset_declarations.json` naming each nullable column and what NULL means
- **Failing-first test and mutation:** failing-first: a unit test asserts NULL (not 3/0) in the INSERT parameters for a context without sources and posterior unchanged otherwise; mutation: restore the constant -> test fails. `ceiling_inputs_degenerate` (ph_sodhana) should then read "inputs absent" not "constant"
- **Output change:** yes - `ayanamsha_robustness`, `dasha_consensus_count`, `lift_vector_jsonb.ayanamsha_robustness_modifier`, `posterior` (0.184 -> 0.2 for a no-evidence anchor), `confidence_*` move; a change in served numbers
- **Blast radius:** readers of `confidence_high`: ph_sodhana, ph_sankrama, ph_phaladesa, ph_muhurta (ordering), the serving layer, L5 `mi_pariksha`
- **Rebuild:** needs production rebuild (rides FD-1)
- **Gate it moves:** Null, Earn
- **Fix class:** writer code; **risk class:** R2 for the code; R4 for the number change (SS, R5); **buildable before J1:** tier-independent for the NULLs; the number change is SS's
- **Decision:** OPEN - Q-L4-05, Q-L4-09

### FD-4 - Per-anchor CGM path or NULL-by-design for karmic frame and causal chain

- **Answers:** G08
- **Change:** Option A: select the CGM path(s) per anchor through a signal -> path join (needs `bodha_cgm_paths` to carry or be joinable by signal; today it has no `signal_id`, `:518-519` comment) and pass the ROOT GRAHA (first element of the path), not the label, to `derive_karmic_frame`. Option B (no new join): declare `karmic_frame`, `karmic_note`, `causal_chain_jsonb` NULL-by-design and stop writing the chart-level aggregate into a per-anchor column.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py:510-559,735-760`; declaration
- **Failing-first test and mutation:** failing-first: two anchors from different signals get different `cgm_path_ids` (A) or NULL `causal_chain_jsonb` (B); mutation: reuse the aggregate -> fails
- **Output change:** yes (A: new values; B: removal of a repeated list)
- **Blast radius:** serving of `causal_chain_jsonb` (dark in the census already: Reach.fields lists it as unselected by any module)
- **Rebuild:** needs production rebuild (rides FD-1)
- **Gate it moves:** Null, Narr
- **Fix class:** writer code; **risk class:** R2; **buildable before J1:** tier-dependent: which graha is "the root" of a path is an acharya call (Q-L4-09)
- **Decision:** OPEN - Q-L4-09

### FD-5 - Make the library defaults neutral

- **Answers:** G11
- **Change:** `NimittaContext` defaults -> `pratijna_grade=0.0`, `pratijna_status='no_evidence'`, `base_rate` = the uniform prior constant; reconcile the JL-009 text at `engine.py:10-12` with `:771`.
- **Files / declaration / migration:** `platform/python-sidecar/services/ph_nimitta/engine.py:389-393,10-12`
- **Failing-first test and mutation:** failing-first: `NimittaContext()` alone gives `_promise_lift == 1.0`; mutation: restore 5.0/conditional -> fails (extends `test_ph_nimitta_honest_defaults.py`)
- **Output change:** none for the writer path (it passes explicit values)
- **Blast radius:** direct callers and tests only
- **Rebuild:** none
- **Gate it moves:** Narr
- **Fix class:** writer code (engine); **risk class:** R1; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### FD-6 - Declare the two missing edges (and review the two unread ones)

- **Answers:** G09; CF-L4-07
- **Change:** Add `ph_nimitta -> bo_pratijna` and `ph_nimitta -> ka_yojaka` to `depends_on`; decide whether `bo_bimba`, `bo_karanajala` (no table read found) stay as ordering-only edges. Migration 1210 deliberately covered 12 edges; this is a separate review because the upstream hash moves.
- **Files / declaration / migration:** one surgical registry migration + `asset_registry_seed.ts`
- **Failing-first test and mutation:** failing-first: fresh-census `Build.dag` PASS for the asset; mutation: remove one edge -> reads-match FAIL naming it
- **Output change:** none
- **Blast radius:** the asset becomes stale when either producer is rebuilt (correct)
- **Rebuild:** none (a declared edge changes the upstream hash, so the next build is not delta-skipped)
- **Gate it moves:** Build (dag)
- **Fix class:** registry/declaration; **risk class:** R2; **buildable before J1:** tier-independent
- **Decision:** no question; Steward

### FD-7 - Decide the FK cascade and the discovery-window semantics

- **Answers:** G07, G10; CF-L4-02
- **Change:** (i) FK: keep CASCADE (an L3 delete then removes L4 rows by design), or follow the F-3 precedent (`F3_MSR_FK_DROP_v1_0.md`: drop the FK, tolerate orphan pointers, report them by function) or SET NULL as `bhavishya_id` already does. (ii) Discovery anchors: either label the window in the ledger (`timing_basis: computed_at+90d`) and keep, or move discovery-seeded rows out of the prediction table.
- **Files / declaration / migration:** migration (FK) / `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py:692-712` (ledger label)
- **Failing-first test and mutation:** failing-first: deleting a `kala_convergence` row leaves the anchor (FK dropped) / the row carries `timing_basis`; mutation: restore CASCADE -> row vanishes
- **Output change:** additive (ledger key) or structural (table move)
- **Blast radius:** L3 rebuild semantics; five L4 child tables; L5 predictions
- **Rebuild:** none for the FK change; the label rides FD-1
- **Gate it moves:** Build, Carr
- **Fix class:** migration / writer code; **risk class:** R4; **buildable before J1:** tier-dependent: no tier says whether an L3 rebuild may delete L4
- **Decision:** OPEN - Q-L4-03, Q-L4-08

### FD-8 - Persist candidate attrition and add a `null_convention` declaration

- **Answers:** G12, G15; CF-L4-10
- **Change:** Return the T-5 / dedup rejection counts in `WriterResult.notes` (the contract field exists) and declare `prose_fields` evidence + a `null_convention` for `peak_date`, `karmic_*`, `subsystem_source`, `convergence_id`, `bhavishya_id`, `signal_id`.
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/ph_nimitta.py:207-212,854-861`; `platform/scripts/governance/asset_declarations.json`
- **Failing-first test and mutation:** failing-first: Null.schema_default / blank_rows leave PARTIAL for the declared form; mutation: undeclare a nullable column that holds NULL -> FAIL
- **Output change:** none
- **Blast radius:** census inputs; `WriterResult.notes` text
- **Rebuild:** none
- **Gate it moves:** Null
- **Fix class:** declaration + writer code; **risk class:** R1; **buildable before J1:** tier-independent
- **Decision:** no question; Track E owns the declarations file

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-L4-01** - *this asset:* rebuild chain, wave 7; 4 stored rows are pre-W3-3c output
- **CF-L4-02** - *this asset:* integrity-SQL coupling to `mimamsa_predictions`; FK cascade from `kala_convergence`
- **CF-L4-04** - *this asset:* constants and decorative band presented as measurements
- **CF-L4-07** - *this asset:* two undeclared and two declared-unread edges
- **CF-L4-08** - *this asset:* `date.today()` in `_horizon_tier` / T-5 gate; identity hashes a computation-date window
- **CF-L4-09** - *this asset:* UUID chart_id: not present today; no encoder in this writer
- **CF-L4-10** - *this asset:* Null/Narr declarations (falsifier declared; `null_convention` absent)
- **CF-L4-11** - *this asset:* Dens NO_DETECTOR (scanner desync on `register_p1_synthesis.ts`)
- **CF-L4-12** - *this asset:* floor 139 and the description text ("150 rows", 8 axes) are stale against any realistic rebuild
- **CF-L4-13** - *this asset:* reader of record for L5 freeze; `ka_bhavishya_lekha` reads this table as a guard (`ka_bhavishya_lekha.py:253-286`)

## 5 - Semantic fingerprint contract (for the rebuild plan)

Natural key `anchor_id` (PRIMARY KEY; `phala_anchor_identity(chart_id, anchor_source, event_type, direction, domain, horizon_tier, window_start, peak_date, window_end, falsifier)`, migration 680). Fingerprint over the identity tuple plus `magnitude`, `posterior`, `confidence_*`, `malleability`. Volatile and excluded: `computed_at`. **Not stable across days or L2 rebuilds for discovery anchors**: `window_*` derive from the discovery's `computed_at`, `horizon_tier` and the T-5 gate read `date.today()` (`engine.py:136`, `:837`). A pre/post comparison must therefore fix an as-of date and rebuild L2 first, or compare only convergence/bhavishya-sourced anchors. The integrity SQL allows up to 4 anchors whose stored id differs from the computed identity (issue #1748).

## 6 - Preserved kernel, carriage check, opportunities

- **Preserved kernel:** Deterministic anchor identity, accepted-row counting, the SPINE-FIRST gate, the T-5 pre-birth clip, CR-46 dedup, the honest `no_evidence` branch of the promise lift, `confidence_basis='structural_not_yet_empirical'` (the sodhana firewall depends on it), the falsifier template and the derivation ledger with `posterior_inputs`.
- **Carriage check (T4 4.1; one only):** D3 (re-derivation): recompute `posterior` and `lift_vector_jsonb` from the ledger's `posterior_inputs` with `compute_posterior` (pure function, `engine.py:289`) and compare to the stored columns; recompute `anchor_id` from the row's identity tuple. Both are deterministic and need no ephemeris. A D1 text check does not apply (no source verse is carried).
- **By design, stated and not flagged:** `confidence_basis` is always `structural_not_yet_empirical` and calibration is L5's (the serving allowlist `CALIBRATED_CONFIDENCE_BASES` is empty on purpose, `query_predictive_anchors.ts:23-28`); L4 does not calibrate itself (T2 3.1). The pattern delete-then-insert per chart and the L4 NO-SCORING stance are stated, not flagged. Whether `posterior` itself is a score under that stance is the question (Q-L4-05), not a verdict.
- **Opportunities (never blocking):** surface `lift_vector_jsonb` (dark in the census) so a caller can see each lift is 1.0; persist attrition counts; a per-anchor CGM path join.

## 7 - Decisions applied, questions for SS, Track I items arising

No decision has been applied: SS has not yet answered the A.L4 questions. This brief raises:

- **Q-L4-01** - Who authorises the canonical L4 rebuild, in what order relative to L3, and what becomes of the 139 frozen L5 predictions whose anchors are gone (135 dangling)? (INDEX section 7)
- **Q-L4-02** - Where does the L5->L4 reference check live: keep the global term in this asset's integrity SQL (deadlocks a rebuild), scope it, or move it to L5?
- **Q-L4-03** - May an L3 rebuild delete L4 rows? Keep `ON DELETE CASCADE` from `kala_convergence`, SET NULL, or drop the FK as F-3 did for MSR?
- **Q-L4-05** - Is `posterior` (and the +/-0.05 band) permitted in L4 under the no-self-calibration stance, and if so under what name and with which NULL rules?
- **Q-L4-07** - What is the source of `direction` for bhavishya anchors, given `probability_tier` is a probability label? (`mixed` until a valence exists?)
- **Q-L4-08** - Are discovery-seeded rows predictions at all? Their window is a computation date + 90 days.
- **Q-L4-09** - (acharya) Which graha is the root of a CGM path for the karmic frame, and should it be per anchor?
- **Q-L4-06** - Floors: set `target_floor` = the achieved count after the rebuild (CLAUDE.md N.4) - confirm.

**Track I items arising (see INDEX section 8):** TI-L4-01, TI-L4-02, TI-L4-03, TI-L4-04, TI-L4-05, TI-L4-06, TI-L4-07, TI-L4-08, TI-L4-09, TI-L4-10.

