import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryVicharaConstantsCapability } from '../query_vichara_constants'

describe('queryVicharaConstantsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 7 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ constant_key: 'ratification_step' }] })
    const result = await queryVicharaConstantsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM brahma_vichara_constants')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('constant_key filter is exact and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryVicharaConstantsCapability.handler({ constant_key: 'ratification_clamp' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('constant_key = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual(['ratification_clamp'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryVicharaConstantsCapability.handler({ constant_key: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('constant_key=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryVicharaConstantsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryVicharaConstantsCapability.scope).toBe('global')
    expect(queryVicharaConstantsCapability.required_inputs).toEqual([])
  })
})
