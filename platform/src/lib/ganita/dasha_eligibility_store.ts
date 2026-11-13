import { query } from '@/lib/db/client'

export interface DashaEligibilityRow extends Record<string, unknown> {
  dasha_row_id: string
  system_id: string
  level_n: number
  lord_graha: string
  lord_sign: string | null
  parent_row_id: string | null
  start_date: string
  end_date: string
  start_iso: string | null
  end_iso: string | null
  kp_sublevel: string | null
  kp_sub_lord: string | null
}

export interface DashaEligibilityQuery {
  chart_id: string
  ayanamsha_id: string
  date_from: string
  date_to: string
  target_lords: readonly string[]
}

/** Read bounded inclusive dasha windows using the shared date/timestamp parsers. */
export async function readDashaEligibilityWindows({
  chart_id,
  ayanamsha_id,
  date_from,
  date_to,
  target_lords,
}: DashaEligibilityQuery): Promise<DashaEligibilityRow[]> {
  const params: unknown[] = [chart_id, ayanamsha_id, date_from, date_to]

  // chart_dashas is a flat one-row-per-level model: each row carries a single
  // lord_graha at level_n (not separate MD/AD/PD/SP lord columns). The optional
  // target-lord filter therefore matches lord_graha at any level.
  let lordFilter = ''
  if (target_lords.length > 0) {
    const ph = target_lords.map((_, i) => `$${5 + i}`).join(', ')
    lordFilter = `AND lord_graha IN (${ph})`
    target_lords.forEach(l => params.push(l))
  }

  const result = await query<DashaEligibilityRow>(
    // WP-1.5 F-DATE-TZ: start_date/end_date are DATE columns → to_char to 'YYYY-MM-DD'
    // (raw return → node-postgres IST-midnight → UTC off-by-one). start_iso/end_iso are
    // timestamptz instants and are correctly returned as ISO datetimes.
    `SELECT
           dasha_row_id, system_id, level_n,
           lord_graha, lord_sign, parent_row_id,
           to_char(start_date, 'YYYY-MM-DD') AS start_date,
           to_char(end_date, 'YYYY-MM-DD')   AS end_date,
           start_iso, end_iso,
           kp_sublevel, kp_sub_lord
         FROM chart_dashas
         WHERE chart_id = $1 AND ayanamsha_id = $2
           AND end_date >= $3 AND start_date <= $4
           ${lordFilter}
         ORDER BY start_date, system_id, level_n
         LIMIT 400`,
    params,
  )
  return result.rows
}
