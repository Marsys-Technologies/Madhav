/**
 * get_nakshatra.pagination.test.ts — the served query has a TOTAL order.
 *
 * After a ga_nakshatra rebuild every (graha_gandanta, subject, is_gandanta) key carries two
 * rows (canonical + strict_0_48 variant). They differ only in `formula_id` (and `fact_id`),
 * so an ORDER BY ending at `fact_key` leaves ties that sort unstably across LIMIT/OFFSET
 * pages (duplicated/skipped rows). Pins: formula_id is selected (the variants are
 * distinguishable in the response) and the ORDER BY ends in formula_id NULLS FIRST, fact_id.
 * Mock-based, no database.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

describe('get_nakshatra pagination order', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('selects formula_id and orders by a total key ending in formula_id NULLS FIRST, fact_id', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })
    const { getNakshatraCapability } = await import('../get_nakshatra')
    const res = await getNakshatraCapability.handler(
      { chart_id: CHART_ID, categories: ['graha_gandanta'], limit: 10, offset: 10 },
      undefined,
    )
    expect(res.is_error).toBe(false)
    expect(mockQuery).toHaveBeenCalledTimes(1)
    const sql = String(mockQuery.mock.calls[0][0]).replace(/\s+/g, ' ')
    expect(sql).toMatch(/SELECT [^]*\bformula_id\b[^]* FROM chart_facts/)
    // PR-2: the Lahiri primary filter is $5 (after LIMIT/OFFSET $3/$4); the ayanamsha sort key is
    // the AYANAMSHA_SERVE_ORDER expression (Lahiri first), not alphabetical.
    expect(sql).toMatch(
      /ORDER BY fact_category, array_position\(ARRAY\[[^\]]*\]::text\[\], ayanamsha_id::text\), ayanamsha_id, fact_subject, fact_key, formula_id NULLS FIRST, fact_id LIMIT \$3 OFFSET \$4/,
    )
    expect(sql).toContain("ayanamsha_id IN ($5, 'INVARIANT')")
  })

  it('serves canonical and strict variant rows with distinct formula_id values', async () => {
    const mk = (id: string, formula: string | null) => ({
      fact_id: id, fact_category: 'graha_gandanta', fact_subject: 'MAR', ayanamsha_id: 'lahiri_chitrapaksha',
      fact_key: 'is_gandanta', formula_id: formula, fact_value_num: null, fact_value_text: 'true',
      fact_value_jsonb: null, unit: null, verification_pass_status: 'single', citation_ref: 'c',
    })
    mockQuery.mockResolvedValueOnce({ rows: [mk('f1', null), mk('f2', 'strict_0_48')] })
    const { getNakshatraCapability } = await import('../get_nakshatra')
    const res = await getNakshatraCapability.handler({ chart_id: CHART_ID, categories: ['graha_gandanta'] }, undefined)
    const rows = (res.content as { rows: Array<Record<string, unknown>> }).rows
    expect(rows).toHaveLength(2)
    expect(new Set(rows.map(r => r['formula_id'])).size).toBe(2)
    // the query contract that makes the rows distinguishable: formula_id is in the select list
    const sql = String(mockQuery.mock.calls[0][0])
    expect(sql.split('FROM chart_facts')[0]).toContain('formula_id')
  })
})
