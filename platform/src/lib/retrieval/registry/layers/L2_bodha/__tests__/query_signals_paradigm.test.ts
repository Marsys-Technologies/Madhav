/**
 * query_signals — the PARADIGM facet: unit tests (design §27.4, R5 W2)
 * ========================================================================
 * Tests the `paradigm` param added to query_signals (design §27.4): filters
 * bodha_msr_signals.signal_tradition to one coherent classical school, defaulting
 * to no filter (every tradition returned, individually tagged). DB is mocked —
 * no live connection required.
 *
 * Scope:
 *   1. paradigm omitted → no signal_tradition filter added to the SQL/params
 *   2. paradigm='jaimini'/'kp'/'tajika'/'parashari' → signal_tradition = $n filter added,
 *      with the paradigm value as the bound param
 *   3. an out-of-vocabulary paradigm (e.g. 'esoteric', not one of design §27.4's 4 named
 *      paradigms) is rejected with is_error, not silently accepted
 *   4. provenance.paradigm_note reflects whichever branch fired
 */

import { describe, it, expect, vi } from 'vitest'

const CHART_A = '33333333-cccc-4ccc-cccc-cccccccccccc'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    if (sql.includes('FROM bodha_msr_signals')) return { rows: [] }
    if (sql.includes('FROM chart_facts')) return { rows: [] }
    return { rows: [] }
  }),
}))

import { query as mockQuery } from '@/lib/db/client'
import { querySignalsCapability } from '../query_signals'

describe('query_signals — paradigm facet (design §27.4)', () => {
  it('omitting paradigm adds no signal_tradition filter', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler({ chart_id: CHART_A }, {})
    expect(result.is_error).toBe(false)
    const [sql] = vi.mocked(mockQuery).mock.calls[0] as [string, unknown[]]
    expect(sql).not.toContain('signal_tradition =')
    const content = result.content as Record<string, unknown>
    const provenance = content.provenance as Record<string, unknown>
    expect(String(provenance.paradigm_note)).toMatch(/No paradigm filter applied/)
  })

  for (const paradigm of ['parashari', 'jaimini', 'kp', 'tajika']) {
    it(`paradigm='${paradigm}' filters on m.signal_tradition = $n bound to '${paradigm}'`, async () => {
      vi.mocked(mockQuery).mockClear()
      const result = await querySignalsCapability.handler({ chart_id: CHART_A, paradigm }, {})
      expect(result.is_error).toBe(false)
      const [sql, params] = vi.mocked(mockQuery).mock.calls[0] as [string, unknown[]]
      expect(sql).toContain('m.signal_tradition = $')
      expect(params).toContain(paradigm)
      const content = result.content as Record<string, unknown>
      const provenance = content.provenance as Record<string, unknown>
      expect(String(provenance.paradigm_note)).toContain(`paradigm:"${paradigm}"`)
      const filters = content.filters as Record<string, unknown>
      expect(filters.paradigm).toBe(paradigm)
    })
  }

  it('rejects a paradigm outside design §27.4\'s 4-paradigm vocabulary (e.g. "esoteric") as is_error, not silently', async () => {
    vi.mocked(mockQuery).mockClear()
    const result = await querySignalsCapability.handler({ chart_id: CHART_A, paradigm: 'esoteric' }, {})
    expect(result.is_error).toBe(true)
    expect(String((result.content as Record<string, unknown>).error)).toMatch(/Unknown paradigm/)
    // Never touched the DB for an invalid paradigm.
    expect(vi.mocked(mockQuery)).not.toHaveBeenCalled()
  })
})
