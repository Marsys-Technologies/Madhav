/**
 * chart_header.ts — D1 data-plane addition (design §10.1 frame safety / §12 D1)
 * =================================================================================
 * "chart_header materialization — trivial view over chart_facts; served by every
 * instrument." Read-only. Never writes. Never used for any positional CLAIM beyond
 * the ~40-token identity/frame-safety summary described in §10.1 — this is NOT a
 * general-purpose chart-facts reader.
 *
 * Fields: chart_id_short, name, lagna_sign, lagna_deg, moon_sign, sun_sign,
 * ayanamsha, current_maha_antar. Sourced from chart_facts (graha_position,
 * fact_subject IN LAGNA/MOON/SUN) + charts (name) + chart_dashas (current
 * vimshottari Maha/Antar, level_n 1/2, containing as_of_date).
 */
import { query } from '@/lib/db/client'
import type { ChartHeader } from './envelope'
import { DEFAULT_AYANAMSHA } from './registry/constants'

const HEADER_CACHE_TTL_MS = 60_000
const _headerCache = new Map<string, { data: ChartHeader; expiresAt: number }>()

function cacheKeyFor(chart_id: string, ayanamsha_id: string, as_of_date: string): string {
  return `chart_header::${chart_id}::${ayanamsha_id}::${as_of_date}`
}

/**
 * Fetch the ~40-token chart_header for a chart. Read-only; three cheap queries
 * (positions, dasha, name), 60s in-process cache (same locality caveat as the
 * general retrieval cache — see design §18: per-instance, not cross-process).
 */
export async function fetchChartHeader(
  chart_id: string,
  ayanamsha_id: string = DEFAULT_AYANAMSHA,
  as_of_date?: string,
): Promise<ChartHeader> {
  const asOf = as_of_date ?? new Date().toISOString().slice(0, 10)
  const ck = cacheKeyFor(chart_id, ayanamsha_id, asOf)
  const cached = _headerCache.get(ck)
  if (cached && Date.now() < cached.expiresAt) return cached.data

  const header: ChartHeader = {
    chart_id_short: chart_id.slice(0, 8),
    name: null,
    lagna_sign: null,
    lagna_deg: null,
    moon_sign: null,
    sun_sign: null,
    ayanamsha: ayanamsha_id,
    current_maha_antar: null,
  }

  try {
    const [nameResult, positionResult, dashaResult] = await Promise.all([
      query<{ name: string | null }>(
        `SELECT name FROM charts WHERE chart_id = $1 OR id = $1 LIMIT 1`,
        [chart_id],
      ),
      query<{ fact_subject: string; fact_key: string; fact_value_text: string | null; fact_value_num: string | null }>(
        `SELECT fact_subject, fact_key, fact_value_text, fact_value_num
         FROM chart_facts
         WHERE chart_id = $1 AND ayanamsha_id = $2 AND fact_category = 'graha_position'
           AND fact_subject IN ('LAGNA', 'MOON', 'SUN')
           AND fact_key IN ('sign', 'longitude_sidereal')`,
        [chart_id, ayanamsha_id],
      ),
      query<{ lord_graha: string; level_n: number }>(
        `SELECT lord_graha, level_n FROM chart_dashas
         WHERE chart_id = $1 AND ayanamsha_id = $2 AND system_id = 'vimshottari'
           AND level_n IN (1, 2) AND start_date <= $3::date AND end_date >= $3::date
         ORDER BY level_n LIMIT 2`,
        [chart_id, ayanamsha_id, asOf],
      ),
    ])

    header.name = nameResult.rows[0]?.name ?? null

    for (const row of positionResult.rows) {
      const subj = row.fact_subject
      const key = row.fact_key
      if (subj === 'LAGNA' && key === 'sign') header.lagna_sign = row.fact_value_text
      if (subj === 'LAGNA' && key === 'longitude_sidereal') {
        header.lagna_deg = row.fact_value_num !== null ? Number(row.fact_value_num) : null
      }
      if (subj === 'MOON' && key === 'sign') header.moon_sign = row.fact_value_text
      if (subj === 'SUN' && key === 'sign') header.sun_sign = row.fact_value_text
    }

    const maha = dashaResult.rows.find(r => r.level_n === 1)?.lord_graha ?? null
    const antar = dashaResult.rows.find(r => r.level_n === 2)?.lord_graha ?? null
    header.current_maha_antar = maha && antar ? `${maha} MD / ${antar} AD` : (maha ? `${maha} MD` : null)
  } catch {
    // Frame-safety header is a best-effort convenience block, not a hard dependency —
    // a failure here must never fail the instrument's own response. Fields stay null.
  }

  _headerCache.set(ck, { data: header, expiresAt: Date.now() + HEADER_CACHE_TTL_MS })
  return header
}
