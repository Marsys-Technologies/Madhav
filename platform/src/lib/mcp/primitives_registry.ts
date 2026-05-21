/**
 * primitives_registry.ts — Surgical primitive whitelist for MCP Tier 3 tools.
 *
 * Single source of truth for which retrieval tools are exposed as MCP surgical
 * primitives. The dispatcher (/api/mcp/primitives/[tool]/route.ts) uses
 * isAllowedSurgicalTool() to reject tool names not in this whitelist with a
 * {ok: false, error: {class: "validation"}} envelope.
 *
 * Surgical primitives bypass the planner and B.11 floor. They are tagged
 * surgical: true in the epistemics block per MCP_BRIEF §4.1 Tier 3.
 *
 * MCP_BRIEF §4.1 — 10 exposed primitives:
 *   query_chart_facts → chart_facts_query
 *   query_signals     → msr_sql
 *   query_dasha_periods → query_dasha_periods
 *   query_panchanga   → query_panchanga
 *   query_ephemeris   → query_ephemeris
 *   query_transit_event → query_transit_event
 *   lel_query         → lel_query
 *   vector_search     → vector_search
 *   get_cgm_subgraph  → cgm_graph_walk
 *   cross_school_lookup → multi_school_signal_lookup
 */

/** The 10 underlying retrieval tool names exposed as surgical primitives. */
export const SURGICAL_TOOLS = [
  'chart_facts_query',
  'msr_sql',
  'query_dasha_periods',
  'query_panchanga',
  'query_ephemeris',
  'query_transit_event',
  'lel_query',
  'vector_search',
  'cgm_graph_walk',
  'multi_school_signal_lookup',
] as const

export type SurgicalToolName = (typeof SURGICAL_TOOLS)[number]

/**
 * Maps MCP-facing primitive tool names (as Claude calls them) to the underlying
 * retrieval tool names registered in RETRIEVAL_TOOLS (platform/src/lib/retrieve/).
 */
export const MCP_TO_RETRIEVAL_TOOL: Record<string, SurgicalToolName> = {
  query_chart_facts: 'chart_facts_query',
  query_signals: 'msr_sql',
  query_dasha_periods: 'query_dasha_periods',
  query_panchanga: 'query_panchanga',
  query_ephemeris: 'query_ephemeris',
  query_transit_event: 'query_transit_event',
  lel_query: 'lel_query',
  vector_search: 'vector_search',
  get_cgm_subgraph: 'cgm_graph_walk',
  cross_school_lookup: 'multi_school_signal_lookup',
}

/**
 * Type guard: returns true if the given MCP tool name is in the surgical
 * primitive whitelist. Used by the dispatcher to reject unlisted tool names.
 */
export function isAllowedSurgicalTool(
  mcpToolName: string
): mcpToolName is keyof typeof MCP_TO_RETRIEVAL_TOOL {
  return mcpToolName in MCP_TO_RETRIEVAL_TOOL
}
