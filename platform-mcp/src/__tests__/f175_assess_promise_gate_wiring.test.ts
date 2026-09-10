/**
 * F-175 — assess_* PACT promise gate: MCP-seam wiring test (PARIŚEṢA-V4)
 *
 * `assess_promise_gate.test.ts` proves the pure logic. THIS file proves the wiring: that all
 * four `assess_*` tools actually consult `marsys://tool/L-PACT/pact_query` and actually apply
 * the result — the half of F-110 that was documented as done and had never been written
 * (`grep -rn interpretPactJoin` returned only the helper and its own test until 2026-08-21;
 * `promise_spine.ts`'s header asserted a `registry_bridge.ts` wiring that did not exist).
 *
 * MUTATION TEST: delete the `fetchAssessPromiseGate(...)` line from any one handler's
 * `Promise.all` in registry_bridge.ts and that tool's case here fails — the served kernel
 * reverts to the pre-fix false-clean certification, verbatim.
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
    tool: (name: string, _d: string, _s: unknown, handler: ToolHandler) => { handlers.set(name, handler) },
  } as unknown as McpServer
  return { server, handlers }
}

const PRINCIPAL: Principal = { user_uid: 'test-user', key_id: 'test-key', role: 'super_admin' }
const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

/** The live defect string, verbatim from assess_marriage(482012f1) on 2026-08-21. */
const CERTIFICATION_TEXT =
  'No contradictions are tagged to this domain specifically (3 exist chart-wide) — ' +
  'an honest domain-scoped absence, not a silent omission.'

const ASSESSMENT_PAYLOAD = {
  chart_id: CHART_ID,
  contradictions: { status: 'no_contradictions_in_domain', chart_wide_contradiction_count: 3 },
  verdict: {
    clauses: [
      { text: 'Domain assessment draws on 10 composite-ranked signal(s).', fact_ids: [], grounded: false, clause_id: 'overview' },
      { text: CERTIFICATION_TEXT, fact_ids: [], grounded: false, clause_id: 'contradictions' },
    ],
    sentence_count: 2,
    fact_ids_cited: [],
    template: 'deterministic_v1',
    note: '',
  },
}

/** Records every capability URI the handler calls, and answers the PACT one as instructed. */
function stubFetch(pactContent: Record<string, unknown> | null) {
  const seen: Array<{ uri: string; args: Record<string, unknown> }> = []
  vi.stubGlobal('fetch', vi.fn(async (_url: string, opts: { body: string }) => {
    const { uri, args } = JSON.parse(opts.body) as { uri: string; args: Record<string, unknown> }
    seen.push({ uri, args })
    if (uri === 'marsys://tool/L-PACT/pact_query') {
      if (pactContent === null) return { ok: false, status: 503, text: async () => 'sidecar down', json: async () => ({ ok: false }) }
      return { ok: true, json: async () => ({ ok: true, content: pactContent }), text: async () => '' }
    }
    const payload = uri.startsWith('marsys://tool/L-DOMAIN/assess_')
      ? ASSESSMENT_PAYLOAD
      : { chart_id: args.chart_id, digest: {}, entity_profiles: [] }
    return { ok: true, json: async () => ({ ok: true, content: { content: payload, is_error: false } }), text: async () => '' }
  }))
  return seen
}

const DENIAL = {
  pact_status: 'denied_at_promise',
  stages: [{ stage: 'PROMISE', status: 'denied', composite_score: -3.5 }],
  fact_id_refs: ['e8e5300adea7bc58', '61ff5df8420a8b45'],
}

async function callTool(tool: string) {
  const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
  const { server, handlers } = makeCapturingServer()
  registerRegistryBridgeTools(server, PRINCIPAL)
  const result = await handlers.get(tool)!({ chart_id: CHART_ID })
  return result.structuredContent!.object as Record<string, unknown>
}

beforeEach(() => vi.unstubAllGlobals())

const TOOLS = [
  ['assess_marriage', 'relationship'],
  ['assess_career', 'career'],
  ['assess_health', 'health'],
  ['assess_wealth', 'wealth'],
] as const

