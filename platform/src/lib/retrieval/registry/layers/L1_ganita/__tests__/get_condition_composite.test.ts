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

  // ── X2 / I-29: the D1 fallback is VISIBLE (served field + Dens facet + separate count) ──

  it('selects varga_fallback_used / varga_fallback_reason as top-level served fields', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ total: '0' }] })
    await getConditionCompositeCapability.handler({ chart_id: CHART_ID }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain("condition_score_breakdown->>'varga_fallback_used'")
    expect(sql).toContain('AS varga_fallback_used')
    expect(sql).toContain("condition_score_breakdown->>'varga_fallback_reason' AS varga_fallback_reason")
    // tri-state: an absent flag is NULL, never coerced to false (CLAUDE.md §N.7 item 6)
    expect(sql).toMatch(/WHEN 'true' THEN true WHEN 'false' THEN false END/)
  })

  it('varga_fallback_used is a declared Dens facet AND a declared input', () => {
    expect(getConditionCompositeCapability.density_contract?.facets).toContain('varga_fallback_used')
    expect(getConditionCompositeCapability.input_schema).toHaveProperty('varga_fallback_used')
  })

  it('varga_fallback_used filter is param-bound (true and "false" both accepted); junk is ignored, not guessed', async () => {
    for (const [arg, expected] of [[true, true], ['false', false], ['yes', null]] as const) {
      mockQuery.mockReset()
      mockQuery
        .mockResolvedValueOnce({ rows: [] })
        .mockResolvedValueOnce({ rows: [{ total: '0' }] })
      await getConditionCompositeCapability.handler({ chart_id: CHART_ID, varga_fallback_used: arg }, undefined)
      const sql = mockQuery.mock.calls[0][0] as string
      const params = mockQuery.mock.calls[0][1] as unknown[]
      if (expected === null) {
        expect(params).toEqual([CHART_ID, 50])
      } else {
        expect(sql).toContain('= $2')
        expect(params).toEqual([CHART_ID, expected, 50])
      }
    }
  })

  it('counts D1-fallback rows in the page and over the full filtered set, separately, with a note', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [
        { graha: 'Sun',  condition_score: 0.335, varga_fallback_used: true },
        { graha: 'Moon', condition_score: 0.61,  varga_fallback_used: false },
        { graha: 'Mars', condition_score: null,  varga_fallback_used: null },
      ] })
      .mockResolvedValueOnce({ rows: [{ total: '135', d1_fallback_total: '90', divisional_total: '45' }] })
    const result = await getConditionCompositeCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['d1_fallback_rows_in_page']).toBe(1)
    expect(content['d1_fallback_total_matching']).toBe(90)
    expect(String(content['d1_fallback_note'])).toContain('D1 dignity ALONE')
    const countSql = mockQuery.mock.calls[1][0] as string
    expect(countSql).toContain('FILTER (WHERE')
    expect(countSql).toContain('IS TRUE')
  })

  it('no D1-fallback rows: count is 0 and no note is shown', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ graha: 'Sun', condition_score: 0.3, varga_fallback_used: false }] })
      .mockResolvedValueOnce({ rows: [{ total: '45', d1_fallback_total: '0', divisional_total: '45' }] })
    const result = await getConditionCompositeCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['d1_fallback_rows_in_page']).toBe(0)
    expect(content['d1_fallback_total_matching']).toBe(0)
    expect(content).not.toHaveProperty('d1_fallback_note')
  })

  it('full-set fallback count is null (honest), not 0, when the count query did not return it', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ graha: 'Sun', condition_score: 0.3 }] })
      .mockResolvedValueOnce({ rows: [{ total: '9' }] })
    const result = await getConditionCompositeCapability.handler({ chart_id: CHART_ID }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['d1_fallback_total_matching']).toBeNull()
  })

  it('descriptor: per_chart scope requires chart_id', () => {
    expect(getConditionCompositeCapability.scope).toBe('per_chart')
    expect(getConditionCompositeCapability.required_inputs).toContain('chart_id')
  })
})
