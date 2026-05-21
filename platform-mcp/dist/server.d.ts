/**
 * server.ts — MARSYS-JIS MCP HTTP/SSE server entry point.
 *
 * Architecture: thin HTTP adapter over the MARSYS platform.
 * - Each POST /mcp request creates a new stateless McpServer + transport.
 * - Auth: Bearer key validated via /api/mcp/keys/validate before tool dispatch.
 * - Stateless per D10 (no conversation history; host chat owns the thread).
 * - 19 tools registered as of MCP-4-S1 (16 read + 3 write).
 *
 * Tool count (v1, all registered as of MCP-4-S1):
 *   Tier 1: ask_madhav
 *   Tier 2: plan_query, execute_plan
 *   Tier 3 (10): query_chart_facts, query_signals, query_dasha_periods,
 *                query_panchanga, query_ephemeris, query_transit_event,
 *                lel_query, vector_search, get_cgm_subgraph, cross_school_lookup
 *   Tier 4 (1): read_asset
 *   Tier 5 (2): get_trace, list_recent_queries
 *   Tier 6 — Write tools (3, MCP-4-S1): log_prediction, record_outcome, flag_disagreement
 *
 * Cloud Run configuration (amjis-mcp service):
 *   Memory: 512 MB, Min instances: 1, Concurrency: 80, Region: asia-south1.
 *   Health check: GET /health → 200 { status: "ok", service: "marsys-mcp" }
 */
export {};
//# sourceMappingURL=server.d.ts.map