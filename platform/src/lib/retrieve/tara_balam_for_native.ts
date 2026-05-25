/**
 * MARSYS-JIS Retrieval tool — tara_balam_for_native (UDA-1-S8)
 *
 * Computes the Tara Bala (Star Strength) score for the native
 * (Abhisek Mohanty, birth nakshatra: Purva Bhadrapada, nakshatra_id=25) on a
 * given date. Tara Bala is a classical Vedic muhurta technique assessing the
 * Moon's daily nakshatra relative to the native's birth nakshatra using the
 * Nava Tara Chakra (9-tara cycle).
 *
 * Classical source: Muhurta Chintamani §Tara Bala; Brihat Parashara Hora
 * Shastra §Tara; Jataka Parijata §Tara Bala computation.
 *
 * Tara positions (1-indexed from birth nakshatra):
 *   1=Janma (0.50), 2=Sampat (0.90), 3=Vipat (0.00),
 *   4=Kshema (0.85), 5=Pratyari (0.10), 6=Sadhaka (0.95),
 *   7=Vadha (0.00), 8=Mitra (0.80), 9=Ati-Mitra (1.00).
 *   Positions 10–18: 0.80 attenuation. Positions 19–27: 0.60 attenuation.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'tara_balam_for_native'
const TOOL_VERSION = '1.0.0'

/** Native's birth nakshatra: Purva Bhadrapada (1-indexed in 27-nakshatra cycle) */
const NATIVE_BIRTH_NAKSHATRA_ID = 25

/** Nava Tara Chakra: position 1–9 (0-indexed offset = position - 1) → score */
const TARA_BASE_SCORES: number[] = [0.50, 0.90, 0.00, 0.85, 0.10, 0.95, 0.00, 0.80, 1.00]

/** Tara names for positions 1–9 */
const TARA_NAMES: string[] = [
  'Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyari',
  'Sadhaka', 'Vadha', 'Mitra', 'Ati-Mitra',
]

/** Cycle attenuation factors: cycle 1 (positions 1–9), cycle 2 (10–18), cycle 3 (19–27) */
const CYCLE_ATTENUATION = [1.0, 0.80, 0.60]

/**
 * 27-nakshatra list in order (0-indexed = nakshatra id - 1).
 * Standard Vedic sidereal order starting from Ashwini.
 */
const NAKSHATRA_NAMES_ORDERED: string[] = [
  'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira',
  'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha', 'Magha',
  'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati',
  'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
  'Uttara Ashadha', 'Shravana', 'Dhanishtha', 'Shatabhisha',
  'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati',
]

function nakshatraNameToId(name: string): number | undefined {
  // Try exact match first, then case-insensitive, then normalized.
  const normalized = name.trim()
  for (let i = 0; i < NAKSHATRA_NAMES_ORDERED.length; i++) {
    if (NAKSHATRA_NAMES_ORDERED[i].toLowerCase() === normalized.toLowerCase()) {
      return i + 1  // 1-indexed
    }
  }
  // Partial match (handles alternate spellings like "P.Bhadrapada")
  for (let i = 0; i < NAKSHATRA_NAMES_ORDERED.length; i++) {
    if (NAKSHATRA_NAMES_ORDERED[i].toLowerCase().startsWith(normalized.toLowerCase().slice(0, 5))) {
      return i + 1
    }
  }
  return undefined
}

function computeTaraBala(moonNakshatraId: number): {
  tara_count: number
  tara_name: string
  score: number
  cycle: number
  interpretation: string
} {
  // Compute 1-indexed position from birth nakshatra (wraps in 27-nakshatra cycle)
  const position = ((moonNakshatraId - NATIVE_BIRTH_NAKSHATRA_ID + 27) % 27) + 1

  const cycleIndex = Math.floor((position - 1) / 9)      // 0, 1, or 2
  const posInCycle = ((position - 1) % 9)                // 0–8 within the cycle

  const baseScore = TARA_BASE_SCORES[posInCycle]
  const attenuation = CYCLE_ATTENUATION[cycleIndex] ?? 0.60
  const score = Math.round(baseScore * attenuation * 100) / 100

  const taraName = TARA_NAMES[posInCycle]
  const cycle = cycleIndex + 1

  let interpretation: string
  if (score >= 0.90) {
    interpretation = `Highly auspicious — ${taraName} tara (cycle ${cycle}); strongly favourable.`
  } else if (score >= 0.80) {
    interpretation = `Auspicious — ${taraName} tara (cycle ${cycle}); favourable for purposeful action.`
  } else if (score >= 0.50) {
    interpretation = `Neutral — ${taraName} tara (cycle ${cycle}); proceed with awareness.`
  } else if (score >= 0.10) {
    interpretation = `Weak — ${taraName} tara (cycle ${cycle}); exercise caution; avoid important beginnings.`
  } else {
    interpretation = `Inauspicious — ${taraName} tara (cycle ${cycle}); avoid new ventures on this date.`
  }

  return { tara_count: position, tara_name: taraName, score, cycle, interpretation }
}

