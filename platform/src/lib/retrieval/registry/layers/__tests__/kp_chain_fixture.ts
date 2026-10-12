/**
 * Shared fixture for the KP-frame chain tests (SS N-356): KP cuspal fact rows for the cusps the
 * domain readings ask for, plus helpers that read the recorded `query` mock trace.
 */
export const KP_CATEGORIES = ['cusp_kp_lords', 'kp_cuspal_significators', 'bhava_cusps', 'kp_ruling_planets_natal']

/** Minimal chart_facts rows for the given cusps: a sub-lord chain + a significator list. */
export function kpRowsForHouses(houses: number[]) {
  return houses.flatMap(h => [
    { fact_id: `kp-star-${h}`, fact_category: 'cusp_kp_lords', ayanamsha_id: 'krishnamurti', fact_subject: `CUSP_${String(h).padStart(2, '0')}`, fact_key: 'star_lord', fact_value_text: 'Mercury', fact_value_num: null, fact_value_jsonb: null },
    { fact_id: `kp-sub-${h}`, fact_category: 'cusp_kp_lords', ayanamsha_id: 'krishnamurti', fact_subject: `CUSP_${String(h).padStart(2, '0')}`, fact_key: 'sub_lord', fact_value_text: 'Venus', fact_value_num: null, fact_value_jsonb: null },
    { fact_id: `kp-sig-${h}`, fact_category: 'kp_cuspal_significators', ayanamsha_id: 'krishnamurti', fact_subject: `CUSP_${h}`, fact_key: 'significators_json', fact_value_text: null, fact_value_num: null, fact_value_jsonb: [2, 6, 10, 11] },
  ])
}

export interface QueryCall { sql: string; params: unknown[] }

export function recordedCalls(mock: { mock: { calls: unknown[][] } }): QueryCall[] {
  return mock.mock.calls.map(c => ({ sql: String(c[0]), params: (c[1] as unknown[] | undefined) ?? [] }))
}

/** True when the call is the get_kp_cusps fact read (its params carry the four KP categories). */
export function isKpChainRead(call: QueryCall): boolean {
  return call.params.some(p => Array.isArray(p) && p.includes('cusp_kp_lords'))
}

/** The ayanamsha id param of a KP chain read: always $2 of the get_kp_cusps SQL. */
export function kpReadAyanamsha(call: QueryCall): unknown {
  return call.params[1]
}
