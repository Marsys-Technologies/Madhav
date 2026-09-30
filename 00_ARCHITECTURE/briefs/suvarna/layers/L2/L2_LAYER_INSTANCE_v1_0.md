---
artifact: L2_LAYER_INSTANCE
canonical_id: SUVARNA_L2_LAYER_INSTANCE
version: "1.0"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_on: 2026-09-30
produced_in: "Exec Suvarṇa"
plan_item: "A.L2i (Track A brief §4, step 2); acceptance is A.L2a / N-10.L2.i, after J1 and A.L2r"
branch: "suvarna/land/A.L2i-analysis-001"
layer: "L2 Bodha (23 active assets, bo_*)"
template: "LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md (tier 3, SEALED), read at checkout 2a78ec64d"
census_run:
  output: "/Users/Dev/suvarna-evidence/census/census_L2.json (+ census_L2.log, SUMMARY.md)"
  exit_code: 2   # FAIL rows present = measured (arch §12.14); no exit 4/5/75
  inspector_commit: "2a78ec64d88e59438bd6527b4c99826432102c57 (checkout /Users/Dev/suvarna-census)"
  generated: "2026-09-30T20:23:30+05:30"
  chart_scope: "482012f1-710e-4a25-994a-93821f5871aa"
  login: "suvarna_reader via the proxy on 127.0.0.1:5433 (read-only)"
companion: "L2_TIER_GAPS_v1_0.md (same directory): TG-L2-001..022 tier gaps, MF-L2-001..013 measurement findings, Q1..Q7 / G1..G2 read definitions"
changelog:
  - "1.0 (2026-09-30): first draft. Filled from the four tiers and the L2 census; the earlier skeleton and inventions under nikasha_test/derivations/ were read as inputs and re-measured, not copied. Part 6 records the Track A layer specifics (MSR asset list, cascade victims, R243 annotation, bo_upaya state, the six ERRORED cells)."
---

# L2 Bodha — layer definition and strategy, instance v1.0 (first draft)

> **PROVISIONAL — until J1; may register gaps, may not certify.** This draft rests on tiers that are sealed but
> carry an open reopen agenda, and on a provisional census. It certifies nothing, writes no ledger or register
> line, and is not cited by anything below it until the layer instance is accepted (A.L2a).

**How to read the tags.** Every figure carries its source. `[C: …]` is a field of the census JSON (path
`L2.assets[*].measurements[<criterion>]`, or a header field of `L2`). `[Q1]`–`[Q7]` are the read-only queries and
`[G1]`–`[G2]` the git/GitHub reads defined in `L2_TIER_GAPS_v1_0.md` Part D (SQL for the ones used here is in
Appendix A). `[W: file:line]` is a writer or library file at the inspected checkout (population:
`platform/python-sidecar/pipeline/orchestrator/writers/bo_*.py` and `platform/python-sidecar/bodha_writers/`, commit
2a78ec64d; identical to `origin/main` e2352f881 [G1]). Tier clauses are cited `T1`/`T2`/`T3`/`T4` with section and line.
"Not measured" always states its reason. **Two populations recur and must not be compared:** *chart-scoped*
(canonical chart 482012f1: every `count_sql`, every Q3 count) and *table-wide* (all charts: the census
`Complete.depth`, `Ldgr.source_presence`).

The census tallies this layer as 452 cells: 266 PASS, 70 NO_DETECTOR, 46 PARTIAL, 46 NOT_GENERIC, 13 FAIL, 6 ERRORED, 5 N/A over 23 assets [C: all measurements]. Header facts: 23 registered ids and 23
`has_writer` registry rows; 0 phantom ids; 0 assets with a writer never exercised; 22 of 23 `count_sql` bound to the
chart (the constant one is `bo_samvada`); 61 global runs, of which 565 touched this layer [C: `L2.registered_ids`,
`registry_has_writer`, `phantom_registered`, `never_exercised_with_writer`, `chart_scoped_count_sql`, `global_runs`,
`global_runs_touching_layer`].

---

## Part 0 · VALUE — the origin

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none — definitional; every P/V cited must exist in the parent under current numbering
traces_to:   —  (this IS the origin)
```

**TIER GAP: TG-L2-001.** The template asks for the P-needs and V-journeys for which L2 is *necessary — cannot be
answered without*. Neither parent assigns any P or V to a layer, so the necessity table is left empty rather than
written from judgement. What the tiers do say about L2's place in a question, quoted and not converted into an
assignment:

| tier clause | what it says | P / V it touches by the tier's own text |
|---|---|---|
| T2 §3.1 (141) | L2 owns the question "What does the chart's connected structure permit us to interpret?" | none named |
| T1 §5 (308) | "Interpretive queries retain the governed whole-chart Bodha consultation before domain detail. Pinpointed factual lookups retain the frame-check and escalation valve rather than a full synthesis." | the interpretive class is not enumerated by P-id; the lookup class is P16's first half (T1 §2, 171) |
| T2 §6.3 (367) | "Whole-chart Bodha consultation is the floor for an interpretive query, not permission to answer from a gestalt alone." | as above |
| T2 §12.1 (582) | in the financial story "L2 constructs the relevant resource-creation and retention mechanisms, including applicable derived-house relations and counter-evidence" | the financial promise: T2 §2 V02 (118) lists P03–P04 |
| T2 §5 (327; 338) | Graha contextual roles: "L2 mechanism"; Āyurdāya: "L2 constitutional structure" | V01 (117); V12 (128) with P07, P23 |
| T1 §8.1 (424) | with the life-event switch ON, L2's use is "Historical comparison of proposed structural interpretations and rival expressions" | V06 (122), P12 (T1 §2, 167) |
| T2 §13.1 (640), §13.2 (650–654) | W04 "L2 connected-meaning slice"; the first implementable slice is canonical meaning → qualified structural distinction → faithful delivered finding | the financial / configuration journey and a Bhāvat Bhāvam case |

The catalog-provenance measure that R85 built (which retrieval catalog units name L2 assets as producers, and the
necessity closure over `depends_on`) exists but its output was not among this draft's inputs; R221 keeps the T3
clause as written until the T3 reopen.

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 (this layer's row), Data plane §3.1 (this layer's row)
measured_by: none — definitional
traces_to:   0.1
```

*Not a tier gap.* T2 §6.3 (361–367) supplies the L2 narrative; the paragraph below is assembled from T1 §1 (46–64),
T2 §1 (60–67), §3.1 (141) and §6.3, and adds no claim of its own.

Conventional Jyotish software computes each element on demand and leaves the reasoning to the reader; the data plane
"computes the whole estate *and the relationships between its parts*, and holds them together so a reasoning layer
can find what connects" (T2 §1, 63–66). Bodha is the layer that does that holding for the chart. It turns L1's
reproducible facts into "a structural mechanism with participants, roles, configuration membership, relevant
domains, supporting/opposing conditions, original fact references, source rules and alternatives" (T2 §6.3, 365):
chart-specific propositions, typed graph relationships, paths, motifs and mechanisms, cross-domain, contradiction
and whole-chart synthesis, and hypothesis and frame-specific assets. Summaries, salience, embeddings and graph
centrality are navigation aids; they "cannot replace the relevant ledgers or certify a causal mechanism", and "a
low-ranked bridge can be decisive to a question and must remain discoverable" (T2 §6.3, 367).

- **Owned question** (T2 §3.1, 141): "What does the chart's connected structure permit us to interpret?"
- **Contribution handed onward** (T2 §3.1, 141): "Whole-chart context, qualified structural propositions, signed
  relationships, configurations, contradictions, alternate routes and candidate mechanisms."
- **What it must not claim** (T2 §3.1, 141): "Graph centrality as causation, catalog matches as confirmed formation,
  temporal hooks as independent clock evidence."
- **Proof obligations it is scored on** (T1 §11, 502): "Concept and relationship completeness + Interpretive fidelity
  (§14): contributions beyond isolated placements; shared roots visible (§3.4); complete prerequisites and
  exceptions." Two of the ten (T3 §3.1, 392).
- **Layer-distinctive fill** (T3, 681): "shared roots visible (several assets from one placement are not independent
  confirmations); 1.3 is where whole-chart reading lives or fails."
- **Identity of record:** 23 active assets (registry, `layer = 'bodha'`, all `is_active`; Q1) writing 17
  distinct registry target tables; scoring mode `contribution` (a chart-product layer, so the reference-layer clauses
  of T3 §1.2, §1.5 and §5.1 do not apply) [C: `L2.scoring`, `L2.n_assets`, `L2.population_active`,
  `L2.population_registry_total` = 23, `L2.population_excluded_inactive` = []].

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types), §7 (DP contracts)
measured_by: registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement
traces_to:   0.2
```

**The three sources of the dependency graph.** Live `asset_registry` (Q1, 127 active rows) was read and is the only
source used below. **TIER GAP: TG-L2-002** — seed and migration pin are named by the template and located by no tier;
they were not read, so no disagreement can be stated. The census emits per-asset edge counts only (`Build.dag` PASS on
23 of 23, e.g. "6 edge(s), all resolvable" [C: `Build.dag`]); the edge lists in §2.5 come from Q1.

**Edge types.** **TIER GAP: TG-L2-003.** T2 §3.2 (146–166) defines five edge types; no source assigns one to any real
edge, and the registry stores only `depends_on` (computational edges). One observation follows from that: the
vocabulary owner is not upstream of L2 in the registry's terms — the layer's declared upstream set is 13
assets, `bg_rules` from L0 (of 40) and 12 of 19 L1 assets:
`bg_rules` (1), `ga_condition` (1), `ga_dashas` (1), `ga_nakshatra` (2), `ga_panchanga` (1), `ga_positions` (6), `ga_sade_sati` (1), `ga_sensitive` (2), `ga_strength` (1), `ga_structural` (4), `ga_vargas` (2), `ga_vichara` (1), `ga_yoga` (1) (count = number of L2 assets declaring it) [Q1]. DP01 (identity/release, L0 → all writers) is
therefore a definition edge that no `depends_on` records, which T2 §3.2 item 1 allows ("It need not trigger a chart
rebuild when only a display alias changes").

**Receives from** (T2 §7.1, 418–425; layer-level, by DP contract):

| contract | producer → consumer | what L2 takes, in T2's words |
|---|---|---|
| DP01 Identity/release | L0 → all adapters and writers | "Canonical entities, qualified aliases, units and released definitions; local representations cannot diverge in meaning." |
| DP02 Rule qualification | L0 → calculation, interpretation, investigator | "Exact rule clauses, method, school/tradition, the prerequisites and exceptions that must be tested, the source witness behind each variant reading, unresolved alternatives and executable scope." |
| DP03 Chart facts | L1 → L2–L4/services | "`fact_id`, grain/value/unit, chart/build, ayanāṃśa/frame/varga, input precision and verification; no downstream re-derivation." |
| DP04 Condition decomposition | L1 → L2/L3/L4 | "Separate condition/bala/benefit/functional role, constituents and reasons. Retain zeros as zeros and unavailable as unavailable." |
| DP05 Configuration | L0+L1 → L2 → L3 | "Formation, participants, every clause tested with its result — passed, partial, failed — and cancellation; hydrate actual configuration before timing." |

**Hands onward to** (T2 §7.1, 425–427):

| contract | producer → consumer | what L2 hands on, in T2's words |
|---|---|---|
| DP06 Structural relationship | L2 → L3 and inquiry | "Actor/relation/target, all relevant domains, constituent facts/signals, signed support/opposition, condition/occurrence ledgers, variants and ancestry." |
| DP05 (relay) | L2 → L3 | hydrated configuration before timing |
| DP08 Temporal mechanism | L2 + qualified clocks → L3 consumers | "Same mechanism/configuration ID, engaged participants, qualified necessary/optional conditions, enablement/inhibition, alternate routes, horizon … No topology-only gating." |

Per-asset assignment of these contracts, and the declared use of each (calculation, applicability, counter-evidence,
uncertainty, interpretation, exclusion, navigation, evaluation): **TIER GAP: TG-L2-004** (see §2.3).

**Measured downstream edges** (registry `depends_on`, computational edges; Q1): 9 of 23 L2 assets
are declared upstream of at least one non-L2 asset; 14 are not (`bo_arudha`, `bo_cdlm_summary`, `bo_cgm_motifs`, `bo_chart_gestalt`, `bo_drishti`, `bo_grounding`, `bo_laksana_rerank`, `bo_nakshatra_semantic`, `bo_pramana_mapa`, `bo_samvada`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`, `bo_yantra_mechanism`).

