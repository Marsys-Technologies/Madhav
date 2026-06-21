/**
 * chart_data_adapter.ts — U4 Task A: de-hardcode the school engines.
 *
 * Provides:
 *   buildChartData(chartId, ayanamshaId?)  → ChartData
 *   buildSchoolSignals(chartId, school, domain, coverageTypes?)  → SignalScore[]
 *
 * Data sources (read-only L1–L3):
 *   chart_facts       → planet positions, dignity, house, ayanamsha
 *   chart_dashas      → active mahadasha/antardasha for any system (vimshottari, yogini)
 *   bodha_msr_signals → signal metadata (score, domain, signal_id, signal_name)
 *   school_signal_coverage → per-signal per-school classification (populated by Task A.0)
 *
 * NEVER writes to any table. Never references ABHISEK_CHART for real charts.
 * defaultSignals in the engines is the FALLBACK-OF-LAST-RESORT (guarded + warns).
 */
import 'server-only'
import { query } from '../db/client'
import type {
  ChartData,
  PlanetPosition,
  DashaState,
  YoginiState,
  SignalScore,
  SchoolName,
  Domain,
  CoverageType,
} from './types'

// ── Authority weights per domain (E2 — §2.5 spec; tuning bounds ±0.05) ──────

export const DOMAIN_AUTHORITY_WEIGHTS: Record<Domain, Record<SchoolName, number>> = {
  CAREER: {
    parashari: 0.20, jaimini: 0.22, kp: 0.16, tajika: 0.12,
    nadi: 0.12, bnn: 0.08, yogini: 0.10,
  },
  HEALTH: {
    parashari: 0.24, jaimini: 0.12, kp: 0.14, tajika: 0.12,
    nadi: 0.18, bnn: 0.10, yogini: 0.10,
  },
  RELATIONSHIP: {
    parashari: 0.22, jaimini: 0.16, kp: 0.14, tajika: 0.14,
    nadi: 0.14, bnn: 0.10, yogini: 0.10,
  },
  SPIRITUAL: {
    parashari: 0.22, jaimini: 0.18, kp: 0.10, tajika: 0.10,
    nadi: 0.16, bnn: 0.10, yogini: 0.14,
  },
  PSYCHOLOGICAL: {
    parashari: 0.22, jaimini: 0.14, kp: 0.12, tajika: 0.12,
    nadi: 0.14, bnn: 0.12, yogini: 0.14,
  },
}

// Planet name mapping: chart_facts stores 'Sun', 'Moon', etc.; types.ts uses lowercase.
const _toTypesPlanetName = (factName: string): string => factName.toLowerCase()

// Sign mapping: chart_facts stores 'Capricorn', etc.; types.ts uses lowercase.
const _toTypesSign = (factSign: string): string => factSign.toLowerCase()

// ── buildChartData ────────────────────────────────────────────────────────────

/**
 * Build a real ChartData for any chartId from L1 (chart_facts + chart_dashas).
 * Returns a ChartData with live planet positions, dasha state, and yogini state.
 * Does NOT reference ABHISEK_CHART or any hardcoded constant.
 */
