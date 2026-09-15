/**
 * register_prashna_ask.test.ts — prashna_ask MCP tool contract tests (W6, Task 7).
 *
 * Vitest — not jest. Registers against a plain mock server object (captures the
 * handler directly, matching muhurta_finder.ts's own testable structural-typing
 * pattern) rather than a real transport, so these tests exercise the handler's
 * OWN logic (durable-create-first return, entitlement gate, depth rejection)
 * plus the exported work-driving recovery function used by prashna_status.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  registerPrashnaAskTool,
  resumeManagedPrashnaJob,
  __resetManagedPrashnaSchedulerForTests,
  prashnaAskJobs,
  type PrashnaAskRegisteringServer,
} from './register_prashna_ask.js'
import * as bridge from '../lib/prashna_ask_bridge.js'
import { __setManagedPrashnaJobStoreForTests, InMemoryManagedPrashnaJobStoreForTests } from '../lib/managed_prashna_jobs.js'
import type { Principal } from '../types.js'

const CHART_ID = 'aaaaaaaa-1111-4000-8000-000000000001'
const testJobs = new InMemoryManagedPrashnaJobStoreForTests()

function makePrincipal(): Principal {
  return { user_uid: 'user-1', key_id: 'key-1', role: 'guest' }
}

function makeMockServer(): { server: PrashnaAskRegisteringServer; getHandler: () => (args: unknown, extra: unknown) => Promise<unknown> } {
  let handler: ((args: unknown, extra: unknown) => Promise<unknown>) | null = null
  const server: PrashnaAskRegisteringServer = {
    tool: (_name, _description, _schema, cb) => {
      handler = cb as unknown as (args: unknown, extra: unknown) => Promise<unknown>
    },
  }
  return { server, getHandler: () => {
    if (!handler) throw new Error('tool() was never called')
    return handler
  } }
}

function makeExtra(progressToken?: string) {
  return {
    signal: new AbortController().signal,
    requestId: 'req-1',
    sendNotification: vi.fn().mockResolvedValue(undefined),
    sendRequest: vi.fn(),
    _meta: progressToken !== undefined ? { progressToken } : undefined,
  }
}

describe('registerPrashnaAskTool', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    testJobs.clear()
    __resetManagedPrashnaSchedulerForTests()
    __setManagedPrashnaJobStoreForTests(testJobs)
  })

  it('rejects a request carrying a depth field', async () => {
    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const handler = getHandler()

    const result = (await handler(
      { chart_id: CHART_ID, question: 'q', response_format: 'standard', depth: 'retrieval' },
      makeExtra()
    )) as { isError?: boolean; structuredContent: { error: string } }

    expect(result.isError).toBe(true)
    expect(result.structuredContent.error).toContain('no `depth` parameter')
  })

  it('rejects whitespace-only and oversized questions before durable creation', async () => {
    const create = vi.spyOn(testJobs, 'create')
    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const handler = getHandler()

    for (const question of ['   ', 'x'.repeat(4001)]) {
      const result = await handler(
        { chart_id: CHART_ID, question, response_format: 'standard' },
        makeExtra(),
      ) as { isError?: boolean }
      expect(result.isError).toBe(true)
    }
    expect(create).not.toHaveBeenCalled()
  })

  it('accepts the C-1 signature without scope_tuple (optional)', async () => {
    vi.spyOn(bridge, 'callPrashnaAskEngine').mockImplementation(
      () => new Promise(() => { /* never resolves in this test */ })
    )
    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const handler = getHandler()

    const result = (await handler(
      { chart_id: CHART_ID, question: 'q', response_format: 'standard' },
      makeExtra()
    )) as { isError?: boolean; structuredContent: { job_id: string; status: string } }

    expect(result.isError).toBeUndefined()
    expect(result.structuredContent.status).toBe('pending')
    expect(typeof result.structuredContent.job_id).toBe('string')
  })

  it('does not start the engine when durable job creation fails', async () => {
    const engine = vi.spyOn(bridge, 'callPrashnaAskEngine')
    vi.spyOn(testJobs, 'create').mockRejectedValueOnce(new Error('store unavailable'))
    const logged = vi.spyOn(console, 'error').mockImplementation(() => undefined)
    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const result = await getHandler()(
      { chart_id: CHART_ID, question: 'q', response_format: 'standard' },
      makeExtra(),
    ) as { isError?: boolean; structuredContent: { error: string } }
    expect(result.isError).toBe(true)
    expect(result.structuredContent.error).toContain('MANAGED_JOB_STORE_UNAVAILABLE')
    expect(engine).not.toHaveBeenCalled()
    logged.mockRestore()
  })

  it('returns a job handle immediately, without waiting for the engine call to resolve', async () => {
    let resolveEngine: (v: unknown) => void = () => {}
    const enginePromise = new Promise((resolve) => { resolveEngine = resolve })
    vi.spyOn(bridge, 'callPrashnaAskEngine').mockImplementation(() => enginePromise as never)

    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const handler = getHandler()

    let handlerResolved = false
    const handlerPromise = handler(
      { chart_id: CHART_ID, question: 'q', response_format: 'standard' },
      makeExtra()
    ).then((r) => { handlerResolved = true; return r })

    // Flush microtasks without resolving the engine call.
    await Promise.resolve()
    await Promise.resolve()

    expect(handlerResolved).toBe(true)
    const result = await handlerPromise as { structuredContent: { status: string } }
    expect(result.structuredContent.status).toBe('pending')
    expect(bridge.callPrashnaAskEngine).not.toHaveBeenCalled()

    // Engine still hasn't resolved — cleanup.
    resolveEngine({ ok: true, trace_id: 't', chart_id: CHART_ID, outcome: 'plan' })
  })

  it("rejects a request whose resolved MCP profile is 'consult'", async () => {
    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'consult')
    const handler = getHandler()

    const result = (await handler(
      { chart_id: CHART_ID, question: 'q', response_format: 'standard' },
      makeExtra()
    )) as { isError?: boolean; structuredContent: { error: string } }

    expect(result.isError).toBe(true)
    expect(result.structuredContent.error).toContain('consult')
  })

  it("allows 'compact' profile to proceed", async () => {
    vi.spyOn(bridge, 'callPrashnaAskEngine').mockImplementation(
      () => new Promise(() => { /* never resolves */ })
    )
    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'compact')
    const handler = getHandler()

    const result = (await handler(
      { chart_id: CHART_ID, question: 'q', response_format: 'standard' },
      makeExtra()
    )) as { isError?: boolean; structuredContent: { status: string } }

    expect(result.isError).toBeUndefined()
    expect(result.structuredContent.status).toBe('pending')
  })

  it('delivers in-request progress while the work-driving recovery call remains open', async () => {
    const planResult = {
      ok: true as const,
      trace_id: 't1',
      chart_id: CHART_ID,
      outcome: 'plan' as const,
      query_class: 'dasha_timing',
      query_intent_summary: 'summary',
      completeness: {
        status: 'complete' as const,
        tools_dispatched: [],
        unserved_tools: [],
        unresolved_tools: [],
        stripped_leaked_capabilities: [],
        cap_tripped: null,
      },
      judgment_flags: [],
      results: [],
    }
    vi.spyOn(bridge, 'callPrashnaAskEngine').mockResolvedValue(planResult)

    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const handler = getHandler()
    const extra = makeExtra('progress-token-1')

    const result = await handler(
      { chart_id: CHART_ID, question: 'q', response_format: 'standard' }, extra,
    ) as { structuredContent: { job_id: string } }
    expect(result.structuredContent.job_id).toBeTypeOf('string')
    await vi.waitFor(() => expect(extra.sendNotification).toHaveBeenCalledTimes(2))

    const terminalCall = extra.sendNotification.mock.calls[1][0]
    expect(terminalCall.method).toBe('notifications/progress')
    expect(terminalCall.params.progressToken).toBe('progress-token-1')
    expect(terminalCall.params.progress).toBe(100)
    expect(terminalCall.params.message).toContain('"outcome":"plan"')
  })

  it('forwards a supplied scope_tuple to callPrashnaAskEngine (W6.1 fix-cycle)', async () => {
    const engineSpy = vi.spyOn(bridge, 'callPrashnaAskEngine').mockResolvedValue({
      ok: true,
      trace_id: 't1',
      chart_id: CHART_ID,
      outcome: 'plan',
      query_class: 'holistic',
      query_intent_summary: 'test',
      completeness: {
        status: 'complete',
        tools_dispatched: [],
        unserved_tools: [],
        unresolved_tools: [],
        stripped_leaked_capabilities: [],
        cap_tripped: null,
      },
      judgment_flags: [],
      results: [],
    })

    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const handler = getHandler()
    const extra = makeExtra(undefined)

    const scopeTuple = {
      intent: 'domain_assessment',
      domains: ['career'],
      width: 'standard',
      depth: 'standard',
      horizon: 'near',
      intervention: 'none',
      entitlement: 'native',
    }
    const result = await handler(
      { chart_id: CHART_ID, question: 'career timing?', response_format: 'standard', scope_tuple: scopeTuple },
      extra
    ) as { structuredContent: { job_id: string } }
    await resumeManagedPrashnaJob(result.structuredContent.job_id, makePrincipal())
    expect(engineSpy.mock.calls[0][0].scopeTuple).toEqual(scopeTuple)
  })

  it('reaches durable "complete" status after work-driving recovery resolves', async () => {
    const planResult = {
      ok: true as const,
      trace_id: 't2',
      chart_id: CHART_ID,
      outcome: 'plan' as const,
      query_class: 'dasha_timing',
      query_intent_summary: 'summary',
      completeness: {
        status: 'complete' as const,
        tools_dispatched: [],
        unserved_tools: [],
        unresolved_tools: [],
        stripped_leaked_capabilities: [],
        cap_tripped: null,
      },
      judgment_flags: [],
      results: [],
    }
    vi.spyOn(bridge, 'callPrashnaAskEngine').mockResolvedValue(planResult)

    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const handler = getHandler()

    const result = (await handler(
      { chart_id: CHART_ID, question: 'q', response_format: 'standard' },
      makeExtra()
    )) as { structuredContent: { job_id: string } }
    const jobId = result.structuredContent.job_id
    await vi.waitFor(async () => {
      expect((await prashnaAskJobs.get(makePrincipal(), jobId))?.status).toBe('complete')
    })
    expect((await prashnaAskJobs.get(makePrincipal(), jobId))?.result).toMatchObject({
      ...planResult,
      persistence: { status: 'managed_job', job_id: jobId },
    })
  })

  it('calls JobRegistry.updateProgress with a human-readable message and pct for each interim progress event', async () => {
    const updateProgressSpy = vi.spyOn(prashnaAskJobs, 'updateProgress')
    let capturedOnProgress: ((p: {
      tools_dispatched_count: number
      cap_ceiling: { maxCalls: number; maxWallClockMs: number }
      elapsed_ms: number
      last_tool: string
    }) => void) | undefined
    let resolveEngine: (v: unknown) => void = () => {}
    const enginePromise = new Promise((resolve) => { resolveEngine = resolve })
    vi.spyOn(bridge, 'callPrashnaAskEngine').mockImplementation((_input, onProgress) => {
      capturedOnProgress = onProgress
      return enginePromise as never
    })

    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const handler = getHandler()

    const handlerResult = (await handler(
      { chart_id: CHART_ID, question: 'q', response_format: 'standard' },
      makeExtra()
    )) as { structuredContent: { job_id: string } }
    const jobId = handlerResult.structuredContent.job_id

    const recovery = resumeManagedPrashnaJob(jobId, makePrincipal())
    await vi.waitFor(() => expect(updateProgressSpy).toHaveBeenCalled())

    // Initial "started" update happens before the engine fetch begins.
    expect(updateProgressSpy).toHaveBeenCalledWith(
      expect.objectContaining({ user_uid: 'user-1', key_id: 'key-1' }),
      jobId,
      expect.any(String),
      expect.objectContaining({ pct: 0 }),
    )

    await vi.waitFor(() => expect(capturedOnProgress).toBeTypeOf('function'))
    capturedOnProgress?.({
      tools_dispatched_count: 3,
      cap_ceiling: { maxCalls: 10, maxWallClockMs: 120_000 },
      elapsed_ms: 12_400,
      last_tool: 'get_dashas',
    })

    await vi.waitFor(() => {
      expect(updateProgressSpy.mock.calls.some((call) => call[3]?.message.includes('3/~10 tool calls made'))).toBe(true)
    })
    const lastCall = updateProgressSpy.mock.calls[updateProgressSpy.mock.calls.length - 1]
    expect(lastCall[1]).toBe(jobId)
    expect(lastCall[3].message).toContain('3/~10 tool calls made')
    expect(lastCall[3].message).toContain('12.4s elapsed')
    expect(lastCall[3].pct).toBeGreaterThan(0)
    expect(lastCall[3].pct).toBeLessThan(100)

    resolveEngine({ ok: true, trace_id: 't5', chart_id: CHART_ID, outcome: 'plan' })
    await recovery
    updateProgressSpy.mockRestore()
  })

  it('caps local engine concurrency and drains queued durable jobs', async () => {
    const resolvers: Array<(value: unknown) => void> = []
    const engine = vi.spyOn(bridge, 'callPrashnaAskEngine').mockImplementation(
      () => new Promise((resolve) => { resolvers.push(resolve) }) as never,
    )
    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const handler = getHandler()

    const handles = await Promise.all(Array.from({ length: 4 }, (_, index) => handler(
      { chart_id: CHART_ID, question: `queued-${index}`, response_format: 'standard' },
      makeExtra(),
    )))
    expect(handles).toHaveLength(4)
    await vi.waitFor(() => expect(engine).toHaveBeenCalledTimes(2))

    const terminal = {
      ok: true as const, trace_id: 'bounded-worker', chart_id: CHART_ID, outcome: 'plan' as const,
      query_class: 'holistic', query_intent_summary: 'bounded',
      completeness: {
        status: 'complete' as const, tools_dispatched: [], unserved_tools: [], unresolved_tools: [],
        stripped_leaked_capabilities: [], empty_result_tools: [], cap_tripped: null,
      },
      judgment_flags: [], results: [],
    }
    resolvers[0](terminal)
    await vi.waitFor(() => expect(engine).toHaveBeenCalledTimes(3))
    resolvers[1](terminal)
    await vi.waitFor(() => expect(engine).toHaveBeenCalledTimes(4))
    resolvers[2](terminal)
    resolvers[3](terminal)
    await vi.waitFor(async () => expect(await testJobs.get(makePrincipal(), (
      handles[3] as { structuredContent: { job_id: string } }
    ).structuredContent.job_id)).toMatchObject({ status: 'complete' }))
  })

  it('reaches durable "failed" status when the work-driving engine call errors', async () => {
    vi.spyOn(bridge, 'callPrashnaAskEngine').mockResolvedValue({
      ok: false,
      trace_id: 't3',
      error: { class: 'orchestrator_error', message: 'planner fault' },
    })

    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const handler = getHandler()

    const result = (await handler(
      { chart_id: CHART_ID, question: 'q', response_format: 'standard' },
      makeExtra()
    )) as { structuredContent: { job_id: string } }
    const jobId = result.structuredContent.job_id
    await vi.waitFor(async () => {
      expect((await prashnaAskJobs.get(makePrincipal(), jobId))?.status).toBe('failed')
    })
    expect((await prashnaAskJobs.get(makePrincipal(), jobId))?.error).toContain('planner fault')
  })

  it('retries a bridge-generated ambiguous failure only after lease expiry and then succeeds', async () => {
    const engine = vi.spyOn(bridge, 'callPrashnaAskEngine')
      .mockResolvedValueOnce({
        ok: false, trace_id: '',
        error: { class: 'internal', message: 'Platform unreachable: reset', retryable: true },
      })
      .mockResolvedValueOnce({
        ok: true, trace_id: 'retry-success', chart_id: CHART_ID, outcome: 'plan',
        query_class: 'holistic', query_intent_summary: 'retry', reading: 'recovered', chart_header: null,
        completeness: {
          status: 'complete', tools_dispatched: [], unserved_tools: [], unresolved_tools: [],
          stripped_leaked_capabilities: [], empty_result_tools: [], cap_tripped: null,
        },
        judgment_flags: [], results: [],
      })
    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const result = await getHandler()(
      { chart_id: CHART_ID, question: 'q', response_format: 'standard' }, makeExtra(),
    ) as { structuredContent: { job_id: string } }

    await vi.waitFor(async () => expect(
      await prashnaAskJobs.get(makePrincipal(), result.structuredContent.job_id),
    ).toMatchObject({
      status: 'running', attempt_count: 1,
      progress: { message: expect.stringContaining('retry waits for lease expiry') },
    }))
    expect(engine).toHaveBeenCalledTimes(1)

    testJobs.expireLease(result.structuredContent.job_id)
    await resumeManagedPrashnaJob(result.structuredContent.job_id, makePrincipal())
    expect((await prashnaAskJobs.get(makePrincipal(), result.structuredContent.job_id))?.status)
      .toBe('complete')
    expect(engine).toHaveBeenCalledTimes(2)
    expect((await prashnaAskJobs.get(makePrincipal(), result.structuredContent.job_id))?.attempt_count).toBe(2)
  })

  it('turns an oversized successful envelope into an explicit terminal storage failure without rerunning', async () => {
    const engine = vi.spyOn(bridge, 'callPrashnaAskEngine').mockResolvedValue({
      ok: true, trace_id: 'oversize', chart_id: CHART_ID, outcome: 'plan',
      query_class: 'holistic', query_intent_summary: 'oversized', reading: 'complete', chart_header: null,
      completeness: {
        status: 'complete', tools_dispatched: [], unserved_tools: [], unresolved_tools: [],
        stripped_leaked_capabilities: [], empty_result_tools: [], cap_tripped: null,
      },
      judgment_flags: [], results: [],
    })
    vi.spyOn(testJobs, 'complete').mockRejectedValueOnce(new Error('MANAGED_JOB_RESULT_TOO_LARGE'))
    const { server, getHandler } = makeMockServer()
    registerPrashnaAskTool(server, makePrincipal(), 'full')
    const result = await getHandler()(
      { chart_id: CHART_ID, question: 'q', response_format: 'standard' }, makeExtra(),
    ) as { structuredContent: { job_id: string } }

    await vi.waitFor(async () => expect(
      (await prashnaAskJobs.get(makePrincipal(), result.structuredContent.job_id))?.status,
    ).toBe('failed'))
    expect((await prashnaAskJobs.get(makePrincipal(), result.structuredContent.job_id))?.error)
      .toContain('MANAGED_JOB_RESULT_TOO_LARGE')
    expect(engine).toHaveBeenCalledTimes(1)
  })
})
