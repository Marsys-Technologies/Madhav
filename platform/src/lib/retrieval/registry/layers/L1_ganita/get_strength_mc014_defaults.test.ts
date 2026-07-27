/**
 * get_strength_mc014_defaults.test.ts — ŚODHANA T3 (MC-014 defaults sweep).
 *
 * `graha_in_house_composite_strength` carries one row per graha PER HOUSE (12x a graha's
 * real placement) — every counterfactual "what if this graha sat in house N" row, served by
 * default alongside the 20 other one-row-per-graha strength categories. This drove the
 * "~520 rows for one chart's full strength pull" complaint (MC-014). Default (`all` omitted
 * or false) now filters `graha_in_house_composite_strength` down to each graha's single
 * ACTUAL house (computed the same way the pre-existing `frame_context` display already
 * did, just applied for filtering under EVERY frame, including the tool's own default
 * `frame:'lagna'`); `all:true` restores every counterfactual row (never removed — B.10, just
 * no longer the default).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

async function getCapabilityHandler() {
  await import('../../catalog')
  const { getCapability } = await import('../../index')
  const cap = getCapability('marsys://tool/L1/get_strength')
  if (!cap) throw new Error('get_strength capability not registered')
  return cap.handler as (args: Record<string, unknown>, ctx?: unknown) => Promise<{ content: Record<string, unknown>; is_error?: boolean }>
}

/** 3 grahas x 12 houses of graha_in_house_composite_strength rows, plus each graha's real
 *  natal sign row (graha_position/sign) so the active-house resolver can compute the real
 *  placement. Sun (SU) sits in Capricorn (10th from Aries lagna); Moon (MO) in Pisces (12th);
 *  Jupiter (JU) in Cancer (4th). Reference sign for frame:'lagna' is Aries (house 1). */
function makeRows() {
  const grahaCompositeRows = (): Record<string, unknown>[] => {
    const rows: Record<string, unknown>[] = []
    for (const graha of ['SU', 'MO', 'JU']) {
      for (let house = 1; house <= 12; house++) {
        rows.push({
          fact_id: `strength_${graha}_h${house}`, fact_category: 'graha_in_house_composite_strength',
          fact_subject: `${graha}_IN_HOUSE_${house}`, ayanamsha_id: 'lahiri_chitrapaksha',
          fact_key: 'score', fact_value_num: 0.5, fact_value_text: null, fact_value_jsonb: null,
          unit: null, verification_pass_status: 'pass', citation_ref: 'c',
        })
      }
    }
    return rows
  }
  const oneRowPerGrahaCategory: Record<string, unknown>[] = ['SU', 'MO', 'JU'].map(graha => ({
    fact_id: `shadbala_${graha}`, fact_category: 'graha_shadbala_total', fact_subject: graha,
    ayanamsha_id: 'lahiri_chitrapaksha', fact_key: 'total', fact_value_num: 400, fact_value_text: null,
    fact_value_jsonb: null, unit: null, verification_pass_status: 'pass', citation_ref: 'c',
  }))
  return [...grahaCompositeRows(), ...oneRowPerGrahaCategory]
}

const SIGN_ROWS = [
  { fact_subject: 'SU', fact_value_text: 'Capricorn' },
  { fact_subject: 'MO', fact_value_text: 'Pisces' },
  { fact_subject: 'JU', fact_value_text: 'Cancer' },
  { fact_subject: 'LAGNA', fact_value_text: 'Aries' },
]

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockImplementation(async (sql: string, params: unknown[]) => {
    // address_resolver.ts's resolveFrameSign — single-subject lookup (frame:'lagna' -> LAGNA).
    if (/fact_category = \$3\s+AND fact_subject = \$4/.test(sql)) {
      const subject = params[3]
      const row = SIGN_ROWS.find(r => r.fact_subject === subject)
      return { rows: row ? [{ fact_id: `sign_${subject}`, fact_value_text: row.fact_value_text }] : [] }
    }
    // get_strength.ts's own multi-graha signRes lookup (fact_subject = ANY([...])).
    if (/fact_category = 'graha_position'/.test(sql)) return { rows: SIGN_ROWS }
    if (/FROM chart_facts/.test(sql)) return { rows: makeRows() }
    return { rows: [] }
  })
})

describe('get_strength — MC-014 actual-placement-only default', () => {
  it('default (all omitted): graha_in_house_composite_strength keeps only each graha\'s real house, not all 12', async () => {
    const handler = await getCapabilityHandler()
    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha' })

    expect(res.is_error).toBeFalsy()
    const rows = res.content['rows'] as Record<string, unknown>[]
    const compositeRows = rows.filter(r => r['fact_category'] === 'graha_in_house_composite_strength')
    // 3 grahas x 1 real house each = 3, not 3 x 12 = 36.
    expect(compositeRows).toHaveLength(3)
    expect(new Set(compositeRows.map(r => r['fact_subject']))).toEqual(
      new Set(['SU_IN_HOUSE_10', 'MO_IN_HOUSE_12', 'JU_IN_HOUSE_4']),
    )
    // The other 20 one-row-per-graha categories are completely unaffected.
    expect(rows.some(r => r['fact_category'] === 'graha_shadbala_total')).toBe(true)
    expect(res.content['all']).toBe(false)
    expect(res.content['counterfactual_rows_dropped']).toBe(33) // 3 grahas x 11 dropped houses
  })

  it('all:true restores every counterfactual placement row (never deleted, just not the default — B.10)', async () => {
    const handler = await getCapabilityHandler()
    const res = await handler({ chart_id: CHART_ID, ayanamsha_id: 'lahiri_chitrapaksha', all: true })

    const rows = res.content['rows'] as Record<string, unknown>[]
    const compositeRows = rows.filter(r => r['fact_category'] === 'graha_in_house_composite_strength')
    expect(compositeRows).toHaveLength(36) // 3 grahas x 12 houses, nothing dropped
    expect(res.content['all']).toBe(true)
  })
})
