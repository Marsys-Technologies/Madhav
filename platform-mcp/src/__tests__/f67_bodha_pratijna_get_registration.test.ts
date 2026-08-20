/**
 * f67_bodha_pratijna_get_registration.test.ts — F-67: `bodha_pratijna_get` was fully
 * descriptor'd (mcp_surface_profiles.generated.ts) and bridge-aliased
 * (tool_name_bridge.ts: query_pratijna / bodha_pratijna_get both map to
 * marsys://tool/L2/query_pratijna) but no `server.tool('bodha_pratijna_get', ...)` (or
 * `server.tool('query_pratijna', ...)`) registration existed anywhere in
 * platform-mcp/src — a pure omission. This test proves the tool is genuinely callable
 * end-to-end through registerP1AliasTools, and that it forwards the documented filters
 * (status, event_class_id, ayanamsha_id, limit, offset) verbatim to the
 * marsys://tool/L2/query_pratijna capability, without reintroducing the 'unknown_tool'
 * dualOutput defect (F-17/F-18/F-43's class of bug) on a brand-new registration.
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

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('bodha_pratijna_get registration (F-67)', () => {
  let handler: (params: Record<string, unknown>) => Promise<{
    content: { type: string; text: string }[]
    structuredContent?: { object: unknown }
    isError?: boolean
  }>
  let registeredNames: string[]

  beforeAll(async () => {
    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    registeredNames = []
    const mockServer = {
      tool: (name: string, ...rest: unknown[]) => {
        registeredNames.push(name)
        if (name === 'bodha_pratijna_get') handler = rest[rest.length - 1] as typeof handler
      },
    } as unknown as McpServer
    const principal = { user_uid: 'test', key_id: 'test', role: 'client' } as unknown as Principal
    registerP1AliasTools(mockServer, principal)
  })

  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('registers bodha_pratijna_get as a real tool (this is the F-67 fix itself)', () => {
    expect(registeredNames).toContain('bodha_pratijna_get')
    expect(handler).toBeTypeOf('function')
  })

  it('chart_id is required', async () => {
    const result = await handler({})
    expect(result.isError).toBe(true)
  })

  it('calls marsys://tool/L2/query_pratijna with chart_id and default limit/offset', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { rows: [], total_matching: 0 } }))
    await handler({ chart_id: CHART_ID })

    expect(mockFetch).toHaveBeenCalledTimes(1)
    const [url, init] = mockFetch.mock.calls[0] as [string, { body: string }]
    expect(url).toContain('/api/retrieval/capability')
    const callBody = JSON.parse(init.body) as { uri: string; args: Record<string, unknown> }
    expect(callBody.uri).toBe('marsys://tool/L2/query_pratijna')
    expect(callBody.args['chart_id']).toBe(CHART_ID)
    expect(callBody.args['limit']).toBe(50)
    expect(callBody.args['offset']).toBe(0)
  })

  it('forwards status, event_class_id, ayanamsha_id, limit, offset filters verbatim', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { rows: [], total_matching: 0 } }))
    await handler({
      chart_id: CHART_ID,
      status: 'promised',
      event_class_id: 'marriage_primary',
      ayanamsha_id: 'lahiri_chitrapaksha',
      limit: 10,
      offset: 5,
    })

    const callBody = JSON.parse((mockFetch.mock.calls[0][1] as { body: string }).body) as { args: Record<string, unknown> }
    expect(callBody.args['status']).toBe('promised')
    expect(callBody.args['event_class_id']).toBe('marriage_primary')
    expect(callBody.args['ayanamsha_id']).toBe('lahiri_chitrapaksha')
    expect(callBody.args['limit']).toBe(10)
    expect(callBody.args['offset']).toBe(5)
  })

  it('returns real rows from the capability response (genuinely callable end-to-end)', async () => {
    const rows = [
      { pratijna_id: 'p1', event_class_id: 'marriage_primary', status: 'promised', grade: 'strong' },
      { pratijna_id: 'p2', event_class_id: 'wealth_primary', status: 'denied', grade: null },
    ]
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { rows, total_matching: 2 } }))

    const result = await handler({ chart_id: CHART_ID }) as unknown as {
      structuredContent: { object: { rows: unknown[]; total_matching: number } }
    }
    const content = result.structuredContent.object
    expect(content.rows).toEqual(rows)
    expect(content.total_matching).toBe(2)
  })

  it('errors carry the real tool name, not the unknown_tool placeholder (CL-11 guard)', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({}, false, 500))
    const result = await handler({ chart_id: CHART_ID }) as unknown as {
      structuredContent: { object: { tool: string } }
      isError: boolean
    }
    expect(result.isError).toBe(true)
    expect(result.structuredContent.object.tool).toBe('bodha_pratijna_get')
    expect(result.structuredContent.object.tool).not.toBe('unknown_tool')
  })
})
