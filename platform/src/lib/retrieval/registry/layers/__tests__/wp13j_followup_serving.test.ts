/**
 * wp13j_followup_serving.test.ts — WP-1.3j (W1-FOLLOWUP serving lane)
 * ===================================================================
 * Proves the follow-up serving surfaces closing the populated-but-unserved BODHA
 * assets + the two phala serving-bug fixes:
 *   (1) 5 new L2 Bodha capabilities (discoveries, pratijna, question_lenses,
 *       rm_prescriptions, rm_resonances) — per_chart, chart-scoped SQL, bounded
 *       (LIMIT ≤50), disclosed total, offset pagination;
 *   (2) query_remedy_program (ph_pratikara / phala_mitigation) — now bounded + total
 *       disclosed (was unbounded), returns the real `remedies` key;
 *   (3) query_rectification (ph_rectification) — ayanamsha is now an OPTIONAL filter;
 *       the prior forced default 'lahiri_chitrapaksha' matched ZERO of 185 real rows.
 *
 * DB is mocked — ground-truth counts verified separately via bounded prod queries on
 * both charts (482012f1… and 1c826d5a…) are asserted through the mocked COUNT total.
 */
import { describe, it, expect, vi } from 'vitest'

const CHART_A = '482012f1-710e-4a25-994a-93821f5871aa'

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string) => {
    if (String(sql).includes('COUNT(*)')) return { rows: [{ total: '42' }] }
    return { rows: [{ probe: 1 }] }
  }),
}))

import { query as mockQuery } from '@/lib/db/client'

import { queryDiscoveriesCapability }     from '../L2_bodha/query_discoveries'
import { queryPratijnaCapability }        from '../L2_bodha/query_pratijna'
import { queryQuestionLensesCapability }  from '../L2_bodha/query_question_lenses'
import { queryRmPrescriptionsCapability } from '../L2_bodha/query_rm_prescriptions'
import { queryRmResonancesCapability }    from '../L2_bodha/query_rm_resonances'
import { queryRemedyProgramCapability, queryRectificationCapability } from '../L4_phala/query_phala_calibration'

type Cap = {
  name: string
  scope: string
  required_inputs?: string[]
  handler: (args: Record<string, unknown>, ctx: unknown) => Promise<{ content: unknown; is_error?: boolean }>
}

const NEW_BODHA: Array<{ cap: Cap; table: string }> = [
  { cap: queryDiscoveriesCapability as unknown as Cap,     table: 'bodha_discoveries' },
  { cap: queryPratijnaCapability as unknown as Cap,        table: 'bodha_pratijna' },
  { cap: queryQuestionLensesCapability as unknown as Cap,  table: 'bodha_question_lenses' },
  { cap: queryRmPrescriptionsCapability as unknown as Cap, table: 'bodha_rm_remedy_prescriptions' },
  { cap: queryRmResonancesCapability as unknown as Cap,    table: 'bodha_rm_resonances' },
]

describe('WP-1.3j — new BODHA serving surfaces (populated-but-unserved)', () => {
  it.each(NEW_BODHA)('$cap.name is per_chart and requires chart_id', ({ cap }) => {
    expect(cap.scope).toBe('per_chart')
    expect(cap.required_inputs).toContain('chart_id')
  })

  it.each(NEW_BODHA)('$cap.name errors without chart_id and does not touch the DB', async ({ cap }) => {
    vi.mocked(mockQuery).mockClear()
    const r = await cap.handler({}, {})
    expect(r.is_error).toBe(true)
    expect(vi.mocked(mockQuery)).not.toHaveBeenCalled()
  })

  it.each(NEW_BODHA)('$cap.name queries $table scoped by chart_id and discloses a total', async ({ cap, table }) => {
    vi.mocked(mockQuery).mockClear()
    const r = await cap.handler({ chart_id: CHART_A }, {})
    expect(r.is_error).toBe(false)
    const calls = vi.mocked(mockQuery).mock.calls
    const main = calls.find(c => String(c[0]).includes(`FROM ${table}`) && !String(c[0]).includes('COUNT(*)'))!
    expect(main, `a SELECT against ${table}`).toBeDefined()
    expect(String(main[0])).toContain('chart_id = $1')
    expect((main[1] as unknown[])[0]).toBe(CHART_A)
    const content = r.content as Record<string, unknown>
    expect(content).toHaveProperty('total_matching', 42)
    expect(content).toHaveProperty('more_available')
    expect(content).toHaveProperty('rows')
  })

  it.each(NEW_BODHA)('$cap.name caps LIMIT at 50 and honors offset (bounded pagination)', async ({ cap }) => {
    vi.mocked(mockQuery).mockClear()
    await cap.handler({ chart_id: CHART_A, limit: 100000, offset: 20 }, {})
    const main = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('LIMIT $') && String(c[0]).includes('OFFSET $'))!
    const params = main[1] as unknown[]
    const offsetParam = Number(params.at(-1))
    const limitParam = Number(params.at(-2))
    expect(limitParam).toBeLessThanOrEqual(50)
    expect(offsetParam).toBe(20)
  })

  it('query_discoveries narrows SQL when discovery_class + ayanamsha_id supplied', async () => {
    vi.mocked(mockQuery).mockClear()
    await queryDiscoveriesCapability.handler({ chart_id: CHART_A, ayanamsha_id: 'lahiri_chitrapaksha', discovery_class: 'yoga' }, {})
    const main = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('FROM bodha_discoveries') && !String(c[0]).includes('COUNT'))!
    expect(String(main[0])).toContain('ayanamsha_id = $')
    expect(String(main[0])).toContain('discovery_class = $')
    expect(main[1] as unknown[]).toContain('yoga')
  })

  it('query_question_lenses does NOT inline the raw ranked-signal array (token safety)', async () => {
    vi.mocked(mockQuery).mockClear()
    await queryQuestionLensesCapability.handler({ chart_id: CHART_A }, {})
    const main = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('FROM bodha_question_lenses') && !String(c[0]).includes('COUNT'))!
    const sql = String(main[0])
    // Discloses a count, never SELECTs the full ranked_signals array as a column.
    expect(sql).toContain('ranked_signal_count')
    expect(sql).not.toMatch(/SELECT[^]*all_relevant_ranked_jsonb\s*,/)
  })
})

