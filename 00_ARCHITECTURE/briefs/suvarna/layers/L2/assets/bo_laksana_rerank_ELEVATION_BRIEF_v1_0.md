---
asset_id: bo_laksana_rerank
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
disposition_proposal_approver: "Steward (G16)"
nirmana_freeze: "t3, 2026-09-11"
decisions_applied: "SS decision N-59 (2026-10-01) on DECISION_SHEET_L2_v1_0.md (PR #2841); items marked (R) provisional until J1; section 8 lists the rulings for this asset"
track_i_items: [TI-L2-04, TI-L2-10, TI-L2-13, TI-L2-14, TI-L2-17, TI-L2-20, TI-L2-31, TI-L2-32]
ledger_gap_ids: [bo_laksana_rerank-Idem.pattern, bo_laksana_rerank-Earn.build_record, bo_laksana_rerank-Cost.baseline, bo_laksana_rerank-Build.history, bo_laksana_rerank-Carr.detector]
---
# bo_laksana_rerank — Post-CGM re-rank pass: UPDATE-only enrichment of `bodha_msr_signals`

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

The only UPDATE-only writer in the layer and the one registered MSR target that replaces no row (layer instance §6.1; MF-L2-010): after the CGM exists it writes real graph centrality onto each MSR signal's `graph_node_strength_contribution_jsonb` hook (closing prior defect CR-84), fills `system_convergence_count`, `cross_system_consensus_count` and `contradicts_signals_array`, and for `ga_vichara_v1` rows overwrites `valence`/`valence_source` (declaration evidence: six non-text columns, `bo_laksana.py:3748-3774`, `:3886`, `:3948`). `@register("bo_laksana_rerank")` at `bo_laksana.py:3821` (class `BoLaksanaRerankWriter`, `:3823`); it shares the writer file with `bo_laksana`. Registry `count_sql` counts the rows that carry a centrality payload (11,094 of the chart's 50,678 rows). Migration 1210 added its direct edges to `bo_bimba` and `ga_vichara` (reads of `bodha_cgm_nodes` and the vichara facts); under the rev-2 Build.dag detector that moved it FAIL → PASS per the migration header.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2011`; seed `catalog_status` DRAFT, live CURRENT | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py:3821`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_msr_signals`; count_sql tables: `bodha_msr_signals` | census CEN-R |
| live rows / floor | 11094 / 1 (chart 482012f1, count_sql scope) — count_sql counts `graph_node_strength_contribution_jsonb IS NOT NULL` (11,094 of 50,678 chart rows) | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_laksana`, `bo_karanajala`, `bo_sudarshana`, `bo_nakshatra_semantic`, `bo_arudha`, `bo_special_lagna`, `bo_vargottama_dhana`, `bo_bimba`, `ga_vichara` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 1 / transitive 40; seed-derived closure (post-1210): direct 1 / transitive 40; direct dependents: `bo_sangati` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_msr_signals`: 89 non-test py/ts/tsx files reference it (65 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `ka_bhavishya_lekha.py`, `mi_adhilepa.py`, `ka_yojaka.py`, `ph_phaladesa.py`, `mi_bhavisya.py`, `ph_nimitta.py` +59 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 9 capability module(s): `L2_bodha/query_domain_reading.ts`, `L2_bodha/query_signals.ts`, `L2_bodha/query_ucd.ts`, `L2_bodha/traverse_chart_graph.ts`, `L3_kala/call_service_wrappers.ts`, `L3_kala/query_temporal_activation.ts`, `reading_checklist.ts`, `register_d8_assess_domain.ts`, `register_d9_judgment.ts`; `density_contract` declared on 3 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t3, 2026-09-11; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 20764472 complete/build (2026-09-11) |
| Idem | Idem.pattern† | PARTIAL | the asset's own table(s) are only UPDATEd in place: bodha_msr_signals (bo_laksana.py:3756), bodha_msr_signals (bo_laksana.py:3886), bodha_msr_signals (bo_laksana.py:3948) — no row is added, but whether a rebuild re-derives every row is not measured [resolved scope: bo_laksana.py, bodha_writers/data_plane_contracts.py, brahmagyan/graha_vocabulary.py, brahmagyan/l0_semantic_release.py] |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Build | Build.history | PARTIAL | latest run complete, but 2 error(s) and 3 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-07-16): TypeError: Object of type Decimal is not JSON serializable Traceback (most recent call last):   File "/app/platform/python-sidecar/pipeline/orchestrator/asset_runner.py", line 562, in _run_data_writer |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 20764472 complete/build (2026-09-11) |
| Complete (information) | Complete.depth | PARTIAL | 150724 rows, 85 cols; fully populated 40; NEVER populated ['varga_provenance_jsonb', 'source_corroboration_count_by_verse', 'divisional_corroboration_count', 'dasha_activation_proximity_score', 'aspect_modifier', 'argala_modifier', 'salience_confidence_interval_jsonb', 'shared_factor_keys_jsonb', 'cross_domain_shared_factor_count', 'graph_edge_pattern_jsonb', 'graha_weakness_indicators_jsonb', 'recurring_pattern_mark… |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width ≥ 19/67 built column(s) (28.4%), a lower bound: L2_bodha/query_signals.ts, L3_kala/call_service_wrappers.ts select(s) a run-time column list selected by 9 capability module(s); dark: ['active… |

**PASS cells (compact):** Ldgr.source_presence (citation_ref populated on 150724/150724 rows); Vocab.identity (declared key (chart_id, ayanamsha_id, signal_type_id, build_id, configuration_jsonb): 0 duplicate(s)); Dens.served† (6 module(s): query_discoveries.ts, query_domain_reading.ts, query_pratijna.ts, query_signals.ts, query_ucd.ts,…); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=11094 = live=11094 (count_sql over the target table; chart 482012f1)); Build.exercised (18 executed run(s) of 25 build_run_assets row(s), scope(s): asset_set, global, layer, last executed 2026-09-11); Build.dep_liveness; Count.floor (live=11094, floor=1, delta=+11093).

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr PASS · Idem PARTIAL · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **NO_DETECTOR** — only a table other assets share (bodha_msr_signals) is referenced, by 19 module(s): L2_bodha/graha_portrait.ts, L2_bodha/query_discoveries.ts, L2_bodha/query_domain_reading.ts (+16 more); the served surface cannot be attributed to bodha_msr_signals by code (never the closable N/A); Idem.pattern rev 2 reads **PARTIAL**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** FAIL — missing edges `bo_laksana_rerank → bo_bimba` (reads `bodha_cgm_nodes` at `bo_laksana.py:3688`) and `→ ga_vichara` (`chart_vichara` at `bo_laksana.py:3918`). **Migration 1210 added both; PASS afterwards (1210 header).** The saved census cell Build.dag PASS † above is the rev-1 reading.

**MSR group.** This asset is one of the seven producers that target `bodha_msr_signals`; the group reading is in `INDEX.md` §3 (per-asset attribution is dark in the default projection because `producer_asset_id` is not served, so the per-asset cells above are the producer-scoped `count_sql` partitions, and Narr declarations attribute through the served `signal_type_class` facet). Chart rows: 50,678 = 45 + 14 + 20 + 25 + 45 + 50,529; table-wide 150,724 rows (MF-L2-004: never compare the two populations).

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| `bo_laksana_rerank-Idem.pattern` (census cell, PARTIAL) | Idem | detector | saved census PARTIAL: "only UPDATEd in place … whether a rebuild re-derives every row is not measured"; the offline rev-2 static re-scan keeps PARTIAL with `update-only:keyed-row-set-unproven` ×3 and says PASS needs the E5.5 semantic-fingerprint comparison across a rebuild on the E5.6 rehearsal database, which no static scan runs. Not a defect found in the writer. The ledger row (`ON CONFLICT …`) is stale. |
| code: `bo_laksana.py:3886-3960`; `asset_declarations.json` `cross_asset_writes: null` | Idem / Build | real (declaration) | the asset writes columns of rows owned by six other producers (including `valence`/`valence_source`, which the owning writer set at insert) but declares `cross_asset_writes` as unknown (null); the file defines it as the list of `table.column` an asset writes outside its own table. CF-19. |
| layer instance §2.1 row 8 [Q3b]; not a census cell | Null | real-or-SS-question | on the chart `valence` is non-null on 50,678/50,678 rows: neutral 34,960, malefic 8,633, benefic 5,448, mixed 1,637; by `valence_source` 44,479 rows come from `keyword_heuristic_v1`, 6,050 from `ga_vichara_v1` (the L1 authority this asset overwrites with), 125 from `categorical_deterministic_v1`, 24 from `valence_doctrine_v1`. Whether a heuristic `neutral` stands for a missing computation (T1 §3.3: a named gap, never a neutral default) is not measured. |
| `bo_laksana_rerank-Build.history` | Build (history) | history | latest run complete; 2 errors and 3 aborts on record (latest error 2026-07-16, `TypeError: Object of type Decimal is not JSON serializable`, a defect since fixed: test `test_bo_laksana_rerank_json_serialization.py` exists). CF-10. |
| `bo_laksana_rerank-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent (migration 1094) / no D1-D3 detector; CF-05, CF-07 |
| census cell Dens.served †; Reach | Dens | detector (attribution) | the rerank's output column is served only through the projection whitelist on request (`query_signals.ts:112`), not in the default projection (declaration evidence); offline rev-4 scan NO_DETECTOR (shared table). CF-04. |
| census: Null/Narr | Null, Narr | detector | `prose_fields = []` is declared with writer evidence (`bo_laksana.py:3872-3960`): the writer composes no string bound to a column; the Narr.lint/agree checks have not run. CF-06 (done), CF-14 (guard test exists in the declaration evidence). |

