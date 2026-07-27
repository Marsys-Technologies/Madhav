/**
 * samapana_trackb_exhaustive.test.ts — SAMĀPANA Track B (brief §2) regression + proof battery.
 * =================================================================================================
 * Covers all four brief items + the acceptance bullets, at the unit/integration layer available
 * in this worktree (no live DB/platform — `fetch`, registry_bridge.ts's only I/O, is mocked; the
 * conductor's Opus Verifier does the live post-deploy acceptance pass per the brief's §6 close).
 *
 *   1. 'exhaustive' is a new VERBOSITY_ZOD tier: same ceiling as 'detailed' (never shrunk), AND
 *      forces the mandatory B.11 orientation pre-fetch (fetchOrientationContext) to its full form.
 *      Back-compat: 'concise'/'detailed'/undefined are BYTE-FOR-BYTE unchanged (pinned below).
 *   2. reading_depth:'deep_dive' on assess_wealth (+ career/marriage/health) deterministically
 *      forces verbosity:'exhaustive' end-to-end — proven via a live-shaped mocked call that
 *      inspects the EXACT args sent to marsys://tool/L2/query_ucd.
 *   3. guardDeepDiveNotLossy refuses (throws) a deep_dive call routed through a lossy summary
 *      form — both the shared pure function AND bodha_chart_digest_get's live handler refusal.
 *   4. bodha_chart_digest_get's `mode` param — previously a DEAD no-op — is fixed and now
 *      genuinely reaches query_ucd as `response_format`; reading_depth:'deep_dive' forces 'full'
 *      even when the caller never touches `mode`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import {
  resolveVerbosityMaxKb,
  resolveOrientationFetchParams,
  resolveEffectiveVerbosity,
  guardDeepDiveNotLossy,
  DeepDiveLossyFormError,
} from '../tools/registry_bridge.js'

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

/** Mirrors registry_bridge_r5w1_signals_synthesis.test.ts's stubFetch pattern — wraps each
 *  `payloads[uri]` domain payload in the two real envelope layers a live call actually has. */
function stubFetch(payloads: Record<string, unknown>, captured: Array<{ uri: string; args: Record<string, unknown> }>) {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const body = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    captured.push(body)
    if (!(body.uri in payloads)) {
      // Unmocked URI: registry_bridge.ts's internal safeCall()s (fetchReadingSupplements)
      // catch this and degrade gracefully; fetchOrientationContext / the top-level assess_*
      // capability call are NOT wrapped in a safeCall, so every URI the assertions below care
      // about is explicitly stubbed.
      return { ok: false, status: 500, text: async () => 'no mocked response' }
    }
    return {
      ok: true,
      json: async () => ({ ok: true, content: { content: payloads[body.uri], is_error: false } }),
      text: async () => '',
    }
  }))
}

beforeEach(() => {
  vi.unstubAllGlobals()
})

// ── Item 1: 'exhaustive' tier — ceiling + back-compat ───────────────────────────────────────

