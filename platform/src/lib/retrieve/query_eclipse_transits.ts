/**
 * MARSYS-JIS Retrieval tool — query_eclipse_transits (UDA-1-S6)
 *
 * Portal port of the MCP query_eclipse_transits surgical primitive.
 * Scans a date range for solar and lunar eclipses using ephemeris_daily.
 *
 * Eclipse detection algorithm:
 *   - Solar eclipse: Sun–Moon angular separation ≤ 1° AND Moon within 12° of
 *     a lunar node (Rahu or Ketu).
 *   - Lunar eclipse: Sun–Moon angular separation within 1° of 180° (opposition)
 *     AND Moon within 12° of a lunar node.
 *
 * Optionally flags eclipses conjunct the native's natal Sun, Moon, or ASC
 * within 5° when natal_sensitive_points=true.
 *
 * Source: platform-mcp/src/tools/query_eclipse_transits.ts (TR-P8-S1)
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_eclipse_transits'
const TOOL_VERSION = '1.0.0'

// ── Constants ─────────────────────────────────────────────────────────────────

/** Max angular separation (Sun–Moon) for a solar eclipse conjunction (degrees). */
const SOLAR_ECLIPSE_SYNODIC_ORB = 1.0
/** Max angular separation from 180° (Sun–Moon) for a lunar eclipse (degrees). */
const LUNAR_ECLIPSE_OPPOSITION_ORB = 1.0
/** Max Moon distance from a node for eclipse to occur (degrees). */
const NODE_ORB = 12.0
/** Orb to flag eclipse conjunct a natal sensitive point (degrees). */
const NATAL_POINT_ORB = 5.0

/** Zodiac sign from ecliptic longitude (0–360°). */
const SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const
type ZodiacSign = typeof SIGNS[number]

/** Native natal sensitive-point longitudes (FORENSIC data, canonical). */
const NATIVE_NATAL_POINTS: Record<string, number> = {
  natal_sun: 316.0,   // Aquarius ~16°
  natal_moon: 335.0,  // Pisces ~5°
  natal_asc: 45.0,    // Taurus ~15°
}

// ── Input interface ───────────────────────────────────────────────────────────

