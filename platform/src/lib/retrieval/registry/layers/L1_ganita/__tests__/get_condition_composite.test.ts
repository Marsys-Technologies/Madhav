import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getConditionCompositeCapability } from '../get_condition_composite'

const CHART_ID = 'test-chart-uuid-0001'

describe('getConditionCompositeCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('requires chart_id', async () => {
    const result = await getConditionCompositeCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('with chart_id: queries ga_condition_composite scoped to chart_id, bounded, with total', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ graha: 'Sun', condition_score: 0.82 }] })
      .mockResolvedValueOnce({ rows: [{ total: '9' }] })
    const result = await getConditionCompositeCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['total_matching']).toBe(9)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('FROM ga_condition_composite')
    expect(sql).toContain('chart_id = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual([CHART_ID, 50])
  })

  it('graha + ayanamsha_id filters are param-bound', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ total: '0' }] })
    await getConditionCompositeCapability.handler({ chart_id: CHART_ID, graha: 'Mars', ayanamsha_id: 'lahiri' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('graha = $2')
    expect(sql).toContain('ayanamsha_id = $3')
    expect(params).toEqual([CHART_ID, 'Mars', 'lahiri', 50])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ total: '0' }] })
    const result = await getConditionCompositeCapability.handler({ chart_id: CHART_ID, graha: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('graha=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await getConditionCompositeCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: per_chart scope requires chart_id', () => {
    expect(getConditionCompositeCapability.scope).toBe('per_chart')
    expect(getConditionCompositeCapability.required_inputs).toContain('chart_id')
  })
})
