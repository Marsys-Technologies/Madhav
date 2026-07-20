import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryMotionStateThresholdsCapability } from '../query_motion_state_thresholds'

describe('queryMotionStateThresholdsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 27 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ graha: 'Mars', motion_state: 'vakra' }] })
    const result = await queryMotionStateThresholdsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_motion_state_thresholds')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('graha + motion_state filters are case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryMotionStateThresholdsCapability.handler({ graha: 'Mercury', motion_state: 'Atichara' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('LOWER(graha) = LOWER($1)')
    expect(sql).toContain('LOWER(motion_state) = LOWER($2)')
    expect(params).toEqual(['Mercury', 'Atichara'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryMotionStateThresholdsCapability.handler({ graha: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('graha=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryMotionStateThresholdsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryMotionStateThresholdsCapability.scope).toBe('global')
    expect(queryMotionStateThresholdsCapability.required_inputs).toEqual([])
  })
})
