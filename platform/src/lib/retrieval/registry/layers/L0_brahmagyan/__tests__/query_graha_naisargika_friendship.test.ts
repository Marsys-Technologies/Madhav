/**
 * query_graha_naisargika_friendship.test.ts — W2 dark-set wiring unit tests.
 * No live DB required — `query` is mocked (same pattern as get_yoga_dosha.test.ts).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryGrahaNaisargikaFriendshipCapability } from '../query_graha_naisargika_friendship'

describe('queryGrahaNaisargikaFriendshipCapability', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('no filters: queries all rows, no WHERE restriction beyond 1=1', async () => {
    mockQuery.mockResolvedValueOnce({
      rows: [
        { graha: 'Sun', other_graha: 'Moon', relation: 'friend', classical_citation: 'BPHS Ch.27' },
      ],
    })
    const result = await queryGrahaNaisargikaFriendshipCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('FROM bg_graha_naisargika_friendship')
    expect(sql).toContain('WHERE 1=1')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(1)
  })

  it('graha filter: case-insensitive match, param bound not string-interpolated', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryGrahaNaisargikaFriendshipCapability.handler({ graha: 'saturn' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('LOWER(graha) = LOWER($1)')
    expect(params).toEqual(['saturn'])
  })

  it('other_graha + relation filters combine with AND', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryGrahaNaisargikaFriendshipCapability.handler({ other_graha: 'Rahu', relation: 'enemy' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    const params = mockQuery.mock.calls[0][1] as unknown[]
    expect(sql).toContain('LOWER(other_graha) = LOWER($1)')
    expect(sql).toContain('relation = $2')
    expect(params).toEqual(['Rahu', 'enemy'])
  })

  it('empty result carries an honest empty_reason, not a silent []', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryGrahaNaisargikaFriendshipCapability.handler({ graha: 'Pluto' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('graha=Pluto')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('connection refused'))
    const result = await queryGrahaNaisargikaFriendshipCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
    expect(String((result.content as Record<string, unknown>)['error'])).toContain('connection refused')
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryGrahaNaisargikaFriendshipCapability.scope).toBe('global')
    expect(queryGrahaNaisargikaFriendshipCapability.required_inputs).toEqual([])
  })
})