export interface QueryEclipseTransitsInput {
  /** Date range to scan for eclipses. Defaults to the current calendar year. */
  date_range?: {
    from: string  // ISO YYYY-MM-DD
    to: string    // ISO YYYY-MM-DD
  }
  /** Filter by eclipse type: "solar", "lunar", or "all". Default: "all". */
  eclipse_type?: 'solar' | 'lunar' | 'all'
  /** When true, flag eclipses within 5° of the native's natal Sun, Moon, or ASC. Default: false. */
  natal_sensitive_points?: boolean
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface EclipseEvent {
  date: string
  eclipse_type: 'solar' | 'lunar'
  degree: number
  sign: ZodiacSign
  conjunct_natal_point: string | null
  impact_assessment: string
}

interface EphemerisRow {
  date: string
  planet: string
  longitude_deg: string | number
  latitude_deg: string | number | null
  speed_deg_per_day: string | number
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Get current calendar year date range. */
function currentYearRange(): { from: string; to: string } {
  const year = new Date().getFullYear()
  return { from: `${year}-01-01`, to: `${year}-12-31` }
}

/**
 * Minimum angular distance between two ecliptic longitudes (0–360°).
 * Returns value in [0, 180].
 */
function angularSep(a: number, b: number): number {
  const diff = Math.abs(a - b) % 360
  return diff > 180 ? 360 - diff : diff
}

/** Zodiac sign from ecliptic longitude. */
function signFromLongitude(longitude: number): ZodiacSign {
  const idx = Math.floor(((longitude % 360) + 360) % 360 / 30)
  return SIGNS[idx] ?? 'Aries'
}

/** Degree within sign (0–29.999…). */
function degreeInSign(longitude: number): number {
  return Math.round(((longitude % 360) + 360) % 360 % 30 * 1000) / 1000
}

/**
 * Check whether the eclipse Moon longitude is conjunct a natal sensitive point.
 * Returns the natal point name if within NATAL_POINT_ORB, else null.
 */
function findNatalConjunction(moonLon: number): string | null {
  for (const [pointName, natalLon] of Object.entries(NATIVE_NATAL_POINTS)) {
    if (angularSep(moonLon, natalLon) <= NATAL_POINT_ORB) {
      return pointName
    }
  }
  return null
}

/** Build a human-readable impact_assessment string. */
function buildImpactAssessment(
  type: 'solar' | 'lunar',
  sign: ZodiacSign,
  conjunctPoint: string | null,
): string {
  const base =
    type === 'solar'
      ? `Solar eclipse in ${sign} — new cycle initiation; themes of ${sign} activated.`
      : `Lunar eclipse in ${sign} — culmination and release; emotional themes of ${sign} surface.`
  if (conjunctPoint) {
    const humanName = conjunctPoint.replace('natal_', 'natal ').replace('_', ' ')
    return `${base} Closely conjunct ${humanName} — personally significant; heightened activation.`
  }
  return base
}

/**
 * Group ephemeris rows by date → planet → EphemerisRow.
 */
function groupEphemerisByDate(
  rows: EphemerisRow[],
): Map<string, Map<string, { longitude: number; declination?: number; speed?: number }>> {
  const byDate = new Map<string, Map<string, { longitude: number; declination?: number; speed?: number }>>()

  for (const row of rows) {
    const date = row.date
    const planet = row.planet.toLowerCase()
    if (!date || !planet) continue

    const lon = typeof row.longitude_deg === 'number'
      ? row.longitude_deg
      : parseFloat(row.longitude_deg as string)
    if (!isFinite(lon)) continue

    const dec = typeof row.latitude_deg === 'number'
      ? row.latitude_deg
      : row.latitude_deg !== null
        ? parseFloat(row.latitude_deg as string)
        : undefined
    const decFinite = dec !== undefined && isFinite(dec) ? dec : undefined

    const spd = typeof row.speed_deg_per_day === 'number'
      ? row.speed_deg_per_day
      : parseFloat(row.speed_deg_per_day as string)
    const spdFinite = isFinite(spd) ? spd : undefined

    if (!byDate.has(date)) byDate.set(date, new Map())
    byDate.get(date)!.set(planet, { longitude: lon, declination: decFinite, speed: spdFinite })
  }

  return byDate
}

// ── Core detection ────────────────────────────────────────────────────────────

/**
 * Detect eclipses from ephemeris data grouped by date.
 *
 * For each date where we have Sun, Moon, and at least one node:
 *   - Solar: Moon–Sun separation ≤ SOLAR_ECLIPSE_SYNODIC_ORB
 *            AND Moon–node distance ≤ NODE_ORB.
 *   - Lunar: Moon–Sun opposition ≤ LUNAR_ECLIPSE_OPPOSITION_ORB
 *            AND Moon–node distance ≤ NODE_ORB.
 *
 * Consecutive eclipse days (same eclipse window, gap < 25 days) are collapsed.
 */
function detectEclipses(
  byDate: Map<string, Map<string, { longitude: number; declination?: number; speed?: number }>>,
  typeFilter: 'solar' | 'lunar' | 'all',
  flagNatal: boolean,
): EclipseEvent[] {
  const events: EclipseEvent[] = []
  const seenDates = new Set<string>()
  const sortedDates = Array.from(byDate.keys()).sort()

  let lastEclipseDate: string | null = null

  for (const date of sortedDates) {
    const planets = byDate.get(date)!

    const sun = planets.get('sun')
    const moon = planets.get('moon')
    const rahu = planets.get('rahu')
    const ketu = planets.get('ketu')

    if (!sun || !moon) continue

    const sunLon = sun.longitude
    const moonLon = moon.longitude

    let nodeDistance = Infinity
    if (rahu) nodeDistance = Math.min(nodeDistance, angularSep(moonLon, rahu.longitude))
    if (ketu) nodeDistance = Math.min(nodeDistance, angularSep(moonLon, ketu.longitude))
    if (nodeDistance === Infinity) continue

    const sunMoonSep = angularSep(sunLon, moonLon)
    const sunMoonOpp = angularSep(sunMoonSep, 180)

    let detectedType: 'solar' | 'lunar' | null = null

    if (sunMoonSep <= SOLAR_ECLIPSE_SYNODIC_ORB && nodeDistance <= NODE_ORB) {
      detectedType = 'solar'
    } else if (sunMoonOpp <= LUNAR_ECLIPSE_OPPOSITION_ORB && nodeDistance <= NODE_ORB) {
      detectedType = 'lunar'
    }

    if (!detectedType) continue
    if (typeFilter !== 'all' && typeFilter !== detectedType) continue

    if (lastEclipseDate !== null) {
      const gap = (new Date(date).getTime() - new Date(lastEclipseDate).getTime()) / 86400000
      if (gap < 25) continue
    }

    if (seenDates.has(date)) continue
    seenDates.add(date)
    lastEclipseDate = date

    const sign = signFromLongitude(moonLon)
    const degree = degreeInSign(moonLon)
    const conjunctPoint = flagNatal ? findNatalConjunction(moonLon) : null
    const impact = buildImpactAssessment(detectedType, sign, conjunctPoint)

    events.push({
      date,
      eclipse_type: detectedType,
      degree,
      sign,
      conjunct_natal_point: conjunctPoint,
      impact_assessment: impact,
    })
  }

  return events
}

// ── Retrieve function ─────────────────────────────────────────────────────────

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  const input = (params ?? {}) as unknown as QueryEclipseTransitsInput

