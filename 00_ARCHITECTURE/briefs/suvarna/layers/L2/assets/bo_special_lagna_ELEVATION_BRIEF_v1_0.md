---
asset_id: bo_special_lagna
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
disposition_proposal_approver: "Steward (G16); any output change needs SS (R5)"
nirmana_freeze: "t3, 2026-09-11"
ledger_gap_ids: [bo_special_lagna-Idem.pattern, bo_special_lagna-Earn.build_record, bo_special_lagna-Cost.baseline, bo_special_lagna-Build.history, bo_special_lagna-Carr.detector]
---
# bo_special_lagna — Special lagnas (Indu, Śrī, Ghaṭī, Horā) as domain-salience MSR signals

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Pure L2 derivation (CR-76) over L1 `special_lagna` facts (`ga_sensitive`): one `special_lagna` signal per lagna × ayanamsha, each carrying `domain_salience` so it ranks within its classically assigned domain despite the chart-wide 0.90 class-prior discount (DR-6) (`bo_special_lagna.py` docstring). `@register("bo_special_lagna")` at `bo_special_lagna.py:105`, replacement at `:148`, INSERT at `:162`; emitter `bodha_writers/special_lagna_emitter.py`. 20 chart rows (4 × 5). The CGM node writer `bo_karanajala` adds `special_lagna` nodes from the same L1 facts (`bo_karanajala.py:1566-1585`), so the L1 set is wider than the four lagnas this MSR class signals. Frozen under the t3 definition (2026-09-11).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:2038`; seed `catalog_status` DRAFT, live CURRENT | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_special_lagna.py:105`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_msr_signals`; count_sql tables: `bodha_msr_signals` | census CEN-R |
| live rows / floor | 20 / 20 (chart 482012f1, count_sql scope) | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `ga_sensitive` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 6 / transitive 48; seed-derived closure (post-1210): direct 6 / transitive 48; direct dependents: `bo_bimba`, `bo_grounding`, `bo_karanajala`, `bo_laksana_rerank`, `bo_samskara`, `bo_sangati` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_msr_signals`: 89 non-test py/ts/tsx files reference it (65 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `ka_bhavishya_lekha.py`, `mi_adhilepa.py`, `ka_yojaka.py`, `ph_phaladesa.py`, `mi_bhavisya.py`, `ph_nimitta.py` +59 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 9 capability module(s): `L2_bodha/query_domain_reading.ts`, `L2_bodha/query_signals.ts`, `L2_bodha/query_ucd.ts`, `L2_bodha/traverse_chart_graph.ts`, `L3_kala/call_service_wrappers.ts`, `L3_kala/query_temporal_activation.ts`, `reading_checklist.ts`, `register_d8_assess_domain.ts`, `register_d9_judgment.ts`; `density_contract` declared on 3 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t3, 2026-09-11; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run e3b14cf3 complete/build (2026-09-11) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_msr_signals (bodha_writers/_idempotency.py:209 via bo_special_lagna.py → bodha_writers/_idempotency.py:replace_prior_msr_for_chart) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Build | Build.history | PARTIAL | latest run complete, but 0 error(s) and 3 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only).  |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run e3b14cf3 complete/build (2026-09-11) |
| Complete (information) | Complete.depth | PARTIAL | 150724 rows, 85 cols; fully populated 40; NEVER populated ['varga_provenance_jsonb', 'source_corroboration_count_by_verse', 'divisional_corroboration_count', 'dasha_activation_proximity_score', 'aspect_modifier', 'argala_modifier', 'salience_confidence_interval_jsonb', 'shared_factor_keys_jsonb', 'cross_domain_shared_factor_count', 'graph_edge_pattern_jsonb', 'graha_weakness_indicators_jsonb', 'recurring_pattern_mark… |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width ≥ 19/67 built column(s) (28.4%), a lower bound: L2_bodha/query_signals.ts, L3_kala/call_service_wrappers.ts select(s) a run-time column list selected by 9 capability module(s); dark: ['active… |

**PASS cells (compact):** Ldgr.source_presence (citation_ref populated on 150724/150724 rows); Vocab.identity (declared key (chart_id, ayanamsha_id, signal_type_id, build_id, configuration_jsonb): 0 duplicate(s)); Dens.served† (6 module(s): query_discoveries.ts, query_domain_reading.ts, query_pratijna.ts, query_signals.ts, query_ucd.ts,…); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=20 = live=20 (count_sql over the target table; chart 482012f1)); Build.exercised (17 executed run(s) of 22 build_run_assets row(s), scope(s): asset_set, global, layer, last executed 2026-09-11); Build.dep_liveness; Count.floor (live=20, floor=20, delta=+0).

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **NO_DETECTOR** — only a table other assets share (bodha_msr_signals) is referenced, by 19 module(s): L2_bodha/graha_portrait.ts, L2_bodha/query_discoveries.ts, L2_bodha/query_domain_reading.ts (+16 more); the served surface cannot be attributed to bodha_msr_signals by code (never the closable N/A); Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** PASS (not in the recompute's L2 gate-diff list; no change from the saved rev-1 PASS) The saved census cell Build.dag PASS † above is the rev-1 reading.

**MSR group.** This asset is one of the seven producers that target `bodha_msr_signals`; the group reading is in `INDEX.md` §3 (per-asset attribution is dark in the default projection because `producer_asset_id` is not served, so the per-asset cells above are the producer-scoped `count_sql` partitions, and Narr declarations attribute through the served `signal_type_class` facet). Chart rows: 50,678 = 45 + 14 + 20 + 25 + 45 + 50,529; table-wide 150,724 rows (MF-L2-004: never compare the two populations).

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| `bo_special_lagna-Idem.pattern` / census cell Idem.pattern PASS † | Idem | other (R243 annotation) + stale ledger row | saved census reads PASS (delete-then-insert via `replace_prior_msr_for_chart`) with no annotation (MF-L2-006); the PASS must be emitted with `chart_scope: 482012f1 only; refused via assert_l2_msr_delete_safe on 1c826d5a, cb73cd3d` (R243; W2-3_REVIEW's per-asset chart list differs for some assets, MF-L2-011: both readings are in layer instance §6.3, neither chosen). The ledger row (`ON CONFLICT where the layer convention is delete-then-insert`) is from the 2026-09-27 run and is stale. CF-13. |
| `bo_special_lagna-Earn.build_record`, `bo_special_lagna-Cost.baseline` | Earn (Cost information) | detector | instrument absent (migration 1094); CF-05; no asset change |
| `bo_special_lagna-Carr.detector` | Carr | detector | no D1/D2/D3 detector exists; CF-07 |
| `bo_special_lagna-Build.history` | Build (history) | history | latest run complete; 0 errors and 3 aborts on record. CF-10 |
| census: Null/Narr (declarations 1.6.0) | Null, Narr | detector | `prose_fields` is declared (see §0 declaration evidence); Narr/Null checks have not run (NO_DETECTOR offline); CF-14 |
| census cell Dens.served † | Dens | detector (attribution) | saved rev-1 PASS; offline rev-4 static scan NO_DETECTOR (shared table; no producer attribution by code); CF-04 |
| census cell Complete.depth | Complete (information) | information | table-wide never-populated columns, identical under all seven MSR assets; CF-17 / CF-16 |
| code: `bodha_writers/special_lagna_emitter.py:96` | Null | real-or-SS-question | every one of the five satellite emitters feeds the shared salience formula the same fixed inputs for terms it does not compute (`orb_tightness=1.0`, `shadbala_norm=1.0`, `dignity_score=0.50`, `ashtakavarga_bindus=4`; here `bodha_writers/special_lagna_emitter.py:96`), labelled `verification_pass_status="documented_approximation"`; whether the label satisfies CLAUDE.md §N.7 item 6 / §N.8 (an honest null beats an invented default) for the stored `computed_salience` is a ruling; changing it changes stored salience (output change, R5); CF-20. |

## 3 · Disposition

**keep (P)** — no cell is a measured defect of the asset: Build.completion, Count.floor and Ldgr read PASS, the Idem PASS is real once annotated (R243), the remaining cells are absent detectors and recorded history. The satellite-salience observation (CF-20) is a ruling, not a defect found by the census.

Approver under Track A brief §10: **Steward (G16); any output change needs SS (R5)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** golden fixture: the four L1 `special_lagna` facts → summary (`special_lagna_emitter.py:135`) and headline (`:139`) must state the same house, sign, lord, nakṣatra and domain list as the cited fact and `domain_salience`
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 6: `bo_bimba`, `bo_grounding`, `bo_karanajala`, `bo_laksana_rerank`, `bo_samskara`, `bo_sangati`; transitive 48); the touched surface is a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can f
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-2 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation of the domain assignment and the referenced house/sign): compare each signal's lagna house, sign, lord and nakshatra with the cited L1 `special_lagna` fact (`constituent_facts_array`); no new astronomical compute exists in this asset, so the check is reference-equality.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 6: `bo_bimba`, `bo_grounding`, `bo_karanajala`, `bo_laksana_rerank`, `bo_samskara`, `bo_sangati`; transitive 48); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-13** — MSR replacement: R243 annotation and F-3 cascade-key retirement. *This asset:* Idem PASS carries the R243 annotation; rebuild consequences below
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* declared prose columns; fidelity test to design
- **CF-20** — Neutral-constant salience inputs in the five MSR satellite emitters. *This asset:* fixed neutral inputs to the shared salience formula
- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* Dens attribution rule for the shared table
- **CF-16** — Shared-root carriers (T1 3.4): the empty columns and their counting rule. *This asset:* table-wide shared-root carrier columns are empty
- **CF-17** — Complete.depth: never-populated columns (declare, populate or drop). *This asset:* table-wide never-populated columns
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage check (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, signal_type_id, configuration_jsonb)`; owned class `special_lagna`. Fingerprint: `configuration_jsonb`, `domain_salience`, `constituent_facts_array`, `computed_salience`, `signature_tier`, headline/summary text, `citation_ref`/`citation_human`. Volatile: `signal_id`, `build_id`, `computed_at`; rerank columns excluded. A rebuild must keep 20 rows.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** one signal per classically named special lagna with its domain assignment, referencing the L1 fact.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation of the domain assignment and the referenced house/sign) (design in FD-2)
- **Opportunities (never blocking):** Complete.width universe undeclared: declare which special lagnas L1 carries and which the MSR class signals (the node writer already reads a wider set).

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t3 on 2026-09-11. Migration 1210 (applied; verified live 2026-10-01 14:37Z per the coordinator): it added no edge to this row; a `depends_on` edit (CF-15) would make the identity check throw, while `count_sql`/`natural_key_partition`/`catalog_status` edits (CF-03) only require an evidence refresh. Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3). **A production rebuild of any MSR producer (SS REVIEW):** `replace_prior_msr_for_chart` deletes the writer's owned classes AND the `bodha_contradictions` rows whose `signal_a_id`/`signal_b_id` fall in them (`_idempotency.py:200-206`) and, through the three L2 keys still in force, `bodha_signal_embeddings`; the live guard refuses on non-canonical charts while Kāla dependants exist (R243) until 1214 is deployed. After the replacement `bo_samskara` (registry level 7), `bo_karanajala` (8), `bo_laksana_rerank` (9) and everything downstream re-run in DAG order. **F-3 and I-6 (read-only context; `F3_MSR_FK_DROP_v1_0.md` v1.1, DRAFT_FOR_REVIEW, branch `suvarna/land/F3-msr-fk-drop-001`, PR #2828; migration 1214 is not on main at this lane's fetch).** I-6: an unguarded MSR replace took the `kala_*` tables from 4 rows to 0 (reproduced on a disposable Postgres) and erased the canonical chart's five Kāla tables on 2026-09-08 (1214 header). Migration 1214 drops FIVE `kala_*` keys only; the three L2 keys (`bodha_contradictions` signal_a/b, `bodha_signal_embeddings`) are not in it and go through an owner-path REVIEW (BUILDER_GRANT_PLAN); SS DECLINED removing the `assert_l2_msr_delete_safe` refusal (it stays and re-arms only if a cross-layer key is re-added). After 1214 the refusal no longer fires on Kāla dependants and nothing errors if a later MSR regeneration leaves them dangling. **Mandatory rebuild-order invariant (F3 `plan_invariant.md`):** the six MSR writers (`bo_laksana`, `bo_arudha`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`, `bo_nakshatra_semantic`) run strictly BEFORE the five Kāla assets (`ka_sangam`, `ka_kalasutra`, `ka_vighnakara`, `ka_kala_darshana`, `ka_bhavishya_lekha`), `ka_yojaka`, the seven Phala assets reached through `kala_convergence`/`phala_anchors` (`ph_nimitta`, `ph_pratikara`, `ph_muhurta`, `ph_pramana`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`) and the L2 consumers (`bo_karanajala`, `bo_bimba`, `bo_samskara`, `bo_sangati`, `bo_cdlm_summary`, `bo_pratijna`), and none of them is rebuilt again later in the same window. **Charts 1c826d5a and cb73cd3d have ALL-v4 signal ids (50,171 and 49,875 signals): the first v5 regeneration of either strands every one of their Kāla rows (1c826d5a: 336,093 `kala_activation` rows) with no error, so the order guard (`msr_rebuild_order_guard.py`, PF-1/PF-2) and the dangling-reference detector are MANDATORY for those two charts; the canonical chart's 50,678 ids are all v5.** 

## 8 · Questions for Strategic Suvarṇa

1. CF-20: is the neutral-constant salience input set (documented_approximation) accepted for the satellites, or must uncomputed terms be NULL?
2. CF-13: is the R243 chart list for this asset final (R243 vs W2-3_REVIEW differ for some satellites, MF-L2-011)?
