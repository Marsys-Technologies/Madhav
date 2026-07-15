/**
 * d15b_b6_serving_hygiene.test.ts — D-1.5b Lane B-6 (Serving hygiene) unit tests.
 *
 * Covers the TS-layer (MCP tool) behaviors that don't require a live platform/sidecar:
 *   - ephemeris_cache_year: month narrowing + rows pagination (item 2)
 *   - ref_remedies_search: genuine keyword honoring, not silent drop (item 3)
 *   - ganita_positions_get / bodha_domain_reading_get: schema exposes the new params
 *
 * `fetch` is mocked globally — no live PLATFORM_URL/sidecar required.
 */
import { describe, it, expect, vi, beforeEach, beforeAll } from 'vitest'
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

// ── ephemeris_cache_year ────────────────────────────────────────────────────

describe('ephemeris_cache_year — D-1.5b item 2 (response budget)', () => {
  let handler: (params: Record<string, unknown>) => Promise<{ content: { type: string; text: string }[]; isError?: boolean }>

  beforeAll(async () => {
    const { registerEphemerisCacheYearTool } = await import('../tools/l0_ephemeris.js')
    const mockServer = {
      tool: (name: string, _desc: string, _schema: unknown, h: typeof handler) => {
        if (name === 'ephemeris_cache_year') handler = h
      },
    } as unknown as McpServer
    registerEphemerisCacheYearTool(mockServer)
  })

  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('narrows the sidecar request to a single month when `month` is passed', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, rows: [] }))
    await handler({ year: 1984, month: 2 })
    const calledUrl = mockFetch.mock.calls[0][0] as string
    expect(calledUrl).toContain('start_date=1984-02-01')
    expect(calledUrl).toContain('end_date=1984-02-29') // 1984 is a leap year
  })

  it('requests the full year when `month` is omitted', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, rows: [] }))
    await handler({ year: 1984 })
    const calledUrl = mockFetch.mock.calls[0][0] as string
    expect(calledUrl).toContain('start_date=1984-01-01')
    expect(calledUrl).toContain('end_date=1984-12-31')
  })

  it('paginates the returned rows — default limit 400, honest total/pagination receipt', async () => {
    const rows = Array.from({ length: 600 }, (_, i) => ({ date: `1984-01-${i}`, body: 'Sun' }))
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, rows }))
    const result = await handler({ year: 1984 })
    const payload = JSON.parse(result.content[0].text) as {
      rows: unknown[]
      pagination: { offset: number; limit: number; total: number; returned_count: number; more_available: boolean }
    }
    expect(payload.pagination.total).toBe(600)
    expect(payload.pagination.limit).toBe(400)
    expect(payload.rows.length).toBe(400)
    expect(payload.pagination.more_available).toBe(true)
  })

  it('honors an explicit limit/offset over the default', async () => {
    const rows = Array.from({ length: 50 }, (_, i) => ({ date: `1984-01-${i}`, body: 'Sun' }))
    mockFetch.mockResolvedValueOnce(jsonResponse({ ok: true, rows }))
    const result = await handler({ year: 1984, limit: 10, offset: 20 })
    const payload = JSON.parse(result.content[0].text) as {
      rows: unknown[]
      pagination: { offset: number; limit: number; total: number; returned_count: number }
    }
    expect(payload.pagination.offset).toBe(20)
    expect(payload.pagination.limit).toBe(10)
    expect(payload.rows.length).toBe(10)
  })
})

// ── ref_remedies_search ─────────────────────────────────────────────────────

