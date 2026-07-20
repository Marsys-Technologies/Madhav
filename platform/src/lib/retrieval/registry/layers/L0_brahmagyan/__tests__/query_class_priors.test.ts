import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryClassPriorsCapability } from '../query_class_priors'

describe('queryClassPriorsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all rows (bounded to 200)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ prior_version: 'v1.0', class_prior: 1.2 }] })
    const result = await queryClassPriorsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('FROM brahma_class_priors')
    expect(sql).toContain('LIMIT 200')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('signal_type_class filter is param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryClassPriorsCapability.handler({ signal_type_class: 'yoga' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('signal_type_class = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual(['yoga'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryClassPriorsCapability.handler({ prior_version: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('prior_version=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryClassPriorsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryClassPriorsCapability.scope).toBe('global')
    expect(queryClassPriorsCapability.required_inputs).toEqual([])
  })
})
