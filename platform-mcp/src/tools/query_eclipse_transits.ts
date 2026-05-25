/**
 * query_eclipse_transits.ts — MCP Tier 3 surgical primitive: eclipse detection.
 *
 * What it does: Scans a date range for solar and lunar eclipses by computing
 * them from ephemeris data. Eclipse detection algorithm:
 *   - Solar eclipse: Sun–Moon angular separation ≤ 1° AND Moon within 12° of
 *     a lunar node (Rahu or Ketu).
 *   - Lunar eclipse: Sun–Moon angular separation within 1° of 180° (opposition)
 *     AND Moon within 12° of a lunar node.
 *
 * Eclipse data source: ephemeris_daily via query_ephemeris. The sidecar
 * eclipses.py endpoint is a stub (not_implemented); this tool does not call it.
 *
 * Optionally flags eclipses conjunct the native's natal Sun, Moon, or ASC
 * within 5° when natal_sensitive_points=true.
 *
 * When to prefer: Use for "Find all eclipses in 2026", "Solar eclipses hitting
 * my natal Sun", or "Upcoming lunar eclipses." Prefer query_transit_event for
 * standard transit lookups. Prefer holistic_bundle when synthesised context
 * is needed alongside eclipse timing.
 *
 * Input shape hints:
 *   date_range   — optional {from, to} ISO dates. Default: current calendar year.
 *   eclipse_type — optional "solar"|"lunar"|"all". Default: "all".
 *   natal_sensitive_points — optional bool. Default: false. When true, flags
 *     eclipses within 5° of native natal Sun, Moon, or ASC.
 *   tier — optional string (passed through for audit).
 *
 * Output shape preview:
 *   {ok, date_range, eclipse_type_filter, eclipses: [{date, eclipse_type, degree,
 *    sign, conjunct_natal_point, impact_assessment}], total_eclipses}
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

// ── Description ───────────────────────────────────────────────────────────────

export const QUERY_ECLIPSE_TRANSITS_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Detects solar and lunar eclipses within a date range by scanning ' +
    'ephemeris positions. Solar eclipse: Sun–Moon separation ≤ 1° and Moon within 12° ' +
    'of Rahu/Ketu. Lunar eclipse: Sun–Moon opposition within 1° and Moon within 12° of ' +
    'a node. Returns eclipse date, type, degree, sign, and optional natal-point flags.',
  whenToPrefer:
    'Use for "Find eclipses in 2026", "Upcoming solar eclipses near natal Sun", or ' +
    '"Lunar eclipses in next 2 years." Prefer query_transit_event for standard transits. ' +
    'Prefer holistic_bundle when synthesised eclipse interpretation in chart context is needed.',
})

// ── Zod schema ────────────────────────────────────────────────────────────────

const QueryEclipseTransitsInputSchema = z.object({
  date_range: z.object({
    from: z.string().describe('ISO start date (YYYY-MM-DD).'),
    to: z.string().describe('ISO end date (YYYY-MM-DD).'),
  }).optional().describe(
    'Date range to scan for eclipses. Defaults to the current calendar year.'
  ),
  eclipse_type: z.enum(['solar', 'lunar', 'all']).optional().default('all').describe(
    'Filter by eclipse type: "solar", "lunar", or "all". Default: "all".'
  ),
  natal_sensitive_points: z.boolean().optional().default(false).describe(
    'When true, flag eclipses within 5° of the native\'s natal Sun, Moon, or ASC. Default: false.'
  ),
  tier: z.string().optional().describe('Audience tier (passed through for audit).'),
})

type QueryEclipseTransitsInput = z.infer<typeof QueryEclipseTransitsInputSchema>

// ── Types ─────────────────────────────────────────────────────────────────────

export interface EclipseEvent {
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
 * Minimum angular distance between two ecliptic longitudes (0–360).
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
 * Extract planet positions per date from ephemeris data.
 * Returns a Map keyed by date, each holding a map of planet → EphemerisRow.
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
    byDate.get(date)!.set(planet.toLowerCase(), { date, planet, longitude, declination, speed })
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

// ── Core detection ────────────────────────────────────────────────────────────

/**
 * Detect eclipses from ephemeris data.
 *
 * For each date where we have Sun, Moon, Rahu (or Ketu) positions:
 *   - Solar: Moon–Sun separation ≤ SOLAR_ECLIPSE_SYNODIC_ORB
 *            AND Moon–node distance ≤ NODE_ORB.
 *   - Lunar: Moon–Sun opposition ≤ LUNAR_ECLIPSE_OPPOSITION_ORB
 *            AND Moon–node distance ≤ NODE_ORB.
 *
 * Consecutive eclipse days are collapsed into one event (keep first day).
 */
