/**
 * N-91 between-state disclosure — the L2 lineage flag survives the MCP edge and drives the served
 * reading_contract for judgment_query, pact_query and get_signals (bodha_signals_get).
 *
 * The capability sets `content.judgment_flags` (register_d9 / d10 / query_signals); the bridge copies
 * it into the v3 envelope's judgment_flags, and `envelope()` builds reading_contract from them. With
 * the flag the contract takes the "NOT yet anchored ... drill before treating it as confirmed" branch
 * with the cause; without it, the unchanged "grounded in N resolvable L1 fact reference(s)" sentence.
 * Same fake McpServer + stubbed fetch as registry_bridge_r5w3_judgment_and_portrait.test.ts.
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
  const server = { tool: (name: string, _d: string, _s: unknown, h: ToolHandler) => { handlers.set(name, h) } } as unknown as McpServer
  return { server, handlers }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const STALE_FLAG = { code: 'l2_receipts_predate_l1', detail: 'bo_laksana built against pre-rebuild ga_structural', severity: 'warning' }
const FAILED_FLAG = { code: 'l2_lineage_check_failed', detail: 'permission denied', severity: 'warning' }
const NOT_ANCHORED = 'Its reading is NOT yet anchored to resolvable L1 fact references in this envelope; drill via the pointers before treating it as confirmed.'

function stubFetch(payloads: Record<string, unknown>): void {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    const defaults: Record<string, unknown> = {
      'marsys://tool/L2/query_ucd': { chart_id: body.args['chart_id'], digest: {}, entity_profiles: [] },
      'marsys://tool/L1/get_chart_header': {
        chart_id_short: '482012f1', name: 'native', lagna_sign: 'Aries', lagna_deg: 1.2,
        moon_sign: 'Purva Bhadrapada', sun_sign: 'Capricorn', ayanamsha: 'lahiri_chitrapaksha', current_maha_antar: 'Saturn/Mercury',
      },
    }
    const payload = body.uri in payloads ? payloads[body.uri] : defaults[body.uri]
    if (payload === undefined) throw new Error(`stubFetch: no mocked response for uri "${body.uri}"`)
    return { ok: true, json: async () => ({ ok: true, content: { content: payload, is_error: false } }), text: async () => '' }
  }))
}

beforeEach(() => { vi.unstubAllGlobals() })

async function call(tool: string, args: Record<string, unknown>): Promise<Record<string, unknown>> {
  const { server, handlers } = makeCapturingServer()
  const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
  registerRegistryBridgeTools(server, PRINCIPAL)
  const out = await handlers.get(tool)!({ chart_id: CHART, response_format: 'v3', ...args })
  expect(out.isError).toBeFalsy()
  const sc = out.structuredContent as { object?: unknown } | undefined
  return (sc?.object ?? sc ?? JSON.parse(out.content[0]!.text)) as Record<string, unknown>
}

const FACT_IDS = Array.from({ length: 5 }, (_, i) => `f-${i}`)

const judgmentPayload = (flags: unknown[]) => ({
  chart_id: CHART, ayanamsha_id: 'lahiri_chitrapaksha',
  about: { domain: 'career', bhava: 10, label: 'Career / Vocation', karakas: ['Sun'], operative_varga: 'D10' },
  receipt: { bhava: true, bhavesha: true, karaka: true, from_moon: true, varga_confirmed: 'D10✓', yogas_checked: 1, bhanga_checked: false, timing_anchored: true },
  fact_id_refs: FACT_IDS,
  drill_pointers: [{ instrument: 'ganita_chart_facts_get', hint: 'full D10 placements.', pointer_type: 'confirm_in_varga' }],
  judgment_flags: flags,
})
const pactPayload = (flags: unknown[]) => ({
  chart_id: CHART,
  about: { domain: 'marriage', bhava: 7, label: 'Marriage / Partnership', karakas: ['Venus'], operative_varga: 'D9' },
  pact_status: 'denied_at_confirmation',
  stages: [{ stage: 'PROMISE', status: 'promised' }, { stage: 'CONFIRMATION', status: 'denied' }],
  fact_id_refs: FACT_IDS,
  drill_pointers: [{ instrument: 'ganita_chart_facts_get', hint: 'full D9 placements.', pointer_type: 'confirm_in_varga', pact_stage: 'confirmation' }],
  judgment_flags: flags,
})
const signalsPayload = (flags: unknown[]) => ({
  chart_id: CHART,
  ...(flags.length ? { judgment_flags: flags } : {}),
  signals: [{ signal_id: 's1', signal_type_id: 'yoga:x', signal_summary_text: 'x', constituent_facts_array: FACT_IDS }],
  returned_count: 1, truncated: false, total_matching_filters: 1,
  ranking_basis: { mode: 'salience_fallback' },
})

const CASES: Array<[string, string, (f: unknown[]) => unknown, Record<string, unknown>]> = [
  ['judgment_query', 'marsys://tool/L-JUDGMENT/judgment_query', judgmentPayload, { domain: 'career' }],
  ['pact_query', 'marsys://tool/L-PACT/pact_query', pactPayload, { domain: 'marriage' }],
  ['get_signals', 'marsys://tool/L2/query_signals', signalsPayload, {}],
]

describe.each(CASES)('%s — L2 lineage flag at the MCP edge', (tool, uri, payload, args) => {
  it('flag unset: reading_contract carries the unchanged "grounded in N resolvable" sentence, no lineage flag', async () => {
    stubFetch({ [uri]: payload([]) })
    const env = await call(tool, args)
    expect(String(env['reading_contract'])).toMatch(/grounded in 5 resolvable L1 fact reference\(s\)/)
    expect(String(env['reading_contract'])).not.toContain('NOT yet anchored')
    const flags = (env['judgment_flags'] as Array<{ code?: string } | string>) ?? []
    expect(flags.some(f => typeof f !== 'string' && f.code === 'l2_receipts_predate_l1')).toBe(false)
  })

  it('l2_receipts_predate_l1: flag in the envelope AND reading_contract takes the NOT-anchored branch with the cause', async () => {
    stubFetch({ [uri]: payload([STALE_FLAG]) })
    const env = await call(tool, args)
    const flags = env['judgment_flags'] as Array<{ code?: string } | string>
    expect(flags.some(f => typeof f !== 'string' && f.code === 'l2_receipts_predate_l1')).toBe(true)
    const rc = String(env['reading_contract'])
    expect(rc).toContain(NOT_ANCHORED)
    expect(rc).toMatch(/Cause: the L2 receipts behind these fact_ids predate the current L1 \(chart_facts\) rebuild/)
    expect(rc).not.toMatch(/grounded in \d+ resolvable/)
  })

  it('l2_lineage_check_failed (fail closed): NOT-anchored with the unchecked-lineage cause', async () => {
    stubFetch({ [uri]: payload([FAILED_FLAG]) })
    const env = await call(tool, args)
    const rc = String(env['reading_contract'])
    expect(rc).toContain(NOT_ANCHORED)
    expect(rc).toMatch(/lineage check could not be completed/)
    expect(rc).not.toMatch(/grounded in \d+ resolvable/)
  })
})