## 3 · Disposition

**keep (P)** — the asset is sound by the census (Build.completion PASS, Count.floor PASS, Ldgr PASS) and its single PARTIAL is a detector limit, not a measured defect; the real observations are a declaration gap (CF-19) and a valence-provenance question. Its place in arch §12.9's list of row-replacing MSR writers is wrong and is recorded (MF-L2-010).

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Declare the cross-asset writes

- **Answers:** CF-19; `asset_declarations.json` `cross_asset_writes`
- **Change:** declare `bodha_msr_signals.graph_node_strength_contribution_jsonb`, `.system_convergence_count`, `.cross_system_consensus_count`, `.contradicts_signals_array`, `.valence`, `.valence_source` as this asset's cross-asset writes with `evidence` pointers to `bo_laksana.py:3748/3757/3774/3886/3948`
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (Track E owns the file) + its validator test `__tests__/test_e6_1_declarations.py`
- **Failing-first test and mutation:** declarations validation passes; mutation: add a seventh UPDATE column in the writer → the declaration-versus-writer scan flags the undeclared column (needs the CF-19 detector)
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 1: `bo_sangati`; transitive 40); the touched surface is `platform/scripts/governance/asset_declarations.json` (Track E owns the file) + its validator test `__tests__/test_e6_1_declarations.py`
- **Rebuild:** none
- **Gate it moves:** Idem (and the E5.5 fingerprint partition)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (the field exists in declarations 1.6.0)

