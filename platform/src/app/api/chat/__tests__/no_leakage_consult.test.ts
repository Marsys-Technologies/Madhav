/**
 * no_leakage_consult.test.ts — W6 Part D regression guard.
 *
 * Confirms /api/chat/consult/route.ts strips any calibration_context_only-flagged
 * capability from toolsAuthorized/plan.tool_calls BEFORE tool dispatch — the
 * "both doors" requirement (F-R7 NO-LEAKAGE doctrine must protect the pre-existing
 * Paripraśna/consult door exactly like the new prashna_ask door, not just one).
 *
 * Reuses the same boundary-mock harness as consult_reports_repoint.test.ts (the
 * established pattern for driving this route end-to-end in tests) but adds a
 * leaked capability to the planner's tool_calls and asserts it never reaches
 * dispatch.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'
const LEAKED_TOOL = 'marsys://tool/L5/lel_query'

vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(async () => ({ uid: 'tester-uid' })),
}))

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params?: unknown[]) => {
    if (/from charts/i.test(sql)) {
      const id = params?.[0] as string
      return {
        rows: [{ id, name: 'Abhisek Mohanty', birth_date: '1984-02-05', birth_time: '10:43', birth_place: 'Bhubaneswar', client_id: 'tester-uid' }],
      }
    }
    if (/from profiles/i.test(sql)) return { rows: [{ role: 'super_admin' }] }
    return { rows: [] }
  }),
}))

vi.mock('@/lib/auth/authorizeChartAccess', () => ({
  authorizeChartAccess: vi.fn(async () => 'view'),
}))

vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(async () => null),
  insertConversationWithId: vi.fn(async () => undefined),
  updateConversationTitle: vi.fn(async () => undefined),
}))

vi.mock('@/lib/persistence/pending_streams_writer', () => ({
  createPendingStreamWriter: vi.fn(() => ({})),
}))

vi.mock('@/lib/bundle/manifest_reader', () => ({
  loadManifest: vi.fn(async () => ({ fingerprint: 'test-fp' })),
}))

// Planner "authorizes" a leaked capability alongside an ordinary tool — the
// consult route must strip the leaked one before dispatch.
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: vi.fn(async () => ({
    outcome: 'plan' as const,
    plan: {
      query_class: 'holistic',
      domains: ['career'],
      forward_looking: false,
      tool_calls: [
        { tool_name: 'msr_sql', params: {}, token_budget: 600, priority: 1 as const, reason: 'test — satisfies B.11 floor' },
        { tool_name: LEAKED_TOOL, params: {}, token_budget: 400, priority: 2 as const, reason: 'test — should be stripped' },
      ],
    },
  })),
}))

vi.mock('@/lib/bundle/bundle_hydrator', () => ({
  hydrateBundle: vi.fn(async () => ({ assets: [], floor_enforced: false })),
}))

// Real filter (Part A) exercised for real — not mocked — against a fixture
// registry carrying exactly one leaked capability, so this test proves the
// real filterLeakedCapabilities wiring, not a stand-in.
vi.mock('@/lib/retrieval/registry', () => ({
  getCapability: vi.fn((uri: string) => (uri === LEAKED_TOOL ? { uri, calibration_context_only: true } : undefined)),
}))
vi.mock('@/lib/retrieval/registry/catalog', () => ({
  getCatalog: vi.fn(() => []),
}))
vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({
  getToolByName: vi.fn((name: string) => ({ name })),
  resolveToolUri: vi.fn((name: string) => name), // identity: names ARE URIs in this fixture
}))

vi.mock('@/lib/cache/index', () => ({
  createToolCache: vi.fn(() => ({})),
  executeWithCache: vi.fn(async (tool: { name: string }) => ({
    results: [{ content: `content-for-${tool.name}` }],
  })),
}))

vi.mock('@/lib/validators/index', () => ({
  runAll: vi.fn(async () => []),
  summarize: vi.fn(() => ({ overall: 'pass', failures: [] })),
}))

vi.mock('@/lib/config/index', () => ({
  configService: { getFlag: vi.fn(() => false) },
}))

vi.mock('@/lib/models/runtime_config', () => ({
  getEffectiveModel: vi.fn(async () => 'gemini-2.5-pro'),
}))

vi.mock('@/lib/db/monitoring-write', () => ({
  writeLlmCallLog: vi.fn(),
  writeQueryPlanLog: vi.fn(),
  writeToolExecutionLog: vi.fn(),
  writeContextAssemblyLog: vi.fn(),
  resolveProvider: vi.fn(() => 'google'),
}))

vi.mock('@/lib/trace/emitter', () => ({
  traceEmitter: { emitStep: vi.fn() },
}))

vi.mock('@/lib/personas', () => ({
  getPersonaForSynthesis: vi.fn(async () => null),
}))

vi.mock('@/lib/projects', () => ({
  getProjectForConversation: vi.fn(async () => null),
}))

const { dispatchSpy } = vi.hoisted(() => ({
  dispatchSpy: vi.fn(async (ctx: Record<string, unknown>) => {
    const queryPlan = ctx.queryPlan as { tools_authorized: string[] }
    const toolResults = (ctx.validToolResults as Array<{ results: Array<{ content: string }> }>) ?? []
    const tool_content = toolResults.flatMap((b) => b.results.map((r) => r.content)).join(' | ')
    const body = JSON.stringify({
      tools_authorized: queryPlan.tools_authorized,
      tool_content,
    })
    return new Response(body, { status: 200, headers: { 'content-type': 'application/json' } })
  }),
}))
vi.mock('@/lib/pipelines/shared', () => ({
  runAdapterDispatch: dispatchSpy,
}))

import { POST } from '../consult/route'

function makePost(chartId: string, text: string): Request {
  return new Request('http://localhost/api/chat/consult', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      chartId,
      messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text }] }],
    }),
  })
}

beforeEach(() => {
  dispatchSpy.mockClear()
})

describe('W6 Part D — consult route NO-LEAKAGE retrofit (both-doors requirement)', () => {
  it('never carries a calibration_context_only-flagged capability into tools_authorized or dispatched tool content', async () => {
    const resp = await POST(makePost(NATIVE, 'Give me an orientation overview of my whole chart.'))
    expect(resp.status).toBe(200)

    const payload = (await resp.json()) as { tools_authorized: string[]; tool_content: string }

    expect(payload.tools_authorized).not.toContain(LEAKED_TOOL)
    expect(payload.tool_content).not.toContain(`content-for-${LEAKED_TOOL}`)
    // The ordinary, non-leaked tool from the same plan DID survive.
    expect(payload.tools_authorized).toContain('msr_sql')
  })
})

describe('RC-02 — judgment_flags aggregation point (web ↔ MCP gate-flag parity)', () => {
  it('threads no_leakage_capabilities_stripped into runAdapterDispatch ctx.judgmentFlags when a strip fires — the SAME flag string /api/mcp/prashna_ask surfaces for the identical condition', async () => {
    await POST(makePost(NATIVE, 'Give me an orientation overview of my whole chart.'))

    expect(dispatchSpy).toHaveBeenCalledTimes(1)
    const ctx = dispatchSpy.mock.calls[0][0] as Record<string, unknown>
    expect(ctx.judgmentFlags).toContain('no_leakage_capabilities_stripped')
  })
})