| L2 asset | non-L2 assets declaring it in `depends_on` | which |
|---|---|---|
| `bo_anveshana` | 1 | `ph_nimitta` |
| `bo_arudha` | 0 | - |
| `bo_bimba` | 2 | `ka_yojaka`, `ph_nimitta` |
| `bo_cdlm_summary` | 0 | - |
| `bo_cgm_motifs` | 0 | - |
| `bo_cgm_paths` | 1 | `ph_nimitta` |
| `bo_chart_gestalt` | 0 | - |
| `bo_drishti` | 0 | - |
| `bo_grounding` | 0 | - |
| `bo_karanajala` | 1 | `ph_nimitta` |
| `bo_laksana` | 9 | `ka_bhavishya_lekha`, `ka_kalasutra`, `ka_sangam`, `ka_yojaka`, `mi_adhilepa`, `mi_bhavisya`, `ph_nimitta`, `ph_phaladesa`, `ph_sodhana` |
| `bo_laksana_rerank` | 0 | - |
| `bo_nakshatra_semantic` | 0 | - |
| `bo_pramana_mapa` | 0 | - |
| `bo_pratijna` | 5 | `ka_avadhi`, `ka_kshetra`, `ka_taranga`, `ka_yojaka`, `mi_darshana` |
| `bo_samskara` | 1 | `ph_nimitta` |
| `bo_samvada` | 0 | - |
| `bo_sangati` | 4 | `ka_kshetra`, `ka_yojaka`, `ph_nimitta`, `ph_sankrama` |
| `bo_special_lagna` | 0 | - |
| `bo_sudarshana` | 0 | - |
| `bo_upaya` | 2 | `ka_kshetra`, `ph_pratikara` |
| `bo_vargottama_dhana` | 0 | - |
| `bo_yantra_mechanism` | 0 | - |

Family note: `ka_sangam` and `ka_kshetra` are family assets (plan §5.3); both read L2 (`bo_laksana`; `bo_pratijna`,
`bo_sangati`, `bo_upaya`). The serving-context edge (T2 §3.2 item 3: the whole-chart consultation floor) is not a
registry edge and is measured only through `Dens.served` in §1.4.

**What the join needs from it** (T1 §11, 502; T2 §3.1): the whole-chart structural depth listed under 0.2. Which
fields the reasoning layer needs exposed is the presentation question of §2.2 (TG-L2-010); what is currently exposed is
measured in §1.4.

### 0.4 · The alignment test

Run by the author on this draft. Every section from Part 1 carries `traces_to:` naming a 0.1 row, or a 0.2 or 0.3
item; **no section was struck**. Sections that could not be filled from the tiers are kept and marked
"TIER GAP" because each still traces to Part 0 and the hole is itself the finding; none was padded. The reviewer runs
the test again (T3 §0.4).

---

