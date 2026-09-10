/**
 * d15b_f3_min_weight_alias.test.ts — D15b-F3 (routed to D-1.6 Lane S-5): bodha_signals_get's
 * `min_weight` parameter was documented in the tool schema and forwarded verbatim to the
 * underlying query_signals capability, which only ever reads `min_salience` — a genuine
 * silent no-op (the exact R-18 "documented param that filters nothing" defect class).
 *
 * Fix: alias `min_weight` -> `min_salience` before forwarding, unless the caller already
 * supplied `min_salience` explicitly (which wins).
 *
 * `fetch` is mocked globally — no live PLATFORM_URL required.
 */
import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function jsonResponse(body: unknown, ok = true, status = 200) {
  return { ok, status, json: async () => body, text: async () => JSON.stringify(body) }
}

describe('bodha_signals_get min_weight -> min_salience alias (D15b-F3)', () => {
  let handler: (params: Record<string, unknown>) => Promise<{ content: { type: string; text: string }[]; isError?: boolean }>

  beforeAll(async () => {
    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const mockServer = {
      tool: (name: string, ...rest: unknown[]) => {
        if (name === 'bodha_signals_get') handler = rest[rest.length - 1] as typeof handler
      },
    } as unknown as McpServer
    const principal = { user_uid: 'test', key_id: 'test', role: 'client' } as unknown as Principal
    registerP1AliasTools(mockServer, principal)
  })

  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('forwards min_weight as min_salience to the query_signals capability call', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { signals: [] } }))
    await handler({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa', min_weight: 0.7 })
    const callBody = JSON.parse((mockFetch.mock.calls[0][1] as { body: string }).body) as { args: Record<string, unknown> }
    expect(callBody.args['min_salience']).toBe(0.7)
    expect(callBody.args['min_weight']).toBeUndefined()
  })

  it('an explicit min_salience is never overridden by min_weight', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { signals: [] } }))
    // @ts-expect-error — exercising an undeclared-but-passthrough param on purpose
    await handler({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa', min_weight: 0.7, min_salience: 0.9 })
    const callBody = JSON.parse((mockFetch.mock.calls[0][1] as { body: string }).body) as { args: Record<string, unknown> }
    expect(callBody.args['min_salience']).toBe(0.9)
  })

  it('omitting min_weight forwards no min_salience at all (no fabricated filter)', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { signals: [] } }))
    await handler({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa' })
    const callBody = JSON.parse((mockFetch.mock.calls[0][1] as { body: string }).body) as { args: Record<string, unknown> }
    expect(callBody.args['min_salience']).toBeUndefined()
  })

  it('rebuilds verdict_summary from signals that survive the final budget trim', async () => {
    const signals = Array.from({ length: 80 }, (_, index) => ({
      signal_id: `signal-${index}`,
      signature_tier: index % 2 === 0 ? 'high' : 'medium',
      constituent_facts_array: [`fact-${index % 4}`],
      detail: 'evidence '.repeat(500),
    }))
    mockFetch.mockResolvedValueOnce(jsonResponse({
      ok: true,
      content: { content: { signals }, is_error: false },
    }))

    const result = await handler({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa' }) as unknown as {
      structuredContent?: { object: { content: Record<string, unknown> } }
    }
    const content = result.structuredContent!.object.content
    const served = content['signals'] as unknown[]
    const verdict = content['verdict_summary'] as { served_count: number; tier_distribution: Record<string, number> }

    expect(served.length).toBeLessThan(signals.length)
    expect(verdict.served_count).toBe(served.length)
    expect(Object.values(verdict.tier_distribution).reduce((total, count) => total + count, 0)).toBe(served.length)
    expect(Buffer.byteLength(JSON.stringify(content), 'utf8')).toBeLessThanOrEqual(25 * 1024)
  })
})
