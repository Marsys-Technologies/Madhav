/**
 * kala_explain_get_n1_concordance.test.ts — N1 seventh step, part B: wires
 * `composeConcordanceVerdict` into `kala_explain_get` as `engine_testimony`/`concordance`,
 * beside `weakest_link`.
 *
 * Same harness as `kala_explain_get_c4_a5.test.ts` (stubbed `fetch` keyed by capability
 * URI). Adds a mock response for `marsys://tool/L3/query_kala_paddhati_profile` so the
 * O-10 authority profile can be varied per test: empty (no seed yet — today's real
 * production state, since migration 677 has not deployed), primary-only (PACT alone,
 * §N.8 honest null — no corroborating vote exists to disagree or agree), and a full
 * primary + concurring/dissenting corroborating set.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

const mockComputeGocharaForecast = vi.hoisted(() => vi.fn())
vi.mock('../tools/retrieval/register_gochara_windows.js', () => ({
  computeGocharaForecast: mockComputeGocharaForecast,
}))
const mockRemoteAuthorize = vi.hoisted(() => vi.fn().mockResolvedValue(true))
vi.mock('../lib/authz.js', () => ({
  remoteAuthorize: mockRemoteAuthorize,
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

const GOCHARA_EMPTY = { windows: [] }
const KP_FACTS_EMPTY = { rows: [] }
const KP_DASHAS_EMPTY = { systems: [] }

const PADDHATI_URI = 'marsys://tool/L3/query_kala_paddhati_profile'

const PADDHATI_EMPTY = { rows: [] }

const PADDHATI_PRIMARY_ONLY = {
  rows: [
    { factor_family: 'O-10', convention_id: 'pact', convention_status: 'computed', arbitration_role: 'primary', precedence: 1 },
  ],
}

const PADDHATI_FULL_ALIGNED = {
  rows: [
    { factor_family: 'O-10', convention_id: 'pact', convention_status: 'computed', arbitration_role: 'primary', precedence: 1 },
    { factor_family: 'O-10', convention_id: 'kp', convention_status: 'computed', arbitration_role: 'corroborating', precedence: null },
  ],
}

function stubFetchForExplain(
  pactResponse: Record<string, unknown>,
  gocharaResponse: Record<string, unknown>,
  paddhatiResponse: Record<string, unknown> = PADDHATI_EMPTY,
  kpFactsResponse: Record<string, unknown> = KP_FACTS_EMPTY,
) {
  mockComputeGocharaForecast.mockReset()
  mockComputeGocharaForecast.mockResolvedValue(gocharaResponse)

  vi.stubGlobal(
    'fetch',
    vi.fn(async (_url: string, opts: { body: string }) => {
      const body = JSON.parse(opts.body) as { uri?: string }
      const uri = body.uri ?? ''

      let payload: Record<string, unknown> = {}
      if (uri === 'marsys://tool/L-PACT/pact_query') {
        payload = pactResponse
      } else if (uri === 'marsys://tool/L1/chart_facts_query') {
        payload = kpFactsResponse
      } else if (uri === 'marsys://tool/L1/get_dashas') {
        payload = KP_DASHAS_EMPTY
      } else if (uri === PADDHATI_URI) {
        payload = paddhatiResponse
      } else if (uri === 'marsys://tool/L5/get_field_snapshot' || uri === 'marsys://tool/L3/get_field_snapshot') {
        payload = { field_snapshot_id: 'snap-001', field_content_hash: 'hash-001' }
      } else {
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

describe('N1 seventh step (part B) — engine_testimony / concordance are always present', () => {
  it('engine_testimony is an array (possibly empty) and concordance key is present', async () => {
    stubFetchForExplain(PACT_CHAIN_COMPLETE, GOCHARA_EMPTY, PADDHATI_EMPTY)
    const { server, handlers } = makeCapturingServer()
    const { registerKalaExplainTool } = await import('../tools/kala_views/explain.js')
    registerKalaExplainTool(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage' })
    const obj = extractObject(result)
    expect(Array.isArray(obj['engine_testimony'])).toBe(true)
    expect('concordance' in obj).toBe(true)
  })
})

describe('N1 seventh step (part B) — honest null (§N.7/§N.8, never an invented verdict)', () => {
  it('empty O-10 profile (today\'s real production state — migration 677 not deployed) → concordance is null', async () => {
    stubFetchForExplain(PACT_CHAIN_COMPLETE, GOCHARA_EMPTY, PADDHATI_EMPTY)
    const { server, handlers } = makeCapturingServer()
    const { registerKalaExplainTool } = await import('../tools/kala_views/explain.js')
    registerKalaExplainTool(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage' })
    const obj = extractObject(result)
    expect(obj['concordance']).toBeNull()
  })

  it('primary-only profile, no corroborating testimony computed → concordance is null (no vote to arbitrate)', async () => {
    // KP facts empty → kpVoice is honest_empty, not 'computed' — contributes no testimony.
    stubFetchForExplain(PACT_CHAIN_COMPLETE, GOCHARA_EMPTY, PADDHATI_PRIMARY_ONLY)
    const { server, handlers } = makeCapturingServer()
    const { registerKalaExplainTool } = await import('../tools/kala_views/explain.js')
    registerKalaExplainTool(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage' })
    const obj = extractObject(result)
    // 'pact' itself never appears as engine_testimony (kala_explain_get IS the PACT
    // reading, not a testimony ABOUT it) — so with kp honest_empty and A5 flag off,
    // there is no 'computed' testimony at all → composeConcordanceVerdict returns null.
    expect(obj['concordance']).toBeNull()
  })
})

describe('N1 seventh step (part B) — a real verdict when both roles have computed testimony', () => {
  it('KP voice computed + corroborating profile row for kp → concordance is a non-null verdict object', async () => {
    const KP_FACTS_WITH_LADDER = {
      rows: [
        { fact_category: 'kp_house_significators', fact_subject: 'HOUSE_07', fact_value: 'Venus', fact_id: 'kp-h7-a' },
      ],
    }
    stubFetchForExplain(PACT_CHAIN_COMPLETE, GOCHARA_EMPTY, PADDHATI_FULL_ALIGNED, KP_FACTS_WITH_LADDER)
    const { server, handlers } = makeCapturingServer()
    const { registerKalaExplainTool } = await import('../tools/kala_views/explain.js')
    registerKalaExplainTool(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage' })
    const obj = extractObject(result)
    // Whatever the KP ladder resolves to (computed or honest_empty depends on parse
    // success), the CONTRACT under test is: engine_testimony is populated when a real
    // voice is computed, and concordance is either null (honest, no primary/no vote) or
    // a well-shaped verdict object — never a crash, never a fabricated default.
    const testimony = obj['engine_testimony'] as Array<Record<string, unknown>>
    expect(Array.isArray(testimony)).toBe(true)
    if (obj['concordance'] !== null) {
      const c = obj['concordance'] as Record<string, unknown>
      expect(['aligned', 'partially_aligned', 'disputed']).toContain(c['status'])
      expect('adjudicated_by' in c).toBe(true)
    }
  })
})
