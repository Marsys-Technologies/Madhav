---
asset_id: bo_karanajala
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
disposition_proposal_approver: "Steward (G16); FD-2's output change needs SS (R5)"
nirmana_freeze: "t3, 2026-09-11"
decisions_applied: "SS decision N-59 (2026-10-01) on DECISION_SHEET_L2_v1_0.md (PR #2841); items marked (R) provisional until J1; section 8 lists the rulings for this asset"
track_i_items: [TI-L2-36, TI-L2-02, TI-L2-10, TI-L2-13, TI-L2-14, TI-L2-16, TI-L2-17, TI-L2-19, TI-L2-30, TI-L2-33]
ledger_gap_ids: [bo_karanajala-Idem.pattern, bo_karanajala-Build.completion, bo_karanajala-Earn.build_record, bo_karanajala-Cost.baseline, bo_karanajala-Dens.served, bo_karanajala-Build.history, bo_karanajala-Carr.detector]
---
# bo_karanajala — CGM edges and contradictions (Kāraṇajāla)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Builds the Causal Graph Model's directed, valenced edges over `bodha_cgm_nodes` and the contradictions register: it reads `bodha_msr_signals` and `bodha_cgm_nodes` and writes `bodha_cgm_edges` (849 chart rows: aspect 360, argala 119, bhava_aspect 95, arudha_house 95, lordship 60, occupancy 45, dispositor 40, special_lagna_house 35; layer instance §2.2 [Q3b]) and `bodha_contradictions` (not readable by the census login). `@register("bo_karanajala")` at `bo_karanajala.py:1739` (a 1,922-line writer), replacement through `replace_prior_cgm_edges` and `replace_prior_contradictions` (`:1909-1910`). Two cross-asset behaviours are in the file: it INSERTs the `arudha` and `special_lagna` nodes into `bodha_cgm_nodes` through `ON CONFLICT (node_id)` (`:1532-1650`; 130 live rows) and it UPDATEs centrality columns on `bo_bimba`'s nodes (`:1878`). Build record 864 against 849 live: `rows_inserted = total_e + total_c` (`:1921`) counts the contradictions the registry `count_sql` does not. Census direct 10 / transitive 44. Migration 1210 added its `ga_vichara` edge (E6 reads-match); frozen under the t3 definition (2026-09-11).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1627` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_karanajala.py:1739`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_cgm_edges`; count_sql tables: `bodha_cgm_edges` | census CEN-R |
| live rows / floor | 849 / 300 (chart 482012f1, count_sql scope) — count_sql counts `bodha_cgm_edges` only; the writer also writes contradictions and 130 nodes | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_laksana`, `bo_bimba`, `ga_positions`, `bo_sudarshana`, `bo_nakshatra_semantic`, `bo_arudha`, `bo_special_lagna`, `bo_vargottama_dhana`, `ga_vichara` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 10 / transitive 44; seed-derived closure (post-1210): direct 10 / transitive 44; direct dependents: `bo_anveshana`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_drishti`, `bo_laksana_rerank`, `bo_pramana_mapa`, `bo_samvada`, `bo_sangati`, `bo_yantra_mechanism`, `ph_nimitta` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_cgm_edges`: 17 non-test py/ts/tsx files reference it (9 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `ph_phaladesa.py`, `stage2_promise.py`, `assetClearSpec.ts`, `address_resolver.ts`, `graha_portrait.ts`, `traverse_chart_graph.ts` +3 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 1 capability module(s): `L2_bodha/traverse_chart_graph.ts`; `density_contract` declared on 0 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t3, 2026-09-11; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 5d4d8d71 complete/skip_no_delta (2026-09-11) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_cgm_edges (bodha_writers/_idempotency.py:358 via bo_karanajala.py → bodha_writers/_idempotency.py:replace_prior_cgm_edges), bodha_cgm_edges (bodha_writers/_idempotency.py:363 via bo_karanajala.py → bodha_writers/_idempotency.py:replace_prior_cgm_edges) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served† | FAIL | 2 module(s): query_contradictions.ts, traverse_chart_graph.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record rows_written=864 disagrees with live=849 (count_sql over the target table; chart 482012f1) |
| Build | Build.history | PARTIAL | latest run complete, but 26 error(s) and 7 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-09): UniqueViolation: duplicate key value violates unique constraint "bodha_cgm_nodes_pkey" DETAIL:  Key (node_id)=(fa521b87-6dcc-5b75-84a9-e61c67bc353c) already exists. Traceback (most recent call last):  |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 5d4d8d71 complete/skip_no_delta (2026-09-11) |
| Complete (information) | Complete.depth | PARTIAL | 2517 rows, 43 cols; fully populated 34; NEVER populated ['intrinsic_strength', 'directionality', 'weight_varga_source', 'cross_subsystem_mapping_ref', 'cancelled_by_jsonb', 'cross_ayanamsha_edge_stability_score', 'edge_betweenness', 'in_shortest_path_count'] |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width ≥ 15/35 built column(s) (42.9%), a lower bound: L2_bodha/traverse_chart_graph.ts select(s) a run-time column list selected by 1 capability module(s); dark: ['active_dasha_periods_jsonb', 'act… |

**PASS cells (compact):** Ldgr.source_presence (citation_ref populated on 2517/2517 rows); Vocab.identity (declared key (chart_id, ayanamsha_id, build_id, snapshot_type, edge_type, from_node_id, to_node_id): 0 duplica…); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.exercised (49 executed run(s) of 121 build_run_assets row(s), scope(s): asset_set, global, layer, last executed 2026-09-1…); Build.dep_liveness; Count.floor (live=849, floor=300, delta=+549).

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **NO_DETECTOR** — 1 serving-root file(s) naming bodha_cgm_edges lose the string scanner's sync (an unbalanced quote, a nested template literal, or a regex literal holding a quote desynced it): platform-mcp/src/tools/registry_bridge.ts; its served select and density_contract cannot be read — never FAIL,; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** FAIL — missing edge `bo_karanajala → ga_vichara` (reads `chart_vichara` at `bo_karanajala.py:222`; ordering held transitively via `bo_bimba`, `bo_laksana`). **Migration 1210 added that edge; per its header the rev-2 detector reads PASS afterwards.** The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| `bo_karanajala-Build.completion` | Build (completion) | real (attribution; cause read in code, not measured) | build record 864 vs live 849: the writer returns edges + contradictions (`:1921`) and `count_sql` counts edges only, so 15 is consistent with the contradiction rows (table unreadable to the census login: MF-L2-002). CF-02. |
| code: `bo_karanajala.py:1532-1650`, `:1878`; declarations `cross_asset_writes: null` | Idem / Build | real (declaration + Idem scope) | the asset upserts 130 nodes into `bo_bimba`'s table and updates its centrality columns, but declares no cross-asset write; `replace_prior_cgm_nodes` (bimba's) deletes only bimba's five node types and the node insert is `ON CONFLICT (node_id)`, so arudha/special_lagna nodes are never deleted by either writer: if an L1 arudha or special-lagna fact disappears its node would remain (upsert-only, the L0 CF-12 class). The census Idem PASS covers `bodha_cgm_edges` only. The 2026-09-09 history error (`UniqueViolation … bodha_cgm_nodes_pkey`) is on this path (fixed since, migrations 714/950 per the code comment). CF-19, CF-12. |
| code: `bo_karanajala.py:386-391` vs `ga_writers/ga_structural_writer.py:615-616` | Carr / Vocab | real (ANSWERED by SS: reference L1) | L2 builds argala edges from house offsets it computes itself, `ARGALA_POSITIONS = {2, 4, 11}` with virodha `{12, 3, 10}` (BPHS Ch.28, `_build_argala_edges` `:495`), while L1 already stores `argala_natal_matrix` / `virodha_argala_natal_matrix` (144 atomic rows each, `ga_structural_writer.py:54-55`) from offsets `[2, 4, 5, 11]` / `[12, 10, 9, 3]` (Jaimini, `:615-616`): two conventions and a re-derivation where an L1 authority exists. **ANSWERED (SS ruling, relayed by the coordinator 2026-10-01): by CLAUDE.md §N.5 L1 is the authority and L2 never recomputes an L1 fact, so `bo_karanajala` must REFERENCE L1's computed argala ({2, 4, 5, 11}, Jaimini); if L2 genuinely needs the BPHS {2, 4, 11} variant, it is a separately named, cited convention, never a silent second definition.** What remains open is only whether L2 needs the BPHS variant as a named class. FD-2. |
| code: `bo_karanajala.py` docstring `:7-18` vs layer instance §2.2 [Q3b] | Complete (information) | information | edge types named in the docstring with 0 live rows on the chart: `conjunction`, `yoga_domain`, `dosha_domain`, `sade_sati` (the eight live types are listed above). Whether yoga/dosha nodes should be joined to domain nodes is a modelling question; `Complete.width` (no declared universe) cannot say. |
| `bo_karanajala-Dens.served` / census cell Dens.served † | Dens | detector (rev 1 FAIL; rev 4 NO_DETECTOR) | saved rev-1 FAIL (2 modules, 0 contracts); offline rev-4 scan unreadable (scanner desync in `registry_bridge.ts`). The served edges expose 15 of 35 built columns; `citation_ref`, `citation_human`, `constituent_fact_ids_array`, `cross_system_consensus_count` and `verification_pass_status` are dark (Reach, information). CF-04. |
| `bo_karanajala-Idem.pattern` | Idem | stale | ledger row (`ON CONFLICT where the layer convention is delete-then-insert`) is from 2026-09-27; saved census PASS for the edges, offline rev-2 PASS. |
| `bo_karanajala-Complete.depth` (census) | Complete (information) | information | NEVER populated (table-wide, 2,517 rows): `intrinsic_strength`, `directionality`, `weight_varga_source`, `cross_subsystem_mapping_ref`, `cancelled_by_jsonb`, `cross_ayanamsha_edge_stability_score`, `edge_betweenness`, `in_shortest_path_count`. `cancelled_by_jsonb` empty while `cancelled_flag` is non-null on all 849 chart rows (T2 §6.3 requires cancelled support and inhibitor to keep opposite polarity; not measured). CF-17. |
| `bo_karanajala-Build.history` | Build (history) | history | latest run complete; 26 errors and 7 aborts on record (latest error 2026-09-09 `UniqueViolation … bodha_cgm_nodes_pkey`). CF-10. |
| `bo_karanajala-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent (migration 1094) / no D1-D3 detector; CF-05, CF-07. |
| census: registry `natural_key_partition` | Idem | real (registry) | blank for this asset (MF-L2-009), though it owns edges, contradictions and 130 nodes. CF-03. |

