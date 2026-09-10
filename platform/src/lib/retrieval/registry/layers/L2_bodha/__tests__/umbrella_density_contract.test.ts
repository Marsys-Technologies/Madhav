/**
 * The L2 umbrella capabilities' density contracts must be EARNED, not declared.
 *
 * NIRMĀṆA L2-W3 (N-17). §N.6 asks every capability to declare its density and
 * empty-reason discipline; §N.8 says a flag with no detector behind it is null, not
 * green. Those two together are the whole point of this file.
 *
 * The hazard is specific and already live at estate scale: `deriveDensityContract()`
 * auto-stamps `empty_reason: true` from a capability's ARCHETYPE alone, so every
 * capability "has" a density contract at runtime whether or not its handler ever sets
 * `content.empty_reason`. A census that only checks for the field's presence therefore
 * passes on capabilities that never produce one. This test checks the claim instead of
 * the field: if a descriptor says `empty_reason: true`, the handler must actually
 * return one on an empty result.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/lib/db/client', () => ({ query: vi.fn() }))
import { query as mockQuery } from '@/lib/db/client'

import { queryChartGestaltCapability } from '../query_chart_gestalt'
import { queryCdlmSummaryCapability } from '../query_cdlm_summary'
import { queryDiscoveriesCapability } from '../query_discoveries'
import { queryQuestionLensesCapability } from '../query_question_lenses'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

const UMBRELLAS = [
  ['query_chart_gestalt', queryChartGestaltCapability],
  ['query_cdlm_summary', queryCdlmSummaryCapability],
  ['query_discoveries', queryDiscoveriesCapability],
  ['query_question_lenses', queryQuestionLensesCapability],
] as const

describe('L2 umbrella density contracts are hand-authored and honest', () => {
  beforeEach(() => {
    ;(mockQuery as unknown as ReturnType<typeof vi.fn>).mockReset()
    // Distinguish the query KINDS: a data query returning `rows: []` is the empty
    // case; a COUNT query must still return one row carrying zero, and the tail's
    // null-percentile probe must return one row carrying zero. A single blanket mock
    // makes every query look non-empty and the empty path is never exercised.
    ;(mockQuery as unknown as ReturnType<typeof vi.fn>).mockImplementation((sql: string) => {
      const q = String(sql)
      if (q.includes('salience_pctl_in_class IS NULL')) return Promise.resolve({ rows: [{ n: 0 }] })
      if (q.includes('class_n') || q.includes('bodha_anomalies')) return Promise.resolve({ rows: [] })
      if (/count\(/i.test(q)) return Promise.resolve({ rows: [{ total: 0, n: 0 }] })
      return Promise.resolve({ rows: [] })
    })
  })

  for (const [name, cap] of UMBRELLAS) {
    it(`${name} declares a density_contract in source`, () => {
      expect(cap.density_contract).toBeDefined()
      expect(Array.isArray(cap.density_contract?.facets)).toBe(true)
      expect(cap.density_contract?.facets.length).toBeGreaterThan(0)
      expect(typeof cap.density_contract?.paginated).toBe('boolean')
    })

    it(`${name} EARNS its empty_reason claim — the handler really sets one`, async () => {
      expect(cap.density_contract?.empty_reason).toBe(true)
      const res = await cap.handler({ chart_id: CHART }, undefined)
      const content = res.content as Record<string, unknown>
      expect(res.is_error).toBe(false)
      // present, non-null, and actually explanatory rather than a placeholder
      expect(content['empty_reason']).toBeTruthy()
      expect(String(content['empty_reason']).length).toBeGreaterThan(40)
      expect(String(content['empty_reason'])).toContain(CHART)
    })

    it(`${name} returns empty_reason: null when it has rows`, async () => {
      ;(mockQuery as unknown as ReturnType<typeof vi.fn>).mockImplementation((sql: string) => {
        const q = String(sql)
        if (q.includes('salience_pctl_in_class IS NULL')) return Promise.resolve({ rows: [{ n: 0 }] })
        if (q.includes('class_n') || q.includes('bodha_anomalies')) return Promise.resolve({ rows: [] })
        if (/count\(/i.test(q)) return Promise.resolve({ rows: [{ total: 1, n: 0 }] })
        return Promise.resolve({ rows: [{ chart_id: CHART }] })
      })
      const res = await cap.handler({ chart_id: CHART }, undefined)
      const content = res.content as Record<string, unknown>
      expect(content['empty_reason']).toBeNull()
    })

    it(`${name} carries the constitutional tail section (D-SALIENCE)`, async () => {
      const res = await cap.handler({ chart_id: CHART }, undefined)
      const content = res.content as Record<string, unknown>
      expect(content).toHaveProperty('tail_watch')
      expect(Array.isArray(content['tail_watch'])).toBe(true)
      // an empty tail must explain itself rather than being a silent []
      expect(content['tail_watch_empty_reason']).toBeTruthy()
      expect(content).toHaveProperty('tail_watch_components')
    })
  }

  it('paginated:true is only claimed where offset is genuinely supported', () => {
    // `limit` alone is a cap, not pagination. Claiming pagination without an offset
    // tells a caller a second page exists that they have no way to request.
    expect(queryDiscoveriesCapability.density_contract?.paginated).toBe(true)
    expect(queryQuestionLensesCapability.density_contract?.paginated).toBe(true)
    expect(queryChartGestaltCapability.density_contract?.paginated).toBe(false)
    expect(queryCdlmSummaryCapability.density_contract?.paginated).toBe(false)
  })
})
