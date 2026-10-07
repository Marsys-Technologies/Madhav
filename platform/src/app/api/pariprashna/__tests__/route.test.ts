/**
 * route.test.ts — POST /api/pariprashna (the WEB door).
 *
 * V3-E-055 (EDIR_V3_REGISTER_v1_0.md). Before this file, `src/app/api/pariprashna/`
 * had NO `__tests__` directory at all: the safety module's own unit tests (680
 * tests, `src/lib/pariprashna/safety/__tests__/*`) and the golden-stream corpus
 * (`tests/pariprashna/route_ports/route_golden_stream.test.ts`, 30 scenarios, none
 * matching `safety|hard_stop|hs1|hs2|hs3|hs4|seal_pending`) were both thorough and
 * green, but nothing proved `runSafetyPolicyGate`'s `speak()` calls actually reach
 * THIS route's SSE wire, and the post-plan escalation branch (`route.ts:186-199`)
 * — unique to this route, not exercised by the safety module's own unit tests,
 * which stop at `reclassifyAfterPlan`'s return value — was untested anywhere.
 *
 * MIRRORS: `src/app/api/mcp/prashna_ask/__tests__/route.test.ts`'s
 * "PPR-12 safety gate (MCP door)" describe block (HS-2 hard stop, seal path,
 * plan-time escalation, the floor test) and `tests/unit/chat-v2/
 * safety_gate_consult_door.test.ts` (the consult door's parallel coverage),
 * adapted to THIS route's SSE wire format instead of those routes' NDJSON /
 * UIMessage-stream shapes. The mock graph below is copied from the proven,
 * already-green `route_golden_stream.test.ts` (same route, same file) rather
 * than reinvented — that harness already demonstrates every one of these mocks
 * lets the real `POST` handler run end-to-end without touching a live DB/LLM.
 *
 * REAL (never mocked) in this file: `runSafetyPolicyGate`, `classifyTurnSafety`,
 * `reclassifyAfterPlan`, and the fixed response strings — so a scenario here
 * genuinely exercises the safety module's classification logic, not a stub of
 * it. Only the ONE flag-read site (`@/lib/pariprashna/safety/flag`) is mocked,
 * for the same reason the two sibling door tests mock it: `configService`'s
 * `getFlag` is ALSO mocked in this file (below), so both approaches would work,
 * but mocking the one-function flag module directly is the belt-and-suspenders
 * pattern the safety module's own unit tests use.
 *
 * Auth/DB/chart access are fully mocked — the synthetic test chart id below is
 * never actually queried against a live database, but the repo's test-data law
 * (never the native's real chart, even in a fully-mocked file) is honored
 * anyway.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// ── The safety flag, mocked at its single read site (belt + suspenders; see
// header comment). PARIPRASHNA_SAFETY_GATE_ENABLED defaults OFF in production
// (V3-E-054, a different already-referred finding) — this file forces it ON
// only within each test's own scope, never touching the flag's real default.
const {
  safetyFlagState, byokFlagState, mockAuthenticateByokUser, mockPrepareByokTurn,
  mockByokSynthStream, mockByokWorkerGenerate, mockByokRelease,
  mockInsertRoleReceipt,
} = vi.hoisted(() => ({
  safetyFlagState: { on: false },
  byokFlagState: { on: false },
  mockAuthenticateByokUser: vi.fn(),
  mockPrepareByokTurn: vi.fn(),
  mockByokSynthStream: vi.fn(),
  mockByokWorkerGenerate: vi.fn(),
  mockByokRelease: vi.fn(),
  mockInsertRoleReceipt: vi.fn(),
}))
vi.mock('@/lib/pariprashna/safety/flag', () => ({
  SAFETY_GATE_FLAG: 'PARIPRASHNA_SAFETY_GATE_ENABLED',
  isSafetyGateEnabled: () => safetyFlagState.on,
}))

// Synthetic test chart ONLY — never the native's real chart
// (`482012f1-710e-4a25-994a-93821f5871aa`), per the repo's test-data law. Auth/DB
// are fully mocked below regardless, so this is belt-and-suspenders.
const CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

// ── auth / flags / config ────────────────────────────────────────────────────
vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(async () => ({ uid: 'route-test-uid' })),
}))
vi.mock('@/lib/config/index', () => ({
  configService: {
    // PARIPRASHNA_ENABLED must be true for `admitRequest` to admit the request
    // at all (the whole route 404s otherwise). The safety gate's own flag is
    // read through the dedicated mock above, not through this getFlag — but it
    // is ALSO branched here (safetyFlagState.on) so both mocking layers agree,
    // in case some future call site starts reading the flag straight off
    // configService instead of through `isSafetyGateEnabled()`.
    getFlag: vi.fn((k: string) => {
      if (k === 'PARIPRASHNA_ENABLED') return true
      if (k === 'PARIPRASHNA_SAFETY_GATE_ENABLED') return safetyFlagState.on
      if (k === 'AI_CONSOLE_BYOK') return byokFlagState.on
      return false
    }),
  },
}))
vi.mock('@/lib/models/runtime_config', () => ({
  getEffectiveModel: vi.fn(async () => 'fake-model'),
}))
vi.mock('@/lib/pariprashna/pipeline/byok_preflight', () => ({
  authenticateByokUser: mockAuthenticateByokUser,
  prepareByokTurn: mockPrepareByokTurn,
}))
vi.mock('@/lib/ai-console/repository', async importOriginal => ({
  ...await importOriginal<typeof import('@/lib/ai-console/repository')>(),
  insertRoleInvocationReceipt: mockInsertRoleReceipt,
}))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({
  authorizeChartAccess: vi.fn(async () => 'view'),
}))

// ── DB ───────────────────────────────────────────────────────────────────────
// `getPool` is exported alongside `query` so the safety module's own
// `defaultSafetyDb().withTransaction(...)` (the audit-row write path,
// `safety/db.ts`) has a fake pool/client to run against instead of failing —
// this is what lets `audit_written` come back `true` in these tests rather
// than the safety module's own (deliberately non-fatal) fallback path.
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params?: unknown[]) => {
    if (/from charts/i.test(sql)) {
      return { rows: [{ id: (params?.[0] as string) ?? CHART, name: 'Route Test Chart', client_id: 'route-test-uid' }] }
    }
    if (/from profiles/i.test(sql)) return { rows: [{ role: 'guest', status: 'active' }] }
    return { rows: [] }
  }),
  getPool: vi.fn(async () => ({
    connect: async () => ({
      query: vi.fn(async () => ({ rows: [] })),
      release: vi.fn(),
    }),
  })),
}))

// ── conversations (no clientConversationId in any scenario here, so only
// `insertConversationWithId` is ever actually called). ──────────────────────
const { mockInsertConversationWithId, mockGetConversation, mockReadinessState } = vi.hoisted(() => ({
  mockInsertConversationWithId: vi.fn(),
  mockGetConversation: vi.fn(),
  mockReadinessState: { value: 'ready' as string },
}))
vi.mock('@/lib/conversations', () => ({
  getConversation: mockGetConversation,
  insertConversationWithId: mockInsertConversationWithId,
}))

// ── shared chart readiness (Jātaka chart workspace): every scenario below runs
// against a Ready chart unless a test says otherwise. ──────────────────────────
vi.mock('@/lib/charts/readiness', () => ({
  getChartReadinessMap: vi.fn(async (ids: string[]) =>
    new Map(ids.map((id) => [id, { state: mockReadinessState.value }])),
  ),
  isDerivedChartReady: (r: { state: string }) => r.state === 'ready',
}))

// ── manifest / orientation (plan-stage front matter; only reached by the
// post-plan-escalation scenario, but the module graph loads unconditionally
// since route.ts imports every stage statically). ───────────────────────────
vi.mock('@/lib/bundle/manifest_reader', () => ({
  loadManifest: vi.fn(async () => ({ fingerprint: 'route-test-manifest-fp' })),
}))
vi.mock('@/lib/retrieval/orientation', () => ({
  buildChartOrientation: vi.fn(async () => null),
}))
vi.mock('@/lib/bundle/bundle_hydrator', () => ({
  hydrateBundle: vi.fn(async () => ({ assets: [], floor_enforced: false })),
}))

// ── planner ──────────────────────────────────────────────────────────────────
const { mockCallPipelinePlanner } = vi.hoisted(() => ({ mockCallPipelinePlanner: vi.fn() }))
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: mockCallPipelinePlanner,
}))
vi.mock('@/lib/pipeline/compiled_floor_adapter', () => ({
  compileFloorForPlan: vi.fn(() => ({
    toolCalls: [],
    mappedPrimitives: [],
    unmappedPrimitives: [],
    compilerIntent: 'general_synthesis',
    compileFailed: false,
  })),
  ensureB11WholeChartReadFloor: vi.fn(() => false),
  ensureDashaContextFloor: vi.fn(() => false),
}))
// Real filter — exercised for real (mirrors route_golden_stream.test.ts); the
// one URI it strips never appears in this file's scenarios.
vi.mock('@/lib/pipeline/no_leakage_filter', () => ({
  filterLeakedCapabilities: (names: readonly string[]) => names.filter((n) => n !== 'marsys://tool/L5/lel_query'),
}))

// ── retrieval dispatch (only reached if a scenario got PAST the safety gate
// and PAST plan-time escalation — none of this file's do, but the modules must
// still resolve at import time since route.ts imports every stage). ─────────
vi.mock('@/lib/retrieval/registry/tool_name_bridge', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/retrieval/registry/tool_name_bridge')>()
  return { ...actual, getToolByName: vi.fn((name: string) => ({ name })) }
})
vi.mock('@/lib/cache/index', () => ({
  createToolCache: vi.fn(() => ({})),
  executeWithCache: vi.fn(async () => ({
    tool_bundle_id: 'tb-unused',
    tool_name: 'unused',
    tool_version: '1.0',
    invocation_params: {},
    results: [],
    served_from_cache: false,
    latency_ms: 1,
    result_hash: 'sha256:unused',
    schema_version: '1.0' as const,
  })),
}))
vi.mock('@/lib/retrieval/qos/dispatch_queue', () => ({
  getSharedQosDispatchQueue: vi.fn(() => ({ submit: async <T,>(task: { run: () => Promise<T> }) => task.run() })),
}))

// ── synthesis prefix builders ────────────────────────────────────────────────
vi.mock('@/lib/pipelines/shared/run_adapter_dispatch', () => ({
  buildConsultSystemContent: vi.fn(() => 'TEST-SYSTEM-CONTENT'),
}))
vi.mock('@/lib/pariprashna/summaries/splice', () => ({
  getConversationSummaryForSplice: vi.fn(async () => null),
}))
vi.mock('@/lib/pariprashna/summaries/assemble', () => ({
  assembleSynthesisPrefix: vi.fn(({ precedingBlock }: { precedingBlock: string }) => precedingBlock),
}))

// ── adapter + agentic loop (no scenario here reaches synthesis, but the
// modules must still import cleanly). ────────────────────────────────────────
async function* emptyAdapterEvents(): AsyncGenerator<Record<string, unknown>> {
  /* no steps — no scenario in this file reaches synthesis */
}
vi.mock('@/lib/providers/dispatcher', () => ({
  getAdapter: vi.fn(() => ({
    getManifest: () => ({ adaptiveToolLoop: true }),
    tools: () => ({ tools: [] }),
    chat: () => emptyAdapterEvents(),
  })),
}))
vi.mock('@/lib/synthesis/agentic_loop', () => ({
  LOOP_CONFIG_BY_PROVIDER: new Proxy({} as Record<string, unknown>, { get: (_t, prop: string) => ({ provider: prop, maxIterations: 8 }) }),
  runAgenticLoop: vi.fn(() => emptyAdapterEvents()),
}))
vi.mock('@/lib/synthesis/mcp_tool_executor', () => ({
  executeMCPTool: vi.fn(async () => ({ results: [] })),
}))

