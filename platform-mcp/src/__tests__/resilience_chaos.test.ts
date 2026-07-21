/**
 * resilience_chaos.test.ts — Task 10: resilience/chaos pass on the
 * platform ↔ platform-mcp seam (the prashna_ask job-handle path).
 *
 * Scope (per the task brief): mocked fault injection at the seam boundary —
 * `fetch` (the only thing `prashna_ask_bridge.ts` calls out over) is stubbed
 * to fail in the four concrete ways this seam can actually fail. No live
 * chaos infrastructure (toxiproxy etc.) exists in this codebase — a
 * `grep -rn "chaos|fault.inject|toxiproxy" platform platform-mcp` before
 * writing this file found one prior-art chaos suite
 * (`platform/src/lib/cache/__tests__/chaos.test.ts`, Redis-cache-focused) and
 * nothing reusable for the MCP↔platform HTTP seam — so this file builds its
 * own mocked-fetch fault points, following that prior art's spirit but this
 * seam's actual shape.
 *
 * These tests drive the REAL production code path end-to-end within the
 * process: `registerPrashnaAskTool`'s handler → the real (unmocked)
 * `callPrashnaAskEngine` bridge → a mocked `global.fetch` → `JobRegistry` →
 * `registerPrashnaStatusTool`'s handler. Only `fetch` is faked; nothing about
 * `prashna_ask_bridge.ts`, `register_prashna_ask.ts`, or `register_prashna_status.ts`
 * is mocked, so a real bug in the wiring between them would surface here even
 * though `register_prashna_ask.test.ts` mocks the bridge itself out.
 *
 * Failure modes covered:
 *   1. MCP connection drop mid-job (background continuation is NOT tied to
 *      the originating request's lifecycle — verified concretely, not assumed).
 *   2. Next.js API 5xx during the engine call.
 *   3. DB pool exhaustion / downstream timeout, surfaced as the bridge's own
 *      `AbortSignal.timeout(ENGINE_CALL_TIMEOUT_MS)` firing.
 *   4. Sidecar timeout surfaced as a completeness `partial`/`wall_clock_cap`
 *      final payload — a completed-but-honest result, not a failure.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { registerPrashnaAskTool, prashnaAskJobs, type PrashnaAskRegisteringServer } from '../tools/register_prashna_ask.js'
import { registerPrashnaStatusTool, type PrashnaStatusRegisteringServer } from '../tools/register_prashna_status.js'
import { __resetPrashnaAskBridgeTokenCacheForTests } from '../lib/prashna_ask_bridge.js'
import type { Principal } from '../types.js'

const CHART_ID = 'aaaaaaaa-1111-4000-8000-000000000099'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function makePrincipal(): Principal {
  return { user_uid: 'user-chaos', key_id: 'key-chaos', role: 'guest' }
}

function makeAskServer(): { server: PrashnaAskRegisteringServer; getHandler: () => (args: unknown, extra: unknown) => Promise<unknown> } {
  let handler: ((args: unknown, extra: unknown) => Promise<unknown>) | null = null
  const server: PrashnaAskRegisteringServer = {
    tool: (_name, _description, _schema, cb) => {
      handler = cb as unknown as (args: unknown, extra: unknown) => Promise<unknown>
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

function makeStatusHandler(): (args: unknown) => Promise<unknown> {
  let handler: ((args: unknown) => Promise<unknown>) | null = null
  const server: PrashnaStatusRegisteringServer = {
    tool: (_name, _description, _schema, cb) => {
      handler = cb
    },
  }
  registerPrashnaStatusTool(server)
  if (!handler) throw new Error('prashna_status tool() was never called')
  return handler
}

function makeExtra(opts: { progressToken?: string; signal?: AbortSignal } = {}) {
  return {
    signal: opts.signal ?? new AbortController().signal,
    requestId: 'req-chaos',
    sendNotification: vi.fn().mockResolvedValue(undefined),
    sendRequest: vi.fn(),
    _meta: opts.progressToken !== undefined ? { progressToken: opts.progressToken } : undefined,
  }
}

/** Builds a mock `Response`-shaped object streaming the given NDJSON lines. */
function makeStreamResponse(
  lines: string[],
  opts: { ok?: boolean; status?: number } = {}
): { ok: boolean; status: number; body: ReadableStream<Uint8Array> } {
  const encoder = new TextEncoder()
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const line of lines) controller.enqueue(encoder.encode(line + '\n'))
      controller.close()
    },
  })
  return { ok: opts.ok ?? true, status: opts.status ?? 200, body }
}

