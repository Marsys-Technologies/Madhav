/**
 * query_transits_over_natal.ts — MCP Tier 3 surgical primitive: transit-to-natal aspect windows.
 *
 * What it does: Given a target natal point (e.g. "natal_moon") and a date range,
 * computes all in-orb transit windows where any of the selected transit planets
 * form a specified aspect (conjunction, opposition, trine, square, sextile) to
 * the natal longitude. Returns grouped transit windows with entry/exit dates,
 * exact date, orb at each boundary, and duration in days.
 *
 * Two-step computation:
 *   1. Fetch natal longitude from query_chart_facts (natal_positions category,
 *      fallback to planet_positions/lagna).
 *   2. Fetch ephemeris day-by-day positions via query_ephemeris.
 *   3. Compute aspect windows in TypeScript (no server-side LLM).
 *
 * When to prefer: Use for "When does Jupiter conjunct natal Moon?" or "Find all
 * Saturn transits over natal Ascendant in 2026." Prefer query_transit_event for
 * sign-ingress or station lookups. Prefer holistic_bundle when you also need
 * synthesised meaning of those transits.
 *
 * Input shape hints:
 *   date_range — required {from, to} ISO dates.
 *   target_natal_point — required; one of natal_sun|natal_moon|natal_mars|natal_mercury|
 *     natal_jupiter|natal_venus|natal_saturn|natal_rahu|natal_ketu|natal_asc.
 *   orb_degrees — optional, default 1.0, range [0.1, 10].
 *   transit_planets — optional filter; if omitted all 9 grahas are checked.
 *   aspects — optional filter; if omitted all 5 major aspects are checked.
 *
 * Output shape preview: {ok, natal_point, natal_longitude, date_range, transit_events, total_events}.
 *
 * TR-P6-S1: new MCP tool.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

// ── Constants ─────────────────────────────────────────────────────────────────

const NATAL_POINTS = [
  'natal_sun', 'natal_moon', 'natal_mars', 'natal_mercury',
  'natal_jupiter', 'natal_venus', 'natal_saturn',
  'natal_rahu', 'natal_ketu', 'natal_asc',
] as const

const TRANSIT_PLANETS = [
  'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu',
] as const

const ALL_ASPECTS = ['conjunction', 'opposition', 'trine', 'square', 'sextile'] as const
type AspectName = typeof ALL_ASPECTS[number]

/** Aspect definitions: target angle in degrees. */
const ASPECT_ANGLES: Record<AspectName, number> = {
  conjunction: 0,
  opposition: 180,
  trine: 120,
  square: 90,
  sextile: 60,
}

// ── Description ───────────────────────────────────────────────────────────────

export const QUERY_TRANSITS_OVER_NATAL_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Computes transit-to-natal aspect windows over a date range. ' +
    'For a given natal point (e.g. natal_moon) and transit planets, finds all dates ' +
    'when a transiting planet enters orb, reaches exactitude, and leaves orb for each ' +
    'major aspect (conjunction, opposition, trine, square, sextile). Returns grouped ' +
    'windows with entry/exit dates, exact date, orb values, and duration in days.',
  enumSource: NATAL_POINTS,
  whenToPrefer:
    'Use for "When does Jupiter conjunct natal Moon in 2026?" or "Find all Saturn aspects ' +
    'to natal Ascendant over the next year." Prefer query_transit_event for sign-ingress ' +
    'lookups. Prefer holistic_bundle when synthesised interpretation of the transits is needed.',
})

// ── Zod schema ────────────────────────────────────────────────────────────────

const QueryTransitsOverNatalInputSchema = z.object({
  date_range: z.object({
    from: z.string().describe('ISO start date (YYYY-MM-DD).'),
    to: z.string().describe('ISO end date (YYYY-MM-DD).'),
  }).describe('Date range to scan for transit events.'),
  target_natal_point: z.enum(NATAL_POINTS).describe(
    'The natal chart point to check transits over. ' +
    'Valid values: natal_sun | natal_moon | natal_mars | natal_mercury | natal_jupiter | ' +
    'natal_venus | natal_saturn | natal_rahu | natal_ketu | natal_asc.'
  ),
  orb_degrees: z.number().min(0.1).max(10).optional().default(1.0).describe(
    'Orb in degrees for aspect detection. Range: 0.1–10. Default 1.0.'
  ),
  transit_planets: z.array(z.enum(TRANSIT_PLANETS)).optional().describe(
    'Which transiting planets to check. Omit to check all 9 grahas.'
  ),
  aspects: z.array(z.enum(ALL_ASPECTS)).optional().describe(
    'Which aspect types to detect. Omit to detect all 5 major aspects: ' +
    'conjunction, opposition, trine, square, sextile.'
  ),
})

type QueryTransitsOverNatalInput = z.infer<typeof QueryTransitsOverNatalInputSchema>

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

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Compute the minimum angular distance between two ecliptic longitudes (0–360). */
function angularDistance(a: number, b: number): number {
  const diff = Math.abs(a - b) % 360
  return diff > 180 ? 360 - diff : diff
}

