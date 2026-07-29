/**
 * registry_bridge_r5w3_judgment_and_portrait.test.ts — MCP-tool-level regression
 * pins for `judgment_query` (design §28.1) and `graha_portrait` (design §28.2),
 * R5 W3 Phase B.
 *
 * Follows the `registry_bridge_r5w1_signals_synthesis.test.ts` precedent: mocks
 * `fetch` (registry_bridge.ts's only I/O) and captures the REAL callback
 * `server.tool(...)` registers via a fake `McpServer`, so this exercises the
 * actual MCP seam (tool registration + Zod schema + handler invocation) — not
 * just the capability handler in isolation. A future edit that silently breaks
 * either tool's live MCP reachability (the exact "registered somewhere,
 * unreachable from the seam" failure class named in JL-009/JL-015(d)) is caught
 * here without needing a live DB.
 *
 * Also pins the R5 W3 Phase B standing checks:
 *   - every Zod-declared param is forwarded to the capability call (the
 *     mandatory W2-lesson, re-verified for both tools here);
 *   - the astrologically typed `pointer_type` field (design §28.4) is present
 *     on `drill_pointers` under response_format='v3', additively alongside the
 *     pre-existing {instrument, hint} shape.
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

/** See registry_bridge_r5w1_signals_synthesis.test.ts's stubFetch docstring for the two
 *  wrapping layers this reproduces ({content, is_error} capability shape + {ok, content}
 *  HTTP envelope). Falls back to an empty digest for query_ucd/get_chart_header so tests
 *  that don't care about orientation/frame-safety don't need to mock them explicitly. */
function stubFetch(payloads: Record<string, unknown>, captured: Array<{ uri: string; args: Record<string, unknown> }>) {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    captured.push(body)
    const defaults: Record<string, unknown> = {
      'marsys://tool/L2/query_ucd': { chart_id: body.args['chart_id'], digest: {}, entity_profiles: [] },
      'marsys://tool/L1/get_chart_header': {
        chart_id_short: '482012f1', name: 'native', lagna_sign: 'Aries', lagna_deg: 1.2,
        moon_sign: 'Purva Bhadrapada', sun_sign: 'Capricorn', ayanamsha: 'lahiri_chitrapaksha',
        current_maha_antar: 'Saturn/Mercury',
      },
    }
    const payload = body.uri in payloads ? payloads[body.uri] : defaults[body.uri]
    if (payload === undefined) {
      throw new Error(`stubFetch: no mocked response for uri "${body.uri}"`)
    }
    const capabilityHandlerReturn = { content: payload, is_error: false }
    return {
      ok: true,
      json: async () => ({ ok: true, content: capabilityHandlerReturn }),
      text: async () => '',
    }
  }))
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

// ── judgment_query ────────────────────────────────────────────────────────────

