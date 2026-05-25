/**
 * query_planet_war.ts — MCP Tier 3 surgical primitive: Graha Yuddha (planetary war) detection.
 *
 * What it does: Detects Graha Yuddha (planetary war) events within a date range.
 * Classical rule: two true planets (Sun and Moon excluded) are within 1° of
 * each other in ecliptic longitude on the same day.
 *
 * Algorithm (thin engine over ephemeris_daily):
 *   1. Fetch ephemeris for the requested planets via query_ephemeris.
 *   2. For each date, compare each pair of planet longitudes.
 *      If |long1 - long2| ≤ 1.0° (with 360° wrap handling) → war event.
 *   3. Winner: planet with higher absolute declination wins (classical rule).
 *      If declination not available, the faster-moving planet (higher speed) wins.
 *   4. Append classical_interpretation based on the winner's identity.
 *
 * Classical interpretations (hardcoded per winning planet):
 *   Mars wins   → "Mars subjugates X — increased aggression, disruption"
 *   Venus wins  → "Venus prevails over X — artistic/material matters dominant"
 *   Saturn wins → "Saturn crushes X — delays, karma, obstruction"
 *   Mercury wins→ "Mercury overcomes X — intellect prevails"
 *   Jupiter wins→ "Jupiter triumphs over X — wisdom, dharma, expansion"
 *
 * 360° wrap: angular distance = min(|a-b|, 360 - |a-b|). This correctly
 * detects a war between a planet at 359° and one at 0.5° as 1.5° separation — no war;
 * and 359° vs 0.0° as 1° = exactly the boundary (included ≤ 1°).
 *
 * When to prefer: Use for "Is there a planetary war this year?" or "When do Mars
 * and Mercury come within 1°?" Prefer query_transit_event for ingress/station lookups.
 * Prefer holistic_bundle for full synthesis including war interpretation in chart context.
 *
 * Input shape hints:
 *   date_range — optional {from, to} ISO dates. Default: current calendar year.
 *   planets    — optional list. Default: all five true planets excluding luminaries.
 *   tier       — optional string (passed through for audit).
 *
 * Output shape preview:
 *   {ok, date_range, planets_checked, war_events: [{date, planet_1, planet_2,
 *    degree, longitude, winner, loser, classical_interpretation}], total_wars}
 *
 * TR-P8-S1: new MCP tool.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

// ── Constants ─────────────────────────────────────────────────────────────────

/** Maximum longitude separation (degrees) for Graha Yuddha. */
const WAR_ORB = 1.0

/** Traditional planets eligible for Graha Yuddha (no Sun/Moon/nodes). */
const DEFAULT_WAR_PLANETS = ['Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'] as const
type WarPlanet = typeof DEFAULT_WAR_PLANETS[number]

// ── Description ───────────────────────────────────────────────────────────────

export const QUERY_PLANET_WAR_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Detects Graha Yuddha (planetary war) — two true planets within 1° ' +
    'of each other in ecliptic longitude. Sun and Moon are excluded (classical rule). ' +
    'Returns each war event with date, the two planets, their shared longitude, winner ' +
    '(higher declination wins; speed as tiebreaker), and classical interpretation.',
  whenToPrefer:
    'Use for "Is there a planetary war in 2026?" or "When do Mars and Venus fight?" ' +
    'Prefer query_transit_event for sign-ingress and station lookups. ' +
    'Prefer holistic_bundle when synthesis of war significance in the full chart is needed.',
})

// ── Zod schema ────────────────────────────────────────────────────────────────

const QueryPlanetWarInputSchema = z.object({
  date_range: z.object({
    from: z.string().describe('ISO start date (YYYY-MM-DD).'),
    to: z.string().describe('ISO end date (YYYY-MM-DD).'),
  }).optional().describe(
    'Date range to scan for war events. Defaults to the current calendar year.'
  ),
  planets: z.array(z.enum(DEFAULT_WAR_PLANETS)).optional().describe(
    'Planets to include in war detection. Default: all five (Mars, Mercury, Jupiter, Venus, Saturn). ' +
    'Sun and Moon are excluded by the classical rule and cannot be specified.'
  ),
  tier: z.string().optional().describe('Audience tier (passed through for audit).'),
})

type QueryPlanetWarInput = z.infer<typeof QueryPlanetWarInputSchema>

// ── Types ─────────────────────────────────────────────────────────────────────

export interface WarEvent {
  date: string
  planet_1: string
  planet_2: string
  /** Angular separation between the two planets (degrees). */
  degree: number
  /** Mean longitude of the two planets at the war point. */
  longitude: number
  winner: string
  loser: string
  classical_interpretation: string
}

