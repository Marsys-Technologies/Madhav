import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryPrashnaSpecialTechniquesCapability } from '../query_prashna_special_techniques'

describe('queryPrashnaSpecialTechniquesCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 3 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ technique_id: 't1' }] })
    const result = await queryPrashnaSpecialTechniquesCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_prashna_special_techniques')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('technique_id filter is exact and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryPrashnaSpecialTechniquesCapability.handler({ technique_id: 't2' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('technique_id = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual(['t2'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryPrashnaSpecialTechniquesCapability.handler({ technique_id: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('technique_id=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryPrashnaSpecialTechniquesCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryPrashnaSpecialTechniquesCapability.scope).toBe('global')
    expect(queryPrashnaSpecialTechniquesCapability.required_inputs).toEqual([])
  })
})
