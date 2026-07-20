import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryTransitEngineCapability } from '../query_transit_engine'

describe('queryTransitEngineCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 9 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ graha: 'moon', avg_daily_motion_deg: 13.176 }] })
    const result = await queryTransitEngineCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_transit_engine')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('graha filter is case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryTransitEngineCapability.handler({ graha: 'Rahu' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('LOWER(graha) = LOWER($1)')
    expect(mockQuery.mock.calls[0][1]).toEqual(['Rahu'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryTransitEngineCapability.handler({ graha: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('graha=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryTransitEngineCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryTransitEngineCapability.scope).toBe('global')
    expect(queryTransitEngineCapability.required_inputs).toEqual([])
  })
})
