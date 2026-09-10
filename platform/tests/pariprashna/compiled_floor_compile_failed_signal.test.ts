/**
 * compiled_floor_compile_failed_signal.test.ts — V3-E-026 remediation proof
 * (EDIR_V3_REGISTER_v1_0.md, S2/HIGH, §N.8 Earned-Signal class).
 *
 * `compileFloorForPlan` (`platform/src/lib/pipeline/compiled_floor_adapter.ts`)
 * is TOTAL and never throws out to its caller: on a registry-completeness bug
 * (`compileContract` throwing) it returns `{ compileFailed: true, toolCalls:
 * [], ... }` — a real, correctly-computed detector for "the intent-specific
 * compiled floor did not compile this turn." Before this fix, `plan_stage.ts`
 * read only `compiledFloor.toolCalls` and never referenced `.compileFailed`
 * anywhere in the file (grep-confirmed by the S4 assurance investigation) — a
 * genuine registry-completeness failure was indistinguishable from a healthy
 * turn on every reader/operator-facing surface.
 *
 * This test drives the REAL `/api/pariprashna` route (the REAL `plan_stage.ts`
 * is not mocked) with `compileFloorForPlan` forced to return
 * `compileFailed: true`, and asserts the route now emits a `flag` wire event
 * carrying that signal — proving the fix, not just asserting on the fixed
 * source. A NEGATIVE CONTROL with `compileFailed: false` proves the assertion
 * is load-bearing (the flag is genuinely conditional on the signal, not always
 * emitted regardless).
 *
 * Technique mirrors `no_leakage_route_canary.test.ts` (PB-3 L-6, door 3):
 * drive the real route through to a real SSE response with only the LLM/DB/
 * adapter boundary mocked; `plan_stage.ts` itself runs for real.
 *
 * Test subject: synthetic chart `1c826d5a-…` ONLY, per S4 stream instructions
 * — never the native's real chart.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const SAFE_TOOL = 'msr_sql'

// ── Toggleable compiled-floor mock — the ONLY thing under test's control. ───
const { floorControl } = vi.hoisted(() => ({ floorControl: { compileFailed: true } }))
vi.mock('@/lib/pipeline/compiled_floor_adapter', () => ({
  compileFloorForPlan: vi.fn(() => ({
    compilerIntent: 'chart_overview',
    toolCalls: [],
    mappedPrimitives: [],
    unmappedPrimitives: [],
    compileFailed: floorControl.compileFailed,
  })),
  ensureB11WholeChartReadFloor: vi.fn(() => false),
  ensureDashaContextFloor: vi.fn(() => false),
}))

// ── Boundary mocks (LLM / DB / auth / adapter) — same shape as the PB-3 L-6
// door-3 canary; `plan_stage.ts` (the file under test) is NOT mocked. ────────
vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'tester-uid' })) }))
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params?: unknown[]) => {
    if (/from charts/i.test(sql)) {
      const id = (params?.[0] as string) ?? CHART
      return { rows: [{ id, name: 'Synthetic Test Chart', client_id: 'tester-uid' }] }
    }
    if (/from profiles/i.test(sql)) return { rows: [{ role: 'super_admin' }] }
    return { rows: [] }
  }),
}))
vi.mock('@/lib/config/index', () => ({
  configService: { getFlag: vi.fn((k: string) => k === 'PARIPRASHNA_ENABLED') },
}))
vi.mock('@/lib/models/runtime_config', () => ({ getEffectiveModel: vi.fn(async () => 'gemini-2.5-pro') }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: vi.fn(async () => 'view') }))
vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(async () => null),
  insertConversationWithId: vi.fn(async () => undefined),
  updateConversationTitle: vi.fn(async () => undefined),
}))
vi.mock('@/lib/bundle/manifest_reader', () => ({ loadManifest: vi.fn(async () => ({ fingerprint: 'test-fp' })) }))
vi.mock('@/lib/retrieval/orientation', () => ({ buildChartOrientation: vi.fn(async () => null) }))
vi.mock('@/lib/bundle/bundle_hydrator', () => ({ hydrateBundle: vi.fn(async () => ({ assets: [], floor_enforced: false })) }))
vi.mock('@/lib/persistence/pending_streams_writer', () => ({ createPendingStreamWriter: vi.fn(() => ({})) }))
vi.mock('@/lib/db/monitoring-write', () => ({ writeContextAssemblyLog: vi.fn() }))
vi.mock('@/lib/pariprashna/protocol/ring_buffer', () => ({
  openTurnBuffer: vi.fn(async () => {}),
  appendBufferedEvent: vi.fn(async () => {}),
}))

// System-content builder + summaries splice/assemble — cheap stubs (pre-synthesis).
vi.mock('@/lib/pipelines/shared/run_adapter_dispatch', () => ({ buildConsultSystemContent: vi.fn(() => 'SYS') }))
vi.mock('@/lib/pariprashna/summaries/splice', () => ({ getConversationSummaryForSplice: vi.fn(async () => null) }))
vi.mock('@/lib/pariprashna/summaries/assemble', () => ({ assembleSynthesisPrefix: vi.fn(({ precedingBlock }: { precedingBlock: string }) => precedingBlock) }))

// Citation gate — PASS (not the subject of this test).
vi.mock('@/lib/synthesis/streaming_citation_validator', () => ({
  validateCitationsForStream: vi.fn(() => ({ gateResult: 'PASS', gateReason: 'ok', layer1Count: 0, layer2Verified: 0 })),
}))

// Planner: a plan carrying a real `scope_tuple` (the field plan_stage.ts gates
// the `compileFloorForPlan` call on) plus one already-authorized safe tool.
const { mockPlanner } = vi.hoisted(() => ({ mockPlanner: vi.fn() }))
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: mockPlanner,
}))
function planWithScopeTuple() {
  return {
    outcome: 'plan' as const,
    plan: {
      query_class: 'holistic',
      domains: ['general'],
      forward_looking: false,
      tool_calls: [
        { tool_name: SAFE_TOOL, params: {}, token_budget: 600, priority: 1 as const, reason: 'planner-authorized' },
      ],
      scope_tuple: {
        intent: 'chart_overview',
        domains: ['general'],
        width: 'standard',
        depth: 'standard',
        horizon: 'present',
        intervention: 'none',
        entitlement: 'native',
      },
    },
  }
}

vi.mock('@/lib/retrieval/registry/tool_name_bridge', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/retrieval/registry/tool_name_bridge')>()
  return { ...actual, getToolByName: vi.fn((name: string) => ({ name })) }
})

// Dispatch seam — cheap stub, not the subject of this test.
vi.mock('@/lib/cache/index', () => ({
  createToolCache: vi.fn(() => ({})),
  executeWithCache: vi.fn(async (t: { name: string }) => ({
    tool_bundle_id: 'v3e026', tool_name: t.name, tool_version: '1.0', invocation_params: {},
    results: [], served_from_cache: false, latency_ms: 1, result_hash: 'sha256:v3e026', schema_version: '1.0' as const,
  })),
}))
vi.mock('@/lib/retrieval/qos/dispatch_queue', () => ({
  getSharedQosDispatchQueue: vi.fn(() => ({ submit: async <T>(task: { run: () => Promise<T> }) => task.run() })),
}))

// Adapter + agentic loop — driven to EMPTY synthesis (no LLM), same as door-3 canary.
vi.mock('@/lib/providers/dispatcher', () => ({
  getAdapter: vi.fn(() => ({
    getManifest: () => ({ adaptiveToolLoop: false }),
    tools: () => ({ tools: [] }),
    chat: async function* () {},
  })),
}))
vi.mock('@/lib/synthesis/agentic_loop', () => ({
  LOOP_CONFIG_BY_PROVIDER: { google: { maxIterations: 8 }, anthropic: { maxIterations: 8 }, openai: { maxIterations: 8 } },
  runAgenticLoop: async function* () {},
}))
vi.mock('@/lib/synthesis/mcp_tool_executor', () => ({ executeMCPTool: vi.fn(async () => ({ results: [] })) }))

import { POST } from '@/app/api/pariprashna/route'

function makeReq(text: string): Request {
  return new Request('http://localhost/api/pariprashna', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ chartId: CHART, stack: 'gemini', messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text }] }] }),
  })
}

/** Parse the SSE body into decoded event objects. */
async function readEvents(resp: Response): Promise<Array<Record<string, unknown>>> {
  const text = await resp.text()
  return text
    .split('\n')
    .filter((l) => l.startsWith('data: '))
    .map((l) => JSON.parse(l.slice(6)) as Record<string, unknown>)
}