## 3 · Disposition

**keep (P)** — the asset builds and its census cells are clean apart from the attribution mismatch; its real findings are two declaration/scope gaps and one cross-layer convention question (argala), none a measured failure. If SS rules the argala edge must read L1, FD-2 is an output change; the disposition stays keep.

Approver under Track A brief §10: **Steward (G16); FD-2's output change needs SS (R5)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Declare and scope the cross-asset node writes

- **SS ruling (N-59, 2026-10-01):** (1) The cross-asset writes (`bodha_cgm_nodes` arudha/special_lagna rows, the centrality UPDATE) are declared and the orphan census run now; (2) the node builder moves to `bo_bimba` in the same change as Q-L2-06, in the one rebuild. TI-L2-17, TI-L2-30.
- **Answers:** CF-19, CF-12; the Idem/Build declaration gap above
- **Change:** declare `bodha_cgm_nodes.*` (arudha, special_lagna rows) and the centrality UPDATE as this asset's cross-asset writes; extend the Idem reading (or its orphan census) to the node upsert: run the node builder in `ctx.dry_run`, compare the produced `(node_type, node_subject)` set with the live arudha/special_lagna nodes and report orphans; if orphans can occur, add a prune scoped to `node_type IN ('arudha','special_lagna')` in `replace_prior` (never table-wide); record the shared table as two producers in the registry attribution
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json`; `bo_karanajala.py` / `bodha_writers/_idempotency.py` (scoped prune, only if orphans are found); registry `natural_key_partition` and `count_sql` via CF-03
- **Failing-first test and mutation:** failing-first: a fixture where an L1 arudha fact is removed leaves a stale node (census FAIL naming it) and the prune removes only that node; mutation: widen the prune to all node types → the shared-table test (bimba's nodes survive) fails
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 10: `bo_anveshana`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_drishti`, `bo_laksana_rerank`, `bo_pramana_mapa`, `bo_samvada`, `bo_sangati`, `bo_yantra_mechanism`, `ph_nimitta`; transitive 44); the touched surface is `platform/scripts/governance/asset_declarations.json`
- **Rebuild:** the prune is exercised by the next rebuild; a prune that deletes nothing is not a rebuild trigger (REVIEW item for SS if it does)
- **Gate it moves:** Idem, Build (completion attribution)
- **Fix class:** registry/declaration + writer code (prune, only if orphans exist); **buildable before J1:** tier-dependent: what Idem means for upsert writers (TGH-T3-18) and the `kind`/producer vocabulary (TGH-T4-01)

