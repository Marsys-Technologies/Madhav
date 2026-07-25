/**
 * el36_graha_portrait_self_starvation.test.ts — EL-36 regression pin.
 *
 * THE BUG (deferred by the batch-1 builder): graha_portrait's MCP layer prepends a generic
 * `orientation_context` digest (a per-graha entity_profiles row for essentially every OTHER
 * entity in the chart). Before this fix:
 *   - the orientation trimmable section pointed at the WRONG path
 *     (`orientation_context.entity_profiles` instead of the live, double-wrapped
 *     `orientation_context.content.entity_profiles`) — a silent no-op, so the generic
 *     preamble was never trimmable and always survived; and
 *   - NONE of the entity-specific payload sections (position/dignity/strength/…) declared
 *     `hardFloor`, so the response-budget PASS 2 hard-cap floored the REAL answer to 0 while
 *     the generic preamble sailed through — a portrait of "0 rows served" over a completeness
 *     receipt still reading "✓".
 *
 * THE FIX (this pin verifies): the priority is INVERTED — the generic orientation preamble is
 * the first thing sacrificed (minKeep 0, no hardFloor, correct `.content.` path), and the
 * confirmed entity-specific sections declare `hardFloor: true` so they survive at their
 * declared minKeep. The completeness receipt is reconciled against what actually shipped.
 *
 * Uses the same fetch-stub seam as registry_bridge_r5w3_judgment_and_portrait.test.ts (no DB).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

type ToolHandler = (args: Record<string, unknown>) => Promise<{
  structuredContent?: { type: 'object'; object: unknown }
  content: Array<{ type: 'text'; text: string }>
  isError?: boolean
}>

function makeCapturingServer(): { server: McpServer; handlers: Map<string, ToolHandler> } {
  const handlers = new Map<string, ToolHandler>()
  const server = {
    tool: (name: string, _desc: string, _schema: unknown, handler: ToolHandler) => {
      handlers.set(name, handler)
    },
  } as unknown as McpServer
  return { server, handlers }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const TEST_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/** Reproduces production's two wrapping layers: the capability handler shape
 *  ({ content, is_error }) plus the HTTP envelope ({ ok, content }). */
function stubFetch(payloads: Record<string, unknown>, captured: Array<{ uri: string; args: Record<string, unknown> }>) {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    captured.push(body)
    const defaults: Record<string, unknown> = {
      'marsys://tool/L1/get_chart_header': {
        chart_id_short: '482012f1', name: 'native', lagna_sign: 'Aries', lagna_deg: 1.2,
        moon_sign: 'Purva Bhadrapada', sun_sign: 'Capricorn', ayanamsha: 'lahiri_chitrapaksha',
        current_maha_antar: 'Saturn/Mercury',
      },
    }
    const payload = body.uri in payloads ? payloads[body.uri] : defaults[body.uri]
    if (payload === undefined) throw new Error(`stubFetch: no mocked response for uri "${body.uri}"`)
    const capabilityHandlerReturn = { content: payload, is_error: false }
    return { ok: true, json: async () => ({ ok: true, content: capabilityHandlerReturn }), text: async () => '' }
  }))
}

/** A large generic orientation digest — the "prepended preamble" the bug let survive.
 *  ~300 entity_profiles rows, each a chunky object, so it dominates the 12KB ceiling on its
 *  own and MUST be the first thing trimmed. */
