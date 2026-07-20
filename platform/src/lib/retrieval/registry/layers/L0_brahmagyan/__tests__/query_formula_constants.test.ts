import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryFormulaConstantsCapability } from '../query_formula_constants'

describe('queryFormulaConstantsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 18 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ constant_id: 'c1', class: 'classical' }] })
    const result = await queryFormulaConstantsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM brahma_formula_constants')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('class filter is exact and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryFormulaConstantsCapability.handler({ class: 'native_judgment' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('class = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual(['native_judgment'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryFormulaConstantsCapability.handler({ constant_id: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('constant_id=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryFormulaConstantsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryFormulaConstantsCapability.scope).toBe('global')
    expect(queryFormulaConstantsCapability.required_inputs).toEqual([])
  })
})