// ── citation gate ────────────────────────────────────────────────────────────
vi.mock('@/lib/synthesis/streaming_citation_validator', () => ({
  validateCitationsForStream: vi.fn(() => ({ gateResult: 'PASS' as const, gateReason: 'test pass', layer1Count: 0, layer2Verified: 0 })),
}))

// ── protocol side channels (ring buffer + stream capture) ────────────────────
vi.mock('@/lib/pariprashna/protocol/ring_buffer', () => ({
  openTurnBuffer: vi.fn(async () => undefined),
  appendBufferedEvent: vi.fn(async () => undefined),
}))
vi.mock('@/lib/pariprashna/protocol/stream_capture', () => ({
  beginTurnCapture: vi.fn(() => undefined),
  captureEvent: vi.fn(async () => undefined),
  endTurnCapture: vi.fn(() => undefined),
}))

// ── provenance / canonical store / samiksha / pricing (never reached by a
// scenario in this file, but imported unconditionally by route.ts's stage
// graph). ─────────────────────────────────────────────────────────────────────
vi.mock('@/lib/pariprashna/provenance/stamp', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/pariprashna/provenance/stamp')>()
  return {
    ...actual,
    computeTurnProvenanceStamp: vi.fn(async () => ({
      build_id: 'build-test',
      priors_version: 'v3',
      formula_versions: { salience_formula_ver: null },
      ranking_config: { mode: 'test' },
      now_context_date: '2026-08-28',
      computed_at: '2026-08-28T00:00:00.000Z',
    })),
    getLastTurnStamp: vi.fn(async () => null),
  }
})
vi.mock('@/lib/pariprashna/store/writer', () => ({
  writeTurn: vi.fn(async (message: Record<string, unknown>) => ({ message_id: message.id as string, parts_written: 0 })),
}))
vi.mock('@/lib/pariprashna/samiksha/capture', () => ({
  captureDetectedCandidates: vi.fn(async () => ({ created: [], skippedExisting: 0, unpaired: 0 })),
}))
vi.mock('@/lib/llm/pricing', () => ({
  getModelPricingSync: vi.fn(() => null),
  computeCostUsd: vi.fn(() => 0),
}))
vi.mock('@/lib/persistence/conversation_writer', () => ({
  writeConversationMessages: vi.fn(async () => ({ verified: true, messageIds: [] })),
}))
vi.mock('@/lib/persistence/pending_streams_writer', () => ({
  createPendingStreamWriter: vi.fn(() => ({ clear: () => undefined })),
}))
vi.mock('@/lib/db/monitoring-write', () => ({
  writeContextAssemblyLog: vi.fn(() => undefined),
}))
vi.mock('@/lib/conversations/title', () => ({
  generateConversationTitle: vi.fn(async () => 'Test Title'),
}))

