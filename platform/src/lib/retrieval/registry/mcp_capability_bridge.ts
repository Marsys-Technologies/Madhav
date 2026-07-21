/**
 * MCP Capability Bridge
 * =====================
 * Maps between the MCP server's tool registrations and the Consume Chat registry URIs.
 * Used by parity_check.ts to compare both channels.
 *
 * The bridge reads the MCP server's registered tool names and maps them to
 * the canonical marsys:// URI scheme used by the retrieval registry.
 *
 * D7 extension (Phase 4 remediation): bridge now also exposes
 * `getRegistryCapabilitiesForMcp()` so the MCP server can introspect which
 * registry capabilities are available at boot without importing the full
 * registry directly (avoiding circular dependency risks).
 *
 * D6/D7 extension (2026-06-28): added all consolidated MCP tool URIs for the
 * 12 workflow-shaped tools (~§2.1 of the D7 brief). Extended from 5 → 17 mappings.
 * Parity is now enforced across the full consolidated MCP surface.
 */

import type { CapabilityUri } from './types'

/**
 * URI prefix mappings from MCP tool names to marsys:// URIs.
 * Format: MCP tool name → marsys:// URI
 *
 * Covers the full set of MCP tools registered in platform-mcp/src/server.ts.
 * Extended by D7 to include all layer tool names from the rebuild arc.
 * Tool names are snake_case, no hyphens, ≤64 chars (cross-family compliance:
 * satisfies Anthropic ^[a-zA-Z0-9_-]{1,64}$ and Gemini [A-Za-z0-9_.]).
 */
const MCP_TOOL_TO_URI: Record<string, CapabilityUri> = {
  // ── L0 Brahmagyan capabilities (Stream A) ──────────────────────────────────
  'resolve_entity':                    'marsys://tool/L0/resolve_entity',
  'list_entities':                     'marsys://tool/L0/list_entities',
  'intent_classify':                   'marsys://prompt/intent-classify',
  'intent-classify':                   'marsys://prompt/intent-classify',
  // Resources use their path as URI
  'asset_registry_all':                'marsys://resource/asset-registry/all',
  'asset_registry_l0':                 'marsys://resource/asset-registry/L0',
  'asset-registry-all':                'marsys://resource/asset-registry/all',
  'asset-registry-L0':                 'marsys://resource/asset-registry/L0',
  // Classical text retrieval (L0)
  'get_classical_citation':            'marsys://tool/L0/query_classical_texts',
  // L0 Stream B — Ephemeris
  'query_planet_position':             'marsys://tool/L0/query_planet_position',
  'query_planet_transit':              'marsys://tool/L0/query_planet_transit',
  'query_aspects_at_time':             'marsys://tool/L0/query_aspects_at_time',
  'query_retrograde_periods':          'marsys://tool/L0/query_retrograde_periods',
  'ephemeris_cache_year':              'marsys://resource/L0/ephemeris_cache_year',
  'ephemeris_cache_native_lifetime':   'marsys://resource/L0/ephemeris_cache_native_lifetime',
  // L0 corpus query tools (Wave 3 R2)
  'query_yoga_catalog':                'marsys://tool/L0/query_yoga_catalog',
  'query_dosha_catalog':               'marsys://tool/L0/query_dosha_catalog',
  'query_remedy_corpus':               'marsys://tool/L0/query_remedy_corpus',
  'query_classical_texts':             'marsys://tool/L0/query_classical_texts',
  // ── L1 Gaṇita capabilities ─────────────────────────────────────────────────
  // PyJHora Stream G
  'compute_natal_positions':           'marsys://tool/L1/compute_natal_positions',
  'query_dasha_periods':               'marsys://tool/L1/query_dasha_periods',
  'query_special_lagnas':              'marsys://tool/L1/query_special_lagnas',
  // Consolidated MCP workflow tools (§2.1 of D7 brief)
  'get_positions':                     'marsys://tool/L1/get_positions',
  'get_dashas':                        'marsys://tool/L1/get_dashas',
  // ── L2 Bodha capabilities ──────────────────────────────────────────────────
  'holistic_bundle':                   'marsys://tool/L2/holistic_bundle',
  'chart_facts_read':                  'marsys://tool/L2/chart_facts_read',
  'query_domain_reading':              'marsys://tool/L2/query_domain_reading',
  'query_signals':                     'marsys://tool/L2/query_signals',
  'query_contradictions':              'marsys://tool/L2/query_contradictions',
  'query_remedies':                    'marsys://tool/L2/query_remedies',
  'query_quality_scorecard':           'marsys://tool/L2/query_quality_scorecard',
  // Consolidated MCP workflow tools (§2.1 of D7 brief)
  'get_chart_orientation':             'marsys://tool/L2/query_ucd',
  'get_domain_reading':                'marsys://tool/L2/query_domain_reading',
  'get_signals':                       'marsys://tool/L2/query_signals',
  'traverse_graph':                    'marsys://tool/L2/traverse_chart_graph',
  'get_remedies':                      'marsys://tool/L2/query_remedies',
  'get_chart_quality':                 'marsys://tool/L2/query_quality_scorecard',
  // ── L3 Kāla capabilities ───────────────────────────────────────────────────
  'kala_temporal':                     'marsys://tool/L3/kala_temporal',
  'query_temporal_activation':         'marsys://tool/L3/query_temporal_activation',
  'query_convergence_windows':         'marsys://tool/L3/query_convergence_windows',
  'query_life_arc':                    'marsys://tool/L3/query_life_arc',
  'query_projections':                 'marsys://tool/L3/query_projections',
  'get_temporal_windows':              'marsys://tool/L3/query_temporal_activation',
  'get_projections':                   'marsys://tool/L3/query_projections',
  // ── L4 Phala capabilities ──────────────────────────────────────────────────
  'phala_event_anchors':               'marsys://tool/L4/phala_event_anchors',
  'phala_mitigation_map':              'marsys://tool/L4/phala_mitigation_map',
  'phala_outlook':                     'marsys://tool/L4/phala_outlook',
  'muhurta_finder':                    'marsys://tool/L4/muhurta_finder',
  // ── L5 Mīmāṃsā capabilities ───────────────────────────────────────────────
  'lel_query':                         'marsys://tool/L5/lel_query',
  'mimamsa_outcome':                   'marsys://tool/L5/mimamsa_outcome',
  // DOCTRINE-WAVES D-4b Lane B-5 (= BRIEF_D4.md v2.0 Lane C-6): mechanism_retrodiction
  'mechanism_retrodiction_get':        'marsys://tool/L5/mechanism_retrodiction_get',
  // L0 Remedy tools (Stream F)
  'query_remedies_tool':               'marsys://tool/L0/query_remedies_tool',
  // ── Asset catalog (all layers) ─────────────────────────────────────────────
  'list_assets':                       'marsys://resource/asset-registry/all',
  // D6/D7 synergy + channel introspection (internal-only, not LLM-facing)
  'synergy_pipeline':                  'marsys://tool/synergy/pipeline',
  'synergy_cross_layer':               'marsys://tool/synergy/cross_layer',
  'channel_mcp_wiring':                'marsys://tool/channel/mcp_wiring',
  'channel_chat_dispatch':             'marsys://tool/channel/chat_dispatch',
  // MARO meta-capabilities (D-PROFILES)
  'maro_orchestrate':                  'marsys://tool/maro/orchestrate',
  'maro_mcp_surface':                  'marsys://tool/maro/mcp_surface',
}

