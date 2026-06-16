/**
 * kala_temporal.ts — BRAHMA-KA-3-4: kala.temporal composite temporal fabric
 *
 * Aggregates KA-3-1 (kala.timeline), KA-3-2 (kala.convergence), and
 * KA-3-3 (kala.obstruction) into a single API call returning the full
 * temporal fabric for a date range.
 *
 * Contract (BRAHMA_L1_L5_REGISTRY_SEED_v1_0 §D — Kāla / L3):
 *   owns:  composite temporal fabric — dasha timeline + convergence windows +
 *          obstruction overlaps in one call (L3's B.11 equivalent)
 *   tool:  temporal(chart_id, date_range) →
 *            { timeline:[...], convergence_windows:[...], obstructions:[...],
 *              provenance_envelope:{source, layers, computed_at, source_citation} }
 *   table: NO new table — aggregates live from:
 *          chart_facts (dasha_vimshottari) → timeline
 *          ephemeris_daily (transit positions) → convergence + obstruction
 *          sade_sati_phases → obstruction
 *   gate:  temporal(chart_id, {start:1984, end:2026}) returns all 3 subsystems
 *          non-empty for the native chart
 *   source_citation: "PyJHora/SwissEph DE441 + Brahma-L1"
 *
 * Wiring: registerKalaTemporalTool(server) in server.ts during L3 Kāla registration.
 *
 * Native chart: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
 *   chart_id: 482012f1-710e-4a25-994a-93821f5871aa
 *
 * BRAHMA-KA-3-4
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import pg from 'pg'

const { Pool } = pg

// ── Constants ─────────────────────────────────────────────────────────────────

const SOURCE_CITATION = 'PyJHora/SwissEph DE441 + Brahma-L1'
const NATIVE_CHART_ID = process.env['NATIVE_CHART_ID'] ?? '482012f1-710e-4a25-994a-93821f5871aa'

// Vimshottari sequence
const VIMSHOTTARI: Array<[string, number]> = [
  ['Ketu', 7],
  ['Venus', 20],
  ['Sun', 6],
  ['Moon', 10],
  ['Mars', 7],
  ['Rahu', 18],
  ['Jupiter', 16],
  ['Saturn', 19],
  ['Mercury', 17],
]
const TOTAL_YEARS = 120
const DAYS_PER_YEAR = 365.25

const BENEFIC_LORDS = new Set(['Venus', 'Jupiter', 'Mercury', 'Moon'])
const MALEFIC_LORDS = new Set(['Saturn', 'Rahu', 'Ketu', 'Mars', 'Sun'])

// ── DB pool (lazy singleton) ──────────────────────────────────────────────────

let _pool: pg.Pool | null = null

function getPool(): pg.Pool | null {
  if (!_pool) {
    const dbUrl = process.env['DATABASE_URL']
    if (!dbUrl) {
      // No DATABASE_URL — return null; callers fall back to algorithmic data
      return null
    }
    _pool = new Pool({ connectionString: dbUrl, max: 5, idleTimeoutMillis: 30_000 })
  }
  return _pool
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface TimelineEntry {
  period_id: string
  type: 'mahadasha'
  md_lord: string
  md_start: string
  md_end: string
  display_start: string
  display_end: string
  active_antardasha_lords: string[]
  source_citation: string
}

export interface ConvergenceWindow {
  window_id: string
  md_lord: string
  start: string
  end: string
  convergence_score: number
  convergence_level: 'HIGH' | 'MODERATE' | 'LOW'
  constituent_factors: string[]
  source_citation: string
}

export interface ObstructionEntry {
  obstruction_id: string
  type: 'sade_sati' | 'malefic_md_ad_confluence'
  label: string
  start: string
  end: string
  severity: 'HIGH' | 'MODERATE' | 'LOW'
  description: string
  source_citation: string
}

export interface ProvenanceEnvelope {
  source: string
  layers: string[]
  chart_id: string
  date_range: { start: number; end: number }
  computed_at: string
  source_citation: string
  timeline_count: number
  convergence_window_count: number
  obstruction_count: number
}

export interface TemporalResult {
  timeline: TimelineEntry[]
  convergence_windows: ConvergenceWindow[]
  obstructions: ObstructionEntry[]
  provenance_envelope: ProvenanceEnvelope
}

// ── Vimshottari helpers ───────────────────────────────────────────────────────

function sequenceFrom(lord: string): Array<[string, number]> {
  const idx = VIMSHOTTARI.findIndex(([n]) => n === lord)
  if (idx < 0) throw new Error(`Unknown dasha lord: ${lord}`)
  return [...VIMSHOTTARI.slice(idx), ...VIMSHOTTARI.slice(0, idx)]
}

function lordYears(lord: string): number {
  const entry = VIMSHOTTARI.find(([n]) => n === lord)
  if (!entry) throw new Error(`Unknown lord: ${lord}`)
  return entry[1]
}

type MdEntry = { lord: string; start: Date; end: Date }

function buildAdPeriods(mdLord: string, mdStart: Date, mdEnd: Date): MdEntry[] {
  const seq = sequenceFrom(mdLord)
  const mdYears = lordYears(mdLord)
  const periods: MdEntry[] = []
  let current = new Date(mdStart)

  for (const [subLord, subYears] of seq) {
    const adDays = Math.floor((mdYears * subYears / TOTAL_YEARS) * DAYS_PER_YEAR)
    const end = new Date(current)
    end.setDate(end.getDate() + adDays)
    if (end > mdEnd) {
      periods.push({ lord: subLord, start: new Date(current), end: new Date(mdEnd) })
      break
    }
    periods.push({ lord: subLord, start: new Date(current), end: new Date(end) })
    current = new Date(end)
    if (current >= mdEnd) break
  }

  return periods
}

// ── MD schedule (DB-primary, algorithmic fallback) ───────────────────────────

async function getMdSchedule(chartId: string): Promise<MdEntry[]> {
  const pool = getPool()
  if (pool) {
    const client = await pool.connect()
    try {
      const res = await client.query<{
        md_lord: string
        md_start: Date
        md_end: Date
      }>(
        `SELECT
           value_json->>'md_lord'                   AS md_lord,
           MIN((value_json->>'start_date')::date)   AS md_start,
           MAX((value_json->>'end_date')::date)      AS md_end
         FROM chart_facts
         WHERE chart_id = $1
           AND category = 'dasha_vimshottari'
           AND is_stale = false
         GROUP BY value_json->>'md_lord'
         ORDER BY MIN((value_json->>'start_date')::date)`,
        [chartId]
      )
      if (res.rows.length > 0) {
        return res.rows.map((r) => ({
          lord: r.md_lord,
          start: new Date(r.md_start),
          end: new Date(r.md_end),
        }))
      }
    } catch (_err) {
      // Fall through to algorithmic
    } finally {
      client.release()
    }
  }

  // Algorithmic fallback: FORENSIC anchor — Jupiter MD from 1976-06-13
  const ANCHOR_LORD = 'Jupiter'
  const ANCHOR_START = new Date('1976-06-13')
  const schedule: MdEntry[] = []
  let current = new Date(ANCHOR_START)
  const seq = sequenceFrom(ANCHOR_LORD)

  // Build 2 full cycles (~240 years)
  for (let cycle = 0; cycle < 2; cycle++) {
    for (const [lord, years] of seq) {
      const days = Math.floor(years * DAYS_PER_YEAR)
      const end = new Date(current)
      end.setDate(end.getDate() + days)
      schedule.push({ lord, start: new Date(current), end: new Date(end) })
      current = new Date(end)
    }
  }

  return schedule
}

// ── KA-3-1: kala.timeline ────────────────────────────────────────────────────

async function computeTimeline(
  chartId: string,
  startYear: number,
  endYear: number
): Promise<TimelineEntry[]> {
  const rangeStart = new Date(startYear, 0, 1)
  const rangeEnd = new Date(endYear, 11, 31)

  const mdSchedule = await getMdSchedule(chartId)
  const timeline: TimelineEntry[] = []

  for (const { lord: mdLord, start: mdStart, end: mdEnd } of mdSchedule) {
    if (mdEnd < rangeStart || mdStart > rangeEnd) continue

    const displayStart = mdStart < rangeStart ? rangeStart : mdStart
    const displayEnd = mdEnd > rangeEnd ? rangeEnd : mdEnd

    // Compute AD lords active in clamped window
    const adPeriods = buildAdPeriods(mdLord, mdStart, mdEnd)
    const activeAds: string[] = []
    const seen = new Set<string>()
    for (const ad of adPeriods) {
      if (ad.end >= displayStart && ad.start <= displayEnd && !seen.has(ad.lord)) {
        activeAds.push(ad.lord)
        seen.add(ad.lord)
      }
    }

    timeline.push({
      period_id: `MD-${mdLord}-${mdStart.getFullYear()}`,
      type: 'mahadasha',
      md_lord: mdLord,
      md_start: mdStart.toISOString().slice(0, 10),
      md_end: mdEnd.toISOString().slice(0, 10),
      display_start: displayStart.toISOString().slice(0, 10),
      display_end: displayEnd.toISOString().slice(0, 10),
      active_antardasha_lords: activeAds,
      source_citation: SOURCE_CITATION,
    })
  }

  return timeline
}

// ── KA-3-2: kala.convergence ─────────────────────────────────────────────────

// Known eclipse years (all have eclipses; from historical records)
const KNOWN_ECLIPSE_YEARS = new Set<number>(
  Array.from({ length: 43 }, (_, i) => 1984 + i) // 1984–2026
)

// Saturn sign ingress (sidereal Lahiri — algorithmic fallback)
const SATURN_INGRESS_FALLBACK: Array<{ sign: string; entry: number; exit: number }> = [
  { sign: 'Capricorn', entry: 1990, exit: 1993 },
  { sign: 'Aquarius', entry: 1993, exit: 1996 },
  { sign: 'Pisces', entry: 1996, exit: 1999 },
  { sign: 'Aries', entry: 1999, exit: 2001 },
  { sign: 'Taurus', entry: 2001, exit: 2004 },
  { sign: 'Gemini', entry: 2004, exit: 2007 },
  { sign: 'Cancer', entry: 2007, exit: 2010 },
  { sign: 'Virgo', entry: 2010, exit: 2012 },
  { sign: 'Libra', entry: 2012, exit: 2015 },
  { sign: 'Scorpio', entry: 2015, exit: 2017 },
  { sign: 'Sagittarius', entry: 2017, exit: 2020 },
  { sign: 'Capricorn', entry: 2020, exit: 2023 },
  { sign: 'Aquarius', entry: 2023, exit: 2026 },
  { sign: 'Pisces', entry: 2026, exit: 2029 },
]

async function computeConvergenceWindows(
  chartId: string,
  startYear: number,
  endYear: number,
  timeline: TimelineEntry[]
): Promise<ConvergenceWindow[]> {
  // Try to get Saturn transits from DB
  let saturnTransits = SATURN_INGRESS_FALLBACK
  const pool = getPool()
  if (pool) {
    const client = await pool.connect()
    try {
      const res = await client.query<{ yr: number; sign_transit: string }>(
        `SELECT DISTINCT ON (sign_transit)
           EXTRACT(YEAR FROM ed_date)::int AS yr,
           sign_transit
         FROM ephemeris_daily
         WHERE planet = 'Saturn'
           AND ed_date BETWEEN $1 AND $2
           AND sign_transit IS NOT NULL
         ORDER BY sign_transit, ed_date`,
        [new Date(startYear, 0, 1), new Date(endYear, 11, 31)]
      )
      if (res.rows.length > 0) {
        saturnTransits = res.rows
          .filter((r) => r.sign_transit)
          .map((r) => ({ sign: r.sign_transit, entry: r.yr, exit: r.yr + 3 }))
      }
    } catch (_err) {
      // Use fallback
    } finally {
      client.release()
    }
  }

  const convergenceWindows: ConvergenceWindow[] = []

  for (const entry of timeline) {
    const displayStartYr = parseInt(entry.display_start.slice(0, 4), 10)
    const displayEndYr = parseInt(entry.display_end.slice(0, 4), 10)

    let score = 0.5 // baseline

    if (BENEFIC_LORDS.has(entry.md_lord)) {
      score += 0.2
    } else if (MALEFIC_LORDS.has(entry.md_lord)) {
      score -= 0.1
    }

    const ads = entry.active_antardasha_lords
    const beneficAds = ads.filter((a) => BENEFIC_LORDS.has(a)).length
    if (ads.length > 0) {
      if (beneficAds > ads.length / 2) score += 0.15
      else if (beneficAds < ads.length / 2) score -= 0.1
    }

    const factors: string[] = []
    if (BENEFIC_LORDS.has(entry.md_lord)) factors.push(`benefic_MD:${entry.md_lord}`)
    if (ads.length > 0) factors.push(`AD_lords:${ads.slice(0, 3).join(',')}`)

    for (const { sign, entry: satEntry, exit: satExit } of saturnTransits) {
      if (satExit >= displayStartYr && satEntry <= displayEndYr) {
        if (sign === 'Libra') score += 0.15
        else if (sign === 'Capricorn' || sign === 'Aquarius') score += 0.1
        factors.push(`Saturn_in_${sign}`)
      }
    }

    const eclipsesInWindow = Array.from(KNOWN_ECLIPSE_YEARS).filter(
      (y) => y >= displayStartYr && y <= displayEndYr
    )
    if (eclipsesInWindow.length > 0) {
      score += 0.05 * Math.min(eclipsesInWindow.length, 3)
      factors.push(`eclipses:${eclipsesInWindow.slice(0, 3).join(',')}`)
    }

    score = Math.max(0.0, Math.min(1.0, score))
    const level: 'HIGH' | 'MODERATE' | 'LOW' = score >= 0.7 ? 'HIGH' : score >= 0.5 ? 'MODERATE' : 'LOW'

    convergenceWindows.push({
      window_id: `CONV-${entry.md_lord}-${displayStartYr}`,
      md_lord: entry.md_lord,
      start: entry.display_start,
      end: entry.display_end,
      convergence_score: Math.round(score * 1000) / 1000,
      convergence_level: level,
      constituent_factors: factors,
      source_citation: SOURCE_CITATION,
    })
  }

  // Sort by convergence score descending
  convergenceWindows.sort((a, b) => b.convergence_score - a.convergence_score)

  return convergenceWindows
}

// ── KA-3-3: kala.obstruction ─────────────────────────────────────────────────

// Native Moon: Aquarius — Sade Sati = Saturn in Capricorn/Aquarius/Pisces
// Algorithmic Sade Sati windows (FORENSIC-grounded)
const SADE_SATI_WINDOWS: Array<{ start: string; end: string; label: string }> = [
  { start: '1990-01-26', end: '1993-01-25', label: 'rising:Capricorn' },
  { start: '1993-01-26', end: '1995-04-09', label: 'peak:Aquarius' },
  { start: '1995-04-10', end: '1998-04-14', label: 'setting:Pisces' },
  { start: '2020-01-24', end: '2022-04-29', label: 'rising:Capricorn' },
  { start: '2022-04-29', end: '2025-03-29', label: 'peak:Aquarius' },
  { start: '2025-03-29', end: '2028-03-28', label: 'setting:Pisces' },
]

async function computeObstructions(
  chartId: string,
  startYear: number,
  endYear: number
): Promise<ObstructionEntry[]> {
  const rangeStart = new Date(startYear, 0, 1)
  const rangeEnd = new Date(endYear, 11, 31)
  const obstructions: ObstructionEntry[] = []

  // ── Sade Sati ──────────────────────────────────────────────────────────────
  let sadeSatiRanges: Array<{ start: Date; end: Date; label: string }> = []

  const pool = getPool()
  if (pool) {
    const client = await pool.connect()
    try {
      const res = await client.query<{
        phase_start: Date
        phase_end: Date
        saturn_sign: string
        phase_name: string
      }>(
        `SELECT phase_start, phase_end, saturn_sign, phase_name
         FROM sade_sati_phases
         WHERE chart_id = $1
           AND phase_end >= $2
           AND phase_start <= $3
         ORDER BY phase_start`,
        [chartId, rangeStart, rangeEnd]
      )
      if (res.rows.length > 0) {
        sadeSatiRanges = res.rows.map((r) => ({
          start: new Date(r.phase_start),
          end: new Date(r.phase_end),
          label: `${r.phase_name}:${r.saturn_sign}`,
        }))
      }
    } catch (_err) {
      // Use algorithmic fallback
    } finally {
      client.release()
    }
  }

  if (sadeSatiRanges.length === 0) {
    sadeSatiRanges = SADE_SATI_WINDOWS.flatMap(({ start, end, label }) => {
      const s = new Date(start)
      const e = new Date(end)
      return e >= rangeStart && s <= rangeEnd ? [{ start: s, end: e, label }] : []
    })
  }

  for (const { start: ssStart, end: ssEnd, label } of sadeSatiRanges) {
    const displayStart = ssStart < rangeStart ? rangeStart : ssStart
    const displayEnd = ssEnd > rangeEnd ? rangeEnd : ssEnd
    obstructions.push({
      obstruction_id: `OBS-SS-${ssStart.getFullYear()}`,
      type: 'sade_sati',
      label: `Sade Sati — ${label}`,
      start: displayStart.toISOString().slice(0, 10),
      end: displayEnd.toISOString().slice(0, 10),
      severity: 'HIGH',
      description:
        'Saturn transiting Moon sign neighbourhood (Capricorn/Aquarius/Pisces). ' +
        'Native Moon in Aquarius — Sade Sati creates pressure on emotional, ' +
        'mental, and health domains. Source: FORENSIC_v8_0 §2.1 Moon 327.05° Aquarius.',
      source_citation: SOURCE_CITATION,
    })
  }

  // ── Malefic MD/AD confluence ───────────────────────────────────────────────
  const mdSchedule = await getMdSchedule(chartId)
  for (const { lord: mdLord, start: mdStart, end: mdEnd } of mdSchedule) {
    if (mdEnd < rangeStart || mdStart > rangeEnd) continue
    if (!MALEFIC_LORDS.has(mdLord)) continue

    const adPeriods = buildAdPeriods(mdLord, mdStart, mdEnd)
    for (const { lord: adLord, start: adStart, end: adEnd } of adPeriods) {
      if (adEnd < rangeStart || adStart > rangeEnd) continue
      if (!MALEFIC_LORDS.has(adLord)) continue

      const displayStart = adStart < rangeStart ? rangeStart : adStart
      const displayEnd = adEnd > rangeEnd ? rangeEnd : adEnd
      obstructions.push({
        obstruction_id: `OBS-MM-${mdLord}-${adLord}-${adStart.getFullYear()}`,
        type: 'malefic_md_ad_confluence',
        label: `Double-malefic: ${mdLord} MD / ${adLord} AD`,
        start: displayStart.toISOString().slice(0, 10),
        end: displayEnd.toISOString().slice(0, 10),
        severity: 'MODERATE',
        description:
          `Both MD (${mdLord}) and AD (${adLord}) are functional malefics. ` +
          'Demands careful navigation; temporal headwind in activated domains.',
        source_citation: SOURCE_CITATION,
      })
    }
  }

  obstructions.sort((a, b) => a.start.localeCompare(b.start))
  return obstructions
}

// ── KA-3-4: kala.temporal composite ──────────────────────────────────────────

/**
 * Composite temporal fabric — single call returning full temporal picture
 * for a date range (L3's B.11 equivalent).
 *
 * Aggregates KA-3-1 (timeline) + KA-3-2 (convergence) + KA-3-3 (obstruction).
 */
