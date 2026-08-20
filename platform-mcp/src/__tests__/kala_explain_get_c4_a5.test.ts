/**
 * kala_explain_get_c4_a5.test.ts — SM-γ C4: A5 gochara-agreement facet on `kala_explain_get`
 *
 * Tests the SM_GAMMA_C4_ENABLED flag-guarded `a5_gochara_agreement` field added to
 * `registerKalaExplainTool` (explain.ts).
 *
 * §N.8 earned-signal discipline: the "flag OFF → field absent" tests assert that the key is
 * NOT present in the response object at all (not merely undefined), matching the
 * byte-identical contract stated in C4.3.
 *
 * Contract gates:
 *   ✓ Flag OFF → `a5_gochara_agreement` absent from response
 *   ✓ Flag ON + gochara windows concur with verdict → agreement = 'concurs', gochara_windows_active > 0
 *   ✓ Flag ON + gochara windows dissent from verdict → agreement = 'dissents'
 *   ✓ Flag ON + no gochara windows for event_class → agreement = 'insufficient_data'
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// F-73: `fetchA5GocharaWindows` (explain.ts) calls `computeGocharaForecast` directly
// (in-process, same package) instead of round-tripping through the registry/HTTP capability
// system — the `marsys://tool/L4/gochara_forecast_get` URI it used to call was never backed
// by a registered capability, so every call 404'd and A5's agreement was permanently
// `insufficient_data`. Mock the real call site instead of intercepting an HTTP call that no
// longer happens.
const mockComputeGocharaForecast = vi.hoisted(() => vi.fn())
vi.mock('../tools/retrieval/register_gochara_windows.js', () => ({
  computeGocharaForecast: mockComputeGocharaForecast,
}))

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

function extractObject(result: Awaited<ReturnType<ToolHandler>>): Record<string, unknown> {
  expect(result.structuredContent).toBeDefined()
  return result.structuredContent!.object as Record<string, unknown>
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const TEST_CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

// Canonical PACT response fixture (chain_complete, marriage domain, bhava=7)
const PACT_CHAIN_COMPLETE = {
  chart_id: TEST_CHART_ID,
  ayanamsha_id: 'lahiri_chitrapaksha',
  as_of_date: '2026-08-13',
  about: { domain: 'marriage', bhava: 7, label: 'Marriage / Partnership' },
  pact_status: 'chain_complete',
  stages: [
    { stage: 'PROMISE', status: 'promised', reason: 'Rashi checklist supports marriage.' },
    { stage: 'CONFIRMATION', status: 'confirmed', reason: 'D9 dignity is net-favorable.', dignities: [{ fact_id: 'fact_d9_venus' }] },
    { stage: 'ACTIVATION', status: 'active', reason: 'Venus dasha currently running.' },
    { stage: 'TRIGGER', status: 'triggered', reason: 'Transit Jupiter over 7th lord.' },
  ],
  drill_pointers: [],
  judgment_flags: [],
  fact_id_refs: ['fact_promise_1'],
}

const PACT_DENIED = {
  chart_id: TEST_CHART_ID,
  ayanamsha_id: 'lahiri_chitrapaksha',
  as_of_date: '2026-08-13',
  about: { domain: 'marriage', bhava: 7, label: 'Marriage / Partnership' },
  pact_status: 'denied_at_confirmation',
  stages: [
    { stage: 'PROMISE', status: 'promised', reason: 'Rashi checklist supports the matter.' },
    { stage: 'CONFIRMATION', status: 'denied', reason: 'D9 dignity is net-hostile.', dignities: [{ fact_id: 'fact_d9_venus' }] },
  ],
  drill_pointers: [],
  judgment_flags: [],
  fact_id_refs: ['fact_promise_1'],
}

// Gochara windows fixtures
const GOCHARA_GAIN_WINDOWS = {
  windows: [
    {
      id: 1, chart_id: TEST_CHART_ID, event_class: 'relationship_gain',
      temporal_shape: 'interval', window_start: '2026-07-01', window_end: '2026-12-31',
      peak_date: '2026-09-15', milestone_id: null, is_irreversibility_milestone: false,
      signed_intensity: 2.0, raw_intensity: 2.0, valence: 'gain', is_adverse: false,
      active_sentences: [], contributing_systems: [], suppression_state: {},
      peak_basis: 'peak_date', calibration_state: 'calibrated', source: 'live',
      computed_at: '2026-08-01T00:00:00Z', continuity_state: null, plateau_disclosure: null,
    },
  ],
}

const GOCHARA_LOSS_WINDOWS = {
  windows: [
    {
      id: 2, chart_id: TEST_CHART_ID, event_class: 'relationship_loss',
      temporal_shape: 'interval', window_start: '2026-06-01', window_end: '2026-11-30',
      peak_date: '2026-08-20', milestone_id: null, is_irreversibility_milestone: false,
      signed_intensity: -1.8, raw_intensity: 1.8, valence: 'loss', is_adverse: true,
      active_sentences: [], contributing_systems: [], suppression_state: {},
      peak_basis: 'peak_date', calibration_state: 'calibrated', source: 'live',
      computed_at: '2026-08-01T00:00:00Z', continuity_state: null, plateau_disclosure: null,
    },
  ],
}

const GOCHARA_EMPTY = { windows: [] }

// KP substrate calls (explain.ts fetchKpSchoolVoice)
const KP_FACTS_EMPTY = { rows: [] }
const KP_DASHAS_EMPTY = { systems: [] }

function stubFetchForExplain(
  pactResponse: Record<string, unknown>,
  gocharaResponse: Record<string, unknown>,
) {
  // F-73: gochara windows no longer come through fetch — see mockComputeGocharaForecast
  // above. (marsys://tool/L4/gochara_forecast_get was never a real registered capability;
  // this used to be papered over with a fetch-level mock the real code never hit.)
  mockComputeGocharaForecast.mockReset()
  mockComputeGocharaForecast.mockResolvedValue(gocharaResponse)

  vi.stubGlobal(
    'fetch',
    vi.fn(async (_url: string, opts: { body: string }) => {
      const body = JSON.parse(opts.body) as {
        uri?: string
        args?: Record<string, unknown>
      }
      const uri = body.uri ?? ''

      let payload: Record<string, unknown> = {}

      if (uri === 'marsys://tool/L-PACT/pact_query') {
        payload = pactResponse
      } else if (uri === 'marsys://tool/L1/chart_facts_query') {
        payload = KP_FACTS_EMPTY
      } else if (uri === 'marsys://tool/L1/get_dashas') {
        payload = KP_DASHAS_EMPTY
      } else if (uri === 'marsys://tool/L5/get_field_snapshot' ||
                 uri === 'marsys://tool/L3/get_field_snapshot') {
        payload = { field_snapshot_id: 'snap-001', field_content_hash: 'hash-001' }
      } else {
        // Unknown URI — return empty payload rather than throwing, so PACT chain completes
        payload = { rows: [] }
      }

      return {
        ok: true,
        json: async () => ({ ok: true, content: { content: payload, is_error: false } }),
        text: async () => '',
      }
    }),
  )
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

afterEach(() => {
  delete process.env['SM_GAMMA_C4_ENABLED']
  vi.resetModules()
})

// ── C4.2 A5 agreement — flag OFF ─────────────────────────────────────────────

describe('C4 A5 gochara_agreement — flag OFF', () => {
  it('flag absent → a5_gochara_agreement key NOT in response (§N.8 zero-footprint)', async () => {
    delete process.env['SM_GAMMA_C4_ENABLED']
    stubFetchForExplain(PACT_CHAIN_COMPLETE, GOCHARA_GAIN_WINDOWS)
    const { server, handlers } = makeCapturingServer()
    const { registerKalaExplainTool } = await import('../tools/kala_views/explain.js')
    registerKalaExplainTool(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage' })
    const obj = extractObject(result)
    expect('a5_gochara_agreement' in obj).toBe(false)
  })

  it('flag=false → a5_gochara_agreement key NOT in response', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'false'
    stubFetchForExplain(PACT_CHAIN_COMPLETE, GOCHARA_GAIN_WINDOWS)
    const { server, handlers } = makeCapturingServer()
    const { registerKalaExplainTool } = await import('../tools/kala_views/explain.js')
    registerKalaExplainTool(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage' })
    const obj = extractObject(result)
    expect('a5_gochara_agreement' in obj).toBe(false)
  })
})

// ── C4.2 A5 agreement — flag ON + concurs ────────────────────────────────────

describe('C4 A5 gochara_agreement — flag ON, windows concur', () => {
  it('chain_complete + gain windows → agreement=concurs, gochara_windows_active > 0', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    stubFetchForExplain(PACT_CHAIN_COMPLETE, GOCHARA_GAIN_WINDOWS)
    const { server, handlers } = makeCapturingServer()
    const { registerKalaExplainTool } = await import('../tools/kala_views/explain.js')
    registerKalaExplainTool(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage' })
    const obj = extractObject(result)
    expect('a5_gochara_agreement' in obj).toBe(true)
    const a5 = obj['a5_gochara_agreement'] as Record<string, unknown>
    expect(a5['agreement']).toBe('concurs')
    expect(a5['gochara_windows_active']).toBeGreaterThan(0)
    expect(typeof a5['note']).toBe('string')
    expect((a5['note'] as string).length).toBeLessThanOrEqual(120)
  })
})

// ── C4.2 A5 agreement — flag ON + dissents ───────────────────────────────────

describe('C4 A5 gochara_agreement — flag ON, windows dissent', () => {
  it('chain_complete + loss windows → agreement=dissents', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    stubFetchForExplain(PACT_CHAIN_COMPLETE, GOCHARA_LOSS_WINDOWS)
    const { server, handlers } = makeCapturingServer()
    const { registerKalaExplainTool } = await import('../tools/kala_views/explain.js')
    registerKalaExplainTool(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage' })
    const obj = extractObject(result)
    const a5 = obj['a5_gochara_agreement'] as Record<string, unknown>
    expect(a5['agreement']).toBe('dissents')
    expect(a5['gochara_windows_active']).toBeGreaterThan(0)
  })

  it('denied_at_confirmation + gain windows → agreement=dissents (gochara contradicts the denial)', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    stubFetchForExplain(PACT_DENIED, GOCHARA_GAIN_WINDOWS)
    const { server, handlers } = makeCapturingServer()
    const { registerKalaExplainTool } = await import('../tools/kala_views/explain.js')
    registerKalaExplainTool(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage' })
    const obj = extractObject(result)
    const a5 = obj['a5_gochara_agreement'] as Record<string, unknown>
    // PACT denied (chain_incomplete) but gochara has gain windows → dissent
    expect(a5['agreement']).toBe('dissents')
  })
})

// ── C4.2 A5 agreement — flag ON + no windows ─────────────────────────────────

describe('C4 A5 gochara_agreement — flag ON, no gochara windows', () => {
  it('no gochara windows → agreement=insufficient_data', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    stubFetchForExplain(PACT_CHAIN_COMPLETE, GOCHARA_EMPTY)
    const { server, handlers } = makeCapturingServer()
    const { registerKalaExplainTool } = await import('../tools/kala_views/explain.js')
    registerKalaExplainTool(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage' })
    const obj = extractObject(result)
    const a5 = obj['a5_gochara_agreement'] as Record<string, unknown>
    expect(a5['agreement']).toBe('insufficient_data')
    expect(a5['gochara_windows_active']).toBe(0)
  })
})

// ── C4.2 A5 agreement — structural shape ────────────────────────────────────

describe('C4 A5 gochara_agreement — structural shape invariants', () => {
  it('has required fields: agreement, gochara_windows_active, dominant_valence, note', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    stubFetchForExplain(PACT_CHAIN_COMPLETE, GOCHARA_GAIN_WINDOWS)
    const { server, handlers } = makeCapturingServer()
    const { registerKalaExplainTool } = await import('../tools/kala_views/explain.js')
    registerKalaExplainTool(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage' })
    const obj = extractObject(result)
    const a5 = obj['a5_gochara_agreement'] as Record<string, unknown>
    expect('agreement' in a5).toBe(true)
    expect('gochara_windows_active' in a5).toBe(true)
    expect('dominant_valence' in a5).toBe(true)
    expect('note' in a5).toBe(true)
    expect(['concurs', 'dissents', 'insufficient_data']).toContain(a5['agreement'])
    expect(typeof a5['gochara_windows_active']).toBe('number')
  })

  it('note is ≤120 chars (always)', async () => {
    process.env['SM_GAMMA_C4_ENABLED'] = 'true'
    stubFetchForExplain(PACT_CHAIN_COMPLETE, GOCHARA_LOSS_WINDOWS)
    const { server, handlers } = makeCapturingServer()
    const { registerKalaExplainTool } = await import('../tools/kala_views/explain.js')
    registerKalaExplainTool(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage' })
    const obj = extractObject(result)
    const a5 = obj['a5_gochara_agreement'] as Record<string, unknown>
    expect(typeof a5['note']).toBe('string')
    expect((a5['note'] as string).length).toBeLessThanOrEqual(120)
  })
})