## Part 1 · VALUE DECOMPOSITION — the layer is the sum of its assets and services

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: asset_registry (live, read-only; Q1) · the census (C) · writer files at 2a78ec64d (W) · Q3 for chart-scoped counts. Registry seed and migration pin: NOT read (TG-L2-002). asset_throughput and the tracker probe: not used (the census replaces them).
traces_to:   0.3
```

Population: the 23 active L2 assets. All are registry kind `data`; 22 have a table target, one (`bo_samvada`) a view.
Kinds the template lists — *service (no table by design)*: none; *residual*: none flagged (`data_disposition`, `dead_flag` and `superseded_by` are empty on all 23; Q1);
*shared*: `bodha_msr_signals` (seven registered producers) and `bodha_cgm_nodes` (two writers); *historical*: the legacy
table `bodha_rm_dasha_windowed_prescriptions`, which no current writer touches (R244; unreadable to the reader, MF-L2-002).
**TIER GAP: TG-L2-007** for the kind vocabulary (a view target; an UPDATE-only writer; writers that write more tables
than the registry names).

| asset | registry storage | registry `target_table` | live rows, chart 482012f1 (count_sql) | floor | delta | table-wide rows / cols / fully populated (`Complete.depth`, all charts) | executed runs / last executed | catalog_status |
|---|---|---|---|---|---|---|---|---|
| `bo_anveshana` | postgres_table | `bodha_discoveries` | not measured (permission denied) | 500 | not measured | 3,695 / 30 / 28 | 38 / 2026-09-10 | CURRENT |
| `bo_arudha` | postgres_table | `bodha_msr_signals` | 25 | 15 | +10 | 150,724 / 85 / 40 | 16 / 2026-09-10 | CURRENT |
| `bo_bimba` | pgvector | `bodha_cgm_nodes` | 385 | 140 | +245 | 1,101 / 45 / 20 | 46 / 2026-09-11 | CURRENT |
| `bo_cdlm_summary` | postgres_table | `bodha_cdlm_chart_summary` | 5 | 1 | +4 | 15 / 23 / 19 | 41 / 2026-09-09 | CURRENT |
| `bo_cgm_motifs` | postgres_table | `bodha_cgm_motifs` | 600 | 0 | n/a | 1,811 / 16 / 16 | 45 / 2026-09-09 | CURRENT |
| `bo_cgm_paths` | postgres_table | `bodha_cgm_paths` | 45 | 9 | +36 | 135 / 20 / 20 | 44 / 2026-09-09 | CURRENT |
| `bo_chart_gestalt` | postgres_table | `bodha_chart_gestalt` | 5 | 1 | +4 | 15 / 20 / 19 | 36 / 2026-09-10 | CURRENT |
| `bo_drishti` | postgres_table | `bodha_question_lenses` | 60 | 60 | +0 | 180 / 15 / 15 | 42 / 2026-09-09 | CURRENT |
| `bo_grounding` | postgres_table | `bodha_grounding_matches` | 50,731 | 0 | n/a | 50,731 / 13 / 10 | 2 / 2026-09-12 | DRAFT |
| `bo_karanajala` | postgres_table | `bodha_cgm_edges` | 849 | 300 | +549 | 2,517 / 43 / 34 | 49 / 2026-09-11 | CURRENT |
| `bo_laksana` | postgres_table | `bodha_msr_signals` | 50,529 | 60000 | -9471 | 150,724 / 85 / 40 | 74 / 2026-09-08 | CURRENT |
| `bo_laksana_rerank` | postgres_table | `bodha_msr_signals` | 11,094 | 1 | +11093 | 150,724 / 85 / 40 | 18 / 2026-09-11 | CURRENT |
| `bo_nakshatra_semantic` | postgres_table | `bodha_msr_signals` | 45 | 45 | +0 | 150,724 / 85 / 40 | 19 / 2026-09-11 | CURRENT |
| `bo_pramana_mapa` | postgres_table | `synthesis_quality_scorecard` | 1 | 1 | +0 | 3 / 34 / 30 | 40 / 2026-09-10 | CURRENT |
| `bo_pratijna` | postgres_table | `bodha_pratijna` | 135 | 0 | n/a | 405 / 16 / 10 | 45 / 2026-09-09 | CURRENT |
| `bo_samskara` | pgvector | `bodha_signal_embeddings` | 50,678 | 60000 | -9322 | 150,724 / 10 / 10 | 62 / 2026-09-11 | CURRENT |
| `bo_samvada` | postgres_view | `vw_chart_digest` | 5 | 0 | n/a | 15 / 13 / 13 | 40 / 2026-09-11 | CURRENT |
| `bo_sangati` | postgres_table | `bodha_cdlm_cells` | not measured (permission denied) | 70 | not measured | 430 / 59 / 30 | 47 / 2026-09-11 | CURRENT |
| `bo_special_lagna` | postgres_table | `bodha_msr_signals` | 20 | 20 | +0 | 150,724 / 85 / 40 | 17 / 2026-09-11 | CURRENT |
| `bo_sudarshana` | postgres_table | `bodha_msr_signals` | 45 | 45 | +0 | 150,724 / 85 / 40 | 16 / 2026-09-10 | CURRENT |
| `bo_upaya` | pgvector | `bodha_rm_resonances` | not measured (permission denied) | 180 | not measured | 135 / 24 / 18 | 47 / 2026-09-09 | CURRENT |
| `bo_vargottama_dhana` | postgres_table | `bodha_msr_signals` | 14 | 10 | +4 | 150,724 / 85 / 40 | 16 / 2026-09-11 | CURRENT |
| `bo_yantra_mechanism` | postgres_table | `bodha_mechanisms` | 615 | 1 | +614 | 1,868 / 24 / 18 | 16 / 2026-09-09 | CURRENT |

*Notes.* "Live rows" are `count_sql` over the target table for chart 482012f1 [C: `Build.completion`, `Count.floor`;
for `bo_samvada` the census counts the view itself, because its registry `count_sql` is the constant `SELECT 0 AS
count`, MF-L2-007]. Floors are aspirational, not gates (CLAUDE.md §N.4): `bo_laksana` (50,529 vs 60,000) and
`bo_samskara` (50,678 vs 60,000) read FAIL and are recorded as information. Three rows are **not measured**: their
completion and floor checks raised `permission denied` for the read-only login (§6.5). "Table-wide" figures are all charts.

**Target tables are a set, not a pointer (T3 §1.1).** The registry names one `target_table` per asset, and each
`count_sql` counts one or two tables. The writers write more. Static scan of each writer file for `INSERT INTO`,
`DELETE FROM` and `replace_prior_*` (population: the 23 registered ids' writer files; `bo_laksana` and
`bo_laksana_rerank` share `bo_laksana.py`):

| asset | registry `target_table` | tables its `count_sql` counts (census `count_sql_tables`) | tables its writer file inserts into or deletes from (static scan) | written but not counted |
|---|---|---|---|---|
| `bo_anveshana` | `bodha_discoveries` | `bodha_discoveries`, `bodha_anomalies`* | `bodha_discoveries`, `bodha_anomalies`* | - |
| `bo_arudha` | `bodha_msr_signals` | `bodha_msr_signals` | `bodha_msr_signals` | - |
| `bo_bimba` | `bodha_cgm_nodes` | `bodha_cgm_nodes` | `bodha_cgm_nodes` | - |
| `bo_cdlm_summary` | `bodha_cdlm_chart_summary` | `bodha_cdlm_chart_summary` | `bodha_cdlm_chart_summary`, `bodha_cdlm_domain_rollups`*, `bodha_cdlm_pattern_clusters`* | `bodha_cdlm_domain_rollups`, `bodha_cdlm_pattern_clusters` |
| `bo_cgm_motifs` | `bodha_cgm_motifs` | `bodha_cgm_motifs` | `bodha_cgm_motifs`, `bodha_cgm_sub_graphs`*, `bodha_cgm_chart_topology_summary`* | `bodha_cgm_sub_graphs`, `bodha_cgm_chart_topology_summary` |
| `bo_cgm_paths` | `bodha_cgm_paths` | `bodha_cgm_paths` | `bodha_cgm_paths` | - |
| `bo_chart_gestalt` | `bodha_chart_gestalt` | `bodha_chart_gestalt` | `bodha_chart_gestalt` | - |
| `bo_drishti` | `bodha_question_lenses` | `bodha_question_lenses` | `bodha_question_lenses` | - |
| `bo_grounding` | `bodha_grounding_matches` | `bodha_grounding_matches` | `bodha_grounding_matches` | - |
| `bo_karanajala` | `bodha_cgm_edges` | `bodha_cgm_edges` | `bodha_cgm_edges`, `bodha_cgm_nodes`, `bodha_contradictions`* | `bodha_cgm_nodes`, `bodha_contradictions` |
| `bo_laksana` | `bodha_msr_signals` | `bodha_msr_signals` | `bodha_msr_signals` | - |
| `bo_laksana_rerank` | `bodha_msr_signals` | `bodha_msr_signals` | (none inserted or deleted: UPDATE-only on `bodha_msr_signals`; shares writer file `bo_laksana.py`) | - |
| `bo_nakshatra_semantic` | `bodha_msr_signals` | `bodha_msr_signals` | `bodha_msr_signals` | - |
| `bo_pramana_mapa` | `synthesis_quality_scorecard` | `synthesis_quality_scorecard` | `synthesis_quality_scorecard` | - |
| `bo_pratijna` | `bodha_pratijna` | `bodha_pratijna` | `bodha_pratijna` | - |
| `bo_samskara` | `bodha_signal_embeddings` | `bodha_signal_embeddings` | `bodha_signal_embeddings` | - |
| `bo_samvada` | `vw_chart_digest` | `vw_chart_digest` | (none: view target; no INSERT/DELETE in the writer file) | - |
| `bo_sangati` | `bodha_cdlm_cells` | `bodha_cdlm_cells`, `bodha_triangulation`* | `bodha_cdlm_cells`, `bodha_convergence`*, `bodha_triangulation`* | `bodha_convergence` |
| `bo_special_lagna` | `bodha_msr_signals` | `bodha_msr_signals` | `bodha_msr_signals` | - |
| `bo_sudarshana` | `bodha_msr_signals` | `bodha_msr_signals` | `bodha_msr_signals` | - |
| `bo_upaya` | `bodha_rm_resonances` | `bodha_rm_resonances`, `bodha_rm_remedy_prescriptions`* | `bodha_rm_resonances`, `bodha_rm_remedy_prescriptions`*, `bodha_rm_chart_summary`*, `bodha_rm_dosha_remedy_bundles`*, `bodha_rm_pattern_remedies`* | `bodha_rm_chart_summary`, `bodha_rm_dosha_remedy_bundles`, `bodha_rm_pattern_remedies` |
| `bo_vargottama_dhana` | `bodha_msr_signals` | `bodha_msr_signals` | `bodha_msr_signals` | - |
| `bo_yantra_mechanism` | `bodha_mechanisms` | `bodha_mechanisms` | `bodha_mechanisms` | - |

`*` = the read-only login cannot SELECT the table (Q4).

Two tables have more than one writer: `bodha_msr_signals` (six inserting writers; §6.1) and `bodha_cgm_nodes`
(`bo_bimba` and `bo_karanajala`; the live 385 rows split 255 by `bo_bimba`'s build record and 130 `arudha` (95) and
`special_lagna` (35) nodes [C: `bo_bimba` `Build.completion`; Q7]). **TIER GAP: TG-L2-005** for how a shared table is
expressed and counted; the census `Complete.depth` still prints the whole-table figure under every producer (MF-L2-004).

**Deployed versus current code (T3 §1.1, "risk").** **TIER GAP: TG-L2-006.** Measured: the L2 writer files and
`bodha_writers/` are byte-identical between the inspected checkout and `origin/main` e2352f881 [G1]; one unmerged live
head exists for L2, PR #2773 for `bo_upaya` (§6.4) [G2]. Not measured: the deployed image tag, and any other unmerged
head. The risk number (current code − deployed) is therefore not computed.

### 1.2 · Individual contribution — ablate one

```
inherits:    Product §14.1 (ablation), Data plane §12.2
measured_by: ablation of the single asset against the layer's served reading; where no served path exists, state "unmeasurable — not reached" and cite the six-state position from 1.4
traces_to:   0.1 (which rows this asset serves)
```

**TIER GAP: TG-L2-008.** No ablation harness exists, and no tier defines the served reading or question set the
ablation would run against, so the individual term is **not measured for any of the 23 assets** — an absent
instrument, not a number.

The template's own escape applies to one asset. `bo_grounding` (catalog status DRAFT) has no serving module
(`Dens.served` N/A, 0 modules), no non-L2 registry dependent, and a census blocking radius of 0 direct / 0 transitive
[C: `Dens.served`; `blocking_radius`; Q1]; no other L2 writer reads its table (static scan, §3.4). T3 (189–190) says
such an asset "has already answered the question for this term … record ≈ 0 and let 1.5 decide", and T3 (245) adds
that "lack of a caller in a bounded search is not redundancy". Recorded: ≈ 0 on this term, no disposition implied.

### 1.3 · Synergistic contribution — ablate the group

```
inherits:    Data plane §3.4 (presentation contract), §7 (DP contracts), the layer's synergy binding if one exists
measured_by: ablation of the shared contracts / vocabulary / ordering against the layer's served reading, holding individual assets in place
traces_to:   0.2
```

**TIER GAP: TG-L2-008.** L2's synergy binding does not exist: T2 §3.5 (207–241) names four *plane-level* seams and
cross-layer ablation as the instrument, and lists no L2 seam. The synergistic term is **absent instrument**; no
fraction is written (T3 §1.5, 249–251). Per T3 §1.5 the seam-by-seam measurement is recorded as the value, with what
each seam's census evidence can and cannot show:

| T2 §3.5 seam | what the census measures | result | what it cannot show |
|---|---|---|---|
| controlled vocabulary (§4.1) | `Vocab.identity` (rule 1, declared key) | PASS 22 of 23; no cell for `bo_samvada`; map census `local_map_candidates` = −1, not measured [C] | rules 2–6; any cross-asset name resolution |
| DP contracts (§7) | nothing per asset (TG-L2-004) | not measured | any field computed and not received |
| edge ordering (§3.2) | `Build.dag`, `Build.dep_liveness`, `Build.history` | `Build.dag` PASS 23/23; `Build.dep_liveness` PASS 17, PARTIAL 6 (an upstream has moved since the asset was built); `Build.history` PARTIAL 23/23 (each with recorded errors or aborts) [C] | whether output composed correctly |
| presentation contract (§3.4) | nothing (TG-L2-010, -011) | not measured | acharya rendering derivability |

L2's own defining rule — shared roots visible (T1 §3.4; T3, 681) — cannot be measured either: no tier defines a root
(**TIER GAP: TG-L2-021**), and the columns the schema names for it are empty (§2.1).

### 1.4 · Cross-layer handoff — what it produces for downstream

```
inherits:    Data plane §11 (six evidence states), §7 (DP contracts this layer PRODUCES)
measured_by: for each produced contract, its position on source-present → qualified → consumed → traceably transformed → served → value evaluated, verified at the consumer
traces_to:   0.3 (hands onward)
```

**TIER GAP: TG-L2-009.** Nothing is verified at the consumer: the census measures the producer side of `served` and the
registry records declared dependents. Position of the layer-level contracts (DP06; DP05 relay; DP08 input):

| state (T2 §11, 572) | evidence available | reading |
|---|---|---|
| source-present | `Complete.depth` counts rows in the target table of all 22 table-target assets (table-wide) and the census counts 5 rows in the view on the chart [C] | reached; completion against the build record is unmeasured for three assets (§6.5) |
| method-qualified | no per-asset qualification field; `classical_sources_jsonb` is non-null on 189 of 50,678 chart MSR rows [Q3] | not measured; sparse where measurable |
| consumed | registry `depends_on` edges to non-L2 assets exist for 9 of 23 assets | declared, not verified at the consumer |
| traceably transformed | no probe | not measured |
| served | `Dens.served`: 14 PASS, 8 FAIL, 1 N/A (`bo_grounding`, no serving module) [C] | producer-side only; the 8 FAILs are surfaces that exist with no declared density contract |
| value evaluated | no ablation (TG-L2-008) | not measured |

Served surface and exposure per asset (`Reach.fields` is reported, not graded, `NOT_GENERIC` on 23 of 23 [C]; "≥" marks a lower bound where a serving module selects a run-time column list; depth is an upper bound). Two of the 14 `Dens.served` PASSes, `bo_cdlm_summary` and `bo_samskara`, sit beside a `Reach.fields` reading of **0 capability modules reading their table** (depth 0.0%): the two census criteria disagree about whether those assets are served (MF-L2-013):

| asset | `Dens.served` | serving modules / declaring a density contract | fields exposed / built (`Reach.fields` width) | depth (upper bound) | non-L2 registry dependents |
|---|---|---|---|---|---|
| `bo_anveshana` | PASS | 2 / 1 | 21/28 (75.0%) | 100.0% | 1 |
| `bo_arudha` | PASS | 6 / 3 | ≥ 19/67 (28.4%) | 100.0% | 0 |
| `bo_bimba` | FAIL | 1 / 0 | 16/32 (50.0%) | 100.0% | 2 |
| `bo_cdlm_summary` | PASS | 1 / 1 | 0/19 (0.0%) | 0.0% | 0 |
| `bo_cgm_motifs` | FAIL | 1 / 0 | 12/16 (75.0%) | 100.0% | 0 |
| `bo_cgm_paths` | FAIL | 1 / 0 | 16/20 (80.0%) | 100.0% | 1 |
| `bo_chart_gestalt` | PASS | 1 / 1 | 16/19 (84.2%) | 100.0% | 0 |
| `bo_drishti` | PASS | 2 / 1 | 12/15 (80.0%) | 100.0% | 0 |
| `bo_grounding` | N/A | 0 / 0 | 0/13 (0.0%) | 0.0% | 0 |
| `bo_karanajala` | FAIL | 2 / 0 | ≥ 15/35 (42.9%) | 100.0% | 1 |
| `bo_laksana` | PASS | 6 / 3 | ≥ 19/67 (28.4%) | 100.0% | 9 |
| `bo_laksana_rerank` | PASS | 6 / 3 | ≥ 19/67 (28.4%) | 100.0% | 0 |
| `bo_nakshatra_semantic` | PASS | 6 / 3 | ≥ 19/67 (28.4%) | 100.0% | 0 |
| `bo_pramana_mapa` | FAIL | 1 / 0 | 14/30 (46.7%) | 100.0% | 0 |
| `bo_pratijna` | PASS | 1 / 1 | 11/16 (68.8%) | 100.0% | 5 |
| `bo_samskara` | PASS | 1 / 1 | 0/10 (0.0%) | 0.0% | 1 |
| `bo_samvada` | FAIL | 1 / 0 | 11/13 (84.6%) | 100.0% | 0 |
| `bo_sangati` | FAIL | 2 / 0 | 8/30 (26.7%) | 100.0% | 4 |
| `bo_special_lagna` | PASS | 6 / 3 | ≥ 19/67 (28.4%) | 100.0% | 0 |
| `bo_sudarshana` | PASS | 6 / 3 | ≥ 19/67 (28.4%) | 100.0% | 0 |
| `bo_upaya` | FAIL | 2 / 0 | 17/22 (77.3%) | 100.0% | 2 |
| `bo_vargottama_dhana` | PASS | 6 / 3 | ≥ 19/67 (28.4%) | 100.0% | 0 |
| `bo_yantra_mechanism` | PASS | 1 / 1 | ≥ 8/24 (33.3%) | 100.0% | 0 |

### 1.5 · The accounting

```
inherits:    —
measured_by: 1.2 + 1.3 + 1.4 against 0.2
traces_to:   0.2
```

**Not computed.** The individual term is an absent instrument (§1.2), the synergistic term is an absent instrument
(§1.3), and the cross-layer term stops at the producer side of `served` (§1.4). No layer value and no elevation delta
is written, and no fraction is recorded (T3 §1.5, 249–251). Facts the eventual accounting will need, and that are
already on record: the census tally above; the six MSR-family Idem PASSes that are chart-conditional (§6.3); the
unmeasured completion of three assets (§6.5); the shared-root carriers that are empty (§2.1); and `bo_grounding` at ≈ 0
on the individual term.

---

## Part 2 · CONDITIONS UNDER WHICH THE VALUE IS REAL

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (this layer's row), §13; Data plane §9.2 (the switch and the storage separation)
measured_by: a detector per rule, named here, that can report the rule violated
traces_to:   0.2 — the value is real only if these hold
```

**The life-event switch** (*not a tier gap*; T2 §9.2, 495–517). ON: L2 may make "structural alternatives compared
against reported history" (500). OFF: "Nothing derived from life events, anywhere. Every reading emits only what the
chart, sources and methods produce on their own" (501). Storage separation: "event-conditioned overlays are kept
separate from event-free structural and temporal products. Turning the switch OFF deselects the overlays; it never
requires recomputing the event-free products" (510–512). Measured: **no L2 asset currently implements an ON-state
overlay**; `lel_origin` is false on 50,678 of 50,678 chart rows of `bodha_msr_signals` [Q3], and `bo_laksana.py` line 11
states "LEL data is L3-gated; L2 is timeless structural". So L2 today emits event-free products only, which is the OFF
behaviour; the ON-state comparison T1 §8.1 names has no L2 owner asset. That is a layer finding, not a tier clause.

**Rules and their detectors.** T3 §2.1 (268–272): "A rule with no detector is a wish"; the honest reading is
NO DETECTOR, never a pass. The census has no criterion for any L2 rule (its 20 criteria are listed in §5.2).

