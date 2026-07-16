/**
 * mcp_client_rate_limit.test.ts — D15b-F1 (D-1.6 Lane S-6, 2026-07-16)
 *
 * Regression test for the D-1.5b Gate-B 429 cascade: a well-formed 429 response
 * (`{error: "rate_limit_exceeded", retry_after_seconds}` — server.ts M8 dispatch-level
 * limiter) must be retried by McpClient, never returned to the caller as if it were the
 * tool's real result.
 */
import { describe, it, expect, vi, afterEach } from 'vitest'
import { McpClient } from '../mcp_client.js'

function jsonResponse(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(body),
  } as unknown as Response
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('McpClient — 429 rate-limit retry (D15b-F1)', () => {
  it('callTool retries past a 429 and returns the real result once the limiter clears', async () => {
    let calls = 0
    vi.stubGlobal('fetch', vi.fn(async () => {
      calls += 1
      if (calls === 1) {
        return jsonResponse(429, {
          error: 'rate_limit_exceeded',
          message: 'Too many requests. Retry after 1 seconds.',
          retry_after_seconds: 0, // 0s so the test doesn't actually wait
        })
      }
      return jsonResponse(200, {
        jsonrpc: '2.0',
        id: 3,
        result: { content: [{ type: 'text', text: JSON.stringify({ ok: true }) }] },
      })
    }))

    const client = new McpClient('https://example.invalid/mcp', 'test-bearer')
    const result = await client.callTool('some_tool', {})

    expect(calls).toBe(2)
    expect(result.content).toEqual({ ok: true })
    expect(result.isToolError).toBe(false)
  })

  it('callTool never returns a 429 body as the tool result (the exact D-1.5b false-red shape)', async () => {
    // Regression guard: BEFORE the D15b-F1 fix, a persistent 429 with a valid JSON body
    // would be returned directly (status < 500, json defined) — the caller would read
    // `content.error === "rate_limit_exceeded"` as if it were a genuine tool payload.
    // After the fix, a persistent 429 exhausts retries and throws instead.
    vi.stubGlobal('fetch', vi.fn(async () =>
      jsonResponse(429, { error: 'rate_limit_exceeded', retry_after_seconds: 0 })
    ))

    const client = new McpClient('https://example.invalid/mcp', 'test-bearer')
    await expect(client.callTool('some_tool', {})).rejects.toThrow(/exhausted retries/)
  })

  it('listTools retries past a 429', async () => {
    let calls = 0
    vi.stubGlobal('fetch', vi.fn(async () => {
      calls += 1
      if (calls === 1) {
        return jsonResponse(429, { error: 'rate_limit_exceeded', retry_after_seconds: 0 })
      }
      return jsonResponse(200, {
        jsonrpc: '2.0',
        id: 2,
        result: { tools: [{ name: 'a_tool' }] },
      })
    }))

    const client = new McpClient('https://example.invalid/mcp', 'test-bearer')
    const tools = await client.listTools()

    expect(calls).toBe(2)
    expect(tools).toEqual([{ name: 'a_tool' }])
  })

  it('a >=500 transport error is still retried (pre-existing behavior unchanged)', async () => {
    let calls = 0
    vi.stubGlobal('fetch', vi.fn(async () => {
      calls += 1
      if (calls === 1) return jsonResponse(503, { error: 'unavailable' })
      return jsonResponse(200, {
        jsonrpc: '2.0',
        id: 3,
        result: { content: [{ type: 'text', text: JSON.stringify({ ok: true }) }] },
      })
    }))

    const client = new McpClient('https://example.invalid/mcp', 'test-bearer')
    const result = await client.callTool('some_tool', {})

    expect(calls).toBe(2)
    expect(result.content).toEqual({ ok: true })
  })
})
