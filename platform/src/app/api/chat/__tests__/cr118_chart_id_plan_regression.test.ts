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
const { byokFlag, prepareByokTurn, getConversationSelection } = vi.hoisted(() => ({
  byokFlag: { on: false }, prepareByokTurn: vi.fn(), getConversationSelection: vi.fn(),
}))
const { chartPermission } = vi.hoisted(() => ({ chartPermission: { value: 'view' as 'view' | 'deny' } }))
const integration = vi.hoisted(() => ({
  actualDispatch: false,
  conversation: null as null | { chart_id: string },
  pendingOnEvent: vi.fn(), pendingOnTextDelta: vi.fn(), pendingClear: vi.fn(async () => undefined),
  writeMessages: vi.fn(async () => ({ verified: true, messageIds: [crypto.randomUUID()] })),
  legacyChat: vi.fn(),
}))

// Jātaka chart workspace: every reading door admits only a Ready chart (shared
// readiness gate) — this harness exercises a Ready chart.
vi.mock('@/lib/charts/readiness', () => ({
  getChartReadinessMap: vi.fn(async (ids: string[]) => new Map(ids.map((id) => [id, { state: 'ready' }]))),
  isDerivedChartReady: (r: { state: string }) => r.state === 'ready',
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
    if (/from profiles/i.test(sql)) return { rows: [{ role: 'super_admin', status: 'active' }] }
    return { rows: [] }
  }),
}))

vi.mock('@/lib/auth/authorizeChartAccess', () => ({
  authorizeChartAccess: vi.fn(async () => chartPermission.value),
}))

vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(async () => integration.conversation),
  insertConversationWithId: vi.fn(async () => undefined),
  updateConversationTitle: vi.fn(async () => undefined),
}))

vi.mock('@/lib/persistence/pending_streams_writer', () => ({
  createPendingStreamWriter: vi.fn(() => ({ onEvent: integration.pendingOnEvent,
    onTextDelta: integration.pendingOnTextDelta, clear: integration.pendingClear })),
}))
vi.mock('@/lib/persistence/conversation_writer', () => ({ writeConversationMessages: integration.writeMessages }))
vi.mock('@/lib/synthesis/streaming_citation_validator', () => ({
  validateCitationsForStream: vi.fn(() => ({ gateResult: 'PASS', gateReason: 'test',
    layer1Count: 0, layer2Verified: 0, layer2Leaked: 0 })),
}))
vi.mock('@/lib/providers/dispatcher', () => ({
  getAdapter: vi.fn(() => ({
    getManifest: () => ({ adaptiveToolLoop: false }),
    tools: () => ({ tools: [] }),
    chat: integration.legacyChat,
  })),
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
  configService: { getFlag: vi.fn((name: string) => name === 'AI_CONSOLE_BYOK' && byokFlag.on) },
}))
vi.mock('@/lib/pariprashna/pipeline/byok_preflight', () => ({ prepareByokTurn }))
vi.mock('@/lib/ai-console/repository', () => ({ getConversationSelection }))

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
  dispatchSpy: vi.fn(async (context: unknown) => {
    void context
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    })
  }),
}))
vi.mock('@/lib/pipelines/shared', async importOriginal => {
  const actual = await importOriginal<typeof import('@/lib/pipelines/shared')>()
  return { ...actual, runAdapterDispatch: (context: Parameters<typeof actual.runAdapterDispatch>[0]) =>
    integration.actualDispatch ? actual.runAdapterDispatch(context) : dispatchSpy(context) }
})

import { POST } from '../consult/route'
import { AiConsoleError } from '@/lib/ai-console/errors'

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
  byokFlag.on = false
  chartPermission.value = 'view'
  integration.actualDispatch = false
  integration.conversation = null
  integration.pendingOnEvent.mockReset()
  integration.pendingOnTextDelta.mockReset()
  integration.pendingClear.mockReset().mockResolvedValue(undefined)
  integration.writeMessages.mockReset().mockResolvedValue({ verified: true, messageIds: [crypto.randomUUID()] })
  integration.legacyChat.mockReset().mockImplementation(async function* () {
    yield { type: 'text_delta', text: 'legacy answer' }
  })
  prepareByokTurn.mockReset()
  getConversationSelection.mockReset().mockResolvedValue({ kind: 'default' })
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

