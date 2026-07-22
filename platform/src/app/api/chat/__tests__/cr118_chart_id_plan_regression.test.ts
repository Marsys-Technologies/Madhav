/**
 * cr118_chart_id_plan_regression.test.ts — RC-11 (CR-118) regression guard.
 *
 * CR-118 (MARSYS_DEFECT_GAP_REGISTER_v2_0.md): msr_sql / get_yoga_firings /
 * cgm_graph_walk mid-stream fast-failed during live /api/chat/consult synthesis
 * — SSE tool events with single-digit-ms latency + is_error, matching the
 * `ToolEvent` shape (`name`/`status`/`ms`/`ok_count`/`err_count`) this route
 * itself emits (route.ts's ToolEvent interface). Root cause: consult/route.ts's
 * `LegacyQueryPlanShape` object (built at the "Adapter: PipelinePlan → legacy-
 * shaped object for retrieval tools" comment) never carried a `chart_id` field
 * — neither the interface nor the literal — even though `tool_name_bridge.ts`'s
 * `getToolByName().retrieve()` reads `plan['chart_id']` to populate
 * `args.chart_id` for every `scope: 'per_chart'` capability
 * (msr_sql/get_yoga_firings/cgm_graph_walk are all per_chart). With chart_id
 * absent, the capability handler hits its own `if (!chart_id) return
 * {content:{error:'chart_id is required'}, is_error:true}` guard — a
 * synchronous, pre-DB-round-trip return, which is exactly the single-digit-ms
 * fast-fail CR-118 documents. This test proves the fix: the `queryPlan` object
 * this route hands to `executeWithCache` (→ `tool.retrieve(plan, params)`)
 * carries `chart_id` equal to the request's `chartId`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const NATIVE = '482012f1-710e-4a25-994a-93821f5871aa'

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

// Planner authorizes exactly the three CR-118 tools — no leakage/floor noise.
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: vi.fn(async () => ({
    outcome: 'plan' as const,
    plan: {
      query_class: 'holistic',
      domains: ['career'],
      forward_looking: false,
      tool_calls: [
        { tool_name: 'msr_sql', params: {}, token_budget: 600, priority: 1 as const, reason: 'CR-118 regression — msr_sql' },
        { tool_name: 'get_yoga_firings', params: {}, token_budget: 400, priority: 1 as const, reason: 'CR-118 regression — get_yoga_firings' },
        { tool_name: 'cgm_graph_walk', params: {}, token_budget: 400, priority: 1 as const, reason: 'CR-118 regression — cgm_graph_walk' },
      ],
    },
  })),
}))

vi.mock('@/lib/bundle/bundle_hydrator', () => ({
  hydrateBundle: vi.fn(async () => ({ assets: [], floor_enforced: false })),
}))

vi.mock('@/lib/retrieval/registry', () => ({
  getCapability: vi.fn(() => undefined),
}))
vi.mock('@/lib/retrieval/registry/catalog', () => ({
  getCatalog: vi.fn(() => []),
}))
vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({
  getToolByName: vi.fn((name: string) => ({ name })),
  resolveToolUri: vi.fn((name: string) => name),
}))

// Capture every `plan` argument executeWithCache is invoked with — this is
// the exact object tool_name_bridge.ts's retrieve() reads plan['chart_id']
// off of. CR-118 reproduces if any per_chart tool's captured plan lacks a
// chart_id matching the request's chartId.
const capturedPlans: Array<{ toolName: string; plan: Record<string, unknown> }> = []

vi.mock('@/lib/cache/index', () => ({
  createToolCache: vi.fn(() => ({})),
  executeWithCache: vi.fn(
    async (tool: { name: string }, plan: Record<string, unknown>) => {
      capturedPlans.push({ toolName: tool.name, plan })
      return { results: [{ content: `content-for-${tool.name}` }] }
    }
  ),
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
  dispatchSpy: vi.fn(async () => new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { 'content-type': 'application/json' },
  })),
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
  capturedPlans.length = 0
})

describe('CR-118 regression — consult route threads chart_id onto the dispatched queryPlan', () => {
  it('every per_chart tool call (msr_sql, get_yoga_firings, cgm_graph_walk) receives a plan carrying chart_id', async () => {
    const resp = await POST(makePost(NATIVE, 'What yogas are firing and what does the causal graph say about career?'))
    expect(resp.status).toBe(200)

    // Sanity: dispatch actually happened for all three CR-118 tools.
    const dispatchedNames = capturedPlans.map((c) => c.toolName)
    expect(dispatchedNames).toEqual(
      expect.arrayContaining(['msr_sql', 'get_yoga_firings', 'cgm_graph_walk'])
    )
    expect(capturedPlans.length).toBeGreaterThanOrEqual(3)

    // The actual regression assertion: NONE of the dispatched plans are
    // missing chart_id (pre-fix, `plan.chart_id` was `undefined` for every
    // call — this is the exact condition tool_name_bridge.ts's retrieve()
    // treats as "no chart_id supplied", triggering the per_chart handler's
    // fast-fail `chart_id is required` guard).
    for (const { toolName, plan } of capturedPlans) {
      expect(plan['chart_id'], `${toolName} plan.chart_id`).toBe(NATIVE)
    }
  })
})