### FD-2 · Argala edges reference L1's computed argala (SS ruling: ANSWERED)

- **SS ruling (N-59, 2026-10-01):** No separate BPHS {2,4,11} class. The virodha pairing, the Rahu/Ketu reversal and the empty-source-sign score of 1.0 go to the L1 sheet as L1 items (L1 owns the pairing); this asset's argala fix lands after the L1 ruling; a graha edge is created only where an occupant exists; 'BPHS Ch. 28' is replaced by the chunk ids and marked `sourced_ocr_unverified`. Batched, gated on the L1 ruling. TI-L2-16, TI-L2-33.
- **Answers:** the Carr/Vocab argala observation; CLAUDE.md §N.5; SS ruling relayed 2026-10-01
- **Change:** build the argala edges from L1's `argala_natal_matrix` / `virodha_argala_natal_matrix` facts (which source signs have argala on a target sign, offsets {2, 4, 5, 11}, Jaimini) joined to `graha_position` (which grahas occupy those signs), citing the L1 `fact_id`s in `constituent_fact_ids_array`, instead of recomputing `ARGALA_POSITIONS` from sign numbers (`_build_argala_edges` `:495`); remove `ARGALA_POSITIONS`/`VIRODHA_POSITIONS` (`:386-391`) from the writer. If a domain reading shows L2 genuinely needs the BPHS Ch.28 {2, 4, 11} variant, emit it only as a separately named, cited class (its own `relationship_class`/`semantic_path_class` and source citation) alongside, never as the default `argala` edge
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/bo_karanajala.py` (`:386-391`, `:495-560`); no L1 change (L1 is the authority)
- **Failing-first test and mutation:** failing-first: every stored argala edge corresponds to an L1 matrix row (same source sign, target sign, position) and cites its `fact_id`; no edge exists at an offset L1 does not list; mutation: re-introduce a local offset set → the test fails (`test_bo_karanajala_*` exists for other edge types)
- **Output change:** yes: the argala edge set changes (the 5th-position/9th-virodha edges L1 lists would appear; edges that exist only under the BPHS set would go or be renamed): SS (R5)
- **Blast radius:** output change: this asset's registry dependents see new values after the rebuild (direct 10: `bo_anveshana`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_drishti`, `bo_laksana_rerank`, `bo_pramana_mapa`, `bo_samvada`, `bo_sangati`, `bo_yantra_mechanism`, `ph_nimitta`; transitive 44)
- **Rebuild:** needs production rebuild of `bo_karanajala` and its dependents (`bo_cgm_motifs`, `bo_cgm_paths`, `bo_yantra_mechanism`, `bo_laksana_rerank`, `bo_sangati`, `bo_drishti`, `bo_anveshana`, `bo_pramana_mapa`, `bo_samvada`, `bo_chart_gestalt`, plus `ph_nimitta` and the L3/L5 readers): 44-asset transitive closure, REVIEW item for SS; the F-3 invariant applies
- **Gate it moves:** Carr, Vocab
- **Fix class:** writer code; **buildable before J1:** tier-independent in direction (SS ruled the principle); the Carr assignment stays tier-dependent
- **Question for SS:** Does L2 need the BPHS {2, 4, 11} variant as a separately named class at all?

