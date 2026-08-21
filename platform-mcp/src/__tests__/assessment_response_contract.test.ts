/**
 * A09 / F56 / F111 — assess_* composition must normalize the registry ToolResult
 * wrapper before building the stable Sāra response.  This is deliberately an MCP-seam
 * test: the platform route adds { ok, content }, while the capability itself returns
 * { content, is_error }.  The latter is the wrapper that previously stranded every
 * assessment field one level below the composition builder.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
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
    tool: (name: string, _description: string, _schema: unknown, handler: ToolHandler) => {
      handlers.set(name, handler)
    },
  } as unknown as McpServer
  return { server, handlers }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function stubFetch(assessmentPayload: Record<string, unknown>) {
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const { uri, args } = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    const payload = uri.startsWith('marsys://tool/L-DOMAIN/assess_')
      ? assessmentPayload
      : { chart_id: args.chart_id, digest: {}, entity_profiles: [] }
    return {
      ok: true,
      json: async () => ({ ok: true, content: { content: payload, is_error: false } }),
      text: async () => '',
    }
  }))
}

beforeEach(() => vi.unstubAllGlobals())

describe('assess_* Sāra response contract', () => {
  // F-14/F-124 (reconciled, PARISESA-V4 REBASE — see 00_ARCHITECTURE/briefs/parisesa/state/
  // phase0/rebase_f14_f124.json): before this fix, assess_health/assess_marriage never called
  // attachDomainCompleteness/attachDomainReading at all, so `reading` was always genuinely
  // absent and this suite's `domain_slice_not_configured` kernel flag was the only disclosure
  // available. Now both handlers DO call the attach functions, so `reading` is populated (an
  // honest per-family digest — `domain_block_not_served` entries when, as in this stub, no
  // varga_analysis exists) and `domain_completeness_empty_reason` carries the "no precompiled
  // slice" disclosure directly in `grounding` — a strictly more informative signal than the
  // old flag, which only said "reading is missing" with no per-family detail. The
  // `domain_slice_not_configured` flag correctly stops firing once `reading` is genuinely
  // non-empty; these two cases now assert the new (superseding) disclosure path instead.
  it.each([
    ['assess_health', 'health'],
    ['assess_marriage', 'relationship'],
  ] as const)(
    '%s discloses that its %s dossier slice is not configured instead of implying career/wealth parity',
    async (tool, domain) => {
      stubFetch({
        chart_id: CHART_ID,
        verdict: { clauses: [{ text: 'A deterministic partial-domain verdict.', fact_ids: [], grounded: false }] },
      })
      const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
      const { server, handlers } = makeCapturingServer()
      registerRegistryBridgeTools(server, PRINCIPAL)

      const result = await handlers.get(tool)!({ chart_id: CHART_ID })
      const object = result.structuredContent!.object as Record<string, unknown>
      const grounding = object.grounding as Record<string, unknown>
      expect(String(grounding.domain_completeness_empty_reason)).toMatch(
        new RegExp(`No precompiled ${domain} concept-slice bundle exists yet`),
      )
      expect(grounding.domain_completeness).toBeUndefined()
      // The disclosure moved from a bare kernel flag to a structured, per-family digest —
      // still honest, no longer a total blackout.
      expect(Array.isArray(grounding.reading)).toBe(true)
      expect((grounding.reading as unknown[]).length).toBeGreaterThan(0)

      // GA-5 review finding on #1382: domain_completeness_empty_reason previously landed
      // ONLY in `grounding`, which response_budget.ts's assembleSaraContent drops ALL-OR-
      // NOTHING under budget pressure -- and the sibling domain_slice_not_configured kernel
      // flag (asserted above in the prior test) is gated on !hasAttachedReading, permanently
      // unreachable once `reading` is always attached (as this test's own fixture proves it
      // is). A low-budget caller could receive NEITHER disclosure. The same text must also
      // land in kernel.flags.
      //
      // F-177 CORRECTION: the original wording here read "...which response_budget.ts never
      // drops." That was not true, and this assertion did not test it -- assembleSaraContent
      // trimmed kernel.flags from the TAIL, and the mirror is pushed last, so on a real chart
      // it was the FIRST entry deleted (live-confirmed on 482012f1). This case only ever
      // passed because its stub kernel is far under the 2048-byte ceiling, so no trim runs.
      // The dense case is now covered end-to-end below and in
      // f177_kernel_flag_disclosure_protection.test.ts.
      const kernel = object.kernel as Record<string, unknown>
      expect(kernel.flags).toContain(grounding.domain_completeness_empty_reason)
    },
  )

  // F-177 (end-to-end, through the real registry_bridge handler -- not the lib in isolation):
  // the same disclosure must survive when the kernel is genuinely dense enough to trigger
  // assembleSaraContent's >=2048-byte trim, which is the condition every real built chart
  // meets and the stub above does not. This is the case that fails on unmodified `main`.
  it.each([
    ['assess_health', 'health'],
    ['assess_marriage', 'relationship'],
  ] as const)(
    '%s keeps its %s empty_reason disclosure in kernel.flags even when the kernel is trimmed',
    async (tool, domain) => {
      // A verdict long enough to push the assembled kernel past the 2048-byte ceiling on its
      // own, mirroring the real multi-sentence assess_* verdicts observed in production.
      const longClause = 'A deterministic partial-domain verdict sentence carrying grounded prose. '.repeat(30)
      stubFetch({
        chart_id: CHART_ID,
        verdict: { clauses: [{ text: longClause, fact_ids: [], grounded: false }] },
      })
      const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
      const { server, handlers } = makeCapturingServer()
      registerRegistryBridgeTools(server, PRINCIPAL)

      const result = await handlers.get(tool)!({ chart_id: CHART_ID })
      const object = result.structuredContent!.object as Record<string, unknown>
      const kernel = object.kernel as { flags: unknown[]; pointers: unknown[] }
      const report = object.composition_report as { kernel_bytes: number }

      // Baseline guard: the trim genuinely ran (otherwise this test proves nothing).
      expect(kernel.pointers.length).toBeLessThan(3)

      const disclosure = kernel.flags.find(
        f => typeof f === 'string' && new RegExp(`No precompiled ${domain} concept-slice bundle exists yet`).test(f),
      )
      expect(disclosure).toBeDefined()
      expect(report.kernel_bytes).toBeGreaterThan(0)
    },
  )

  it.each([
    ['assess_health', 'health', []],
    ['assess_marriage', 'relationship', []],
    ['assess_health', 'health', null],
    ['assess_marriage', 'relationship', null],
  ] as const)(
    '%s treats %p reading as absent for the disclosure guard',
    async (tool, domain, reading) => {
      stubFetch({
        chart_id: CHART_ID,
        reading,
        verdict: { clauses: [{ text: 'A deterministic empty-reading verdict.', fact_ids: [], grounded: false }] },
      })
      const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
      const { server, handlers } = makeCapturingServer()
      registerRegistryBridgeTools(server, PRINCIPAL)

      const result = await handlers.get(tool)!({ chart_id: CHART_ID })
      const kernel = (result.structuredContent!.object as Record<string, unknown>).kernel as Record<string, unknown>
      expect(kernel.flags).toContain(
        `domain_slice_not_configured: no precomputed ${domain} dossier slice is attached; this assessment is not a complete domain reading.`,
      )
    },
  )

  it.each(['assess_marriage', 'assess_health'] as const)(
    '%s reaches the same normalized shared composer',
    async (tool) => {
      stubFetch({
        chart_id: CHART_ID,
        verdict: { clauses: [{ text: 'A deterministic shared-composer verdict.', fact_ids: [], grounded: false }] },
      })
      const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
      const { server, handlers } = makeCapturingServer()
      registerRegistryBridgeTools(server, PRINCIPAL)

      const result = await handlers.get(tool)!({ chart_id: CHART_ID })
      const kernel = (result.structuredContent!.object as Record<string, unknown>).kernel as Record<string, unknown>
      expect(kernel.verdict).toBe('A deterministic shared-composer verdict.')
      expect(kernel.verdict_status).toBe('available')
    },
  )

  it('emits only served MCP drill instruments for the composed assessment seams', async () => {
    stubFetch({
      chart_id: CHART_ID,
      verdict: { clauses: [{ text: 'A deterministic shared-composer verdict.', fact_ids: [], grounded: false }] },
    })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    const { server, handlers } = makeCapturingServer()
    registerRegistryBridgeTools(server, PRINCIPAL)

    const result = await handlers.get('assess_wealth')!({ chart_id: CHART_ID })
    const kernel = (result.structuredContent!.object as Record<string, unknown>).kernel as Record<string, unknown>
    expect(kernel.pointers).toEqual([
      { instrument: 'bodha_domain_reading_get', hint: 'marsys://tool/L2/query_domain_reading' },
      { instrument: 'kala_windows_get', hint: 'marsys://tool/L3/query_temporal_activation' },
      { instrument: 'bodha_graph_traverse_get', hint: 'mode:"contradictions" — marsys://tool/L2/traverse_chart_graph' },
    ])
  })

  it('preserves verdict, promise, and evidence from a normalized wrapped capability payload', async () => {
    const verdictText = 'Wealth indications are mixed and require the cited evidence.'
    const promise = {
      projection: 'supported', promise_verdict: 'chain_complete', shared_fact_ids: ['fact-1'], stance: 'consistent',
    }
    stubFetch({
      chart_id: CHART_ID,
      verdict: {
        clauses: [{ text: verdictText, fact_ids: ['fact-1'], grounded: true }],
        sentence_count: 1,
        fact_ids_cited: ['fact-1'],
        template: 'deterministic_v1',
        note: 'deterministic fixture',
      },
      promise,
      evidence: { fact_ids: ['fact-1'], citations: ['BPHŚ 1.1'] },
      activating_dasha: { activations: [{ signal_id: 'sig-1' }] },
    })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    const { server, handlers } = makeCapturingServer()
    registerRegistryBridgeTools(server, PRINCIPAL)

    const result = await handlers.get('assess_wealth')!({ chart_id: CHART_ID })
    expect(result.isError).toBeFalsy()
    const response = result.structuredContent!.object as Record<string, unknown>
    const kernel = response.kernel as Record<string, unknown>
    const evidence = response.evidence as Record<string, unknown>

    expect(kernel.verdict).toBe(verdictText)
    expect(kernel.promise).toEqual(promise)
    expect(evidence.fact_ids).toEqual(['fact-1'])
    expect(evidence.citations).toEqual(['BPHŚ 1.1'])
    expect(evidence.activating_dasha).toEqual({ activations: [{ signal_id: 'sig-1' }] })
  })

  it('reports a typed unknown with a causal reason when an upstream payload genuinely omits composition data', async () => {
    stubFetch({ chart_id: CHART_ID })
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    const { server, handlers } = makeCapturingServer()
    registerRegistryBridgeTools(server, PRINCIPAL)

    const result = await handlers.get('assess_wealth')!({ chart_id: CHART_ID })
    expect(result.isError).toBeFalsy()
    const response = result.structuredContent!.object as Record<string, unknown>
    const kernel = response.kernel as Record<string, unknown>

    expect(kernel.verdict_status).toBe('unknown')
    expect(kernel.unknown_reason).toBe('upstream_assessment_composition_absent')
    expect(kernel.verdict).toBe('')
    expect(kernel.promise).toBeNull()
    expect(response.evidence).toBeUndefined()
  })
})