export async function buildChartData(
  chartId: string,
  ayanamshaId: string = 'lahiri',
): Promise<ChartData> {
  // 1. Planet positions from chart_facts
  const planetsResult = await query<{
    graha_name: string
    rasi_name: string
    bhava_number: number
    degree_in_rasi: number
    is_retrograde: boolean
    is_exalted: boolean
    is_debilitated: boolean
  }>(
    `SELECT
       graha_name,
       rasi_name,
       bhava_number,
       degree_in_rasi,
       COALESCE(is_retrograde, false) AS is_retrograde,
       COALESCE(is_exalted, false) AS is_exalted,
       COALESCE(is_debilitated, false) AS is_debilitated
     FROM chart_facts
     WHERE chart_id = $1
       AND ayanamsha_id = $2
       AND fact_type = 'graha_placement'
       AND graha_name IS NOT NULL
     ORDER BY bhava_number, graha_name`,
    [chartId, ayanamshaId],
  )

  const planets: PlanetPosition[] = planetsResult.rows.map(r => ({
    planet: _toTypesPlanetName(r.graha_name),
    sign: _toTypesSign(r.rasi_name),
    house: r.bhava_number,
    degree: Number(r.degree_in_rasi),
    isRetrograde: Boolean(r.is_retrograde),
    isExalted: Boolean(r.is_exalted),
    isDebilitated: Boolean(r.is_debilitated),
  }))

  // 2. Ascendant, moon sign, sun sign from chart_facts
  const bodyResult = await query<{
    fact_type: string
    rasi_name: string
    graha_name: string | null
  }>(
    `SELECT fact_type, rasi_name, graha_name
     FROM chart_facts
     WHERE chart_id = $1
       AND ayanamsha_id = $2
       AND fact_type IN ('lagna', 'chandra_rasi', 'surya_rasi')`,
    [chartId, ayanamshaId],
  )

  let ascendant = 'unknown'
  let moonSign = 'unknown'
  let sunSign = 'unknown'
  for (const row of bodyResult.rows) {
    if (row.fact_type === 'lagna') ascendant = _toTypesSign(row.rasi_name)
    if (row.fact_type === 'chandra_rasi') moonSign = _toTypesSign(row.rasi_name)
    if (row.fact_type === 'surya_rasi') sunSign = _toTypesSign(row.rasi_name)
  }

  // 3. Active Vimshottari dasha from chart_dashas
  const today = new Date().toISOString().split('T')[0]
  const dashaResult = await query<{
    dasha_level: number
    graha_name: string
    start_date: string
    end_date: string
  }>(
    `SELECT dasha_level, graha_name, start_date, end_date
     FROM chart_dashas
     WHERE chart_id = $1
       AND ayanamsha_id = $2
       AND system_id = 'vimshottari'
       AND start_date <= $3
       AND end_date >= $3
     ORDER BY dasha_level
     LIMIT 3`,
    [chartId, ayanamshaId, today],
  )

  const dashaRows = dashaResult.rows
  const activeDasha: DashaState = {
    mahadasha: dashaRows[0]?.graha_name ?? 'unknown',
    antardasha: dashaRows[1]?.graha_name ?? 'unknown',
    pratyantardasha: dashaRows[2]?.graha_name,
    start: dashaRows[1]?.start_date ?? dashaRows[0]?.start_date ?? today,
    end: dashaRows[1]?.end_date ?? dashaRows[0]?.end_date ?? today,
  }

  // 4. Active Yogini dasha from chart_dashas
  const yoginiResult = await query<{
    graha_name: string
    dasha_name: string
    start_date: string
    end_date: string
  }>(
    `SELECT graha_name, COALESCE(dasha_name, graha_name) AS dasha_name, start_date, end_date
     FROM chart_dashas
     WHERE chart_id = $1
       AND ayanamsha_id = $2
       AND system_id = 'yogini'
       AND dasha_level = 1
       AND start_date <= $3
       AND end_date >= $3
     LIMIT 1`,
    [chartId, ayanamshaId, today],
  )

  let yoginiDasha: YoginiState | undefined
  if (yoginiResult.rows.length > 0) {
    const yr = yoginiResult.rows[0]
    const start = new Date(yr.start_date)
    const end = new Date(yr.end_date)
    const now = new Date()
    const totalMs = end.getTime() - start.getTime()
    const elapsedMs = now.getTime() - start.getTime()
    const totalYears = totalMs / (365.25 * 24 * 3600 * 1000)
    const elapsedYears = Math.max(0, elapsedMs / (365.25 * 24 * 3600 * 1000))
    yoginiDasha = {
      yogini: yr.dasha_name.toLowerCase(),
      lord: _toTypesPlanetName(yr.graha_name),
      yearsElapsed: Math.round(elapsedYears * 100) / 100,
      yearsRemaining: Math.round(Math.max(0, totalYears - elapsedYears) * 100) / 100,
    }
  }

  // 5. Chara padas (Jaimini karakas) from chart_facts
  const carakaResult = await query<{
    karaka_type: string
    graha_name: string
  }>(
    `SELECT karaka_type, graha_name
     FROM chart_facts
     WHERE chart_id = $1
       AND ayanamsha_id = $2
       AND fact_type = 'chara_karaka'`,
    [chartId, ayanamshaId],
  )

  const charaPadas: Record<string, string> = {}
  for (const r of carakaResult.rows) {
    if (r.karaka_type && r.graha_name) {
      charaPadas[r.karaka_type.toLowerCase()] = _toTypesPlanetName(r.graha_name)
    }
  }

  // 6. KP sub-lords from chart_facts
  const kpResult = await query<{
    bhava_or_planet: string
    sub_lord: string
  }>(
    `SELECT bhava_or_planet, sub_lord
     FROM chart_facts
     WHERE chart_id = $1
       AND ayanamsha_id = $2
       AND fact_type = 'kp_sub_lord'`,
    [chartId, ayanamshaId],
  )

  const kpSubLords: Record<string, string> = {}
  for (const r of kpResult.rows) {
    if (r.bhava_or_planet && r.sub_lord) {
      kpSubLords[r.bhava_or_planet.toLowerCase()] = _toTypesPlanetName(r.sub_lord)
    }
  }

  return {
    chartId,
    chartType: 'natal',
    ascendant,
    moonSign,
    sunSign,
    planets,
    activeDasha,
    yoginiDasha,
    charaPadas: Object.keys(charaPadas).length > 0 ? charaPadas : undefined,
    kpSubLords: Object.keys(kpSubLords).length > 0 ? kpSubLords : undefined,
    pendingFlags: [],   // Tājika + BNN flags resolved via Task B; adapter clears them
  }
}

// ── buildSchoolSignals ────────────────────────────────────────────────────────

/**
 * Build live SignalScore[] for a school+domain from L2 signals + L4 coverage classification.
 * Reads bodha_msr_signals × school_signal_coverage.
 *
 * coverageTypes defaults to ['primary'] for own-tradition signals.
 * Falls through to an empty array if school_signal_coverage is not yet populated
 * (Task A.0 prerequisite) — engines' defaultSignals then acts as guarded fallback.
 */
