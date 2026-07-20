import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryVastuDirectionRemedialsCapability } from '../query_vastu_direction_remedials'

describe('queryVastuDirectionRemedialsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 24 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ direction: 'North', remedy_type: 'color' }] })
    const result = await queryVastuDirectionRemedialsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_vastu_direction_remedials')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('direction + remedy_type filters are case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryVastuDirectionRemedialsCapability.handler({ direction: 'South', remedy_type: 'Symbol' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('LOWER(direction) = LOWER($1)')
    expect(sql).toContain('LOWER(remedy_type) = LOWER($2)')
    expect(params).toEqual(['South', 'Symbol'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryVastuDirectionRemedialsCapability.handler({ direction: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('direction=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryVastuDirectionRemedialsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryVastuDirectionRemedialsCapability.scope).toBe('global')
    expect(queryVastuDirectionRemedialsCapability.required_inputs).toEqual([])
  })
})