describe("SAMAPANA Track B item 1 — 'exhaustive' verbosity tier", () => {
  it("resolveVerbosityMaxKb('exhaustive') keeps the SAME (unshrunk) ceiling as 'detailed'/undefined", () => {
    expect(resolveVerbosityMaxKb(40, 'exhaustive')).toBe(40)
    expect(resolveVerbosityMaxKb(40, 'exhaustive')).toBe(resolveVerbosityMaxKb(40, 'detailed'))
    expect(resolveVerbosityMaxKb(40, 'exhaustive')).toBe(resolveVerbosityMaxKb(40, undefined))
  })

  it("BACK-COMPAT PIN: 'detailed' and omitted verbosity are byte-for-byte unchanged by the 'exhaustive' addition", () => {
    // Same fixed expectations as the pre-existing W3 C-4 guard test (verbosity_hard_floor.test.ts)
    // — pinned again here so a future regression in this exact function is caught by BOTH files.
    expect(resolveVerbosityMaxKb(12, 'detailed')).toBe(12)
    expect(resolveVerbosityMaxKb(12, undefined)).toBe(12)
    expect(resolveVerbosityMaxKb(55, 'detailed')).toBe(55)
  })

  it("BACK-COMPAT PIN: 'concise' behavior is completely untouched by the 'exhaustive' addition", () => {
    expect(resolveVerbosityMaxKb(12, 'concise')).toBe(6)
    expect(resolveVerbosityMaxKb(55, 'concise')).toBe(28)
    expect(resolveVerbosityMaxKb(1, 'concise')).toBe(4)
  })

  it("resolveOrientationFetchParams: 'exhaustive' forces the B.11 orientation pre-fetch to its full form (top_k_signals:100, response_format:'full')", () => {
    expect(resolveOrientationFetchParams('exhaustive')).toEqual({ top_k_signals: 100, response_format: 'full' })
  })

  it("BACK-COMPAT PIN: resolveOrientationFetchParams for 'concise'/'detailed'/undefined is UNCHANGED — top_k_signals:10, response_format:'digest' (today's exact shape)", () => {
    const today = { top_k_signals: 10, response_format: 'digest' as const }
    expect(resolveOrientationFetchParams('concise')).toEqual(today)
    expect(resolveOrientationFetchParams('detailed')).toEqual(today)
    expect(resolveOrientationFetchParams(undefined)).toEqual(today)
  })
})

// ── Item 2: reading_depth:'deep_dive' contract ──────────────────────────────────────────────

describe("SAMAPANA Track B item 2 — reading_depth:'deep_dive' contract", () => {
  it("resolveEffectiveVerbosity: 'deep_dive' deterministically forces 'exhaustive', overriding ANY caller-supplied verbosity", () => {
    expect(resolveEffectiveVerbosity(undefined, 'deep_dive')).toBe('exhaustive')
    expect(resolveEffectiveVerbosity('concise', 'deep_dive')).toBe('exhaustive')
    expect(resolveEffectiveVerbosity('detailed', 'deep_dive')).toBe('exhaustive')
  })

  it("resolveEffectiveVerbosity: 'standard'/omitted reading_depth leaves verbosity untouched (back-compat)", () => {
    expect(resolveEffectiveVerbosity('concise', 'standard')).toBe('concise')
    expect(resolveEffectiveVerbosity('detailed', undefined)).toBe('detailed')
    expect(resolveEffectiveVerbosity(undefined, undefined)).toBeUndefined()
  })

  it("ACCEPTANCE: a reading_depth:'deep_dive' call to assess_wealth sends the mandatory orientation pre-fetch (query_ucd) with response_format:'full' and top_k_signals:100 — NOT the default top-10 digest", async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L2/query_ucd': { chart_id: TEST_CHART_ID, digest: {}, entity_profiles: [], top_signals: [] },
      'marsys://tool/L-DOMAIN/assess_wealth': { varga_analysis: {}, activating_dasha: {}, contradictions: {} },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('assess_wealth')!

    const result = await handler({ chart_id: TEST_CHART_ID, reading_depth: 'deep_dive' })
    expect(result.isError).toBeFalsy()

    const ucdCall = captured.find(c => c.uri === 'marsys://tool/L2/query_ucd')
    expect(ucdCall).toBeDefined()
    expect(ucdCall!.args['response_format']).toBe('full')
    expect(ucdCall!.args['top_k_signals']).toBe(100)
  })

  it("BACK-COMPAT PIN: assess_wealth WITHOUT reading_depth (or reading_depth:'standard') still sends today's exact orientation pre-fetch shape — response_format:'digest', top_k_signals:10", async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({
      'marsys://tool/L2/query_ucd': { chart_id: TEST_CHART_ID, digest: {}, entity_profiles: [], top_signals: [] },
      'marsys://tool/L-DOMAIN/assess_wealth': { varga_analysis: {}, activating_dasha: {}, contradictions: {} },
    }, captured)

    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('assess_wealth')!

    await handler({ chart_id: TEST_CHART_ID })
    let ucdCall = captured.find(c => c.uri === 'marsys://tool/L2/query_ucd')
    expect(ucdCall!.args['response_format']).toBe('digest')
    expect(ucdCall!.args['top_k_signals']).toBe(10)

    captured.length = 0
    await handler({ chart_id: TEST_CHART_ID, reading_depth: 'standard' })
    ucdCall = captured.find(c => c.uri === 'marsys://tool/L2/query_ucd')
    expect(ucdCall!.args['response_format']).toBe('digest')
    expect(ucdCall!.args['top_k_signals']).toBe(10)
  })

  it("assess_career/assess_marriage/assess_health all wire reading_depth:'deep_dive' the same way (uniform contract, not an assess_wealth-only special case)", async () => {
    for (const [toolName, uri] of [
      ['assess_career', 'marsys://tool/L-DOMAIN/assess_career'],
      ['assess_marriage', 'marsys://tool/L-DOMAIN/assess_marriage'],
      ['assess_health', 'marsys://tool/L-DOMAIN/assess_health'],
    ] as const) {
      const { server, handlers } = makeCapturingServer()
      const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
      stubFetch({
        'marsys://tool/L2/query_ucd': { chart_id: TEST_CHART_ID, digest: {}, entity_profiles: [], top_signals: [] },
        [uri]: { varga_analysis: {}, activating_dasha: {}, contradictions: {} },
      }, captured)

      const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
      registerRegistryBridgeTools(server, PRINCIPAL)
      const handler = handlers.get(toolName)!

      const result = await handler({ chart_id: TEST_CHART_ID, reading_depth: 'deep_dive' })
      expect(result.isError, `${toolName} unexpectedly errored`).toBeFalsy()

      const ucdCall = captured.find(c => c.uri === 'marsys://tool/L2/query_ucd')
      expect(ucdCall, `${toolName}: no orientation pre-fetch captured`).toBeDefined()
      expect(ucdCall!.args['response_format'], `${toolName}`).toBe('full')
      expect(ucdCall!.args['top_k_signals'], `${toolName}`).toBe(100)
    }
  })
})

