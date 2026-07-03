---
artifact: RETRIEVAL_CITATION_REPORT_D4_GRAPH_ADOPTION
canonical_id: RETRIEVAL_CITATION_REPORT_D4_GRAPH_ADOPTION
version: 1.0
status: CURRENT
created: 2026-06-28
author: D4 wave agent (Claude Code, feature/retrieval-d4-graph)
classification: Gate C reverse-citation report — D4 wave
gate: Gate C (CLAUDECODE_BRIEF_RETRIEVAL_PARALLEL_COORDINATION §2)
scope: platform-mcp/src/tools/get_cgm_subgraph.ts adoption (NOT deletion)
---

# GATE C — Reverse-Citation Report: D4 Graph Adoption

## §1 — What this report covers

The D4 wave adopts the logic from `platform-mcp/src/tools/get_cgm_subgraph.ts` (the BFS traversal
approach) into the new registry capability at
`platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts`.

**No file was deleted.** The old file is NOT removed — Gate C applies when deleting/retiring.
This report documents the supersession relationship and active citation status for the record.

## §2 — Old file status

**File:** `platform-mcp/src/tools/get_cgm_subgraph.ts`
**Status:** Written-yet-unwired (per RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION §2 B4)
**Target table:** `bodha_graph` — the pre-mig-325 table, now DROPPED by migration 325.
**MCP wiring:** NOT registered in `platform-mcp/src/server.ts` (confirmed: grep returned no hits)
**Decision:** RETAIN-AS-IS (no functional impact since table is dropped + tool unregistered)

## §3 — Active citations found (grep results, 2026-06-28)

| File | Line | Citation | Classification |
|---|---|---|---|
| `platform-mcp/src/tools/get_cgm_subgraph.ts` | self | Self-reference in comments | IGNORE |
| `platform-mcp/src/resources/capabilities.ts:91` | `\| \`get_cgm_subgraph\` \| Active \|` | Documentation string | STALE-DOC (not functional) |
| `platform-mcp/src/resources/capabilities.ts:162` | `\| \`get_cgm_subgraph\` \| CGM graph subgraph walk \|` | Documentation string | STALE-DOC (not functional) |
| `platform-mcp/src/bundles/holistic_bundle.ts:194` | `CGM: 'get_cgm_subgraph'` | String constant, not an import | UNREACHABLE (tool unregistered) |
| `platform-mcp/src/resources/house_rules_variants/universal.md:27` | `` - `get_cgm_subgraph` (CGM corpus) `` | LLM-visible doc | STALE-DOC (tool not wired) |

## §4 — Verdict

All citations are either:
- Documentation/doc-strings (not functional code paths)
- String constants in `holistic_bundle.ts` that reference a tool name (not an import), and the
  referenced tool is not registered in `server.ts` anyway (dead string reference)

**No active functional path routes through `get_cgm_subgraph`.** The old file is safe to leave in
place; D4's `traverse_chart_graph` in the new registry is the canonical graph traversal capability.

The stale documentation citations in `capabilities.ts` and `universal.md` should be updated as part
of the D7 (channels) wave when the MCP surface is consolidated — that is the correct scope for those
changes, not D4.

## §5 — Schema adoption note

The old `get_cgm_subgraph.ts` targeted `bodha_graph` (the old table, DROPPED by mig 325).
The new `traverse_chart_graph.ts` targets `bodha_cgm_nodes` + `bodha_cgm_edges` + `bodha_contradictions`
(the mig 325 schema). These are structurally different tables — the adoption is of the BFS pattern
only, not the SQL.

*End of RETRIEVAL_CITATION_REPORT_D4_GRAPH_ADOPTION v1.0.*
