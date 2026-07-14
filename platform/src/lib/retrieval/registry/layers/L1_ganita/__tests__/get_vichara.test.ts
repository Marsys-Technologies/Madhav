/**
 * get_vichara.test.ts — Lane 5 (§N.6 density retrofit) unit tests for the new
 * ganita_vichara_get registry capability. No live DB required — `query` is mocked.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { getVicharaCapability } from '../get_vichara'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('getVicharaCapability (ganita_vichara_get)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('rejects an unknown family loudly (CR-42 — never silently unfiltered)', async () => {
    const result = await getVicharaCapability.handler({ chart_id: CHART_ID, family: 'not_a_family' }, undefined)
    expect(result.is_error).toBe(true)
    const content = result.content as Record<string, unknown>
    expect(String(content['error'])).toMatch(/Unknown family/)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('rejects an unknown domain loudly', async () => {
    const result = await getVicharaCapability.handler({ chart_id: CHART_ID, domain: 'astrology_of_pets' }, undefined)
    expect(result.is_error).toBe(true)
    const content = result.content as Record<string, unknown>
    expect(String(content['error'])).toMatch(/Unknown domain/)
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('requires chart_id', async () => {
    const result = await getVicharaCapability.handler({}, undefined)
    expect(result.is_error).toBe(true)
  })

  it('applies case-insensitive subject matching (CR-10) via UPPER() comparison', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] }) // rows
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] }) // count
    mockQuery.mockResolvedValueOnce({ rows: [] }) // family counts
    await getVicharaCapability.handler({ chart_id: CHART_ID, subject: 'venus' }, undefined)
    const rowsSql = mockQuery.mock.calls[0][0] as string
    expect(rowsSql).toMatch(/UPPER\(subject\) = UPPER\(/)
  })

  it('degrades honestly (not an error) when chart_vichara does not exist yet', async () => {
    mockQuery.mockRejectedValueOnce(new Error('relation "chart_vichara" does not exist'))
    const result = await getVicharaCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['rows']).toEqual([])
    expect(String(content['empty_reason'])).toMatch(/has not been built yet/)
    const provenance = content['provenance'] as Record<string, unknown>
    expect(provenance['status']).toBe('asset_not_built')
  })

  it('surfaces a genuine internal error (not the missing-table branch) as is_error', async () => {
    mockQuery.mockRejectedValueOnce(new Error('connection terminated unexpectedly'))
    const result = await getVicharaCapability.handler({ chart_id: CHART_ID }, undefined)
    expect(result.is_error).toBe(true)
  })

  it('builds family_counts + empty_reason correctly on a populated result', async () => {
    const rows = [
      { id: '1', vichara_family: 'leverage_index', subject: 'VENUS', domain: 'wealth', value_num: 1.8 },
    ]
    mockQuery.mockResolvedValueOnce({ rows }) // rows query
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '1' }] }) // count query
    mockQuery.mockResolvedValueOnce({ rows: [{ vichara_family: 'leverage_index', n: '1' }] }) // family counts
    const result = await getVicharaCapability.handler({ chart_id: CHART_ID, family: 'leverage_index' }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['empty_reason']).toBeUndefined()
    const verdict = content['verdict'] as Record<string, unknown>
    expect(verdict['total_rows']).toBe(1)
    expect((verdict['family_counts'] as Record<string, number>)['leverage_index']).toBe(1)
  })

  it('reports empty_reason with the applied filters named when genuinely zero rows (not a missing table)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await getVicharaCapability.handler({ chart_id: CHART_ID, family: 'leverage_index', domain: 'wealth' }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(String(content['empty_reason'])).toMatch(/leverage_index/)
    expect(String(content['empty_reason'])).toMatch(/wealth/)
  })
})