// ── Item 3: hard-guard against lossy summary forms under a deep dive ───────────────────────

describe('SAMAPANA Track B item 3 — deep-dive cannot be routed through a lossy summary form', () => {
  it('guardDeepDiveNotLossy: no-op (pass-through) when reading_depth is not deep_dive', () => {
    expect(() => guardDeepDiveNotLossy(undefined, 'response_format', 'summary', ['summary', 'digest'])).not.toThrow()
    expect(() => guardDeepDiveNotLossy('standard', 'response_format', 'summary', ['summary', 'digest'])).not.toThrow()
  })

  it('guardDeepDiveNotLossy: no-op when the lossy form param is simply omitted under deep_dive (the normal case — deep_dive defaults it to full itself)', () => {
    expect(() => guardDeepDiveNotLossy('deep_dive', 'response_format', undefined, ['summary', 'digest'])).not.toThrow()
  })

  it("guardDeepDiveNotLossy: no-op when deep_dive is combined with the FULL form explicitly (not a contradiction)", () => {
    expect(() => guardDeepDiveNotLossy('deep_dive', 'response_format', 'full', ['summary', 'digest'])).not.toThrow()
  })

  it('THE GUARD: throws DeepDiveLossyFormError when deep_dive is explicitly combined with a named lossy form', () => {
    expect(() => guardDeepDiveNotLossy('deep_dive', 'response_format', 'summary', ['summary', 'digest']))
      .toThrow(DeepDiveLossyFormError)
    expect(() => guardDeepDiveNotLossy('deep_dive', 'response_format', 'digest', ['summary', 'digest']))
      .toThrow(DeepDiveLossyFormError)
  })

  it('ACCEPTANCE (live handler refusal, not just the pure function): get_chart_orientation refuses reading_depth:deep_dive + response_format:summary with an explicit error, not a silent pick', async () => {
    const { server, handlers } = makeCapturingServer()
    stubFetch({}, [])
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    registerRegistryBridgeTools(server, PRINCIPAL)
    const handler = handlers.get('get_chart_orientation')!

    const result = await handler({ chart_id: TEST_CHART_ID, reading_depth: 'deep_dive', response_format: 'summary' })
    expect(result.isError).toBeTruthy()
    const text = JSON.stringify(result)
    expect(text).toContain('deep_dive')
    expect(text).toContain("cannot be combined with response_format:'summary'")
  })

  it("ACCEPTANCE (live handler refusal): bodha_chart_digest_get refuses reading_depth:deep_dive + mode:summary", async () => {
    const { server, handlers } = makeCapturingServer()
    stubFetch({}, [])
    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    registerP1AliasTools(server, PRINCIPAL)
    const handler = handlers.get('bodha_chart_digest_get')!

    const result = await handler({ chart_id: TEST_CHART_ID, reading_depth: 'deep_dive', mode: 'summary' })
    expect(result.isError).toBeTruthy()
    const text = JSON.stringify(result)
    expect(text).toContain("cannot be combined with mode:'summary'")
  })
})

