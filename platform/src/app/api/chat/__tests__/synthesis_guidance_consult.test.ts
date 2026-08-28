/**
 * synthesis_guidance_consult.test.ts — V3-E-024 remediation (extends PR #1621).
 *
 * PR #1621 fixed V3-E-024 (the Vidhi compiler's E-7 `llm_extension_note` —
 * computed by `compileContract` on every call but discarded by
 * `CompiledFloorResult`, so it reached nowhere) at ONE of the three production
 * `compileFloorForPlan` call sites: `plan_stage.ts`. This asserts the identical
 * fold-into-`plan.synthesis_guidance` fix now also applies at
 * `/api/chat/consult/route.ts` (~line 676), by driving the route end-to-end
 * with a REAL `compileFloorForPlan` (not mocked — same posture as
 * `no_leakage_consult.test.ts`, the established harness this file reuses) and
 * a deepdive `scope_tuple`, then asserting the note reaches the object
 * `runAdapterDispatch` receives (the same `plan.synthesis_guidance` field
 * `buildConsultSystemContent` folds into the synthesis system prompt under
 * "SYNTHESIS GUIDANCE:" — see `run_adapter_dispatch.ts`).
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
        rows: [{ id, name: 'Test Native', birth_date: '1984-02-05', birth_time: '10:43', birth_place: 'Bhubaneswar', client_id: 'tester-uid' }],
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

// Planner returns a resolved deepdive `scope_tuple` (career, standard width,
// deep depth) — this is what drives `compileFloorForPlan`'s real
// `llm_extension_note` to lead with the E-7 INSIGHT MANDATE prefix (see
// `vidhi/compiler.ts`'s `extensionNoteForDepth`).
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: vi.fn(async () => ({
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
        { tool_name: 'msr_sql', params: {}, token_budget: 600, priority: 1 as const, reason: 'test — satisfies B.11 floor' },
      ],
      scope_tuple: { intent: 'domain_assessment', domains: ['career'], width: 'standard', depth: 'deep' },
      synthesis_guidance: 'Lead with the dominant career yoga.',
    },
  })),
}))

vi.mock('@/lib/bundle/bundle_hydrator', () => ({
  hydrateBundle: vi.fn(async () => ({ assets: [], floor_enforced: false })),
}))

// compiled_floor_adapter is DELIBERATELY NOT mocked — this test exercises the
// REAL `compileFloorForPlan` so the assertion is a genuine before/after check
// on the fix, not a stand-in.

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
    const plan = ctx.plan as { synthesis_guidance?: string }
    const body = JSON.stringify({ synthesis_guidance: plan.synthesis_guidance ?? null })
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

describe('V3-E-024 — consult/route.ts folds compileFloorForPlan().llm_extension_note into plan.synthesis_guidance', () => {
  it('appends the E-7 INSIGHT MANDATE note (real compileFloorForPlan, deepdive scope_tuple) to the planner-authored synthesis_guidance the dispatch layer receives', async () => {
    const resp = await POST(makePost(NATIVE, 'Give me a deep dive on my career.'))
    expect(resp.status).toBe(200)

    const payload = (await resp.json()) as { synthesis_guidance: string | null }
    expect(payload.synthesis_guidance).not.toBeNull()
    // The planner's own guidance survives (fold-in appends, never replaces).
    expect(payload.synthesis_guidance).toContain('Lead with the dominant career yoga.')
    // Before this fix, `llm_extension_note` was computed by the real compiler
    // but had no field on CompiledFloorResult to carry it out at all — this is
    // the genuine post-fix behavior, not a value that existed before PR #1621.
    expect(payload.synthesis_guidance).toContain('INSIGHT MANDATE (E-7)')
    expect(payload.synthesis_guidance).toContain('Band 3 (question-specific extension) is LLM-owned')
  })
})
