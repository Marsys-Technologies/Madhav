/**
 * NIR-05: Post-retrieval readiness re-check in /api/chat/consult.
 *
 * Proves that if a chart becomes non-ready mid-retrieval (e.g., an L1/L2 rebuild
 * starts while hydrateBundle / retrieval tools are executing), consult aborts with
 * HTTP 409 CHART_RECOMPUTE_REQUIRED BEFORE starting LLM synthesis or streaming.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

const { readinessSequence, dispatchSpy } = vi.hoisted(() => ({
  readinessSequence: [] as Array<{ state: string } | 'throw'>,
  dispatchSpy: vi.fn(async () => new Response('ok', { status: 200 })),
}))

vi.mock('@/lib/charts/readiness', () => ({
  getChartReadinessMap: vi.fn(async (ids: string[]) => {
    const next = readinessSequence.shift() ?? { state: 'ready' }
    if (next === 'throw') throw new Error('readiness lookup failed mid-turn')
    return new Map(ids.map((id) => [id, next]))
  }),
  isDerivedChartReady: (r: { state: string }) => r.state === 'ready',
}))
vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'tester-uid' })) }))
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params?: unknown[]) => {
    if (/from charts/i.test(sql)) {
      return {
        rows: [{
          id: params?.[0], name: 'Native', birth_date: '1984-02-05',
          birth_time: '10:43', birth_place: 'Bhubaneswar', client_id: 'tester-uid',
        }],
      }
    }
    if (/from profiles/i.test(sql)) return { rows: [{ role: 'guest' }] }
    return { rows: [] }
  }),
}))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: vi.fn(async () => 'all') }))
vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(async () => null),
  insertConversationWithId: vi.fn(async () => undefined),
  updateConversationTitle: vi.fn(async () => undefined),
}))
vi.mock('@/lib/persistence/pending_streams_writer', () => ({ createPendingStreamWriter: vi.fn(() => ({})) }))
vi.mock('@/lib/bundle/manifest_reader', () => ({ loadManifest: vi.fn(async () => ({ fingerprint: 'test-fp' })) }))
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: vi.fn(async () => ({
    outcome: 'plan' as const,
    metrics: {
      planning_confidence: 0.9,
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
        { tool_name: 'msr_sql', params: {}, token_budget: 600, priority: 1 as const, reason: 'test' },
      ],
    },
  })),
}))
vi.mock('@/lib/bundle/bundle_hydrator', () => ({ hydrateBundle: vi.fn(async () => ({ assets: [], floor_enforced: false })) }))
vi.mock('@/lib/retrieval/registry', () => ({ getCapability: vi.fn(() => undefined) }))
vi.mock('@/lib/retrieval/registry/catalog', () => ({ getCatalog: vi.fn(() => []) }))
vi.mock('@/lib/retrieval/registry/tool_name_bridge', () => ({
  getToolByName: vi.fn((name: string) => ({ name })),
  resolveToolUri: vi.fn((name: string) => name),
}))
vi.mock('@/lib/cache/index', () => ({
  createToolCache: vi.fn(() => ({})),
  executeWithCache: vi.fn(async () => ({ results: [{ content: 'signal' }] })),
}))
vi.mock('@/lib/validators/index', () => ({
  runAll: vi.fn(async () => []),
  summarize: vi.fn(() => ({ overall: 'pass', failures: [] })),
}))
vi.mock('@/lib/config/index', () => ({ configService: { getFlag: vi.fn(() => false) } }))
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: vi.fn(async () => 'gemini-2.5-pro') }))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeLlmCallLog: vi.fn(),
  writeQueryPlanLog: vi.fn(),
  writeToolExecutionLog: vi.fn(),
  writeContextAssemblyLog: vi.fn(),
  resolveProvider: vi.fn(() => 'google'),
}))
vi.mock('@/lib/trace/emitter', () => ({ traceEmitter: { emitStep: vi.fn() } }))
vi.mock('@/lib/personas', () => ({ getPersonaForSynthesis: vi.fn(async () => null) }))
vi.mock('@/lib/projects', () => ({ getProjectForConversation: vi.fn(async () => null) }))
vi.mock('@/lib/pipelines/shared', () => ({ runAdapterDispatch: dispatchSpy }))

import { POST } from '../route'
import { readinessRefusalMessage } from '@/lib/charts/readinessCopy'

function makeReq() {
  return new Request('http://localhost/api/chat/consult', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      chartId: CHART,
      messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text: 'Give me an overview.' }] }],
    }),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  readinessSequence.length = 0
})

describe('NIR-05 POST /api/chat/consult — pre-retrieval & post-retrieval readiness holds', () => {
  it('aborts pre-retrieval with 409 when chart is building before planning or dispatch', async () => {
    readinessSequence.push({ state: 'building' })
    const res = await POST(makeReq())
    expect(res.status).toBe(409)
    const body = await res.json()
    expect(body.error.code).toBe('CHART_RECOMPUTE_REQUIRED')
    expect(body.error.retry).toBe(true)
    expect(dispatchSpy).not.toHaveBeenCalled()
  })

  it.each([
    ['building', true],
    ['failed', false],
    ['needs-rebuild', false],
  ] as const)('aborts post-retrieval with 409 when readiness becomes %s mid-retrieval, before LLM synthesis', async (postState, retry) => {
    readinessSequence.push({ state: 'ready' }, { state: postState })
    const res = await POST(makeReq())
    expect(res.status).toBe(409)
    const body = await res.json()
    expect(body.error.code).toBe('CHART_RECOMPUTE_REQUIRED')
    expect(body.error.message).toBe(readinessRefusalMessage(postState))
    expect(body.error.retry).toBe(retry)
    expect(dispatchSpy).not.toHaveBeenCalled()
  })

  it('fails closed post-retrieval with retry=true if readiness lookup throws mid-retrieval', async () => {
    readinessSequence.push({ state: 'ready' }, 'throw')
    const res = await POST(makeReq())
    expect(res.status).toBe(409)
    const body = await res.json()
    expect(body.error.code).toBe('CHART_RECOMPUTE_REQUIRED')
    expect(body.error.retry).toBe(true)
    expect(dispatchSpy).not.toHaveBeenCalled()
  })

  it('proceeds to LLM synthesis only when both pre-retrieval and post-retrieval checks are Ready', async () => {
    readinessSequence.push({ state: 'ready' }, { state: 'ready' })
    const res = await POST(makeReq())
    expect(res.status).toBe(200)
    expect(dispatchSpy).toHaveBeenCalledTimes(1)
  })
})
