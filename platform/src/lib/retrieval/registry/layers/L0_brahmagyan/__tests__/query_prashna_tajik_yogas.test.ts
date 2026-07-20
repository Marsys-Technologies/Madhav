import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryPrashnaTajikYogasCapability } from '../query_prashna_tajik_yogas'

describe('queryPrashnaTajikYogasCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all 16 rows', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ yoga_id: 'y1' }] })
    const result = await queryPrashnaTajikYogasCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    expect(mockQuery.mock.calls[0][0] as string).toContain('FROM bg_prashna_tajik_yogas')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  it('is_fructification_indicator filter is boolean and param-bound', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryPrashnaTajikYogasCapability.handler({ is_fructification_indicator: true }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('is_fructification_indicator = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual([true])
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await queryPrashnaTajikYogasCapability.handler({ yoga_id: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('yoga_id=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await queryPrashnaTajikYogasCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: global scope, no chart_id required', () => {
    expect(queryPrashnaTajikYogasCapability.scope).toBe('global')
    expect(queryPrashnaTajikYogasCapability.required_inputs).toEqual([])
  })
})
