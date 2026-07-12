# FUSED Lane 1b+5 shard — mimamsa_preferences (8 families)

Channel (path-level): served-only-by-down-pipeline. No surgical MCP tool serves this table (0 CAPABILITY_MANIFEST mappings; 0 refs in mcp/primitives/[tool]/route.ts; absent from ALIVE + DEAD-19 lists). Serving path is the portal/L5 operational pipeline only (UI preference save/load), not a chart-consuming MCP surgical tool.
DB truth: `SELECT count(*) FROM mimamsa_preferences` = 0 rows (EMPTY). Columns: user_id, channel_id, saved_state, updated_at. Non-chart operational state (no chart_id column) — user UI preferences, currently unpopulated on both charts.
Wire probe: NONE possible — no surgical tool to call; can't diff wire-vs-DB. Lane 5 four failure modes un-testable (no wire value).
Derivation: path-grade(exemplar=user_id[VF-2448]) + member-confirmation (all 8 families identical channel/shape — same table, same absent-surgical-tool condition, same 0-row data-plane state). heterogeneity_escalated=false.

| family_key | channel | retrievability_verdict | fidelity_verdict | derivation |
|---|---|---|---|---|
| user_id (VF-2448) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; table EMPTY (0 rows); non-chart operational state | N/A — no wire path; diff un-exercisable | path-grade(exemplar=user_id) + member-confirmation |
| channel_id (VF-2449) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; table EMPTY (0 rows) | N/A — no wire path | path-grade + member-confirmation |
| saved_state (VF-2450) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; table EMPTY (0 rows) | N/A — no wire path | path-grade + member-confirmation |
| updated_at (VF-2451) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; table EMPTY (0 rows) | N/A — no wire path | path-grade + member-confirmation |
| user_id (VF-2998) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; table EMPTY (0 rows); dup of VF-2448 | N/A — no wire path | path-grade + member-confirmation |
| channel_id (VF-2999) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; table EMPTY (0 rows); dup of VF-2449 | N/A — no wire path | path-grade + member-confirmation |
| saved_state (VF-3000) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; table EMPTY (0 rows); dup of VF-2450 | N/A — no wire path | path-grade + member-confirmation |
| updated_at (VF-3001) | served-only-by-down-pipeline | UNREACHABLE-via-public-MCP; table EMPTY (0 rows); dup of VF-2451 | N/A — no wire path | path-grade + member-confirmation |
