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
