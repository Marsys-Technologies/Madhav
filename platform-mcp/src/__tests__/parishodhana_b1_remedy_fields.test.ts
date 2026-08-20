/**
 * PARISHODHANA B1 (R-29/EL-51 follow-up) — regression test.
 *
 * `fields` (compact|all) was not declared on the `bodha_remedies_get` /
 * `bodha_remedies_search` MCP alias zod schemas — the same silent-param-strip
 * failure mode CR-42 previously fixed for `graha`/`planet` on these same tools
 * (see d1_6_s1_cr42_regressions.test.ts). Any caller-supplied `fields='all'` was
 * therefore dropped by the MCP SDK before the handler ever saw it, silently
 * forcing every call into 'compact' mode regardless of what was requested —
 * making the tool's own `drill_pointers` recovery hint ("Call with fields='all'
 * for full raw rows") a dead end, and blocking the documented recovery path for
 * associated_*_array / estimated_cost_inr_range_jsonb / prescription_detail_jsonb
 * (which also carries the EL-51 maraka_contraindication_verdict field).
 */
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function jsonResponse(body: unknown, ok = true, status = 200) {
  return {
    ok, status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  }
}

const principal: Principal = { user_uid: 'test-uid', key_id: 'mcp_test_key' }

describe('bodha_remedies_get / bodha_remedies_search — `fields` schema + passthrough (PARISHODHANA B1)', () => {
  const registeredSchemas = new Map<string, Record<string, unknown>>()
  const registeredHandlers = new Map<string, (params: Record<string, unknown>) => Promise<unknown>>()

  beforeAll(async () => {
    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const mockServer = {
      tool: (name: string, _desc: string, schema: Record<string, unknown>, handler: (params: Record<string, unknown>) => Promise<unknown>) => {
        registeredSchemas.set(name, schema)
        registeredHandlers.set(name, handler)
      },
    } as unknown as McpServer
    registerP1AliasTools(mockServer, principal)
  })

  beforeEach(() => {
    mockFetch.mockReset()
  })
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('bodha_remedies_get declares `fields` in its zod schema', () => {
    const schema = registeredSchemas.get('bodha_remedies_get')
    expect(schema).toBeDefined()
    expect(Object.keys(schema!)).toContain('fields')
  })

  it('bodha_remedies_search declares `fields` in its zod schema', () => {
    const schema = registeredSchemas.get('bodha_remedies_search')
    expect(schema).toBeDefined()
    expect(Object.keys(schema!)).toContain('fields')
  })

  it('bodha_remedies_get: a caller-supplied fields="all" is forwarded to the capability call unchanged', async () => {
    // F-125: bodha_remedies_get now also carries the B.11 orientation gate
    // (requiresOrientation: true), so it issues a SECOND fetch call
    // (marsys://tool/L2/query_ucd) after the primary capability call — both mocked here.
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { resonances: [], prescriptions: [] } }))
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { content: { chart_id: '482012f1-710e-4a25-994a-93821f5871aa', entity_profiles: [] }, is_error: false } }))
    const handler = registeredHandlers.get('bodha_remedies_get')!
    await handler({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa', graha: 'Saturn', fields: 'all' })

    expect(mockFetch).toHaveBeenCalledTimes(2)
    const body = JSON.parse((mockFetch.mock.calls[0][1] as { body: string }).body) as {
      args: Record<string, unknown>
    }
    expect(body.args['fields']).toBe('all')
  })

  it('bodha_remedies_get: omitting fields does not forward a `fields` key at all (compact remains the capability default)', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, content: { resonances: [], prescriptions: [] } }))
    const handler = registeredHandlers.get('bodha_remedies_get')!
    await handler({ chart_id: '482012f1-710e-4a25-994a-93821f5871aa', graha: 'Saturn' })

    const body = JSON.parse((mockFetch.mock.calls[0][1] as { body: string }).body) as {
      args: Record<string, unknown>
    }
    expect(body.args['fields']).toBeUndefined()
  })
})