describe('judgment_query — MCP tool registration + seam reachability', () => {
  it('registers as a real server.tool callback and is reachable', async () => {
    const { server, handlers } = makeCapturingServer()
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    expect(handlers.get('judgment_query')).toBeDefined()
    // Alongside the new tool, spot-check a pre-existing tool still registers too —
    // no alias/registration regression from adding judgment_query (JL-015(d) precedent).
    expect(handlers.get('get_signals')).toBeDefined()
  })

  it('forwards every declared param (chart_id, ayanamsha_id, domain, bhava, max_signals) to the capability call — the mandatory W2-lesson check', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L-JUDGMENT/judgment_query': {
        chart_id: TEST_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha',
        about: { domain: 'marriage', bhava: 7, label: 'Marriage / Partnership', karakas: ['Venus'], operative_varga: 'D9' },
        receipt: { bhava: true, bhavesha: true, karaka: true, from_moon: true, varga_confirmed: 'D9✓', yogas_checked: 2, bhanga_checked: false, timing_anchored: true },
        // SAMĀPTI A2: fixtures name the live MCP tools production actually emits
        // ('ganita_chart_facts_get', not the internal capability name 'get_divisionals')
        // — sc_pointer_validation.ts scans test fixtures too. See the file-level note
        // in src/lib/kala_envelope.test.ts for the convention.
        drill_pointers: [{ instrument: 'ganita_chart_facts_get', hint: 'x', pointer_type: 'confirm_in_varga' }],
        judgment_flags: [],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('judgment_query')!

    await handler({
      chart_id: TEST_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', domain: 'marriage',
      max_signals: 12,
    })

    const call = captured.find(c => c.uri === 'marsys://tool/L-JUDGMENT/judgment_query')
    expect(call).toBeDefined()
    expect(call!.args['chart_id']).toBe(TEST_CHART_ID)
    expect(call!.args['ayanamsha_id']).toBe('lahiri_chitrapaksha')
    expect(call!.args['domain']).toBe('marriage')
    expect(call!.args['max_signals']).toBe(12)
  })

  it('a bare `bhava` (no domain) is forwarded too', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L-JUDGMENT/judgment_query': {
        chart_id: TEST_CHART_ID, about: { bhava: 3 },
        receipt: {}, drill_pointers: [], judgment_flags: [],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('judgment_query')!

    const result = await handler({ chart_id: TEST_CHART_ID, bhava: 3 })
    expect(result.isError).toBeFalsy()

    const call = captured.find(c => c.uri === 'marsys://tool/L-JUDGMENT/judgment_query')!
    expect(call.args['bhava']).toBe(3)
  })

  it('rejects a call with neither `domain` nor `bhava`, without calling the capability', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({}, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('judgment_query')!

    const result = await handler({ chart_id: TEST_CHART_ID })
    expect(result.isError).toBe(true)
    expect(captured.find(c => c.uri === 'marsys://tool/L-JUDGMENT/judgment_query')).toBeUndefined()
  })

  it('response_format=v3 populates drill_pointers with the astrologically typed pointer_type field (design §28.4), additive alongside instrument/hint', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L-JUDGMENT/judgment_query': {
        chart_id: TEST_CHART_ID,
        about: { domain: 'career', bhava: 10, label: 'Career / Vocation', karakas: ['Sun', 'Mercury', 'Saturn'], operative_varga: 'D10' },
        receipt: { bhava: true, bhavesha: true, karaka: true, from_moon: true, varga_confirmed: 'D10✓', yogas_checked: 3, bhanga_checked: false, timing_anchored: true },
        fact_id_refs: ['f-1', 'f-2'],
        drill_pointers: [
          // SAMĀPTI A2: each instrument is a live registered MCP tool, matching what
          // register_d9_judgment.ts:1138-1146 actually emits today. The pre-2026-07-30
          // fixture used the INTERNAL registry capability names ('get_divisionals',
          // 'query_signals', 'query_classical_texts'), none of which is a registered
          // tool — the SC-18 dead-pointer class this fixture was silently modelling.
          { instrument: 'ganita_chart_facts_get', hint: 'full D10 placements.', pointer_type: 'confirm_in_varga' },
          { instrument: 'get_signals', hint: 'domain=career signal set.', pointer_type: 'opposing_yoga' },
          { instrument: 'get_dashas', hint: 'full dasha timeline.', pointer_type: 'dasha_of_promise' },
          { instrument: 'traverse_graph', hint: 'dispositor context.', pointer_type: 'dispositor_chain' },
          { instrument: 'ref_rules_search', hint: 'verse citations.', pointer_type: 'other' },
          { instrument: 'synth_tail_divergence_get', hint: 'tail-check.', pointer_type: 'tail_dissent' },
        ],
        judgment_flags: [],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('judgment_query')!

    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'career', response_format: 'v3' })
    expect(result.isError).toBeFalsy()

    const envelope = result.structuredContent?.object as Record<string, unknown>
    const pointers = envelope['drill_pointers'] as Array<{ instrument: string; hint: string; pointer_type?: string }>
    expect(pointers.length).toBe(6)
    // Every pointer keeps the pre-existing {instrument, hint} shape (additive-only)...
    for (const p of pointers) {
      expect(typeof p.instrument).toBe('string')
      expect(typeof p.hint).toBe('string')
    }
    // ...AND now carries a pointer_type drawn from the closed §28.4 vocabulary.
    const types = pointers.map(p => p.pointer_type)
    expect(types).toEqual([
      'confirm_in_varga', 'opposing_yoga', 'dasha_of_promise',
      'dispositor_chain', 'other', 'tail_dissent',
    ])
    // The tail_dissent move is new this pass — pin its presence + target instrument.
    const tailPointer = pointers.find(p => p.pointer_type === 'tail_dissent')
    expect(tailPointer?.instrument).toBe('synth_tail_divergence_get')
  })

  // WP-S4-fix2 (Gate Ś #10 — receipt-honesty violation, live-reproduced twice against
  // 482012f1): register_d9_judgment.ts can honestly stamp `receipt.timing_anchored: true`
  // pre-serve (e.g. because real chart_dashas mahadasha-window data existed at write time)
  // while the ACTUALLY SERVED `checklist.timing_hooks` arrays are all empty on the wire —
  // whether from response-budget trimming the reconcile helper's trim_report-path matching
  // didn't catch, or the section simply never had data. Either way, a caller must never see
  // an affirmative "✓" receipt next to zero backing evidence (CLAUDE.md §N.6 point 3 / B.10).
  it('forces receipt.timing_anchored=false when served timing_hooks are all empty, even if the capability stamped true (Gate Ś #10)', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L-JUDGMENT/judgment_query': {
        chart_id: TEST_CHART_ID,
        about: { domain: 'wealth', bhava: 2, label: 'Wealth / Artha', karakas: ['Jupiter'], operative_varga: 'D2' },
        checklist: {
          timing_hooks: { current: [], mahadasha_windows_by_graha: {}, kala_activations: [] },
        },
        // The capability honestly believed timing was anchored pre-serve (e.g. real
        // chart_dashas rows existed at write time) — but nothing survived onto the wire.
        receipt: { bhava: true, bhavesha: true, karaka: true, from_moon: true, varga_confirmed: 'D2✓', yogas_checked: 1, bhanga_checked: false, timing_anchored: true },
        fact_id_refs: [],
        drill_pointers: [],
        judgment_flags: [],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('judgment_query')!

    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'wealth', response_format: 'v3' })
    expect(result.isError).toBeFalsy()

    const envelope = result.structuredContent?.object as Record<string, unknown>
    const verdict = envelope['verdict'] as Record<string, unknown>
    const receipt = verdict['receipt'] as Record<string, unknown>
    expect(receipt['timing_anchored']).toBe(false)
    const flags = envelope['judgment_flags'] as Array<{ code: string } | string>
    expect(flags.some(f => typeof f !== 'string' && f.code === 'timing_anchored_forced_false')).toBe(true)
  })

  it('leaves receipt.timing_anchored=true untouched when timing_hooks genuinely carry data', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L-JUDGMENT/judgment_query': {
        chart_id: TEST_CHART_ID,
        about: { domain: 'wealth', bhava: 2, label: 'Wealth / Artha', karakas: ['Jupiter'], operative_varga: 'D2' },
        checklist: {
          timing_hooks: {
            current: [{ level_n: 1, lord_graha: 'Jupiter' }],
            mahadasha_windows_by_graha: {},
            kala_activations: [],
          },
        },
        receipt: { bhava: true, bhavesha: true, karaka: true, from_moon: true, varga_confirmed: 'D2✓', yogas_checked: 1, bhanga_checked: false, timing_anchored: true },
        fact_id_refs: [],
        drill_pointers: [],
        judgment_flags: [],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('judgment_query')!

    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'wealth', response_format: 'v3' })
    const envelope = result.structuredContent?.object as Record<string, unknown>
    const verdict = envelope['verdict'] as Record<string, unknown>
    const receipt = verdict['receipt'] as Record<string, unknown>
    expect(receipt['timing_anchored']).toBe(true)
    const flags = envelope['judgment_flags'] as Array<{ code: string } | string>
    expect(flags.some(f => typeof f !== 'string' && f.code === 'timing_anchored_forced_false')).toBe(false)
  })

  // PARIŚODHANA Phase B1 (CR-2/CR-63/R-38 — receipt-honesty violation, live-confirmed
  // 2026-07-27 on chart 482012f1-710e-4a25-994a-93821f5871aa across wealth/career/marriage):
  // the varga_confirmed sibling of the Gate Ś #10 timing_anchored fix above. register_d9_judgment.ts
  // can stamp receipt.varga_confirmed:"D2✓" from its own pre-trim computation, while the
  // SERVED checklist.varga_confirmation.rows ends up empty on the wire — whether from
  // response-budget trimming (PASS 2's hard-cap fallback can floor this non-hardFloor
  // section to 0) or from finalizeMcpBudget's own trim_report-collapse step erasing the
  // per-path record reconcileReceiptWithTrimReport depends on. Either way, a caller must
  // never see an affirmative "✓" receipt next to zero backing evidence (CLAUDE.md §N.6
  // point 3 / B.10).
  it('forces receipt.varga_confirmed=false when served varga_confirmation.rows are empty, even if the capability stamped "D2✓" (CR-2/CR-63/R-38)', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L-JUDGMENT/judgment_query': {
        chart_id: TEST_CHART_ID,
        about: { domain: 'wealth', bhava: 2, label: 'Wealth / Artha', karakas: ['Jupiter'], operative_varga: 'D2' },
        checklist: {
          varga_confirmation: { varga: 'D2', rows: [] },
        },
        // The capability honestly believed the varga was confirmed pre-serve (e.g. real
        // chart_divisionals rows existed at write time) — but nothing survived onto the wire.
        receipt: { bhava: true, bhavesha: true, karaka: true, from_moon: true, varga_confirmed: 'D2✓', yogas_checked: 1, bhanga_checked: false, timing_anchored: false },
        fact_id_refs: [],
        drill_pointers: [],
        judgment_flags: [],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('judgment_query')!

    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'wealth', response_format: 'v3' })
    expect(result.isError).toBeFalsy()

    const envelope = result.structuredContent?.object as Record<string, unknown>
    const verdict = envelope['verdict'] as Record<string, unknown>
    const receipt = verdict['receipt'] as Record<string, unknown>
    expect(receipt['varga_confirmed']).toBe(false)
    const flags = envelope['judgment_flags'] as Array<{ code: string } | string>
    expect(flags.some(f => typeof f !== 'string' && f.code === 'varga_confirmed_forced_false')).toBe(true)
  })

  it('leaves receipt.varga_confirmed="D9✓" untouched when varga_confirmation.rows genuinely carry data', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L-JUDGMENT/judgment_query': {
        chart_id: TEST_CHART_ID,
        about: { domain: 'marriage', bhava: 7, label: 'Marriage / Partnership', karakas: ['Venus'], operative_varga: 'D9' },
        checklist: {
          varga_confirmation: {
            varga: 'D9',
            rows: [{ role: 'bhavesha', graha: 'Venus', sign: 'Sagittarius', fact_id: 'f-1' }],
          },
        },
        receipt: { bhava: true, bhavesha: true, karaka: true, from_moon: true, varga_confirmed: 'D9✓', yogas_checked: 1, bhanga_checked: false, timing_anchored: false },
        fact_id_refs: [],
        drill_pointers: [],
        judgment_flags: [],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('judgment_query')!

    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage', response_format: 'v3' })
    expect(result.isError).toBeFalsy()

    const envelope = result.structuredContent?.object as Record<string, unknown>
    const verdict = envelope['verdict'] as Record<string, unknown>
    const receipt = verdict['receipt'] as Record<string, unknown>
    expect(receipt['varga_confirmed']).toBe('D9✓')
    const flags = envelope['judgment_flags'] as Array<{ code: string } | string>
    expect(flags.some(f => typeof f !== 'string' && f.code === 'varga_confirmed_forced_false')).toBe(false)
  })
})