// ── Item 4: bodha_chart_digest_get's dead `mode` param + the deep-dive contract-side forcing ──

describe("SAMAPANA Track B item 4 — bodha_chart_digest_get's mode param + footgun fix", () => {
  it("REGRESSION FIX: mode:'full' now genuinely reaches query_ucd as response_format:'full' (previously a dead no-op — always served 'summary' regardless of `mode`)", async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({ 'marsys://tool/L2/query_ucd': { chart_id: TEST_CHART_ID, digest: {}, top_signals: [] } }, captured)

    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    registerP1AliasTools(server, PRINCIPAL)
    const handler = handlers.get('bodha_chart_digest_get')!

    await handler({ chart_id: TEST_CHART_ID, mode: 'full' })
    const call = captured.find(c => c.uri === 'marsys://tool/L2/query_ucd')
    expect(call!.args['response_format']).toBe('full')
    // the raw `mode` key must NOT leak through unmapped (that was the shape of the dead-param bug)
    expect(call!.args['mode']).toBeUndefined()
  })

  it("BACK-COMPAT PIN: mode omitted still defaults to response_format:'summary' (documented footgun, unchanged default)", async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({ 'marsys://tool/L2/query_ucd': { chart_id: TEST_CHART_ID, digest: {}, top_signals: [] } }, captured)

    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    registerP1AliasTools(server, PRINCIPAL)
    const handler = handlers.get('bodha_chart_digest_get')!

    await handler({ chart_id: TEST_CHART_ID })
    const call = captured.find(c => c.uri === 'marsys://tool/L2/query_ucd')
    expect(call!.args['response_format']).toBe('summary')
  })

  it("ACCEPTANCE (item 4b, contract-side fix): reading_depth:'deep_dive' forces response_format:'full' + top_k_signals:100 even when the caller never touches `mode`", async () => {
    const { server, handlers } = makeCapturingServer()
    const captured: Array<{ uri: string; args: Record<string, unknown> }> = []
    stubFetch({ 'marsys://tool/L2/query_ucd': { chart_id: TEST_CHART_ID, digest: {}, top_signals: [] } }, captured)

    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    registerP1AliasTools(server, PRINCIPAL)
    const handler = handlers.get('bodha_chart_digest_get')!

    const result = await handler({ chart_id: TEST_CHART_ID, reading_depth: 'deep_dive' })
    expect(result.isError).toBeFalsy()
    const call = captured.find(c => c.uri === 'marsys://tool/L2/query_ucd')
    expect(call!.args['response_format']).toBe('full')
    expect(call!.args['top_k_signals']).toBe(100)
  })
})