beforeEach(() => {
  mockPlanner.mockResolvedValue(planWithScopeTuple())
})

describe('V3-E-026 — compiled-floor compileFailed signal now surfaces on the wire (real plan_stage.ts, real route)', () => {
  it('compileFailed:true — the route emits a compiled_floor_compile_failed flag (previously: total silence)', async () => {
    floorControl.compileFailed = true
    const resp = await POST(makeReq('Give me a whole-chart overview.'))
    expect(resp.status).toBe(200)
    const events = await readEvents(resp)

    const flag = events.find((e) => e.type === 'flag' && e.code === 'compiled_floor_compile_failed')
    expect(flag, 'expected a compiled_floor_compile_failed flag when compileFloorForPlan reports compileFailed:true').toBeDefined()
    expect(flag?.level).toBe('error')
    expect(String(flag?.detail)).toContain('chart_overview') // carries the compiler intent, not just a bare code
  })

  it('NEGATIVE CONTROL: compileFailed:false — NO compiled_floor_compile_failed flag fires (proves the assertion is conditional, not vacuous)', async () => {
    floorControl.compileFailed = false
    const resp = await POST(makeReq('Give me a whole-chart overview.'))
    expect(resp.status).toBe(200)
    const events = await readEvents(resp)

    const flag = events.find((e) => e.type === 'flag' && e.code === 'compiled_floor_compile_failed')
    expect(flag, 'a healthy compile must NOT raise the failure flag').toBeUndefined()
  })
})
