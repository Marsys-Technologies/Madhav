/**
 * significator_condition.live_rows.test.ts — F-113 end-to-end assembly over REAL rows
 * ===================================================================================
 * The sibling `significator_condition.f113.test.ts` pins the pure selection contract and the
 * verdict clause. This file pins the ASSEMBLY: `buildSignificatorCondition` run end-to-end
 * with `@/lib/db/client` and `address_resolver` stubbed to return the ACTUAL production rows
 * for the canonical chart (482012f1-710e-4a25-994a-93821f5871aa, lahiri_chitrapaksha),
 * captured by direct SQL against production on 2026-08-21:
 *
 *   graha_shadbala_total.rupa (with PERCENT_RANK over the 9 rows — the identical window
 *   ganita_dasha_lord_capability_get uses):
 *     SUN 8.47 (1.000) · SAT 7.83 (0.875) · JUP 7.80 (0.750) · MER 7.55 (0.625)
 *     MOON 5.65 (0.500) · MAR 5.57 (0.375) · VEN 4.64 (0.250)
 *     KET_MEAN 0.625 (0.125) · RAH_MEAN 0.375 (0.000)
 *
 *   graha_dignity_per_varga (fact_key='dignity_state'):
 *     D1_SAT = 'exalted'  (fact_id 355fe607160e1d76)   ← the fact F-113 says was omitted
 *     D1_VEN = 'neutral'  (fact_id 6d91cccd12d138e7)
 *     D1_MAR = 'neutral'  (fact_id c8d49365ebe51631)
 *
 *   7th bhāva (lagna frame): Libra · lord Venus (9th, Sagittarius) · occupants Mars, Saturn
 *   (both in the 7th, Libra) — as served live by judgment_query(domain='marriage').
 *
 * If this test ever goes red because the selection contract stopped surfacing the exalted
 * 7th-house Saturn, F-113 has regressed.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => queryMock(...a) }))

const resolveAddressMock = vi.fn()
vi.mock('../../../address_resolver', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../../address_resolver')>()
  return { ...actual, resolveAddress: (...a: unknown[]) => resolveAddressMock(...a) }
})

import { buildSignificatorCondition, describeNotablePlacements } from '../significator_condition'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
const AYA = 'lahiri_chitrapaksha'

// Production rows, verbatim.
const SHADBALA_ROWS = [
  { fact_subject: 'SUN', rupa: 8.47, percentile: 1 },
  { fact_subject: 'SAT', rupa: 7.83, percentile: 0.875 },
  { fact_subject: 'JUP', rupa: 7.8, percentile: 0.75 },
  { fact_subject: 'MER', rupa: 7.55, percentile: 0.625 },
  { fact_subject: 'MOON', rupa: 5.65, percentile: 0.5 },
  { fact_subject: 'MAR', rupa: 5.57, percentile: 0.375 },
  { fact_subject: 'VEN', rupa: 4.64, percentile: 0.25 },
  { fact_subject: 'KET_MEAN', rupa: 0.625, percentile: 0.125 },
  { fact_subject: 'RAH_MEAN', rupa: 0.375, percentile: 0 },
]
const DIGNITY: Record<string, { fact_id: string; fact_value_text: string }> = {
  D1_SAT: { fact_id: '355fe607160e1d76', fact_value_text: 'exalted' },
  D1_VEN: { fact_id: '6d91cccd12d138e7', fact_value_text: 'neutral' },
  D1_MAR: { fact_id: 'c8d49365ebe51631', fact_value_text: 'neutral' },
}
const SHADBALA_FACT_ID: Record<string, { fact_id: string; fact_value_num: number }> = {
  SAT: { fact_id: '802b98a85d32bc93', fact_value_num: 7.83 },
  VEN: { fact_id: '5a80bdf4947d5e16', fact_value_num: 4.64 },
  MAR: { fact_id: '918ddc509a17a250', fact_value_num: 5.57 },
}
const GRAHA_PLACEMENT: Record<string, { graha: string; graha_code: string; house: number; sign: string }> = {
  Saturn: { graha: 'Saturn', graha_code: 'SAT', house: 7, sign: 'Libra' },
  Mars: { graha: 'Mars', graha_code: 'MAR', house: 7, sign: 'Libra' },
  Venus: { graha: 'Venus', graha_code: 'VEN', house: 9, sign: 'Sagittarius' },
}

beforeEach(() => {
  queryMock.mockReset()
  resolveAddressMock.mockReset()

  queryMock.mockImplementation(async (sql: string, params: unknown[]) => {
    if (sql.includes('PERCENT_RANK')) return { rows: SHADBALA_ROWS }
    if (sql.includes('graha_dignity_per_varga')) {
      const hit = DIGNITY[String(params[2])]
      return { rows: hit ? [hit] : [] }
    }
    if (sql.includes('graha_shadbala_total')) {
      const hit = SHADBALA_FACT_ID[String(params[2])]
      return { rows: hit ? [hit] : [] }
    }
    return { rows: [] }
  })

  resolveAddressMock.mockImplementation(async (_chart: string, expr: Record<string, unknown>) => {
    switch (expr['type']) {
      case 'bhava':
        return { entities: [{ kind: 'sign', sign: 'Libra', house_number: 7, frame: 'lagna', fact_ids: ['bhava-7'] }], chain: [] }
      case 'lord_of':
        return { entities: [{ kind: 'graha', ...GRAHA_PLACEMENT['Venus'], varga: 'D1', fact_ids: ['ven-pos'] }], chain: [] }
      case 'occupants_of':
        return { entities: [{ kind: 'occupants', house: 7, sign: 'Libra', varga: 'D1', frame: 'lagna', grahas: ['Mars', 'Saturn'], fact_ids: ['occ-7'] }], chain: [] }
      case 'graha': {
        const p = GRAHA_PLACEMENT[String(expr['graha'])]
        if (!p) throw new Error(`unmocked graha ${String(expr['graha'])}`)
        return { entities: [{ kind: 'graha', ...p, varga: 'D1', fact_ids: [`${p.graha_code}-pos`] }], chain: [] }
      }
      default:
        throw new Error(`unmocked address expr ${String(expr['type'])}`)
    }
  })
})

describe('F-113 · buildSignificatorCondition over real production rows', () => {
  it('grades the 7th bhāva occupants — the leg that did not exist before F-113', async () => {
    const sc = await buildSignificatorCondition(CHART, AYA, 'relationship')
    expect(sc.empty_reason).toBeUndefined()
    expect(sc.bhava).toBe(7)
    expect(sc.bhava_sign).toBe('Libra')
    expect(sc.occupants.map(o => o.graha).sort()).toEqual(['Mars', 'Saturn'])
    const saturn = sc.occupants.find(o => o.graha === 'Saturn')!
    expect(saturn.dignity_state).toBe('exalted')
    expect(saturn.dignity_weight).toBe(2)
    expect(saturn.shadbala_rupa).toBe(7.83)
    expect(saturn.shadbala_percentile).toBe(0.875)
    expect(saturn.fact_ids).toContain('355fe607160e1d76')
  })

  it('surfaces exactly the two facts F-113 names, and not the third occupant', async () => {
    const sc = await buildSignificatorCondition(CHART, AYA, 'relationship')
    expect(sc.notable.map(p => p.graha)).toEqual(['Saturn', 'Venus'])
    expect(sc.notable[1]!.shadbala_percentile).toBe(0.25) // the exact figure F-113 cites
  })

  it("produces a verdict sentence that says 'exalted' — the literal F-113 reproducer", async () => {
    const sc = await buildSignificatorCondition(CHART, AYA, 'relationship')
    const sentence = describeNotablePlacements(sc.notable, sc.bhava)!
    expect(sentence).toContain('exalted')
    expect(sentence).toContain('Saturn')
    expect(sentence).toContain('7th')
    expect(sentence).toContain('Libra')
    expect(sentence).toContain('7.83')
    expect(sentence).toContain('Venus')
  })

  it('reports an honest empty_reason for a domain with no shastra spec', async () => {
    const sc = await buildSignificatorCondition(CHART, AYA, 'not_a_domain')
    expect(sc.empty_reason).toContain('no SHASTRA_MAP entry')
    expect(sc.notable).toEqual([])
  })
})