// ── graha_portrait ────────────────────────────────────────────────────────────

describe('graha_portrait — MCP tool registration + seam reachability', () => {
  it('registers as a real server.tool callback and is reachable', async () => {
    const { server, handlers } = makeCapturingServer()
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    expect(handlers.get('graha_portrait')).toBeDefined()
    expect(handlers.get('judgment_query')).toBeDefined()
  })

  it('forwards every declared param (chart_id, graha, ayanamsha_id, operative_vargas, include) to the capability call — the mandatory W2-lesson check', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L2/graha_portrait': {
        chart_id: TEST_CHART_ID, graha: 'Saturn', graha_code: 'SAT',
        position: { rows: [], count: 0 },
        completeness: { position: '✓' },
        notes: [],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('graha_portrait')!

    await handler({
      chart_id: TEST_CHART_ID, graha: 'Saturn', ayanamsha_id: 'lahiri_chitrapaksha',
      operative_vargas: ['D1', 'D9'], include: ['position', 'dignity'],
    })

    const call = captured.find(c => c.uri === 'marsys://tool/L2/graha_portrait')
    expect(call).toBeDefined()
    expect(call!.args['chart_id']).toBe(TEST_CHART_ID)
    expect(call!.args['graha']).toBe('Saturn')
    expect(call!.args['ayanamsha_id']).toBe('lahiri_chitrapaksha')
    expect(call!.args['operative_vargas']).toEqual(['D1', 'D9'])
    expect(call!.args['include']).toEqual(['position', 'dignity'])
  })

  it('rejects a call missing `graha`, without calling the capability', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({}, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('graha_portrait')!

    const result = await handler({ chart_id: TEST_CHART_ID })
    expect(result.isError).toBe(true)
    expect(captured.find(c => c.uri === 'marsys://tool/L2/graha_portrait')).toBeUndefined()
  })

  // ŚUDDHA-VĀCA P0-1..4 (lane:serve-shadbala): the native's originating complaint. The
  // strength.rows array for a graha under fact_category='graha_shadbala_total' carries TWO
  // fact_key variants for the SAME (chart_id, ayanamsha_id, fact_subject) — 'ratio' (L1
  // achieved/required, ~0.8-1.7) and 'rupa' (raw achieved, ~4.6-8.5) — confirmed live for
  // chart 482012f1's Sun: ratio=1.694, rupa=8.47. The buggy code selected whichever row
  // `.find()` landed on first (no fact_key pin), got the ratio row, and printed it labeled
  // "rupas" against a hardcoded SHADBALA_REQUIRED_RUPAS[Sun]=5.0 constant — producing
  // "1.69 rupas vs 5.00 required — grade: weak (deficit)" for the chart's single strongest
  // planet. The fix pins fact_key='rupa' AND fetches `required_rupa` from its own L1 fact
  // (stored under ayanamsha_id='INVARIANT', §N.5 — never a wrapper-local constant).
  describe('shadbala narration (P0-1..4 — the native-caught Sun-reads-weak defect)', () => {
    const strengthRowsWithBothFactKeys = [
      {
        fact_id: 'fid-ratio', fact_category: 'graha_shadbala_total', fact_subject: 'SUN',
        ayanamsha_id: 'lahiri_chitrapaksha', fact_key: 'ratio', fact_value_num: 1.694,
        fact_value_text: null, fact_value_jsonb: null, unit: null, verification_pass_status: 'two_pass_verified',
      },
      {
        fact_id: 'fid-rupa', fact_category: 'graha_shadbala_total', fact_subject: 'SUN',
        ayanamsha_id: 'lahiri_chitrapaksha', fact_key: 'rupa', fact_value_num: 8.47,
        fact_value_text: null, fact_value_jsonb: null, unit: null, verification_pass_status: 'two_pass_verified',
      },
    ]

    it('grades Sun STRONG at 8.47 rupas vs 5.00 required — never the ratio row mislabeled as rupas', async () => {
      const { server, handlers } = makeCapturingServer()
      const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
      stubFetch({
        'marsys://tool/L2/graha_portrait': {
          chart_id: TEST_CHART_ID, graha: 'Sun', graha_code: 'SUN',
          strength: { rows: strengthRowsWithBothFactKeys, count: 2 },
          completeness: { strength: '✓' },
          notes: [],
        },
        'marsys://tool/L1/chart_facts_query': {
          rows: [{
            fact_id: 'fid-required-rupa', fact_category: 'graha_shadbala_total', fact_subject: 'SUN',
            ayanamsha_id: 'INVARIANT', fact_key: 'required_rupa', fact_value_num: 5.0,
            fact_value_text: null, fact_value_jsonb: null, unit: null, verification_pass_status: 'two_pass_verified',
          }],
        },
      }, captured)

      const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
      registerRegistryBridgeTools(server, PRINCIPAL)
      const handler = handlers.get('graha_portrait')!

      const result = await handler({ chart_id: TEST_CHART_ID, graha: 'Sun', response_format: 'v3', include: ['strength'] })
      expect(result.isError).toBeFalsy()
      const envelope = result.structuredContent?.object as Record<string, unknown>
      const verdict = envelope['verdict'] as Record<string, unknown>
      const narration = String(verdict['narration'])

      expect(narration).toContain('8.47 rupas vs 5.00 required')
      expect(narration).toContain('strong (surplus)')
      expect(narration).toContain('+3.47 rupas')
      expect(narration).not.toContain('1.69 rupas')
      expect(narration).not.toContain('weak (deficit)')

      // The required_rupa fetch must be the real thing — fact_key pinned, INVARIANT-scoped,
      // never a guessed/hardcoded ayanamsha or category.
      const requiredCall = captured.find(c => c.uri === 'marsys://tool/L1/chart_facts_query')
      expect(requiredCall).toBeDefined()
      expect(requiredCall!.args['ayanamsha_id']).toBe('INVARIANT')
      expect(requiredCall!.args['fact_key']).toBe('required_rupa')
      expect(requiredCall!.args['category']).toBe('graha_shadbala_total')
    })

    it('emits an honest null grade (never a fabricated threshold) when the L1 required_rupa fetch fails', async () => {
      const { server, handlers } = makeCapturingServer()
      const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
      vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
        const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
        captured.push(body)
        if (body.uri === 'marsys://tool/L1/chart_facts_query') {
          throw new Error('simulated required_rupa fetch failure')
        }
        if (body.uri === 'marsys://tool/L2/graha_portrait') {
          return {
            ok: true,
            json: async () => ({ ok: true, content: { content: {
              chart_id: TEST_CHART_ID, graha: 'Sun', graha_code: 'SUN',
              strength: { rows: strengthRowsWithBothFactKeys, count: 2 },
              completeness: { strength: '✓' }, notes: [],
            }, is_error: false } }),
            text: async () => '',
          }
        }
        return {
          ok: true,
          json: async () => ({ ok: true, content: { content: { chart_id_short: '482012f1', name: 'native', lagna_sign: 'Aries', lagna_deg: 1.2, moon_sign: 'Purva Bhadrapada', sun_sign: 'Capricorn', ayanamsha: 'lahiri_chitrapaksha', current_maha_antar: 'Saturn/Mercury' }, is_error: false } }),
          text: async () => '',
        }
      }))

      const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
      registerRegistryBridgeTools(server, PRINCIPAL)
      const handler = handlers.get('graha_portrait')!

      const result = await handler({ chart_id: TEST_CHART_ID, graha: 'Sun', response_format: 'v3', include: ['strength'] })
      expect(result.isError).toBeFalsy()
      const envelope = result.structuredContent?.object as Record<string, unknown>
      const verdict = envelope['verdict'] as Record<string, unknown>
      const narration = String(verdict['narration'])

      // §1.2 / §N.7.6 — an honest null beats an invented judgment: never fall back to a
      // guessed/hardcoded required-rupa threshold just because the real L1 fetch failed.
      expect(narration).toContain('8.47 rupas')
      expect(narration).not.toContain('5.00 required')
      expect(narration).not.toMatch(/grade: (strong|weak)/)
    })
  })

  it('response_format=v3 populates typed drill_pointers (design §28.4), additive alongside instrument/hint', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L2/graha_portrait': {
        chart_id: TEST_CHART_ID, graha: 'Saturn', graha_code: 'SAT',
        position: { rows: [{ fact_id: 'f-1' }], count: 1 },
        completeness: { position: '✓', dignity: '✓', functional_nature: '✓', strength: '✓', avasthas: '✓', yogas: 'zero_rows', dashas: '✓', cgm_neighborhood: '✓' },
        notes: [],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('graha_portrait')!

    const result = await handler({ chart_id: TEST_CHART_ID, graha: 'Saturn', response_format: 'v3' })
    expect(result.isError).toBeFalsy()

    const envelope = result.structuredContent?.object as Record<string, unknown>
    const pointers = envelope['drill_pointers'] as Array<{ instrument: string; hint: string; pointer_type?: string }>
    expect(pointers.length).toBe(3)
    for (const p of pointers) {
      expect(typeof p.instrument).toBe('string')
      expect(typeof p.hint).toBe('string')
      expect(typeof p.pointer_type).toBe('string')
    }
    expect(pointers.map(p => p.pointer_type)).toEqual([
      'dasha_of_promise', 'dispositor_chain', 'karaka_condition',
    ])

    // v3 verdict carries the design §28.6 completeness receipt vocabulary.
    const verdict = envelope['verdict'] as Record<string, unknown>
    expect(verdict['sections_populated']).toBe(7)
    expect(verdict['sections_requested']).toBe(8)
  })
})
