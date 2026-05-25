/**
 * MARSYS-JIS Retrieval tool — query_transits_over_natal (UDA-1-S1)
 *
 * Portal port of the MCP query_transits_over_natal surgical primitive.
 * Computes transit-to-natal aspect windows over a date range.
 *
 * Two-step computation:
 *   1. Fetch natal longitude from chart_facts (natal_positions, planet_positions,
 *      or lagna categories).
 *   2. Fetch ephemeris day-by-day positions from ephemeris_daily.
 *   3. Compute aspect windows in TypeScript (no server-side LLM).
 *
 * Source: platform-mcp/src/tools/query_transits_over_natal.ts (TR-P6-S1)
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_transits_over_natal'
const TOOL_VERSION = '1.0.0'

// ── Constants ─────────────────────────────────────────────────────────────────

const NATAL_POINTS = [
  'natal_sun', 'natal_moon', 'natal_mars', 'natal_mercury',
  'natal_jupiter', 'natal_venus', 'natal_saturn',
  'natal_rahu', 'natal_ketu', 'natal_asc',
] as const
type NatalPoint = typeof NATAL_POINTS[number]

const ALL_ASPECT_NAMES = ['conjunction', 'opposition', 'trine', 'square', 'sextile'] as const
type AspectName = typeof ALL_ASPECT_NAMES[number]

const ASPECT_ANGLES: Record<AspectName, number> = {
  conjunction: 0,
  opposition: 180,
  trine: 120,
  square: 90,
  sextile: 60,
}

// ── Input interface ───────────────────────────────────────────────────────────

export interface QueryTransitsOverNatalInput {
  date_range: {
    from: string  // ISO YYYY-MM-DD
    to: string    // ISO YYYY-MM-DD
  }
  /** The natal chart point to check transits over. */
  target_natal_point: NatalPoint
  /** Orb in degrees. Range: 0.1–10. Default 1.0. */
  orb_degrees?: number
  /** Which transiting planets to check. Omit for all 9 grahas. */
  transit_planets?: string[]
  /** Which aspect types to detect. Omit for all 5 major aspects. */
  aspects?: AspectName[]
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface TransitEvent {
  transit_planet: string
  aspect_type: string
  orb_at_entry: number
  orb_at_exact: number
  date_entered_orb: string
  date_exact: string
  date_left_orb: string
  duration_days: number
}

interface EphemerisRow {
  date: string
  planet: string
  longitude_deg: string | number
}

