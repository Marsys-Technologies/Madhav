/**
 * b11_gate_f125.test.ts — F-125 regression: the B.11 orientation gate
 * (`fetchOrientationContext`, registry_bridge.ts) was module-private (no `export`), making
 * it structurally unreachable from `kala_upaya_get` (kala_views/upaya.ts) and the
 * interpretive `bodha_*` regAlias family (register_p1_aliases.ts) — every OTHER per_chart
 * domain tool registered directly inside registry_bridge.ts already carried
 * `orientation_context`/`orientation_ok`; these did not, and could not, regardless of
 * developer intent (F-125.spec_writer.json / .reviewer.json / .ratifier.json, all COMPLETE
 * at spec stage).
 *
 * This file exercises the REAL MCP seam — the actual `server.tool(...)` callback each tool
 * registers, not the underlying pure builder function in isolation — so a future edit that
 * silently re-severs the gate (e.g. reverting the export, or dropping the merge in either
 * call site) fails this test, not just a narrower unit check. Mirrors the
 * `registry_bridge_r5w3_judgment_and_portrait.test.ts` / `upaya.test.ts` harness
 * conventions already established in this package.
 *
 * Every assertion below FAILS on pre-fix `origin/main` (traced + independently re-verified
 * against current source before this fix landed): `fetchOrientationContext` had no `export`
 * keyword; `kala_views/upaya.ts` had zero occurrences of the string "orientation";
 * `register_p1_aliases.ts` had no `requiresOrientation` option and no
 * `fetchOrientationContext` import.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

// ── Shared MCP-seam capture harness (registry_bridge_r5w3 precedent) ──────────────────────

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
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/**
 * Stubs global `fetch` (the only I/O both `registry_bridge.ts#callRegistryCapability` and
 * `register_p1_aliases.ts#callRegistryCap` perform) keyed by the `uri` in the request body.
 *
 * `marsys://tool/L2/query_ucd` is served DOUBLE-WRAPPED (`{content: payload, is_error}`) —
 * `fetchOrientationContext`'s own `assessOrientationPayload` docstring names this as the
 * real shape `callRegistryCapability` returns for this specific capability (see
 * registry_bridge.ts's EL-36 note); every other URI here is served SINGLE-wrapped, matching
 * `parishodhana_b1_remedy_fields.test.ts`'s established convention for
 * `register_p1_aliases.ts#callRegistryCap` callers.
 */
function stubFetch(
  payloads: Record<string, unknown>,
  captured: Array<{ uri: string; args: Record<string, unknown> }>,
) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (_url: string, opts: { body: string }) => {
      const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
      captured.push(body)
      if (body.uri === 'marsys://tool/L2/query_ucd') {
        const payload = payloads[body.uri] ?? {
          chart_id: body.args['chart_id'],
          entity_profiles: [{ id: 'ep-1' }],
          convergence_domains: [{ id: 'cd-1' }],
          digest: { msr_signal_count: 12 },
        }
        return {
          ok: true,
          json: async () => ({ ok: true, content: { content: payload, is_error: false } }),
          text: async () => '',
        }
      }
      const payload = body.uri in payloads ? payloads[body.uri] : {}
      return {
        ok: true,
        json: async () => ({ ok: true, content: payload }),
        text: async () => '',
      }
    }),
  )
}

beforeEach(() => {
  vi.unstubAllGlobals()
  vi.resetModules()
})

// ── kala_upaya_get ──────────────────────────────────────────────────────────────────────

const mockCallPlatformPrimitive = vi.fn()
const mockCallPlatformWrites = vi.fn()
vi.mock('../client.js', async () => {
  const actual = await vi.importActual<typeof import('../client.js')>('../client.js')
  return {
    ...actual,
    callPlatformPrimitive: (...args: unknown[]) => mockCallPlatformPrimitive(...args),
    callPlatformWrites: (...args: unknown[]) => mockCallPlatformWrites(...args),
  }
})