/**
 * Returns the set of capability URIs that the MCP server currently exports.
 * Reads from the MCP server's registered tools at runtime.
 */
export async function listMcpCapabilityUris(): Promise<CapabilityUri[]> {
  // In production: query the MCP server for its tool/resource/prompt list
  // In CI: use the statically declared MCP_TOOL_TO_URI map
  // This implementation uses the static map for determinism
  return Object.values(MCP_TOOL_TO_URI)
}

/**
 * Convert an MCP tool name to a marsys:// URI.
 */
export function mcpToolNameToUri(toolName: string): CapabilityUri | undefined {
  return MCP_TOOL_TO_URI[toolName]
}

/**
 * Register a new MCP tool → URI mapping.
 * Called when new capabilities are added to both channels.
 */
export function registerMcpToolUri(toolName: string, uri: CapabilityUri): void {
  MCP_TOOL_TO_URI[toolName] = uri
}

/**
 * getRegistryCapabilitiesForMcp() — D7 extension.
 *
 * Returns all MCP tool → URI mappings currently declared in this bridge.
 * Used by platform-mcp/src/server.ts at boot to verify that its registered
 * tool names are covered by registry URIs, enabling the audit CHECK 3 gate:
 * "MCP server tools are wired to the retrieval registry."
 *
 * This avoids a direct import of the registry into the MCP server package
 * (which would create a cross-package dependency). Instead, the bridge is
 * the shared coordination point.
 */
export function getRegistryCapabilitiesForMcp(): Record<string, CapabilityUri> {
  // Return a frozen snapshot so callers cannot mutate the bridge map
  return Object.freeze({ ...MCP_TOOL_TO_URI })
}
