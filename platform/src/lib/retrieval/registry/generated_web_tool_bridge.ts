/**
 * generated_web_tool_bridge.ts — accessor for the W5 L1 generated web↔MCP bridge
 * ================================================================================
 * Thin, side-effect-free accessor over `web_tool_bridge.generated.json`
 * (`platform/scripts/manifest/generate_projections.ts`, artifact (e) — see that
 * script + `web_tool_bridge_builder.ts` for how the JSON is derived).
 *
 * `tool_name_bridge.ts`'s `resolveToolUri()` consults this as its generated
 * fallback layer: a hand-curated `TOOL_NAME_TO_URI` entry always wins (it may
 * encode a deliberate override), but any name NOT in that hand-curated map is
 * now resolvable if the generated projection covers it — this is the mechanism
 * that widens web-channel floor adoption as the catalog grows, without a human
 * re-editing `tool_name_bridge.ts` every time (the W5 brief's stated goal).
 *
 * Regenerate the JSON with:
 *   npx tsx --conditions=react-server scripts/manifest/generate_projections.ts
 */
import type { CapabilityUri } from './types'
import webToolBridgeData from '../../../generated/projections/web_tool_bridge.generated.json'

interface BridgeEntry {
  name: string
  uri: string | null
}

interface WebToolBridgeJson {
  vidhi_live_tool_bridge: { entries: BridgeEntry[] }
  canonical_faces_bridge: { entries: BridgeEntry[] }
}

const data = webToolBridgeData as unknown as WebToolBridgeJson

/**
 * Merged name → URI map. `canonical_faces_bridge` is the broader list (it's a
 * superset for most entries) and is applied first; `vidhi_live_tool_bridge`
 * entries then apply on top so a name present in both surfaces stays
 * consistent (they resolve the same way — same builder, same inputs — this is
 * just a defensive merge order, not a semantic distinction).
 */
const GENERATED_NAME_TO_URI: ReadonlyMap<string, CapabilityUri> = (() => {
  const m = new Map<string, CapabilityUri>()
  for (const e of data.canonical_faces_bridge.entries) {
    if (e.uri) m.set(e.name, e.uri)
  }
  for (const e of data.vidhi_live_tool_bridge.entries) {
    if (e.uri) m.set(e.name, e.uri)
  }
  return m
})()

/** Resolve a web/MCP-facing tool name via the generated projection. `undefined` if unmapped. */
export function resolveGeneratedToolUri(name: string): CapabilityUri | undefined {
  return GENERATED_NAME_TO_URI.get(name)
}

/** Total distinct names the generated projection can resolve. Exported for tests/census. */
export function generatedBridgeSize(): number {
  return GENERATED_NAME_TO_URI.size
}