interface ChartFactsRow {
  fact_id: string
  category: string
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Compute the minimum angular distance between two ecliptic longitudes (0–360). */
function angularDistance(a: number, b: number): number {
  const diff = Math.abs(a - b) % 360
  return diff > 180 ? 360 - diff : diff
}

/**
 * Classify angular distance into an aspect name, or null if not in orb.
 */
function classifyAspect(
  distance: number,
  orb: number,
  aspects: readonly AspectName[],
): { aspect: AspectName; residualOrb: number } | null {
  for (const aspect of aspects) {
    const angle = ASPECT_ANGLES[aspect]
    const residualOrb = Math.abs(distance - angle)
    if (residualOrb <= orb) {
      return { aspect, residualOrb }
    }
  }
  return null
}

/** Map a natal_point key to a planet name for chart_facts matching. */
function natalPointToPlanetName(natalPoint: string): string {
  const mapping: Record<string, string> = {
    natal_sun: 'Sun',
    natal_moon: 'Moon',
    natal_mars: 'Mars',
    natal_mercury: 'Mercury',
    natal_jupiter: 'Jupiter',
    natal_venus: 'Venus',
    natal_saturn: 'Saturn',
    natal_rahu: 'Rahu',
    natal_ketu: 'Ketu',
    natal_asc: 'Asc',
  }
  return mapping[natalPoint] ?? natalPoint.replace('natal_', '')
}

/**
 * Extract natal longitude from chart_facts rows for a given planet name.
 */
function extractNatalLongitudeFromRows(rows: ChartFactsRow[], planetName: string): number | null {
  const planetLower = planetName.toLowerCase()
  const isAsc = ['asc', 'ascendant', 'lagna'].includes(planetLower)

  for (const row of rows) {
    const vj = row.value_json
    if (!vj || typeof vj !== 'object') continue

    // Check planet field
    const rowPlanet = (vj['planet'] ?? vj['graha'] ?? '') as string
    const rowPlanetLower = rowPlanet.toLowerCase()
    const rowMatches =
      rowPlanetLower === planetLower ||
      (isAsc && ['asc', 'ascendant', 'lagna'].includes(rowPlanetLower))

    if (!rowMatches) continue

    // Try common longitude field names
    for (const field of ['longitude', 'degree', 'lon', 'longitude_deg']) {
      const val = vj[field]
      if (typeof val === 'number' && isFinite(val)) return val
      if (typeof val === 'string') {
        const parsed = parseFloat(val)
        if (isFinite(parsed)) return parsed
      }
    }

    // Try value_number directly if row matches
    if (typeof row.value_number === 'number' && isFinite(row.value_number)) {
      return row.value_number
    }
  }
  return null
}

/** Days between two ISO date strings. */
function daysBetween(from: string, to: string): number {
  const msPerDay = 1000 * 60 * 60 * 24
  return Math.round((new Date(to).getTime() - new Date(from).getTime()) / msPerDay)
}

// ── Core computation ──────────────────────────────────────────────────────────

interface InOrbDay {
  date: string
  residualOrb: number
  aspect: AspectName
  planet: string
}

/**
 * Given ephemeris rows, compute transit windows over the given natal longitude.
 *
 * Algorithm:
 *   1. For each row determine whether the transiting planet is in orb for any aspect.
 *   2. Group consecutive in-orb days for the same (planet, aspect) key.
 *   3. Within each window, find the day with minimum residualOrb as the "exact" date.
 */
function computeTransitEvents(
  rows: EphemerisRow[],
  natalLongitude: number,
  orbDegrees: number,
  filterPlanets: string[] | undefined,
  filterAspects: readonly AspectName[],
): TransitEvent[] {
  const planetFilter = filterPlanets
    ? new Set(filterPlanets.map(p => p.toLowerCase()))
    : null

  // Collect in-orb days per (planet+aspect) key
  const daysByKey: Map<string, InOrbDay[]> = new Map()

  for (const row of rows) {
    if (planetFilter && !planetFilter.has(row.planet.toLowerCase())) continue

    const lon = typeof row.longitude_deg === 'number'
      ? row.longitude_deg
      : parseFloat(row.longitude_deg as string)
    if (!isFinite(lon)) continue

    const dist = angularDistance(lon, natalLongitude)
    const match = classifyAspect(dist, orbDegrees, filterAspects)
    if (!match) continue

    const key = `${row.planet}::${match.aspect}`
    if (!daysByKey.has(key)) daysByKey.set(key, [])
    daysByKey.get(key)!.push({
      date: row.date,
      residualOrb: match.residualOrb,
      aspect: match.aspect,
      planet: row.planet,
    })
  }

  // Group consecutive days into windows (gap tolerance: up to 2 calendar days)
  const events: TransitEvent[] = []

  for (const [, days] of daysByKey) {
    if (days.length === 0) continue

    days.sort((a, b) => a.date.localeCompare(b.date))

    const windows: InOrbDay[][] = []
    let currentWindow: InOrbDay[] = [days[0]!]

    for (let i = 1; i < days.length; i++) {
      const prev = currentWindow[currentWindow.length - 1]!
      const gap = daysBetween(prev.date, days[i]!.date)
      if (gap <= 2) {
        currentWindow.push(days[i]!)
      } else {
        windows.push(currentWindow)
        currentWindow = [days[i]!]
      }
    }
    windows.push(currentWindow)

    for (const window of windows) {
      if (window.length === 0) continue

      const entryDay = window[0]!
      const exitDay = window[window.length - 1]!

      // Find exact day (minimum residual orb)
      let exactDay = window[0]!
      for (const d of window) {
        if (d.residualOrb < exactDay.residualOrb) exactDay = d
      }

      const durationDays = daysBetween(entryDay.date, exitDay.date) + 1

      events.push({
        transit_planet: entryDay.planet,
        aspect_type: entryDay.aspect,
        orb_at_entry: Math.round(entryDay.residualOrb * 1000) / 1000,
        orb_at_exact: Math.round(exactDay.residualOrb * 1000) / 1000,
        date_entered_orb: entryDay.date,
        date_exact: exactDay.date,
        date_left_orb: exitDay.date,
        duration_days: durationDays,
      })
    }
  }

  events.sort((a, b) => a.date_entered_orb.localeCompare(b.date_entered_orb))
  return events
}

// ── Retrieve function ─────────────────────────────────────────────────────────

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  const input = (params ?? {}) as unknown as QueryTransitsOverNatalInput

  const orbDegrees = Math.min(10, Math.max(0.1, input.orb_degrees ?? 1.0))
  const filterAspects: readonly AspectName[] =
    input.aspects && input.aspects.length > 0 ? input.aspects : ALL_ASPECT_NAMES

  const targetNatalPoint = input.target_natal_point
  if (!targetNatalPoint || !NATAL_POINTS.includes(targetNatalPoint)) {
    const errContent = JSON.stringify({
      ok: false,
      error: 'invalid_natal_point',
      message: `target_natal_point must be one of: ${NATAL_POINTS.join(', ')}`,
    })
    return makeBundle(start, input, [{
      content: errContent,
      source_canonical_id: 'CHART_FACTS',
      source_version: '1.0',
      confidence: 0,
      significance: 0,
    }], errContent)
  }

  const dateRange = input.date_range
  if (!dateRange?.from || !dateRange?.to) {
    const errContent = JSON.stringify({
      ok: false,
      error: 'missing_date_range',
      message: 'date_range.from and date_range.to are required.',
    })
    return makeBundle(start, input, [{
      content: errContent,
      source_canonical_id: 'EPHEMERIS_DAILY',
      source_version: '1.0',
      confidence: 0,
      significance: 0,
    }], errContent)
  }

