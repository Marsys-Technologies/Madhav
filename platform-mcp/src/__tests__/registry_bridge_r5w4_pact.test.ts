/**
 * registry_bridge_r5w4_pact.test.ts — MCP-tool-level regression pins for `pact_query`
 * (design §26/§28.3), R5 W4 lane 1 "PACT protocol end-to-end".
 *
 * Follows the registry_bridge_r5w3_judgment_and_portrait.test.ts precedent: mocks `fetch`
 * (registry_bridge.ts's only I/O) and captures the REAL callback `server.tool(...)` registers
 * via a fake `McpServer`, so this exercises the actual MCP seam (tool registration + Zod
 * schema + handler invocation + param forwarding — the MANDATORY standing requirement) without
 * needing a live DB. The capability's own chain-halting logic is unit-tested separately at
 * platform/src/lib/retrieval/registry/layers/__tests__/register_d10_pact.test.ts; this file
 * only pins that the MCP seam reaches it correctly and negotiates response_format faithfully.
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

describe('pact_query — MCP tool registration + seam reachability', () => {
  it('registers as a real server.tool callback and is reachable alongside judgment_query/graha_portrait', async () => {
    const { server, handlers } = makeCapturingServer()
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    expect(handlers.get('pact_query')).toBeDefined()
    expect(handlers.get('judgment_query')).toBeDefined()
    expect(handlers.get('graha_portrait')).toBeDefined()
  })

  it('forwards every declared param (chart_id, ayanamsha_id, domain, bhava, as_of_date, max_signals) to the capability call — the mandatory W2-lesson check', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L-PACT/pact_query': {
        chart_id: TEST_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha',
        about: { domain: 'marriage', bhava: 7, label: 'Marriage / Partnership', karakas: ['Venus'], operative_varga: 'D9' },
        pact_status: 'denied_at_promise',
        stages: [{ stage: 'PROMISE', status: 'denied', reason: 'contested' }],
        drill_pointers: [{ instrument: 'judgment_query', hint: 'x', pointer_type: 'check_bhanga', pact_stage: 'promise' }],
        judgment_flags: ['PACT chain halted at PROMISE'],
        fact_id_refs: [],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('pact_query')!

    await handler({
      chart_id: TEST_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', domain: 'marriage',
      as_of_date: '2026-07-08', max_signals: 12,
    })

    const call = captured.find(c => c.uri === 'marsys://tool/L-PACT/pact_query')
    expect(call).toBeDefined()
    expect(call!.args['chart_id']).toBe(TEST_CHART_ID)
    expect(call!.args['ayanamsha_id']).toBe('lahiri_chitrapaksha')
    expect(call!.args['domain']).toBe('marriage')
    expect(call!.args['as_of_date']).toBe('2026-07-08')
    expect(call!.args['max_signals']).toBe(12)
  })

  it('a bare `bhava` (no domain) is forwarded too', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L-PACT/pact_query': {
        chart_id: TEST_CHART_ID, about: { bhava: 3 },
        pact_status: 'denied_at_promise', stages: [], drill_pointers: [], judgment_flags: [], fact_id_refs: [],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('pact_query')!

    const result = await handler({ chart_id: TEST_CHART_ID, bhava: 3 })
    expect(result.isError).toBeFalsy()
    const call = captured.find(c => c.uri === 'marsys://tool/L-PACT/pact_query')!
    expect(call.args['bhava']).toBe(3)
  })

  it('rejects a call with neither `domain` nor `bhava`, without calling the capability', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({}, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('pact_query')!

    const result = await handler({ chart_id: TEST_CHART_ID })
    expect(result.isError).toBe(true)
    expect(captured.find(c => c.uri === 'marsys://tool/L-PACT/pact_query')).toBeUndefined()
  })

  it('response_format=v3 populates drill_pointers with the `pact_stage` field (design §28.3) alongside pointer_type, and a chain-honesty verdict', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L-PACT/pact_query': {
        chart_id: TEST_CHART_ID,
        about: { domain: 'marriage', bhava: 7, label: 'Marriage / Partnership', karakas: ['Venus'], operative_varga: 'D9' },
        pact_status: 'denied_at_confirmation',
        stages: [
          { stage: 'PROMISE', status: 'promised' },
          { stage: 'CONFIRMATION', status: 'denied' },
        ],
        fact_id_refs: ['f-1', 'f-2'],
        drill_pointers: [
          // SAMĀPTI A2: 'ganita_chart_facts_get' is the live MCP tool; production
          // (register_d10_pact.ts:300) emits it in place of the internal capability
          // name 'get_divisionals', which sc_pointer_validation.ts flags as an
          // unresolvable pointer (SC-18 class).
          { instrument: 'ganita_chart_facts_get', hint: 'full D9 placements.', pointer_type: 'confirm_in_varga', pact_stage: 'confirmation' },
        ],
        judgment_flags: ['PACT chain halted at CONFIRMATION'],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('pact_query')!

    const result = await handler({ chart_id: TEST_CHART_ID, domain: 'marriage', response_format: 'v3' })
    expect(result.isError).toBeFalsy()

    const envelope = result.structuredContent?.object as Record<string, unknown>
    const pointers = envelope['drill_pointers'] as Array<{ instrument: string; hint: string; pointer_type?: string; pact_stage?: string }>
    expect(pointers.length).toBe(1)
    expect(pointers[0]!.pact_stage).toBe('confirmation')
    expect(pointers[0]!.pointer_type).toBe('confirm_in_varga')

    const verdict = envelope['verdict'] as Record<string, unknown>
    expect(verdict['pact_status']).toBe('denied_at_confirmation')
    expect(verdict['stages_completed']).toBe(2)
  })
})