// ═════════════════════════════════════════════════════════════════════════════
import { POST } from '../route'
import { HS2_FIXED_RESPONSE, SEAL_PENDING_ACKNOWLEDGMENT } from '@/lib/pariprashna/safety/fixed_responses'
import { trackRoleExecutor } from '@/lib/ai-console/execution/tracked-executor'
import { AiConsoleError } from '@/lib/ai-console/errors'
import { admitByokTurn } from '@/lib/limits/byok_admission'

function makeReq(question: string, conversationId?: string): Request {
  return new Request('http://localhost/api/pariprashna', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      chartId: CHART,
      ...(conversationId ? { conversationId } : {}),
      messages: [{ role: 'user', parts: [{ type: 'text', text: question }] }],
    }),
  })
}

/** The minimal planner-outcome shape `plan_stage.ts` needs to keep going. */
function planOutcome(toolNames: string[]) {
  return {
    outcome: 'plan' as const,
    plan: {
      query_class: 'holistic',
      domains: [],
      forward_looking: false,
      tool_calls: toolNames.map((tool_name) => ({ tool_name, params: {}, token_budget: 400, priority: 1 as const, reason: 'test' })),
    },
  }
}

/** Decode the SSE body into typed event objects, alongside the raw text. */
function parseSse(text: string): Array<Record<string, unknown>> {
  return text
    .split('\n')
    .filter((l) => l.startsWith('data: '))
    .map((l) => JSON.parse(l.slice(6)) as Record<string, unknown>)
}

async function runRoute(question: string): Promise<{ status: number; contentType: string | null; text: string; events: Array<Record<string, unknown>> }> {
  const res = await POST(makeReq(question))
  const text = await res.text()
  return { status: res.status, contentType: res.headers.get('content-type'), text, events: parseSse(text) }
}

beforeEach(() => {
  safetyFlagState.on = false
  byokFlagState.on = false
  mockCallPipelinePlanner.mockReset()
  mockAuthenticateByokUser.mockReset().mockResolvedValue({
    user: { uid: 'route-test-uid' }, profile: { role: 'guest' },
  })
  mockByokSynthStream.mockReset()
  mockByokWorkerGenerate.mockReset()
  mockByokRelease.mockReset()
  mockInsertRoleReceipt.mockReset().mockResolvedValue(undefined)
  const roleExecutor = (role: 'synthesizer' | 'planner' | 'deep_planner' | 'worker') => ({
    descriptor: { role, providerId: 'openai', connectionId: `connection-${role}`, modelId: `model-${role}` },
    generate: role === 'worker' ? mockByokWorkerGenerate : vi.fn(),
    stream: role === 'synthesizer' ? mockByokSynthStream : vi.fn(),
  })
  mockPrepareByokTurn.mockReset().mockResolvedValue({
    kind: 'byok', selection: { kind: 'default' }, plan: {}, snapshotId: crypto.randomUUID(),
    safeSnapshot: { roles: { synthesizer: { kind: 'provider_model', providerId: 'openai',
      connectionId: 'connection', modelId: 'model' } } },
    executors: { synthesizer: roleExecutor('synthesizer'), planner: roleExecutor('planner'),
      deep_planner: roleExecutor('deep_planner'), worker: roleExecutor('worker') },
    displayModelId: 'model', releaseAdmission: mockByokRelease,
  })
  mockInsertConversationWithId.mockReset().mockResolvedValue(undefined)
  mockGetConversation.mockReset().mockResolvedValue(null)
  mockReadinessState.value = 'ready'
})

afterEach(() => {
  safetyFlagState.on = false
  byokFlagState.on = false
})

