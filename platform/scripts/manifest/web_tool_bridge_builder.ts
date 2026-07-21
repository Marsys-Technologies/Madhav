/**
 * web_tool_bridge_builder.ts — R-1 projection compiler, 5th artifact (W5 L1)
 * ================================================================================
 * RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §3 R-1 item 2 lists the projection
 * compiler's outputs as "chat tool defs, MCP tool registrations, census, docs
 * resource, per-family schema dialects...". W4 close (STATE.md) measured the
 * web chat channel reaching only ~10% of the compiled floor (career-family
 * only) because TWO separate hand-maintained name-mapping layers stood between
 * the deterministic Vidhi floor compiler's MCP-native `live_tool` names and the
 * web channel's retrieval-registry execution path:
 *
 *   1. `tool_name_bridge.ts`'s `TOOL_NAME_TO_URI` — legacy retrieval-tool name
 *      → registry URI (~89 hand-curated entries).
 *   2. `compiled_floor_adapter.ts`'s `LIVE_TOOL_TO_RETRIEVAL` — MCP `live_tool`
 *      name → retrieval-tool name (hand-curated, only 4 of the 23 distinct
 *      `live_tool` names `src/lib/vidhi/registry_data.ts` declares).
 *
 * Neither layer is generated from the catalog; both drift independently as the
 * catalog grows (exactly the failure mode this campaign's projection compiler
 * exists to kill — see R1_PROJECTION_COMPILER_REPORT.md).
 *
 * This module builds ONE generated projection — `web_tool_bridge.generated.json`
 * — that supersedes #2 above (and gives #1 a generated fallback layer, see
 * `tool_name_bridge.ts`'s `resolveToolUri()`), by mechanically chaining THREE
 * already-existing, already-authored data sources instead of re-typing a 4th:
 *
 *   (a) `getCatalog()` — every live capability's own `.name` resolves directly
 *       (a capability registered under the exact MCP-facing name needs no
 *       alias at all).
 *   (b) `canonical_faces.json`'s `deprecated_aliases` (D-2 Lane V-3) — maps a
 *       LEGACY retrieval-facing name to its CANONICAL MCP-facing name. Reversed
 *       here (canonical → legacy) so a canonical `live_tool` name can find its
 *       legacy twin.
 *   (c) `tool_name_bridge.ts`'s `TOOL_NAME_TO_URI` + `MCP_TO_RETRIEVAL_TOOL` —
 *       the legacy twin (from (b)) resolves to a URI through the existing
 *       hand-curated chain, which is preserved as-is (not re-authored) because
 *       it encodes real migration history (D7, WP-1.x, R6 0b-deadtools) that
 *       is not mechanically re-derivable from the catalog alone.
 *
 * Every resolution is reported with its `resolution_kind` and the exact chain
 * of intermediate names used — nothing is silently invented; an unresolvable
 * name is reported as `unmapped`, never dropped.
 */
import type { CapabilityDescriptor } from '../../src/lib/retrieval/registry/types'
import { resolveType } from './projection_builders'

export type WebToolBridgeResolutionKind =
  | 'catalog_name_direct'      // toolName === some live capability's own .name
  | 'legacy_retrieval_name'    // toolName is a TOOL_NAME_TO_URI key directly
  | 'mcp_alias_direct'         // toolName is an MCP_TO_RETRIEVAL_TOOL key whose target resolves
  | 'canonical_reverse_alias'  // toolName is canonical; a deprecated_aliases legacy twin resolves
  | 'unmapped'

export interface WebToolBridgeEntry {
  name: string
  uri: string | null
  resolution_kind: WebToolBridgeResolutionKind
  /** Intermediate names walked to reach the URI, in order (empty for direct hits). */
  via: string[]
}

export interface CanonicalFacesData {
  canonical_faces: string[]
  deprecated_aliases: Record<string, string>
}

/**
 * Pure resolver — no I/O. Takes every data source as an explicit argument so
 * both the CLI generator and a future parity test can call the exact same
 * logic (the r5 codegen-parity discipline `projection_builders.ts` already
 * documents).
 *
 * @param names               the MCP/web-facing names to resolve (e.g. Vidhi's
 *                            23 distinct `live_tool` values, or the full
 *                            `canonical_faces` list for broader coverage).
 * @param caps                live catalog (`getCatalog()`).
 * @param legacyToUri         `TOOL_NAME_TO_URI` (legacy retrieval name → URI).
 * @param mcpToRetrieval      `MCP_TO_RETRIEVAL_TOOL` (MCP-facing name → legacy
 *                            retrieval name).
 * @param canonicalFaces      parsed `canonical_faces.json`.
 */
export function resolveWebToolBridge(
  names: string[],
  caps: CapabilityDescriptor[],
  legacyToUri: Readonly<Record<string, string>>,
  mcpToRetrieval: Readonly<Record<string, string>>,
  canonicalFaces: CanonicalFacesData,
): WebToolBridgeEntry[] {
  const catalogNameToUri = new Map<string, string>()
  for (const c of caps) {
    if (resolveType(c) === 'tool' && c.name && !catalogNameToUri.has(c.name)) {
      catalogNameToUri.set(c.name, c.uri)
    }
  }

  // Reverse deprecated_aliases: canonical (MCP-facing) name → legacy alias name(s).
  const canonicalToLegacy = new Map<string, string[]>()
  for (const [legacy, canonical] of Object.entries(canonicalFaces.deprecated_aliases ?? {})) {
    const arr = canonicalToLegacy.get(canonical) ?? []
    arr.push(legacy)
    canonicalToLegacy.set(canonical, arr)
  }

  function resolveOne(name: string): WebToolBridgeEntry {
    // (a) direct catalog hit — the capability is already registered under this exact name.
    const catalogUri = catalogNameToUri.get(name)
    if (catalogUri) {
      return { name, uri: catalogUri, resolution_kind: 'catalog_name_direct', via: [] }
    }

    // (b) legacy retrieval name resolves directly via the existing hand-curated map.
    const legacyUri = legacyToUri[name]
    if (legacyUri) {
      return { name, uri: legacyUri, resolution_kind: 'legacy_retrieval_name', via: [] }
    }

    // (c) MCP-facing alias → legacy retrieval name → URI.
    const viaLegacy = mcpToRetrieval[name]
    if (viaLegacy) {
      const uri = legacyToUri[viaLegacy] ?? catalogNameToUri.get(viaLegacy) ?? null
      if (uri) {
        return { name, uri, resolution_kind: 'mcp_alias_direct', via: [viaLegacy] }
      }
    }

    // (d) name is a CANONICAL face; walk its legacy twin(s) through the same two hops.
    const legacyTwins = canonicalToLegacy.get(name) ?? []
    for (const legacy of legacyTwins) {
      const directUri = legacyToUri[legacy] ?? catalogNameToUri.get(legacy)
      if (directUri) {
        return { name, uri: directUri, resolution_kind: 'canonical_reverse_alias', via: [legacy] }
      }
      const viaLegacy2 = mcpToRetrieval[legacy]
      if (viaLegacy2) {
        const uri2 = legacyToUri[viaLegacy2] ?? catalogNameToUri.get(viaLegacy2)
        if (uri2) {
          return { name, uri: uri2, resolution_kind: 'canonical_reverse_alias', via: [legacy, viaLegacy2] }
        }
      }
    }

    return { name, uri: null, resolution_kind: 'unmapped', via: [] }
  }

  return names.map(resolveOne).sort((a, b) => a.name.localeCompare(b.name))
}
