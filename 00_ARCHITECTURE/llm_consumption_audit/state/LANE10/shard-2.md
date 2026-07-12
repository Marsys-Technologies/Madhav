# LANE 10 — PROMISE-vs-DELIVERY — shard-2

Grader: Lane 10 (Charter §7.5 attribution decision tree, RATIFIED).
Charts: Abhisek `482012f1-710e-4a25-994a-93821f5871aa` (A), Abhinandan `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (B).
Channel: DEPLOYED MCP (amjis-mcp-qm256lasva-el.a.run.app), read-only. DB truth: mcp__postgres__query.
Status: COMPLETE — 7/7 assets graded.

## Method notes
- Retrieval-plane reachability determined by (a) grepping `platform/src/lib/retrieval/registry` + `platform/src` for the asset's target table, and (b) live deployed-channel probes of candidate fronting tools.
- 4-source promise re-search for all NOT FOUND rows: build brief (`00_ARCHITECTURE/briefs/`), `asset_registry` row, layer closure doc, MCP tool description. Where a real declared intent was found in the `asset_registry` english_description, promise_status=re-sourced.

---

## AP-015 — ga_vastu — SHORTFALL (retrieval-plane, class 1 UNREACHABLE)
- promise_status: **re-sourced**. No build brief exists. asset_registry english_description IS a declared intent: "Maps each classical graha to its ruling Vastu direction (per bg_vastu_directions) and computes direction_impact (weakened / neutral / strengthened) using condition_score from ga_condition_composite. Indication tier: traditional_vastu."
- data_plane: **present**. `SELECT COUNT(*) FROM ga_vastu_planet_direction_map` → A=40, B=40 (verbatim). target_floor=40.
- retrieval_plane: **UNREACHABLE**. `grep -rn ga_vastu_planet_direction_map platform/src` → ZERO hits outside the writer/migration. No MCP tool in the deployed tools/list (125 tools) fronts vastu. No reachable path in ≤ the calls a consuming LLM would make.
- ranking_form: n/a (never reached).
- shortfall_layer: **retrieval-plane**. Finding: computed+stored (40 rows/chart) but no serving path — class 1.

## AP-016 — ga_yoga — SHORTFALL (retrieval-plane, class 1 UNREACHABLE)
- promise_status: **re-sourced**. Brief `CLAUDECODE_BRIEF_GA_YOGA_REDDOT_AND_NAME_CLEANUP_v1_0.md` is a cockpit-cleanup brief, not a delivery promise. asset_registry declared intent: "Per-chart yoga firing table: evaluates classical Nabhasa and other yoga formation rules against L1 chart_facts. Each row = one yoga that fired, with constituent fact ids, strength, and family tagging."
- data_plane: **present**. `SELECT COUNT(*) FROM ga_yoga_firings` → A=50, B=56 (verbatim). Table carries the asset's distinctive columns: `strength`, `strength_label`, `bhanga_active`, `bhanga_rule_fired`, `partial_formation_pct`, `is_partial`, `family_ids`, `activation_dasha_periods`, `constituent_fact_ids`, `derivation`.
- retrieval_plane: **UNREACHABLE for the asset**. `grep -rn ga_yoga_firings platform/src` → ZERO hits (no serving code). The deployed `ganita_yogas_get` tool is served by `get_yoga_dosha.ts`, which reads `chart_facts` (fact_category IN yoga_fires/yoga_label/dosha_*/bhadra_flag/panchaka_flag) — a DIFFERENT, thinner L1-panchanga surface. Live probe of `ganita_yogas_get` returned chart_facts rows (bhadra_flag / dosha_label), NOT ga_yoga_firings rows. None of the asset's distinctive facets (strength scoring, bhanga/cancellation, partial-formation %, family tagging, dasha-activation windows) is served by any deployed tool.
- shortfall_layer: **retrieval-plane**. The ga_yoga_firings asset (Nabhasa firings + strength + bhanga + family + dasha activation) is entirely unreachable over the wire; a parallel thin yoga-label surface exists via `ganita_yogas_get` but does not deliver the promised firing dossier. Class 1.

## AP-017 — bo_anveshana — DELIVERS
- promise_status: **declared** (brief `CLAUDECODE_BRIEF_BO_ANVESHANA_v1_0.md:45-52` quoted; corroborated by asset_registry "Discovery engine: non-obviousness + graph-mining + embedding outliers + bodha_discoveries + anomalies").
- data_plane: **present**. `bodha_discoveries` A=2392, B=1150; `bodha_anomalies` A=3978, B=2350 (verbatim). count_sql union = A 6370.
- retrieval_plane: **reachable-deployed**. `bodha_discoveries_get` live payload returns first-class RANKED discoveries: `composite_discovery_rank`, `non_obviousness_score`, `consequence_score`, `reasoning_chain_jsonb` (sigma_deviation / subsystem_baseline steps), `why_an_acharya_misses_it`, `surface_reading`/`depth_reading`/`surface_depth_delta`, `hypothesis_text`, `falsifier_jsonb`, `meaningfulness_basis`, `corroborating_methods_array`. Verbatim: `"why_an_acharya_misses_it":"Statistically extreme within ga_sensitive subsystem (5.0σ) but easy to miss when chart is read holistically"`.
- ranking_form: **usable**. Ranked, retrievable, self-describing; the promised "surface consequential non-obvious patterns as first-class, ranked, retrievable insights" is met.
- Note (not a Lane-10 shortfall): R-37 anchor (top-K duplication/family-collapse) is a ranking-QUALITY question owned by Lane 6; the promise-vs-delivery contract is satisfied at the deployed channel. shortfall_layer=none.

## AP-018 — bo_bimba — PARTIAL (data-plane, class 4 EMPTY SHELL on metric/embedding facets)
- promise_status: **declared** (brief `CLAUDECODE_BRIEF_BO_KARANAJALA_BIMBA_v1_0.md:49-50`: "a THIN nodes-only face that registers bodha_cgm_nodes from the same compute"). asset_registry adds the fuller promise: "carries composite_centrality, pagerank, betweenness, VECTOR(768) embedding and igraph-computed metrics".
- data_plane: **partial**. `bodha_cgm_nodes` A=140, B=140 (verbatim; floor=140). BUT metric/embedding coverage is holed on BOTH charts: `count(pagerank_score)=60/140`, `count(betweenness_centrality)=0`, `count(eigenvector_centrality)=0`, `count(node_embedding_vec)=0` (verbatim, both charts identical). The 768-dim embedding, betweenness, and eigenvector centrality the registry promise advertises are entirely NULL.
- retrieval_plane: **reachable-deployed**. `bodha_graph_subgraph_get` live payload returns nodes with metadata (node_type, node_subject, `pagerank_score`, strength_score, dignity_state). Verbatim: `"node_subject":"Moon","pagerank_score":0.1026177,"betweenness_centrality":null,"eigenvector_centrality":null`.
- ranking_form: **degraded** — the served node carries `betweenness_centrality:null` / `eigenvector_centrality:null`, i.e. the tool advertises those fields and returns nothing (class 4).
- Verdict rationale: the QUOTED thin promise (register nodes-only face) DELIVERS — 140 nodes exist and are reachable. But the registry's advertised centrality+embedding metrics are a data-plane void (betweenness/eigenvector/embedding = 0/140), so bo_bimba is graded PARTIAL. shortfall_layer=data-plane. Source disagreement (thin brief vs. fuller registry) logged per §7.5 rule 6.

## AP-019 — bo_cdlm_summary — SHORTFALL (retrieval-plane, class 1 UNREACHABLE)
- promise_status: **re-sourced**. No build brief. asset_registry declared intent: "Per-chart cross-domain linkage strength summary aggregated from bodha_cdlm_cells."
- data_plane: **present**. `SELECT COUNT(*) FROM bodha_cdlm_chart_summary` → A=5, B=5 (verbatim; floor=1).
- retrieval_plane: **UNREACHABLE**. `grep -rn bodha_cdlm_chart_summary platform/src` → ZERO hits. No deployed MCP tool serves the CDLM chart summary.
- shortfall_layer: **retrieval-plane**. Class 1.

## AP-020 — bo_cgm_motifs — SHORTFALL (retrieval-plane, class 1 UNREACHABLE)
- promise_status: **re-sourced**. No motif-specific build brief. asset_registry declared intent: "Recurring structural patterns detected over the CGM graph: mutual reception, stellium, parivartana chains."
- data_plane: **present** (B) / floor-legit-empty (A). `SELECT COUNT(*) FROM bodha_cgm_motifs` → A=0, B=6 (verbatim; target_floor=0, so A=0 is a legitimate "no motifs fired", not a data-plane defect; B=6 confirms the writer produces rows).
- retrieval_plane: **UNREACHABLE**. `grep -rn bodha_cgm_motifs platform/src` → ZERO hits. No deployed MCP tool exposes motifs; `get_cgm_subgraph` / `bodha_graph_subgraph_get` return hub_nodes + convergence digest only — no motif surface.
- shortfall_layer: **retrieval-plane**. Class 1 (the 6 motif rows on chart B can never reach a consumer).

## AP-021 — bo_cgm_paths — SHORTFALL (retrieval-plane, class 1 UNREACHABLE)
- promise_status: **re-sourced**. No build brief. asset_registry declared intent: "Dispositor chain paths and structural path analysis over CGM graph."
- data_plane: **present**. `SELECT COUNT(*) FROM bodha_cgm_paths` → A=45, B=45 (verbatim; floor=9).
- retrieval_plane: **UNREACHABLE**. `grep -rn bodha_cgm_paths platform/src` → ZERO hits. Only consumer anywhere is `platform/python-sidecar/services/ph_nimitta/engine.py:287` (an L4 internal build-time consumer: "from bodha_cgm_paths (top path for this signal)") — NOT an MCP retrieval surface. No deployed tool serves paths over the wire.
- shortfall_layer: **retrieval-plane**. Class 1.

---
## Roll-up
| row | asset | verdict | shortfall_layer | class |
|---|---|---|---|---|
| AP-015 | ga_vastu | SHORTFALL | retrieval-plane | 1 |
| AP-016 | ga_yoga | SHORTFALL | retrieval-plane | 1 |
| AP-017 | bo_anveshana | DELIVERS | none | — |
| AP-018 | bo_bimba | PARTIAL | data-plane | 4 |
| AP-019 | bo_cdlm_summary | SHORTFALL | retrieval-plane | 1 |
| AP-020 | bo_cgm_motifs | SHORTFALL | retrieval-plane | 1 |
| AP-021 | bo_cgm_paths | SHORTFALL | retrieval-plane | 1 |

5 retrieval-plane UNREACHABLE (class 1), 1 data-plane EMPTY-SHELL partial (class 4), 1 DELIVERS.
Cross-note: 5 of 7 assets in this shard are built + populated in the DB on both charts but have NO deployed MCP serving path (vastu, yoga-firings, cdlm_summary, motifs, paths). Systemic retrieval-plane gap for L1 vastu/yoga-firing surfaces and the CGM motif/path/CDLM-summary derived surfaces.