export interface TaraBalamInput {
  /** ISO date (YYYY-MM-DD) to compute Tara Bala for. */
  date: string
}

interface PanchangaRow {
  moon_nakshatra: string
  moon_nakshatra_index: number
}

interface EphemerisRow {
  nakshatra: string
  sidereal_longitude: string
}

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  try {
    return await retrieveImpl(plan, params, start)
  } catch (err) {
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: (params ?? null) as Record<string, unknown> | null,
      status: 'error',
      rows_returned: 0,
      latency_ms: Date.now() - start,
      token_estimate: 0,
      data_asset_id: 'PANCHANGA_DAILY',
      error_code: err instanceof Error ? err.message : String(err),
      served_from_cache: false,
      fallback_used: false,
    })
    throw err
  }
}

async function retrieveImpl(
  plan: QueryPlan,
  params: Record<string, unknown> | undefined,
  start: number,
): Promise<ToolBundle> {
  const input = (params ?? {}) as unknown as TaraBalamInput
  const dateStr = input.date ?? new Date().toISOString().slice(0, 10)

  const storage = getStorageClient()

  let moonNakshatraId: number
  let moonNakshatraName: string

  // Primary: panchanga_daily has moon_nakshatra (name) and moon_nakshatra_index (1-indexed).
  const panchangaResult = await storage.query<PanchangaRow>(
    `SELECT moon_nakshatra, moon_nakshatra_index FROM panchanga_daily WHERE date = $1 LIMIT 1`,
    [dateStr]
  )

  if (panchangaResult.rows.length > 0) {
    const row = panchangaResult.rows[0]
    moonNakshatraName = row.moon_nakshatra
    moonNakshatraId = row.moon_nakshatra_index  // 1-indexed in panchanga
  } else {
    // Fallback: ephemeris_daily — derive nakshatra_id from name or longitude.
    const ephResult = await storage.query<EphemerisRow>(
      `SELECT nakshatra, sidereal_longitude FROM ephemeris_daily WHERE date = $1 AND planet = 'moon' LIMIT 1`,
      [dateStr]
    )

    if (ephResult.rows.length === 0) {
      throw new Error(`tara_balam_for_native: no Moon data for date ${dateStr}`)
    }

    const ephRow = ephResult.rows[0]
    moonNakshatraName = ephRow.nakshatra

    const idFromName = nakshatraNameToId(ephRow.nakshatra)
    if (idFromName !== undefined) {
      moonNakshatraId = idFromName
    } else {
      // Last resort: derive from sidereal longitude (each nakshatra = 13.333°)
      const lon = Number(ephRow.sidereal_longitude)
      moonNakshatraId = Math.floor(lon / (360 / 27)) + 1
      moonNakshatraName = NAKSHATRA_NAMES_ORDERED[moonNakshatraId - 1] ?? `nakshatra_${moonNakshatraId}`
    }
  }

  const taraResult = computeTaraBala(moonNakshatraId)

  const resultPayload = {
    date: dateStr,
    birth_nakshatra: 'Purva Bhadrapada',
    birth_nakshatra_id: NATIVE_BIRTH_NAKSHATRA_ID,
    moon_nakshatra: moonNakshatraName,
    moon_nakshatra_id: moonNakshatraId,
    ...taraResult,
    native: 'Abhisek Mohanty',
    epistemics: { surgical: true },
  }

  const results: ToolBundleResult[] = [{
    content: JSON.stringify(resultPayload),
    source_canonical_id: 'PANCHANGA_DAILY',
    source_version: '1.0',
    confidence: 0.95,
    significance: 0.80,
  }]

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: { date: dateStr },
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: { date: dateStr } as Record<string, unknown>,
    status: 'success',
    rows_returned: 1,
    latency_ms: bundle.latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'PANCHANGA_DAILY',
    error_code: null,
    served_from_cache: false,
    fallback_used: false,
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Tara Bala (Star Strength) for the native — computes the Nava Tara Chakra position of the ' +
    "Moon's daily nakshatra relative to native's birth nakshatra (Purva Bhadrapada, id=25). " +
    'Returns tara_count (1–27), tara_name (Janma→Ati-Mitra), score (0–1), and interpretation. ' +
    'Use for single-date muhurta screening. Prefer muhurta_finder for date-range search. ' +
    'Source: MC §Tara Bala; BPHS §Tara.',
  retrieve,
}
