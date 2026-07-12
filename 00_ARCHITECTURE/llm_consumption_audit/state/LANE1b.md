# LANE1b — Concept×Retrievability matrix rollup (FUSED 1b+5 pass)

```
resume:
  lane_id: LANE1b
  fused_with: LANE5 (single pass, shared shard substrate)
  substrate: 00_ARCHITECTURE/llm_consumption_audit/state/FUSED_1b5/shard-*.md
  paths_total: 134
  paths_audited: 134
  families_total: 3058
  per_family_rows_written: 3058
  findings_1b: 133
  status: DONE
  checkpoint_ts: 2026-07-12 (native chart audit session, wave 1)
```

## Scope

Lane 1b answers, per value-family, the question: **is this concept RETRIEVABLE by a consumer,
and through which channel?** One row per family (3058 families across 134 audited paths),
each classified by per-channel verdict. Per-family rows live in the shard substrate at
`FUSED_1b5/shard-*.md` (one shard per table). This file is the roll-up.

## Channel distribution (families by per-channel verdict)

| channel | families | meaning |
|---|---|---|
| reachable-surgical | 1384 | fronted by an ALIVE surgical primitive; consumer can target it directly |
| served-only-by-down-pipeline | 1402 | data exists but only reachable via a DEAD register-class tool or full-pipeline `ask_madhav` — no live surgical primitive |
| truly-UNREACHABLE | 157 | no live path AND/OR no underlying data (empty shell / empty writer plane) |
| mixed | 115 | family reachable on some slices/charts but not others |
| **total** | **3058** | |

Heterogeneity-escalated paths (a table whose families split across channels enough to force
per-family re-derivation rather than path-grade inheritance): **bodha_msr_signals**.

## Interpretation

- **~45% of families (1384/3058) are surgically reachable** — a consumer LLM with the surgical
  primitive set can target them directly.
- **~46% (1402/3058) have data but no live surgical wire** — the register-class tools
  (pattern_register, contradiction_register, resonance_register, cluster_atlas, discovery
  registers) are all in DEAD-19 (500 / not-in-registry on call), and `query_cdlm_lookup` /
  `cgm_graph_walk` / `get_cgm_subgraph` are dead or route to missing URIs. These are the
  **consult-repair (LCA-2) quick-win** class: data + serving code both exist; only the tool
  registry wiring blocks them.
- **~5% (157/3058) are truly unreachable**, dominated by **empty-shell tables** where the
  writer never produced rows (see CRITICAL findings below).

## HIGH / CRITICAL findings (133 Lane-1b findings; the load-bearing subset)

### Empty data plane (CRITICAL — no underlying data on either chart)
- **bodha_cdlm_domain_rollups** — 0 rows both charts; all 21 column-families unretrievable. CDLM domain-rollup layer never populated.
- **bodha_cdlm_evolution_gradients** — 0 rows both charts; all 19 families unretrievable.
- **bodha_cdlm_pattern_clusters** — 0 rows both charts; all 24 families unretrievable.
- **bodha_cgm_chart_topology_summary** — 0 rows both charts; all 26 families (topology metrics, embeddings, graphml/gexf exports) unretrievable.
- **bodha_cgm_motifs** — 0 rows for the **canonical native Abhisek (482012f1)**; only Abhinandan (1c826d5a) has 6 motifs (parivartana_chain 5, stellium 1). The native's own chart yields NO CGM motifs.
- **bodha_cgm_sub_graphs** — EMPTY SHELL: 0 rows across ALL charts (not just the two audit charts). Sub-graph/cluster stage schema-enumerated but never produced data. Doubly unreachable (empty plane + dead front).
- **bodha_contradictions** — EMPTY SHELL: 0 rows across ALL charts. Signal-tension/contradiction detection stage never wrote data. Doubly unreachable (empty plane + dead `contradiction_register`).

### Data exists but no live surgical wire (HIGH — LCA-2 consult-repair quick-win)
- **bodha_anomalies** — 3978 (Abhisek) / 2350 (Abhinandan) rows; no ALIVE surgical primitive; register-class tools all DEAD-19.
- **bodha_cdlm_cells** — 70 rows/chart; surgical `query_cdlm_lookup` confirmed dead (not in registry).
- **bodha_cdlm_chart_summary** — 5 rows/chart; same dead `query_cdlm_lookup`.
- **bodha_cgm_edges** — 1057 rows (Abhisek 534 / Abhinandan 523), all 4 edge_types + 5 relationship_classes + 4 semantic_path_classes populated (aspect 720, argala 222, dispositor 85, dosha_domain 30). Surgical `cgm_graph_walk` not whitelisted; `get_cgm_subgraph` facade 500s routing to it.
- **bodha_cgm_nodes** — 140 rows/chart. `get_cgm_subgraph` is advertised in the surgical whitelist but its handler routes to missing `cgm_graph_walk` URI, 500ing on every call. No live surgical wire path.
- **bodha_cgm_paths** — 45 dispositor-chain path rows/chart; only front `get_cgm_subgraph` 500s (dead `cgm_graph_walk`).
- **bodha_discoveries** — 2392 (Abhisek) / 1150 (Abhinandan) rows; unreachable via any ALIVE surgical tool (discovery/pattern/resonance registers all DEAD-19). CONFIRMED.

### Dead serving tools implicated
- **query_cdlm_lookup** — not in registry (`TOOL_NAME_TO_URI` missing entry). Kills all CDLM surgical retrieval.
- **cgm_graph_walk** — not in surgical whitelist; its facade **get_cgm_subgraph** 500s delegating to the missing URI. Kills all CGM graph retrieval (nodes/edges/paths/motifs/sub_graphs/topology).
- **register-class** (pattern/contradiction/resonance/discovery registers, cluster_atlas) — all DEAD-19.

## Verifier coverage note

Findings above are DB-truth-grounded (read-only `mcp__postgres__query` counts) plus wire probes
(`curl POST /api/mcp/primitives/...`). Where the only front is a dead tool, no wire value exists
to diff — those families are classified from DB truth + registry-probe alone (no fidelity signal
possible; see LANE5.md). Per-family verdicts and exemplar evidence are in `FUSED_1b5/shard-*.md`.
