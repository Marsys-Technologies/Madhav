/**
 * deprecated_tool_gate.ts — RC-14 breaking flip: the P1 legacy-name removal gate
 * ================================================================================
 * RETRIEVAL_RESIDUAL_CLOSURE_BRIEF §E RC-14 ("impl/w5-breaking" flip). Phase-3 of
 * MCP_TOOL_NAMING_STANDARD §4 ("remove the OLD-name registrations"): the go-forward
 * MCP surface exposes ONLY the canonical `layer_noun_verb` faces
 * (`platform/src/lib/retrieval/registry/canonical_faces.json` → `canonical_faces`).
 * The 43 legacy short names (that file's `deprecated_aliases` KEYS) are cut over.
 *
 * WHY A CENTRAL GATE (not 43 hand-deletions across ~9 registrars): every canonical
 * face already resolves (verified: each `deprecated_aliases` value is a live
 * `server.tool` registration), and every legacy name's own handler delegates to a
 * platform PRIMITIVE (e.g. `callPlatformPrim('query_remedies', …)`) or registry
 * capability — NOT to the sibling MCP `server.tool` — so removing the legacy MCP
 * registration drops zero capability. Gating in ONE place (a) is the mechanism the
 * RC-14 task itself sanctions ("gate it so it no longer registers legacy names"),
 * (b) keeps a single auditable source of truth mirroring canonical_faces.json,
 * (c) is trivially reversible, and (d) can't half-break a multi-line handler block.
 *
 * WEB-CHANNEL REPLAY IS UNAFFECTED: old persisted web conversations that reference
 * these legacy names still resolve through the web door
 * (`platform/src/lib/retrieval/registry/tool_name_bridge.ts` +
 * `web_tool_bridge.generated.json`), which is a DIFFERENT surface and is KEPT. This
 * gate only removes the names from THIS MCP server's `tools/list`.
 *
 * Applied UNCONDITIONALLY (all profiles, including `full`) — unlike the profile gate
 * (`mcp_profile.ts::applyProfileGate`), which is a no-op for `full`. Call ONCE, right
 * after constructing the per-request McpServer, before any `register*Tools()` runs.
 */

import type { ToolRegisteringServer } from './mcp_profile.js'

/**
 * The 43 legacy P1 tool names removed from the MCP surface at the RC-14 breaking flip.
 * MIRROR of `canonical_faces.json`'s `deprecated_aliases` KEYS (2026-07-23). Kept as a
 * TS mirror (same pattern as `mcp_surface_profiles.generated.ts`) because platform-mcp
 * cannot import the platform-package JSON across the process boundary. If a name is
 * added to / removed from `deprecated_aliases`, update this set (the
 * deprecated_tool_gate.test.ts count assertion guards the size).
 *
 * The 6 DEFERRED renames (recall_session→session_recall, …) are NOT here — those are
 * renamed at their source registrations (old name gone, new name live), not gated.
 */
export const DEPRECATED_MCP_TOOL_NAMES: ReadonlySet<string> = new Set([
  // registry_bridge.ts (D7/D8)
  'list_assets', 'get_cgm_subgraph', 'traverse_graph', 'get_signals',
  'get_chart_orientation', 'get_domain_reading', 'get_chart_quality', 'get_remedies',
  'query_chart_facts', 'get_positions', 'get_dashas', 'get_projections',
  'get_temporal_windows', 'yoga_activation_by_dasha', 'get_classical_citation',
  'vector_search',
  // l0_brahmagyan.ts
  'asset_registry_all', 'asset_registry_l0',
  // l0_ephemeris.ts
  'query_aspects_at_time', 'ephemeris_cache_year', 'query_planet_position',
  'query_planet_transit', 'query_retrograde_periods',
  // retrieval/remedy_tools.ts
  'query_mantras', 'list_remedies_by_category', 'query_remedies_by_planet',
  'query_remedies_for_chart', 'query_remedies', 'read_remedy', 'query_tantric_remedies',
  // retrieval/pyhora_natal.ts
  'compute_natal_positions', 'query_special_lagnas',
  // phala tool files
  'event_anchors', 'mitigation_map', 'phala_outlook', 'muhurta_finder',
  // mimamsa tool files
  'query_calibration', 'lel_query', 'record_outcome',
  // register_p1_aliases.ts in-file deprecated names
  'bodha_remedies_search', 'query_dasha_periods', 'ref_remedies_search',
  'util_intent_classify',
])

export interface DeprecatedGateResult {
  /** Legacy names whose registration was blocked this request (read after all register*Tools run). */
  blockedDeprecated: string[]
}

/* eslint-disable @typescript-eslint/no-explicit-any -- McpServer.tool() is a heavily
   overloaded SDK method; this gate only needs to intercept the call by NAME. Same
   `as any` pattern mcp_profile.ts::applyProfileGate uses for the same reason. */

/**
 * Monkeypatches `server.tool()` IN PLACE so any registration for a name in
 * DEPRECATED_MCP_TOOL_NAMES becomes a no-op (the legacy tool is never added to this
 * request's McpServer, so a `tools/call` for it fails exactly like any unregistered
 * name — MCP protocol error, not a filtered success). Idempotent-safe per request
 * (fresh McpServer per POST /mcp). Apply BEFORE applyProfileGate so both layers stack.
 */
export function applyDeprecatedToolGate(server: ToolRegisteringServer): DeprecatedGateResult {
  const blockedDeprecated: string[] = []
  const originalTool = server.tool.bind(server)
  server.tool = (name: string, ...rest: any[]) => {
    if (DEPRECATED_MCP_TOOL_NAMES.has(name)) {
      blockedDeprecated.push(name)
      return undefined
    }
    return originalTool(name, ...rest)
  }
  return { blockedDeprecated }
}
/* eslint-enable @typescript-eslint/no-explicit-any */
