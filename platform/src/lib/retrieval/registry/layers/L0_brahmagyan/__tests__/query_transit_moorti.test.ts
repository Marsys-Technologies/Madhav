import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryTransitMoortiCapability } from '../query_transit_moorti'

describe('queryTransitMoortiCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 27 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ nakshatra_offset: 1, moorti_name: 'swarna' }] })
    const result = await queryTransitMoortiCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_transit_moorti')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('nakshatra_offset filter is integer-checked and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryTransitMoortiCapability.handler({ nakshatra_offset: 9 }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('nakshatra_offset = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual([9])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryTransitMoortiCapability.handler({ nakshatra_offset: 99 }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('nakshatra_offset=99')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryTransitMoortiCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryTransitMoortiCapability.scope).toBe('global')
    expect(queryTransitMoortiCapability.required_inputs).toEqual([])
  })
})
