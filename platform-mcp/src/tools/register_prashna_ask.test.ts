/**
 * register_prashna_ask.test.ts — prashna_ask MCP tool contract tests (W6, Task 7).
 *
 * Vitest — not jest. Registers against a plain mock server object (captures the
 * handler directly, matching muhurta_finder.ts's own testable structural-typing
 * pattern) rather than a real transport, so these tests exercise the handler's
 * OWN logic (job-handle-first return, entitlement gate, depth rejection,
 * progress-notification delivery, JobRegistry completion) independent of the
 * MCP SDK's actual stream-lifecycle behavior — see register_prashna_ask.ts's file
 * header for the documented caveat about that lower layer.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { registerPrashnaAskTool, prashnaAskJobs, type PrashnaAskRegisteringServer } from './register_prashna_ask.js'
import * as bridge from '../lib/prashna_ask_bridge.js'
import type { Principal } from '../types.js'

const CHART_ID = 'aaaaaaaa-1111-4000-8000-000000000001'

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

  it('delivers the terminal result via a progress notification, not requiring a separate job_id lookup', async () => {
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

    await handler({ chart_id: CHART_ID, question: 'q', response_format: 'standard' }, extra)

    // Allow the background continuation (fire-and-forget) to run to completion.
    await vi.waitFor(() => {
      expect(extra.sendNotification).toHaveBeenCalledTimes(2) // started + terminal
    })

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
    await handler(
      { chart_id: CHART_ID, question: 'career timing?', response_format: 'standard', scope_tuple: scopeTuple },
      extra
    )

    await vi.waitFor(() => {
      expect(engineSpy).toHaveBeenCalled()
    })
    expect(engineSpy.mock.calls[0][0].scopeTuple).toEqual(scopeTuple)
  })

  it('reaches JobRegistry "complete" status after the background call resolves', async () => {
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

    await vi.waitFor(() => {
      expect(prashnaAskJobs.get(jobId)?.status).toBe('complete')
    })
    expect(prashnaAskJobs.get(jobId)?.result).toEqual(planResult)
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

    // Initial "started" update happened synchronously before the first await.
    expect(updateProgressSpy).toHaveBeenCalledWith(jobId, expect.objectContaining({ pct: 0 }))

    capturedOnProgress?.({
      tools_dispatched_count: 3,
      cap_ceiling: { maxCalls: 10, maxWallClockMs: 120_000 },
      elapsed_ms: 12_400,
      last_tool: 'get_dashas',
    })

    const lastCall = updateProgressSpy.mock.calls[updateProgressSpy.mock.calls.length - 1]
    expect(lastCall[0]).toBe(jobId)
    expect(lastCall[1].message).toContain('3/~10 tool calls made')
    expect(lastCall[1].message).toContain('12.4s elapsed')
    expect(lastCall[1].pct).toBeGreaterThan(0)
    expect(lastCall[1].pct).toBeLessThan(100)

    resolveEngine({ ok: true, trace_id: 't5', chart_id: CHART_ID, outcome: 'plan' })
    updateProgressSpy.mockRestore()
  })

  it('reaches JobRegistry "failed" status when the engine call errors', async () => {
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

    await vi.waitFor(() => {
      expect(prashnaAskJobs.get(jobId)?.status).toBe('failed')
    })
    expect(prashnaAskJobs.get(jobId)?.error).toContain('planner fault')
  })
})
