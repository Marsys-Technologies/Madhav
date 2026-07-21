/**
 * no_leakage_runtime_canary_consult.test.ts — W6 Part E LIVE/runtime NO-LEAKAGE
 * canary, door 1: /api/chat/consult/route.ts.
 *
 * Companion to `platform/src/lib/retrieval/registry/__tests__/no_leakage_runtime_canary.test.ts`
 * (door 2, prashna_ask) — see that file's header for the full rationale on why
 * this is a LIVE/runtime canary distinct from `projection_compiler_parity.test.ts`'s
 * static F-R7 codegen check. Split into its own file because the two routes need
 * incompatible top-level module mocks that collide if combined in one file's
 * hoisted `vi.mock` calls (this route needs the real `@/lib/models/registry`
 * STACK_ROUTING export; the prashna_ask canary mocks a lighter model surface).
 *
 * Real registry + real `filterLeakedCapabilities` (Part A) — NOT mocked. Only
 * `getToolByName`'s actual dispatch is stubbed (via `importOriginal`, so
 * `resolveToolUri`/`getCapability` stay real) to avoid a live DB call from a real
 * capability handler, plus the usual DB/auth/planner boundary mocks this route's
 * existing test suites (`consult_reports_repoint.test.ts`) already establish as
 * the pattern for driving it end-to-end.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const LEAKED_TOOL = 'marsys://tool/L5/lel_query'
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(async () => ({ uid: 'tester-uid' })),
}))

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params?: unknown[]) => {
    if (/from charts/i.test(sql)) {
      const id = (params?.[0] as string) ?? CHART
      return { rows: [{ id, name: 'Abhisek Mohanty', birth_date: '1984-02-05', birth_time: '10:43', birth_place: 'Bhubaneswar', client_id: 'tester-uid' }] }
    }
    if (/from profiles/i.test(sql)) return { rows: [{ role: 'super_admin' }] }
    return { rows: [] }
  }),
}))

vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: vi.fn(async () => 'view') }))

vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(async () => null),
  insertConversationWithId: vi.fn(async () => undefined),
  updateConversationTitle: vi.fn(async () => undefined),
}))

vi.mock('@/lib/persistence/pending_streams_writer', () => ({ createPendingStreamWriter: vi.fn(() => ({})) }))
vi.mock('@/lib/bundle/manifest_reader', () => ({ loadManifest: vi.fn(async () => ({ fingerprint: 'test-fp' })) }))

// Fixture "compromised planner" output: authorizes the real leaked capability
// alongside an ordinary tool.
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: vi.fn(async () => ({
    outcome: 'plan' as const,
    plan: {
      query_class: 'holistic',
      domains: ['career'],
      forward_looking: false,
      tool_calls: [
        { tool_name: 'msr_sql', params: {}, token_budget: 600, priority: 1 as const, reason: 'canary fixture — B.11 floor satisfied' },
        { tool_name: LEAKED_TOOL, params: {}, token_budget: 400, priority: 2 as const, reason: 'canary fixture — must be stripped' },
      ],
    },
  })),
}))

vi.mock('@/lib/bundle/bundle_hydrator', () => ({
  hydrateBundle: vi.fn(async () => ({ assets: [], floor_enforced: false })),
}))

// Real registry: NOT mocked. tool_name_bridge keeps the REAL resolveToolUri (so
// filterLeakedCapabilities' real lookups work), stubbing only getToolByName's
// dispatch to avoid a live DB call from inside a real capability handler.
vi.mock('@/lib/retrieval/registry/tool_name_bridge', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/retrieval/registry/tool_name_bridge')>()
  return {
    ...actual,
    getToolByName: vi.fn((name: string) => ({ name })),
  }
})

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

const { dispatchSpy } = vi.hoisted(() => ({
  dispatchSpy: vi.fn(async (ctx: Record<string, unknown>) => {
    const queryPlan = ctx.queryPlan as { tools_authorized: string[] }
    const toolResults = (ctx.validToolResults as Array<{ results: Array<{ content: string }> }>) ?? []
    const tool_content = toolResults.flatMap((b) => b.results.map((r) => r.content)).join(' | ')
    return new Response(
      JSON.stringify({ tools_authorized: queryPlan.tools_authorized, tool_content }),
      { status: 200, headers: { 'content-type': 'application/json' } },
    )
  }),
}))
vi.mock('@/lib/pipelines/shared', () => ({ runAdapterDispatch: dispatchSpy }))

import { POST } from '../consult/route'

function makePost(chartId: string, text: string): Request {
  return new Request('http://localhost/api/chat/consult', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ chartId, messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text }] }] }),
  })
}

beforeEach(() => {
  dispatchSpy.mockClear()
})

describe('W6 Part E — NO-LEAKAGE runtime canary — door 1 (consult route, real registry + real filter)', () => {
  it('a real calibration_context_only capability never reaches dispatch', async () => {
    const resp = await POST(makePost(CHART, 'Give me an orientation overview of my whole chart.'))
    expect(resp.status).toBe(200)

    const payload = (await resp.json()) as { tools_authorized: string[]; tool_content: string }
    expect(payload.tools_authorized).not.toContain(LEAKED_TOOL)
    expect(payload.tool_content).not.toContain(`content-for-${LEAKED_TOOL}`)
    expect(payload.tools_authorized).toContain('msr_sql')
  })
})