| # | rule (tier clause) | detector | measured, if anything |
|---|---|---|---|
| 1 | Biography-dependent support must not appear as event-free chart structure (T1 §8.1, 424) | none in the census. Code-side, `bo_pramana_mapa.py` 141–191 counts `lel_origin IS TRUE` rows (term A) and life-event key shapes in JSON (term B); its own earned status is not assessed here | `lel_origin` false on 50,678 / 50,678 chart rows [Q3]. **Census reading: NO DETECTOR** |
| 2 | No graph centrality as causation; summaries, salience, embeddings and centrality are navigation aids that cannot replace ledgers (T2 §3.1, 141; §6.3, 367) | none | not measured. **NO DETECTOR** |
| 3 | No catalog match as confirmed formation (T2 §3.1, 141; T1 §3.7, 242) | none for the rule. `Dens.served` measures whether served surfaces layer by density, a different claim | not measured. **NO DETECTOR** |
| 4 | No temporal hook as independent clock evidence (T2 §3.1, 141) | none | the L2 columns that would carry temporal hooks read NEVER populated: `active_dasha_periods_jsonb`, `activation_predicted_dates_jsonb`, `dasha_activation_proximity_score`, `predicted_outcome_class` on the 150,724-row MSR table; `predicted_activation_dasha_windows_jsonb` on `bodha_cdlm_cells` (430 rows) [C: `Complete.depth` on `bo_arudha`, `bo_sangati`, all charts]. L2 emits none in those columns. **NO DETECTOR** |
| 5 | Shared roots visible; several assets from one placement are not independent confirmations (T1 §3.4, 222–224; §11, 502; T3, 681) | none | **TIER GAP: TG-L2-021.** The four columns the schema names for it (`shared_factor_keys_jsonb`, `cross_domain_shared_factor_count`, and on `bodha_cdlm_cells` `shared_factor_keys_jsonb`, `shared_signals_high_convergence_count`) are NEVER populated [C]; on the chart both MSR columns are null on 50,678 / 50,678 rows [Q3]. A different pair is filled: `system_convergence_count` and `cross_system_consensus_count` are non-null on 50,023 of 50,678 chart rows (655 null: signals whose constituent facts could not be resolved), computed by `bo_laksana_rerank` over signals sharing a `chart_facts.fact_subject` [W: `bo_laksana.py` 3726–3752; Q3b]. **NO DETECTOR** |
| 6 | Keep occurrence support separate from delivery condition; a cancelled inhibitor and a cancelled support keep their opposite polarity (T2 §6.3, 365) | none | not measured. **NO DETECTOR** |
| 7 | No invented computation, source, detector, confidence or score (T1 §13, 566) | none at rule level; the census has no `Null` or `Narr` check (§5.2) | not measured. **NO DETECTOR** |
| 8 | Missing computation is a named gap, never a neutral default (T1 §3.3, 211; T2 §5 Missingness control, 619; §11, 574) | none (no `Null` check) | `valence` is non-null on 50,678 / 50,678 chart MSR rows: neutral 34,960, malefic 8,633, benefic 5,448, mixed 1,637 [Q3b]; by `valence_source` 44,479 rows come from `keyword_heuristic_v1`, 6,050 from `ga_vichara_v1`, 125 from `categorical_deterministic_v1`, 24 from `valence_doctrine_v1` [Q3b]. Whether any `neutral` is a default for a missing computation is **not measured**. **NO DETECTOR** |

### 2.2 · Presentation obligation

```
inherits:    Product §2 (two modes, one depth); Data plane §3.4 (the field → contract mapping)
measured_by: presentation-parity test (Data plane §12.2): both renderings from the consumed reading package, no recomputation, identical finding / confidence / uncertainty
traces_to:   0.1 — the acharya rows are unservable if these fields are not carried
```

**TIER GAP: TG-L2-010** (which §3.4 rows L2 carries) and **TG-L2-011** (whether the parity test is L2's own work).
Derivable from T2 §3.4 (188–197) and §7.1 (425): the two rows whose carrying contract L2 produces are "The competing
readings and which classical authority each rests on" (DP06 variants and ancestry, with DP02 for the witness) and
"The chain of influence with its typed relations, not a summarized verdict" (DP06). Whether L2 must also retain the rows
produced at L1 (conventions, intermediate quantities, dignity components) or at L3/L4 (the temporal row) is not stated.
The parity test is [TRANSFERS] in T2 (83–85, 614) and a layer acceptance test in T3 (628); it has not been run for L2.

Measured presence of DP06's own fields on the chart (T2 §7.2, 441: "`domains_affected_array`, `configuration_jsonb`,
`constituent_facts_array`, `constituent_signals_array`, conditioning/epistemic information and qualified signed
relationships where actually produced"), `bodha_msr_signals`, 50,678 rows [Q3]: `domains_affected_array` non-empty on
50,678; `configuration_jsonb` non-null on 50,678; `constituent_facts_array` non-empty on 50,678;
`constituent_signals_array` **non-empty on 0**; `epistemic_jsonb` non-null on 50,678; `valence` non-null on 50,678 (§2.1
row 8) [Q3b]. On `bodha_cgm_edges`, 849 rows: `valence`, `direction`, `cancelled_flag`, `relationship_basis` non-null on 849;
`underlying_msr_signal_ids_array` non-empty on 360 and `constituent_fact_ids_array` non-empty on 330 (edge types:
aspect 360, argala 119, bhava_aspect 95, arudha_house 95, lordship 60, occupancy 45, dispositor 40,
special_lagna_house 35) [Q3b].

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7 (DP01-DP17), §7.1 (common envelope)
measured_by: for each contract, the fields and grain actually present in the producer's table and actually read by the consumer — verified both ends
traces_to:   0.3
```

**TIER GAP: TG-L2-004.** The two layer-level tables are in §0.3 (T2's own wording). The columns the template asks for —
which asset produces or consumes which contract, at which grain and identity, and the declared use — have no source:
`asset_registry.provides_apis` is empty on all 23 L2 rows and the registry has no produces/consumes column [Q1]. Grain and
identity are partly recoverable from the registry natural key (§5.2, Idem row); generation appears as a `build_id`
column on the tables read (`bodha_msr_signals`, `bodha_cgm_edges`; Q3b). "Verified both ends" is met at the producer end only (field presence
in §2.2); the consumer end is TG-L2-009.

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3 (substance), Data plane §5 (domain obligations)
measured_by: per obligation: applied / inapplicable-with-reason / unavailable / unqualified / unresolved — the five states, never a blank
traces_to:   0.1
```

**TIER GAP: TG-L2-012.** T2 §5 (325–339) is the obligation table. Where it or another clause names L2:

| T2 §5 obligation (line) | L2 named? | five-state result |
|---|---|---|
| Graha contextual roles (327) | yes: "L2 mechanism" | not measured |
| Rāśi/bhāva/lord/kāraka (328) | no | not measured |
| Bala/dignity/avasthā (329) | no | not measured |
| Sambandha (330) | no owner named; T2 §6.3 (363) assigns "Relationship and graph assets" to Bodha | not measured |
| Bhāvat Bhāvam (331) | no in §5; W04 (640) gives L2 "relevant Bhāvat Bhāvam scope" | not measured. The registry `bhavat_bhavam_amplifier` class is in `bo_laksana`'s owned list and has 0 chart rows [Q3] |
| Varga and reference perspectives (332) | no | not measured |
| Yoga/doṣa/bhaṅga (333) | no | not measured |
| Nakshatra/KP (334) | no | not measured |
| Present interval (335) | no: L3 and L4 | — |
| Kāla (336) | no: L3 | — |
| Praśna/Muhūrta/calendar (337) | no | — |
| Ayurdaya and constitution (338) | yes: "L2 constitutional structure" | not measured |
| Voluntary practice (339) | no | — |

Every asset's `Complete.width` reads NOT_GENERIC ("no declared universe for this asset") [C]; no universe is declared
anywhere (R22), so the width side of coverage is unmeasurable. A tool name, an empty result or a populated field is not
"applied" (T3 §2.4, 311).

### 2.6 · Vocabulary conformance

```
inherits:    Data plane §4.1 (the controlled vocabulary — six rules with detectors)
measured_by: alias-set coverage per entity class the layer touches · independent-map census per class · interface-parameter census (enum / resolver-validated / free) · presence of a parity test for every code-side snapshot the layer relies on
traces_to:   0.2 — the value is real only if the layer speaks the plane's one language
```

**TIER GAP: TG-L2-013.** T2 §4.1 (268–271) lists the sixteen entity classes and assigns none to a layer, so "which of
the sixteen L2 emits or accepts" is not stated. Measured: rule 1 (identity, the authority's declared key) `Vocab.identity`
PASS on 22 of 23 assets, no cell for `bo_samvada` (MF-L2-003) [C]. Not measured: rules 2–6, the independent-map census
(`local_map_candidates` = −1, MF-L2-005), the interface-parameter census, and the snapshot parity tests. L2 conforms to
the L0 vocabulary; it does not own it (T3, 326).

### 2.7 · Source carriage and reproduction — did we transmit it faithfully?

```
inherits:    Product §11; Data plane §12.2 (Source carriage and reproduction), §4.3, §5
measured_by: the three checks below, each named per obligation this layer owns, each able to return false
traces_to:   0.1 — a layer that corrupts what it carries serves no P-need, however well it is engineered
```

**TIER GAP: TG-L2-014.** T3 assigns the a/b/c checks at layer scope per obligation owned, and the obligation set is
itself unfilled (TG-L2-012). `Carr.detector` reads NO_DETECTOR on 23 of 23 assets with the text "which check applies
is per-asset semantics" [C]. No per-asset assignment is written here. The doctrinal verdict is not a data-plane
obligation (T3, 342–347) and is not attempted.

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; the registry DAG
measured_by: topological sort of the reconciled depends_on from 0.3; cycle check; cross-layer gates via egate.sql scoped to the CURRENT frozen definition revision
traces_to:   0.3
```

Topological sort of the live registry graph (Q1; all 127 active assets, 0 assets missing from the active set; **no
cycle**: the level computation completed). L2 occupies registry levels 1–14 of 0–26 (27 levels); its own
internal depth is 0–8.

| L2-internal depth | registry level (0-26) | asset | declared upstream, L0/L1 | declared upstream, L2 | census blocking radius direct / transitive |
|---|---|---|---|---|---|
| 0 | 1 | `bo_sudarshana` | `ga_positions` | - | 6 / 48 |
| 0 | 2 | `bo_vargottama_dhana` | `ga_vargas`, `ga_positions` | - | 6 / 48 |
| 0 | 3 | `bo_special_lagna` | `ga_sensitive` | - | 6 / 48 |
| 0 | 4 | `bo_arudha` | `ga_structural`, `ga_positions` | - | 6 / 48 |
| 0 | 4 | `bo_nakshatra_semantic` | `ga_nakshatra`, `ga_positions`, `ga_structural` | - | 6 / 48 |
| 0 | 6 | `bo_laksana` | `bg_rules`, `ga_positions`, `ga_strength`, `ga_sensitive`, `ga_panchanga`, `ga_sade_sati`, `ga_structural`, `ga_nakshatra`, `ga_condition`, `ga_vargas`, `ga_vichara` | - | 22 / 48 |
| 1 | 7 | `bo_bimba` | - | `bo_laksana`, `bo_sudarshana`, `bo_nakshatra_semantic`, `bo_arudha`, `bo_special_lagna`, `bo_vargottama_dhana` | 8 / 45 |
| 1 | 7 | `bo_grounding` | `ga_yoga` | `bo_laksana`, `bo_sudarshana`, `bo_nakshatra_semantic`, `bo_arudha`, `bo_special_lagna`, `bo_vargottama_dhana` | 0 / 0 |
| 1 | 7 | `bo_samskara` | - | `bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana` | 3 / 22 |
| 2 | 8 | `bo_karanajala` | `ga_positions` | `bo_laksana`, `bo_bimba`, `bo_sudarshana`, `bo_nakshatra_semantic`, `bo_arudha`, `bo_special_lagna`, `bo_vargottama_dhana` | 10 / 44 |
| 3 | 9 | `bo_cgm_motifs` | - | `bo_bimba`, `bo_karanajala` | 2 / 19 |
| 3 | 9 | `bo_cgm_paths` | - | `bo_bimba`, `bo_karanajala` | 3 / 20 |
| 3 | 9 | `bo_laksana_rerank` | - | `bo_laksana`, `bo_karanajala`, `bo_sudarshana`, `bo_nakshatra_semantic`, `bo_arudha`, `bo_special_lagna`, `bo_vargottama_dhana` | 1 / 40 |
| 4 | 10 | `bo_sangati` | - | `bo_laksana`, `bo_karanajala`, `bo_sudarshana`, `bo_nakshatra_semantic`, `bo_arudha`, `bo_special_lagna`, `bo_vargottama_dhana`, `bo_laksana_rerank` | 12 / 39 |
| 4 | 10 | `bo_yantra_mechanism` | - | `bo_karanajala`, `bo_cgm_motifs`, `bo_cgm_paths` | 0 / 0 |
| 5 | 11 | `bo_cdlm_summary` | - | `bo_sangati` | 0 / 0 |
| 5 | 11 | `bo_drishti` | - | `bo_laksana`, `bo_sangati`, `bo_karanajala` | 2 / 22 |
| 5 | 11 | `bo_pratijna` | - | `bo_laksana`, `bo_sangati` | 5 / 31 |
| 5 | 11 | `bo_upaya` | `ga_structural`, `ga_dashas` | `bo_laksana`, `bo_sangati`, `bo_cgm_motifs` | 4 / 17 |
| 6 | 12 | `bo_anveshana` | - | `bo_sangati`, `bo_karanajala`, `bo_samskara`, `bo_drishti`, `bo_bimba`, `bo_laksana` | 3 / 21 |
| 7 | 13 | `bo_chart_gestalt` | - | `bo_laksana`, `bo_sangati`, `bo_bimba`, `bo_cgm_paths`, `bo_anveshana` | 0 / 0 |
| 7 | 13 | `bo_pramana_mapa` | - | `bo_upaya`, `bo_drishti`, `bo_anveshana`, `bo_laksana`, `bo_sangati`, `bo_bimba`, `bo_karanajala`, `bo_samskara` | 1 / 1 |
| 8 | 14 | `bo_samvada` | - | `bo_laksana`, `bo_karanajala`, `bo_upaya`, `bo_sangati`, `bo_pramana_mapa` | 0 / 0 |

MSR waves per arch §12.9 (quoted, to be confirmed in §6.1): W0 `bo_sudarshana` (level 1), `bo_vargottama_dhana` (2);
W1 `bo_special_lagna` (3), `bo_arudha` (4), `bo_nakshatra_semantic` (4); W2 `bo_laksana` (6), `bo_laksana_rerank` (9).
The levels agree with the waves.

**Cross-layer gate under the frozen definition revision.** **TIER GAP: TG-L2-015.** Read [Q6]: the campaign definitions
table has one frozen revision, `t3-2026-09-11-8b884eac` (five earlier revisions superseded); its manifest holds 22 L2
assets (`bo_grounding` is not in it). `egate.sql -v layer=L2` returns 14 L2 assets, every one `BLOCKED-ANCESTORS`, none
with a W2 analysis or verdict recorded (`w2_analysis` false, `w2_verdict` false); the other 8 carry an `asset_frozen`
event under that revision. Unfrozen-ancestor counts: `bo_sudarshana` 1; `bo_arudha` 13; `bo_laksana` 21; `bo_cdlm_summary`,
`bo_cgm_motifs`, `bo_cgm_paths`, `bo_drishti`, `bo_pratijna` 24; `bo_anveshana`, `bo_upaya` 25; `bo_yantra_mechanism` 26;
`bo_chart_gestalt` 27; `bo_pramana_mapa` 28; `bo_samvada` 29. This is Nirmāṇa-campaign tooling: plan v1.5 §1.1 holds that
"Frozen by Nirmāṇa is not elevated", and what the T3 clause means under Suvarṇa is not stated, so these results are
recorded as measured facts and not used as a gate.

---

## Part 3 · THE DELTA

```
inherits:    —
measured_by: 1.5's shortfall, itemised
traces_to:   0.2
```

### 3.1 · Per obligation

**TIER GAP: TG-L2-016.** The two obligations L2 is scored on (T1 §11, 502) are *Concept and relationship completeness*
and *Interpretive fidelity* (ten obligations, not eleven; T3, 392). T1 §14 (589–590) states the required evidence, but no
seeded case set, question set or scoring instrument exists, and none of the census's 20 criteria measures either. Standing:
**not measured**. Adjacent census facts, information only and not scores: `Complete.depth` PARTIAL on 15 of 23 assets (columns
never populated, §2.1); `Dens.served` FAIL on 8; `Carr.detector` NO_DETECTOR on 23.

### 3.2 · Per asset — disposition

**TIER GAP: TG-L2-017.** No disposition letter is assigned in this instance. No tier maps measured evidence to a
disposition, and dispositions belong to the A.L2 dispositions file. Facts already on record that any disposition must
cite, without a letter attached: `bo_upaya` cannot rebuild until PR #2773 lands (R244, §6.4); six MSR-family Idem PASSes are
chart-conditional (R243, §6.3); `bo_karanajala` writes `arudha` and `special_lagna` nodes into `bo_bimba`'s table (R247(a),
§1.1); `bo_laksana_rerank` is UPDATE-only (R247(b), §6.1); `bo_grounding` is DRAFT and unreached (§1.2); three assets have
unmeasured completion (§6.5); `bo_samvada` is a view over other assets' tables.

### 3.3 · Per asset — what it must add

**TIER GAP: TG-L2-017 (chain).** The contract fields (§2.3), presentation fields (§2.2) and coverage states (§2.4) each
asset must add are the unfilled inputs; the list cannot be derived from this instance.

### 3.4 · Intra-layer interplay

Declared edges are in §2.5. Table-level read matrix from a static scan of each writer file (`FROM` / `JOIN`; population:
the 23 registered ids' writer files at 2a78ec64d). `bo_laksana` and `bo_laksana_rerank` share one file, so the
`bodha_cgm_nodes` and `bodha_contradictions` reads shown under `bo_laksana` belong to the re-rank code in that file.
Field-level reads and the declared use of each input are not available (TG-L2-004):

| reading asset | L2 tables its writer file reads (`FROM` / `JOIN`, static scan) and the asset(s) that write each |
|---|---|
| `bo_anveshana` | `bodha_cgm_edges` (`bo_karanajala`), `bodha_cgm_nodes` (`bo_bimba`, `bo_karanajala`), `bodha_convergence` (`bo_sangati`), `bodha_msr_signals` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`), `bodha_signal_embeddings` (`bo_samskara`) |
| `bo_arudha` | - |
| `bo_bimba` | `bodha_msr_signals` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`) |
| `bo_cdlm_summary` | `bodha_cdlm_cells` (`bo_sangati`) |
| `bo_cgm_motifs` | `bodha_cgm_edges` (`bo_karanajala`), `bodha_cgm_nodes` (`bo_bimba`, `bo_karanajala`) |
| `bo_cgm_paths` | `bodha_cgm_edges` (`bo_karanajala`), `bodha_cgm_nodes` (`bo_bimba`, `bo_karanajala`) |
| `bo_chart_gestalt` | `bodha_cdlm_cells` (`bo_sangati`), `bodha_cgm_nodes` (`bo_bimba`, `bo_karanajala`), `bodha_cgm_paths` (`bo_cgm_paths`), `bodha_discoveries` (`bo_anveshana`), `bodha_msr_signals` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`) |
| `bo_drishti` | `bodha_cgm_edges` (`bo_karanajala`), `bodha_msr_signals` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`) |
| `bo_grounding` | `bodha_msr_signals` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`) |
| `bo_karanajala` | `bodha_msr_signals` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`) |
| `bo_laksana` | `bodha_cgm_nodes` (`bo_bimba`, `bo_karanajala`), `bodha_contradictions` (`bo_karanajala`) |
| `bo_laksana_rerank` | `bodha_cgm_nodes` (`bo_bimba`, `bo_karanajala`), `bodha_contradictions` (`bo_karanajala`), `bodha_msr_signals` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`) |
| `bo_nakshatra_semantic` | - |
| `bo_pramana_mapa` | `bodha_cdlm_cells` (`bo_sangati`), `bodha_cgm_edges` (`bo_karanajala`), `bodha_cgm_nodes` (`bo_bimba`, `bo_karanajala`), `bodha_contradictions` (`bo_karanajala`), `bodha_convergence` (`bo_sangati`), `bodha_discoveries` (`bo_anveshana`), `bodha_msr_signals` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`), `bodha_question_lenses` (`bo_drishti`), `bodha_rm_remedy_prescriptions` (`bo_upaya`), `bodha_rm_resonances` (`bo_upaya`), `bodha_signal_embeddings` (`bo_samskara`) |
| `bo_pratijna` | - |
| `bo_samskara` | `bodha_msr_signals` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`) |
| `bo_samvada` | `bodha_contradictions` (`bo_karanajala`), `bodha_convergence` (`bo_sangati`), `bodha_msr_signals` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`), `bodha_rm_resonances` (`bo_upaya`), `synthesis_quality_scorecard` (`bo_pramana_mapa`) |
| `bo_sangati` | `bodha_contradictions` (`bo_karanajala`), `bodha_msr_signals` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`) |
| `bo_special_lagna` | - |
| `bo_sudarshana` | - |
| `bo_upaya` | `bodha_cdlm_cells` (`bo_sangati`), `bodha_cgm_motifs` (`bo_cgm_motifs`), `bodha_cgm_nodes` (`bo_bimba`, `bo_karanajala`), `bodha_msr_signals` (`bo_arudha`, `bo_laksana`, `bo_nakshatra_semantic`, `bo_special_lagna`, `bo_sudarshana`, `bo_vargottama_dhana`) |
| `bo_vargottama_dhana` | - |
| `bo_yantra_mechanism` | `bodha_cgm_edges` (`bo_karanajala`), `bodha_cgm_motifs` (`bo_cgm_motifs`), `bodha_cgm_nodes` (`bo_bimba`, `bo_karanajala`) |

