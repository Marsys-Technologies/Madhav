/**
 * MARSYS-JIS Retrieval tool — chandra_balam_for_native (UDA-1-S8)
 *
 * Computes the Chandra Bala (Moon Strength) score for the native
 * (Abhisek Mohanty, birth Moon sign: Pisces / Meena, moon_sign_id=12) on a given date.
 * Chandra Bala assesses the strength of the Moon on a given day by its position
 * relative to the native's natal Moon sign using the classical positional scoring:
 * positions 1,3,6,7,10,11 from birth Moon sign are auspicious; others are weak.
 *
 * Classical source: Muhurta Chintamani §Chandra Bala; DP "Chandra Bala" reference.
 *
 * Position scores from birth Moon sign:
 *   1=0.80 (same sign), 2=0.30, 3=0.90 (Kshema), 4=0.20, 5=0.30,
 *   6=0.90 (Sadhaka), 7=0.85 (Mitra), 8=0.10 (Vadha), 9=0.40,
 *   10=0.90 (Karma), 11=0.95 (Labha — most auspicious), 12=0.30 (loss).
 *
 * Note: Chandra Bala is distinct from Tara Bala — Tara Bala uses nakshatra-level
 * counting (27 nakshatras); Chandra Bala uses sign-level counting (12 signs).
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'chandra_balam_for_native'
const TOOL_VERSION = '1.0.0'

/** Native's birth Moon sign: Pisces / Meena (1-indexed in 12-sign cycle) */
const NATIVE_BIRTH_MOON_SIGN_ID = 12

/** Chandra Bala position scores: index 0 = position 1 (same sign) … index 11 = position 12 */
const CHANDRA_BALA_SCORES: number[] = [
  0.80, // 1 — same sign as birth Moon
  0.30, // 2
  0.90, // 3 — Kshema
  0.20, // 4
  0.30, // 5
  0.90, // 6 — Sadhaka
  0.85, // 7 — Mitra
  0.10, // 8 — Vadha
  0.40, // 9
  0.90, // 10 — Karma
  0.95, // 11 — Labha (most auspicious)
  0.30, // 12 — loss
]

/** Classical position names for Chandra Bala (empty string = no classical name) */
const CHANDRA_POSITION_NAMES: string[] = [
  '', // placeholder (0 unused — 1-indexed positions follow)
  'Sama Rashi',  // 1
  '',            // 2
  'Kshema',      // 3
  '',            // 4
  '',            // 5
  'Sadhaka',     // 6
  'Mitra',       // 7
  'Vadha',       // 8
  '',            // 9
  'Karma',       // 10
  'Labha',       // 11
  '',            // 12
]

/** Zodiac sign names (1-indexed) matching ephemeris_daily 'sign' column values. */
const SIGN_NAMES_ORDERED: string[] = [
  '', // placeholder (0 unused)
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
]

function signNameToId(name: string): number | undefined {
  const normalized = name.trim()
  for (let i = 1; i <= 12; i++) {
    if (SIGN_NAMES_ORDERED[i].toLowerCase() === normalized.toLowerCase()) {
      return i
    }
  }
  // Partial match (first 4 chars)
  for (let i = 1; i <= 12; i++) {
    if (SIGN_NAMES_ORDERED[i].toLowerCase().startsWith(normalized.toLowerCase().slice(0, 4))) {
      return i
    }
  }
  return undefined
}