function bigOrientationPayload() {
  const entity_profiles = Array.from({ length: 300 }, (_, i) => ({
    entity: `graha_${i}`,
    top_signal_ids: [`sig-${i}-a`, `sig-${i}-b`, `sig-${i}-c`],
    salience: 0.5,
    narrative: `Generic composite-ranked digest row ${i} — this is framing for a DIFFERENT entity than the one asked about, recoverable in full via get_chart_orientation. `.repeat(2),
  }))
  return { chart_id: TEST_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', digest: { msr_signal_count: 573 }, entity_profiles }
}

/** A small-but-REAL Saturn portrait — the entity-specific answer that must survive. */
function realSaturnPortrait() {
  const bigish = (n: number, tag: string) =>
    Array.from({ length: n }, (_, i) => ({ tag: `${tag}-${i}`, value: `deterministic-${tag}-row-${i}`, fact_id: `f-${tag}-${i}` }))
  return {
    chart_id: TEST_CHART_ID, graha: 'Saturn', graha_code: 'SAT',
    position: { rows: [{ fact_id: 'f-pos-1', sign: 'Libra', house: 7, nakshatra: 'Vishakha' }], count: 1 },
    dignity: {
      operative_varga_rows: bigish(4, 'op'),
      all_varga_rows: bigish(20, 'all'),   // superset dup — floorable first (no hardFloor)
      other_rows: bigish(10, 'other'),     // floorable first (no hardFloor)
    },
    functional_nature: { rows: bigish(2, 'fn') },
    strength: { rows: bigish(6, 'str') },
    avasthas: { rows: bigish(5, 'av') },
    yogas: {
      parivartana_exchanges: bigish(3, 'pv'),        // confirmed — hardFloor
      catalog_yoga_matches: bigish(6, 'cy'),         // catalog-only — floorable
      catalog_dosha_matches: bigish(6, 'cd'),        // catalog-only — floorable
    },
    dashas: { rows: bigish(5, 'da') },
    cgm_neighborhood: { edges: bigish(5, 'edge'), nodes: bigish(5, 'node') },
    provenance: { synthesis_of: Array.from({ length: 8 }, (_, i) => `marsys://tool/x/${i}`) },
    completeness: {
      position: '✓', dignity: '✓', functional_nature: '✓', strength: '✓', avasthas: '✓',
      yogas: '✓', dashas: '✓', cgm_neighborhood: '✓',
    },
  }
}

beforeEach(() => { vi.unstubAllGlobals() })

describe('EL-36 — graha_portrait no longer self-starves under the generic orientation preamble', () => {
  it('protects the entity-specific payload and sacrifices the generic preamble first', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L2/query_ucd': bigOrientationPayload(),
      'marsys://tool/L2/graha_portrait': realSaturnPortrait(),
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('graha_portrait')!

    const result = await handler({ chart_id: TEST_CHART_ID, graha: 'Saturn', response_format: 'v3' })
    expect(result.isError).toBeFalsy()

    const env = result.structuredContent?.object as Record<string, unknown>
    const content = env['content'] as Record<string, unknown>

    // 1. The whole thing actually shrank under the 12KB ceiling (the pre-fit was ~50KB+).
    const wireBytes = Buffer.byteLength(JSON.stringify(env), 'utf8')
    expect(wireBytes).toBeLessThanOrEqual(12 * 1024)

    // 2. The generic preamble is what got cut — orientation_context.content.entity_profiles
    //    is drastically reduced from the 300 rows fed in (the correct `.content.` path now bites).
    const oc = env['orientation_context'] as Record<string, unknown>
    const ocInner = oc['content'] as Record<string, unknown>
    const survivingProfiles = (ocInner['entity_profiles'] as unknown[]) ?? []
    expect(survivingProfiles.length).toBeLessThan(50) // started at 300; heavily sacrificed

    // 3. The entity-specific CORE answer SURVIVED at (or above) its declared hardFloor minKeep —
    //    this is the exact "real rows exist, 0 served" defect EL-36 names, now closed.
    expect((content['position'] as Record<string, unknown>)['rows']).toHaveLength(1)
    const dignity = content['dignity'] as Record<string, unknown>
    expect((dignity['operative_varga_rows'] as unknown[]).length).toBeGreaterThanOrEqual(2)
    expect((content['strength'] as Record<string, unknown>)['rows']).toHaveLength(6)
    expect(((content['avasthas'] as Record<string, unknown>)['rows'] as unknown[]).length).toBeGreaterThanOrEqual(3)
    const yogas = content['yogas'] as Record<string, unknown>
    expect((yogas['parivartana_exchanges'] as unknown[]).length).toBeGreaterThanOrEqual(3)
    expect(((content['dashas'] as Record<string, unknown>)['rows'] as unknown[]).length).toBeGreaterThanOrEqual(2)
    const cgm = content['cgm_neighborhood'] as Record<string, unknown>
    expect((cgm['edges'] as unknown[]).length).toBeGreaterThanOrEqual(3)
    expect((cgm['nodes'] as unknown[]).length).toBeGreaterThanOrEqual(3)

    // 4. Receipt truth: because the core sections genuinely survived, their completeness marks
    //    stay '✓' honestly (no false-positive over an empty array; no false downgrade either).
    const verdict = env['verdict'] as Record<string, unknown>
    const completeness = verdict['completeness'] as Record<string, string>
    expect(completeness['position']).toBe('✓')
    expect(completeness['strength']).toBe('✓')
    expect(completeness['dashas']).toBe('✓')
    // sections_populated is consistent with the surviving '✓' marks.
    const populated = Object.values(completeness).filter(v => v === '✓').length
    expect(verdict['sections_populated']).toBe(populated)
  })

  it('trims non-hardFloor superset/catalog sections before the confirmed core, and records it honestly', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L2/query_ucd': bigOrientationPayload(),
      'marsys://tool/L2/graha_portrait': realSaturnPortrait(),
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('graha_portrait')!

    const result = await handler({ chart_id: TEST_CHART_ID, graha: 'Saturn', response_format: 'v3' })
    const env = result.structuredContent?.object as Record<string, unknown>
    const trimReport = env['trim_report'] as Array<{ path: string; kept_count: number }> | null | undefined
    expect(Array.isArray(trimReport)).toBe(true)

    // The generic preamble is what shrank — asserted on the SERVED DATA (robust): the
    // trim_report itself is allowed to self-degrade (finalizeMcpBudget drops its own entries
    // when re-attaching them reopens the gap), so the data is the load-bearing evidence.
    const oc = env['orientation_context'] as Record<string, unknown>
    const ocInner = oc['content'] as Record<string, unknown>
    expect(((ocInner['entity_profiles'] as unknown[]) ?? []).length).toBeLessThan(50) // from 300

    // No CONFIRMED hardFloor core section was floored to zero — the load-bearing safety
    // invariant, checked against the trim_report's own honest record of what it cut to 0.
    const coreZeroed = (trimReport ?? []).some(e =>
      e.kept_count === 0 &&
      /content\.(position\.rows|dignity\.operative_varga_rows|strength\.rows|avasthas\.rows|dashas\.rows|cgm_neighborhood\.(edges|nodes)|yogas\.parivartana_exchanges|functional_nature\.rows)$/.test(e.path))
    expect(coreZeroed).toBe(false)

    // And the served content confirms the same core sections are non-empty on the wire.
    const content = env['content'] as Record<string, unknown>
    expect(((content['position'] as Record<string, unknown>)['rows'] as unknown[]).length).toBeGreaterThan(0)
    expect(((content['strength'] as Record<string, unknown>)['rows'] as unknown[]).length).toBeGreaterThan(0)
  })
})