Declared versus actual: for every asset, each L2 table its file reads is written by at least one asset in its declared
transitive upstream set; the scan found **no undeclared intra-L2 read edge**. `bo_pramana_mapa` reads eleven L2 tables and `bo_samvada`
five (their inputs are aggregation and view sources). Boundary with adjacent layers: L1 in, 12 assets and
`bg_rules` (§0.3); L3, L4 and L5 out, per the downstream table in §0.3.

---

## Part 4 · STRATEGY

### 4.1 · Order

```
inherits:    2.5
measured_by: the DAG; the three-way baseline per asset (deployed / current code / target)
traces_to:   0.2
```

Order: the topological levels of §2.5. Within a level nothing constrains order, and the template asks that ties be broken
by learning value; that choice is left to the A.L2 briefs. **Three-way baseline.** *Deployed*: production rows and last
build per asset, in §1.1 (production structure was not compared with the migration ledger; the deployed image tag is
not measured, TG-L2-006). *Current code*: identical to `origin/main` for every L2 writer [G1]; the exception is `bo_upaya`,
where PR #2773 carries an unmerged fix (§6.4). *Target*: the asset briefs (A.L2), not yet written. Delta = target −
current code cannot be stated; risk = current code − deployed is stated only for `bo_upaya`.

Build record and upstream liveness, per asset [C: `Build.history`, `Build.dep_liveness`]:

| asset | errors / aborts on record (`Build.history`) | `Build.dep_liveness` | stale upstream |
|---|---|---|---|
| `bo_anveshana` | 24 / 11 | PARTIAL | 'bo_drishti (stale, chart 482012f1)' |
| `bo_arudha` | 1 / 3 | PASS | - |
| `bo_bimba` | 25 / 7 | PASS | - |
| `bo_cdlm_summary` | 16 / 8 | PASS | - |
| `bo_cgm_motifs` | 25 / 10 | PASS | - |
| `bo_cgm_paths` | 17 / 7 | PASS | - |
| `bo_chart_gestalt` | 23 / 11 | PARTIAL | 'bo_cgm_paths (stale, chart 482012f1)', 'bo_anveshana (stale, chart 482012f1)' |
| `bo_drishti` | 17 / 8 | PASS | - |
| `bo_grounding` | 2 / 1 | PASS | - |
| `bo_karanajala` | 26 / 7 | PASS | - |
| `bo_laksana` | 39 / 7 | PASS | - |
| `bo_laksana_rerank` | 2 / 3 | PASS | - |
| `bo_nakshatra_semantic` | 0 / 3 | PASS | - |
| `bo_pramana_mapa` | 26 / 12 | PARTIAL | 'bo_upaya (stale, chart 482012f1)', 'bo_drishti (stale, chart 482012f1)', 'bo_anveshana (stale, chart 482012f1)' |
| `bo_pratijna` | 25 / 8 | PASS | - |
| `bo_samskara` | 36 / 8 | PASS | - |
| `bo_samvada` | 23 / 11 | PARTIAL | 'bo_upaya (stale, chart 482012f1)', 'bo_pramana_mapa (stale, chart 482012f1)' |
| `bo_sangati` | 25 / 8 | PASS | - |
| `bo_special_lagna` | 0 / 3 | PASS | - |
| `bo_sudarshana` | 1 / 3 | PASS | - |
| `bo_upaya` | 27 / 11 | PARTIAL | 'bo_cgm_motifs (stale, chart 482012f1)' |
| `bo_vargottama_dhana` | 0 / 3 | PASS | - |
| `bo_yantra_mechanism` | 1 / 3 | PARTIAL | 'bo_cgm_motifs (stale, chart 482012f1)', 'bo_cgm_paths (stale, chart 482012f1)' |

### 4.2 · Work packets

```
inherits:    Data plane §13.1, §13.3 item 8
measured_by: each packet's proof — a detector that fails when the packet has not landed
traces_to:   3.x — every packet closes a named delta item
```

