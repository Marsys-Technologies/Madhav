import { describe, it, expect, vi, beforeEach } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

import { queryClassPriorsCapability, LIFETIME_COUNT_FACT_KIND } from '../query_class_priors'

describe('queryClassPriorsCapability', () => {
  beforeEach(() => { mockQuery.mockReset() })

  it('no filter: queries all salience rows (bounded to 200)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ prior_version: 'v1.0', class_prior: 1.2 }] })
    const result = await queryClassPriorsCapability.handler({}, undefined)
    expect(result.is_error).toBe(false)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain('FROM brahma_class_priors')
    expect(sql).toContain('LIMIT 200')
    expect(mockQuery.mock.calls[0][1]).toEqual([])
  })

  // ── ṢAḌ-DARŚANA W2 lane `l0-ne-priors`: the N_e rows written by
  //    bg_class_lifetime_counts (migration 522) share this table and the
  //    class_prior column but are EXPECTED EVENT COUNTS, not ranking multipliers.
  //    Serving both in one flat array is the §N.6 density violation this excludes.

  it('EXCLUDES the N_e lifetime-count coordinate from every query', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    await queryClassPriorsCapability.handler({}, undefined)
    const sql = mockQuery.mock.calls[0][0] as string
    expect(sql).toContain(`fact_kind <> '${LIFETIME_COUNT_FACT_KIND}'`)
  })

  it('the exclusion survives every user filter combination', async () => {
    for (const args of [
      {},
      { prior_version: 'ne_v01' },
      { signal_type_class: 'childbirth' },
      { prior_version: 'ne_v01', signal_type_class: 'marriage', source_subsystem: '*' },
    ]) {
      mockQuery.mockReset()
      mockQuery.mockResolvedValueOnce({ rows: [] })
      await queryClassPriorsCapability.handler(args, undefined)
      const sql = mockQuery.mock.calls[0][0] as string
      expect(sql, `args=${JSON.stringify(args)}`).toContain(
        `fact_kind <> '${LIFETIME_COUNT_FACT_KIND}'`,
      )
    }
  })

  it('discloses the exclusion as a named field, not silently (B.10)', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ prior_version: '1.0', class_prior: 1.2 }] })
    const result = await queryClassPriorsCapability.handler({}, undefined)
    const content = result.content as Record<string, unknown>
    expect(content['excluded_fact_kinds']).toEqual([LIFETIME_COUNT_FACT_KIND])
    expect(String(content['excluded_note'])).toContain('bg_class_lifetime_counts')
  })

  it('the description states the scope narrowing', () => {
    expect(queryClassPriorsCapability.description).toContain(LIFETIME_COUNT_FACT_KIND)
    expect(queryClassPriorsCapability.description).toContain('bg_class_lifetime_counts')
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
