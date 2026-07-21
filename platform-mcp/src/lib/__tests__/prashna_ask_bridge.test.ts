/**
 * prashna_ask_bridge.test.ts — HTTP-call-only tests for callPrashnaAskEngine.
 *
 * Vitest — not jest. Mocks fetch globally (matches m8_e2e_proof.test.ts style).
 * SERVICE_TOKEN env override bypasses GoogleAuth entirely (same pattern client.ts
 * uses for testability), so no google-auth-library mock is needed.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  callPrashnaAskEngine,
  __resetPrashnaAskBridgeTokenCacheForTests,
} from '../prashna_ask_bridge.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

const PRINCIPAL = { userUid: 'user-1', keyId: 'key-1' }

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
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ ok: true, trace_id: 't1', chart_id: 'c1', outcome: 'plan' }),
    })

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

  it('returns the plan outcome shape verbatim on success', async () => {
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
    mockFetch.mockResolvedValueOnce({ ok: true, status: 200, json: async () => planResponse })

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
    mockFetch.mockResolvedValueOnce({ ok: true, status: 200, json: async () => clarification })

    const result = await callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL })
    expect(result).toEqual(clarification)
  })

  it('passes through an McpEnvelope-shaped error response from the route unchanged', async () => {
    const errEnvelope = {
      ok: false,
      trace_id: '',
      error: { class: 'auth', message: 'Invalid service token' },
    }
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401, json: async () => errEnvelope })

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

  it('returns a synthesized error envelope when the platform returns non-JSON', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => { throw new Error('not json') },
    })

    const result = await callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL })
    expect(result.ok).toBe(false)
    if (!result.ok) {
      expect(result.error.message).toContain('non-JSON')
    }
  })

  it('never throws — all failure modes resolve to an error envelope', async () => {
    mockFetch.mockRejectedValueOnce(new Error('boom'))
    await expect(
      callPrashnaAskEngine({ chartId: 'c1', question: 'q', principal: PRINCIPAL })
    ).resolves.not.toThrow()
  })
})