describe('AI Console BYOK request boundary', () => {
  it.each([
    ['owner or chart denial', 'AI_PERMISSION_DENIED', 400],
    ['stale or broken selection', 'AI_CHOICE_BROKEN', 400],
    ['snapshot failure', 'AI_EXECUTION_FAILED', 400],
    ['admission refusal', 'AI_RATE_LIMITED', 429],
  ] as const)('returns a safe zero-call error for %s', async (_name, code, status) => {
    byokFlagState.on = true
    mockPrepareByokTurn.mockRejectedValueOnce(new AiConsoleError(code))
    const response = await POST(new Request('http://localhost/api/pariprashna', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chartId: CHART, ai_selection: { kind: 'default' },
        messages: [{ id: 'user-1', role: 'user', parts: [{ type: 'text', text: 'Question' }] }] }),
    }))
    expect(response.status).toBe(status)
    expect(await response.json()).toMatchObject({ code })
    expect(mockCallPipelinePlanner).not.toHaveBeenCalled()
    expect(mockByokSynthStream).not.toHaveBeenCalled()
    expect(mockInsertRoleReceipt).not.toHaveBeenCalled()
  })

  it('rejects oversized assistant/tool history before atomic preflight or any executor exists', async () => {
    byokFlagState.on = true
    const response = await POST(new Request('http://localhost/api/pariprashna', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        chartId: CHART,
        ai_selection: { kind: 'default' },
        messages: [
          { id: 'assistant-1', role: 'assistant', parts: [
            { type: 'reasoning', text: 'r'.repeat(1_100_000) },
            { type: 'dynamic-tool', toolName: 'fixture', toolCallId: 'call-1', state: 'output-available',
              input: { query: 'q'.repeat(500_000) }, output: { text: 'o'.repeat(500_000) } },
          ] },
          { id: 'user-1', role: 'user', parts: [{ type: 'text', text: 'short question' }] },
        ],
      }),
    }))

    expect(response.status).toBe(400)
    expect(await response.json()).toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(mockPrepareByokTurn).not.toHaveBeenCalled()
    expect(mockCallPipelinePlanner).not.toHaveBeenCalled()
  })

  it.each(['direct', 'custom'] as const)(
    'maps the exact four %s role executors through an actual successful POST',
    async (configurationKind) => {
      byokFlagState.on = true
      mockCallPipelinePlanner.mockResolvedValue(planOutcome([]))
      mockByokSynthStream.mockImplementation(() => new ReadableStream({
        start(controller) {
          controller.enqueue({ type: 'text_delta', text: 'routed answer' })
          controller.enqueue({ type: 'finish', finishReason: 'stop', retryCount: 0,
            usage: { inputTokens: 1, outputTokens: 2, totalTokens: 3 } })
          controller.close()
        },
      }))
      const baseRuntime = await mockPrepareByokTurn.getMockImplementation()!({})
      const directTarget = { providerId: 'openai', connectionId: 'connection-direct', modelId: 'model-direct' }
      const directExecutor = <T extends { descriptor: Record<string, unknown> }>(executor: T): T => ({
        ...executor, descriptor: { ...executor.descriptor, ...directTarget },
      })
      const executors = configurationKind === 'direct'
        ? {
            synthesizer: directExecutor(baseRuntime.executors.synthesizer),
            planner: directExecutor(baseRuntime.executors.planner),
            deep_planner: directExecutor(baseRuntime.executors.deep_planner),
            worker: directExecutor(baseRuntime.executors.worker),
          }
        : baseRuntime.executors
      mockPrepareByokTurn.mockResolvedValueOnce({ ...baseRuntime, executors })

      const response = await POST(new Request('http://localhost/api/pariprashna', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ chartId: CHART, ai_selection: { kind: 'default' },
          messages: [{ id: 'user-1', role: 'user', parts: [{ type: 'text', text: 'Question' }] }] }),
      }))
      expect(response.status).toBe(200)
      await expect(response.text()).resolves.toContain('routed answer')

      const injected = mockCallPipelinePlanner.mock.calls[0][10]
      expect(injected).toMatchObject({
        plannerExecutor: executors.planner,
        deepPlannerExecutor: executors.deep_planner,
        workerExecutor: executors.worker,
        maxOutputTokens: 16_384,
      })
      expect(mockByokSynthStream).toHaveBeenCalledWith(expect.objectContaining({
        abortSignal: expect.any(AbortSignal), maxOutputTokens: 16_384,
      }))
      const descriptors = [executors.synthesizer.descriptor, executors.planner.descriptor,
        executors.deep_planner.descriptor, executors.worker.descriptor]
      expect(descriptors.map(descriptor => descriptor.role).sort()).toEqual([
        'deep_planner', 'planner', 'synthesizer', 'worker',
      ])
      if (configurationKind === 'direct') {
        expect(new Set(descriptors.map(descriptor =>
          `${descriptor.providerId}:${descriptor.connectionId}:${descriptor.modelId}`))).toHaveLength(1)
      } else {
        expect(new Set(descriptors.map(descriptor => descriptor.modelId))).toHaveLength(4)
      }
    },
  )

  it('aborts the exact Synthesizer when the response reader cancels and starts no later Worker work', async () => {
    byokFlagState.on = true
    mockCallPipelinePlanner.mockResolvedValue(planOutcome([]))
    const delegateCancel = vi.fn()
    let synthSignal: AbortSignal | undefined
    mockByokSynthStream.mockImplementation((input: { abortSignal?: AbortSignal }) => {
      synthSignal = input.abortSignal
      return new ReadableStream({
        async pull(controller) {
          await new Promise(resolve => setTimeout(resolve, 100))
          controller.enqueue({ type: 'finish', finishReason: 'stop', retryCount: 0,
            usage: { inputTokens: 1, outputTokens: 0, totalTokens: 1 } })
          controller.close()
        },
        cancel: delegateCancel,
      })
    })
    const delegate = {
      descriptor: { role: 'synthesizer' as const, providerId: 'openai' as const,
        connectionId: 'connection-synthesizer', modelId: 'model-synthesizer' },
      generate: vi.fn(), stream: mockByokSynthStream,
    }
    const trackedSynth = trackRoleExecutor(delegate, {
      userId: 'route-test-uid', snapshotId: '30000000-0000-4000-8000-000000000003',
    })
    const baseRuntime = await mockPrepareByokTurn.getMockImplementation()!({})
    mockPrepareByokTurn.mockResolvedValueOnce({ ...baseRuntime,
      executors: { ...baseRuntime.executors, synthesizer: trackedSynth } })
    const response = await POST(new Request('http://localhost/api/pariprashna', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chartId: CHART, ai_selection: { kind: 'default' },
        messages: [{ id: 'user-1', role: 'user', parts: [{ type: 'text', text: 'Question' }] }] }),
    }))
    const reader = response.body!.getReader()
    await reader.read()
    await vi.waitFor(() => expect(mockByokSynthStream).toHaveBeenCalledOnce())
    await reader.cancel()

    expect(synthSignal?.aborted).toBe(true)
    expect(delegateCancel).toHaveBeenCalledOnce()
    expect(mockByokWorkerGenerate).not.toHaveBeenCalled()
    expect(mockByokRelease).toHaveBeenCalled()
    expect(mockInsertRoleReceipt).toHaveBeenCalledTimes(2)
    expect(mockInsertRoleReceipt.mock.calls[0][0]).toMatchObject({
      role: 'synthesizer', phase: 'start', status: 'started',
    })
    expect(mockInsertRoleReceipt.mock.calls[1][0]).toMatchObject({
      role: 'synthesizer', phase: 'terminal', status: 'cancelled',
      invocationId: mockInsertRoleReceipt.mock.calls[0][0].invocationId,
    })
  })

  it('holds admission until delegate cancellation and the cancelled terminal receipt both finish', async () => {
    byokFlagState.on = true
    mockCallPipelinePlanner.mockResolvedValue(planOutcome([]))
    let resolveDelegateCleanup!: () => void
    let resolveTerminalReceipt!: () => void
    const delegateCleanup = new Promise<void>(resolve => { resolveDelegateCleanup = resolve })
    const terminalReceipt = new Promise<void>(resolve => { resolveTerminalReceipt = resolve })
    const delegateCancel = vi.fn(() => delegateCleanup)
    mockByokSynthStream.mockReturnValue(new ReadableStream({ cancel: delegateCancel }))
    mockInsertRoleReceipt.mockImplementation((receipt: { phase: string }) =>
      receipt.phase === 'terminal' ? terminalReceipt : Promise.resolve())

    const routeAdmission = admitByokTurn({ userId: 'deferred-cleanup-user', questionChars: 1 })
    const siblingAdmission = admitByokTurn({ userId: 'deferred-cleanup-user', questionChars: 1 })
    expect(routeAdmission.allowed).toBe(true)
    expect(siblingAdmission.allowed).toBe(true)
    if (!routeAdmission.allowed || !siblingAdmission.allowed) throw new Error('admission fixture failed')
    const releaseAdmission = vi.fn(routeAdmission.release)
    const delegate = {
      descriptor: { role: 'synthesizer' as const, providerId: 'openai' as const,
        connectionId: 'connection-synthesizer', modelId: 'model-synthesizer' },
      generate: vi.fn(), stream: mockByokSynthStream,
    }
    const trackedSynth = trackRoleExecutor(delegate, {
      userId: 'route-test-uid', snapshotId: '30000000-0000-4000-8000-000000000003',
    })
    const baseRuntime = await mockPrepareByokTurn.getMockImplementation()!({})
    mockPrepareByokTurn.mockResolvedValueOnce({ ...baseRuntime, releaseAdmission,
      executors: { ...baseRuntime.executors, synthesizer: trackedSynth } })

    try {
      const response = await POST(new Request('http://localhost/api/pariprashna', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ chartId: CHART, ai_selection: { kind: 'default' },
          messages: [{ id: 'user-1', role: 'user', parts: [{ type: 'text', text: 'Question' }] }] }),
      }))
      const reader = response.body!.getReader()
      await reader.read()
      await vi.waitFor(() => expect(mockByokSynthStream).toHaveBeenCalledOnce())
      let cancelSettled = false
      const cancelling = reader.cancel().then(() => { cancelSettled = true })

      await vi.waitFor(() => expect(delegateCancel).toHaveBeenCalledOnce())
      expect(cancelSettled).toBe(false)
      expect(releaseAdmission).not.toHaveBeenCalled()
      expect(admitByokTurn({ userId: 'deferred-cleanup-user', questionChars: 1 }))
        .toMatchObject({ allowed: false })

      resolveDelegateCleanup()
      await vi.waitFor(() => expect(mockInsertRoleReceipt).toHaveBeenCalledTimes(2))
      expect(cancelSettled).toBe(false)
      expect(releaseAdmission).not.toHaveBeenCalled()

      resolveTerminalReceipt()
      await cancelling
      expect(releaseAdmission).toHaveBeenCalledOnce()
      expect(mockByokWorkerGenerate).not.toHaveBeenCalled()
      const replacement = admitByokTurn({ userId: 'deferred-cleanup-user', questionChars: 1 })
      expect(replacement.allowed).toBe(true)
      if (replacement.allowed) replacement.release()
    } finally {
      resolveDelegateCleanup()
      resolveTerminalReceipt()
      routeAdmission.release()
      siblingAdmission.release()
    }
  })
})