/**
 * Classify angular distance into an aspect name, or null if no aspect is in orb.
 * Returns the matching aspect and the residual orb (distance from exact aspect angle).
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

/**
 * Map a natal_point key to a planet name used to match rows in the ephemeris/chart_facts.
 * The natal_asc key maps to "Asc" / "Ascendant" / "Lagna".
 */
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
 * Unwrap a ToolBundle envelope returned by callPlatformPrimitive.
 * Returns the parsed inner data (from results[0].content), or null on failure.
 */
function unwrapToolBundle(envelope: Record<string, unknown>): unknown {
  const result = envelope['result']
  if (!result || typeof result !== 'object') return null
  const resultObj = result as Record<string, unknown>

  // ToolBundle pattern: result.results[0].content (JSON string)
  const bundleResults = resultObj['results'] as Array<{ content: unknown }> | undefined
  if (bundleResults && bundleResults.length > 0) {
    const raw = bundleResults[0].content
    if (typeof raw === 'string') {
      try { return JSON.parse(raw) } catch { /* fall through */ }
    }
    if (raw !== null && raw !== undefined) return raw
  }

  // Direct result object (some primitives skip ToolBundle wrapping)
  return resultObj
}

/**
 * Extract natal longitude (0–360) for a given planet from chart_facts data.
 * Looks for matching rows in natal_positions or planet_positions/lagna categories.
 *
 * Row shape from the platform is variable; we try several common field patterns:
 *   - value_num (numeric)
 *   - longitude, degree, lon
 *   - planet field matching the planet name (case-insensitive)
 */
function extractNatalLongitude(
  data: unknown,
  planetName: string,
): number | null {
  if (!data || typeof data !== 'object') return null
  const d = data as Record<string, unknown>

  // Try rows array (single-category response)
  const rows = d['rows'] as unknown[] | undefined
  if (Array.isArray(rows)) {
    return findLongitudeInRows(rows, planetName)
  }

  // Try rows_by_category (batched response)
  const rbc = d['rows_by_category'] as Record<string, unknown[]> | undefined
  if (rbc) {
    for (const cat of ['natal_positions', 'planet_positions', 'lagna']) {
      const catRows = rbc[cat]
      if (Array.isArray(catRows) && catRows.length > 0) {
        const found = findLongitudeInRows(catRows, planetName)
        if (found !== null) return found
      }
    }
  }

  return null
}

function findLongitudeInRows(rows: unknown[], planetName: string): number | null {
  const planetLower = planetName.toLowerCase()
  // Aliases for Ascendant
  const isAsc = ['asc', 'ascendant', 'lagna'].includes(planetLower)

  for (const row of rows) {
    if (!row || typeof row !== 'object') continue
    const r = row as Record<string, unknown>

    // Check planet field matches
    const rowPlanet = (r['planet'] ?? r['graha'] ?? '') as string
    const rowPlanetLower = rowPlanet.toLowerCase()
    const rowMatches =
      rowPlanetLower === planetLower ||
      (isAsc && ['asc', 'ascendant', 'lagna'].includes(rowPlanetLower))

    if (!rowMatches) continue

    // Extract longitude value
    for (const field of ['longitude', 'degree', 'lon', 'value_num']) {
      const val = r[field]
      if (typeof val === 'number' && isFinite(val)) {
        return val
      }
      if (typeof val === 'string') {
        const parsed = parseFloat(val)
        if (isFinite(parsed)) return parsed
      }
    }
  }
  return null
}

/**
 * Extract planetary position rows from ephemeris data.
 * Returns array of { date, planet, longitude } objects.
 */
function extractEphemerisRows(
  data: unknown,
): Array<{ date: string; planet: string; longitude: number }> {
  if (!data || typeof data !== 'object') return []
  const d = data as Record<string, unknown>

  // Check for positions array directly on data or nested inside
  let positionsArr: unknown[] | undefined

  // Pattern 1: data.positions
  if (Array.isArray(d['positions'])) {
    positionsArr = d['positions']
  }
  // Pattern 2: data.rows
  else if (Array.isArray(d['rows'])) {
    positionsArr = d['rows']
  }

  if (!positionsArr) return []

  const result: Array<{ date: string; planet: string; longitude: number }> = []
  for (const item of positionsArr) {
    if (!item || typeof item !== 'object') continue
    const r = item as Record<string, unknown>

    const date = (r['date'] ?? '') as string
    const planet = (r['planet'] ?? r['graha'] ?? '') as string

    // longitude may come as 'longitude', 'degree', or 'lon'
    let longitude: number | null = null
    for (const field of ['longitude', 'degree', 'lon']) {
      const val = r[field]
      if (typeof val === 'number' && isFinite(val)) { longitude = val; break }
      if (typeof val === 'string') {
        const parsed = parseFloat(val)
        if (isFinite(parsed)) { longitude = parsed; break }
      }
    }

    if (date && planet && longitude !== null) {
      result.push({ date, planet, longitude })
    }
  }
  return result
}

