/**
 * prashna_ask_bridge.test.ts — HTTP-call-only tests for callPrashnaAskEngine.
 *
 * Vitest — not jest. Mocks fetch globally (matches m8_e2e_proof.test.ts style).
 * SERVICE_TOKEN env override bypasses GoogleAuth entirely (same pattern client.ts
 * uses for testability), so no google-auth-library mock is needed.
 *
 * W6 Part 2: the platform route now streams NDJSON (progress lines + one final
 * line) instead of a single JSON blob — `makeStreamResponse()` below builds a
 * mock `Response`-shaped object whose `.body` is a real `ReadableStream` so the
 * bridge's incremental reader/decoder path is genuinely exercised, not bypassed.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  callPrashnaAskEngine,
  __resetPrashnaAskBridgeTokenCacheForTests,
  type PrashnaAskProgressEvent,
} from '../prashna_ask_bridge.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

const PRINCIPAL = { userUid: 'user-1', keyId: 'key-1' }

function makeStreamResponse(
  lines: string[],
  opts: { ok?: boolean; status?: number } = {}
): { ok: boolean; status: number; body: ReadableStream<Uint8Array> } {
  const encoder = new TextEncoder()
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const line of lines) {
        controller.enqueue(encoder.encode(line + '\n'))
      }
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

// PLATFORM_URL is read once at module load (identical to client.ts's own
// top-level const) — it cannot be overridden per-test without resetModules,
// so these tests assert against the module's already-resolved base URL.

describe('callPrashnaAskEngine', () => {
  it('POSTs to /api/mcp/prashna_ask with the exact client.ts auth-header pattern', async () => {
    mockFetch.mockResolvedValueOnce(
      makeStreamResponse([JSON.stringify({ ok: true, trace_id: 't1', chart_id: 'c1', outcome: 'plan' })])
    )

    await callPrashnaAskEngine({ chartId: 'c1', question: 'what dasha am I in?', principal: PRINCIPAL })

    expect(mockFetch).toHaveBeenCalledTimes(1)
    const [url, opts] = mockFetch.mock.calls[0]
    expect(url).toBe('http://localhost:3000/api/mcp/prashna_ask')
    expect(opts.method).toBe('POST')
    expect(opts.headers['Authorization']).toBe('Bearer test-static-token')
    // MCP_INTERNAL_TOKEN, like PLATFORM_URL, is a module-load-time constant
    // (identical to client.ts) — assert the header key is sent, not its value.
    expect(typeof opts.headers['X-MCP-Internal-Token']).toBe('string')
    expect(opts.headers['X-MCP-User']).toBe('user-1')
    expect(opts.headers['X-MCP-Key-Id']).toBe('key-1')
    expect(JSON.parse(opts.body)).toEqual({ chart_id: 'c1', question: 'what dasha am I in?' })
  })

  it('returns the plan outcome shape verbatim on success (single-blob body, no event field)', async () => {
    const planResponse = {
      ok: true,
      trace_id: 't1',
      chart_id: 'c1',
      outcome: 'plan',
      query_class: 'dasha_timing',
      query_intent_summary: 'current dasha',
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
    }
    mockFetch.mockResolvedValueOnce(makeStreamResponse([JSON.stringify(planResponse)]))

    const result = await callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL })
    expect(result).toEqual(planResponse)
  })

  it('streams interim progress lines to onProgress and resolves with the final event payload', async () => {
    const planResponse = {
      ok: true,
      trace_id: 't1',
      chart_id: 'c1',
      outcome: 'plan',
      query_class: 'dasha_timing',
      query_intent_summary: 'current dasha',
      completeness: {
        status: 'complete',
        tools_dispatched: [{ tool_name: 'chart_facts_query', status: 'done', result_count: 1, latency_ms: 5 }],
        unserved_tools: [],
        unresolved_tools: [],
        stripped_leaked_capabilities: [],
        cap_tripped: null,
      },
      judgment_flags: [],
      results: [{ tool_name: 'chart_facts_query', bundle: {} }],
    }
    const progressLine1 = {
      event: 'progress',
      tools_dispatched_count: 1,
      cap_ceiling: { maxCalls: 10, maxWallClockMs: 120_000 },
      elapsed_ms: 40,
      last_tool: 'chart_facts_query',
    }
    const progressLine2 = {
      event: 'progress',
      tools_dispatched_count: 2,
      cap_ceiling: { maxCalls: 10, maxWallClockMs: 120_000 },
      elapsed_ms: 90,
      last_tool: 'get_positions',
    }
    mockFetch.mockResolvedValueOnce(
      makeStreamResponse([
        JSON.stringify(progressLine1),
        JSON.stringify(progressLine2),
        JSON.stringify({ event: 'final', ...planResponse }),
      ])
    )

    const onProgress = vi.fn()
    const result = await callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL }, onProgress)

    expect(onProgress).toHaveBeenCalledTimes(2)
    expect(onProgress).toHaveBeenNthCalledWith(1, progressLine1)
    expect(onProgress).toHaveBeenNthCalledWith(2, progressLine2)
    // The resolved value has the `event` discriminator stripped and otherwise
    // matches the route's final body exactly.
    expect(result).toEqual(planResponse)
  })

  it('resolves an "event":"error" line as a bridge error envelope, not a fake final payload', async () => {
    mockFetch.mockResolvedValueOnce(
      makeStreamResponse([
        JSON.stringify({ event: 'progress', tools_dispatched_count: 1, cap_ceiling: { maxCalls: 10, maxWallClockMs: 120_000 }, elapsed_ms: 10, last_tool: 'chart_facts_query' }),
        JSON.stringify({ event: 'error', trace_id: 't1', chart_id: 'c1', message: 'registry lookup exploded' }),
      ])
    )
    const result = await callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL })
    expect(result.ok).toBe(false)
    expect((result as { error: { message: string } }).error.message).toContain('registry lookup exploded')
  })

  it('does not require onProgress — a caller that omits it sees unchanged behavior', async () => {
    const planResponse = { ok: true, trace_id: 't9', chart_id: 'c1', outcome: 'plan' }
    mockFetch.mockResolvedValueOnce(
      makeStreamResponse([
        JSON.stringify({
          event: 'progress',
          tools_dispatched_count: 1,
          cap_ceiling: { maxCalls: 10, maxWallClockMs: 120_000 },
          elapsed_ms: 10,
          last_tool: 'chart_facts_query',
        }),
        JSON.stringify({ event: 'final', ...planResponse }),
      ])
    )

    const result = await callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL })
    expect(result).toEqual(planResponse)
  })

  it('returns the clarification_needed outcome shape verbatim', async () => {
    const clarification = {
      ok: true,
      trace_id: 't2',
      outcome: 'clarification_needed',
      question: 'Which domain?',
      missing_scope_dims: ['domains'],
      suggested_options: ['wealth', 'career'],
    }
    mockFetch.mockResolvedValueOnce(makeStreamResponse([JSON.stringify(clarification)]))

    const result = await callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL })
    expect(result).toEqual(clarification)
  })

  it('passes through an McpEnvelope-shaped error response from the route unchanged', async () => {
    const errEnvelope = {
      ok: false,
      trace_id: '',
      error: { class: 'auth', message: 'Invalid service token' },
    }
    mockFetch.mockResolvedValueOnce(makeStreamResponse([JSON.stringify(errEnvelope)], { ok: false, status: 401 }))

    const result = await callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL })
    expect(result).toEqual(errEnvelope)
  })

  it('returns a synthesized error envelope when the platform is unreachable (network error)', async () => {
    mockFetch.mockRejectedValueOnce(new Error('ECONNREFUSED'))

    const result = await callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL })
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.class).toBe('internal')
      expect(result.error.message).toContain('Platform unreachable')
      expect(result.error.message).toContain('ECONNREFUSED')
    }
  })

  it('returns a synthesized error envelope when the platform stream never yields a resolvable line', async () => {
    mockFetch.mockResolvedValueOnce(makeStreamResponse(['not json at all']))

    const result = await callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL })
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.message).toContain('non-JSON or empty')
    }
  })

  it('never throws — all failure modes resolve to an error envelope', async () => {
    mockFetch.mockRejectedValueOnce(new Error('boom'))
    await expect(
      callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL })
    ).resolves.not.toThrow()
  })

  it('never throws when the stream body itself errors mid-read', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      body: new ReadableStream<Uint8Array>({
        start(controller) {
          controller.error(new Error('stream broke'))
        },
      }),
    })

    const result = await callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL })
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.message).toContain('stream broke')
    }
  })
})

// Type-only sanity check — ensures PrashnaAskProgressEvent's shape stays in
// sync with what the route actually emits (compile-time only; no runtime cost).
const _typeCheck: PrashnaAskProgressEvent = {
  tools_dispatched_count: 1,
  cap_ceiling: { maxCalls: 10, maxWallClockMs: 1 },
  elapsed_ms: 1,
  last_tool: 'x',
}
void _typeCheck