### FD-3 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** a golden fixture over the six `citation_human` sites (`:625` argala offset and cancellation, `:708`, `:785`, `:1672`, `:1732` placements, `:1360` contradiction naming shared domains): the string must state the same house/sign numbers and the same cancelled/uncancelled state as the cited L1 fact and the edge's own `cancelled_flag`; pure endpoint labels (`:1024 :1147 :1199 :1269`) are excluded by the declaration
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 10: `bo_anveshana`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_drishti`, `bo_laksana_rerank`, `bo_pramana_mapa`, `bo_samvada`, `bo_sangati`, `bo_yantra_mechanism`, `ph_nimitta`; transitive 44); the touched surface is a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can f
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-4 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): recompute each edge's existence and class from L1 facts it cites (aspect/house relation from `graha_position`, lordship from the canonical sign-lord table, arudha_house and special_lagna_house from the cited L1 fact) and compare; argala edges are checked against L1's matrix once FD-2 is ruled. The §N.5 resolver covers the MSR side only; a twin for `constituent_fact_ids_array` is part of this design.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 10: `bo_anveshana`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_drishti`, `bo_laksana_rerank`, `bo_pramana_mapa`, `bo_samvada`, `bo_sangati`, `bo_yantra_mechanism`, `ph_nimitta`; transitive 44); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-02** — Producer attribution: multi-table writers, rider rows and shared tables (count scope). *This asset:* build record counts contradictions the `count_sql` omits (864 vs 849)
- **CF-19** — cross_asset_writes declarations (writes into rows another asset owns). *This asset:* cross-asset node writes (FD-1)
- **CF-12** — Idem: an orphan census for upsert-only writes (a PASS on the delete does not test accretion elsewhere). *This asset:* the node upsert is upsert-only (orphans possible); the same orphan census as L0's CF-12
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* blank `natural_key_partition`; count scope
- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* Dens FAIL on two modules; 20 of 35 built columns dark
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* declared `citation_human` (six composed sites)
- **CF-15** — depends_on audit: declared edges versus what each writer reads. *This asset:* 1210 added `ga_vichara`; declared edges versus reads re-audit
- **CF-17** — Complete.depth: never-populated columns (declare, populate or drop). *This asset:* never-populated columns
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, snapshot_type, from_node_id, to_node_id, edge_type, …)` is not declared in the registry (blank `natural_key_partition`); the table's unique key is the one `Vocab.identity` read for `bodha_cgm_edges` (not stated in the census text for this asset: read it from the catalog before E5.5). Fingerprint over edge endpoints (resolved to node natural keys, not `node_id`), `edge_type`, `relationship_class`, `valence`, `computed_strength`, `cancelled_flag`, `constituent_fact_ids_array`, `underlying_msr_signal_ids_array` (sorted; ids resolved to signal natural keys) and the contradiction pairs. **Volatile:** `edge_id`, `node_id` endpoints as raw ids, `build_id`, `computed_at`, `engine_version`; centrality columns on nodes belong to the nodes' fingerprint. Expected: 849 edges, plus the contradiction rows, unchanged by an idempotent rebuild.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the eight live edge types with L1-resolving `constituent_fact_ids_array` (non-empty on 330 of 849 chart rows, a partial carrier; instance §2.2), the contradiction register, the arudha/special-lagna nodes.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-4)
- **Opportunities (never blocking):** the four documented edge types with no rows; `cancelled_by_jsonb`; serve `constituent_fact_ids_array` and `citation_human` on edges (Reach).

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t3 on 2026-09-11 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 (applied; verified live 2026-10-01 14:37Z per the coordinator) added this row's direct edge(s) `ga_vichara`, so its frozen manifest is stale against the registry fingerprint (1210 header, CONSEQUENCES 1: the identity check throws on any `depends_on` change, so the monitor reads `plan_adaptation_required`). Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (`bo_anveshana`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_drishti`, `bo_laksana_rerank`, `bo_pramana_mapa`, `bo_samvada`, `bo_sangati`, `bo_yantra_mechanism`, `ph_nimitta`) re-run after it in DAG order; seed-derived transitive closure 44 assets. **F-3 invariant (this asset carries or derives from MSR signal ids):** it must be rebuilt strictly after every MSR producer and not before a later MSR regeneration in the same window (`msr_rebuild_order_guard.py`, F3 `plan_invariant.md`); I-6: an unguarded MSR replace took the `kala_*` tables from 4 rows to 0 and erased the canonical chart's five Kāla tables on 2026-09-08; charts 1c826d5a and cb73cd3d (all-v4 ids) make the guard mandatory; see INDEX §7. Rebuilding this asset rewrites 130 nodes it does not own and the contradictions that cascade from MSR replacement; `bo_laksana_rerank` reads its output, so the DAG order is karanajala (level 8) then rerank (9) then `bo_sangati` (10). Its direct dependents are the 10 named above, but the transitive closure is 44 assets (it feeds `bo_sangati`, which feeds 13 more).

