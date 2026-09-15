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
const COMPILED_TRANSIT_ARGS = {
  as_of_date: '2026-09-15',
  requests: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
    .map((planet) => ({ planet, start_date: '2026-09-15', end_date: '2026-09-15' })),
}

const { plannerSpy, qosSubmitSpy, compileInquirySpy } = vi.hoisted(() => ({
  plannerSpy: vi.fn(),
  qosSubmitSpy: vi.fn(async ({ run }: { run: () => Promise<unknown> }) => run()),
  compileInquirySpy: vi.fn(),
}))

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
  callPipelinePlanner: (...args: unknown[]) => plannerSpy(...args),
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
  getToolByName: vi.fn((name: string) => ({
    name,
    dispatch_units: name === 'query_current_transit_snapshot' ? 9 : 1,
  })),
  resolveToolUri: vi.fn((name: string) => name),
}))

vi.mock('@/lib/retrieval/qos/dispatch_queue', () => ({
  getSharedQosDispatchQueue: vi.fn(() => ({ submit: qosSubmitSpy })),
}))

vi.mock('@/lib/retrieval/registry/knowledge', () => ({
  assertPinnedCapabilityKnowledgeCurrent: vi.fn(() => ({ content_hash: 'sha256:test' })),
  loadChartCapabilityOverlay: vi.fn(async () => ({ overlay_version: 'overlay-test', build_id: 'build-test' })),
}))

vi.mock('@/lib/vidhi/inquiry', () => ({
  managedPlanToAiInquiryProposal: vi.fn(() => ({ question_facets: [], uncommon_adjacencies: [], hypotheses: [] })),
  compileInquiryContract: (...args: unknown[]) => compileInquirySpy(...args),
  adoptInquiryPlanItems: vi.fn((plan: { tool_calls: Array<Record<string, unknown>> }, contract: { plan_items: Array<{ state: string; binding_id: string | null; args: Record<string, unknown> }> }) => {
    const adopted = contract.plan_items
      .filter((item) => item.state === 'ready' && item.binding_id?.startsWith('registry:'))
      .map((item) => ({
        tool_name: item.binding_id!.slice('registry:'.length),
        params: item.args,
        token_budget: 800,
        priority: 1,
        reason: 'Inquiry Contract fixture',
      }))
    plan.tool_calls.splice(0, plan.tool_calls.length, ...adopted)
    return adopted.map((call) => call.tool_name)
  }),
}))

// Capture every `plan` argument executeWithCache is invoked with — this is
// the exact object tool_name_bridge.ts's retrieve() reads plan['chart_id']
// off of. CR-118 reproduces if any per_chart tool's captured plan lacks a
// chart_id matching the request's chartId.
const capturedPlans: Array<{ toolName: string; plan: Record<string, unknown>; params: Record<string, unknown> | undefined }> = []

vi.mock('@/lib/cache/index', () => ({
  createToolCache: vi.fn(() => ({})),
  executeWithCache: vi.fn(
    async (tool: { name: string }, plan: Record<string, unknown>, _cache: unknown, params?: Record<string, unknown>) => {
      capturedPlans.push({ toolName: tool.name, plan, params })
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
  qosSubmitSpy.mockClear()
  compileInquirySpy.mockReset()
  capturedPlans.length = 0
  plannerSpy.mockResolvedValue({
    outcome: 'plan' as const,
    metrics: {
      planning_confidence: 0.82,
      fallback_used: false,
      active_model_id: 'mock-planner-model',
      parsed_on_first_attempt: true,
      first_parse_error: null,
    },
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
  })
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

  it('adopts compiler-owned aggregate arguments and reserves all nine QoS units', async () => {
    plannerSpy.mockResolvedValueOnce({
      outcome: 'plan' as const,
      metrics: {
        planning_confidence: 0.91, fallback_used: false, active_model_id: 'mock-planner-model',
        parsed_on_first_attempt: true, first_parse_error: null,
      },
      plan: {
        query_class: 'predictive', domains: ['timing'], forward_looking: true,
        scope_tuple: {
          intent: 'transit_timing', domains: ['timing'], width: 'focused', depth: 'standard',
          horizon: 'current', intervention: false, entitlement: 'native',
        },
        tool_calls: [{
          tool_name: 'query_current_transit_snapshot',
          params: { as_of_date: '2099-01-01', requests: [{ planet: 'Sun' }] },
          token_budget: 800, priority: 1 as const, reason: 'planner proposal',
        }],
      },
    })
    compileInquirySpy.mockReturnValue({
      obligations: [],
      plan_items: [{
        item_id: 'item-transit', state: 'ready',
        binding_id: 'registry:query_current_transit_snapshot',
        args: COMPILED_TRANSIT_ARGS,
      }],
    })

    const resp = await POST(makePost(NATIVE, 'Where are all current transiting planets today?'))
    expect(resp.status).toBe(200)

    expect(compileInquirySpy).toHaveBeenCalledWith(expect.objectContaining({
      temporal_anchor_source: 'request_context_clock',
      temporal_anchor_date: expect.stringMatching(/^\d{4}-\d{2}-\d{2}$/),
      execution_channel: 'platform_internal',
    }))
    const aggregate = capturedPlans.find((entry) => entry.toolName === 'query_current_transit_snapshot')
    expect(aggregate?.params).toEqual(COMPILED_TRANSIT_ARGS)
    expect(aggregate?.params).not.toEqual(expect.objectContaining({ as_of_date: '2099-01-01' }))
    expect(qosSubmitSpy).toHaveBeenCalledWith(expect.objectContaining({ units: 9 }))
  })
})
