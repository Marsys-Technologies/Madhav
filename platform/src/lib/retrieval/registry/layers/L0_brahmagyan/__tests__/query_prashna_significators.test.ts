import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryPrashnaSignificatorsCapability } from '../query_prashna_significators'

describe('queryPrashnaSignificatorsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 12 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ question_class: 'marriage' }] })
    const result = await queryPrashnaSignificatorsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_prashna_significators')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('question_class filter is case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryPrashnaSignificatorsCapability.handler({ question_class: 'Career' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('LOWER(question_class) = LOWER($1)')
    expect(mockQuery.mock.calls[0][1]).toEqual(['Career'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryPrashnaSignificatorsCapability.handler({ question_class: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('question_class=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryPrashnaSignificatorsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryPrashnaSignificatorsCapability.scope).toBe('global')
    expect(queryPrashnaSignificatorsCapability.required_inputs).toEqual([])
  })
})