/**
 * Days between two ISO date strings.
 */
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
 * Given a flat list of (date, planet, longitude) rows, compute transit windows
 * over the given natal longitude.
 *
 * Algorithm:
 *   1. For each row determine whether the transiting planet is in orb for any aspect.
 *   2. Group consecutive in-orb days for the same (planet, aspect) key.
 *   3. Within each window, find the day with minimum residualOrb as the "exact" date.
 */
function computeTransitEvents(
  rows: Array<{ date: string; planet: string; longitude: number }>,
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

    const dist = angularDistance(row.longitude, natalLongitude)
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

  // Group consecutive days into windows (gap tolerance: 1 day)
  const events: TransitEvent[] = []

  for (const [, days] of daysByKey) {
    if (days.length === 0) continue

    // Sort by date
    days.sort((a, b) => a.date.localeCompare(b.date))

    const windows: InOrbDay[][] = []
    let currentWindow: InOrbDay[] = [days[0]]

    for (let i = 1; i < days.length; i++) {
      const prev = currentWindow[currentWindow.length - 1]
      const gap = daysBetween(prev.date, days[i].date)
      if (gap <= 2) {
        // Allow up to 1-day gap (gap=2 means next day)
        currentWindow.push(days[i])
      } else {
        windows.push(currentWindow)
        currentWindow = [days[i]]
      }
    }
    windows.push(currentWindow)

    for (const window of windows) {
      if (window.length === 0) continue

      const entryDay = window[0]
      const exitDay = window[window.length - 1]

      // Find exact day (minimum residual orb)
      let exactDay = window[0]
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

  // Sort chronologically
  events.sort((a, b) => a.date_entered_orb.localeCompare(b.date_entered_orb))
  return events
}

// ── MCP tool registration ─────────────────────────────────────────────────────

export function registerQueryTransitsOverNatal(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'query_transits_over_natal',
    QUERY_TRANSITS_OVER_NATAL_DESCRIPTION,
    QueryTransitsOverNatalInputSchema.shape,
    async (args: QueryTransitsOverNatalInput) => {
      const principal = getPrincipal()
      const orbDegrees = args.orb_degrees ?? 1.0
      const filterAspects: readonly AspectName[] =
        args.aspects && args.aspects.length > 0
          ? args.aspects
          : ALL_ASPECTS

      const planetName = natalPointToPlanetName(args.target_natal_point)

      // ── Step 1: Fetch natal longitude ─────────────────────────────────────

      const chartFactsResult = await callPlatformPrimitive(
        'query_chart_facts',
        { categories: ['natal_positions'], limit: 100 },
        principal,
      )

      let natalLongitude: number | null = null

      if (chartFactsResult.envelope.ok && chartFactsResult.status < 400) {
        const data = unwrapToolBundle(chartFactsResult.envelope as Record<string, unknown>)
        natalLongitude = extractNatalLongitude(data, planetName)
      }

      // Fallback to planet_positions / lagna if natal_positions returned nothing
      if (natalLongitude === null) {
        const fallbackResult = await callPlatformPrimitive(
          'query_chart_facts',
          { categories: ['planet_positions', 'lagna'], limit: 100 },
          principal,
        )
        if (fallbackResult.envelope.ok && fallbackResult.status < 400) {
          const data = unwrapToolBundle(fallbackResult.envelope as Record<string, unknown>)
          natalLongitude = extractNatalLongitude(data, planetName)
        }
      }

      if (natalLongitude === null) {
        return errorResult({
          ok: false,
          error: 'natal_longitude_not_found',
          message:
            `Could not resolve natal longitude for "${args.target_natal_point}" ` +
            `(planet: "${planetName}"). Check that natal_positions or planet_positions ` +
            `category has a row for this planet.`,
        })
      }

      // ── Step 2: Fetch ephemeris positions ─────────────────────────────────

      const ephemerisResult = await callPlatformPrimitive(
        'query_ephemeris',
        {
          start_date: args.date_range.from,
          end_date: args.date_range.to,
          sample_step: '1d',
        },
        principal,
      )

      if (!ephemerisResult.envelope.ok || ephemerisResult.status >= 400) {
        return errorResult(ephemerisResult.envelope)
      }

      const ephemerisData = unwrapToolBundle(
        ephemerisResult.envelope as Record<string, unknown>,
      )
      const ephemerisRows = extractEphemerisRows(ephemerisData)

      // ── Step 3: Compute transit windows ───────────────────────────────────

      const transitEvents = computeTransitEvents(
        ephemerisRows,
        natalLongitude,
        orbDegrees,
        args.transit_planets ? [...args.transit_planets] : undefined,
        filterAspects,
      )

      return okResult({
        ok: true,
        natal_point: args.target_natal_point,
        natal_longitude: Math.round(natalLongitude * 1000) / 1000,
        date_range: args.date_range,
        transit_events: transitEvents,
        total_events: transitEvents.length,
        epistemics: { surgical: true },
      })
    },
  )
}
