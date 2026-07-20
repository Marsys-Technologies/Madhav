import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryAvasthaSchemesCapability } from '../query_avastha_schemes'

describe('queryAvasthaSchemesCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 35 rows across 5 schemes', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ scheme_name: 'baladi', state_name: 'bala' }] })
    const result = await queryAvasthaSchemesCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('FROM bg_avastha_schemes')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('scheme_name filter is case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryAvasthaSchemesCapability.handler({ scheme_name: 'Deeptaadi' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('LOWER(scheme_name) = LOWER($1)')
    expect(params).toEqual(['Deeptaadi'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryAvasthaSchemesCapability.handler({ scheme_name: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('scheme_name=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryAvasthaSchemesCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryAvasthaSchemesCapability.scope).toBe('global')
    expect(queryAvasthaSchemesCapability.required_inputs).toEqual([])
  })
})
