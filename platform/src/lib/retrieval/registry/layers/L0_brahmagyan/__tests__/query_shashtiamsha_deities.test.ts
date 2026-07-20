import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryShashtiamshaDeitiesCapability } from '../query_shashtiamsha_deities'

describe('queryShashtiamshaDeitiesCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 60 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ amsa_number: 1, quality: 'soumya', deity_name: null }] })
    const result = await queryShashtiamshaDeitiesCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_shashtiamsha_deities')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('amsa_number filter is integer-checked and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryShashtiamshaDeitiesCapability.handler({ amsa_number: 30 }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('amsa_number = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual([30])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryShashtiamshaDeitiesCapability.handler({ amsa_number: 99 }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('amsa_number=99')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryShashtiamshaDeitiesCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required, deity_name floor disclosed', () => {
    expect(queryShashtiamshaDeitiesCapability.scope).toBe('global')
    expect(queryShashtiamshaDeitiesCapability.required_inputs).toEqual([])
    expect(queryShashtiamshaDeitiesCapability.description).toContain('NULL')
  })
})