export async function buildSchoolSignals(
  chartId: string,
  school: SchoolName,
  domain: Domain,
  coverageTypes: CoverageType[] = ['primary'],
): Promise<SignalScore[]> {
  if (coverageTypes.length === 0) return []

  const coveragePlaceholders = coverageTypes.map((_, i) => `$${i + 3}`).join(', ')

  const result = await query<{
    signal_id: string
    signal_name: string
    domain_score: number
    strength_score: number
    confidence: number
  }>(
    `SELECT
       s.signal_id,
       s.signal_name,
       COALESCE(s.domain_score, 3.0)::float AS domain_score,
       COALESCE(s.strength_score, 0.5)::float AS strength_score,
       COALESCE(ssc.confidence, 0.7)::float AS confidence
     FROM bodha_msr_signals s
     JOIN school_signal_coverage ssc
       ON ssc.signal_id = s.signal_id
       AND ssc.chart_id = $1
       AND ssc.school = $2
       AND ssc.coverage_type IN (${coveragePlaceholders})
     WHERE s.chart_id = $1
       AND s.domain = $4
     ORDER BY (s.strength_score * ssc.confidence) DESC
     LIMIT 10`,
    [chartId, school, ...coverageTypes, domain],
  )

  return result.rows.map(r => ({
    signalId: r.signal_id,
    signalName: r.signal_name,
    score: Number(r.domain_score),
    weight: Number(r.confidence),
    attributionRef: `school_signal_coverage:${r.signal_id}:${school}`,
  }))
}

// ── getSchoolConsensus (read-path for ph_nimitta + U3 C13) ──────────────────

export interface SchoolConsensusResult {
  chartId: string
  domain: Domain
  nOf7: number
  convergenceLevel: 'HIGH' | 'MEDIUM' | 'LOW'
  perSchool: Record<SchoolName, number>
  weightedMeanScore: number
  meanDomainScore: number
  stdDomainScore: number
  direction: string
  divergenceFlag: boolean
  isTimingRefinementSignal: boolean
  convergenceNarrative?: string
}

/**
 * Read-path for ph_nimitta Axis 6 + U3 C13 school_consensus current.
 * Returns null if no convergence row exists yet (triggers the build route).
 */
export async function getSchoolConsensus(
  chartId: string,
  domain: Domain,
): Promise<SchoolConsensusResult | null> {
  const result = await query<{
    chart_id: string
    domain: string
    schools_agreeing: number
    convergence_level: string
    per_school_scores: Record<string, number>
    per_school_weighted: Record<string, number>
    weighted_mean_score: number
    mean_domain_score: number
    std_domain_score: number
    direction: string
    convergence_narrative: string | null
  }>(
    `SELECT
       chart_id, domain, schools_agreeing, convergence_level,
       per_school_scores, per_school_weighted,
       weighted_mean_score, mean_domain_score, std_domain_score,
       direction, convergence_narrative
     FROM convergence_scores
     WHERE chart_id = $1 AND domain = $2`,
    [chartId, domain],
  )

  if (result.rows.length === 0) return null
  const r = result.rows[0]

  // Check for any temporal_scope disagreement in this domain (timing-refinement signal)
  const disResult = await query<{ count: string }>(
    `SELECT COUNT(*) AS count
     FROM school_disagreements
     WHERE chart_id = $1 AND domain = $2 AND is_timing_refinement_signal = true`,
    [chartId, domain],
  )
  const isTimingRefinement = parseInt(disResult.rows[0]?.count ?? '0', 10) > 0

  return {
    chartId: r.chart_id,
    domain: r.domain as Domain,
    nOf7: r.schools_agreeing,
    convergenceLevel: r.convergence_level as 'HIGH' | 'MEDIUM' | 'LOW',
    perSchool: (r.per_school_scores ?? {}) as Record<SchoolName, number>,
    weightedMeanScore: Number(r.weighted_mean_score),
    meanDomainScore: Number(r.mean_domain_score),
    stdDomainScore: Number(r.std_domain_score),
    direction: r.direction,
    divergenceFlag: r.schools_agreeing < 4,
    isTimingRefinementSignal: isTimingRefinement,
    convergenceNarrative: r.convergence_narrative ?? undefined,
  }
}

// ── getTajikaYear (Task B — resolve [VARSHA_KUNDALI_PENDING]) ────────────────

export interface TajikaYearData {
  varsha_year: number
  varshesha: string
  muntha: string
}

/**
 * Read varṣeśa (year-lord) + muntha from l1_tajik_varsha_year_lords for a given year.
 * Used by tajika_engine to resolve [VARSHA_KUNDALI_PENDING].
 */
export async function getTajikaYear(
  chartId: string,
  year: number,
): Promise<TajikaYearData | null> {
  const result = await query<TajikaYearData>(
    `SELECT
       varsha_year,
       COALESCE(varshesha_by_tajik_classical, varshesha) AS varshesha,
       muntha
     FROM l1_tajik_varsha_year_lords
     WHERE chart_id = $1 AND varsha_year = $2
     LIMIT 1`,
    [chartId, year],
  )
  return result.rows[0] ?? null
}