const mockCallKalaRegistryCap = vi.fn()
vi.mock('../tools/kala_views/shared.js', async () => {
  const actual = await vi.importActual<typeof import('../tools/kala_views/shared.js')>(
    '../tools/kala_views/shared.js',
  )
  return { ...actual, callKalaRegistryCap: (...args: unknown[]) => mockCallKalaRegistryCap(...args) }
})

describe('kala_upaya_get — F-125 B.11 orientation gate', () => {
  beforeEach(() => {
    mockCallPlatformPrimitive.mockReset()
    mockCallPlatformWrites.mockReset()
    mockCallKalaRegistryCap.mockReset()
    // Same degradation pattern upaya.test.ts's "does NOT refuse an ordinary career/health
    // remedy request" case uses: pact_query/alternate-routing/remedy-sourcing all degrade
    // to honest_empty; buildKalaUpayaResult still returns a full (non-refusal) result.
    mockCallKalaRegistryCap.mockResolvedValue({ content: { error: 'no fixture in this test' }, is_error: true })
    mockCallPlatformPrimitive.mockRejectedValue(new Error('unreachable in unit test'))
  })

  it('response carries orientation_ok and orientation_context on an ordinary domain query — FAILS pre-fix (gate was unreachable)', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({}, captured)

    const { registerKalaUpayaGet } = await import('../tools/kala_views/upaya.js')
    registerKalaUpayaGet(server, PRINCIPAL)
    const handler = handlers.get('kala_upaya_get')!
    expect(handler).toBeDefined()

    const result = await handler({ chart_id: CHART_ID, domain: 'career' })
    expect(result.isError).toBeFalsy()
    const parsed = JSON.parse(result.content[0]!.text) as Record<string, unknown>

    expect(parsed).toHaveProperty('orientation_ok')
    expect(parsed).toHaveProperty('orientation_context')
    expect(parsed['orientation_ok']).toBe(true)

    // Non-vacuous: the gate must be a REAL fetch, not a hardcoded field. Confirms
    // fetchOrientationContext's marsys://tool/L2/query_ucd call actually fired.
    const ucdCall = captured.find((c) => c.uri === 'marsys://tool/L2/query_ucd')
    expect(ucdCall).toBeDefined()
    expect(ucdCall!.args['chart_id']).toBe(CHART_ID)

    // The tool's own diagnosis/interventions/coverage machinery is unaffected — additive only.
    expect(parsed).toHaveProperty('diagnosis')
    expect(parsed).toHaveProperty('interventions')
  })

  it('honestly reports orientation_ok=false (never drops the payload) when UCD orientation is empty', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch(
      { 'marsys://tool/L2/query_ucd': { chart_id: CHART_ID, digest: {}, msr_signal_count: 0 } },
      captured,
    )

    const { registerKalaUpayaGet } = await import('../tools/kala_views/upaya.js')
    registerKalaUpayaGet(server, PRINCIPAL)
    const handler = handlers.get('kala_upaya_get')!

    const result = await handler({ chart_id: CHART_ID, domain: 'health' })
    const parsed = JSON.parse(result.content[0]!.text) as Record<string, unknown>
    expect(parsed['orientation_ok']).toBe(false)
    expect(parsed['orientation_context']).toBeDefined()
  })

  // Gate G16 (ADJUDICATION-13, absolute) is that a mortality-excluded request makes NO
  // network call of any kind, before ANY await — upaya.test.ts's firing-proof already pins
  // this at the buildKalaUpayaResult layer. This test pins the SAME invariant one layer up,
  // at the actual registered MCP handler, to prove the F-125 fix does not quietly widen the
  // gate into a substrate call G16 forbids.
  it('a mortality-excluded request carries no orientation field and makes no query_ucd call', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({}, captured)

    const { registerKalaUpayaGet } = await import('../tools/kala_views/upaya.js')
    registerKalaUpayaGet(server, PRINCIPAL)
    const handler = handlers.get('kala_upaya_get')!

    const result = await handler({ chart_id: CHART_ID, question_frame: { domain: 'longevity' } })
    const parsed = JSON.parse(result.content[0]!.text) as Record<string, unknown>

    expect(parsed['excluded']).toBe(true)
    expect(parsed).not.toHaveProperty('orientation_ok')
    expect(parsed).not.toHaveProperty('orientation_context')
    expect(captured.find((c) => c.uri === 'marsys://tool/L2/query_ucd')).toBeUndefined()
    expect(mockCallKalaRegistryCap).not.toHaveBeenCalled()
  })
})

