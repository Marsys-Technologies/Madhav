/**
 * register_prashna_status.test.ts — prashna_status MCP tool contract tests (W6 Part 3).
 *
 * Vitest — not jest. Registers against a plain mock server object (same pattern
 * register_prashna_ask.test.ts uses) and drives the SAME `prashnaAskJobs`
 * module-scoped singleton register_prashna_ask.ts writes to, so these tests
 * exercise the real cross-module contract, not a stand-in registry.
 */
import { describe, it, expect, beforeEach } from 'vitest'
import { registerPrashnaStatusTool, type PrashnaStatusRegisteringServer } from './register_prashna_status.js'
import { prashnaAskJobs } from './register_prashna_ask.js'

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
    const { server, getHandler } = makeMockServer()
    registerPrashnaStatusTool(server)
    handler = getHandler()
  })

  it('returns a clear error for an unknown/expired job_id — not a silent empty object', async () => {
    const result = (await handler({ job_id: 'does-not-exist' })) as {
      isError?: boolean
      structuredContent: { error: string; job_id: string }
    }
    expect(result.isError).toBe(true)
    expect(result.structuredContent.error).toContain('Unknown or expired job_id')
    expect(result.structuredContent.job_id).toBe('does-not-exist')
  })

  it('rejects malformed input (missing job_id)', async () => {
    const result = (await handler({})) as { isError?: boolean; structuredContent: { error: string } }
    expect(result.isError).toBe(true)
    expect(result.structuredContent.error).toContain('Invalid prashna_status input')
  })

  it('returns a meaningful progress payload — not a bare "pending" — for a pending/running job', async () => {
    const job = prashnaAskJobs.create({ chartId: 'chart-1' })
    prashnaAskJobs.updateProgress(job.id, { message: '3/~10 tool calls made, 4.2s elapsed', pct: 42 })

    const result = (await handler({ job_id: job.id })) as {
      structuredContent: {
        status: string
        job_id: string
        elapsed_ms: number
        progress: { message: string; pct: number }
      }
    }
    expect(result.structuredContent.status).toBe('running')
    expect(result.structuredContent.job_id).toBe(job.id)
    expect(typeof result.structuredContent.elapsed_ms).toBe('number')
    expect(result.structuredContent.progress.message).toBe('3/~10 tool calls made, 4.2s elapsed')
    expect(result.structuredContent.progress.pct).toBe(42)
  })

  it('returns a meaningful default progress payload for a job that is still literally "pending" (no progress recorded yet)', async () => {
    const job = prashnaAskJobs.create({ chartId: 'chart-1' })

    const result = (await handler({ job_id: job.id })) as {
      structuredContent: { status: string; progress: { message: string; pct: number } }
    }
    expect(result.structuredContent.status).toBe('pending')
    // Never a bare {status:"pending"} with nothing else — a message + pct are
    // always present, even before the first real progress update lands.
    expect(typeof result.structuredContent.progress.message).toBe('string')
    expect(result.structuredContent.progress.message.length).toBeGreaterThan(0)
    expect(typeof result.structuredContent.progress.pct).toBe('number')
  })

  it('returns the FULL final result (not a summary) once the job is complete', async () => {
    const job = prashnaAskJobs.create({ chartId: 'chart-1' })
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
    prashnaAskJobs.complete(job.id, finalResult)

    const result = (await handler({ job_id: job.id })) as {
      structuredContent: { status: string; result: typeof finalResult }
    }
    expect(result.structuredContent.status).toBe('complete')
    // Full completeness receipt intact — not a pointer telling the caller to
    // look elsewhere.
    expect(result.structuredContent.result).toEqual(finalResult)
    expect(result.structuredContent.result.completeness.status).toBe('complete')
  })

  it('returns the error for a failed job', async () => {
    const job = prashnaAskJobs.create({ chartId: 'chart-1' })
    prashnaAskJobs.fail(job.id, 'planner fault: could not classify scope')

    const result = (await handler({ job_id: job.id })) as {
      structuredContent: { status: string; error: string }
    }
    expect(result.structuredContent.status).toBe('failed')
    expect(result.structuredContent.error).toBe('planner fault: could not classify scope')
  })
})