### FD-2 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): recompute `system_convergence_count`/`cross_system_consensus_count` by the stated rule (signals sharing a `chart_facts.fact_subject`, `bo_laksana.py:3726-3752`) and the centrality values from `bodha_cgm_nodes`; compare.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 1: `bo_sangati`; transitive 40); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-19** — cross_asset_writes declarations (writes into rows another asset owns). *This asset:* the declaration above
- **CF-13** — MSR replacement: R243 annotation and F-3 cascade-key retirement. *This asset:* not one of the six R243 PASSes (its Idem reads PARTIAL), but it must run after any MSR replacement because it updates rows of every producer
- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* output column dark in the default projection; Dens attribution rule
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* declared `[]`; keep the AST guard from the declaration evidence
- **CF-17** — Complete.depth: never-populated columns (declare, populate or drop). *This asset:* table-wide never-populated columns
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3 (§6)

## 5 · Semantic fingerprint contract (for E5.5)

Rows are the ones `producer_asset_id` names for the six owners; this asset's fingerprint is the *columns it writes*, keyed by the owner row's natural key `(chart_id, ayanamsha_id, signal_type_id, configuration_jsonb)`: `graph_node_strength_contribution_jsonb` (floats; equivalence by value within the writer's rounding), `system_convergence_count`, `cross_system_consensus_count`, `contradicts_signals_array` (sorted), `valence` and `valence_source` for the `ga_vichara_v1` rows. Volatile: `computed_at` inside the payload, `formula_version` constant is kept. An idempotent rerun must leave these unchanged (this is the comparison E5.5 supplies for the PARTIAL Idem cell).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** graph centrality written back as the MSR hook, the fact-subject-level convergence counts and the contradiction back-fill; never inserts or deletes a row.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-2)
- **Opportunities (never blocking):** extend the L1-sourced (`ga_vichara_v1`) valence beyond the 6,050 rows where a vichara fact exists, so fewer of the 44,479 keyword-heuristic valences remain (an output change); put `graph_node_strength_contribution_jsonb` in the default projection (Reach).

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t3 on 2026-09-11. Migration 1210 (applied; verified live 2026-10-01 14:37Z per the coordinator): it added edges (`bo_bimba`, `ga_vichara`): `depends_on` changed, so the frozen manifest now fails the identity check (`plan_adaptation_required`). Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3). **A production rebuild of any MSR producer (SS REVIEW):** `replace_prior_msr_for_chart` deletes the writer's owned classes AND the `bodha_contradictions` rows whose `signal_a_id`/`signal_b_id` fall in them (`_idempotency.py:200-206`) and, through the three L2 keys still in force, `bodha_signal_embeddings`; the live guard refuses on non-canonical charts while Kāla dependants exist (R243) until 1214 is deployed. After the replacement `bo_samskara` (registry level 7), `bo_karanajala` (8), `bo_laksana_rerank` (9) and everything downstream re-run in DAG order. **F-3 and I-6 (read-only context; `F3_MSR_FK_DROP_v1_0.md` v1.1, DRAFT_FOR_REVIEW, branch `suvarna/land/F3-msr-fk-drop-001`, PR #2828; migration 1214 is not on main at this lane's fetch).** I-6: an unguarded MSR replace took the `kala_*` tables from 4 rows to 0 (reproduced on a disposable Postgres) and erased the canonical chart's five Kāla tables on 2026-09-08 (1214 header). Migration 1214 drops FIVE `kala_*` keys only; the three L2 keys (`bodha_contradictions` signal_a/b, `bodha_signal_embeddings`) are not in it and go through an owner-path REVIEW (BUILDER_GRANT_PLAN); SS DECLINED removing the `assert_l2_msr_delete_safe` refusal (it stays and re-arms only if a cross-layer key is re-added). After 1214 the refusal no longer fires on Kāla dependants and nothing errors if a later MSR regeneration leaves them dangling. **Mandatory rebuild-order invariant (F3 `plan_invariant.md`):** the six MSR writers (`bo_laksana`, `bo_arudha`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`, `bo_nakshatra_semantic`) run strictly BEFORE the five Kāla assets (`ka_sangam`, `ka_kalasutra`, `ka_vighnakara`, `ka_kala_darshana`, `ka_bhavishya_lekha`), `ka_yojaka`, the seven Phala assets reached through `kala_convergence`/`phala_anchors` (`ph_nimitta`, `ph_pratikara`, `ph_muhurta`, `ph_pramana`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`) and the L2 consumers (`bo_karanajala`, `bo_bimba`, `bo_samskara`, `bo_sangati`, `bo_cdlm_summary`, `bo_pratijna`), and none of them is rebuilt again later in the same window. **Charts 1c826d5a and cb73cd3d have ALL-v4 signal ids (50,171 and 49,875 signals): the first v5 regeneration of either strands every one of their Kāla rows (1c826d5a: 336,093 `kala_activation` rows) with no error, so the order guard (`msr_rebuild_order_guard.py`, PF-1/PF-2) and the dangling-reference detector are MANDATORY for those two charts; the canonical chart's 50,678 ids are all v5.** This asset must run after any MSR replacement and after `bo_karanajala` (it reads `bodha_contradictions`/`bodha_cgm_nodes`); its own rerun is idempotent and writes no row.

