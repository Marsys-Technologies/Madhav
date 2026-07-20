import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryGrahaDikCapability } from '../query_graha_dik'

describe('queryGrahaDikCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 9 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ graha: 'sun', peak_house: 10 }] })
    const result = await queryGrahaDikCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_graha_dik')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('graha filter is case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryGrahaDikCapability.handler({ graha: 'Saturn' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('LOWER(graha) = LOWER($1)')
    expect(mockQuery.mock.calls[0][1]).toEqual(['Saturn'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryGrahaDikCapability.handler({ graha: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('graha=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryGrahaDikCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryGrahaDikCapability.scope).toBe('global')
    expect(queryGrahaDikCapability.required_inputs).toEqual([])
  })
})
