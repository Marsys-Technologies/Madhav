/**
 * Fixtures for the identity_cross_check tests (SS N-360): a router over the five-ayanamsha chart_facts /
 * chart_dashas / chart_divisionals reads that chart_snapshot and graha_portrait make. No database.
 * The `query` mock itself is created (and `vi.mock`ed) by each test file.
 */
import { AYANAMSHA_SERVE_ORDER } from '../../constants'

export const CHART = '482012f1-710e-4a25-994a-93821f5871aa'
export const LAHIRI = 'lahiri_chitrapaksha'
export const KEY = 'identity_cross_check'
export const POSITION_BUILD = '11111111-1111-4111-8111-111111111111'
export const DASHA_BUILD = '22222222-2222-4222-8222-222222222222'
export const OTHERS_IN_ORDER = ['true_chitra', 'krishnamurti', 'raman', 'surya_siddhanta_classical']
// fixture rows are emitted in ALPHABETICAL order on purpose: the builder must re-order to serve order
export const ALPHA: string[] = [...AYANAMSHA_SERVE_ORDER].sort()

/** ayanamsha -> "SUBJECT.key" (or "maha_lord") -> value */
export type Override = Record<string, Record<string, string>>

export interface IdentityDbOptions {
  stored?: readonly string[]
  override?: Override
}

const BASE: Record<string, string> = {
  'LAGNA.sign': 'Aries',
  'MOON.sign': 'Aquarius', 'MOON.nakshatra': 'Purva Bhadrapada',
  'SAT.sign': 'Libra', 'SAT.nakshatra': 'Vishakha',
  maha_lord: 'Venus',
}

export type DbCall = { sql: string; params: unknown[] }

/** Install the router on `queryMock` and return the recorded calls. */
export function installIdentityDb(
  queryMock: { mockImplementation: (fn: (sql: string, params?: unknown[]) => Promise<{ rows: unknown[] }>) => unknown },
  opts: IdentityDbOptions = {},
): DbCall[] {
  const stored = opts.stored ?? AYANAMSHA_SERVE_ORDER
  const value = (aya: string, k: string): string | undefined => opts.override?.[aya]?.[k] ?? BASE[k]
  const lon = (aya: string, subject: string): number => 10 + ALPHA.indexOf(aya) + (subject === 'MOON' ? 0.5 : 0)
  const factRows = (subjects: readonly string[]) => [...stored].sort().flatMap((aya) => subjects.flatMap((subject) => [
    { ayanamsha_id: aya, fact_subject: subject, fact_key: 'sign', fact_value_text: value(aya, `${subject}.sign`) ?? null, fact_value_num: null },
    ...(subject === 'LAGNA' ? [] : [{ ayanamsha_id: aya, fact_subject: subject, fact_key: 'nakshatra', fact_value_text: value(aya, `${subject}.nakshatra`) ?? null, fact_value_num: null }]),
    { ayanamsha_id: aya, fact_subject: subject, fact_key: 'longitude_sidereal', fact_value_text: null, fact_value_num: String(lon(aya, subject)) },
  ]))
  const calls: DbCall[] = []
  queryMock.mockImplementation(async (sql: string, params: unknown[] = []) => {
    calls.push({ sql, params })
    if (typeof sql !== 'string') return { rows: [] }
    if (sql.includes('FROM chart_divisionals')) {
      return { rows: [
        { varga: 'D1', graha: 'Lagna', sign: 'Aries', degree_in_sign: '12.431', id: 'd-lagna' },
        { varga: 'D1', graha: 'Moon', sign: 'Aquarius', degree_in_sign: '29.772', id: 'd-moon' },
        { varga: 'D1', graha: 'Saturn', sign: 'Libra', degree_in_sign: '4.5', id: 'd-sat' },
        { varga: 'D1', graha: 'Sun', sign: 'Capricorn', degree_in_sign: '22.195', id: 'd-sun' },
      ] }
    }
    // chart_snapshot's identity read: Lagna + Moon
    if (sql.includes("fact_subject = 'LAGNA' AND fact_key IN")) return { rows: factRows(['LAGNA', 'MOON']) }
    // graha_portrait's per-graha read
    if (sql.includes('fact_subject = ANY($3::text[])')) return { rows: factRows(params[2] as string[]) }
    if (sql.includes('FROM chart_dashas') && sql.includes('level_n = 1 AND start_date <= $3::date')) {
      return { rows: [...stored].sort().map((aya) => ({ ayanamsha_id: aya, lord_graha: value(aya, 'maha_lord') ?? 'Venus' })) }
    }
    return { rows: [] }
  })
  return calls
}

/** What `resolveChartServedGeneration` returns in these tests (a resolved generation with a ga_dashas build). */
export const SERVED_GENERATION = {
  chart_id: CHART, source: 'per_asset_receipts', generation_hash: 'hash-test',
  assets: { ga_dashas: { asset_id: 'ga_dashas', state: 'resolved', rows_build_id: DASHA_BUILD, receipt_build_id: DASHA_BUILD } },
  served_build_ids: [POSITION_BUILD], withheld_builds: [],
}
