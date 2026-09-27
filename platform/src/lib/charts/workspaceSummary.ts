import 'server-only'
import { query } from '@/lib/db/client'
import type { ForensicChart } from '@/lib/forensic/snapshot'
import { DEFAULT_AYANAMSHA } from '@/lib/retrieval/registry/constants'

/**
 * Chart-workspace summary reader (Jātaka chart workspace, Task 3).
 *
 * Reads only this chart's own L1/L1-derived rows: `chart_facts` graha-position
 * signs for the D1 grid, `chart_dashas` for the current Vimśottarī mahā/antar
 * daśā, and firings-authoritative `ga_yoga_firings` for confirmed yogas. It
 * never substitutes another chart's values: a chart with nothing computed gets
 * an honest empty D1 (`isEmpty`), and a failed read yields empty values plus a
 * flag rather than a plausible-looking default (CLAUDE.md §N.6/§N.7, B.10).
 *
 * Read-only. No computation beyond formatting a stored sidereal longitude as
 * degrees/minutes/seconds within its sign.
 */

export interface ConfirmedYoga {
  id: string
  name: string
}

export interface ChartWorkspaceSummary {
  d1: ForensicChart
  currentDasha: { md: string; ad: string; adEnd: string } | null
  confirmedYogas: ConfirmedYoga[]
  /** Honesty flags: e.g. `positions_unresolved`, `dasha_unresolved`, `yogas_unresolved`. */
  flags: string[]
}

const SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const

const GRAHAS = ['SUN', 'MOON', 'MARS', 'MERCURY', 'JUPITER', 'VENUS', 'SATURN', 'RAHU', 'KETU'] as const

const CONFIRMED_YOGA_LIMIT = 6

function titleCase(code: string): string {
  return code.charAt(0).toUpperCase() + code.slice(1).toLowerCase()
}

function degreeWithinSignDms(longitude: number): string {
  const within = ((longitude % 30) + 30) % 30
  let totalSeconds = Math.round(within * 3600)
  const deg = Math.floor(totalSeconds / 3600)
  totalSeconds -= deg * 3600
  const min = Math.floor(totalSeconds / 60)
  const sec = totalSeconds - min * 60
  return `${deg}°${String(min).padStart(2, '0')}′${String(sec).padStart(2, '0')}″`
}

function emptyD1(chartId: string): ForensicChart {
  return {
    chartId,
    lagnaSign: '',
    lagnaDegreeDms: '',
    houses: Array.from({ length: 12 }, (_, i) => ({ house: i + 1, sign: '', planets: [] as string[] })),
    topYogas: [],
    currentDasha: null,
    isEmpty: true,
  }
}

type PositionRow = {
  fact_subject: string
  fact_key: string
  fact_value_text: string | null
  fact_value_num: string | null
}

type DashaRow = { level_n: number; lord_graha: string; end_date: string }
type YogaRow = { yoga_canonical_id: string; name: string | null }

export async function getChartWorkspaceSummary(
  chartId: string,
  ayanamshaId: string = DEFAULT_AYANAMSHA,
): Promise<ChartWorkspaceSummary> {
  const flags: string[] = []
  const today = new Date().toISOString().slice(0, 10)

  const [positions, dashas, yogas] = await Promise.all([
    query<PositionRow>(
      `SELECT DISTINCT ON (fact_subject, fact_key)
              fact_subject, fact_key, fact_value_text, fact_value_num::text AS fact_value_num
         FROM chart_facts
        WHERE chart_id = $1 AND ayanamsha_id = $2
          AND fact_category = 'graha_position'
          AND fact_key IN ('sign', 'longitude_sidereal')
        ORDER BY fact_subject, fact_key, computed_at DESC, build_id DESC`,
      [chartId, ayanamshaId],
    ).then((r) => r.rows).catch(() => { flags.push('positions_unresolved'); return [] as PositionRow[] }),
    query<DashaRow>(
      `SELECT DISTINCT ON (level_n) level_n, lord_graha, end_date::text AS end_date
         FROM chart_dashas
        WHERE chart_id = $1 AND ayanamsha_id = $2 AND system_id = 'vimshottari'
          AND level_n IN (1, 2) AND start_date <= $3::date AND end_date >= $3::date
        ORDER BY level_n, start_date DESC, end_date, lord_graha`,
      [chartId, ayanamshaId, today],
    ).then((r) => r.rows).catch(() => { flags.push('dasha_unresolved'); return [] as DashaRow[] }),
    query<YogaRow>(
      `SELECT y.yoga_canonical_id, y.name
         FROM (
           SELECT DISTINCT ON (f.yoga_canonical_id)
                  f.yoga_canonical_id, c.name_en AS name, f.strength
             FROM ga_yoga_firings f
             LEFT JOIN brahma_yoga_catalog c ON c.canonical_id = f.yoga_canonical_id
            WHERE f.chart_id = $1 AND f.ayanamsha_id = $2
              AND f.fired = true AND NOT f.is_partial AND NOT f.bhanga_active
            ORDER BY f.yoga_canonical_id, f.strength DESC NULLS LAST, f.id
         ) y
        ORDER BY y.strength DESC NULLS LAST, y.yoga_canonical_id
        LIMIT ${CONFIRMED_YOGA_LIMIT}`,
      [chartId, ayanamshaId],
    ).then((r) => r.rows).catch(() => { flags.push('yogas_unresolved'); return [] as YogaRow[] }),
  ])

  const bySubject = new Map<string, PositionRow[]>()
  for (const row of positions) {
    bySubject.set(row.fact_subject, [...(bySubject.get(row.fact_subject) ?? []), row])
  }
  const signOf = (subject: string) =>
    bySubject.get(subject)?.find((r) => r.fact_key === 'sign')?.fact_value_text ?? null

  const lagnaSign = signOf('LAGNA')
  const lagnaIdx = lagnaSign ? SIGNS.indexOf(lagnaSign as (typeof SIGNS)[number]) : -1

  const md = dashas.find((d) => d.level_n === 1)
  const ad = dashas.find((d) => d.level_n === 2)
  const currentDasha = md && ad ? { md: titleCase(md.lord_graha), ad: titleCase(ad.lord_graha), adEnd: ad.end_date } : null

  const confirmedYogas = yogas.map((y) => ({ id: y.yoga_canonical_id, name: y.name ?? y.yoga_canonical_id }))

  if (lagnaIdx < 0) {
    return { d1: { ...emptyD1(chartId), currentDasha }, currentDasha, confirmedYogas, flags }
  }

  const houses = Array.from({ length: 12 }, (_, i) => ({
    house: i + 1,
    sign: SIGNS[(lagnaIdx + i) % 12],
    planets: [] as string[],
  }))
  for (const graha of GRAHAS) {
    const sign = signOf(graha)
    const signIdx = sign ? SIGNS.indexOf(sign as (typeof SIGNS)[number]) : -1
    if (signIdx < 0) continue
    houses[(signIdx - lagnaIdx + 12) % 12].planets.push(titleCase(graha))
  }

  const lagnaLongitude = bySubject.get('LAGNA')?.find((r) => r.fact_key === 'longitude_sidereal')?.fact_value_num
  return {
    d1: {
      chartId,
      lagnaSign: SIGNS[lagnaIdx],
      lagnaDegreeDms: lagnaLongitude != null ? degreeWithinSignDms(Number(lagnaLongitude)) : '',
      houses,
      topYogas: confirmedYogas.map((y) => y.name),
      currentDasha,
      isEmpty: false,
    },
    currentDasha,
    confirmedYogas,
    flags,
  }
}