T2 §13.1 (640) names the tier's own L2 packet, **W04 "L2 connected-meaning slice"** ("Full participants/domains/signs/ledgers;
relevant Bhāvat Bhāvam scope; configuration and contradiction hydration"; exit: accepted W02/W03 contracts and a
source-qualified operator). Packets that close named delta items cannot be derived, because Part 3 is unfilled (TG-L2-017).
Campaign items that already touch L2 are listed for orientation only and are not derived from the tiers: E4.2 (`bo_upaya`
fix; proof: the source-order test), E1.6 (R246 DELETE-FK-child detector, after E4.2), F3.FK / F3.GUARD / F3.PROOF (the eight
foreign keys of §6.2 dropped and the refusal retired; MSR waves and the L2 full-layer rebuild wait for F3.FK and F3.GUARD),
and B.U (the live `bo_upaya` rebuild, its own wave) [Track E brief §4, §4a; plan §1.2, §4.2].

### 4.3 · Generation, invalidation, rollback

```
inherits:    Data plane §11, §4.4, DP16
measured_by: the generation pins each consumer records; the invalidation path exercised, not described
traces_to:   2.1 — a rebuild that resets chronology is a hindsight leak
```

Measured: `bodha_msr_signals` carries `build_id` and `producer_asset_id`; the live delete guard requires an admitted
generation context (`madhav.l2_generation_id`, `madhav.l2_asset_id`, and an intent row whose generation state is
`building`) [Q5]. **Not measured:** the generation table `data_plane_l2_producer_generations` (permission denied for the
reader, MF-L2-002), the pins any consumer records, and whether any invalidation path has been exercised. Whether a rebuild
resets chronology is therefore unmeasured. The cross-layer consequence of a replacement is §6.2.

### 4.4 · What each asset brief inherits

```
inherits:    Product §16 (what every brief states); Data plane §13.3 (asset brief sentence)
measured_by: derivability — a brief author must be able to fill these from this instance alone
traces_to:   0.1
```

The thirteen rows of T4 §0.1, and what this instance can supply to a brief today. **A brief that has to invent any of the
unsupplied rows has found a defect here, not in the brief** (T3, 480).

| # | row | supplied by this instance | state |
|---|---|---|---|
| 1 | P-needs and V-journeys served | §0.1 | **not supplied** (TG-L2-001) |
| 2 | obligations scored on | §0.2 | supplied at layer level |
| 3 | correctness rules and switch behaviour | §2.1 | supplied (rules and switch); detectors NO DETECTOR |
| 4 | presentation fields | §2.2 | partial (TG-L2-010, -011) |
| 5 | contracts produced and consumed, with declared use | §0.3, §2.3 | layer level supplied; per asset not (TG-L2-004) |
| 6 | coverage obligations and states | §2.4 | **not supplied** (TG-L2-012) |
| 7 | position in the order and three-way baseline | §2.5, §4.1 | partial: order measured, baseline partly (TG-L2-006, -015) |
| 8 | disposition and must-add list | §3.2, §3.3 | **not supplied** (TG-L2-017) |
| 9 | individual term | §1.2 | **absent instrument** (TG-L2-008) |
| 10 | synergistic term, which seam | §1.3 | **absent instrument** (TG-L2-008) |
| 11 | cross-layer term, contract at evidence state | §1.4 | partial (TG-L2-009) |
| 12 | preserved kernel | §5.2 Idem row | **not supplied**; natural key for 20 of 23 (TG-L2-018) |
| 13 | Jyotish concepts with the carriage check each invites | §2.7 | **not supplied** (TG-L2-014) |

Also required by T3 §4.4 (476): the asset's manifestation or temporal role — layer default derivable, per asset not
(TG-L2-019): T2 §3.1 places activation in L3 and manifestation in L4, so L2's default is "neither (supplies what both rest on)".
Of thirteen rows, 2 are supplied, 4 partially, and 7 are not supplied or are absent instruments.

---

## Part 5 · EVALUATION AND CERTIFICATION

### 5.1 · The score is ablation, in three flavours

```
inherits:    Product §14, §14.1; Data plane §12.2
measured_by: ablation deltas
traces_to:   0.2
```

L2 scores on two of the product's ten obligations (§0.2). Individual flavour: absent instrument. Synergistic flavour:
absent instrument. Cross-layer flavour: producer side only (§1.4). L2 is a chart-product layer, so no reference-layer
substitution applies (T3, 500–501). Nothing is scored in this draft.

### 5.2 · What is certified, and what is merely checked

```
inherits:    Product §14; CLAUDE.md §N.6-N.8; the t3 lesson (certification is expensive to re-earn)
measured_by: the certification ledger for gates; the tracker's marker scan for shape
traces_to:   4.4 — the gates are what an asset brief is certified against
```

Nothing is certified and no ledger or certification record is written (§5.3).

**(a) The nine gates against the census.** Population: 23 L2 assets, the 20 census criteria mapped to the gate each
belongs to (Cost, Count, Complete and Reach are non-gate and shown below as information, D3):

| gate | census criteria read (23 assets each) | PASS | FAIL | PARTIAL | NO_DETECTOR | ERRORED | N/A | cells absent |
|---|---|---|---|---|---|---|---|---|
| Ldgr | `Ldgr.source_presence` | 16 | 0 | 0 | 0 | 0 | 0 | 7 |
| Idem | `Idem.pattern` | 21 | 0 | 2 | 0 | 0 | 0 | 0 |
| Earn | `Earn.build_record` | 0 | 0 | 0 | 23 | 0 | 0 | 0 |
| Null | (no census check exists) | - | - | - | - | - | - | - |
| Vocab | `Vocab.identity` | 22 | 0 | 0 | 0 | 0 | 0 | 1 |
| Carr | `Carr.detector` | 0 | 0 | 0 | 23 | 0 | 0 | 0 |
| Narr | (no census check exists) | - | - | - | - | - | - | - |
| Dens | `Dens.served` | 14 | 8 | 0 | 0 | 0 | 1 | 0 |
| Build | `Build.registered`, `Build.contract`, `Build.target`, `Build.dag`, `Build.count_integrity`, `Build.completion`, `Build.exercised`, `Build.history`, `Build.dep_liveness` | 171 | 3 | 29 | 1 | 3 | 0 | 0 |

Per-asset rows for the six single-criterion checks (Idem, Ldgr, Vocab, Dens, Carr, Earn). **†** = one of the six R243 chart-conditional
PASSes (annotation in §6.3: `chart_scope: 482012f1 only; refused via assert_l2_msr_delete_safe on <charts>`); **‡** =
the R244 withheld PASS (§6.4):

| asset | Idem (`Idem.pattern`) | Ldgr (`Ldgr.source_presence`) | Vocab (`Vocab.identity`) | Dens (`Dens.served`) | Carr (`Carr.detector`) | Earn (`Earn.build_record`) |
|---|---|---|---|---|---|---|
| `bo_anveshana` | PASS | no row | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_arudha` | PASS † | PASS | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_bimba` | PASS | PASS | PASS | FAIL | NO_DETECTOR | NO_DETECTOR |
| `bo_cdlm_summary` | PASS | PASS | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_cgm_motifs` | PASS | PASS | PASS | FAIL | NO_DETECTOR | NO_DETECTOR |
| `bo_cgm_paths` | PASS | PASS | PASS | FAIL | NO_DETECTOR | NO_DETECTOR |
| `bo_chart_gestalt` | PASS | no row | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_drishti` | PASS | PASS | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_grounding` | PASS | no row | PASS | N/A | NO_DETECTOR | NO_DETECTOR |
| `bo_karanajala` | PASS | PASS | PASS | FAIL | NO_DETECTOR | NO_DETECTOR |
| `bo_laksana` | PASS † | PASS | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_laksana_rerank` | PARTIAL | PASS | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_nakshatra_semantic` | PASS † | PASS | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_pramana_mapa` | PASS | no row | PASS | FAIL | NO_DETECTOR | NO_DETECTOR |
| `bo_pratijna` | PASS | no row | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_samskara` | PASS | no row | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_samvada` | PARTIAL | no row | no row | FAIL | NO_DETECTOR | NO_DETECTOR |
| `bo_sangati` | PASS | PASS | PASS | FAIL | NO_DETECTOR | NO_DETECTOR |
| `bo_special_lagna` | PASS † | PASS | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_sudarshana` | PASS † | PASS | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_upaya` | PASS ‡ | PASS | PASS | FAIL | NO_DETECTOR | NO_DETECTOR |
| `bo_vargottama_dhana` | PASS † | PASS | PASS | PASS | NO_DETECTOR | NO_DETECTOR |
| `bo_yantra_mechanism` | PASS | PASS | PASS | PASS | NO_DETECTOR | NO_DETECTOR |

Cells at FAIL or ERRORED (all criteria) [C]:

| asset | cells at FAIL or ERRORED |
|---|---|
| `bo_anveshana` | `Build.completion` ERRORED; `Count.floor` ERRORED |
| `bo_bimba` | `Build.completion` FAIL; `Dens.served` FAIL |
| `bo_cdlm_summary` | `Build.completion` FAIL |
| `bo_cgm_motifs` | `Dens.served` FAIL |
| `bo_cgm_paths` | `Dens.served` FAIL |
| `bo_karanajala` | `Build.completion` FAIL; `Dens.served` FAIL |
| `bo_laksana` | `Count.floor` FAIL |
| `bo_pramana_mapa` | `Dens.served` FAIL |
| `bo_samskara` | `Count.floor` FAIL |
| `bo_samvada` | `Dens.served` FAIL |
| `bo_sangati` | `Build.completion` ERRORED; `Count.floor` ERRORED; `Dens.served` FAIL |
| `bo_upaya` | `Build.completion` ERRORED; `Count.floor` ERRORED; `Dens.served` FAIL |

Non-gate criteria (information; never blockers, D3):

| non-gate criterion (information, D3) | verdicts over 23 assets |
|---|---|
| `Cost.baseline` | 23 NO_DETECTOR |
| `Count.floor` | 3 ERRORED, 2 FAIL, 4 N/A, 14 PASS |
| `Complete.depth` | 15 PARTIAL, 8 PASS |
| `Complete.width` | 23 NOT_GENERIC |
| `Reach.fields` | 23 NOT_GENERIC |

**The carriage menu (D1 / D2 / D3).** Not assigned (TG-L2-014).

**The gate map** (fixed by the template, 572–582); this instance's right-hand column:

