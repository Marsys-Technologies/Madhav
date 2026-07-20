import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryTransitVedhaCapability } from '../query_transit_vedha'

describe('queryTransitVedhaCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 33 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ primary_graha: 'sun', primary_transit_house: 3 }] })
    const result = await queryTransitVedhaCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_transit_vedha')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('primary_graha + primary_transit_house filters are param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryTransitVedhaCapability.handler({ primary_graha: 'Sun', primary_transit_house: 3 }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('LOWER(primary_graha) = LOWER($1)')
    expect(sql).toContain('primary_transit_house = $2')
    expect(params).toEqual(['Sun', 3])
  })

  it('empty result carries an honest empty_reason and the governance-anomaly note', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryTransitVedhaCapability.handler({ primary_graha: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('primary_graha=nope')
    expect(String(content['governance_note'])).toContain('no CREATE TABLE migration')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryTransitVedhaCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryTransitVedhaCapability.scope).toBe('global')
    expect(queryTransitVedhaCapability.required_inputs).toEqual([])
  })
})
