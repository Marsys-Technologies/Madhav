/**
 * MARSYS-JIS Retrieval tool — query_planet_war (UDA-1-S6)
 *
 * Portal port of the MCP query_planet_war surgical primitive.
 * Detects Graha Yuddha (planetary war) events within a date range.
 *
 * Classical rule: two true planets (Sun and Moon excluded) are within 1° of
 * each other in ecliptic longitude on the same day.
 *
 * Algorithm:
 *   1. Fetch ephemeris for the requested planets from ephemeris_daily.
 *   2. For each date, compare each pair of planet longitudes.
 *      If |long1 - long2| ≤ 1.0° (with 360° wrap handling) → war event.
 *   3. Winner: planet with higher absolute declination wins (classical rule).
 *      If declination not available, the faster-moving planet (higher speed) wins.
 *   4. Append classical_interpretation based on the winning planet.
 *
 * 360° wrap: angular distance = min(|a-b|, 360 - |a-b|).
 *
 * Source: platform-mcp/src/tools/query_planet_war.ts (TR-P8-S1)
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_planet_war'
const TOOL_VERSION = '1.0.0'

// ── Constants ─────────────────────────────────────────────────────────────────

/** Maximum longitude separation (degrees) for Graha Yuddha. */
const WAR_ORB = 1.0

/** Traditional planets eligible for Graha Yuddha (no Sun/Moon/nodes). */
const DEFAULT_WAR_PLANETS = ['mars', 'mercury', 'jupiter', 'venus', 'saturn'] as const
type WarPlanet = typeof DEFAULT_WAR_PLANETS[number]

// ── Input interface ───────────────────────────────────────────────────────────

export interface QueryPlanetWarInput {
  /** Date range to scan for war events. Defaults to the current calendar year. */
  date_range?: {
    from: string  // ISO YYYY-MM-DD
    to: string    // ISO YYYY-MM-DD
  }
  /**
   * Planets to include in war detection. Default: all five.
   * Sun and Moon are excluded by the classical rule and cannot be specified.
   */
  planets?: Array<'Mars' | 'Mercury' | 'Jupiter' | 'Venus' | 'Saturn'>
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface WarEvent {
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
  longitude_deg: string | number
  latitude_deg: string | number | null
  speed_deg_per_day: string | number
}

interface PlanetEntry {
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
function angularSep(a: number, b: number): number {
  const diff = Math.abs(a - b)
  return diff > 180 ? 360 - diff : diff
}

/**
 * Build classical interpretation string.
 */
function buildWarInterpretation(winner: string, loser: string): string {
  const w = winner.toLowerCase()
  const templates: Record<string, string> = {
    mars: `Mars subjugates ${loser} — increased aggression, disruption`,
    venus: `Venus prevails over ${loser} — artistic/material matters dominant`,
    saturn: `Saturn crushes ${loser} — delays, karma, obstruction`,
    mercury: `Mercury overcomes ${loser} — intellect prevails`,
    jupiter: `Jupiter triumphs over ${loser} — wisdom, dharma, expansion`,
  }
  return templates[w] ?? `${winner} defeats ${loser} in Graha Yuddha`
}

/**
 * Determine the winner between two planets.
 *
 * Classical rule: higher absolute declination wins.
 * Tiebreaker: higher daily speed (faster planet wins).
 * If neither available: alphabetical (deterministic fallback).
 */
function determineWinner(
  p1: PlanetEntry,
  p2: PlanetEntry,
): { winner: string; loser: string } {
  if (p1.declination !== undefined && p2.declination !== undefined) {
    const dec1 = Math.abs(p1.declination)
    const dec2 = Math.abs(p2.declination)
    if (dec1 !== dec2) {
      return dec1 > dec2
        ? { winner: p1.planet, loser: p2.planet }
        : { winner: p2.planet, loser: p1.planet }
    }
  }

  if (p1.speed !== undefined && p2.speed !== undefined) {
    const spd1 = Math.abs(p1.speed)
    const spd2 = Math.abs(p2.speed)
    if (spd1 !== spd2) {
      return spd1 > spd2
        ? { winner: p1.planet, loser: p2.planet }
        : { winner: p2.planet, loser: p1.planet }
    }
  }

  return p1.planet < p2.planet
    ? { winner: p1.planet, loser: p2.planet }
    : { winner: p2.planet, loser: p1.planet }
}

/**
 * Group ephemeris rows by date → planet → PlanetEntry.
 */
function groupEphemerisByDate(
  rows: EphemerisRow[],
): Map<string, Map<string, PlanetEntry>> {
  const byDate = new Map<string, Map<string, PlanetEntry>>()

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
    byDate.get(date)!.set(planet, {
      planet: row.planet,
      longitude: lon,
      declination: decFinite,
      speed: spdFinite,
    })
  }