describe('AI Console BYOK Consult POST boundary', () => {
  it('rejects a chart-authority denial before resolution, role execution, or dispatch', async () => {
    byokFlag.on = true
    chartPermission.value = 'deny'

    const response = await POST(makePost(NATIVE, 'Question'))

    expect(response.status).toBe(403)
    expect(prepareByokTurn).not.toHaveBeenCalled()
    expect(plannerSpy).not.toHaveBeenCalled()
    expect(dispatchSpy).not.toHaveBeenCalled()
  })

  it.each([
    ['stale or broken selection', new AiConsoleError('AI_CHOICE_BROKEN'), 400, 'AI_CHOICE_BROKEN'],
    ['snapshot failure', new AiConsoleError('AI_EXECUTION_FAILED'), 400, 'AI_EXECUTION_FAILED'],
    ['admission refusal', new AiConsoleError('AI_RATE_LIMITED'), 429, 'AI_RATE_LIMITED'],
  ] as const)('returns a safe zero-call response for %s', async (_label, failure, status, code) => {
    byokFlag.on = true
    prepareByokTurn.mockRejectedValueOnce(failure)

    const response = await POST(makePost(NATIVE, 'Question'))

    expect(response.status).toBe(status)
    expect(await response.json()).toMatchObject({ code })
    expect(plannerSpy).not.toHaveBeenCalled()
    expect(dispatchSpy).not.toHaveBeenCalled()
  })

  it('rejects oversized assistant/tool history before snapshot, admission, planning, or dispatch', async () => {
    byokFlag.on = true
    const response = await POST(new Request('http://localhost/api/chat/consult', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chartId: NATIVE, messages: [
        { id: 'assistant-1', role: 'assistant', parts: [
          { type: 'reasoning', text: 'r'.repeat(1_100_000) },
          { type: 'dynamic-tool', toolName: 'fixture', toolCallId: 'call-1', state: 'output-available',
            input: { query: 'q'.repeat(500_000) }, output: { text: 'o'.repeat(500_000) } },
        ] },
        { id: 'user-1', role: 'user', parts: [{ type: 'text', text: 'short question' }] },
      ] }),
    }))

    expect(response.status).toBe(400)
    expect(await response.json()).toMatchObject({ code: 'AI_EXECUTION_FAILED' })
    expect(prepareByokTurn).not.toHaveBeenCalled()
    expect(plannerSpy).not.toHaveBeenCalled()
    expect(dispatchSpy).not.toHaveBeenCalled()
  })

  it('passes four distinct custom-role executors through planner and successful dispatch', async () => {
    byokFlag.on = true
    const roleExecutor = (role: 'synthesizer' | 'planner' | 'deep_planner' | 'worker') => ({
      descriptor: { role, providerId: 'openai', connectionId: `connection-${role}`, modelId: `model-${role}` },
      generate: vi.fn(), stream: vi.fn(),
    })
    const executors = { synthesizer: roleExecutor('synthesizer'), planner: roleExecutor('planner'),
      deep_planner: roleExecutor('deep_planner'), worker: roleExecutor('worker') }
    const releaseAdmission = vi.fn()
    prepareByokTurn.mockResolvedValue({
      kind: 'byok', selection: { kind: 'explicit', choice: { kind: 'custom_configuration',
        configurationId: '30000000-0000-4000-8000-000000000003' } }, plan: {},
      safeSnapshot: { roles: { synthesizer: { kind: 'provider_model', providerId: 'openai',
        connectionId: 'connection-synthesizer', modelId: 'model-synthesizer' } } },
      snapshotId: '30000000-0000-4000-8000-000000000004', executors,
      displayModelId: 'model-synthesizer', releaseAdmission,
    })
    const response = await POST(makePost(NATIVE, 'Question'))
    expect(response.status).toBe(200)
    expect(prepareByokTurn).toHaveBeenCalledOnce()
    const byokPlanner = plannerSpy.mock.calls[0][10]
    expect(byokPlanner).toMatchObject({ plannerExecutor: executors.planner,
      deepPlannerExecutor: executors.deep_planner, workerExecutor: executors.worker,
      maxOutputTokens: 16_384 })
    expect(dispatchSpy).toHaveBeenCalledOnce()
    expect(dispatchSpy.mock.calls[0][0]).toMatchObject({ byokRuntime: { executors } })
  })

  it.each(['direct', 'custom'] as const)(
    'streams an actual successful %s runtime response and releases after on-finish',
    async (configurationKind) => {
      byokFlag.on = true
      integration.actualDispatch = true
      const conversationId = crypto.randomUUID()
      integration.conversation = { chart_id: NATIVE }
      const synthStream = vi.fn(() => new ReadableStream({
        start(controller) {
          controller.enqueue({ type: 'text_delta', text: 'routed consult answer' })
          controller.enqueue({ type: 'finish', finishReason: 'stop', retryCount: 0,
            usage: { inputTokens: 1, outputTokens: 3, totalTokens: 4 } })
          controller.close()
        },
      }))
      const target = (role: 'synthesizer' | 'planner' | 'deep_planner' | 'worker') => ({
        descriptor: { role, providerId: 'openai',
          connectionId: configurationKind === 'direct' ? 'connection-direct' : `connection-${role}`,
          modelId: configurationKind === 'direct' ? 'model-direct' : `model-${role}` },
        generate: vi.fn(), stream: role === 'synthesizer' ? synthStream : vi.fn(),
      })
      const executors = { synthesizer: target('synthesizer'), planner: target('planner'),
        deep_planner: target('deep_planner'), worker: target('worker') }
      const releaseAdmission = vi.fn()
      prepareByokTurn.mockResolvedValueOnce({
        kind: 'byok', selection: { kind: 'default' }, plan: {}, snapshotId: crypto.randomUUID(),
        safeSnapshot: { roles: { synthesizer: { kind: 'provider_model', providerId: 'openai',
          connectionId: executors.synthesizer.descriptor.connectionId,
          modelId: executors.synthesizer.descriptor.modelId } } },
        executors, displayModelId: executors.synthesizer.descriptor.modelId, releaseAdmission,
      })

      const response = await POST(new Request('http://localhost/api/chat/consult', {
        method: 'POST', headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ chartId: NATIVE, conversationId,
          messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text: 'Question' }] }] }),
      }))
      expect(response.status).toBe(200)
      const wire = await response.text()
      expect(wire).toContain('routed consult answer')
      expect(wire).toContain('data-persistence')
      expect(wire).toContain('[DONE]')
      expect(synthStream).toHaveBeenCalledWith(expect.objectContaining({
        abortSignal: expect.any(AbortSignal), maxOutputTokens: 16_384,
      }))
      expect(releaseAdmission).toHaveBeenCalledOnce()
      expect(integration.writeMessages).toHaveBeenCalledOnce()
      expect(dispatchSpy).not.toHaveBeenCalled()
    },
  )

  it('waits for actual Consult reader-cancel cleanup before releasing admission', async () => {
    byokFlag.on = true
    integration.actualDispatch = true
    integration.conversation = { chart_id: NATIVE }
    let resolveCleanup!: () => void
    const cleanup = new Promise<void>(resolve => { resolveCleanup = resolve })
    const delegateCancel = vi.fn(() => cleanup)
    let synthSignal: AbortSignal | undefined
    const synthStream = vi.fn((input: { abortSignal?: AbortSignal }) => {
      synthSignal = input.abortSignal
      return new ReadableStream({ cancel: delegateCancel })
    })
    const executor = (role: 'synthesizer' | 'planner' | 'deep_planner' | 'worker') => ({
      descriptor: { role, providerId: 'openai', connectionId: `connection-${role}`, modelId: `model-${role}` },
      generate: vi.fn(), stream: role === 'synthesizer' ? synthStream : vi.fn(),
    })
    const executors = { synthesizer: executor('synthesizer'), planner: executor('planner'),
      deep_planner: executor('deep_planner'), worker: executor('worker') }
    const releaseAdmission = vi.fn()
    prepareByokTurn.mockResolvedValueOnce({ kind: 'byok', selection: { kind: 'default' }, plan: {},
      snapshotId: crypto.randomUUID(), safeSnapshot: { roles: { synthesizer: { kind: 'provider_model',
        providerId: 'openai', connectionId: 'connection-synthesizer', modelId: 'model-synthesizer' } } },
      executors, displayModelId: 'model-synthesizer', releaseAdmission })

    const response = await POST(new Request('http://localhost/api/chat/consult', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chartId: NATIVE, conversationId: crypto.randomUUID(),
        messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text: 'Question' }] }] }),
    }))
    const reader = response.body!.getReader()
    await reader.read()
    await vi.waitFor(() => expect(synthStream).toHaveBeenCalledOnce())
    let settled = false
    const cancelling = reader.cancel().then(() => { settled = true })
    await vi.waitFor(() => expect(delegateCancel).toHaveBeenCalledOnce())
    expect(synthSignal?.aborted).toBe(true)
    expect(settled).toBe(false)
    expect(releaseAdmission).not.toHaveBeenCalled()
    resolveCleanup()
    await cancelling
    expect(releaseAdmission).toHaveBeenCalledOnce()
  })

  it('releases admission for an actual stream setup failure without exposing internals', async () => {
    byokFlag.on = true
    integration.actualDispatch = true
    integration.pendingOnEvent.mockImplementationOnce(() => { throw new Error('private setup failure') })
    const synthStream = vi.fn()
    const releaseAdmission = vi.fn()
    const executor = (role: 'synthesizer' | 'planner' | 'deep_planner' | 'worker') => ({
      descriptor: { role, providerId: 'openai', connectionId: `connection-${role}`, modelId: `model-${role}` },
      generate: vi.fn(), stream: role === 'synthesizer' ? synthStream : vi.fn(),
    })
    const executors = { synthesizer: executor('synthesizer'), planner: executor('planner'),
      deep_planner: executor('deep_planner'), worker: executor('worker') }
    prepareByokTurn.mockResolvedValueOnce({ kind: 'byok', selection: { kind: 'default' }, plan: {},
      snapshotId: crypto.randomUUID(), safeSnapshot: { roles: { synthesizer: { kind: 'provider_model',
        providerId: 'openai', connectionId: 'connection-synthesizer', modelId: 'model-synthesizer' } } },
      executors, displayModelId: 'model-synthesizer', releaseAdmission })

    const response = await POST(makePost(NATIVE, 'Question'))
    const wire = await response.text()
    expect(wire).not.toContain('private setup failure')
    expect(synthStream).not.toHaveBeenCalled()
    expect(releaseAdmission).toHaveBeenCalledOnce()
  })

  it('releases admission after an actual mid-stream writer failure and emits only a safe error', async () => {
    byokFlag.on = true
    integration.actualDispatch = true
    integration.pendingOnTextDelta.mockImplementationOnce(() => { throw new Error('private writer failure') })
    const synthStream = vi.fn(() => new ReadableStream({
      start(controller) {
        controller.enqueue({ type: 'text_delta', text: 'uncommitted answer' })
        controller.enqueue({ type: 'finish', finishReason: 'stop', retryCount: 0,
          usage: { inputTokens: 1, outputTokens: 2, totalTokens: 3 } })
        controller.close()
      },
    }))
    const executor = (role: 'synthesizer' | 'planner' | 'deep_planner' | 'worker') => ({
      descriptor: { role, providerId: 'openai', connectionId: `connection-${role}`, modelId: `model-${role}` },
      generate: vi.fn(), stream: role === 'synthesizer' ? synthStream : vi.fn(),
    })
    const executors = { synthesizer: executor('synthesizer'), planner: executor('planner'),
      deep_planner: executor('deep_planner'), worker: executor('worker') }
    const releaseAdmission = vi.fn()
    prepareByokTurn.mockResolvedValueOnce({ kind: 'byok', selection: { kind: 'default' }, plan: {},
      snapshotId: crypto.randomUUID(), safeSnapshot: { roles: { synthesizer: { kind: 'provider_model',
        providerId: 'openai', connectionId: 'connection-synthesizer', modelId: 'model-synthesizer' } } },
      executors, displayModelId: 'model-synthesizer', releaseAdmission })

    const response = await POST(makePost(NATIVE, 'Question'))
    const wire = await response.text()
    expect(wire).not.toContain('private writer failure')
    expect(wire).toContain('The selected AI could not complete the request')
    expect(releaseAdmission).toHaveBeenCalledOnce()
  })

  it('completes the actual Consult wire and releases admission when on-finish persistence fails', async () => {
    byokFlag.on = true
    integration.actualDispatch = true
    integration.writeMessages.mockRejectedValueOnce(new Error('private persistence failure'))
    const synthStream = vi.fn(() => new ReadableStream({
      start(controller) {
        controller.enqueue({ type: 'text_delta', text: 'answer despite persistence failure' })
        controller.enqueue({ type: 'finish', finishReason: 'stop', retryCount: 0,
          usage: { inputTokens: 1, outputTokens: 2, totalTokens: 3 } })
        controller.close()
      },
    }))
    const executor = (role: 'synthesizer' | 'planner' | 'deep_planner' | 'worker') => ({
      descriptor: { role, providerId: 'openai', connectionId: `connection-${role}`, modelId: `model-${role}` },
      generate: vi.fn(), stream: role === 'synthesizer' ? synthStream : vi.fn(),
    })
    const executors = { synthesizer: executor('synthesizer'), planner: executor('planner'),
      deep_planner: executor('deep_planner'), worker: executor('worker') }
    const releaseAdmission = vi.fn()
    prepareByokTurn.mockResolvedValueOnce({ kind: 'byok', selection: { kind: 'default' }, plan: {},
      snapshotId: crypto.randomUUID(), safeSnapshot: { roles: { synthesizer: { kind: 'provider_model',
        providerId: 'openai', connectionId: 'connection-synthesizer', modelId: 'model-synthesizer' } } },
      executors, displayModelId: 'model-synthesizer', releaseAdmission })

    const response = await POST(makePost(NATIVE, 'Question'))
    const wire = await response.text()
    expect(wire).toContain('answer despite persistence failure')
    expect(wire).not.toContain('private persistence failure')
    expect(wire).toContain('[DONE]')
    expect(releaseAdmission).toHaveBeenCalledOnce()
  })
})