interface EphemerisRow {
  date: string
  planet: string
  longitude: number
  declination?: number
  speed?: number
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Get current calendar year date range. */
function currentYearRange(): { from: string; to: string } {
  const year = new Date().getFullYear()
  return { from: `${year}-01-01`, to: `${year}-12-31` }
}

/**
 * Minimum angular distance between two ecliptic longitudes (0–360°).
 * Correctly handles 360° wrap: angularSep(359, 0.5) = 1.5.
 */
export function angularSep(a: number, b: number): number {
  const diff = Math.abs(a - b)
  return diff > 180 ? 360 - diff : diff
}

/**
 * Build classical interpretation string.
 * winner = the winning planet name; loser = the losing planet name.
 */
export function buildWarInterpretation(winner: string, loser: string): string {
  const templates: Record<string, string> = {
    Mars: `Mars subjugates ${loser} — increased aggression, disruption`,
    Venus: `Venus prevails over ${loser} — artistic/material matters dominant`,
    Saturn: `Saturn crushes ${loser} — delays, karma, obstruction`,
    Mercury: `Mercury overcomes ${loser} — intellect prevails`,
    Jupiter: `Jupiter triumphs over ${loser} — wisdom, dharma, expansion`,
  }
  return templates[winner] ?? `${winner} defeats ${loser} in Graha Yuddha`
}

/**
 * Determine the winner between two planets.
 *
 * Classical rule: higher absolute declination wins.
 * Tiebreaker: higher daily speed (faster planet wins).
 * If neither available: default to planet_1 (first alphabetically by name).
 *
 * Returns { winner, loser }.
 */
export function determineWinner(
  planet1: EphemerisRow,
  planet2: EphemerisRow,
): { winner: string; loser: string } {
  // Declination-based (primary)
  if (
    planet1.declination !== undefined &&
    planet2.declination !== undefined
  ) {
    const dec1 = Math.abs(planet1.declination)
    const dec2 = Math.abs(planet2.declination)
    if (dec1 !== dec2) {
      return dec1 > dec2
        ? { winner: planet1.planet, loser: planet2.planet }
        : { winner: planet2.planet, loser: planet1.planet }
    }
  }

  // Speed-based tiebreaker (faster planet wins)
  if (planet1.speed !== undefined && planet2.speed !== undefined) {
    const spd1 = Math.abs(planet1.speed)
    const spd2 = Math.abs(planet2.speed)
    if (spd1 !== spd2) {
      return spd1 > spd2
        ? { winner: planet1.planet, loser: planet2.planet }
        : { winner: planet2.planet, loser: planet1.planet }
    }
  }

  // Default: alphabetical (deterministic fallback)
  return planet1.planet < planet2.planet
    ? { winner: planet1.planet, loser: planet2.planet }
    : { winner: planet2.planet, loser: planet1.planet }
}

/**
 * Group ephemeris rows by date → planet → EphemerisRow.
 */
function groupEphemerisByDate(
  data: unknown,
): Map<string, Map<string, EphemerisRow>> {
  const byDate = new Map<string, Map<string, EphemerisRow>>()
  if (!data || typeof data !== 'object') return byDate

  const d = data as Record<string, unknown>
  let rows: unknown[] = []

  if (Array.isArray(d['positions'])) rows = d['positions']
  else if (Array.isArray(d['rows'])) rows = d['rows']

  for (const item of rows) {
    if (!item || typeof item !== 'object') continue
    const r = item as Record<string, unknown>

    const date = String(r['date'] ?? '')
    const planet = String(r['planet'] ?? r['graha'] ?? '')
    if (!date || !planet) continue

    let longitude: number | null = null
    for (const field of ['longitude', 'degree', 'lon']) {
      const val = r[field]
      if (typeof val === 'number' && isFinite(val)) { longitude = val; break }
      if (typeof val === 'string') {
        const p = parseFloat(val)
        if (isFinite(p)) { longitude = p; break }
      }
    }
    if (longitude === null) continue

    let declination: number | undefined
    const decVal = r['declination'] ?? r['dec']
    if (typeof decVal === 'number' && isFinite(decVal)) declination = decVal

    let speed: number | undefined
    const spdVal = r['speed'] ?? r['daily_motion']
    if (typeof spdVal === 'number' && isFinite(spdVal)) speed = spdVal

    if (!byDate.has(date)) byDate.set(date, new Map())
    byDate.get(date)!.set(planet.toLowerCase(), {
      date, planet, longitude, declination, speed,
    })
  }

  return byDate
}

/**
 * Unwrap a ToolBundle envelope returned by callPlatformPrimitive.
 */
function unwrapToolBundle(envelope: Record<string, unknown>): unknown {
  const result = envelope['result']
  if (!result || typeof result !== 'object') return null
  const resultObj = result as Record<string, unknown>
  const bundleResults = resultObj['results'] as Array<{ content: unknown }> | undefined
  if (bundleResults && bundleResults.length > 0) {
    const raw = bundleResults[0]!.content
    if (typeof raw === 'string') {
      try { return JSON.parse(raw) } catch { /* fall through */ }
    }
    if (raw !== null && raw !== undefined) return raw
  }
  return resultObj
}

// ── Core computation ──────────────────────────────────────────────────────────

/**
 * Detect Graha Yuddha war events from the grouped ephemeris data.
 *
 * For each date, compare all unique planet pairs (both in the targetPlanets set).
 * If angular separation ≤ WAR_ORB → record a war event.
 * Consecutive days of the same pair are collapsed (only first day is kept).
 */
export function detectPlanetWars(
  byDate: Map<string, Map<string, EphemerisRow>>,
  targetPlanets: readonly string[],
): WarEvent[] {
  const events: WarEvent[] = []
  const sortedDates = Array.from(byDate.keys()).sort()

  // Track last-seen war date per planet pair to avoid duplicating multi-day events
  const lastWarDate = new Map<string, string>()

  for (const date of sortedDates) {
    const planets = byDate.get(date)!
    const planetKeys = targetPlanets.map(p => p.toLowerCase())

    // Collect available planet rows for this date
    const available: EphemerisRow[] = []
    for (const key of planetKeys) {
      const row = planets.get(key)
      if (row) available.push(row)
    }

    // Compare each unique pair
    for (let i = 0; i < available.length; i++) {
      for (let j = i + 1; j < available.length; j++) {
        const p1 = available[i]!
        const p2 = available[j]!

        const sep = angularSep(p1.longitude, p2.longitude)
        if (sep > WAR_ORB) continue

        // Collapse consecutive days: skip if same pair had a war within 7 days
        const pairKey = [p1.planet, p2.planet].sort().join('::')
        const prev = lastWarDate.get(pairKey)
        if (prev !== undefined) {
          const gap = (new Date(date).getTime() - new Date(prev).getTime()) / 86400000
          if (gap < 7) continue  // same war window
        }
        lastWarDate.set(pairKey, date)

        const { winner, loser } = determineWinner(p1, p2)
        const meanLon = ((p1.longitude + p2.longitude) / 2 + 360) % 360
        const interpretation = buildWarInterpretation(winner, loser)

        events.push({
          date,
          planet_1: p1.planet,
          planet_2: p2.planet,
          degree: Math.round(sep * 1000) / 1000,
          longitude: Math.round(meanLon * 1000) / 1000,
          winner,
          loser,
          classical_interpretation: interpretation,
        })
      }
    }
  }

  return events
}

// ── MCP tool registration ─────────────────────────────────────────────────────

export function registerQueryPlanetWar(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'query_planet_war',
    QUERY_PLANET_WAR_DESCRIPTION,
    QueryPlanetWarInputSchema.shape,
    async (args: QueryPlanetWarInput) => {
      const principal = getPrincipal()
      const dateRange = args.date_range ?? currentYearRange()
      const targetPlanets: readonly WarPlanet[] =
        args.planets && args.planets.length > 0 ? args.planets : DEFAULT_WAR_PLANETS

      // ── Fetch ephemeris for the requested planets ──────────────────────────
      const ephResult = await callPlatformPrimitive(
        'query_ephemeris',
        {
          start_date: dateRange.from,
          end_date: dateRange.to,
          planets: [...targetPlanets],
          sample_step: '1d',
        },
        principal,
      )

      if (!ephResult.envelope.ok || ephResult.status >= 400) {
        return errorResult(ephResult.envelope)
      }

      const ephData = unwrapToolBundle(ephResult.envelope as unknown as Record<string, unknown>)
      const byDate = groupEphemerisByDate(ephData)

      // ── Detect planetary wars ──────────────────────────────────────────────
      const warEvents = detectPlanetWars(byDate, targetPlanets)

      return okResult({
        ok: true,
        date_range: dateRange,
        planets_checked: [...targetPlanets],
        war_events: warEvents,
        total_wars: warEvents.length,
        epistemics: { surgical: true, source: 'ephemeris_computed' },
      })
    },
  )
}
