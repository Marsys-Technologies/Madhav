import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryDoshaCatalogCapability } from '../query_dosha_catalog'

type DoshaContent = {
  rows: unknown[]
  returned: number
  total: number
  limit: number
  offset: number
  truncated: boolean
}
type DoshaResult = { is_error: boolean; content: DoshaContent }
const handler = queryDoshaCatalogCapability.handler as (
  args: Record<string, unknown>,
  ctx?: Record<string, unknown>
) => Promise<DoshaResult>

describe('queryDoshaCatalogCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('documents the current 79-row catalog', () => {
    expect(queryDoshaCatalogCapability.description).toContain('79 canonical doshas')
  })

  it('no filter: defaults to the complete 79-row catalog and reports complete metadata', async () => {
    const rows = Array.from({ length: 79 }, (_, i) => ({ canonical_id: `dosha-${i + 1}`, name_en: `Dosha ${i + 1}` }))
    mockQuery.mockResolvedValueOnce({ rows })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '79' }] })

    const result = await handler({}, undefined)

    expect(result.is_error).toBe(false)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('FROM brahma_dosha_catalog')
    expect(sql).not.toContain('name_en ILIKE')
    expect(mockQuery.mock.calls[0][1]).toEqual([79, 0])
    expect(result.content.returned).toBe(79)
    expect(result.content.total).toBe(79)
    expect(result.content.truncated).toBe(false)
  })

  it('explicit pagination reports the true matching total rather than the page count', async () => {
    const rows = Array.from({ length: 10 }, (_, i) => ({ canonical_id: `dosha-${i + 11}` }))
    mockQuery.mockResolvedValueOnce({ rows })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '79' }] })

    const result = await handler({ limit: 10, offset: 10 }, undefined)

    expect(result.is_error).toBe(false)
    expect(result.content.returned).toBe(10)
    expect(result.content.total).toBe(79)
    expect(result.content.truncated).toBe(true)
  })

  it("dosha_name='mangal' matches via synonym expansion even though 'mangal' is not a substring of 'Manglik'", async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ canonical_id: 'manglik', name_en: 'Manglik Dosha' }] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '1' }] })
    await queryDoshaCatalogCapability.handler({ dosha_name: 'mangal' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    // 'manglik' is not a literal substring of the term 'mangal' or vice versa in JS terms —
    // this asserts the underlying finding: 'mangal' does NOT occur inside 'manglik'.
    expect('manglik'.includes('mangal')).toBe(false)
    // the synonym group must still cause the handler to search for 'manglik' and 'kuja' too
    expect(params).toContain('%manglik%')
    expect(params).toContain('%kuja%')
    expect(params).toContain('%mangal%')
    expect(sql).toContain('name_en ILIKE')
    expect(sql).toContain('name_sa ILIKE')
    expect(sql).toContain('canonical_id ILIKE')
  })

  it("dosha_name='Mangal' (mixed case) also expands via synonym group", async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    await queryDoshaCatalogCapability.handler({ dosha_name: 'Mangal' }, undefined)
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(params).toContain('%manglik%')
    expect(params).toContain('%kuja%')
  })

  it("dosha_name='kuja' also expands to reach the primary Manglik entry", async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    await queryDoshaCatalogCapability.handler({ dosha_name: 'kuja' }, undefined)
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(params).toContain('%mangal%')
    expect(params).toContain('%manglik%')
    expect(params).toContain('%kuja%')
  })

  it('dosha_name with no synonym match (e.g. "kemadruma") stays a single-term search', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    await queryDoshaCatalogCapability.handler({ dosha_name: 'kemadruma' }, undefined)
    const params = mockQuery.mock.calls[0][1] as unknown[]
    // exactly one search term, then limit and offset
    expect(params.length).toBe(3)
    expect(params[0]).toBe('%kemadruma%')
  })

  it('severity filter is still param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    await queryDoshaCatalogCapability.handler({ severity: 'severe' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('severity_grades ? $')
    expect(mockQuery.mock.calls[0][1]).toContain('severe')
  })

  it('domain filter maps to category column', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    await queryDoshaCatalogCapability.handler({ domain: 'graha_placement' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('category = $')
    expect(mockQuery.mock.calls[0][1]).toContain('graha_placement')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryDoshaCatalogCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryDoshaCatalogCapability.scope).toBe('global')
    expect(queryDoshaCatalogCapability.required_inputs).toEqual([])
  })
})