describe('V3-E-055: PPR-12 safety gate (WEB door /api/pariprashna) — reaches the SSE wire', () => {
  it('parses the authoritative camelCase conversationId and reuses that existing conversation row', async () => {
    const existingConversationId = '33333333-3333-4333-8333-333333333333'
    safetyFlagState.on = true
    mockGetConversation.mockResolvedValue({ id: existingConversationId, chart_id: CHART, user_id: 'route-test-uid', module: 'consume' })

    const response = await POST(makeReq('I want to kill myself.', existingConversationId))
    const events = parseSse(await response.text())

    expect(events.find(event => event.type === 'turn.open')?.conversation_id).toBe(existingConversationId)
    expect(mockGetConversation).toHaveBeenCalledWith({ id: existingConversationId, userId: 'route-test-uid', isSuperAdmin: false })
    expect(mockInsertConversationWithId).not.toHaveBeenCalled()
  })

  it('flag OFF (the shipped default): a crisis question runs untouched, no safety block on the wire', async () => {
    safetyFlagState.on = false
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))

    const { status, text, events } = await runRoute('I want to kill myself.')

    expect(status).toBe(200)
    expect(mockCallPipelinePlanner).toHaveBeenCalled()
    expect(text).not.toContain(HS2_FIXED_RESPONSE.split('\n')[0])
    expect(events.some((e) => typeof e.code === 'string' && (e.code as string).startsWith('safety_decision:'))).toBe(false)
  })

  it('1) HS-2 hard stop: the fixed refusal text renders verbatim on THIS route\'s SSE wire, with the safety_decision judgment flag alongside it', async () => {
    safetyFlagState.on = true
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))

    const { status, contentType, text, events } = await runRoute('I want to kill myself.')

    expect(status).toBe(200)
    expect(contentType).toContain('event-stream')
    // The fixed prose's first line, verbatim, on the RAW SSE wire bytes — this
    // is the literal `res.text()` the client reads, not a parsed/decoded
    // convenience. Checked against the first line only because the raw wire
    // JSON-escapes the embedded newlines (`\n` → the two characters `\` `n`);
    // the FULL string, byte-for-byte via JSON decoding, is asserted right
    // below via the parsed `block.commit` event.
    expect(text).toContain(HS2_FIXED_RESPONSE.split('\n')[0])

    // The typed events prove the WIRE FORMAT: a `flag` event carrying the
    // judgment flag alongside a `block.open`/`block.delta`/`block.commit` triad
    // carrying the fixed text — this route's equivalent of `judgment_flags`.
    const flagEvent = events.find((e) => e.type === 'flag' && e.code === 'safety_decision:hard_stop')
    expect(flagEvent).toBeDefined()
    const commit = events.find((e) => e.type === 'block.commit' && e.block_id === 'safety-hs2-0')
    expect(commit).toBeDefined()
    expect(commit!.text).toBe(HS2_FIXED_RESPONSE)

    // PRE-DISPATCH: "a blocked class must never build a retrieval plan."
    expect(mockCallPipelinePlanner).not.toHaveBeenCalled()

    // The turn still closes cleanly — a designed answer, not a fault.
    const close = events.find((e) => e.type === 'turn.close')
    expect(close?.status).toBe('ok')
  })

  it('2) seal path: HS-4 mortality-window question renders the seal acknowledgment on the SSE wire, with its judgment flag', async () => {
    safetyFlagState.on = true
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))

    const { status, text, events } = await runRoute('When will I die?')

    expect(status).toBe(200)
    // First line on the raw wire bytes (see the HS-2 test above for why only
    // the first line — JSON-escaped embedded newlines); the full string,
    // byte-for-byte, is asserted below via the parsed `block.commit` event.
    expect(text).toContain(SEAL_PENDING_ACKNOWLEDGMENT.split('\n')[0])

    const flagEvent = events.find((e) => e.type === 'flag' && e.code === 'safety_decision:seal_pending_signoff')
    expect(flagEvent).toBeDefined()
    const commit = events.find((e) => e.type === 'block.commit' && e.block_id === 'safety-seal-0')
    expect(commit).toBeDefined()
    expect(commit!.text).toBe(SEAL_PENDING_ACKNOWLEDGMENT)

    // No reading leaves this call — the planner never ran, exactly as the
    // pre-plan hard-stop case.
    expect(mockCallPipelinePlanner).not.toHaveBeenCalled()
    const close = events.find((e) => e.type === 'turn.close')
    expect(close?.status).toBe('ok')
  })

  it('3) post-plan escalation (route.ts:186-199): a longevity capability the wording hid escalates AFTER the planner ran, and seals before evidence/synthesis', async () => {
    safetyFlagState.on = true
    // The QUESTION is clean — the pre-plan classification will be `proceed`.
    // The PLAN reveals `ganita_ayurdaya_get` (a MORTALITY_CLASS capability),
    // which `reclassifyAfterPlan` escalates to `seal_pending_signoff`.
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['ganita_ayurdaya_get', 'chart_facts_query']))

    const { status, text, events } = await runRoute('Tell me about my constitution.')

    expect(status).toBe(200)
    // The planner DID run — the escalation is only visible after it.
    expect(mockCallPipelinePlanner).toHaveBeenCalledTimes(1)

    // Two DISTINCT safety_decision flags on the wire: the pre-plan `proceed`
    // (emitted by runSafetyPolicyGate, since the flag is on) and the post-plan
    // escalation (emitted by route.ts's own escalation branch, `detail:
    // 'escalated at plan time'`) — proving the branch that is unique to this
    // route, not just the gate's own pre-plan behaviour, actually ran.
    const preFlag = events.find((e) => e.type === 'flag' && e.code === 'safety_decision:proceed')
    expect(preFlag).toBeDefined()
    const escalationFlag = events.find(
      (e) => e.type === 'flag' && e.code === 'safety_decision:seal_pending_signoff' && e.detail === 'escalated at plan time',
    )
    expect(escalationFlag).toBeDefined()

    // The seal acknowledgment (not the HS-2 text) is what actually reaches the
    // wire, on the route's own post-plan block id.
    expect(text).toContain(SEAL_PENDING_ACKNOWLEDGMENT.split('\n')[0])
    const commit = events.find((e) => e.type === 'block.commit' && e.block_id === 'safety-postplan-0')
    expect(commit).toBeDefined()
    expect(commit!.text).toBe(SEAL_PENDING_ACKNOWLEDGMENT)

    // Nothing past the plan closure ran: no activity/tool-dispatch phase event
    // and no second, later block (evidence + synthesis never started).
    expect(events.some((e) => e.type === 'activity.upsert')).toBe(false)
    const blockCommits = events.filter((e) => e.type === 'block.commit')
    expect(blockCommits).toHaveLength(1)

    const close = events.find((e) => e.type === 'turn.close')
    expect(close?.status).toBe('ok')
  })

  it('4) THE FLOOR: an ordinary benign question is completely unaffected with the flag ON (no safety flag, no refusal text)', async () => {
    safetyFlagState.on = true
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))

    const { status, text, events } = await runRoute('What does my chart say about my career this year?')

    expect(status).toBe(200)
    expect(mockCallPipelinePlanner).toHaveBeenCalledTimes(1)
    expect(text).not.toContain(HS2_FIXED_RESPONSE.split('\n')[0])
    expect(text).not.toContain(SEAL_PENDING_ACKNOWLEDGMENT.split('\n')[0])
    // `proceed` is still recorded (every turn gets a decision — G3-A reads it),
    // but never a refusal action.
    const flagEvent = events.find((e) => e.type === 'flag' && typeof e.code === 'string' && (e.code as string).startsWith('safety_decision:'))
    expect(flagEvent?.code).toBe('safety_decision:proceed')
  })
})

