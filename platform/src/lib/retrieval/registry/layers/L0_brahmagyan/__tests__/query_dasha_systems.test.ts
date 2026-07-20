import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryDashaSystemsCapability } from '../query_dasha_systems'

describe('queryDashaSystemsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 18 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ canonical_id: 'vimshottari', school: 'parashari' }] })
    const result = await queryDashaSystemsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM brahma_dasha_systems')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('school filter is case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryDashaSystemsCapability.handler({ school: 'Jaimini' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('LOWER(school) = LOWER($1)')
    expect(mockQuery.mock.calls[0][1]).toEqual(['Jaimini'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryDashaSystemsCapability.handler({ canonical_id: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('canonical_id=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryDashaSystemsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryDashaSystemsCapability.scope).toBe('global')
    expect(queryDashaSystemsCapability.required_inputs).toEqual([])
  })
})
