import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryPrashnaLagnaMethodsCapability } from '../query_prashna_lagna_methods'

describe('queryPrashnaLagnaMethodsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 5 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ method_id: 'm1', tradition: 'tajika' }] })
    const result = await queryPrashnaLagnaMethodsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_prashna_lagna_methods')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('tradition filter is case-insensitive and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryPrashnaLagnaMethodsCapability.handler({ tradition: 'KP' }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('LOWER(tradition) = LOWER($1)')
    expect(mockQuery.mock.calls[0][1]).toEqual(['KP'])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryPrashnaLagnaMethodsCapability.handler({ method_id: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('method_id=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryPrashnaLagnaMethodsCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryPrashnaLagnaMethodsCapability.scope).toBe('global')
    expect(queryPrashnaLagnaMethodsCapability.required_inputs).toEqual([])
  })
})