## 8 · Questions for Strategic Suvarṇa

1. FD-2 (principle ANSWERED: reference L1): does L2 need the BPHS {2, 4, 11} variant as a separately named, cited class?
2. FD-1 / CF-12: is node ownership of `arudha`/`special_lagna` to stay with `bo_karanajala` (declared cross-asset write) or move to `bo_bimba`'s node builder (the in-code comment says it was placed here because bimba was outside the lane's scope)?
3. Edge types in the docstring with no live rows (`yoga_domain`, `dosha_domain`, `conjunction`, `sade_sati`): intended for this chart, or unwired?

**SS rulings (N-59, 2026-10-01; decision sheet `DECISION_SHEET_L2_v1_0.md` (PR #2841); (R) = provisional until the J1 review). The questions above are kept for the record.**

- **Q-L2-01 - accepted.** The produced-table set of this asset is declared (option A) with a detector clause; `count_sql` is neither widened nor narrowed. The reader SELECT on the 10 unreadable `bodha_*` tables goes first (they are owned by `data_plane_l2_owner` and pinned in the ownership preflight, so it is a D6 plan with hash as REVIEW, not an amjis_app migration); the gap in this asset's count is confirmed from the tables before the detector is written. TI-L2-01, TI-L2-02.
- **Q-L2-06 (R) - changed.** `yoga_node_subject` (shared with `bo_bimba`) changes with the identity fix; the `yoga_member` edges and every key built on it follow, per the design REVIEW SS will see before coding. Batched. TI-L2-19, TI-L2-30.
- **Q-L2-15 - accepted.** (1) The cross-asset writes (`bodha_cgm_nodes` arudha/special_lagna rows, the centrality UPDATE) are declared and the orphan census run now; (2) the node builder moves to `bo_bimba` in the same change as Q-L2-06, in the one rebuild. TI-L2-17, TI-L2-30.
- **Q-L2-21 / A-1 (R) - accepted.** No separate BPHS {2,4,11} class. The virodha pairing, the Rahu/Ketu reversal and the empty-source-sign score of 1.0 go to the L1 sheet as L1 items (L1 owns the pairing); this asset's argala fix lands after the L1 ruling; a graha edge is created only where an occupant exists; 'BPHS Ch. 28' is replaced by the chunk ids and marked `sourced_ocr_unverified`. Batched, gated on the L1 ruling. TI-L2-16, TI-L2-33.
- **Q-L2-12 - accepted.** This asset is in the CF-03 batch: the registry migration and the seed alignment (seed TO live) are pre-approved now; its floor is restated to the achieved count AFTER the one rebuild. TI-L2-10, TI-L2-24.
- **Layer-wide (Q-L2-18, Q-L2-19, sequencing).** Build.history counts only runs since the last writer or registry change (L0 Q11 carried; TI-L2-13) and Carr uses a D3 stratified sample with the section N.5 resolver, PASS only if every sampled row re-derives (L0 Q13 grading; TI-L2-14); both are read after the one coherent L2 rebuild on main's code, in which no asset is rebuilt twice.
- **TI-L2-36 (SS, 2026-10-02) - added to the batch.** The five `single_pass` literals (`bo_karanajala.py:706`, `:783`, `:1022`, `:1670`, `:1730`) switch to the `single` constant of `brahmagyan/verification_vocab.py` (grandfathered in the AST guard). Tier respelling: L1 writers now emit `single`, never `single_pass` (PR #2854); the F-10 tier-inversion count is not read between S-L1 and S-L2 (INDEX 12.4). One rebuild, no asset rebuilt twice.
