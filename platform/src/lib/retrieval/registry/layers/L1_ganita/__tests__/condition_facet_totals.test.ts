import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getAvasthsCapability } from '../get_avasthas'
import { getDignityCapability } from '../get_dignity'
import { getKarakasCapability } from '../get_karakas'

const CHART_ID = 'test-chart-uuid-0001'

const facets = [
  ['dignity', getDignityCapability, { limit: 3 }],
  ['avasthas', getAvasthsCapability, { limit: 3 }],
  ['karakas', getKarakasCapability, { limit: 3 }],
] as const

describe('condition facet pagination receipts', () => {
  beforeEach(() => mockQuery.mockReset())

  it.each(facets)('%s reports the matching total rather than its limited page size', async (_name, capability, args) => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ fact_id: 'one' }, { fact_id: 'two' }, { fact_id: 'three' }] })
      .mockResolvedValueOnce({ rows: [{ total: '563' }] })

    const result = await capability.handler({ chart_id: CHART_ID, ...args }, undefined)

    expect(result.is_error).toBe(false)
    expect((result.content as Record<string, unknown>).total).toBe(563)
    expect(mockQuery).toHaveBeenCalledTimes(2)

    const [pageSql, pageParams] = mockQuery.mock.calls[0] as [string, unknown[]]
    const [countSql, countParams] = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(pageSql).toContain('LIMIT $3 OFFSET $4')
    expect(countSql).toContain('SELECT COUNT(*)::text AS total')
    expect(countSql).not.toContain('LIMIT')
    expect(countParams).toEqual(pageParams.slice(0, 2))
  })

  it.each(facets)('%s keeps optional filters identical for page and count queries', async (_name, capability, args) => {
    mockQuery
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ total: '0' }] })

    await capability.handler({ chart_id: CHART_ID, ...args, ayanamsha_id: 'lahiri' }, undefined)

    const [pageSql, pageParams] = mockQuery.mock.calls[0] as [string, unknown[]]
    const [countSql, countParams] = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(pageSql).toContain('ayanamsha_id = $3')
    expect(countSql).toContain('ayanamsha_id = $3')
    expect(pageParams).toEqual([CHART_ID, expect.any(Array), 'lahiri', 3, 0])
    expect(countParams).toEqual([CHART_ID, expect.any(Array), 'lahiri'])
  })

  it('dignity includes both ayanamsha and varga filters in its count', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ total: '0' }] })

    await getDignityCapability.handler({ chart_id: CHART_ID, limit: 3, ayanamsha_id: 'lahiri', varga: 'D1' }, undefined)

    const [pageSql, pageParams] = mockQuery.mock.calls[0] as [string, unknown[]]
    const [countSql, countParams] = mockQuery.mock.calls[1] as [string, unknown[]]
    expect(pageSql).toContain('fact_key ILIKE $4')
    expect(countSql).toContain('fact_key ILIKE $4')
    expect(pageParams).toEqual([CHART_ID, expect.any(Array), 'lahiri', '%D1%', 3, 0])
    expect(countParams).toEqual([CHART_ID, expect.any(Array), 'lahiri', '%D1%'])
  })
})