describe('Jātaka chart workspace — Paripraśna write gates', () => {
  const ARCHIVED_ID = '0f0e0d0c-0b0a-4908-8706-050403020100'

  function continueReq(question: string): Request {
    return new Request('http://localhost/api/pariprashna', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        chartId: CHART,
        conversationId: ARCHIVED_ID,
        messages: [{ role: 'user', parts: [{ type: 'text', text: question }] }],
      }),
    })
  }

  it.each(['building', 'needs-rebuild', 'not-built', 'partially-built', 'failed'])(
    'a %s chart lets the planner work with the data currently available',
    async (state) => {
      mockReadinessState.value = state
      mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
      const { events } = await runRoute('What does my chart say about work?')
      expect(events.some((e) => e.code === 'CHART_RECOMPUTE_REQUIRED')).toBe(false)
      expect(mockCallPipelinePlanner).toHaveBeenCalledTimes(1)
      expect(mockInsertConversationWithId).toHaveBeenCalledTimes(1)
    },
  )

  it('a correction-archived conversation refuses a new turn with CONVERSATION_ARCHIVED_READ_ONLY', async () => {
    mockGetConversation.mockResolvedValue({
      id: ARCHIVED_ID,
      chart_id: CHART,
      user_id: 'route-test-uid',
      module: 'consume',
      archived_at: '2026-09-27T10:00:00Z',
      archive_reason: 'chart_details_changed',
      archived_chart_snapshot: { birth_date: '1984-02-05', birth_time: '10:43:00' },
      archived_by_run_id: null,
    })
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    const res = await POST(continueReq('Continue please'))
    const events = parseSse(await res.text())
    expect(events.some((e) => e.code === 'CONVERSATION_ARCHIVED_READ_ONLY')).toBe(true)
    expect(mockCallPipelinePlanner).not.toHaveBeenCalled()
    expect(mockInsertConversationWithId).not.toHaveBeenCalled()
  })

  it('a manually archived conversation cannot be continued', async () => {
    mockGetConversation.mockResolvedValue({
      id: ARCHIVED_ID,
      chart_id: CHART,
      user_id: 'route-test-uid',
      module: 'consume',
      archived_at: '2026-09-27T10:00:00Z',
      archive_reason: null,
      archived_chart_snapshot: null,
      archived_by_run_id: null,
    })
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    const res = await POST(continueReq('Continue please'))
    const events = parseSse(await res.text())
    expect(events.some((e) => e.code === 'CONVERSATION_ARCHIVED_READ_ONLY')).toBe(false)
    expect(mockCallPipelinePlanner).not.toHaveBeenCalled()
  })
})

