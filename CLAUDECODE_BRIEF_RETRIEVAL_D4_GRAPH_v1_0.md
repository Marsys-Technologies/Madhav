---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_D4_GRAPH
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-06-27
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — D4 graph retrieval (the CGM traversal tool; highest net-new value)
session_type: implementation — the superhuman-value surface
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 (principle 4; wave D4)
depends_on: D1 (contract)
prereq_reading:
  - RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md (principle 4; wave D4)
  - RETRIEVAL_GROUNDTRUTH_ASSET_MATRIX_v1_0.md (§3 CGM nodes/edges/contradictions spine)
  - RETRIEVAL_GROUNDTRUTH_TOOL_TOPOLOGY_v1_0.md (worked example 4: traverse_chart_graph)
  - RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md (§2 B4: get_cgm_subgraph + vector_search exist but UNWIRED)
hard_constraints:
  - skip LLM graph-extraction — the relationships are CURATED (CGM nodes/edges already exist in mig 325)
  - chart-agnostic (#14); empty-on-missing (#2); reference-keyed returns (F1)
acceptance_criteria: see §4
---

# CLAUDE CODE BRIEF — D4: GRAPH RETRIEVAL (CGM traversal tool)

> This is where the corpus's unique relational value lives — holding all linkages at once, surfacing
> convergences and contradictions no human reads in working memory. The relationships are ALREADY curated
> (bodha_cgm_nodes/edges, bodha_contradictions in mig 325), so we DO NOT pay for LLM entity/relation extraction.

## §0 — Embedded decisions
- Build ONE dedicated `traverse_chart_graph` tool (topology worked-ex 4): modes neighbors / paths /
  convergence-clusters / contradictions, depth + filter, keyed/returned by signal_id.
- **Adopt the existing unwired code:** `platform-mcp/src/tools/get_cgm_subgraph.ts` and the `vector_search`
  impl in `bo_2-7.ts` are real but unwired and (per audit) may carry native-default contamination — adopt
  their logic into a clean, chart-agnostic registry capability; do NOT carry their contamination forward.
- Retain passage/signal-level retrieval alongside the graph (avoid the factual-regression trap).

## §1 — The traversal tool
Implement over bodha_cgm_nodes (centrality: pagerank/betweenness/hub) + bodha_cgm_edges (relationship_basis,
valence, cross-subsystem) + bodha_contradictions. Entry by metric-rank OR semantic (768-dim node vectors via
the Vertex embeddings, `bo_samskara`). **Decision in-wave:** precise traversal mechanism — Text2Cypher over a
property-graph view vs a parameterized SQL/recursive-CTE API vs adopting get_cgm_subgraph's manifest approach.
Recommendation: start with the existing SQL/manifest path (it's real), add a cheap multi-hop primitive
(PPR-style / bounded budget) for "themes across everything."

## §2 — Grounding + dedup
Nodes/edges resolve to signal_ids → the grounding spine (D3) hydrates each once with value + citation (F1/F3).
Contradictions surface as first-class results. Empty-on-missing for absent subgraphs (never fabricate edges).

## §3 — What this is NOT
Not a generic GraphRAG indexing pipeline (no LLM extraction). Not the router (D2 dispatches to this). Not the
per-asset fan-out (D5).

## §4 — Acceptance criteria
- `traverse_chart_graph` registry capability (chart-agnostic, contract-conformant) with the 4 modes.
- Adopts existing get_cgm_subgraph/vector_search logic, scrubbed of any native default; gate green.
- Multi-hop primitive for cross-domain "themes/contradictions"; passage-level retrieval retained.
- Returns signal_id-keyed refs hydrated via D3; contradictions first-class; empty-on-missing.
- Tests on a real chart's CGM (two distinct charts → disjoint subgraphs; no native bleed).

*End of CLAUDECODE_BRIEF_RETRIEVAL_D4_GRAPH v1.0.*
