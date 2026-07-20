import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryPrashnaFructificationRulesCapability } from '../query_prashna_fructification_rules'

describe('queryPrashnaFructificationRulesCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 5 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ rule_id: 'r1', time_unit: 'days' }] })
    const result = await queryPrashnaFructificationRulesCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_prashna_fructification_rules')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('time_unit filter is case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryPrashnaFructificationRulesCapability.handler({ time_unit: 'Months' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('LOWER(time_unit) = LOWER($1)')
    expect(mockQuery.mock.calls[0][1]).toEqual(['Months'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryPrashnaFructificationRulesCapability.handler({ rule_id: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('rule_id=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryPrashnaFructificationRulesCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryPrashnaFructificationRulesCapability.scope).toBe('global')
    expect(queryPrashnaFructificationRulesCapability.required_inputs).toEqual([])
  })
})
