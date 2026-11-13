import { query } from '@/lib/db/client'

export interface TransitVedhaReferenceFilters {
  readonly primaryGraha: string | null
  readonly primaryHouse: number | null
}

/** Read the global reference surface; preserve the driver's result and promise. */
export function queryTransitVedhaReference({ primaryGraha, primaryHouse }: TransitVedhaReferenceFilters): ReturnType<typeof query<Record<string, unknown>>> {
  const filters: string[] = ['1=1']
  const params: unknown[] = []
  let p = 1
  if (primaryGraha) { filters.push(`LOWER(primary_graha) = LOWER($${p++})`); params.push(primaryGraha) }
  if (primaryHouse != null && Number.isInteger(primaryHouse)) { filters.push(`primary_transit_house = $${p++}`); params.push(primaryHouse) }
  const where = filters.join(' AND ')

  const sql = `
      SELECT primary_graha, primary_transit_house, vedha_graha, vedha_house, vedha_type,
             classical_note, classical_citation
      FROM bg_transit_vedha
      WHERE ${where}
      ORDER BY primary_graha, primary_transit_house`

  return query<Record<string, unknown>>(sql, params)
}

export interface TransitAvGatesReferenceFilters {
  readonly gateKind: string | null
  readonly graha: string | null
}

export function queryTransitAvGatesReference({ gateKind, graha }: TransitAvGatesReferenceFilters): ReturnType<typeof query<Record<string, unknown>>> {
  const filters: string[] = ['1=1']
  const params: unknown[] = []
  let p = 1
  if (gateKind) { filters.push(`gate_kind = $${p++}`); params.push(gateKind) }
  if (graha)    { filters.push(`LOWER(graha) = LOWER($${p++})`); params.push(graha) }
  const where = filters.join(' AND ')

  const sql = `
      SELECT gate_kind, graha, house_from_moon, kakshya_lord, min_av_score, min_sav_score,
             effect, classical_citation, rule_notes
      FROM bg_transit_av_gates
      WHERE ${where}
      ORDER BY gate_kind, graha, house_from_moon`

  return query<Record<string, unknown>>(sql, params)
}

export interface TransitEngineReferenceFilters {
  readonly graha: string | null
}

export function queryTransitEngineReference({ graha }: TransitEngineReferenceFilters): ReturnType<typeof query<Record<string, unknown>>> {
  const filters: string[] = ['1=1']
  const params: unknown[] = []
  let p = 1
  if (graha) { filters.push(`LOWER(graha) = LOWER($${p++})`); params.push(graha) }
  const where = filters.join(' AND ')

  const sql = `
      SELECT graha, avg_daily_motion_deg, zodiac_period_days, sign_residence_days, classical_citation
      FROM bg_transit_engine
      WHERE ${where}
      ORDER BY graha`

  return query<Record<string, unknown>>(sql, params)
}

export interface TransitMoortiReferenceFilters {
  readonly nakshatraOffset: number | null
  readonly moortiName: string | null
}

export function queryTransitMoortiReference({ nakshatraOffset, moortiName }: TransitMoortiReferenceFilters): ReturnType<typeof query<Record<string, unknown>>> {
  const filters: string[] = ['1=1']
  const params: unknown[] = []
  let p = 1
  if (nakshatraOffset != null && Number.isInteger(nakshatraOffset)) { filters.push(`nakshatra_offset = $${p++}`); params.push(nakshatraOffset) }
  if (moortiName) { filters.push(`LOWER(moorti_name) = LOWER($${p++})`); params.push(moortiName) }
  const where = filters.join(' AND ')

  const sql = `
      SELECT nakshatra_offset, moorti_name, quality_tier, phala_brief, classical_citation, rule_notes
      FROM bg_transit_moorti
      WHERE ${where}
      ORDER BY nakshatra_offset`

  return query<Record<string, unknown>>(sql, params)
}
