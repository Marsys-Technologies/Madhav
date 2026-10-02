/**
 * chart_facts_query_ayurdaya_unreduced_base.test.ts — SS N-62 Q10 (display-side).
 *
 * chart_facts_query can serve fact_category='ayurdaya' rows (total_years etc.) generically.
 * When it does, the response must carry the same unreduced-base disclosure as get_ayurdaya;
 * every non-ayurdaya response must be unchanged; stored values must not move.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const AYANAMSHA = 'lahiri_chitrapaksha'
const CAVEAT = 'Unreduced base figure from the classical pinda/amsa/nisarga computation; no reductions (harana) are applied; not a prediction of lifespan.'

beforeEach(() => { mockQuery.mockReset() })

async function getHandler() {
  await import('../catalog')
  const { getCapability } = await import('../index')
  const cap = getCapability('marsys://tool/L1/chart_facts_query')
  if (!cap) throw new Error('chart_facts_query capability not registered')
  return cap.handler as (args: Record<string, unknown>, ctx?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>
}

function serveRows(rows: Array<Record<string, unknown>>) {
  mockQuery.mockImplementation(async (sql: string) => {
    if (/COUNT\(/i.test(sql)) return { rows: [{ total: rows.length }] }
    return { rows }
  })
}

const ayuRow = (): Record<string, unknown> => ({
  fact_id: 'a1', fact_category: 'ayurdaya', fact_subject: 'PINDAYU', fact_key: 'total_years',
  fact_value_num: 98.7521, fact_value_text: 'purnayu',
  fact_value_jsonb: { method: 'pindayu', harana_status: 'base_only_haranas_deferred_to_w3' },
})

describe('chart_facts_query — ayurdaya unreduced-base disclosure (SS N-62 Q10)', () => {
  for (const shape of ['pivoted', 'rows'] as const) {
    it(`[${shape}] adds ayurdaya_figure_disclosure + judgment flag and leaves the number unchanged`, async () => {
      const handler = await getHandler()
      serveRows([ayuRow()])
      const res = await handler({ chart_id: CHART, ayanamsha_id: AYANAMSHA, category: 'ayurdaya', shape })
      expect(res.is_error).toBeFalsy()
      expect(res.content['ayurdaya_figure_disclosure']).toMatchObject({
        figure_kind: 'unreduced_base', reductions_applied: false, caveat: CAVEAT,
      })
      const flags = res.content['judgment_flags'] as Array<Record<string, unknown>>
      expect(flags.map(f => f['code'])).toContain('ayurdaya_unreduced_base_figures')
      // the stored number is served verbatim in both shapes
      expect(JSON.stringify(res.content)).toContain('98.7521')
    })
  }

  it('does not touch a response with no ayurdaya figure (no disclosure keys; total_years under another category ignored)', async () => {
    const handler = await getHandler()
    serveRows([
      { fact_id: 'p1', fact_category: 'graha_position', fact_subject: 'SUN', fact_key: 'sign', fact_value_num: null, fact_value_text: 'Capricorn', fact_value_jsonb: null },
      { fact_id: 'd1', fact_category: 'dasha_total', fact_subject: 'VIMSHOTTARI', fact_key: 'total_years', fact_value_num: 120, fact_value_text: null, fact_value_jsonb: null },
    ])
    const res = await handler({ chart_id: CHART, ayanamsha_id: AYANAMSHA, shape: 'rows' })
    expect(res.content['ayurdaya_figure_disclosure']).toBeUndefined()
    expect(JSON.stringify(res.content['judgment_flags'] ?? [])).not.toContain('ayurdaya_unreduced_base_figures')
  })

  it('reports reduction_status_unverified (null) when the served total cannot confirm base-only status', async () => {
    const handler = await getHandler()
    serveRows([{ ...ayuRow(), fact_value_jsonb: { method: 'pindayu', harana_status: 'something_else' } }])
    const res = await handler({ chart_id: CHART, ayanamsha_id: AYANAMSHA, category: 'ayurdaya', shape: 'rows' })
    expect(res.content['ayurdaya_figure_disclosure']).toMatchObject({ figure_kind: 'reduction_status_unverified', reductions_applied: null })
  })
})
