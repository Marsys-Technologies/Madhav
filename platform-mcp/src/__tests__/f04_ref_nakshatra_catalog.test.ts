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

describe('F04 ref_nakshatra_get — canonical structured catalog', () => {
  let handler: (params: Record<string, unknown>) => Promise<{ structuredContent: { object: unknown } }>

  beforeAll(async () => {
    const { registerP1ReferenceTools } = await import('../tools/register_p1_reference.js')
    const mockServer = {
      tool: (name: string, _desc: string, _schema: unknown, registeredHandler: typeof handler) => {
        if (name === 'ref_nakshatra_get') handler = registeredHandler
      },
    } as unknown as McpServer
    registerP1ReferenceTools(mockServer, principal)
  })

  beforeEach(() => {
    mockFetch.mockReset()
  })

  it('normalizes a catalog name lookup and returns canonical attributes with provenance', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({
      rows: [{
        nakshatra_id: 25,
        name_en: 'Purva Bhadrapada',
        vimshottari_lord: 'Jupiter',
        presiding_deity: 'Aja Ekapada',
        gana: 'Manushya',
        nadi: 'Madhya',
        varna: 'Brahmin',
        nakshatra_gender: 'Male',
        symbol: 'Front legs of a funeral cot',
        body_part: 'left side',
        pada_lords: ['Jupiter', 'Saturn', 'Saturn', 'Jupiter'],
        classical_source: 'BPHS',
        tradition_scope: 'classical',
        total_matching: 1,
      }],
    }))

    const result = await handler({ nakshatra: 'purva_bhadrapada' })
    const obj = result.structuredContent.object as { content: Record<string, unknown> }

    expect(obj.content).toMatchObject({
      source: 'reference_nakshatra',
      structured_filter_applied: true,
      total: 1,
      rows: [expect.objectContaining({
        name_en: 'Purva Bhadrapada',
        vimshottari_lord: 'Jupiter',
        pada_lords: ['Jupiter', 'Saturn', 'Saturn', 'Jupiter'],
      })],
      provenance: expect.objectContaining({ table: 'reference_nakshatra' }),
    })
    const request = mockFetch.mock.calls[0]![1] as { body: string }
    const body = JSON.parse(request.body) as { sql: string; params: unknown[] }
    expect(body.sql).toContain('FROM reference_nakshatra n')
    expect(body.sql).toContain('reference_nakshatra_pada')
    expect(body.params).toContain('purva_bhadrapada')
    expect(mockFetch).toHaveBeenCalledTimes(1)
  })

  it('labels a classical-text fallback when no canonical catalog row matches', async () => {
    mockFetch
      .mockResolvedValueOnce(jsonResponse({ rows: [] }))
      .mockResolvedValueOnce(jsonResponse({
        ok: true,
        content: { search_mode: 'hybrid_vector_keyword', query_used: 'not-a-nakshatra nakshatra', citations: [], rows: [], total: 0 },
      }))

    const result = await handler({ nakshatra: 'not-a-nakshatra' })
    const obj = result.structuredContent.object as { content: Record<string, unknown> }

    expect(obj.content).toMatchObject({
      source: 'classical_text_fallback',
      structured_filter_applied: false,
      fallback_reason: expect.stringMatching(/No structured reference_nakshatra row/),
    })
    expect(mockFetch).toHaveBeenCalledTimes(2)
  })

  it('keeps the keyword-only classical text path unchanged', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({
      ok: true,
      content: { search_mode: 'hybrid_vector_keyword', query_used: 'Rohini symbolism nakshatra', citations: [], rows: [], total: 0 },
    }))

    const result = await handler({ keyword: 'Rohini symbolism' })
    const obj = result.structuredContent.object as { content: Record<string, unknown> }

    expect(obj.content).toMatchObject({
      structured_filter_applied: false,
      fallback_reason: expect.stringMatching(/No structured catalog filter/),
      query_used: 'Rohini symbolism nakshatra',
    })
    const request = mockFetch.mock.calls[0]![1] as { body: string }
    expect(JSON.parse(request.body)).toMatchObject({ uri: 'marsys://tool/L0/query_classical_texts' })
  })
})
