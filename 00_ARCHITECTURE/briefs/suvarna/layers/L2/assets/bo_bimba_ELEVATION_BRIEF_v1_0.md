---
asset_id: bo_bimba
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
disposition_proposal_approver: "Steward (G16); FD-1's output change needs SS (R5)"
nirmana_freeze: "t3, 2026-09-11"
ledger_gap_ids: [bo_bimba-Idem.pattern, bo_bimba-Build.completion, bo_bimba-Earn.build_record, bo_bimba-Cost.baseline, bo_bimba-Complete.depth, bo_bimba-Dens.served, bo_bimba-Build.history, bo_bimba-Carr.detector]
---
# bo_bimba — CGM nodes: one `bodha_cgm_nodes` row per chart entity

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

The node registry of the Causal/Cosmic Graph Model: one `bodha_cgm_nodes` row per entity active in the chart, extracted from `bodha_msr_signals` after `bo_laksana` (`bo_bimba.py` docstring): `graha` (9), `bhava` (1-12), `domain` and `yoga`/`dosha` nodes, `snapshot_type = static_natal`. `@register("bo_bimba")` at `bo_bimba.py:615`, INSERT at `:68`, replacement through `replace_prior_cgm_nodes` (`:658` → `bodha_writers/_idempotency.py:343`), which deletes only the owned node types `bhava, domain, dosha, graha, yoga`; centrality columns are left NULL here and back-filled by `bo_karanajala`. The table also holds `arudha` and `special_lagna` nodes inserted by `bo_karanajala` (`bo_karanajala.py:1532-1650`), which is why the build record (255) is less than the live count (385): 255 + 130 (arudha 95 + special_lagna 35, layer instance §1.1, Q7). Census blocking radius direct 8 / transitive 45 (10 direct in the seed-derived post-1210 closure: migration 1210 added the edges from `bo_laksana_rerank` and `bo_yantra_mechanism`). Frozen under the t3 definition (2026-09-11).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1676` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_bimba.py:615`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_cgm_nodes`; count_sql tables: `bodha_cgm_nodes` | census CEN-R |
| live rows / floor | 385 / 140 (chart 482012f1, count_sql scope) — 385 chart rows = 255 written by this asset + 130 `arudha`/`special_lagna` nodes written by `bo_karanajala` | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_laksana`, `bo_sudarshana`, `bo_nakshatra_semantic`, `bo_arudha`, `bo_special_lagna`, `bo_vargottama_dhana` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 8 / transitive 45; seed-derived closure (post-1210): direct 10 / transitive 45; direct dependents: `bo_anveshana`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_chart_gestalt`, `bo_karanajala`, `bo_laksana_rerank`, `bo_pramana_mapa`, `bo_yantra_mechanism`, `ka_yojaka`, `ph_nimitta` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_cgm_nodes`: 20 non-test py/ts/tsx files reference it (8 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `ka_yojaka.py`, `taranga_service.py`, `stage2_promise.py`, `writer.py`, `graha_portrait.ts`, `traverse_chart_graph.ts` +2 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 1 capability module(s): `L2_bodha/traverse_chart_graph.ts`; `density_contract` declared on 0 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t3, 2026-09-11; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 0a3236eb complete/build (2026-09-11) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_cgm_nodes (bodha_writers/_idempotency.py:343 via bo_bimba.py → bodha_writers/_idempotency.py:replace_prior_cgm_nodes), bodha_cgm_nodes (bodha_writers/_idempotency.py:348 via bo_bimba.py → bodha_writers/_idempotency.py:replace_prior_cgm_nodes) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served† | FAIL | 1 module(s): traverse_chart_graph.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record rows_written=255 disagrees with live=385 (count_sql over the target table; chart 482012f1) |
| Build | Build.history | PARTIAL | latest run complete, but 25 error(s) and 7 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-06): BLOCKED: upstream dependency(ies) bo_laksana did not complete in this run; skipped to avoid building on incomplete data |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 0a3236eb complete/build (2026-09-11) |
| Complete (information) | Complete.depth | PARTIAL | 1101 rows, 45 cols; fully populated 20; NEVER populated ['source_subsystem', 'clustering_coefficient', 'closeness_centrality', 'core_number', 'cgm_subgraph_cluster_id', 'configuration_constituents_array', 'hub_score', 'hub_edge_types_array', 'cross_ayanamsha_presence_score', 'node_embedding_vec', 'ephemeris_audit_jsonb', 'msr_salience_version_used', 'cdlm_version_used'] |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 16/32 built column(s) (50.0%) selected by 1 capability module(s); dark: ['ayanamsha_id', 'build_id', 'chart_id', 'citation_human', 'citation_ref', 'computed_at', 'configuration_lifecycle_stat… |

**PASS cells (compact):** Ldgr.source_presence (citation_ref populated on 1101/1101 rows); Vocab.identity (declared key (chart_id, ayanamsha_id, build_id, snapshot_type, node_type, node_subject): 0 duplicate(s)); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.exercised (46 executed run(s) of 118 build_run_assets row(s), scope(s): asset_set, global, layer, last executed 2026-09-1…); Build.dep_liveness; Count.floor (live=385, floor=140, delta=+245).

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **NO_DETECTOR** — 1 serving-root file(s) naming bodha_cgm_nodes lose the string scanner's sync (an unbalanced quote, a nested template literal, or a regex literal holding a quote desynced it): platform-mcp/src/tools/registry_bridge.ts; its served select and density_contract cannot be read — never FAIL,; Idem.pattern rev 2 reads **PASS**.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| `bo_bimba-Build.completion` | Build (completion) | real (attribution; cause established) | build record `rows_written=255` vs live 385. The 130 difference is exactly the `arudha` 95 + `special_lagna` 35 nodes `bo_karanajala` upserts into this table (layer instance §1.1/MF-L2-008, Q7 verified). Not a failed build: the count scope covers a table two writers share. CF-02, CF-19. |
| code: `bo_bimba.py:252-258`, `:491-505`; declaration evidence `bo_bimba` prose_fields | Narr / Vocab | real-or-SS-question | `_yoga_config_name` returns `configuration_jsonb.fact_value_text` first, then `yoga_name`, `dosha_name`, `name`, `label`, then `signal_type_id`; its result titles the node (`node_label_human`, `:505`), builds `citation_human` (`:523`) and keys the node (`yoga_node_subject`, `:261-271`, slug of the name). The E6.1 declaration evidence records on the native chart `citation_human` values 'Dosha node: afflicted', 'Yoga node: true' and 'Yoga node: 1984-02-05T19:29:13+00:00', i.e. a computed status or timestamp used as a name (CLAUDE.md §N.7 items 1 and 6). Whether distinct yogas/dosha collapse onto one `node_subject` (for example `yoga:true`) is not measured: compare distinct yoga/dosha `(class, signal_type_id)` in `bodha_msr_signals` with distinct yoga/dosha `node_subject` in `bodha_cgm_nodes` on 482012f1. FD-1. |
| `bo_bimba-Dens.served` / census cell Dens.served † | Dens | real as measured at rev 1; offline rev 4 NO_DETECTOR | saved rev-1 FAIL (1 module `traverse_chart_graph.ts`, 0 declaring a contract). The offline rev-4 scan could not read the served surface because `platform-mcp/src/tools/registry_bridge.ts` desyncs the scanner's string reader (never FAIL, never PASS). CF-04. |
| `bo_bimba-Complete.depth` (census) | Complete (information) | information | NEVER populated (table-wide): `source_subsystem`, `clustering_coefficient`, `closeness_centrality`, `core_number`, `cgm_subgraph_cluster_id`, `configuration_constituents_array`, `hub_score`, `hub_edge_types_array`, `cross_ayanamsha_presence_score`, `node_embedding_vec`, `ephemeris_audit_jsonb`, `msr_salience_version_used`, `cdlm_version_used`. The registry row declares `storage_type = pgvector` and its description says the node carries a `VECTOR(768)` embedding (`asset_registry_seed.ts:1676-1690`), while `node_embedding_vec` is never populated. CF-03 (registry truth), CF-17. |
| `bo_bimba-Earn.build_record`, `bo_bimba-Cost.baseline` | Earn (Cost information) | detector | instrument absent (migration 1094); CF-05; no asset change |
| `bo_bimba-Carr.detector` | Carr | detector | no D1/D2/D3 detector exists; CF-07 (design in FD below) |
| `bo_bimba-Build.history` | Build (history) | history | latest run complete; 25 errors and 7 aborts on record (latest error 2026-08-06, `BLOCKED: upstream dependency bo_laksana did not complete`). CF-10 |
| `bo_bimba-Idem.pattern` | Idem | stale | ledger row (`no idempotency pattern in the writer's own SQL — it likely delegates`) is from the 2026-09-27 run; the saved census reads PASS (`replace_prior_cgm_nodes`, `_idempotency.py:343`, scoped to the five owned node types) and the offline rev-2 scan keeps PASS. |

## 3 · Disposition

**keep (P)** — the asset is a sound node builder by the census except the record-versus-live mismatch, which is an attribution fact (two writers, one table), not a defect; the one code defect candidate (yoga/dosha node naming) needs a measurement and a ruling and is a bounded writer change (FD-1) that must not touch node identity. The preserved kernel is the deterministic node set with its `fact_id`-resolving citations.

Approver under Track A brief §10: **Steward (G16); FD-1's output change needs SS (R5)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Separate a yoga/dosha node's display name from its identity key

- **Answers:** the Narr/Vocab candidate above; CLAUDE.md §N.7 items 1 and 6
- **Change:** split `_yoga_config_name` into (a) the unchanged identity input used by `yoga_node_subject` (so every `node_id`, derived by `bodha_cgm_node_identity()` from `node_subject`, is unchanged and no edge in `bo_karanajala` re-wires) and (b) a display name that never reads `fact_value_text`: `yoga_name`, `dosha_name`, `name`, `label`, then the L1/L0 catalogue name for `signal_type_id`; use (b) for `node_label_human` and `citation_human`. If the measurement above shows two distinct yogas share a `node_subject`, report it as a separate identity finding (an identity-mapping change, SS).
- **Files / declaration / migration:** `platform/python-sidecar/pipeline/orchestrator/writers/bo_bimba.py` (`_yoga_config_name` `:252`, label `:505`, citation `:523`) and its consumers of `yoga_node_subject` (`bo_karanajala.py`)
- **Failing-first test and mutation:** failing-first: a fixture yoga signal whose `fact_value_text` is 'true' / a timestamp produces a label from the catalogue name and the same `node_subject` as before; mutation: make the display name read `fact_value_text` again → the test fails; extends `test_nar_bo_bimba_dignity.py`'s approach (fixtures reproducing the live shapes)
- **Output change:** yes: `node_label_human` and `citation_human` text change on the affected yoga/dosha nodes (no id change): SS (R5)
- **Blast radius:** local to node display text; node ids, edges and every downstream asset's keys are unchanged. Readers of `node_label_human`: `traverse_chart_graph.ts`, `graha_portrait.ts` and the L3/L4 readers of `bodha_cgm_nodes` named in §0
- **Rebuild:** needs production rebuild of `bo_bimba` (idempotent, per-chart delete-then-insert); no downstream re-run is required for ids, but `bo_karanajala` rewrites node centrality on its next run (REVIEW item for SS)
- **Gate it moves:** Narr (NO_DETECTOR → measured), Vocab (display versus identity)
- **Fix class:** writer code; **buildable before J1:** tier-dependent: waits on the Narr rule for composed names (SS 2026-10-01 ruling exists; the "name from a status text" case needs the verdict) and on the measurement
- **Question for SS:** Display name only, or is a `node_subject` collision between distinct yogas also in scope (an identity change)?

### FD-2 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** extend the existing `test_nar_bo_bimba_dignity.py` shape to the yoga/dosha `citation_human` and `node_label_human` strings: a fixture of MSR yoga/dosha signals reproducing the live shapes ('afflicted', 'true', a timestamp) must yield catalogue-based names; graha/bhava/domain labels stay constant structural labels
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents); the change is local to this asset’s record or declaration unless the output change says otherwise
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-3 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): recompute each graha node's `dignity_state` and house from L1 `graha_dignity_per_varga` and `graha_position` facts and compare; recompute the bhava/domain node set from the canonical vocabularies. A node whose stored dignity differs from L1 is the §N.5 halt case.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents); the change is local to this asset’s record or declaration unless the output change says otherwise
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-02** — Producer attribution: multi-table writers, rider rows and shared tables (count scope). *This asset:* shared table with `bo_karanajala` (385 = 255 + 130): scope the completion comparison per writer
- **CF-19** — cross_asset_writes declarations (writes into rows another asset owns). *This asset:* declare that `bo_karanajala` writes into this table (see that brief); this asset's own delete is scoped to its five node types
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* registry truth: `storage_type`/description claim a vector column that is never populated
- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* Dens: served only through `traverse_chart_graph.ts`; no contract; 16 of 32 built columns exposed
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* declared prose `citation_human` (4 composed sites)
- **CF-17** — Complete.depth: never-populated columns (declare, populate or drop). *This asset:* never-populated columns above
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, snapshot_type, node_type, node_subject)` for the node types this asset owns (`bhava, domain, dosha, graha, yoga`); the `arudha`/`special_lagna` rows belong to `bo_karanajala`'s partition. Fingerprint: `node_label_human`, `position_in_chart_jsonb`, `strength_score`, `dignity_state`, `degree_in`/`degree_out` (before the back-fill), `citation_ref`, `citation_human`, `verification_pass_status`. **Volatile:** `node_id` (a deterministic function of the natural key, but a surrogate), `build_id`, `computed_at`, and every centrality column `bo_karanajala` back-fills (`pagerank`, `betweenness`, `eigenvector`, `harmonic_centrality`, `degree_*` after wiring). `node_embedding_vec` is never populated; an embedding equivalence policy is not needed until it is.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** one node per graha, bhava, domain, yoga and dosha with a `citation_ref` resolving to L1, `dignity_state` read from L1 `graha_dignity_per_varga` (fixed on main: `test_nar_bo_bimba_dignity.py`), the snapshot type.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-3)
- **Opportunities (never blocking):** populate or drop the vector column and the igraph metrics the description promises; declare the node-type universe (`Complete.width`).

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t3 on 2026-09-11 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 added no edge to this row; any registry edit proposed in §4 (`count_sql`, `natural_key_partition`, `catalog_status`, `depends_on`, `integrity_check_sql`) enters `registryContractFingerprintInput` and would stale the manifest. The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (`bo_anveshana`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_chart_gestalt`, `bo_karanajala`, `bo_laksana_rerank`, `bo_pramana_mapa`, `bo_yantra_mechanism`, `ka_yojaka`, `ph_nimitta`) re-run after it in DAG order; seed-derived transitive closure 45 assets. Idempotent per-chart delete-then-insert of the owned node types only; `bo_karanajala` must re-run afterwards because it back-fills centrality onto these rows and wires edges to their ids.

## 8 · Questions for Strategic Suvarṇa

1. FD-1: display-name-only fix (no identity change), and is the measurement of yoga/dosha node-subject collisions to be run before the fix is approved?
2. CF-02 / CF-19: record the shared `bodha_cgm_nodes` table as two producers (255 + 130) so the build record compares per producer?
3. Registry truth: drop the `pgvector` storage type and the VECTOR(768) wording, or populate `node_embedding_vec` (an output change)?
