/**
 * verify_capability_map.integration.test.ts — WP-1.6 (P-12) map-route verification.
 *
 * The data-plane verifier for the capability MAP: samples N concept families from
 * the generated CONCEPT_CAPABILITY_MAP.json, resolves each family's claimed route
 * against the LIVE, integrated retrieval registry, EXECUTES the handler on the
 * native chart, and confirms the concept actually ARRIVES (a payload comes back,
 * not is_error). This is the empirical check the static, table-granular map cannot
 * make on its own — it proves the concept→route→arrival path resolves NOW, post-W1.
 *
 * Gated by INTEGRATION=true (needs the live read-only DB), same as the WP-1.3f suite.
 *   INTEGRATION=true npx vitest run \
 *     scripts/audit/capability_map/verify_capability_map.integration.test.ts
 */
import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, it, expect } from 'vitest'

const INTEGRATION = process.env.INTEGRATION === 'true'
const describeIf = INTEGRATION ? describe : describe.skip

const NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'

const __dirname = dirname(fileURLToPath(import.meta.url))
const MAP_PATH = join(
  __dirname, '..', '..', '..', '..',
  '00_ARCHITECTURE/llm_consumption_audit/capability_map/CONCEPT_CAPABILITY_MAP.json'
)

interface MapRoute { uri: string; tool: string; layer: string; scope: string; deployed_mcp: boolean }
interface MapConcept { table: string; seed_channel: string; post_w1_channel: string; routes: MapRoute[] }
interface MapFamily { family_key: string; reachable_post_w1: boolean; best_channel: string; moved: boolean; concepts: MapConcept[] }

function loadMap(): MapFamily[] {
  return (JSON.parse(readFileSync(MAP_PATH, 'utf8')) as { families: MapFamily[] }).families
}

/**
 * A curated, diverse sample spanning L1–L5, deployed + surgical channels, and
 * several W1 newly-reachable tables (phala_*, mimamsa_*). Each entry names the
 * concrete route tool we expect the map to carry for that family, and executes
 * it. Chosen so every route requires only chart_id (+ optional ayanamsha/limit).
 */
const SAMPLE: Array<{ family: string; table: string; tool: string }> = [
  { family: 'anumukha_shani_period::duration_days', table: 'chart_facts', tool: 'chart_facts_query' },
  { family: 'anchored_solar_return_iso', table: 'chart_dashas', tool: 'get_dashas' },
  { family: 'activation_predicted_dates_jsonb', table: 'bodha_msr_signals', tool: 'query_signals' },
  { family: 'anchor_id', table: 'phala_anchors', tool: 'query_predictive_anchors' },      // W1 newly reachable
  { family: 'action_class', table: 'phala_muhurta', tool: 'query_auspicious_windows' },    // W1 newly reachable
  { family: 'afflicting_graha', table: 'phala_mitigation', tool: 'query_remedy_program' }, // W1 newly reachable
  { family: 'base_rate', table: 'mimamsa_calibration', tool: 'query_calibration' },        // W1 newly reachable
  { family: 'chart_id', table: 'kala_convergence', tool: 'query_convergence_windows' },
]

async function getHandler(uri: string) {
  await import('@/lib/retrieval/registry/catalog')
  const { getCapability } = await import('@/lib/retrieval/registry')
  const cap = getCapability(uri)
  if (!cap) throw new Error(`capability not registered: ${uri}`)
  return cap.handler as (a: Record<string, unknown>, c?: unknown) => Promise<{ content: unknown; is_error?: boolean }>
}

describeIf('WP-1.6 capability map — sampled routes resolve + arrive on the live DB', () => {
  it('every sampled family carries its claimed route in the generated map', () => {
    const map = loadMap()
    const byKey = new Map(map.map((f) => [f.family_key, f]))
    for (const s of SAMPLE) {
      const fam = byKey.get(s.family)
      expect(fam, `family missing from map: ${s.family}`).toBeDefined()
      const concept = fam!.concepts.find((c) => c.table === s.table)
      expect(concept, `concept ${s.family}@${s.table} missing`).toBeDefined()
      const tools = concept!.routes.map((r) => r.tool)
      expect(tools, `route ${s.tool} not on ${s.family}@${s.table} (has ${tools.join(',')})`).toContain(s.tool)
    }
  })

  it('executing each sampled route on the native chart returns a payload (concept arrives, not is_error)', async () => {
    const results: Array<{ family: string; tool: string; arrived: boolean; empty: boolean }> = []
    for (const s of SAMPLE) {
      const map = loadMap()
      const fam = map.find((f) => f.family_key === s.family)!
      const route = fam.concepts.find((c) => c.table === s.table)!.routes.find((r) => r.tool === s.tool)!
      const handler = await getHandler(route.uri)
      const res = await handler({ chart_id: NATIVE, ayanamsha_id: AYANAMSHA, limit: 5 })
      const arrived = res.is_error !== true && res.content != null
      const empty = JSON.stringify(res.content ?? {}).length < 40
      results.push({ family: s.family, tool: s.tool, arrived, empty })
      expect(res.is_error, `${s.tool} errored for ${s.family}`).not.toBe(true)
      expect(res.content, `${s.tool} returned no content for ${s.family}`).toBeTruthy()
    }
    console.log('[WP-1.6 map-route sample]\n' + results.map((r) => `  ${r.family} -> ${r.tool} -> arrived=${r.arrived}${r.empty ? ' (honest-empty)' : ''}`).join('\n'))
    expect(results.every((r) => r.arrived)).toBe(true)
  })
})