  const planetName = natalPointToPlanetName(targetNatalPoint)

  const storage = getStorageClient()

  // ── Step 1: Fetch natal longitude from chart_facts ────────────────────────

  let natalLongitude: number | null = null

  // Try natal_positions category first, then planet_positions / lagna
  for (const cat of ['natal_positions', 'planet_positions', 'lagna']) {
    if (natalLongitude !== null) break

    const cfResult = await storage.query<ChartFactsRow>(
      `SELECT fact_id, category, value_text, value_number, value_json
       FROM chart_facts
       WHERE is_stale = false
         AND category = $1
       ORDER BY fact_id
       LIMIT 100`,
      [cat],
    )

    natalLongitude = extractNatalLongitudeFromRows(cfResult.rows, planetName)
  }

  // Fallback: search by planet name across all categories
  if (natalLongitude === null) {
    const fallback = await storage.query<ChartFactsRow>(
      `SELECT fact_id, category, value_text, value_number, value_json
       FROM chart_facts
       WHERE is_stale = false
         AND (value_json->>'planet' ILIKE $1 OR fact_id ILIKE $2)
       ORDER BY fact_id
       LIMIT 50`,
      [`%${planetName}%`, `%${planetName}%`],
    )
    natalLongitude = extractNatalLongitudeFromRows(fallback.rows, planetName)
  }

  if (natalLongitude === null) {
    const errContent = JSON.stringify({
      ok: false,
      error: 'natal_longitude_not_found',
      message:
        `Could not resolve natal longitude for "${targetNatalPoint}" ` +
        `(planet: "${planetName}"). Check that natal_positions or planet_positions ` +
        `category has a row for this planet in chart_facts.`,
    })
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: input as unknown as Record<string, unknown>,
      status: 'zero_rows',
      rows_returned: 0,
      latency_ms: Date.now() - start,
      token_estimate: Math.ceil(errContent.length / 4),
      data_asset_id: 'CHART_FACTS',
      error_code: 'natal_longitude_not_found',
      served_from_cache: false,
      fallback_used: true,
    })
    return makeBundle(start, input, [{
      content: errContent,
      source_canonical_id: 'CHART_FACTS',
      source_version: '1.0',
      confidence: 0,
      significance: 0,
    }], errContent)
  }

  // ── Step 2: Fetch ephemeris positions for the date range ──────────────────

  // Build optional planet filter for the SQL query
  const planetFilterArg = input.transit_planets && input.transit_planets.length > 0
    ? input.transit_planets.map(p => p.toLowerCase())
    : null

  const ephSql = planetFilterArg
    ? `SELECT date::text, planet, longitude_deg
       FROM ephemeris_daily
       WHERE date >= $1::date AND date <= $2::date
         AND planet = ANY($3::text[])
       ORDER BY date ASC, planet ASC`
    : `SELECT date::text, planet, longitude_deg
       FROM ephemeris_daily
       WHERE date >= $1::date AND date <= $2::date
       ORDER BY date ASC, planet ASC`

  const ephArgs = planetFilterArg
    ? [dateRange.from, dateRange.to, planetFilterArg]
    : [dateRange.from, dateRange.to]

  const ephResult = await storage.query<EphemerisRow>(ephSql, ephArgs)
  const ephemerisRows = ephResult.rows

  // ── Step 3: Compute transit windows ──────────────────────────────────────

  const transitEvents = computeTransitEvents(
    ephemerisRows,
    natalLongitude,
    orbDegrees,
    input.transit_planets,
    filterAspects,
  )

  const payload = {
    ok: true,
    natal_point: targetNatalPoint,
    natal_longitude: Math.round(natalLongitude * 1000) / 1000,
    date_range: dateRange,
    transit_events: transitEvents,
    total_events: transitEvents.length,
    epistemics: { surgical: true },
  }

  const content = JSON.stringify(payload)

  const results: ToolBundleResult[] = [{
    content,
    source_canonical_id: 'EPHEMERIS_DAILY',
    source_version: '1.0',
    confidence: 0.9,
    significance: 0.8,
  }]

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: input as unknown as Record<string, unknown>,
    status: transitEvents.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: transitEvents.length,
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
  input: QueryTransitsOverNatalInput,
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
    invocation_params: input as unknown as object,
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }
}

// ── Export ────────────────────────────────────────────────────────────────────

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Computes transit-to-natal aspect windows over a date range. Given a natal point ' +
    '(natal_sun|natal_moon|natal_mars|natal_mercury|natal_jupiter|natal_venus|natal_saturn|' +
    'natal_rahu|natal_ketu|natal_asc) and optional transit planet / aspect filters, ' +
    'returns grouped windows with entry/exit/exact dates, orb values, and duration. ' +
    'Reads natal longitude from chart_facts and transit positions from ephemeris_daily. ' +
    'Use for "When does Jupiter conjunct natal Moon?" or "Find all Saturn transits over ' +
    'natal Ascendant." Prefer query_transit_event for sign-ingress lookups.',
  retrieve,
}