// ── bodha_* regAlias family (register_p1_aliases.ts) ───────────────────────────────────

describe('bodha_* regAlias family — F-125 B.11 orientation gate (requiresOrientation)', () => {
  it.each([
    ['bodha_remedies_get', 'marsys://tool/L2/query_remedies', { chart_id: CHART_ID, graha: 'Saturn' }],
    ['bodha_remedies_search', 'marsys://tool/L2/query_remedies', { chart_id: CHART_ID, keyword: 'shanti' }],
    ['bodha_domain_reading_get', 'marsys://tool/L2/query_domain_reading', { chart_id: CHART_ID, domain: 'career' }],
    ['bodha_quality_get', 'marsys://tool/L2/query_quality_scorecard', { chart_id: CHART_ID }],
  ])(
    '%s response carries orientation_ok and orientation_context — FAILS pre-fix (gate was unreachable)',
    async (toolName, capabilityUri, args) => {
      const { server, handlers } = makeCapturingServer()
      const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
      stubFetch({ [capabilityUri]: { rows: [] } }, captured)

      const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
      registerP1AliasTools(server, PRINCIPAL)
      const handler = handlers.get(toolName)!
      expect(handler).toBeDefined()

      const result = await handler(args)
      expect(result.isError).toBeFalsy()
      // dualOutput's own wire shape: content[0].text is the JSON of the (possibly
      // budget-trimmed) served object directly — no extra nesting layer.
      const envelope = JSON.parse(result.content[0]!.text) as Record<string, unknown>
      const inner = (envelope['content'] ?? envelope) as Record<string, unknown>

      expect(inner).toHaveProperty('orientation_ok')
      expect(inner).toHaveProperty('orientation_context')
      expect(inner['orientation_ok']).toBe(true)

      const ucdCall = captured.find((c) => c.uri === 'marsys://tool/L2/query_ucd')
      expect(ucdCall).toBeDefined()
      expect(ucdCall!.args['chart_id']).toBe(CHART_ID)

      const domainCall = captured.find((c) => c.uri === capabilityUri)
      expect(domainCall).toBeDefined()
    },
  )

  // Negative control: an RS-4-exempt regAlias tool (factual L1 lookup, diagnosis §4) must
  // NOT gain orientation fields — requiresOrientation is opt-in per spec §2c, not a blanket
  // change to every regAlias registration.
  it('ganita_medical_get (RS-4-exempt) carries no orientation field and makes no query_ucd call', async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({ 'marsys://tool/L1/get_medical_indications': { rows: [] } }, captured)

    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    registerP1AliasTools(server, PRINCIPAL)
    const handler = handlers.get('ganita_medical_get')!
    expect(handler).toBeDefined()

    const result = await handler({ chart_id: CHART_ID })
    expect(result.isError).toBeFalsy()
    const envelope = JSON.parse(result.content[0]!.text) as Record<string, unknown>
    const inner = (envelope['content'] ?? envelope) as Record<string, unknown>

    expect(inner).not.toHaveProperty('orientation_ok')
    expect(inner).not.toHaveProperty('orientation_context')
    expect(captured.find((c) => c.uri === 'marsys://tool/L2/query_ucd')).toBeUndefined()
  })
})
