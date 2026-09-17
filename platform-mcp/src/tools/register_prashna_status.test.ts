/**
 * register_prashna_status.test.ts — prashna_status MCP tool contract tests (W6 Part 3).
 *
 * Vitest — not jest. Registers against a plain mock server object (same pattern
 * register_prashna_ask.test.ts uses) and drives the SAME `prashnaAskJobs`
 * module-scoped singleton register_prashna_ask.ts writes to, so these tests
 * exercise the real cross-module contract, not a stand-in registry.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { registerPrashnaStatusTool, type PrashnaStatusRegisteringServer } from './register_prashna_status.js'
import { __resetManagedPrashnaSchedulerForTests, prashnaAskJobs } from './register_prashna_ask.js'
import * as bridge from '../lib/prashna_ask_bridge.js'
import { __setManagedPrashnaJobStoreForTests, InMemoryManagedPrashnaJobStoreForTests } from '../lib/managed_prashna_jobs.js'

const principal = { user_uid: 'user-1', key_id: 'key-1', role: 'guest' as const }
const testJobs = new InMemoryManagedPrashnaJobStoreForTests()
const request = {
  inquiry_id: 'eeeeeeee-1111-4000-8000-000000000001',
  question: 'status test', response_format: 'standard' as const,
}

function makeMockServer(): { server: PrashnaStatusRegisteringServer; getHandler: () => (args: unknown) => Promise<unknown> } {
  let handler: ((args: unknown) => Promise<unknown>) | null = null
  const server: PrashnaStatusRegisteringServer = {
    tool: (_name, _description, _schema, cb) => {
      handler = cb as unknown as (args: unknown) => Promise<unknown>
    },
  }
  return {
    server,
    getHandler: () => {
      if (!handler) throw new Error('tool() was never called')
      return handler
    },
  }
}

describe('registerPrashnaStatusTool', () => {
  let handler: (args: unknown) => Promise<unknown>

  beforeEach(() => {
    vi.restoreAllMocks()
    testJobs.clear()
    __resetManagedPrashnaSchedulerForTests()
    __setManagedPrashnaJobStoreForTests(testJobs)
    vi.spyOn(bridge, 'callPrashnaAskEngine').mockImplementation(() => new Promise(() => undefined))
    const { server, getHandler } = makeMockServer()
    registerPrashnaStatusTool(server, principal)
    handler = getHandler()
  })

  it('returns a clear error for an unknown/expired job_id — not a silent empty object', async () => {
    const unknownJobId = 'dddddddd-1111-4000-8000-000000000001'
    const result = (await handler({ job_id: unknownJobId })) as {
      isError?: boolean
      structuredContent: { error: string; job_id: string }
    }
    expect(result.isError).toBe(true)
    expect(result.structuredContent.error).toContain('Unknown or expired job_id')
    expect(result.structuredContent.job_id).toBe(unknownJobId)
  })

  it('rejects malformed input (missing job_id)', async () => {
    const result = (await handler({})) as { isError?: boolean; structuredContent: { error: string } }
    expect(result.isError).toBe(true)
    expect(result.structuredContent.error).toContain('Invalid prashna_status input')
  })

  it('rejects a non-UUID job_id before calling the durable store', async () => {
    const result = (await handler({ job_id: 'does-not-exist' })) as {
      isError?: boolean
      structuredContent: { error: string }
    }
    expect(result.isError).toBe(true)
    expect(result.structuredContent.error).toContain('Invalid prashna_status input')
  })

  it('returns a meaningful progress payload — not a bare "pending" — for a pending/running job', async () => {
    const job = await prashnaAskJobs.create(principal, {
      job_id: crypto.randomUUID(), chart_id: 'aaaaaaaa-1111-4000-8000-000000000001', request,
    })
    const workerId = 'bbbbbbbb-1111-4000-8000-000000000001'
    await prashnaAskJobs.claim(principal, job.job_id, workerId)
    await prashnaAskJobs.updateProgress(principal, job.job_id, workerId, { message: '3/~10 tool calls made, 4.2s elapsed', pct: 42 })

    const result = (await handler({ job_id: job.job_id })) as {
      structuredContent: {
        status: string
        job_id: string
        elapsed_ms: number
        progress: { message: string; pct: number }
      }
    }
    expect(result.structuredContent.status).toBe('running')
    expect(result.structuredContent.job_id).toBe(job.job_id)
    expect(typeof result.structuredContent.elapsed_ms).toBe('number')
    expect(result.structuredContent.progress.message).toBe('3/~10 tool calls made, 4.2s elapsed')
    expect(result.structuredContent.progress.pct).toBe(42)
  })

  it('returns a meaningful default progress payload for a job that is still literally "pending" (no progress recorded yet)', async () => {
    const job = await prashnaAskJobs.create(principal, {
      job_id: crypto.randomUUID(), chart_id: 'aaaaaaaa-1111-4000-8000-000000000001', request,
    })

    const result = (await handler({ job_id: job.job_id })) as {
      structuredContent: { status: string; progress: { message: string; pct: number } }
    }
    expect(result.structuredContent.status).toBe('pending')
    // Never a bare {status:"pending"} with nothing else — a message + pct are
    // always present, even before the first real progress update lands.
    expect(typeof result.structuredContent.progress.message).toBe('string')
    expect(result.structuredContent.progress.message.length).toBeGreaterThan(0)
    expect(typeof result.structuredContent.progress.pct).toBe('number')
  })

  it('lets two stateless status handlers race recovery while only one engine call wins', async () => {
    let resolveEngine: (value: unknown) => void = () => undefined
    const engine = vi.mocked(bridge.callPrashnaAskEngine).mockImplementation(
      () => new Promise((resolve) => { resolveEngine = resolve }) as never,
    )
    const job = await prashnaAskJobs.create(principal, {
      job_id: crypto.randomUUID(), chart_id: 'aaaaaaaa-1111-4000-8000-000000000001', request,
    })
    const first = makeMockServer()
    const second = makeMockServer()
    registerPrashnaStatusTool(first.server, principal)
    registerPrashnaStatusTool(second.server, principal)
    await Promise.all([
      first.getHandler()({ job_id: job.job_id }),
      second.getHandler()({ job_id: job.job_id }),
    ])
    await vi.waitFor(() => expect(engine).toHaveBeenCalledTimes(1))
    resolveEngine({
      ok: true, trace_id: 'cross-instance', chart_id: job.chart_id, outcome: 'plan',
      query_class: 'holistic', query_intent_summary: 'recovered', reading: 'done', chart_header: null,
      completeness: { status: 'complete', tools_dispatched: [], unserved_tools: [], unresolved_tools: [], stripped_leaked_capabilities: [], empty_result_tools: [], cap_tripped: null },
      judgment_flags: [], results: [],
    })
    await vi.waitFor(async () => {
      expect((await prashnaAskJobs.get(principal, job.job_id))?.status).toBe('complete')
    })
  })

  it('returns the FULL final result (not a summary) once the job is complete', async () => {
    const job = await prashnaAskJobs.create(principal, {
      job_id: crypto.randomUUID(), chart_id: 'aaaaaaaa-1111-4000-8000-000000000001', request,
    })
    const workerId = 'bbbbbbbb-1111-4000-8000-000000000002'
    await prashnaAskJobs.claim(principal, job.job_id, workerId)
    const finalResult = {
      ok: true,
      trace_id: 't1',
      chart_id: 'chart-1',
      outcome: 'plan',
      query_class: 'dasha_timing',
      query_intent_summary: 'summary',
      completeness: {
        status: 'complete',
        tools_dispatched: [{ tool_name: 'chart_facts_query', status: 'done', result_count: 1, latency_ms: 5 }],
        unserved_tools: [],
        unresolved_tools: [],
        stripped_leaked_capabilities: [],
        cap_tripped: null,
      },
      judgment_flags: [],
      results: [{ tool_name: 'chart_facts_query', bundle: { results: [{ id: '1' }] } }],
    }
    await prashnaAskJobs.complete(principal, job.job_id, workerId, finalResult as never)

    const result = (await handler({ job_id: job.job_id })) as {
      structuredContent: { status: string; result: typeof finalResult }
    }
    expect(result.structuredContent.status).toBe('complete')
    // Full completeness receipt intact — not a pointer telling the caller to
    // look elsewhere.
    expect(result.structuredContent.result).toEqual(finalResult)
    expect(result.structuredContent.result.completeness.status).toBe('complete')
  })

  it('returns the error for a failed job', async () => {
    const job = await prashnaAskJobs.create(principal, {
      job_id: crypto.randomUUID(), chart_id: 'aaaaaaaa-1111-4000-8000-000000000001', request,
    })
    const workerId = 'bbbbbbbb-1111-4000-8000-000000000003'
    await prashnaAskJobs.claim(principal, job.job_id, workerId)
    await prashnaAskJobs.fail(principal, job.job_id, workerId, 'planner fault: could not classify scope')

    const result = (await handler({ job_id: job.job_id })) as {
      structuredContent: { status: string; error: string }
    }
    expect(result.structuredContent.status).toBe('failed')
    expect(result.structuredContent.error).toBe('planner fault: could not classify scope')
  })
})