beforeEach(() => {
  mockFetch.mockReset()
  __resetPrashnaAskBridgeTokenCacheForTests()
  process.env['SERVICE_TOKEN'] = 'test-static-token'
  process.env['MCP_INTERNAL_TOKEN'] = 'test-internal-token'
})

afterEach(() => {
  delete process.env['SERVICE_TOKEN']
  delete process.env['MCP_INTERNAL_TOKEN']
})

async function askAndGetJobId(extra: ReturnType<typeof makeExtra>): Promise<string> {
  const { server, getHandler } = makeAskServer()
  registerPrashnaAskTool(server, makePrincipal(), 'full')
  const handler = getHandler()
  const result = (await handler(
    { chart_id: CHART_ID, question: 'chaos probe question', response_format: 'standard' },
    extra
  )) as { structuredContent: { job_id: string; status: string } }
  expect(result.structuredContent.status).toBe('pending')
  return result.structuredContent.job_id
}

describe('resilience/chaos: prashna_ask job-handle path', () => {
  // ── 1. MCP connection drop mid-job ─────────────────────────────────────
  describe('failure mode 1: MCP connection drop mid-job', () => {
    it('completes the background job even after the ORIGINATING request signal aborts', async () => {
      // Simulate a client-dropped connection: an AbortController representing
      // the inbound MCP request, aborted immediately after the job handle is
      // returned — before the engine call resolves.
      const requestAbort = new AbortController()
      let resolveFetch: (v: unknown) => void = () => {}
      mockFetch.mockImplementationOnce(
        () => new Promise((resolve) => { resolveFetch = resolve })
      )

      const extra = makeExtra({ signal: requestAbort.signal })
      const jobId = await askAndGetJobId(extra)

      // The "connection" drops now — nothing in runInBackground/callPrashnaAskEngine
      // is wired to this signal (confirmed by reading both files: neither
      // forwards `extra.signal` into the fetch() call's AbortSignal), so this
      // must have zero effect on the in-flight engine call.
      requestAbort.abort()

      expect(prashnaAskJobs.get(jobId)?.status).toBe('running')

      // Resolve the "engine call" — this proves the background continuation
      // is still alive and drives the job to completion despite the aborted
      // request signal.
      resolveFetch(
        makeStreamResponse([
          JSON.stringify({ ok: true, trace_id: 't-drop', chart_id: CHART_ID, outcome: 'plan' }),
        ])
      )

      await vi.waitFor(() => {
        expect(prashnaAskJobs.get(jobId)?.status).toBe('complete')
      })

      // A NEW "connection" (a fresh prashna_status call, simulating the
      // caller reconnecting) can still retrieve the finished result.
      const statusHandler = makeStatusHandler()
      const statusResult = (await statusHandler({ job_id: jobId })) as {
        structuredContent: { status: string; result: { outcome: string } }
      }
      expect(statusResult.structuredContent.status).toBe('complete')
      expect(statusResult.structuredContent.result.outcome).toBe('plan')
    })

    it(
      'ARCHITECTURAL FINDING (not a bug in this task\'s scope): the SDK\'s per-request ' +
      'StreamableHTTPServerTransport closes the response stream the instant the job-handle ' +
      'result is sent, so a real MCP client has no live channel left for the later terminal ' +
      'notifications/progress push — JobRegistry state (verified above) is the only durable ' +
      'delivery path today; documented in register_prashna_ask.ts\'s file header',
      () => {
        // This test intentionally has no runtime assertion beyond documenting
        // the finding in its title — the file header of register_prashna_ask.ts
        // (read in full for this task) already investigated and recorded this
        // exact caveat, with a citation to the SDK source line range, and
        // flagged it for a native/architecture ruling rather than a code fix
        // here. Re-litigating that investigation is out of this task's scope;
        // this test exists so the finding is discoverable from the test suite,
        // not only from a doc comment.
        expect(true).toBe(true)
      }
    )
  })

  // ── 2. Next.js API 5xx during the engine call ──────────────────────────
  describe('failure mode 2: platform route returns a 5xx', () => {
    it('degrades honestly: bridge → error envelope, job → failed, prashna_status → "failed" with the real message', async () => {
      mockFetch.mockResolvedValueOnce(
        makeStreamResponse(
          [JSON.stringify({ ok: false, trace_id: 't-5xx', error: { class: 'internal', message: 'floor-compile crashed: OOM' } })],
          { ok: false, status: 503 }
        )
      )

      const jobId = await askAndGetJobId(makeExtra())

      await vi.waitFor(() => {
        expect(prashnaAskJobs.get(jobId)?.status).toBe('failed')
      })
      expect(prashnaAskJobs.get(jobId)?.error).toContain('floor-compile crashed: OOM')

      const statusHandler = makeStatusHandler()
      const statusResult = (await statusHandler({ job_id: jobId })) as {
        structuredContent: { status: string; error: string }
      }
      expect(statusResult.structuredContent.status).toBe('failed')
      expect(statusResult.structuredContent.error).toContain('floor-compile crashed: OOM')
    })

    it('degrades honestly when the 5xx body is not even JSON (raw Next.js error page)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        body: null,
        json: () => Promise.reject(new Error('Unexpected token < in JSON')),
      })

      const jobId = await askAndGetJobId(makeExtra())

      await vi.waitFor(() => {
        expect(prashnaAskJobs.get(jobId)?.status).toBe('failed')
      })
      expect(prashnaAskJobs.get(jobId)?.error).toContain('non-JSON')

      const statusHandler = makeStatusHandler()
      const statusResult = (await statusHandler({ job_id: jobId })) as {
        structuredContent: { status: string; error: string }
      }
      expect(statusResult.structuredContent.status).toBe('failed')
    })

    it('never leaves the job stuck "pending"/"running" when fetch itself throws (network-level failure)', async () => {
      mockFetch.mockRejectedValueOnce(new Error('ECONNRESET'))

      const jobId = await askAndGetJobId(makeExtra())

      await vi.waitFor(() => {
        expect(prashnaAskJobs.get(jobId)?.status).toBe('failed')
      })
      expect(prashnaAskJobs.get(jobId)?.error).toContain('Platform unreachable')
      expect(prashnaAskJobs.get(jobId)?.error).toContain('ECONNRESET')
    })
  })

  // ── 3. DB pool exhaustion / downstream timeout ─────────────────────────
  describe('failure mode 3: engine call hangs past the bridge timeout', () => {
    it('passes a real AbortSignal to fetch (the timeout path is wired, not just declared)', async () => {
      mockFetch.mockResolvedValueOnce(
        makeStreamResponse([JSON.stringify({ ok: true, trace_id: 't', chart_id: CHART_ID, outcome: 'plan' })])
      )

      await askAndGetJobId(makeExtra())
      await vi.waitFor(() => expect(mockFetch).toHaveBeenCalledTimes(1))

      const [, opts] = mockFetch.mock.calls[0] as [string, { signal: unknown }]
      expect(opts.signal).toBeInstanceOf(AbortSignal)
    })

    it('degrades honestly when the timeout fires: job → failed with a timeout-shaped error, never stuck pending', async () => {
      // Simulate exactly what happens when `AbortSignal.timeout(ENGINE_CALL_TIMEOUT_MS)`
      // trips inside a real fetch() call: fetch rejects with a DOMException-
      // shaped abort/timeout error. We don't wait out the real 300s timeout —
      // we assert the bridge's existing catch-and-envelope path handles that
      // rejection shape correctly, which is the actual code under test here
      // (the timer itself is native platform behavior, not this codebase's).
      const timeoutError = new Error('The operation was aborted due to timeout')
      timeoutError.name = 'TimeoutError'
      mockFetch.mockRejectedValueOnce(timeoutError)

      const jobId = await askAndGetJobId(makeExtra())

      await vi.waitFor(() => {
        expect(prashnaAskJobs.get(jobId)?.status).toBe('failed')
      })
      const error = prashnaAskJobs.get(jobId)?.error ?? ''
      expect(error).toContain('Platform unreachable')
      expect(error.toLowerCase()).toContain('timeout')

      const statusHandler = makeStatusHandler()
      const statusResult = (await statusHandler({ job_id: jobId })) as {
        structuredContent: { status: string; error: string }
      }
      expect(statusResult.structuredContent.status).toBe('failed')
      expect(statusResult.structuredContent.error.toLowerCase()).toContain('timeout')
    })

    it('degrades honestly when the response stream itself hangs/errors mid-read (e.g. a DB-pool-exhausted downstream dependency dropping the connection)', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        body: new ReadableStream<Uint8Array>({
          start(controller) {
            controller.error(new Error('downstream connection reset (pool exhausted)'))
          },
        }),
      })

      const jobId = await askAndGetJobId(makeExtra())

      await vi.waitFor(() => {
        expect(prashnaAskJobs.get(jobId)?.status).toBe('failed')
      })
      expect(prashnaAskJobs.get(jobId)?.error).toContain('pool exhausted')
    })
  })

  // ── 4. Sidecar timeout surfaced as an honest partial completion ────────
  describe('failure mode 4: sidecar/wall-clock cap trips — engine returns a partial-but-honest result', () => {
    it('calls job.complete() (NOT job.fail()) for a partial result, and prashna_status reports "complete" with the partial receipt intact', async () => {
      const partialResult = {
        ok: true,
        trace_id: 't-partial',
        chart_id: CHART_ID,
        outcome: 'plan',
        query_class: 'dasha_timing',
        query_intent_summary: 'partial due to wall clock cap',
        completeness: {
          status: 'partial',
          tools_dispatched: [
            { tool_name: 'chart_facts_query', status: 'done', result_count: 3, latency_ms: 40 },
          ],
          unserved_tools: ['get_dashas', 'get_temporal_windows'],
          unresolved_tools: [],
          stripped_leaked_capabilities: [],
          cap_tripped: 'wall_clock_cap',
        },
        judgment_flags: ['completeness_partial'],
        results: [{ tool_name: 'chart_facts_query', bundle: {} }],
      }
      mockFetch.mockResolvedValueOnce(makeStreamResponse([JSON.stringify(partialResult)]))

      const jobId = await askAndGetJobId(makeExtra())

      await vi.waitFor(() => {
        expect(prashnaAskJobs.get(jobId)?.status).toBe('complete')
      })
      // Never routed through job.fail() — this is a completion, not a crash.
      expect(prashnaAskJobs.get(jobId)?.error).toBeUndefined()
      expect(prashnaAskJobs.get(jobId)?.result).toEqual(partialResult)

      const statusHandler = makeStatusHandler()
      const statusResult = (await statusHandler({ job_id: jobId })) as {
        structuredContent: {
          status: string
          result: { completeness: { status: string; cap_tripped: string | null } }
        }
      }
      expect(statusResult.structuredContent.status).toBe('complete')
      expect(statusResult.structuredContent.result.completeness.status).toBe('partial')
      expect(statusResult.structuredContent.result.completeness.cap_tripped).toBe('wall_clock_cap')
    })
  })
})
