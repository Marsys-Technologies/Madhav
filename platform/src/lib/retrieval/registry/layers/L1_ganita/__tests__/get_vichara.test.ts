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

  // D-2 §6.1 finding fix (D-4a Lane A-1): chart_vichara.subject stores the graha CODE
  // ('VEN'), not the full name — subject='venus' previously false-emptied even though
  // rows exist under 'VEN'. Retry-with-resolved-code + disclosed subject_alias_resolved.
  it('resolves subject=venus (full name, no literal match) to VEN via the shared graha alias table and discloses the resolution', async () => {
    // First attempt: literal UPPER(subject)=UPPER('venus') -> 0 rows (stored subject is 'VEN', not 'VENUS').
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    mockQuery.mockResolvedValueOnce({ rows: [] })
    // Retry attempt with resolved code 'VEN': real rows exist.
    const rows = [{ id: '1', vichara_family: 'leverage_index', subject: 'VEN', domain: 'wealth', value_num: 3.94 }]
    mockQuery.mockResolvedValueOnce({ rows })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '1' }] })
    mockQuery.mockResolvedValueOnce({ rows: [{ vichara_family: 'leverage_index', n: '1' }] })

    const result = await getVicharaCapability.handler({ chart_id: CHART_ID, family: 'leverage_index', subject: 'venus' }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['empty_reason']).toBeUndefined()
    expect(content['total_matching']).toBe(1)
    expect((content['rows'] as unknown[]).length).toBe(1)
    expect(content['subject_alias_resolved']).toEqual({ input: 'venus', resolved_code: 'VEN' })
    // The retry must have used the resolved code, not the literal 'venus', in its params.
    expect(mockQuery).toHaveBeenCalledTimes(6)
    const retryCountParams = mockQuery.mock.calls[4][1] as unknown[]
    expect(retryCountParams[retryCountParams.length - 1]).toBe('VEN')
  })

  it('leaves an unrecognized subject value as an honest zero-row result (no alias match, no crash)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '0' }] })
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const result = await getVicharaCapability.handler({ chart_id: CHART_ID, subject: 'not_a_graha_at_all' }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['subject_alias_resolved']).toBeUndefined()
    expect(String(content['empty_reason'])).toMatch(/subject/)
    expect(mockQuery).toHaveBeenCalledTimes(3) // no retry attempted — grahaCodeOf() threw, nothing to retry with
  })

  it('does not retry when the literal subject already matches a code (VEN produces rows on the first pass)', async () => {
    const rows = [{ id: '1', vichara_family: 'leverage_index', subject: 'VEN', domain: 'wealth', value_num: 3.94 }]
    mockQuery.mockResolvedValueOnce({ rows })
    mockQuery.mockResolvedValueOnce({ rows: [{ total: '1' }] })
    mockQuery.mockResolvedValueOnce({ rows: [{ vichara_family: 'leverage_index', n: '1' }] })
    const result = await getVicharaCapability.handler({ chart_id: CHART_ID, subject: 'VEN' }, undefined)
    expect(result.is_error).toBe(false)
    const content = result.content as Record<string, unknown>
    expect(content['subject_alias_resolved']).toBeUndefined()
    expect(mockQuery).toHaveBeenCalledTimes(3) // already had rows on the first pass — no retry needed
  })
})
