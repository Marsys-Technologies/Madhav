import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryTransitAvGatesCapability } from '../query_transit_av_gates'

describe('queryTransitAvGatesCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 8 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ gate_kind: 'kakshya', graha: 'jupiter' }] })
    const result = await queryTransitAvGatesCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_transit_av_gates')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('gate_kind + graha filters are param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryTransitAvGatesCapability.handler({ gate_kind: 'sav_threshold', graha: 'Venus' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('gate_kind = $1')
    expect(sql).toContain('LOWER(graha) = LOWER($2)')
    expect(params).toEqual(['sav_threshold', 'Venus'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryTransitAvGatesCapability.handler({ gate_kind: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('gate_kind=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryTransitAvGatesCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryTransitAvGatesCapability.scope).toBe('global')
    expect(queryTransitAvGatesCapability.required_inputs).toEqual([])
  })
})
