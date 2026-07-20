import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryVastuDirectionsCapability } from '../query_vastu_directions'

describe('queryVastuDirectionsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 8 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ direction: 'North', ruling_graha: 'Mercury' }] })
    const result = await queryVastuDirectionsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_vastu_directions')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('direction + ruling_graha filters are case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryVastuDirectionsCapability.handler({ direction: 'Northeast', ruling_graha: 'Jupiter' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('LOWER(direction) = LOWER($1)')
    expect(sql).toContain('LOWER(ruling_graha) = LOWER($2)')
    expect(params).toEqual(['Northeast', 'Jupiter'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryVastuDirectionsCapability.handler({ direction: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('direction=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryVastuDirectionsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryVastuDirectionsCapability.scope).toBe('global')
    expect(queryVastuDirectionsCapability.required_inputs).toEqual([])
  })
})