function computeChandraBala(moonSignId: number): {
  position_from_birth_moon: number
  chandra_bala_score: number
  interpretation: string
} {
  // Compute 1-indexed position from birth Moon sign (wraps in 12-sign cycle)
  const position = ((moonSignId - NATIVE_BIRTH_MOON_SIGN_ID + 12) % 12) + 1

  const score = CHANDRA_BALA_SCORES[position - 1] ?? 0.30
  const posName = CHANDRA_POSITION_NAMES[position] || `position ${position}`

  let interpretation: string
  if (score >= 0.90) {
    interpretation = `Highly auspicious — ${posName} from birth Moon (position ${position}); Moon strongly supports.`
  } else if (score >= 0.80) {
    interpretation = `Auspicious — ${posName} from birth Moon (position ${position}); Moon well-placed.`
  } else if (score >= 0.40) {
    interpretation = `Neutral — position ${position} from birth Moon; Moon moderately placed.`
  } else if (score >= 0.20) {
    interpretation = `Weak — ${posName} from birth Moon (position ${position}); Moon unfavourable; avoid important events.`
  } else {
    interpretation = `Inauspicious — ${posName} from birth Moon (position ${position}); Moon in Vadha; strongly avoid muhurta.`
  }

  return { position_from_birth_moon: position, chandra_bala_score: score, interpretation }
}

export interface ChandraBalamInput {
  /** ISO date (YYYY-MM-DD) to compute Chandra Bala for. */
  date: string
}

interface PanchangaRow {
  moon_nakshatra: string
  moon_longitude_deg: string
}

interface EphemerisRow {
  sign: string
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
  const input = (params ?? {}) as unknown as ChandraBalamInput
  const dateStr = input.date ?? new Date().toISOString().slice(0, 10)

  const storage = getStorageClient()

  let moonSignId: number
  let moonSignName: string
  let moonNakshatraName: string

  // Primary: ephemeris_daily has 'sign' (name) and 'nakshatra' (name) for moon.
  const ephResult = await storage.query<EphemerisRow>(
    `SELECT sign, nakshatra, sidereal_longitude::text AS sidereal_longitude
     FROM ephemeris_daily WHERE date = $1 AND planet = 'moon' LIMIT 1`,
    [dateStr]
  )

  if (ephResult.rows.length > 0) {
    const ephRow = ephResult.rows[0]
    moonSignName = ephRow.sign
    moonNakshatraName = ephRow.nakshatra

    const idFromName = signNameToId(ephRow.sign)
    if (idFromName !== undefined) {
      moonSignId = idFromName
    } else {
      // Derive from longitude if sign name not resolved
      const lon = Number(ephRow.sidereal_longitude)
      moonSignId = Math.floor(lon / 30) + 1
      moonSignName = SIGN_NAMES_ORDERED[moonSignId] ?? `sign_${moonSignId}`
    }
  } else {
    // Fallback: panchanga_daily has moon_longitude_deg to derive sign.
    const panchangaResult = await storage.query<PanchangaRow>(
      `SELECT moon_nakshatra, moon_longitude_deg::text AS moon_longitude_deg
       FROM panchanga_daily WHERE date = $1 LIMIT 1`,
      [dateStr]
    )

    if (panchangaResult.rows.length === 0) {
      throw new Error(`chandra_balam_for_native: no Moon data for date ${dateStr}`)
    }

    const row = panchangaResult.rows[0]
    moonNakshatraName = row.moon_nakshatra
    const lon = Number(row.moon_longitude_deg)
    moonSignId = Math.floor(lon / 30) + 1
    moonSignName = SIGN_NAMES_ORDERED[moonSignId] ?? `sign_${moonSignId}`
  }

  const chandraResult = computeChandraBala(moonSignId)

  const resultPayload = {
    date: dateStr,
    birth_moon_sign: 'Pisces',
    birth_moon_sign_id: NATIVE_BIRTH_MOON_SIGN_ID,
    moon_sign: moonSignName,
    moon_sign_id: moonSignId,
    moon_nakshatra: moonNakshatraName,
    ...chandraResult,
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
    "Chandra Bala (Moon Strength) for the native — scores the Moon's sign position relative to " +
    "native's birth Moon sign (Pisces/Meena, id=12) on a given date. " +
    'Positions 1,3,6,7,10,11 are auspicious; 4,8,12 are weak. ' +
    'Returns chandra_bala_score (0–1), position_from_birth_moon (1–12), moon_sign, and interpretation. ' +
    'Use for sign-level Moon strength check. Prefer tara_balam_for_native for nakshatra-level Tara Bala. ' +
    'Source: MC §Chandra Bala.',
  retrieve,
}