export function detectEclipses(
  byDate: Map<string, Map<string, EphemerisRow>>,
  typeFilter: 'solar' | 'lunar' | 'all',
  flagNatal: boolean,
): EclipseEvent[] {
  const events: EclipseEvent[] = []
  const seenDates = new Set<string>()
  const sortedDates = Array.from(byDate.keys()).sort()

  // Track previous eclipse date to collapse multi-day eclipse windows
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

    // Node distance: use whichever node is available; pick minimum distance
    let nodeDistance = Infinity
    if (rahu) nodeDistance = Math.min(nodeDistance, angularSep(moonLon, rahu.longitude))
    if (ketu) nodeDistance = Math.min(nodeDistance, angularSep(moonLon, ketu.longitude))
    if (nodeDistance === Infinity) continue  // no node data → skip

    const sunMoonSep = angularSep(sunLon, moonLon)
    const sunMoonOpp = angularSep(sunMoonSep, 180)  // distance from exact opposition

    let detectedType: 'solar' | 'lunar' | null = null

    if (sunMoonSep <= SOLAR_ECLIPSE_SYNODIC_ORB && nodeDistance <= NODE_ORB) {
      detectedType = 'solar'
    } else if (sunMoonOpp <= LUNAR_ECLIPSE_OPPOSITION_ORB && nodeDistance <= NODE_ORB) {
      detectedType = 'lunar'
    }

    if (!detectedType) continue
    if (typeFilter !== 'all' && typeFilter !== detectedType) continue

    // Collapse: skip if within 2 days of previous eclipse of same type
    if (lastEclipseDate !== null) {
      const gap = (new Date(date).getTime() - new Date(lastEclipseDate).getTime()) / 86400000
      if (gap < 25) continue  // same eclipse window — skip
    }

    if (seenDates.has(date)) continue
    seenDates.add(date)
    lastEclipseDate = date

    const eclipseLon = detectedType === 'solar' ? moonLon : moonLon
    const sign = signFromLongitude(eclipseLon)
    const degree = degreeInSign(eclipseLon)
    const conjunctPoint = flagNatal ? findNatalConjunction(eclipseLon) : null
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

// ── MCP tool registration ─────────────────────────────────────────────────────

export function registerQueryEclipseTransits(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'query_eclipse_transits',
    QUERY_ECLIPSE_TRANSITS_DESCRIPTION,
    QueryEclipseTransitsInputSchema.shape,
    async (args: QueryEclipseTransitsInput) => {
      const principal = getPrincipal()
      const dateRange = args.date_range ?? currentYearRange()
      const typeFilter = args.eclipse_type ?? 'all'
      const flagNatal = args.natal_sensitive_points ?? false

      // ── Fetch ephemeris (Sun, Moon, Rahu, Ketu) for the date range ─────────
      const ephResult = await callPlatformPrimitive(
        'query_ephemeris',
        {
          start_date: dateRange.from,
          end_date: dateRange.to,
          planets: ['Sun', 'Moon', 'Rahu', 'Ketu'],
          sample_step: '1d',
        },
        principal,
      )

      if (!ephResult.envelope.ok || ephResult.status >= 400) {
        return errorResult(ephResult.envelope)
      }

      const ephData = unwrapToolBundle(ephResult.envelope as unknown as Record<string, unknown>)
      const byDate = groupEphemerisByDate(ephData)

      // ── Detect eclipses ────────────────────────────────────────────────────
      const eclipses = detectEclipses(byDate, typeFilter, flagNatal)

      return okResult({
        ok: true,
        date_range: dateRange,
        eclipse_type_filter: typeFilter,
        eclipses,
        total_eclipses: eclipses.length,
        epistemics: { surgical: true, source: 'ephemeris_computed' },
      })
    },
  )
}
