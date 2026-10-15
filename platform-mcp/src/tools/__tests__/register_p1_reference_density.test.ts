/**
 * DENS-F (CLAUDE.md §N.6): the serving-density claims of the two tools whose SELECT lives in register_p1_reference.ts
 * (ref_nakshatra_get -> bg_nakshatra; ref_transit_rules_get -> bg_transit_rules), checked against the real schema and handler.
 * A contract is a CLAIM about the handler: every facet is a real input key; `empty_reason: true` means a zero-row page carries a
 * non-empty `empty_reason` and a populated page carries none; `paginated: true` means the tool takes limit/offset.
 */
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'
import {
  NAKSHATRA_INPUT, TRANSIT_RULES_INPUT, REF_NAKSHATRA_DENSITY, REF_TRANSIT_RULES_DENSITY,
  registerP1ReferenceTools,
} from '../register_p1_reference.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)
const principal: Principal = { user_uid: 'test-uid', key_id: 'mcp_test_key' }

function jsonResponse(body: unknown) {
  return { ok: true, status: 200, json: async () => body, text: async () => JSON.stringify(body) }
}

type Handler = (params: Record<string, unknown>) => Promise<{ structuredContent: { object: { content: Record<string, unknown> } } }>

describe('DENS-F: register_p1_reference density contracts', () => {
  const handlers: Record<string, Handler> = {}
  const schemas: Record<string, Record<string, unknown>> = {}

  beforeAll(() => {
    const mockServer = {
      tool: (name: string, _desc: string, schema: Record<string, unknown>, h: Handler) => { handlers[name] = h; schemas[name] = schema },
    } as unknown as McpServer
    registerP1ReferenceTools(mockServer, principal)
  })
  beforeEach(() => { mockFetch.mockReset() })

  it('the registered schemas are the exported ones the contracts are checked against', () => {
    expect(schemas['ref_nakshatra_get']).toBe(NAKSHATRA_INPUT)
    expect(schemas['ref_transit_rules_get']).toBe(TRANSIT_RULES_INPUT)
  })

  it('every declared facet is a real input of its tool; paginated means limit and offset are inputs', () => {
    for (const f of REF_NAKSHATRA_DENSITY.facets) expect(Object.keys(NAKSHATRA_INPUT)).toContain(f)
    for (const f of REF_TRANSIT_RULES_DENSITY.facets) expect(Object.keys(TRANSIT_RULES_INPUT)).toContain(f)
    for (const input of [NAKSHATRA_INPUT, TRANSIT_RULES_INPUT]) {
      expect(Object.keys(input)).toEqual(expect.arrayContaining(['limit', 'offset']))
    }
    expect(REF_NAKSHATRA_DENSITY.paginated).toBe(true)
    expect(REF_TRANSIT_RULES_DENSITY.paginated).toBe(true)
  })

  it('ref_transit_rules_get (empty_reason: true): a zero-row page names the filters, a populated one carries none', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ rows: [] }))
    const empty = (await handlers['ref_transit_rules_get']!({ graha: 'Jupiter', house: 7 })).structuredContent.object.content
    expect(String(empty['empty_reason'])).toContain('graha=Jupiter')
    expect(String(empty['empty_reason'])).toContain('house=7')
    mockFetch.mockResolvedValueOnce(jsonResponse({ rows: [{ id: 1, rule_type: 'gochara', graha: 'Jupiter', primary_house: 2 }] }))
    const full = (await handlers['ref_transit_rules_get']!({ graha: 'Jupiter' })).structuredContent.object.content
    expect(full['empty_reason']).toBeUndefined()
    expect(full['total']).toBe(1)
  })

  it('ref_nakshatra_get (empty_reason: false is the honest claim): a zero-row structured lookup is labelled as a fallback, not given an empty_reason', async () => {
    expect(REF_NAKSHATRA_DENSITY.empty_reason).toBe(false)
    mockFetch
      .mockResolvedValueOnce(jsonResponse({ rows: [] }))
      .mockResolvedValueOnce(jsonResponse({ rows: [{ total_matching: 0 }] }))
      .mockResolvedValueOnce(jsonResponse({ ok: true, content: { search_mode: 'hybrid_vector_keyword', citations: [], rows: [], total: 0 } }))
    const out = (await handlers['ref_nakshatra_get']!({ nakshatra: 'no_such_nakshatra' })).structuredContent.object.content
    expect(out['structured_filter_applied']).toBe(false)
    expect(String(out['fallback_reason'])).toContain('No structured reference_nakshatra row matched')
  })
})