describe('F-175 — all four assess_* tools consult the PACT chain', () => {
  it.each(TOOLS)('%s calls pact_query for domain=%s exactly once', async (tool, domain) => {
    const seen = stubFetch(DENIAL)
    await callTool(tool)
    const pactCalls = seen.filter(c => c.uri === 'marsys://tool/L-PACT/pact_query')
    // §5.3 latency contract: pact_query runs judgment_query's full checklist. Exactly one.
    expect(pactCalls).toHaveLength(1)
    expect(pactCalls[0]!.args).toMatchObject({ chart_id: CHART_ID, domain })
  })

  it.each(TOOLS)('%s no longer serves the false-clean certification when the chain denies', async (tool) => {
    stubFetch(DENIAL)
    const object = await callTool(tool)
    const kernel = object.kernel as Record<string, unknown>
    const verdict = String(kernel.verdict)

    // The L2 finding survives verbatim (disclosure, not suppression — §N.5).
    expect(verdict).toContain('No contradictions are tagged to this domain specifically (3 exist chart-wide)')
    // …but it can no longer be read as a domain all-clear.
    expect(verdict).toContain('NOT A CLEAN BILL OF HEALTH')
    expect(verdict).toContain('PROMISE CHAIN CONTRADICTS THIS DOMAIN')
    expect(verdict).toContain('denied_at_promise')
  })

  it.each(TOOLS)('%s populates kernel.promise (null on every response before F-175)', async (tool) => {
    stubFetch(DENIAL)
    const kernel = (await callTool(tool)).kernel as Record<string, unknown>
    expect(kernel.promise).toMatchObject({ stance: 'contradicts', projection: 'contradicted' })
  })

  it.each(TOOLS)('%s raises the budget-protected kernel flag', async (tool) => {
    stubFetch(DENIAL)
    const kernel = (await callTool(tool)).kernel as Record<string, unknown>
    const codes = (kernel.flags as Array<string | { code: string }>)
      .map(f => (typeof f === 'string' ? f : f.code))
    expect(codes).toContain('promise_chain_contradicts_domain')
  })

  it('the structured grounding carries the gate and the annotated L2 surface', async () => {
    stubFetch(DENIAL)
    const grounding = (await callTool('assess_marriage')).grounding as Record<string, unknown>
    expect(grounding.promise_gate).toMatchObject({
      state: 'checked', domain: 'relationship', pact_status: 'denied_at_promise',
      contradicts_domain_assessment: true,
    })
    const contra = grounding.contradictions as Record<string, unknown>
    expect(contra.status).toBe('no_contradictions_in_domain') // L2 truth, untouched (§N.5)
    expect(contra.not_a_domain_all_clear).toBe(true)          // …but not readable as clean
  })
})

describe('F-175 — no over-correction, and no silent failure', () => {
  it('a clean chain leaves the certification prose byte-identical and raises no flag', async () => {
    stubFetch({ pact_status: 'chain_complete', stages: [], fact_id_refs: [] })
    const kernel = (await callTool('assess_career')).kernel as Record<string, unknown>
    const verdict = String(kernel.verdict)
    expect(verdict).toBe(`Domain assessment draws on 10 composite-ranked signal(s). ${CERTIFICATION_TEXT}`)
    const codes = (kernel.flags as Array<string | { code: string }>)
      .map(f => (typeof f === 'string' ? f : f.code))
    expect(codes).not.toContain('promise_chain_contradicts_domain')
    expect(codes).not.toContain('promise_chain_unchecked')
    expect(kernel.promise).toMatchObject({ stance: 'consistent' })
  })

  it('an unreachable chain still serves the bundle, disclosed as unchecked — never as clean', async () => {
    stubFetch(null) // L-PACT returns 503
    const object = await callTool('assess_marriage')
    const kernel = object.kernel as Record<string, unknown>
    // The assessment is NOT lost because the gate failed.
    expect(kernel.verdict_status).toBe('available')
    expect(String(kernel.verdict)).toContain(CERTIFICATION_TEXT)
    // But the caller can tell "not checked" from "checked and clear" (F-110 A7 / §N.8).
    const codes = (kernel.flags as Array<string | { code: string }>)
      .map(f => (typeof f === 'string' ? f : f.code))
    expect(codes).toContain('promise_chain_unchecked')
    expect(kernel.promise).toBeNull()
    expect((object.grounding as Record<string, unknown>).promise_gate).toMatchObject({ state: 'unreachable', join: null })
  })
})