describe('Jātaka chart workspace — persistence-boundary race (deterministic)', () => {
  // The refused turn's terminal sequence: the refusal error, then exactly one
  // turn.close with status 'error' as the last event — never a successful finish.
  function expectRefusedTerminal(events: Array<Record<string, unknown>>) {
    const errorIdx = events.findIndex((e) => e.type === 'error' && e.code === 'CONVERSATION_ARCHIVED_READ_ONLY')
    const closes = events.filter((e) => e.type === 'turn.close')
    expect(closes).toHaveLength(1)
    expect(closes[0].status).toBe('error')
    expect(events.at(-1)?.type).toBe('turn.close')
    expect(errorIdx).toBeGreaterThanOrEqual(0)
    expect(errorIdx).toBeLessThan(events.length - 1)
  }

  // These turns must reach persistence, so synthesis produces real text.
  async function useTextSynthesis(text = 'Your tenth house is strongly placed this year.') {
    const { runAgenticLoop } = await import('@/lib/synthesis/agentic_loop')
    vi.mocked(runAgenticLoop).mockImplementation(async function* () {
      yield { type: 'text_delta', text }
    } as never)
    return () => vi.mocked(runAgenticLoop).mockImplementation((() => emptyAdapterEvents()) as never)
  }

  it('a turn admitted before a chart correction cannot persist after the correction commits', async () => {
    const restoreSynthesis = await useTextSynthesis()
    const { query } = await import('@/lib/db/client')
    const { writeConversationMessages } = await import('@/lib/persistence/conversation_writer')
    const { writeTurn } = await import('@/lib/pariprashna/store/writer')
    const dbQuery = vi.mocked(query)
    const original = dbQuery.getMockImplementation()!
    let corrected = false
    dbQuery.mockImplementation(async (sql: string, params?: unknown[]) => {
      // After the correction commits, the conversation row carries the lock.
      if (corrected && /FROM conversations WHERE id/.test(sql)) {
        return { rows: [{ chart_id: CHART, archive_reason: 'chart_details_changed' }] } as never
      }
      return original(sql, params)
    })
    vi.mocked(writeConversationMessages).mockClear()
    vi.mocked(writeTurn).mockClear()

    // 1. Start under the old state: admission passes (Ready, active conversation).
    mockReadinessState.value = 'ready'
    // 2. The correction commits while the turn is planning/streaming.
    mockCallPipelinePlanner.mockImplementation(async () => {
      corrected = true
      mockReadinessState.value = 'building'
      return planOutcome(['chart_facts_query'])
    })

    try {
      const { events } = await runRoute('What does my chart say about work?')

      expect(mockInsertConversationWithId).toHaveBeenCalled() // admitted before the correction
      expect(mockCallPipelinePlanner).toHaveBeenCalled()
      // 3. The final write is refused at the persistence boundary.
      expect(vi.mocked(writeConversationMessages)).not.toHaveBeenCalled()
      expect(vi.mocked(writeTurn)).not.toHaveBeenCalled()
      expect(events.some((e) => e.code === 'CONVERSATION_ARCHIVED_READ_ONLY')).toBe(true)
      expectRefusedTerminal(events)
    } finally {
      dbQuery.mockImplementation(original)
      mockCallPipelinePlanner.mockReset()
      mockReadinessState.value = 'ready'
      restoreSynthesis()
    }
  })

  it('a correction that commits after the first guard (during the history write) still stops the canonical write', async () => {
    const restoreSynthesis = await useTextSynthesis()
    const { query } = await import('@/lib/db/client')
    const { writeConversationMessages } = await import('@/lib/persistence/conversation_writer')
    const { writeTurn } = await import('@/lib/pariprashna/store/writer')
    const dbQuery = vi.mocked(query)
    const original = dbQuery.getMockImplementation()!
    let corrected = false
    dbQuery.mockImplementation(async (sql: string, params?: unknown[]) => {
      if (corrected && /FROM conversations WHERE id/.test(sql)) {
        return { rows: [{ chart_id: CHART, archive_reason: 'chart_details_changed' }] } as never
      }
      return original(sql, params)
    })
    vi.mocked(writeTurn).mockClear()
    // The correction commits while the history rows are being written — after the
    // write-through's first guard has already passed.
    vi.mocked(writeConversationMessages).mockImplementationOnce(async () => {
      corrected = true
      mockReadinessState.value = 'building'
      return { verified: true, messageIds: [], missingMessageIds: [] }
    })
    mockReadinessState.value = 'ready'
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))

    try {
      const { events } = await runRoute('What does my chart say about work?')

      expect(vi.mocked(writeConversationMessages)).toHaveBeenCalled()
      expect(vi.mocked(writeTurn)).not.toHaveBeenCalled()
      expect(events.some((e) => e.code === 'CONVERSATION_ARCHIVED_READ_ONLY')).toBe(true)
      expectRefusedTerminal(events)
    } finally {
      dbQuery.mockImplementation(original)
      mockReadinessState.value = 'ready'
      restoreSynthesis()
    }
  })

  const PREDICTIVE_TEXT =
    'You will likely receive a promotion at work between March 2027 and June 2027, during the Jupiter period.'

  it('a turn with a prediction captures it for review when nothing changes (control)', async () => {
    const restoreSynthesis = await useTextSynthesis(PREDICTIVE_TEXT)
    const { captureDetectedCandidates } = await import('@/lib/pariprashna/samiksha/capture')
    vi.mocked(captureDetectedCandidates).mockClear()
    mockReadinessState.value = 'ready'
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    try {
      await runRoute('When will my career rise?')
      expect(vi.mocked(captureDetectedCandidates)).toHaveBeenCalled()
    } finally {
      restoreSynthesis()
    }
  })

  it('a correction that commits during the canonical write stops the Samīkṣā capture', async () => {
    const restoreSynthesis = await useTextSynthesis(PREDICTIVE_TEXT)
    const { query } = await import('@/lib/db/client')
    const { writeTurn } = await import('@/lib/pariprashna/store/writer')
    const { captureDetectedCandidates } = await import('@/lib/pariprashna/samiksha/capture')
    const dbQuery = vi.mocked(query)
    const original = dbQuery.getMockImplementation()!
    const originalWriteTurn = vi.mocked(writeTurn).getMockImplementation()
    let corrected = false
    dbQuery.mockImplementation(async (sql: string, params?: unknown[]) => {
      if (corrected && /FROM conversations WHERE id/.test(sql)) {
        return { rows: [{ chart_id: CHART, archive_reason: 'chart_details_changed' }] } as never
      }
      return original(sql, params)
    })
    vi.mocked(captureDetectedCandidates).mockClear()
    // The correction commits while the assistant row is being written.
    vi.mocked(writeTurn).mockImplementation((async (message: { role: string }, parts: unknown) => {
      if (message.role === 'assistant') {
        corrected = true
        mockReadinessState.value = 'building'
      }
      return originalWriteTurn ? originalWriteTurn(message as never, parts as never) : (undefined as never)
    }) as never)
    mockReadinessState.value = 'ready'
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    try {
      const { events } = await runRoute('When will my career rise?')
      expect(corrected).toBe(true)
      expect(vi.mocked(captureDetectedCandidates)).not.toHaveBeenCalled()
      expect(events.some((e) => e.code === 'CONVERSATION_ARCHIVED_READ_ONLY')).toBe(true)
      expectRefusedTerminal(events)
    } finally {
      dbQuery.mockImplementation(original)
      if (originalWriteTurn) vi.mocked(writeTurn).mockImplementation(originalWriteTurn)
      mockReadinessState.value = 'ready'
      restoreSynthesis()
    }
  })

  it('a turn whose history write fails ends with an error terminal, never ok', async () => {
    const restoreSynthesis = await useTextSynthesis()
    const { writeConversationMessages } = await import('@/lib/persistence/conversation_writer')
    vi.mocked(writeConversationMessages).mockResolvedValueOnce({ verified: false, messageIds: [], missingMessageIds: ['m'] })
    mockReadinessState.value = 'ready'
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    try {
      const { events } = await runRoute('What does my chart say about work?')
      const commit = events.find((e) => e.type === 'turn.commit')
      expect(commit?.status).toBe('error')
      const closes = events.filter((e) => e.type === 'turn.close')
      expect(closes).toHaveLength(1)
      expect(closes[0].status).toBe('error')
      expect(events.at(-1)?.type).toBe('turn.close')
    } finally {
      restoreSynthesis()
    }
  })

  it('without a correction the same turn persists normally', async () => {
    const restoreSynthesis = await useTextSynthesis()
    const { writeConversationMessages } = await import('@/lib/persistence/conversation_writer')
    vi.mocked(writeConversationMessages).mockClear()
    mockReadinessState.value = 'ready'
    mockCallPipelinePlanner.mockResolvedValue(planOutcome(['chart_facts_query']))
    const { events } = await runRoute('What does my chart say about work?')
    expect(vi.mocked(writeConversationMessages)).toHaveBeenCalled()
    expect(events.some((e) => e.code === 'CONVERSATION_ARCHIVED_READ_ONLY')).toBe(false)
    expect(events.filter((e) => e.type === 'turn.close').map((e) => e.status)).toEqual(['ok'])
    restoreSynthesis()
  })
})