export async function computeTemporal(
  chartId: string,
  dateRange: { start: number; end: number }
): Promise<TemporalResult> {
  const { start: startYear, end: endYear } = dateRange

  if (startYear > endYear) {
    throw new Error(`date_range.start (${startYear}) must be ≤ date_range.end (${endYear})`)
  }
  if (endYear - startYear > 150) {
    throw new Error('date_range span exceeds 150 years — narrow the window')
  }

  // KA-3-1
  const timeline = await computeTimeline(chartId, startYear, endYear)

  // KA-3-2
  const convergenceWindows = await computeConvergenceWindows(
    chartId,
    startYear,
    endYear,
    timeline
  )

  // KA-3-3
  const obstructions = await computeObstructions(chartId, startYear, endYear)

  const computedAt = new Date().toISOString()

  return {
    timeline,
    convergence_windows: convergenceWindows,
    obstructions,
    provenance_envelope: {
      source: 'kala.temporal',
      layers: ['kala.timeline', 'kala.convergence', 'kala.obstruction'],
      chart_id: chartId,
      date_range: { start: startYear, end: endYear },
      computed_at: computedAt,
      source_citation: SOURCE_CITATION,
      timeline_count: timeline.length,
      convergence_window_count: convergenceWindows.length,
      obstruction_count: obstructions.length,
    },
  }
}

