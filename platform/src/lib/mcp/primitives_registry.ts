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
 * MCP arch §3.7 — 14 Tier 3 primitives + 1 Tier 4 raw-asset read:
 *   query_chart_facts       → chart_facts_query
 *   query_signals           → msr_sql
 *   query_dasha_periods     → query_dasha_periods
 *   query_panchanga         → query_panchanga
 *   query_ephemeris         → query_ephemeris
 *   query_transit_event     → query_transit_event
 *   lel_query               → lel_query
 *   vector_search           → vector_search
 *   get_cgm_subgraph        → cgm_graph_walk
 *   cross_school_lookup     → multi_school_signal_lookup
 *   read_classical_text     → classical_text_search  (Tier 4 raw-asset read)
 *   — TR Wave additions (PR #159 / Tooling Remediation v1.0) —
 *   query_varshphal         → query_varshaphala      (Class A: engine existed)
 *   query_divisional_chart  → divisional_query        (Class A: engine existed)
 *   query_remedial_mantras  → remedial_codex_query    (Class A: engine existed)
 *   muhurta_finder          → query_muhurat           (Class A: engine existed)
 *
 * NOT YET WHITELISTED (Class B/C/D — engine implementation required first):
 *   tara_balam_for_native, chandra_balam_for_native — retrieval tool not yet built
 *   query_transits_over_natal — engine needs to be written (TR §6.1)
 *   query_yogas_active_now — engine needs to be written (TR §6.2)
 *   get_shadbala_full — roll-up engine needs to be written (TR §6.4)
 *   query_planetary_period_predictions — engine needs to be written (TR §7.3)
 *   query_dasamsha_career — engine needs to be written (TR §7.4)
 *   query_shashtiamsha — engine needs to be written (TR §7.5)
 *   query_drekkana_drishti — engine needs to be written (TR §7.6)
 *   query_remedies_prescribed — engine needs to be written (TR §8.3)
 *   query_jaimini_chara_dasha — sidecar stub not yet implemented (TR §7.2)
 *   query_eclipse_transits — sidecar stub not yet implemented (TR §8.1)
 *   query_planet_war — thin engine not yet built (TR §8.2)
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
  // TR Wave Class A retrieval tools (engines existed pre-PR-#159)
  'query_varshaphala',
  'divisional_query',
  'remedial_codex_query',
  'query_muhurat',
  // TR Wave Class B/C stubs (retrieval tools not yet built; listed here so
  // MCP_TO_RETRIEVAL_TOOL stub entries satisfy the SurgicalToolName type)
  'query_tara_balam',
  'query_chandra_balam',
  'jaimini_chara_dasha',
  'jaimini_chara_dasha_full',
  // UDA Campaign additions — 14 portal-native tools now whitelisted for MCP primitive dispatch
  'msr_sql',
  'temporal',
  'kp_query',
  'query_kp_ruling_planets',
  'pattern_register',
  'resonance_register',
  'cluster_atlas',
  'contradiction_register',
  'query_ucn_walk',
  'query_cdlm_lookup',
  'query_rm_walk',
  'query_jaimini_drishti',
  'timeline_query',
  'query_signal_state',
] as const

export type SurgicalToolName = (typeof SURGICAL_TOOLS)[number]

/**
 * Maps MCP-facing primitive tool names (as Claude calls them) to the underlying
 * retrieval tool names registered in RETRIEVAL_TOOLS (platform/src/lib/retrieve/).
 */
export const MCP_TO_RETRIEVAL_TOOL: Record<string, SurgicalToolName> = {
  // Original 11
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
  // TR Wave additions (PR #159 — Class A: existing retrieval engines)
  query_varshphal: 'query_varshaphala',
  query_divisional_chart: 'divisional_query',
  query_remedial_mantras: 'remedial_codex_query',
  muhurta_finder: 'query_muhurat',
  // TR Wave Class A — retrieval-name aliases (TR wrappers call callPlatformPrimitive
  // with the retrieval name directly, not the MCP name; these pass-through entries
  // are required for production dispatch to succeed)
  query_varshaphala: 'query_varshaphala',
  divisional_query: 'divisional_query',
  remedial_codex_query: 'remedial_codex_query',
  query_muhurat: 'query_muhurat',
  // TR Wave Class B/C stubs — admit through whitelist so failure shifts from
  // 400 whitelist-block to 500 retrieval-not-found (retrieval tools not yet built)
  query_tara_balam: 'query_tara_balam',
  query_chandra_balam: 'query_chandra_balam',
  jaimini_chara_dasha: 'jaimini_chara_dasha',
  jaimini_chara_dasha_full: 'jaimini_chara_dasha_full',
  // UDA Campaign additions — 14 portal-native tools exposed as MCP primitives
  // MCP name → platform retrieval tool name (same in all 14 cases)
  msr_sql: 'msr_sql',
  temporal: 'temporal',
  kp_query: 'kp_query',
  query_kp_ruling_planets: 'query_kp_ruling_planets',
  pattern_register: 'pattern_register',
  resonance_register: 'resonance_register',
  cluster_atlas: 'cluster_atlas',
  contradiction_register: 'contradiction_register',
  query_ucn_walk: 'query_ucn_walk',
  query_cdlm_lookup: 'query_cdlm_lookup',
  query_rm_walk: 'query_rm_walk',
  query_jaimini_drishti: 'query_jaimini_drishti',
  timeline_query: 'timeline_query',
  query_signal_state: 'query_signal_state',
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