## 8 · Questions for Strategic Suvarṇa

1. Is the keyword-heuristic valence (44,479 of 50,678 chart rows; 34,960 `neutral` in total) an accepted documented approximation, or a Null-gate question (neutral standing for a missing computation)?
2. CF-19: confirm the rerank's six columns are declared cross-asset writes (and whether `valence` belongs to the producer or to the rerank for E5.5 fingerprint ownership).
3. Is the arch §12.9 definition of the L2 MSR set (writers whose rebuild replaces rows) to be corrected to six, with the rerank listed as an UPDATE-only dependant (MF-L2-010)?

**SS rulings (N-59, 2026-10-01; decision sheet `DECISION_SHEET_L2_v1_0.md` (PR #2841); (R) = provisional until the J1 review). The questions above are kept for the record.**

- **Q-L2-14 (R) - accepted.** The rerank's `system_convergence_count` / `cross_system_consensus_count` use the same single rule (root = fact subject, plus varga where the subject is a varga sign). Batched. TI-L2-22, TI-L2-31.
- **Q-L2-15 - accepted.** The rerank's six columns are declared cross-asset writes; `valence` and `valence_source` of `bo_laksana` rows belong to the rerank in the fingerprint contract (the producer's fingerprint excludes them). TI-L2-17.
- **Q-L2-16 (R) - changed.** The MSR set is six producers (the rerank an UPDATE-only dependant). Valence: where a category or keyword rule matched, the value is kept (a matched `neutral` too); where nothing matched and the code falls through to `neutral`, NULL is stored. FIRST every reader of `valence` is traced; if any reader breaks on NULL, SS is asked before coding. Batched after the trace. TI-L2-20, TI-L2-32.
- **Q-L2-12 - accepted.** This asset is in the CF-03 batch: the registry migration and the seed alignment (seed TO live) are pre-approved now; its floor is restated to the achieved count AFTER the one rebuild. TI-L2-10, TI-L2-24.
- **Q-L2-02 - accepted.** The producer's served surface is read through the `signal_type_class` facet of `query_signals.ts` (the 18 classes partition exactly by producer on the canonical chart). No rebuild. TI-L2-04.
- **Layer-wide (Q-L2-18, Q-L2-19, sequencing).** Build.history counts only runs since the last writer or registry change (L0 Q11 carried; TI-L2-13) and Carr uses a D3 stratified sample with the section N.5 resolver, PASS only if every sampled row re-derives (L0 Q13 grading; TI-L2-14); both are read after the one coherent L2 rebuild on main's code, in which no asset is rebuilt twice.