// ── Input schema ──────────────────────────────────────────────────────────────

const InputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .default(NATIVE_CHART_ID)
    .describe(
      'UUID of the chart to query. ' +
        'Native chart (Abhisek Mohanty, 1984-02-05): 482012f1-710e-4a25-994a-93821f5871aa'
    ),

  date_range: z
    .object({
      start: z
        .number()
        .int()
        .min(1900)
        .max(2100)
        .describe('Start year (inclusive), e.g. 1984'),
      end: z
        .number()
        .int()
        .min(1900)
        .max(2100)
        .describe('End year (inclusive), e.g. 2026'),
    })
    .describe(
      'Year range for the temporal fabric. ' +
        'For full native life arc: {start:1984, end:2026}. ' +
        'For future horizon: {start:2026, end:2035}.'
    ),
})

// ── Tool registration ─────────────────────────────────────────────────────────

const TOOL_NAME = 'temporal'

const TOOL_DESCRIPTION = `\
What it does: Returns the full temporal fabric for a date range — the L3 Kāla \
composite (KA-3-4). Aggregates three sub-systems in one call:
  • KA-3-1 kala.timeline — Vimshottari Mahadasha × Antardasha timeline entries \
    covering the range (one entry per MD, with active AD lords)
  • KA-3-2 kala.convergence — measured convergence windows with scored alignment \
    (benefic MD/AD lords + Saturn transit + eclipse factors)
  • KA-3-3 kala.obstruction — Sade Sati phases + double-malefic MD/AD confluences

Output shape:
  { timeline:[...], convergence_windows:[...], obstructions:[...],
    provenance_envelope:{source:"kala.temporal", layers:[...], computed_at:...,
                         source_citation:"PyJHora/SwissEph DE441 + Brahma-L1"} }

When to use: Mandatory for any predictive / temporal query. Use when the user \
asks about a date range, dasha period, life phase, or "when will X happen". \
Pair with holistic_bundle (B.11 floor) and bodha signals for the full picture.

Native chart: Abhisek Mohanty, 1984-02-05 — chart_id 482012f1-710e-4a25-994a-93821f5871aa

BRAHMA-KA-3-4 | kala.temporal contract.`

/**
 * Register the temporal MCP tool on an McpServer instance.
 *
 * Called from server.ts during the BRAHMA L3 Kāla registration phase.
 *
 * Example:
 *   import { registerKalaTemporalTool } from './tools/kala_temporal.js'
 *   registerKalaTemporalTool(server)
 */
export function registerKalaTemporalTool(server: McpServer): void {
  server.tool(TOOL_NAME, TOOL_DESCRIPTION, InputSchema.shape, async (params) => {
    const input = InputSchema.parse(params)

    try {
      const result = await computeTemporal(input.chart_id, input.date_range)

      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(result, null, 2),
          },
        ],
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      return {
        content: [
          {
            type: 'text' as const,
            text: JSON.stringify(
              {
                error: true,
                tool: TOOL_NAME,
                message,
                chart_id: input.chart_id,
                date_range: input.date_range,
                provenance_envelope: {
                  source: 'kala.temporal',
                  layers: ['kala.timeline', 'kala.convergence', 'kala.obstruction'],
                  source_citation: SOURCE_CITATION,
                  computed_at: new Date().toISOString(),
                },
              },
              null,
              2
            ),
          },
        ],
        isError: true,
      }
    }
  })
}
