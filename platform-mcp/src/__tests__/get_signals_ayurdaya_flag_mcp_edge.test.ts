/**
 * get_signals — the Āyurdāya disclosure flag survives the MCP edge (SS N-62 Q10, display-side).
 *
 * The MCP bridge (registry_bridge.ts) reads ONLY the capability's `content` — a flag set solely on the
 * handler result's top-level `judgment_flags` is dropped. query_signals therefore also carries the
 * closed-vocabulary flag at `content.judgment_flags`, and the v3 envelope merges it into its own
 * top-level `judgment_flags`. This drives the real get_signals callback through a faked platform
 * route (same {ok, content: <handler return>} shape the real route emits).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

type ToolHandler = (args: Record<string, unknown>) => Promise<{
  structuredContent?: unknown
  content: Array<{ type: 'text'; text: string }>
  isError?: boolean
}>

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const CAVEAT = 'Unreduced base figure from the classical pinda/amsa/nisarga computation; no reductions (harana) are applied; not a prediction of lifespan.'
const FLAG = { code: 'ayurdaya_unreduced_base_figures', detail: CAVEAT, severity: 'info' }

function makeCapturingServer(): { server: McpServer; handlers: Map<string, ToolHandler> } {
  const handlers = new Map<string, ToolHandler>()
  const server = { tool: (name: string, _d: string, _s: unknown, h: ToolHandler) => { handlers.set(name, h) } } as unknown as McpServer
  return { server, handlers }
}

/** query_signals handler return as the real platform route serialises it (content AND result-level flags). */
const QUERY_SIGNALS_RETURN = {
  content: {
    chart_id: CHART,
    ayurdaya_figure_disclosure: { figure_kind: 'unreduced_base', reductions_applied: false, caveat: CAVEAT },
    judgment_flags: [FLAG],
    signals: [{
      signal_id: 's1', signal_type_id: 'ayurdaya:total_years', signal_summary_text: 'category=ayurdaya | key=total_years | value_num=98.75',
      figure_kind: 'unreduced_base', reductions_applied: false, constituent_facts_array: ['f1'],
    }],
    returned_count: 1, truncated: false, total_matching_filters: 1,
    ranking_basis: { mode: 'salience_fallback' },
  },
  is_error: false,
  judgment_flags: [FLAG],
}

function stubFetch(): void {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    const handlerReturn =
      body.uri === 'marsys://tool/L2/query_signals' ? QUERY_SIGNALS_RETURN
      : body.uri === 'marsys://tool/L1/get_chart_header' ? { content: { chart_id_short: '482012f1', name: 'native', lagna_sign: 'Aries', lagna_deg: 1.2, moon_sign: 'Purva Bhadrapada', sun_sign: 'Capricorn', ayanamsha: 'lahiri_chitrapaksha', current_maha_antar: 'Saturn/Mercury' }, is_error: false }
      : { content: { chart_id: body.args['chart_id'], digest: {}, entity_profiles: [] }, is_error: false }
    return { ok: true, json: async () => ({ ok: true, content: handlerReturn }), text: async () => '' }
  }))
}

beforeEach(() => { vi.unstubAllGlobals() })

async function callGetSignals(args: Record<string, unknown>): Promise<Record<string, unknown>> {
  const { server, handlers } = makeCapturingServer()
  stubFetch()
  const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
  registerRegistryBridgeTools(server, PRINCIPAL)
  const out = await handlers.get('get_signals')!({ chart_id: CHART, ...args })
  // budget-capped instruments serve the payload in structuredContent (text is a pointer string)
  const sc = out.structuredContent as { object?: unknown } | undefined
  return (sc?.object ?? sc ?? JSON.parse(out.content[0]!.text)) as Record<string, unknown>
}

/** Every `judgment_flags` array anywhere in the served payload. */
function allFlagArrays(v: unknown, found: unknown[][] = []): unknown[][] {
  if (Array.isArray(v)) { for (const x of v) allFlagArrays(x, found); return found }
  if (v && typeof v === 'object') {
    for (const [k, x] of Object.entries(v as Record<string, unknown>)) {
      if (k === 'judgment_flags' && Array.isArray(x)) found.push(x)
      allFlagArrays(x, found)
    }
  }
  return found
}

describe('get_signals — ayurdaya flag + disclosure survive the MCP edge', () => {
  it('legacy format: content.judgment_flags and the nested disclosure reach the caller', async () => {
    const served = await callGetSignals({})
    const flat = JSON.stringify(served)
    expect(flat).toContain('ayurdaya_unreduced_base_figures')
    expect(flat).toContain(CAVEAT)
    const flagArrays = allFlagArrays(served)
    expect(flagArrays.some(a => a.some(f => (f as Record<string, unknown>)['code'] === 'ayurdaya_unreduced_base_figures'))).toBe(true)
  })

  it('v3 format: the envelope top-level judgment_flags carries the flag too', async () => {
    const served = await callGetSignals({ response_format: 'v3' })
    const topLevel = served['judgment_flags'] as Array<Record<string, unknown>> | undefined
    expect(Array.isArray(topLevel)).toBe(true)
    expect(topLevel!.some(f => f['code'] === 'ayurdaya_unreduced_base_figures')).toBe(true)
    // the per-row annotation and the stored number also travel unchanged
    const flat = JSON.stringify(served)
    expect(flat).toContain('"figure_kind":"unreduced_base"')
    expect(flat).toContain('value_num=98.75')
  })
})