describe('Consult flag-off request and wire golden parity', () => {
  it('preserves the legacy adapter request and AI-SDK event vocabulary', async () => {
    integration.actualDispatch = true
    const conversationId = crypto.randomUUID()
    integration.conversation = { chart_id: NATIVE }

    const response = await POST(new Request('http://localhost/api/chat/consult', {
      method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chartId: NATIVE, conversationId,
        messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text: 'Legacy golden question' }] }] }),
    }))
    const wire = await response.text()
    const eventTypes = wire.split('\n')
      .filter(line => line.startsWith('data: {'))
      .map(line => JSON.parse(line.slice(6)) as { type: string })
      .map(event => event.type)

    expect(response.headers.get('x-vercel-ai-ui-message-stream')).toBe('v1')
    expect(integration.legacyChat).toHaveBeenCalledOnce()
    expect(integration.legacyChat.mock.calls[0][0]).toMatchObject({
      messages: expect.arrayContaining([{ role: 'user', content: 'Legacy golden question' }]),
    })
    expect(eventTypes).toEqual([
      'start', 'data-orientation', 'data-stage', 'data-stage', 'data-stage',
      'data-tool', 'data-tool', 'data-tool', 'data-tool', 'data-stage', 'data-stage',
      'text-start', 'text-delta', 'text-end', 'data-persistence', 'data-judgment-flags',
      'finish', 'data-stage', 'data-observability',
    ])
    expect(wire).toContain('[DONE]')
    expect(prepareByokTurn).not.toHaveBeenCalled()
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