describe('ref_remedies_search — D-1.5b item 3 (CR-42 honor-or-reject)', () => {
  let handler: (params: Record<string, unknown>) => Promise<{ structuredContent: { object: unknown } }>

  beforeAll(async () => {
    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const mockServer = {
      tool: (name: string, _desc: string, _schema: unknown, h: typeof handler) => {
        if (name === 'ref_remedies_search') handler = h
      },
    } as unknown as McpServer
    const principal: Principal = { user_uid: 'test-uid', key_id: 'mcp_test_key' }
    registerP1AliasTools(mockServer, principal)
  })

  beforeEach(() => {
    mockFetch.mockReset()
  })

  // Matches the real /api/mcp/primitives/[tool] response shape (route.ts buildEnvelope):
  // { ok: true, result: <ToolBundle>, ... } — callPlatformPrim() returns res.json() verbatim.
  function primitiveEnvelope(rows: Record<string, unknown>[]) {
    return jsonResponse({
      ok: true,
      result: {
        results: rows.map(r => ({ content: JSON.stringify(r), source_canonical_id: 'BPHS', confidence: 0.9 })),
      },
    })
  }

  it('genuinely filters by keyword instead of silently ignoring it (CR-42)', async () => {
    mockFetch.mockResolvedValueOnce(primitiveEnvelope([
      { remedy_id: '1', prescription_text: 'Chant the Hanuman Chalisa daily at sunrise.' },
      { remedy_id: '2', prescription_text: 'Donate red lentils on Tuesdays.' },
      { remedy_id: '3', mantra_text: 'Om Hanuman Namah', prescription_text: 'unrelated' },
    ]))
    const result = await handler({ keyword: 'hanuman' })
    const obj = result.structuredContent.object as {
      result: { results: { content: string }[] }
      keyword_search: { applied: boolean; keyword: string; matched_count: number; candidate_pool_size: number }
    }
    expect(obj.keyword_search.applied).toBe(true)
    expect(obj.keyword_search.keyword).toBe('hanuman')
    expect(obj.keyword_search.candidate_pool_size).toBe(3)
    expect(obj.keyword_search.matched_count).toBe(2)
    expect(obj.result.results.length).toBe(2)
    const ids = obj.result.results.map(r => (JSON.parse(r.content) as { remedy_id: string }).remedy_id)
    expect(ids.sort()).toEqual(['1', '3'])
  })

  it('requests a widened candidate pool (top_k) when a keyword is supplied', async () => {
    mockFetch.mockResolvedValueOnce(primitiveEnvelope([]))
    await handler({ keyword: 'saturn', limit: 5 })
    const body = JSON.parse((mockFetch.mock.calls[0][1] as { body: string }).body) as {
      params: Record<string, unknown>
    }
    expect(body.params['top_k']).toBeGreaterThan(5)
  })

  it('with no keyword, behaves as a plain passthrough (no keyword_search receipt)', async () => {
    mockFetch.mockResolvedValueOnce(primitiveEnvelope([{ remedy_id: '1', prescription_text: 'anything' }]))
    const result = await handler({ planet: 'Saturn' })
    const obj = result.structuredContent.object as Record<string, unknown>
    expect(obj['keyword_search']).toBeUndefined()
  })
})

// ── schema exposure smoke (items 1 + 2) ─────────────────────────────────────

describe('registered schemas expose the new D-1.5b params', () => {
  const registered = new Map<string, Record<string, unknown>>()

  beforeAll(async () => {
    const { registerP1AliasTools } = await import('../tools/register_p1_aliases.js')
    const mockServer = {
      tool: (name: string, _desc: string, schema: Record<string, unknown>) => {
        registered.set(name, schema)
      },
    } as unknown as McpServer
    const principal: Principal = { user_uid: 'test-uid', key_id: 'mcp_test_key' }
    registerP1AliasTools(mockServer, principal)
  })

  it('ganita_positions_get exposes include_upagrahas (CR-50)', () => {
    const schema = registered.get('ganita_positions_get')
    expect(schema).toBeDefined()
    expect(Object.keys(schema!)).toContain('include_upagrahas')
  })

  it('bodha_domain_reading_get exposes lens_limit/lens_offset (item 2)', () => {
    const schema = registered.get('bodha_domain_reading_get')
    expect(schema).toBeDefined()
    expect(Object.keys(schema!)).toContain('lens_limit')
    expect(Object.keys(schema!)).toContain('lens_offset')
  })
})