  const dateRange = input.date_range ?? currentYearRange()
  const typeFilter = input.eclipse_type ?? 'all'
  const flagNatal = input.natal_sensitive_points ?? false

  const storage = getStorageClient()

  // Fetch Sun, Moon, Rahu, Ketu for the date range
  const ephSql = `
    SELECT date::text AS date, planet,
           longitude_deg, latitude_deg, speed_deg_per_day
    FROM ephemeris_daily
    WHERE date >= $1::date
      AND date <= $2::date
      AND planet = ANY($3::text[])
    ORDER BY date ASC, planet ASC
  `
  const ephResult = await storage.query<EphemerisRow>(
    ephSql,
    [dateRange.from, dateRange.to, ['sun', 'moon', 'rahu', 'ketu']],
  )

  const byDate = groupEphemerisByDate(ephResult.rows)
  const eclipses = detectEclipses(byDate, typeFilter, flagNatal)

  const payload = {
    ok: true,
    date_range: dateRange,
    eclipse_type_filter: typeFilter,
    eclipses,
    total_eclipses: eclipses.length,
    epistemics: { surgical: true, source: 'ephemeris_computed' },
  }

  const content = JSON.stringify(payload)

  const results: ToolBundleResult[] = [{
    content,
    source_canonical_id: 'EPHEMERIS_DAILY',
    source_version: '1.0',
    confidence: 0.9,
    significance: 0.85,
  }]

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: input as unknown as Record<string, unknown>,
    status: eclipses.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: eclipses.length,
    latency_ms: Date.now() - start,
    token_estimate: Math.ceil(content.length / 4),
    data_asset_id: 'EPHEMERIS_DAILY',
    error_code: null,
    served_from_cache: false,
    fallback_used: false,
  })

  return makeBundle(start, input, results, content)
}

// ── Bundle factory ────────────────────────────────────────────────────────────

function makeBundle(
  start: number,
  input: QueryEclipseTransitsInput,
  results: ToolBundleResult[],
  hashSource: string,
): ToolBundle {
  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(hashSource.slice(0, 200))
      .digest('hex')

  return {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: input as unknown as Record<string, unknown>,
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }
}

// ── Tool registration ─────────────────────────────────────────────────────────

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Detects solar and lunar eclipses within a date range by scanning ephemeris_daily ' +
    'positions. Solar eclipse: Sun–Moon separation ≤ 1° and Moon within 12° of Rahu/Ketu. ' +
    'Lunar eclipse: Sun–Moon opposition within 1° and Moon within 12° of a node. ' +
    'Returns eclipse date, type, degree, sign, and optional natal-point flags. ' +
    'Use for "Find eclipses in 2026", "Upcoming solar eclipses near natal Sun". ' +
    'Prefer query_transit_event for standard transits; holistic_bundle for synthesis.',
  retrieve,
}