describe('WP-1.3j — ph_pratikara mitigation serving-bug fix (F-L10-024)', () => {
  const cap = queryRemedyProgramCapability as unknown as Cap

  it('is per_chart and requires chart_id', () => {
    expect(cap.scope).toBe('per_chart')
    expect(cap.required_inputs).toContain('chart_id')
  })

  it('returns the real `remedies` key, discloses total, and is now bounded (LIMIT ≤50)', async () => {
    vi.mocked(mockQuery).mockClear()
    const r = await cap.handler({ chart_id: CHART_A, limit: 99999 }, {})
    expect(r.is_error).toBe(false)
    const content = r.content as Record<string, unknown>
    expect(content).toHaveProperty('remedies')
    expect(content).toHaveProperty('total_matching', 42)
    expect(content).toHaveProperty('more_available')
    const main = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('FROM phala_mitigation') && String(c[0]).includes('LIMIT $'))!
    const limitParam = Number((main[1] as unknown[]).at(-2))
    expect(limitParam).toBeLessThanOrEqual(50)
    expect(String(main[0])).toContain('chart_id = $1')
  })

  it('narrows both the page and total through the linked anchor domain', async () => {
    vi.mocked(mockQuery).mockClear()
    await cap.handler({ chart_id: CHART_A, domain: 'career', limit: 8 }, {})
    const calls = vi.mocked(mockQuery).mock.calls
    const main = calls.find(c => String(c[0]).includes('FROM phala_mitigation') && String(c[0]).includes('LIMIT $'))!
    const count = calls.find(c => String(c[0]).includes('COUNT(*)') && String(c[0]).includes('FROM phala_mitigation'))!

    for (const call of [main, count]) {
      expect(String(call[0])).toContain('EXISTS (')
      expect(String(call[0])).toContain('FROM phala_anchors')
      expect(String(call[0])).toContain('a.domain = $')
      expect(call[1] as unknown[]).toContain('career')
    }
  })
})

describe('WP-1.3j — ph_rectification serving-bug fix (F-L10-025)', () => {
  const cap = queryRectificationCapability as unknown as Cap

  it('omitting ayanamsha_id returns ALL ayanamshas — no forced lahiri_chitrapaksha filter', async () => {
    vi.mocked(mockQuery).mockClear()
    const r = await cap.handler({ chart_id: CHART_A }, {})
    expect(r.is_error).toBe(false)
    const main = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('FROM phala_rectification') && String(c[0]).includes('LIMIT $'))!
    // No ayanamsha_id predicate when omitted; the prior bug hard-coded a default.
    expect(String(main[0])).not.toContain('ayanamsha_id = $')
    const params = main[1] as unknown[]
    expect(params).not.toContain('lahiri_chitrapaksha')
    const content = r.content as Record<string, unknown>
    expect(content).toHaveProperty('total_matching', 42)
  })

  it('maps the L1 long form lahiri_chitrapaksha → short code lahiri (which the table stores)', async () => {
    vi.mocked(mockQuery).mockClear()
    await cap.handler({ chart_id: CHART_A, ayanamsha_id: 'lahiri_chitrapaksha' }, {})
    const main = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('FROM phala_rectification') && String(c[0]).includes('LIMIT $'))!
    expect(String(main[0])).toContain('ayanamsha_id = $')
    const params = main[1] as unknown[]
    expect(params).toContain('lahiri')
    expect(params).not.toContain('lahiri_chitrapaksha')
  })

  it('caps top_k at 50 (bounded)', async () => {
    vi.mocked(mockQuery).mockClear()
    await cap.handler({ chart_id: CHART_A, top_k: 9999 }, {})
    const main = vi.mocked(mockQuery).mock.calls.find(c => String(c[0]).includes('FROM phala_rectification') && String(c[0]).includes('LIMIT $'))!
    const limitParam = Number((main[1] as unknown[]).at(-2))
    expect(limitParam).toBeLessThanOrEqual(50)
  })
})
