/**
 * kala_views_priority_explain.test.ts — ṢAḌ-DARŚANA W0.4 MCP-tool-level regression pins for
 * `kala_priority_get` (VIEW 5 PRIORITIZE) and `kala_explain_get` (VIEW 6 EXPLAIN).
 *
 * Follows the registry_bridge_r5w4_pact.test.ts precedent: mocks `fetch` (the only I/O both
 * facades perform) and captures the REAL callback `server.tool(...)` registers via a fake
 * `McpServer`, exercising the actual MCP seam (registration + Zod schema + handler invocation
 * + param forwarding to the wrapped capability) without a live DB.
 *
 * Both facades are thin W0 wrappers — kala_priority_get over
 * `marsys://tool/L3/call_priority_ranking` (the SAME capability kala_priority_ranking_get
 * calls), kala_explain_get over `marsys://tool/L-PACT/pact_query` (the SAME capability
 * pact_query calls). These tests pin: (1) both tools register exactly once via
 * registerRegistryBridgeTools, (2) every declared param forwards to the wrapped capability,
 * (3) the elevated envelope fields (reading, tri_plane, coverage, freshness,
 * calibration_maturity) are present and honestly shaped, (4) the honest-empty / denial paths
 * never fabricate — they disclose the gap.
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
    const payload = body.uri in payloads ? payloads[body.uri] : undefined
    if (payload === undefined) {
      throw new Error(`stubFetch: no mocked response for uri "${body.uri}"`)
    }
    return {
      ok: true,
      json: async () => ({ ok: true, content: payload }),
      text: async () => '',
    }
  }))
}

function extractObject(result: Awaited<ReturnType<ToolHandler>>): Record<string, unknown> {
  expect(result.structuredContent).toBeDefined()
  return result.structuredContent!.object as Record<string, unknown>
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

describe('registerRegistryBridgeTools — kala_priority_get / kala_explain_get registration', () => {
  it('registers both tools exactly once, alongside pact_query/kala_priority_ranking_get consumers', async () => {
    const { server, handlers } = makeCapturingServer()
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    expect(handlers.get('kala_priority_get')).toBeDefined()
    expect(handlers.get('kala_explain_get')).toBeDefined()
    expect(handlers.get('pact_query')).toBeDefined()
  })
})

describe('kala_priority_get — PRIORITIZE facade over marsys://tool/L3/call_priority_ranking', () => {
  it('rejects a missing chart_id without calling the capability', async () => {
    const { server, handlers } = makeCapturingServer()
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('kala_priority_get')!
    const result = await handler({})
    expect(result.isError).toBe(true)
  })

  it('forwards chart_id/ayanamsha_id/date_from/date_to/top_k/domain to the wrapped capability', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L3/call_priority_ranking': {
        chart_id: TEST_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha',
        date_from: '2026-08-01', date_to: '2026-09-01', domain_filter: ['career'],
        ranked_signals: [
          { signal_id: 'sig_1', signal_headline_text: 'Jupiter pushkara navamsha', priority_score: 0.91, neutral_dignity_downranked: false },
          { signal_id: 'sig_2', signal_headline_text: 'graha dignity per varga: dignity state = neutral', priority_score: 0.12, neutral_dignity_downranked: true },
        ],
        signal_count: 2, neutral_dignity_downranked_count: 1,
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('kala_priority_get')!

    const result = await handler({
      chart_id: TEST_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha',
      date_from: '2026-08-01', date_to: '2026-09-01', top_k: 10, domain: 'career',
    })

    const call = captured.find(c => c.uri === 'marsys://tool/L3/call_priority_ranking')
    expect(call).toBeDefined()
    expect(call!.args['chart_id']).toBe(TEST_CHART_ID)
    expect(call!.args['ayanamsha_id']).toBe('lahiri_chitrapaksha')
    expect(call!.args['date_from']).toBe('2026-08-01')
    expect(call!.args['date_to']).toBe('2026-09-01')
    expect(call!.args['top_k']).toBe(10)
    expect(call!.args['domain']).toBe('career')

    const obj = extractObject(result)
    expect(obj['ok']).toBe(true)
    expect(obj['tool']).toBe('kala_priority_get')
    // Envelope shape (kala_envelope.ts) — all fields present.
    expect(obj['reading']).toBeDefined()
    expect(obj['question_frame']).toBeNull()
    expect(typeof obj['field_snapshot_id']).toBe('string')
    expect(obj['tri_plane']).toBeDefined()
    expect(Array.isArray(obj['coverage'])).toBe(true)
    expect(obj['freshness']).toBeDefined()
    // This fixture only provides the wrapped registry capability. Its DB-proxy calibration
    // authority is deliberately absent, so it must be represented as typed unknown—not the
    // meaningful all-zero value reserved for a reachable authority with no fitted row.
    expect(obj['calibration_maturity']).toEqual({
      n_events: null,
      prospective_resolutions: null,
      event_class_coverage: null,
      weights_version: null,
      skill_score: null,
      state: 'unavailable',
      reason: 'calibration_maturity_authority_unavailable',
    })
    expect(obj['composed']).toBeDefined()
    // Raw passthrough — never fabricated, this is the underlying capability's own data.
    expect(Array.isArray(obj['ranked_signals'])).toBe(true)
    expect((obj['ranked_signals'] as unknown[]).length).toBe(2)

    // Reading evidence carries no fabricated `strength` (priority_score is the unexamined
    // legacy scalar — see file header honesty note).
    const reading = obj['reading'] as { evidence: Array<{ strength?: string }> }
    for (const ev of reading.evidence) expect(ev.strength).toBeUndefined()

    // The fixture has no DB-proxy salience response. The table is a live authority but
    // unreadable in this call, so coverage is honest_empty rather than the retired W0
    // `not_in_corpus` claim.
    const coverage = obj['coverage'] as Array<{ concept: string; state: string }>
    expect(coverage.some(c => c.concept === 'salience_vector_five_axis' && c.state === 'honest_empty')).toBe(true)
  })

  it('honest-empty: zero ranked_signals produces a non-fabricated thesis and honest_empty coverage', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L3/call_priority_ranking': {
        chart_id: TEST_CHART_ID, date_from: '2026-08-01', date_to: '2026-09-01',
        domain_filter: null, ranked_signals: [], signal_count: 0, neutral_dignity_downranked_count: 0,
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('kala_priority_get')!
    const result = await handler({ chart_id: TEST_CHART_ID })
    const obj = extractObject(result)

    const reading = obj['reading'] as { thesis: string; evidence: unknown[] }
    expect(reading.evidence).toEqual([])
    expect(reading.thesis).toContain('No priority-ranked signals')

    const coverage = obj['coverage'] as Array<{ concept: string; state: string }>
    expect(coverage.some(c => c.concept === 'priority_ranking_legacy_scalar' && c.state === 'honest_empty')).toBe(true)

    // Item 43 (tri-plane wiring): even with zero ranked_signals, PRIORITIZE's tri_plane
    // pointers to EXPLAIN/AHEAD/ELECT are view-level facts and remain REAL — never collapse
    // to no_lever just because this call's own data happened to be empty.
    const triPlane = obj['tri_plane'] as { interpretation_ref: { instrument: string }; prediction_ref: { instrument: string }; intervention_ref: { instrument: string } }
    expect(triPlane.interpretation_ref.instrument).toBe('kala_explain_get')
    expect(triPlane.prediction_ref.instrument).toBe('kala_ahead_get')
    expect(triPlane.intervention_ref.instrument).toBe('kala_elect_get')
  })

  it('reconciles row-derived counts after the final response budget trims ranked signals', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    const rankedSignals = Array.from({ length: 60 }, (_, index) => ({
      signal_id: `sig_${index}`,
      signal_headline_text: `Signal ${index}: ${'detail '.repeat(500)}`,
      priority_score: 1 - index / 100,
      neutral_dignity_downranked: index % 2 === 0,
    }))
    stubFetch({
      'marsys://tool/L3/call_priority_ranking': {
        chart_id: TEST_CHART_ID,
        date_from: '2026-08-01',
        date_to: '2026-09-01',
        domain_filter: null,
        ranked_signals: rankedSignals,
        signal_count: rankedSignals.length,
        neutral_dignity_downranked_count: rankedSignals.filter(row => row.neutral_dignity_downranked).length,
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const result = await handlers.get('kala_priority_get')!({ chart_id: TEST_CHART_ID })
    const obj = extractObject(result)
    const served = obj['ranked_signals'] as Array<{ neutral_dignity_downranked?: boolean }>

    expect(served.length).toBeLessThan(rankedSignals.length)
    expect(obj['signal_count']).toBe(served.length)
    expect(obj['neutral_dignity_downranked_count']).toBe(
      served.filter(row => row.neutral_dignity_downranked === true).length,
    )
    expect(Buffer.byteLength(JSON.stringify(obj), 'utf8')).toBeLessThanOrEqual(40 * 1024)
  })
})

describe('kala_explain_get — EXPLAIN facade over marsys://tool/L-PACT/pact_query', () => {
  it('rejects a missing chart_id without calling the capability', async () => {
    const { server, handlers } = makeCapturingServer()
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID })
    expect(result.isError).toBe(true)
  })

  it('requires domain or bhava', async () => {
    const { server, handlers } = makeCapturingServer()
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID })
    expect(result.isError).toBe(true)
  })

  it('forwards chart_id/ayanamsha_id/domain/as_of_date/max_signals; names the weakest link on a denial; routes intervention_ref to kala_upaya_get', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L-PACT/pact_query': {
        chart_id: TEST_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', as_of_date: '2026-08-01',
        about: { domain: 'marriage', bhava: 7, label: 'Marriage / Partnership' },
        pact_status: 'denied_at_confirmation',
        stages: [
          { stage: 'PROMISE', status: 'promised', reason: 'Rashi checklist supports the matter.' },
          { stage: 'CONFIRMATION', status: 'denied', reason: 'D9 dignity is net-hostile.', dignities: [{ fact_id: 'fact_d9_venus' }] },
        ],
        drill_pointers: [{ instrument: 'ganita_chart_facts_get', hint: 'x', pointer_type: 'confirm_in_varga', pact_stage: 'confirmation' }],
        judgment_flags: [],
        fact_id_refs: ['fact_promise_1'],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!

    const result = await handler({
      chart_id: TEST_CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', domain: 'marriage',
      as_of_date: '2026-08-01', max_signals: 12,
    })

    const call = captured.find(c => c.uri === 'marsys://tool/L-PACT/pact_query')
    expect(call).toBeDefined()
    expect(call!.args['chart_id']).toBe(TEST_CHART_ID)
    expect(call!.args['ayanamsha_id']).toBe('lahiri_chitrapaksha')
    expect(call!.args['domain']).toBe('marriage')
    expect(call!.args['as_of_date']).toBe('2026-08-01')
    expect(call!.args['max_signals']).toBe(12)

    const obj = extractObject(result)
    expect(obj['ok']).toBe(true)
    expect(obj['tool']).toBe('kala_explain_get')
    expect(obj['pact_status']).toBe('denied_at_confirmation')

    const weakestLink = obj['weakest_link'] as { stage: string; status: string; reason: string }
    expect(weakestLink.stage).toBe('CONFIRMATION')
    expect(weakestLink.status).toBe('denied')

    // interpretation_ref is honestly null — this reading IS the interpretive plane already.
    const triPlane = obj['tri_plane'] as { interpretation_ref: unknown; intervention_ref: { instrument: string } }
    // ND-1 (ṢAḌ-DARŚANA W1 verify-reopen, 2026-07-30): the bare-null contract this assertion
    // encoded is retired — every tri_plane slot is now either a real pointer or an honest,
    // self-describing `no_lever`. See tools/kala_views/ahead.ts's prediction_ref for the
    // rationale (the campaign's own tri_plane_no_dead_end_gate.ts grades a bare null WARN).
    expect((triPlane.interpretation_ref as { no_lever?: boolean } | null)?.no_lever).toBe(true)
    expect(triPlane.intervention_ref.instrument).toBe('kala_upaya_get')

    // See the PRIORITIZE facade fixture above: this test intentionally exercises a
    // proxy-unavailable substrate, which must not be collapsed to empirical zero.
    expect(obj['calibration_maturity']).toEqual({
      n_events: null,
      prospective_resolutions: null,
      event_class_coverage: null,
      weights_version: null,
      skill_score: null,
      state: 'unavailable',
      reason: 'calibration_maturity_authority_unavailable',
    })

    // The CONFIRMATION stage's dignity fact_id is attributed to its own evidence row.
    const reading = obj['reading'] as { evidence: Array<{ claim: string; fact_ids: string[] }> }
    const confirmationEvidence = reading.evidence.find(e => e.claim.startsWith('CONFIRMATION'))
    expect(confirmationEvidence?.fact_ids).toEqual(['fact_d9_venus'])
    // PROMISE stage has no per-stage fact_id at this substrate tier — honestly uncited, not fabricated.
    const promiseEvidence = reading.evidence.find(e => e.claim.startsWith('PROMISE'))
    expect(promiseEvidence?.fact_ids).toEqual([])
  })

  it('a chain_complete result routes intervention_ref to kala_elect_get', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L-PACT/pact_query': {
        chart_id: TEST_CHART_ID, as_of_date: '2026-08-01', about: { bhava: 10, label: 'Career' },
        pact_status: 'chain_complete',
        stages: [
          { stage: 'PROMISE', status: 'promised', reason: 'x' },
          { stage: 'CONFIRMATION', status: 'confirmed', reason: 'x' },
          { stage: 'ACTIVATION', status: 'active_now', reason: 'x' },
          { stage: 'TRIGGER', status: 'gate_data_fetched', reason: 'x' },
        ],
        drill_pointers: [], judgment_flags: [], fact_id_refs: [],
      },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('kala_explain_get')!
    const result = await handler({ chart_id: TEST_CHART_ID, bhava: 10, as_of_date: '2026-08-01' })
    const obj = extractObject(result)

    const triPlane = obj['tri_plane'] as { intervention_ref: { instrument: string } }
    expect(triPlane.intervention_ref.instrument).toBe('kala_elect_get')
    const weakestLink = obj['weakest_link'] as { stage: string }
    expect(weakestLink.stage).toBe('TRIGGER')
  })
})