| gate | section a brief author reads | what this instance supplies | unfillable, and why |
|---|---|---|---|
| **Ldgr** | §2.3 | signals carry `constituent_facts_array` non-empty on 50,678 / 50,678 chart MSR rows; `citation_ref` is populated on 150,724 / 150,724 table-wide rows [C: `Ldgr.source_presence`]. The census emits no cell for 7 assets | the per-asset named `fact_id` sources (TG-L2-020) |
| **Idem** | §2.5, §4.1 | the registry natural key for 20 of 23 assets (table below); census `Idem.pattern` PASS 21, PARTIAL 2 (`bo_laksana_rerank`: "only UPDATEd in place"; `bo_samvada`: no write to its view target) | natural key blank for `bo_anveshana`, `bo_karanajala`, `bo_samvada` (MF-L2-009); the collateral-deletion clause (TG-L2-022); six PASSes are chart-conditional (§6.3); `bo_upaya` PASS is withheld (§6.4) |
| **Earn** | §2.4 | `Earn.build_record` NO_DETECTOR on 23 / 23 ("instrument absent (migration 1094)") [C] | which emitted states are claims and what would falsify each (TG-L2-020) |
| **Null** | §2.4, §1.4 | no census check. One documented convention exists in one writer: three rollup columns take a measured count, a measured zero, or NULL "nothing was checked, so nothing is claimed" (`bo_laksana.py` 3781–3801, ruling #1720); `system_convergence_count` is null on 655 of 50,678 chart rows [Q3b] | the asset's own null convention, per asset (TG-L2-020) |
| **Vocab** | §2.6 | rule-1 identity PASS on 22 / 23 [C] | the classes each asset owns or consumes (TG-L2-013) |
| **Carr** | §2.7 | NO_DETECTOR on 23 / 23 [C] | which of D1/D2/D3 each asset invites (TG-L2-014) |
| **Narr** | §2.2 | no census check. Columns whose names carry prose exist (e.g. `signal_summary_text`, `signal_headline_text` on `bodha_msr_signals`; `hypothesis_text`, `depth_reading`, `why_an_acharya_misses_it` on `bodha_discoveries` [C: `Reach.fields`]); whether the prose restates cited facts is not measured | which assets emit prose and in which fields (TG-L2-020) |
| **Dens** | §2.2, §3.4 | the serving modules and density declarations per asset (§1.4 table): 14 PASS, 8 FAIL, 1 N/A | — |
| **Build** | §2.5, §1.1, §4.3 | writer and registered id (`Build.registered` PASS 23 / 23), declared target (PASS 23 / 23), edges (§2.5), build record (§4.1); `Build.completion` 16 PASS, 3 FAIL, 3 ERRORED, 1 NO_DETECTOR [C] | completion of three assets is unmeasured (§6.5); deployed versus code (TG-L2-006) |

Registry natural keys (`natural_key_partition`, the Idem natural key; Q1):

| asset | registry `natural_key_partition` (Q1, truncated to 170 characters) |
|---|---|
| `bo_anveshana` | (blank) |
| `bo_arudha` | bodha_msr_signals.signal_type_class = arudha |
| `bo_bimba` | bodha_cgm_nodes.node_type IN (bhava, domain, dosha, graha, yoga) |
| `bo_cdlm_summary` | bodha_cdlm_chart_summary (chart_id, ayanamsha_id) -- BoCdlmSummaryWriter (@register('bo_cdlm_summary')) is the confirmed sole live BUILD-TIME writer of bodha_cdlm_chart_s... |
| `bo_cgm_motifs` | bodha_cgm_motifs (chart_id, ayanamsha_id, snapshot_type, fingerprint_hash) + bodha_cgm_sub_graphs (chart_id, ayanamsha_id, subgraph_centroid_node_id) + bodha_cgm_chart_to... |
| `bo_cgm_paths` | bodha_cgm_paths (chart_id, ayanamsha_id, snapshot_type, path_type, from_node_id, to_node_id) -- BoCgmPathsWriter (@register('bo_cgm_paths')) is the confirmed sole live BU... |
| `bo_chart_gestalt` | bodha_chart_gestalt (chart_id, ayanamsha_id) -- BoChartGestaltWriter (@register('bo_chart_gestalt')) is the confirmed sole live BUILD-TIME writer (grepped tree-wide for I... |
| `bo_drishti` | bodha_question_lenses (chart_id, ayanamsha_id, question_type) -- sole writer, chart-wide delete-then-insert, one row per (question_type x ayanamsha) |
| `bo_grounding` | bodha_grounding_matches (chart_id, ayanamsha_id, target_kind, target_id) -- sole writer; live table unique constraint is (chart_id, ayanamsha_id, target_kind, target_id, ... |
| `bo_karanajala` | (blank) |
| `bo_laksana` | bodha_msr_signals.signal_type_class IN (yoga, dosha, sade_sati, panchanga, karaka_alignment, tradition_specific, parivartana, configuration, varga_pattern, annual, medica... |
| `bo_laksana_rerank` | bodha_msr_signals.graph_node_strength_contribution_jsonb / system_convergence_count / cross_system_consensus_count / contradicts_signals_array (UPDATE-only enrichment, ch... |
| `bo_nakshatra_semantic` | bodha_msr_signals.signal_type_class = nakshatra_semantic |
| `bo_pramana_mapa` | synthesis_quality_scorecard (chart_id) -- sole writer; single-row-per-chart asset, replace_prior_scorecard (bodha_writers/_idempotency.py:484) deletes ALL prior rows for ... |
| `bo_pratijna` | bodha_pratijna (chart_id, ayanamsha_id, event_class_id) -- sole writer, ON CONFLICT (chart_id, ayanamsha_id, event_class_id) DO UPDATE declared directly in the writer's o... |
| `bo_samskara` | bodha_signal_embeddings (signal_id) -- BoSamskaraWriter is the confirmed sole live BUILD-TIME writer (grepped tree-wide for INSERT/DELETE/UPDATE INTO bodha_signal_embeddi... |
| `bo_samvada` | (blank) |
| `bo_sangati` | bodha_cdlm_cells (chart_id, ayanamsha_id, snapshot_type, domain_row, domain_col) + bodha_convergence (chart_id, ayanamsha_id, snapshot_type, domain) + bodha_triangulation... |
| `bo_special_lagna` | bodha_msr_signals.signal_type_class = special_lagna |
| `bo_sudarshana` | bodha_msr_signals.signal_type_class = sudarshana_agreement |
| `bo_upaya` | bo_upaya writes six tables, BoUpayaWriter (@register('bo_upaya')) confirmed sole live writer of all six (tree-wide grep for each table name across platform/ found only re... |
| `bo_vargottama_dhana` | bodha_msr_signals.signal_type_class IN (vargottama_amplification, dhana_axis) |
| `bo_yantra_mechanism` | bodha_mechanisms (chart_id, ayanamsha_id, mechanism_class, fingerprint_hash) -- BoYantraMechanismWriter (@register('bo_yantra_mechanism')) is the confirmed sole live writ... |

**(b) Brief shape.** Not applicable to this instance. **(c) Inheritance and ladder position.** This instance
descends from T1 and T2 by the `inherits:` lines; ladder positions are status fields and not verdicts.

### 5.3 · Certification is per criterion, not per definition revision

No certification record is written by this draft. A record would carry `asset · criterion · criterion_version · detector ·
evidence · verdict · verified_by · verified_on` with the closed verdict set (T3, 607–611). The six R243 PASSes and the
R244 PASS may not be emitted without their annotation or withholding (§6.3, §6.4).

### 5.4 · Acceptance of the instance itself

| test | state |
|---|---|
| 1. Derivability: a fresh reader derives one brief and reports every invention | not run; the instance leaves 7 of 13 inherited rows unsupplied (§4.4), so it would fail as drafted |
| 2. Alignment: every section names `traces_to:` | author's run in §0.4; reviewer's run pending |
| 3. Measured, not inherited: every figure names its `measured_by:` | every figure is tagged; reviewer's re-run pending |
| 4. Presentation parity holds for the served surface | not run (TG-L2-011) |
| 5. The gate map exists | written in §5.2; unfillable cells reported there |
| 6. Independent review, findings folded | not done. No verdict is claimed. Acceptance is A.L2a, after J1 and A.L2r |

---

## Part 6 · Track A layer specifics (Track A brief §4)

### 6.1 · (a) The measured list of L2 MSR assets

```
inherits:    arch §12.9 (which assets are "L2 MSR"); F-3 (N-32)
measured_by: writer files at 2a78ec64d (INSERT / DELETE / UPDATE on bodha_msr_signals, case-insensitive, over platform/python-sidecar, platform/src, platform/scripts excluding tests and migrations); Q1 (registry target); Q3 (producer_asset_id on chart 482012f1); census Idem.pattern
traces_to:   0.3
```

Arch §12.9 defines the set as "the L2 writers whose rebuild replaces rows in `bodha_msr_signals`" and says "A.L2i confirms
from the writers". Registry target: **seven** assets. Writers that **replace** rows: **six**.

| # | asset | registry `target_table` | `@register` | replaces rows? (evidence) | owned classes | INSERT | rows it owns on chart 482012f1 (`producer_asset_id`; Q3) | census `Idem.pattern` | wave (§12.9) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `bo_sudarshana` | `bodha_msr_signals` | `bo_sudarshana.py:167` | yes: `replace_prior_msr_for_chart` at :248 | `sudarshana_agreement` | :265 | 45 | PASS † | W0 |
| 2 | `bo_vargottama_dhana` | same | `bo_vargottama_dhana.py:115` | yes: :159 | `vargottama_amplification`, `dhana_axis` (:44–46) | :173 | 14 | PASS † | W0 |
| 3 | `bo_special_lagna` | same | `bo_special_lagna.py:105` | yes: :148 | `special_lagna` (:41) | :162 | 20 | PASS † | W1 |
| 4 | `bo_arudha` | same | `bo_arudha.py:135` | yes: :175 | `arudha` (:41) | :189 | 25 | PASS † | W1 |
| 5 | `bo_nakshatra_semantic` | same | `bo_nakshatra_semantic.py:110` | yes: :161 | `nakshatra_semantic` (:46) | :175 | 45 | PASS † | W1 |
| 6 | `bo_laksana` | same | `bo_laksana.py:3355` | yes: :3595 | 15 classes (:145–161), 12 present on the chart | :3067 | 50,529 | PASS † | W2 |
| 7 | `bo_laksana_rerank` | same | `bo_laksana.py:3821` | **no**: UPDATE-only (docstring :3824–3825; UPDATEs at :3748, :3757, :3774, :3886, :3948); no DELETE or INSERT | none (chart-wide UPDATE of several columns, "no signal_type_class scope", registry `natural_key_partition`) | none | **0** | PARTIAL ("only UPDATEd in place") | W2 |

Rows owned sum to 45 + 14 + 20 + 25 + 45 + 50,529 = 50,678 = all `bodha_msr_signals` chart rows; the seven registry `count_sql`
values are scoped per producer (`bo_laksana_rerank` counts rows with `graph_node_strength_contribution_jsonb IS NOT NULL`,
11,094) [Q1, Q3]. `producer_asset_id` names exactly six producers. No other file in the searched population inserts, updates
or deletes the table.

**Conflicts reported, not resolved (MF-L2-010).** (i) Arch §12.9 lists `bo_laksana_rerank` among writers "whose rebuild
replaces rows"; measured, it replaces none and owns none, though it is a registry target and in the W2 wave. It still
matters to F-3 because it updates columns on rows of every producer (per the registry `natural_key_partition`:
`graph_node_strength_contribution_jsonb`, `system_convergence_count`, `cross_system_consensus_count`,
`contradicts_signals_array`; the code also updates `valence` and `valence_source`), so it must run after any MSR replacement.
(ii) `bo_sudarshana.py:244` cites "the 8 bodha_msr_signals writers"; the scan finds six inserting writers.

**Rows that die with an MSR replacement** (measured relationships): `bodha_signal_embeddings` is 1:1 with the chart's MSR
rows (50,678 = 50,678; written by `bo_samskara`); `bodha_contradictions` (written by `bo_karanajala`, unreadable to the
reader) is deleted by the same helper. After any MSR replacement both must be rebuilt, in DAG order (`bo_samskara` level 7,
`bo_karanajala` level 8, `bo_laksana_rerank` level 9).

### 6.2 · (b) Cascade victims: the eight `ON DELETE CASCADE` keys into `bodha_msr_signals`

```
inherits:    plan §3.8, §5.3 (F-3); Track E §4a (F3.FK-migrate-001, F3.GUARD, F3.PROOF)
measured_by: Q2 (pg_constraint, contype 'f', confrelid public.bodha_msr_signals, as suvarna_reader) and Q3 (chart-scoped referencing-row counts)
traces_to:   0.3
```

Input to the F-3 migration lane. Eight constraints from **seven** tables, all `ON DELETE CASCADE`, all validated,
`ON UPDATE NO ACTION`, referenced column `signal_id`; no partitioned or inherited children (`pg_inherits` 0; no
`conparentid`). **Four of the eight referencing columns are NOT NULL** (`bodha_contradictions.signal_a_id`, `.signal_b_id`,
`bodha_signal_embeddings.signal_id`, `kala_activation.signal_id`); Track E §4a records that as the reason `ON DELETE SET NULL` was rejected as the alternative.

| # | constraint | referencing table (layer) | column | NOT NULL | delete action | writer of the referencing table | referencing rows, chart 482012f1 |
|---|---|---|---|---|---|---|---|
| 1 | `bodha_contradictions_signal_a_id_fkey` | `bodha_contradictions` (L2) | `signal_a_id` | yes | CASCADE | `bo_karanajala` (`bo_karanajala.py:93`, :1910) | **not measured** (permission denied) |
| 2 | `bodha_contradictions_signal_b_id_fkey` | `bodha_contradictions` (L2) | `signal_b_id` | yes | CASCADE | `bo_karanajala` | **not measured** (permission denied) |
| 3 | `bodha_signal_embeddings_signal_id_fkey` | `bodha_signal_embeddings` (L2) | `signal_id` | yes | CASCADE | `bo_samskara` | 50,678 |
| 4 | `kala_activation_signal_id_fkey` | `kala_activation` (L3) | `signal_id` | yes | CASCADE | `ka_kalasutra` | 0 |
| 5 | `kala_bhavishya_signal_id_fkey` | `kala_bhavishya` (L3) | `signal_id` | no | CASCADE | `ka_bhavishya_lekha` | 0 |
| 6 | `kala_convergence_signal_id_fkey` | `kala_convergence` (L3) | `signal_id` | no | CASCADE | `ka_sangam` (a **family** asset: charter R8, notify its owner) | 0 |
| 7 | `kala_darshana_signal_id_fkey` | `kala_darshana` (L3) | `signal_id` | no | CASCADE | `ka_kala_darshana` | 0 |
| 8 | `kala_obstruction_signal_id_fkey` | `kala_obstruction` (L3) | `signal_id` | no | CASCADE | `ka_vighnakara` | 0 |

Table owners from the registry `target_table` (Q1) except `bodha_contradictions`, which no registry row declares (owner from
the writer file). Referencing rows are joins to the chart's MSR signals [Q3]; the five `kala_*` tables hold none for the
canonical chart today, which is the condition under which the six MSR-family PASSes are earned (§6.3).

**Onward closure** (recursive over `pg_constraint`, Q2), for the migration lane's proof: `kala_convergence` cascades into
`kala_obstruction`, `kala_darshana` and `phala_anchors`, and sets NULL in `kala_bhavishya`; `kala_bhavishya` sets NULL in
`phala_anchors`; `phala_anchors` cascades into `phala_sodhana`, `phala_suddha_sodhana`, `phala_sankrama` and `phala_pramana`
and sets NULL in `phala_muhurta` and `phala_mitigation`; `phala_muhurta` sets NULL in `phala_mitigation`; `phala_mitigation`
sets NULL in `phala_sankrama`. This agrees with plan §3.8.

**The live guard** [Q5]: `public.assert_l2_msr_delete_safe` (SECURITY DEFINER) requires `session_user = data_plane_builder`,
an admitted L2 asset and generation context, locks the exact replacement scope by `producer_asset_id`, skips the two L2
tables (embeddings, contradictions), and for the five `kala_*` keys raises "L2 MSR replacement blocked by cross-layer
dependent rows" when a referencing row exists. Its refusal branch is what the F-3 migration retires. Not re-measured here:
the code comment's blast radius ("864,733 rows across 12 tables", `_idempotency.py`), and any other chart (chart 482012f1
only). Other charts' dependents per `W2-3_REVIEW.md` rows 36–41 (2026-09-28): 1c826d5a — 552 `kala_convergence` under
`bo_arudha`; 16,853 `kala_convergence` and 750 `kala_darshana` under `bo_laksana`; 552 under `bo_sudarshana`; cb73cd3d — 1,270
under `bo_nakshatra_semantic`; 635 under `bo_sudarshana`; 635 under `bo_vargottama_dhana`; none for `bo_special_lagna`.

### 6.3 · (c) R243: the six chart-conditional PASSes carry their annotation

```
inherits:    register R243 (annotation-only; "any emit or certification of these six must carry the annotation")
measured_by: census Idem.pattern (2026-09-30); Q3 (dependents on the canonical chart); Q5; register R243 and W2-3_REVIEW.md rows 36–41 for other charts (not re-measured)
traces_to:   2.1 — Idem is earned only where the delete is allowed to happen
```

The annotation, verbatim from R243: **`chart_scope: 482012f1 only; refused via assert_l2_msr_delete_safe on <charts>`**.
Each of the six PASSes below carries it. Census `Idem.pattern` PASS text for these assets contains no annotation (it reads
"DELETE FROM the asset's own table(s) (delete-then-insert): bodha_msr_signals … via replace_prior_msr_for_chart", MF-L2-006), so
the annotation must be added at any emit or certification.

| asset | census `Idem.pattern` (2026-09-30) | annotation carried (R243's `<charts>`, the register of record) | dependents on chart 482012f1 today [Q3] | `<charts>` per W2-3_REVIEW (2026-09-28), for comparison |
|---|---|---|---|---|
| `bo_arudha` | PASS † | `chart_scope: 482012f1 only; refused via assert_l2_msr_delete_safe on 1c826d5a, cb73cd3d` | 0 in all five `kala_*` tables | 1c826d5a |
| `bo_special_lagna` | PASS † | `chart_scope: 482012f1 only; refused via assert_l2_msr_delete_safe on 1c826d5a, cb73cd3d` | 0 | none ("no dependents on any chart today") |
| `bo_nakshatra_semantic` | PASS † | `chart_scope: 482012f1 only; refused via assert_l2_msr_delete_safe on 1c826d5a, cb73cd3d` | 0 | cb73cd3d |
| `bo_sudarshana` | PASS † | `chart_scope: 482012f1 only; refused via assert_l2_msr_delete_safe on 1c826d5a, cb73cd3d` | 0 | 1c826d5a, cb73cd3d |
| `bo_vargottama_dhana` | PASS † | `chart_scope: 482012f1 only; refused via assert_l2_msr_delete_safe on 1c826d5a, cb73cd3d` | 0 | cb73cd3d |
| `bo_laksana` | PASS † | `chart_scope: 482012f1 only; refused via assert_l2_msr_delete_safe on 1c826d5a` | 0 | 1c826d5a |

R243's chart list and W2-3_REVIEW's per-asset list disagree for `bo_arudha`, `bo_special_lagna`, `bo_nakshatra_semantic` and
`bo_vargottama_dhana` (MF-L2-011). Both readings are shown and neither is chosen; other charts were not re-measured. The
annotation is carried with `<charts>` exactly as R243 states it, and the owner of R243 resolves the per-asset chart list.
`bo_laksana_rerank` is not one of the six (its `Idem.pattern` reads PARTIAL). Once F-3 drops the eight keys and retires the
refusal, this annotation ceases to apply to new emits.

### 6.4 · (d) `bo_upaya` — Track E lane E4.2 (recorded, not redesigned)

```
inherits:    register R244 (BLOCKS_FREEZE) and its 2026-09-28 ruling; Track E brief §4 (E4.2-build-001)
measured_by: census (bo_upaya rows); writer at 2a78ec64d lines 1936–1946; G2 (gh pr view 2773, read 2026-09-30)
traces_to:   0.3
```

**Defect (R244):** commit `fa9857f00` (#2607) removed the delete of the legacy `bodha_rm_dasha_windowed_prescriptions` rows, which
carry a validated, non-deferrable NO ACTION foreign key onto the prescriptions table the writer still deletes, so every
rebuild would raise a foreign-key violation. **Ruling (2026-09-28):** restore the delete, in front of
`replace_prior_rm_prescriptions()`. **In the inspected code** the legacy delete is absent: the writer calls
`replace_prior_rm_prescriptions` then `replace_prior_rm_resonances` (`bo_upaya.py` 1945–1946) under the comment
"DP-SD-015: do not delete or append the legacy daśā-window table" (1942–1944).

**Fix PR (E4.2):** #2773, "fix(bo_upaya): restore the legacy windowed-prescriptions delete so the writer can rebuild (R244)", branch
`suvarna/land/E4.2-build-001`, head `5ca4af860`, base `main`; files `bo_upaya.py`, `tests/l2/test_bo_upaya_source_order.py`,
`tests/l2/test_l2_writer_adoption.py`. State when read (2026-09-30): OPEN, not a draft, merge state **BLOCKED**, no review decision;
checks: Governance Gates **FAILURE**; Build Check (PR only) and Unit Tests IN_PROGRESS; DB Integration Tests, TypeScript, Secret
Scan, Earned-Signal Gate, Coverage Gate and the others SUCCESS or SKIPPED [G2]. The live rebuild of `bo_upaya` waits for its own wave
(B.U); the R246 detector follows E4.2 (E1.6).

**Census on the asset:** `Idem.pattern` PASS (the detector reads PASS while R244 says unearned; withheld from emits by procedure,
‡ above, MF-L2-006); `Build.completion` and `Count.floor` ERRORED, unmeasured (§6.5); `Dens.served` FAIL (2 modules, 0 declaring a
density contract); `Build.dep_liveness` PARTIAL (`bo_cgm_motifs` stale); 47 executed runs, last executed 2026-09-09; `Complete.depth`
PARTIAL (135 rows table-wide, 24 columns, 18 fully populated) [C]. The register's "5 referencing rows on the canonical chart" was
**not re-measured**: the referencing table is unreadable to the reader.

### 6.5 · (e) The six ERRORED census cells — unmeasured, not PASS

```
inherits:    census exit code 2; arch §12.14; SUMMARY.md anomalies
measured_by: census assets[*].measurements[Build.completion / Count.floor]; Q4 (has_table_privilege)
traces_to:   1.1
```

Six cells, three assets, two checks each, all `permission denied` for the read-only login (a grant gap, not an inspector fault):

| asset | check | census text | table | floor |
|---|---|---|---|---|
| `bo_anveshana` | `Build.completion` | check errored: `ERROR:  permission denied for table bodha_anomalies` | `bodha_anomalies` | — |
| `bo_anveshana` | `Count.floor` | same, "floor=500 not measured" | `bodha_anomalies` | 500 |
| `bo_sangati` | `Build.completion` | check errored: `ERROR:  permission denied for table bodha_triangulation` | `bodha_triangulation` | — |
| `bo_sangati` | `Count.floor` | same, "floor=70 not measured" | `bodha_triangulation` | 70 |
| `bo_upaya` | `Build.completion` | check errored: `ERROR:  permission denied for table bodha_rm_remedy_prescriptions` | `bodha_rm_remedy_prescriptions` | — |
| `bo_upaya` | `Count.floor` | same, "floor=180 not measured" | `bodha_rm_remedy_prescriptions` | 180 |

Whether those assets built completely, and whether they meet their floors, is **unknown**. A `SELECT` grant on the three tables
would clear the six cells. The same probe (Q4) shows ten more `bodha_*` tables and the generation table unreadable, so the
completion of the other writes of these three assets and of three further ones (`bo_cdlm_summary`, `bo_cgm_motifs`, `bo_karanajala`)
is also untested (MF-L2-002); `bodha_contradictions` is
among them and is a cascade victim (§6.2).

### 6.6 · Figures that disagree with an earlier document

Reported, not resolved (full list MF-L2-010 to -012): arch §12.9's seven-writer definition against six replacers (§6.1);
R243's chart list against W2-3_REVIEW (§6.3); the skeleton's 2026-09-26 aggregates against today's census (Idem PASS 10 →
21; Earn/Cost FAIL 23 → NO_DETECTOR 23; per-producer MSR rows each 150,724 → scoped 50,529 / 11,094 / 45 / 45 / 25 / 20 / 14);
R101 and R107 (recorded as inventions) against T2 §6.3 and §9.2, which do supply the clauses.

---

## Appendix A · Reads used (all read-only; chart 482012f1 unless stated)

```sql
-- Q1 registry (chart-independent catalog)
select asset_id, layer, depends_on, target_table, target_floor, storage_type, catalog_status, has_substeps,
       natural_key_partition, count_sql, provides_apis from asset_registry where is_active;
-- Q2 the eight keys and their closure
select c.conname, c.conrelid::regclass, a.attname, a.attnotnull, c.confdeltype, c.confupdtype, c.convalidated
  from pg_constraint c join pg_attribute a on a.attrelid=c.conrelid and a.attnum=any(c.conkey)
 where c.contype='f' and c.confrelid='public.bodha_msr_signals'::regclass;   -- plus a recursive closure on confrelid
-- Q3 (examples; each with chart_id = '482012f1-710e-4a25-994a-93821f5871aa')
select producer_asset_id, count(*) from bodha_msr_signals where chart_id=$1 group by 1;
select signal_type_class, count(*) from bodha_msr_signals where chart_id=$1 group by 1;
select count(*), count(system_convergence_count), count(shared_factor_keys_jsonb), count(cross_domain_shared_factor_count),
       count(nullif(cardinality(constituent_facts_array),0)), count(nullif(cardinality(constituent_signals_array),0))
  from bodha_msr_signals where chart_id=$1;
select count(*) from kala_activation e join bodha_msr_signals m using(signal_id) where m.chart_id=$1;  -- and the other four kala_* tables
-- Q4 grants
select c.relname from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relkind in ('r','v','p','m') and c.relname like 'bodha\_%'
   and not has_table_privilege(current_user, c.oid, 'SELECT');
-- Q5
select pg_get_functiondef(p.oid) from pg_proc p where proname='assert_l2_msr_delete_safe';
-- Q6
select definition_revision, definition_status from nirmana_evidence.nirmana_elevation_campaign_definitions;
-- and: psql -v layer=L2 -f platform/scripts/nirmana/egate.sql   (read-only by its own header)
-- Q3b (further chart-scoped field-presence counts)
select valence_source, valence, count(*) from bodha_msr_signals where chart_id=$1 group by 1,2;
select count(*), count(valence), count(direction), count(cancelled_flag), count(nullif(cardinality(underlying_msr_signal_ids_array),0)) from bodha_cgm_edges where chart_id=$1;
-- Q7
select node_type, count(*) from bodha_cgm_nodes where chart_id=$1 group by 1;
```

Static scans (population: `platform/python-sidecar/pipeline/orchestrator/writers/bo_*.py`, `platform/python-sidecar/bodha_writers/`,
`platform/src`, `platform/scripts`, excluding tests and migrations, at 2a78ec64d): `INSERT INTO` / `DELETE FROM` / `UPDATE` targets
and `replace_prior_*` calls per writer file (§1.1, §6.1); `FROM` / `JOIN` table names per writer file (§3.4).
