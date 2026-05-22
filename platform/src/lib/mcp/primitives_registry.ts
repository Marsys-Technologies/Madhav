/**
 * primitives_registry.ts — Surgical primitive whitelist for MCP Tier 3 + Tier 4 tools.
 *
 * Single source of truth for which retrieval tools are exposed as MCP primitives.
 * The dispatcher (/api/mcp/primitives/[tool]/route.ts) uses
 * isAllowedSurgicalTool() to reject tool names not in this whitelist with a
 * {ok: false, error: {class: "validation"}} envelope.
 *
 * Surgical primitives bypass the planner and B.11 floor. They are tagged
 * surgical: true in the epistemics block per MCP_BRIEF §4.1 Tier 3.
 *
 * MCP arch §3.7 — 10 Tier 3 primitives + 1 Tier 4 raw-asset read:
 *   query_chart_facts    → chart_facts_query
 *   query_signals        → msr_sql
 *   query_dasha_periods  → query_dasha_periods
 *   query_panchanga      → query_panchanga
 *   query_ephemeris      → query_ephemeris
 *   query_transit_event  → query_transit_event
 *   lel_query            → lel_query
 *   vector_search        → vector_search
 *   get_cgm_subgraph     → cgm_graph_walk
 *   cross_school_lookup  → multi_school_signal_lookup
 *   read_classical_text  → classical_text_search  (Tier 4 raw-asset read)
 */

/** The underlying retrieval tool names exposed as MCP primitives. */
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
  'classical_text_search',
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
  read_classical_text: 'classical_text_search',
}

/**
 * Type guard: returns true if the given MCP tool name is in the surgical
 * primitive whitelist. Used by the dispatcher to reject unlisted tool names.
 *
 * Uses Object.hasOwn() rather than `in` to avoid prototype-pollution false
 * positives (e.g. "__proto__" is a prototype property on all plain objects).
 */
export function isAllowedSurgicalTool(
  mcpToolName: string
): mcpToolName is keyof typeof MCP_TO_RETRIEVAL_TOOL {
  return Object.hasOwn(MCP_TO_RETRIEVAL_TOOL, mcpToolName)
}
