import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

function jsonResponse(body: unknown, ok = true, status = 200) {
  return {
    ok,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  }
}

const principal: Principal = { user_uid: 'test-uid', key_id: 'mcp_test_key' }

describe('F22 ref_dasha_systems_get — canonical structured catalog', () => {
  let handler: (params: Record<string, unknown>) => Promise<{ structuredContent: { object: unknown } }>

  beforeAll(async () => {
    const { registerP1ReferenceTools } = await import('../tools/register_p1_reference.js')
    const mockServer = {
      tool: (name: string, _desc: string, _schema: unknown, registeredHandler: typeof handler) => {
        if (name === 'ref_dasha_systems_get') handler = registeredHandler
      },
    } as unknown as McpServer
    registerP1ReferenceTools(mockServer, principal)
  })

  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('unwraps the registered structured capability for an exact system request', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({
      ok: true,
      content: {
        content: {
          rows: [{
            canonical_id: 'vimshottari',
            name_en: 'Vimshottari Dasha',
            total_cycle_years: 120,
            base_unit: 'nakshatra_lord',
            sequence_jsonb: [{ graha: 'Ketu', years: 7 }],
            school: 'Parashari',
            classical_citations: ['BPHS'],
          }],
          count: 1,
          filters: { canonical_id: 'vimshottari', school: null },
          provenance: { tables: ['brahma_dasha_systems'] },
        },
        is_error: false,
      },
    }))

    const result = await handler({ system: 'vimshottari', limit: 10, offset: 0 })
    const obj = result.structuredContent.object as { content: Record<string, unknown> }

    expect(obj.content).toMatchObject({
      source: 'brahma_dasha_systems',
      structured_filter_applied: true,
      structured_catalog_served: true,
      total: 1,
      rows: [expect.objectContaining({ canonical_id: 'vimshottari', total_cycle_years: 120 })],
      pagination: { offset: 0, limit: 10, total: 1, more_available: false, next_offset: null },
      provenance: expect.objectContaining({ table: 'brahma_dasha_systems' }),
    })
    const request = mockFetch.mock.calls[0]![1] as { body: string }
    expect(JSON.parse(request.body)).toMatchObject({
      uri: 'marsys://tool/L0/query_dasha_systems',
      args: { canonical_id: 'vimshottari' },
    })
  })

  it('applies keyword filtering and pagination to the structured catalog receipt', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({
      ok: true,
      content: {
        content: {
          rows: [
            { canonical_id: 'vimshottari', name_en: 'Vimshottari Dasha', school: 'Parashari', total_cycle_years: 120 },
            { canonical_id: 'yogini', name_en: 'Yogini Dasha', school: 'Parashari', total_cycle_years: 36 },
          ],
          count: 2,
          provenance: { tables: ['brahma_dasha_systems'] },
        },
        is_error: false,
      },
    }))

    const result = await handler({ keyword: 'parashari', limit: 1, offset: 1 })
    const obj = result.structuredContent.object as { content: Record<string, unknown> }

    expect(obj.content).toMatchObject({
      source: 'brahma_dasha_systems',
      structured_filter_applied: true,
      total: 2,
      rows: [expect.objectContaining({ canonical_id: 'yogini' })],
      pagination: { offset: 1, limit: 1, total: 2, more_available: false, next_offset: null },
    })
    const request = mockFetch.mock.calls[0]![1] as { body: string }
    expect(JSON.parse(request.body)).toMatchObject({
      uri: 'marsys://tool/L0/query_dasha_systems',
      args: {},
    })
  })

  it('keeps a genuine structured no-row lookup distinct from a classical-text fallback', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({
      ok: true,
      content: {
        content: { rows: [], count: 0, provenance: { tables: ['brahma_dasha_systems'] } },
        is_error: false,
      },
    }))

    const result = await handler({ system: 'not-a-system', limit: 1, offset: 0 })
    const obj = result.structuredContent.object as { content: Record<string, unknown> }

    expect(obj.content).toMatchObject({
      source: 'brahma_dasha_systems',
      structured_filter_applied: true,
      structured_catalog_served: true,
      rows: [],
      total: 0,
      empty_reason: expect.stringContaining('not-a-system'),
      pagination: { offset: 0, limit: 1, total: 0, more_available: false, next_offset: null },
    })
    expect(obj.content).not.toHaveProperty('fallback_reason')
  })
})
