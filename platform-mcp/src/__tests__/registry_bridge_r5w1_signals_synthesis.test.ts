/**
 * registry_bridge_r5w1_signals_synthesis.test.ts — regression pins for the two
 * opportunistic bug fixes made in the R5 W1 signals_query/synthesis_query lane
 * (see R5_RUN_LEDGER W1 lane report + JL-009(c)):
 *
 *   (b) get_signals forwarded its `limit` param as `{ limit: ... }` to
 *       query_signals.ts, whose handler only reads `top_k`/`offset` — the facet
 *       was silently ignored. Fixed to forward `top_k: resolvedLimit`.
 *   (c) get_chart_orientation read fields directly off callRegistryCapability()'s
 *       return value without unwrapping the `{content, is_error}` capability-handler
 *       shape — every field read was silently `undefined`. Fixed to unwrap `.content`.
 *
 * No live platform/DB required — `fetch` (registry_bridge.ts's only I/O) is mocked
 * to return a controlled `{ ok: true, content: {...} }` shape per capability `uri`,
 * matching the /api/retrieval/capability contract.
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
const TEST_CHART_ID = '00000000-0000-0000-0000-000000000001'

/**
 * Captures every outgoing capability call { uri, args } and answers per-uri from `payloads`.
 * `payloads[uri]` is the CAPABILITY HANDLER's own domain payload (e.g. query_ucd's digest
 * object) — this helper wraps it in the two real envelope layers a live call actually has:
 *   1. the capability handler's own `{content, is_error}` return shape (what
 *      callRegistryCapability() returns raw — see its docstring in registry_bridge.ts);
 *   2. the /api/retrieval/capability HTTP route's `{ok, content, error}` JSON envelope
 *      (what callRegistryCapability() unwraps via `data.content` before returning).
 * Getting this wrapping right is exactly the point of the (c) `.content`-unwrap regression
 * this file pins — a wrong wrap here would produce a false pass.
 */
function stubFetch(payloads: Record<string, unknown>, captured: Array<{ uri: string; args: Record<string, unknown> }>) {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    captured.push(body)
    if (!(body.uri in payloads)) {
      throw new Error(`stubFetch: no mocked response for uri "${body.uri}"`)
    }
    const capabilityHandlerReturn = { content: payloads[body.uri], is_error: false }
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

// ── (b) get_signals: limit -> top_k forwarding fix ──────────────────────────────

describe('get_signals — limit forwarding regression (JL-009(c)(1))', () => {
  it('forwards the caller-supplied `limit` as `top_k` to query_signals.ts, not as `limit`', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L2/query_ucd': { chart_id: TEST_CHART_ID, digest: {}, entity_profiles: [] },
      'marsys://tool/L2/query_signals': { signals: [], returned_count: 0, truncated: false },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('get_signals')
    expect(handler).toBeDefined()

    await handler!({ chart_id: TEST_CHART_ID, limit: 37 })

    const signalsCall = captured.find(c => c.uri === 'marsys://tool/L2/query_signals')
    expect(signalsCall).toBeDefined()
    // Regression pin: the caller's `limit: 37` must arrive as `top_k: 37` — the
    // handler this call reaches (query_signals.ts) never reads a bare `limit` key,
    // so before the fix this value was silently dropped and the default (50) used.
    expect(signalsCall!.args['top_k']).toBe(37)
  })

  it('a cursor value is translated to a numeric `offset`, not silently dropped', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L2/query_ucd': { chart_id: TEST_CHART_ID, digest: {}, entity_profiles: [] },
      'marsys://tool/L2/query_signals': { signals: [], returned_count: 0, truncated: false },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('get_signals')!

    await handler({ chart_id: TEST_CHART_ID, limit: 10, cursor: '50' })

    const signalsCall = captured.find(c => c.uri === 'marsys://tool/L2/query_signals')!
    expect(signalsCall.args['offset']).toBe(50)
  })
})

// ── (c) get_chart_orientation: `.content` unwrap fix ─────────────────────────────

describe('get_chart_orientation — .content unwrap regression (JL-009(c)(2))', () => {
  it('returns non-undefined digest fields (chart_id, digest, entity_profiles) from the wrapped capability response', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    const fakeDigest = {
      chart_id: TEST_CHART_ID,
      ayanamsha_id: 'lahiri_chitrapaksha',
      digest: { msr_signal_count: 573, contradiction_count: 2, weakest_graha: 'Saturn', top_priority_class: 'yoga' },
      entity_profiles: [{ entity_type: 'graha', entity: 'SATURN', aggregate_score: 1.2, peak_score: 0.9, signal_count: 2, dominant_domains: [], dominant_valence: null, signal_type_classes: [], top_signal_ids: [] }],
      top_signals: [],
      convergence_domains: [],
      provenance: { tables: [], ranking_note: '', aggregation_note: '' },
    }
    stubFetch({ 'marsys://tool/L2/query_ucd': fakeDigest }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('get_chart_orientation')!

    const result = await handler({ chart_id: TEST_CHART_ID, response_format: 'digest' })
    expect(result.isError).toBeFalsy()

    // The registry capability handler's raw return shape is { content, is_error } —
    // callRegistryCapability() already unwraps ONE level (`data.content` from the HTTP
    // envelope) but the capability's OWN handler return (`{content, is_error}`) is a
    // second layer this call site must also unwrap. Pre-fix, every field below read
    // `undefined` because that second unwrap never happened. The legacy envelope
    // nests the tool's own payload under `.content` (buildRetrievalEnvelope) — that
    // layer is unrelated to the bug and expected.
    const envelope = result.structuredContent?.object as Record<string, unknown>
    expect(envelope).toBeDefined()
    const digestPayload = envelope['content'] as Record<string, unknown>
    expect(digestPayload).toBeDefined()
    expect(digestPayload['chart_id']).toBe(TEST_CHART_ID)
    expect(digestPayload['digest']).toBeDefined()
    expect((digestPayload['digest'] as Record<string, unknown>)['msr_signal_count']).toBe(573)
    expect(digestPayload['entity_profiles']).toBeDefined()
    expect((digestPayload['entity_profiles'] as unknown[]).length).toBe(1)
  })
})