  return byDate
}

// ── Core computation ──────────────────────────────────────────────────────────

/**
 * Detect Graha Yuddha war events from the grouped ephemeris data.
 *
 * For each date, compare all unique planet pairs.
 * If angular separation ≤ WAR_ORB → record a war event.
 * Consecutive days of the same pair are collapsed (gap < 7 days).
 */
function detectPlanetWars(
  byDate: Map<string, Map<string, PlanetEntry>>,
  targetPlanets: readonly string[],
): WarEvent[] {
  const events: WarEvent[] = []
  const sortedDates = Array.from(byDate.keys()).sort()
  const lastWarDate = new Map<string, string>()

  for (const date of sortedDates) {
    const planets = byDate.get(date)!
    const planetKeys = targetPlanets.map(p => p.toLowerCase())

    const available: PlanetEntry[] = []
    for (const key of planetKeys) {
      const row = planets.get(key)
      if (row) available.push(row)
    }

    for (let i = 0; i < available.length; i++) {
      for (let j = i + 1; j < available.length; j++) {
        const p1 = available[i]!
        const p2 = available[j]!

        const sep = angularSep(p1.longitude, p2.longitude)
        if (sep > WAR_ORB) continue

        const pairKey = [p1.planet.toLowerCase(), p2.planet.toLowerCase()].sort().join('::')
        const prev = lastWarDate.get(pairKey)
        if (prev !== undefined) {
          const gap = (new Date(date).getTime() - new Date(prev).getTime()) / 86400000
          if (gap < 7) continue
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

// ── Retrieve function ─────────────────────────────────────────────────────────

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  const input = (params ?? {}) as unknown as QueryPlanetWarInput

  const dateRange = input.date_range ?? currentYearRange()

  // Normalize input planets to lowercase; fall back to all five
  let targetPlanets: readonly string[] = DEFAULT_WAR_PLANETS
  if (input.planets && input.planets.length > 0) {
    targetPlanets = input.planets.map(p => p.toLowerCase()) as WarPlanet[]
  }

  const storage = getStorageClient()

  // Fetch ephemeris for the requested planets
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
    [dateRange.from, dateRange.to, [...targetPlanets]],
  )

  const byDate = groupEphemerisByDate(ephResult.rows)
  const warEvents = detectPlanetWars(byDate, targetPlanets)

  const payload = {
    ok: true,
    date_range: dateRange,
    planets_checked: [...targetPlanets],
    war_events: warEvents,
    total_wars: warEvents.length,
    epistemics: { surgical: true, source: 'ephemeris_computed' },
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
    status: warEvents.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: warEvents.length,
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
  input: QueryPlanetWarInput,
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
    'Detects Graha Yuddha (planetary war) — two true planets within 1° of each other ' +
    'in ecliptic longitude. Sun and Moon excluded (classical rule). Returns each war event ' +
    'with date, the two planets, their shared longitude, winner (higher declination wins; ' +
    'speed as tiebreaker), and classical interpretation. ' +
    'Use for "Is there a planetary war in 2026?" or "When do Mars and Venus fight?" ' +
    'Prefer holistic_bundle when synthesis of war significance in the full chart is needed.',
  retrieve,
}
