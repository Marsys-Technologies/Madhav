import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getPrashnaLagnaCapability } from '../get_prashna_lagna'

const PRASHNA_CHART_ID = 'test-prashna-chart-uuid-0001'

describe('getPrashnaLagnaCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('requires chart_id', async () => {
    const result = await getPrashnaLagnaCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('with chart_id: queries ga_prashna_lagna scoped to chart_id', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [{ lagna_method: 'tajik_moment_lagna', lagna_rashi: 'Aries' }] })
      .mockResolvedValueOnce({ rows: [{ total: '1' }] })
    const result = await getPrashnaLagnaCapability.handler({ chart_id: PRASHNA_CHART_ID }, undefined)
    expect(result.is_error).toBe(false)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('FROM ga_prashna_lagna')
    expect(sql).toContain('chart_id = $1')
    expect(mockQuery.mock.calls[0][1]).toEqual([PRASHNA_CHART_ID, 20])
  })

  it('primary_only filter adds is_primary = TRUE with no extra param', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ total: '0' }] })
    await getPrashnaLagnaCapability.handler({ chart_id: PRASHNA_CHART_ID, primary_only: true }, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('is_primary = TRUE')
  })

  it('empty result carries an honest empty_reason', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [{ total: '0' }] })
    const result = await getPrashnaLagnaCapability.handler({ chart_id: PRASHNA_CHART_ID, lagna_method: 'nope' }, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['count']).toBe(0)
    expect(String(content['empty_reason'])).toContain('lagna_method=nope')
  })

  it('DB error surfaces as is_error, not thrown', async () => {
    mockQuery.mockRejectedValueOnce(new Error('timeout'))
    const result = await getPrashnaLagnaCapability.handler({ chart_id: PRASHNA_CHART_ID }, undefined)
    expect(result.is_error).toBe(true)
  })

  it('descriptor: per_chart scope requires chart_id', () => {
    expect(getPrashnaLagnaCapability.scope).toBe('per_chart')
    expect(getPrashnaLagnaCapability.required_inputs).toContain('chart_id')
  })
})
