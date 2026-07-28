/**
 * no_leakage_route_canary.test.ts — PB-3 lane L-6, deliverable 1: Arm-2 NO-LEAKAGE
 * verified ON THE NEW ROUTE (`/api/pariprashna`), §14.10 + BRIEF_PB-3 §G item 10
 * [integrity]: "zero leakage-flagged tools reachable from the route's planner
 * context (canary + exclusion test, demonstrated-can-fail)."
 *
 * This is DOOR 3 — the companion to the two existing runtime canaries:
 *   door 1  `src/app/api/chat/__tests__/no_leakage_runtime_canary_consult.test.ts`
 *   door 2  `src/lib/retrieval/registry/__tests__/no_leakage_runtime_canary.test.ts`
 * Same technique: drive the REAL route with a COMPROMISED planner that authorizes
 * a REAL `calibration_context_only` tool (`lel_query`), against the REAL registry
 * + REAL `filterLeakedCapabilities` (NOT mocked), and assert the leaked tool
 * never reaches the route's dispatch. Only the LLM/DB/adapter boundary is mocked;
 * synthesis is driven to empty so the assertion is about the retrieval+plan
 * projections (the ones a leaked tool would ride on), which is where the route
 * enforces F-R7 (route.ts line ~485).
 *
 * ── Why this is not the PB-2 "test that can never fail" anti-pattern ──────────
 * FOLLOWUP_PB-2_BYTE_EQUALITY_FIXTURE_COVERAGE warns that a green run must
 * actually stand in for the claim. Two guards here:
 *   1. The filter is the REAL one — this exercises the shipped enforcement, not a
 *      test-local reimplementation.
 *   2. A PERMANENT NEGATIVE CONTROL (`leakControl.disabled = true`) turns the
 *      exclusion off and asserts the leak DOES reach dispatch — proving the
 *      scenario is a genuine leak vector and the positive assertion is
 *      load-bearing, not vacuously green. If a future change made the route
 *      leak-proof by some OTHER mechanism, this negative control would fail
 *      loudly (a canary on the canary). A live red-then-green scratch cycle is
 *      also recorded in REPORT_PB-3.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const LEAKED_TOOL = 'lel_query' // resolves to marsys://tool/L5/lel_query, calibration_context_only:true
const SAFE_TOOL = 'msr_sql'
const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

// ── Toggleable delegating mock of the REAL filter ────────────────────────────
// Default: the REAL filterLeakedCapabilities runs (this is the shipped
// enforcement). When leakControl.disabled === true, it becomes identity — the
// negative control that proves the leak is otherwise reachable.
const { leakControl, dispatchedTools } = vi.hoisted(() => ({
  leakControl: { disabled: false },
  dispatchedTools: [] as string[],
}))
vi.mock('@/lib/pipeline/no_leakage_filter', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/pipeline/no_leakage_filter')>()
  return {
    ...actual,
    filterLeakedCapabilities: (names: readonly string[]) =>
      leakControl.disabled ? [...names] : actual.filterLeakedCapabilities(names),
  }
})

// ── Boundary mocks (LLM / DB / auth / adapter) — registry + filter stay REAL. ─
vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'tester-uid' })) }))
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params?: unknown[]) => {
    if (/from charts/i.test(sql)) {
      const id = (params?.[0] as string) ?? CHART
      return { rows: [{ id, name: 'Abhisek Mohanty', client_id: 'tester-uid' }] }
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

// Floor adapters — no-op so the authorized set is exactly {SAFE_TOOL, LEAKED_TOOL}.
vi.mock('@/lib/pipeline/compiled_floor_adapter', () => ({
  compileFloorForPlan: vi.fn(() => ({ toolCalls: [], mappedPrimitives: [], unmappedPrimitives: [], compilerIntent: 'general_synthesis', compileFailed: false })),
  ensureB11WholeChartReadFloor: vi.fn(() => false),
  ensureDashaContextFloor: vi.fn(() => false),
}))

// System-content builder + summaries splice/assemble — cheap stubs (pre-synthesis).
vi.mock('@/lib/pipelines/shared/run_adapter_dispatch', () => ({ buildConsultSystemContent: vi.fn(() => 'SYS') }))
vi.mock('@/lib/pariprashna/summaries/splice', () => ({ getConversationSummaryForSplice: vi.fn(async () => null) }))
vi.mock('@/lib/pariprashna/summaries/assemble', () => ({ assembleSynthesisPrefix: vi.fn(({ precedingBlock }: { precedingBlock: string }) => precedingBlock) }))

// Citation gate — PASS (post-synthesis, empty text).
vi.mock('@/lib/synthesis/streaming_citation_validator', () => ({
  validateCitationsForStream: vi.fn(() => ({ gateResult: 'PASS', gateReason: 'ok', layer1Count: 0, layer2Verified: 0 })),
}))

// Compromised planner: authorizes the REAL leaked capability alongside a safe one.
const { mockPlanner } = vi.hoisted(() => ({ mockPlanner: vi.fn() }))
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: mockPlanner,
}))
function compromisedPlan() {
  return {
    outcome: 'plan' as const,
    plan: {
      query_class: 'holistic',
      domains: ['career'],
      forward_looking: false,
      tool_calls: [
        { tool_name: SAFE_TOOL, params: {}, token_budget: 600, priority: 1 as const, reason: 'B.11 floor' },
        { tool_name: LEAKED_TOOL, params: {}, token_budget: 400, priority: 2 as const, reason: 'canary — must be stripped' },
      ],
    },
  }
}

// tool_name_bridge: REAL resolveToolUri/TOOL_NAME_TO_URI (so the real filter +
// resolveActivityLabel work); only getToolByName's dispatch stubbed.
vi.mock('@/lib/retrieval/registry/tool_name_bridge', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/retrieval/registry/tool_name_bridge')>()
  return { ...actual, getToolByName: vi.fn((name: string) => ({ name })) }
})

// Dispatch seam — records every tool name the route actually dispatches.
vi.mock('@/lib/cache/index', () => ({
  createToolCache: vi.fn(() => ({})),
  executeWithCache: vi.fn(async (t: { name: string }) => {
    dispatchedTools.push(t.name)
    return {
      tool_bundle_id: 'canary', tool_name: t.name, tool_version: '1.0', invocation_params: {},
      results: [], served_from_cache: false, latency_ms: 1, result_hash: 'sha256:canary', schema_version: '1.0' as const,
    }
  }),
}))
vi.mock('@/lib/retrieval/qos/dispatch_queue', () => ({
  getSharedQosDispatchQueue: vi.fn(() => ({ submit: async <T>(task: { run: () => Promise<T> }) => task.run() })),
}))

// Adapter + agentic loop — driven to EMPTY synthesis (no LLM), so accumulatedText
// stays '' and the finalize/persistence block is skipped entirely.
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
  dispatchedTools.length = 0
  leakControl.disabled = false
  mockPlanner.mockResolvedValue(compromisedPlan())
})

describe('PB-3 L-6 — NO-LEAKAGE runtime canary — door 3 (/api/pariprashna, real registry + real filter)', () => {
  it('a real calibration_context_only tool authorized by the planner NEVER reaches dispatch', async () => {
    const resp = await POST(makeReq('Give me a whole-chart career orientation.'))
    expect(resp.status).toBe(200)
    const events = await readEvents(resp)

    // Projection 1 (retrieval dispatch): the leaked tool never dispatched.
    expect(dispatchedTools).not.toContain(LEAKED_TOOL)
    // Sanity: the safe tool DID dispatch (the route ran retrieval for real).
    expect(dispatchedTools).toContain(SAFE_TOOL)

    // The route surfaced the F-R7 strip as a wire flag (count only, no id — gate 11).
    const stripFlag = events.find((e) => e.type === 'flag' && e.code === 'no_leakage_capabilities_stripped')
    expect(stripFlag, 'expected a no_leakage_capabilities_stripped flag').toBeDefined()
    // The flag must NEVER carry the raw leaked capability name on the wire.
    expect(JSON.stringify(stripFlag)).not.toContain(LEAKED_TOOL)
  })

  it('NEGATIVE CONTROL: with the exclusion disabled, the SAME leaked tool DOES reach dispatch (proves the assertion is load-bearing)', async () => {
    leakControl.disabled = true // break the exclusion
    const resp = await POST(makeReq('Give me a whole-chart career orientation.'))
    expect(resp.status).toBe(200)
    await readEvents(resp)

    // Without the filter, the compromised planner's leaked tool flows straight to
    // dispatch — this is the leak the positive test above is preventing.
    expect(dispatchedTools).toContain(LEAKED_TOOL)
    expect(dispatchedTools).toContain(SAFE_TOOL)
  })
})
