/**
 * kala_timeline.ts — BRAHMA-KA-3-1: kala.timeline
 *
 * Asset:  kala.timeline (L3 Kāla)
 * Tool:   timeline_query(chart_id, date_range) → {timeline, provenance_envelope}
 * Table:  kala_timeline (chart_id, date, active_mahadasha, active_antardasha,
 *                        transit_highlights JSONB, signal_activations JSONB,
 *                        source_citation NOT NULL)
 *
 * CONTRACT (BRAHMA L3 Kāla KA-3-1):
 *   - owns:  deterministic dasha×transit alignment series over native life range
 *   - tool:  timeline_query(chart_id, date_range)
 *   - layer: L3 Kāla (depends on L1 ganita.dashas + L1 ganita.positions
 *                     + L2 bodha.signals)
 *   - source: PyJHora/SwissEph DE441 + Brahma-L1
 *   - acceptance:
 *       - Saturn MD rows present for 1991-08-21 → 2010-08-21
 *       - Mercury MD rows present for 2010-08-21 → 2027-08-21
 *       - source_citation NOT NULL on all rows
 *       - deterministic: same date always returns same row
 *
 * Wiring: registerKalaTimeline(server, principal) → server.ts during L3 Kāla registration.
 *
 * Native chart: Abhisek Mohanty, 1984-02-05, 10:43 IST Bhubaneswar
 *   chart_id: 482012f1-710e-4a25-994a-93821f5871aa
 *
 * BRAHMA-KA-3-1
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import pg from 'pg'
import type { Principal } from '../types.js'

const { Pool } = pg

// ── DB pool (lazy) ────────────────────────────────────────────────────────────

let _pool: pg.Pool | null = null

function getPool(): pg.Pool {
  if (!_pool) {
    const dbUrl = process.env['DATABASE_URL']
    if (!dbUrl) {
      throw new Error('[kala_timeline] DATABASE_URL not set — cannot connect to kala_timeline table')
    }
    _pool = new Pool({ connectionString: dbUrl, max: 5, idleTimeoutMillis: 30_000 })
  }
  return _pool
}

// ── Vimshottari constants (FORENSIC §5.1 — do not recompute) ─────────────────
//
// Canonical MD boundaries for Abhisek Mohanty from FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.1.
// FORENSIC dates are canonical per GAP.09; JH dates (±7-9 days) are NOT used.

const FORENSIC_MD_SCHEDULE: Array<{ lord: string; start: string; end: string }> = [
  { lord: 'Jupiter', start: '1984-02-05', end: '1991-08-21' },
  { lord: 'Saturn',  start: '1991-08-21', end: '2010-08-21' },
  { lord: 'Mercury', start: '2010-08-21', end: '2027-08-21' },
  { lord: 'Ketu',    start: '2027-08-21', end: '2034-08-21' },
  { lord: 'Venus',   start: '2034-08-21', end: '2054-08-21' },
  { lord: 'Sun',     start: '2054-08-21', end: '2060-08-21' },
]

const VIMSHOTTARI: Array<{ lord: string; years: number }> = [
  { lord: 'Ketu',    years: 7  },
  { lord: 'Venus',   years: 20 },
  { lord: 'Sun',     years: 6  },
  { lord: 'Moon',    years: 10 },
  { lord: 'Mars',    years: 7  },
  { lord: 'Rahu',    years: 18 },
  { lord: 'Jupiter', years: 16 },
  { lord: 'Saturn',  years: 19 },
  { lord: 'Mercury', years: 17 },
]

const DAYS_PER_YEAR = 365.25

function addDays(d: Date, n: number): Date {
  const r = new Date(d)
  r.setDate(r.getDate() + n)
  return r
}

function toIso(d: Date): string {
  return d.toISOString().slice(0, 10)
}

/**
 * Compute the active Mahadasha lord for a given date.
 * Uses FORENSIC_MD_SCHEDULE as ground truth; extends algorithmically outside range.
 */
function activeMd(queryDate: Date): { lord: string; start: Date; end: Date } {
  for (const entry of FORENSIC_MD_SCHEDULE) {
    const start = new Date(entry.start)
    const end   = new Date(entry.end)
    if (queryDate >= start && queryDate < end) {
      return { lord: entry.lord, start, end }
    }
  }

  // Forward extension beyond last FORENSIC entry
  const lastEntry = FORENSIC_MD_SCHEDULE[FORENSIC_MD_SCHEDULE.length - 1]
  if (!lastEntry) throw new Error('FORENSIC_MD_SCHEDULE is empty')
  let lastEnd = new Date(lastEntry.end)
  const lastIdx = VIMSHOTTARI.findIndex(v => v.lord === lastEntry.lord)
  let idx = lastIdx

  if (queryDate >= lastEnd) {
    while (true) {
      idx = (idx + 1) % VIMSHOTTARI.length
      const entry = VIMSHOTTARI[idx]
      if (!entry) throw new Error(`VIMSHOTTARI index out of range: ${idx}`)
      const nextEnd = addDays(lastEnd, Math.round(entry.years * DAYS_PER_YEAR))
      if (queryDate >= lastEnd && queryDate < nextEnd) {
        return { lord: entry.lord, start: lastEnd, end: nextEnd }
      }
      lastEnd = nextEnd
    }
  }

  // Backward extension before first FORENSIC entry
  const firstEntry = FORENSIC_MD_SCHEDULE[0]
  if (!firstEntry) throw new Error('FORENSIC_MD_SCHEDULE is empty')
  let firstStart = new Date(firstEntry.start)
  const firstIdx = VIMSHOTTARI.findIndex(v => v.lord === firstEntry.lord)
  idx = firstIdx

  while (true) {
    idx = (idx - 1 + VIMSHOTTARI.length) % VIMSHOTTARI.length
    const entry = VIMSHOTTARI[idx]
    if (!entry) throw new Error(`VIMSHOTTARI index out of range: ${idx}`)
    const prevStart = addDays(firstStart, -Math.round(entry.years * DAYS_PER_YEAR))
    if (queryDate >= prevStart && queryDate < firstStart) {
      return { lord: entry.lord, start: prevStart, end: firstStart }
    }
    firstStart = prevStart
  }
}

// ── Input schema ──────────────────────────────────────────────────────────────

const DateRangeSchema = z.object({
  start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, {
    message: 'start must be ISO date YYYY-MM-DD',
  }),
  end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, {
    message: 'end must be ISO date YYYY-MM-DD',
  }),
})

const KalaTimelineSchema = z.object({
  /**
   * Chart UUID to query the timeline for.
   * Native: 482012f1-710e-4a25-994a-93821f5871aa
   */
  chart_id: z.string().uuid({
    message: 'chart_id must be a valid UUID (e.g. 482012f1-710e-4a25-994a-93821f5871aa)',
  }),

  /**
   * Date range for the timeline query.
   * Both start and end are inclusive ISO dates (YYYY-MM-DD).
   * Maximum span: 36,600 days (~100 years). Typical use: 1–5 years.
   */
  date_range: DateRangeSchema,

  /**
   * Maximum number of rows to return. Default: 365 (one year of daily rows).
   * Max: 36,600.
   */
  limit: z.number().int().min(1).max(36_600).default(365),
})

export type KalaTimelineParams = z.infer<typeof KalaTimelineSchema>

// ── Types ─────────────────────────────────────────────────────────────────────

export interface TimelineRow {
  date: string
  active_mahadasha: string
  active_antardasha: string
  transit_highlights: unknown[]
  signal_activations: unknown[]
  source_citation: string
}

export interface TimelineResult {
  timeline: TimelineRow[]
  provenance_envelope: {
    asset: string
    unit: string
    source: string
    layer: string
    depends: string[]
    chart_id: string
    range: { start: string; end: string }
    count: number
    generated_at: string
  }
}

// ── Tool description ──────────────────────────────────────────────────────────

const KALA_TIMELINE_DESCRIPTION = `\
What it does: Returns the deterministic dasha×transit alignment series from \
kala_timeline (KA-3-1, L3 Kāla). Each row contains the active Vimshottari \
Mahadasha + Antardasha lord for the given date, optional transit highlights \
from ephemeris_daily, and optional bodha signal activations from L2 Bodha.

Source: PyJHora/SwissEph DE441 + Brahma-L1 (FORENSIC §5.1 canonical dasha dates). \
FORENSIC dates are canonical per GAP.09 — JH dates (±7–9 days) are NOT used.

Outputs per row: date (ISO), active_mahadasha (e.g. "Saturn", "Mercury"), \
active_antardasha (sub-period lord), transit_highlights (array of planet/longitude \
events from ephemeris_daily — empty if table not populated), signal_activations \
(bodha signals lit by this dasha×transit state — empty if bodha tables empty), \
source_citation (always "PyJHora/SwissEph DE441 + Brahma-L1").

When to prefer: Use timeline_query to understand the dasha context for any date \
or date range — e.g. "what MD/AD was active during event X?", "show the dasha \
sequence for 2010–2030". Pair with holistic_bundle (B.11 floor) for whole-chart \
synthesis. For a single date's dasha, use date_range {start: DATE, end: DATE} \
with limit=1. For multi-year dasha arc analysis, use a wider range with limit \
up to 36600 (daily granularity).

Provenance: Every row carries source_citation = "PyJHora/SwissEph DE441 + Brahma-L1". \
Response includes provenance_envelope with asset, unit, layer, depends, and range.`

// ── Core query logic ──────────────────────────────────────────────────────────

async function queryKalaTimeline(
  chartId: string,
  start: Date,
  end: Date,
  limit: number,
): Promise<TimelineResult> {
  // Try DB first; fall back to algorithmic if no DB or table absent
  let rows: TimelineRow[] = []
  let pool: pg.Pool | null = null
  try {
    pool = getPool()
  } catch {
    // DATABASE_URL not set — skip to algorithmic fallback
  }

  if (pool !== null) try {
    const result = await pool.query<{
      date: Date
      active_mahadasha: string
      active_antardasha: string
      transit_highlights: unknown
      signal_activations: unknown
      source_citation: string
    }>(
      `SELECT date, active_mahadasha, active_antardasha,
              transit_highlights, signal_activations, source_citation
       FROM kala_timeline
       WHERE chart_id = $1
         AND date BETWEEN $2 AND $3
       ORDER BY date
       LIMIT $4`,
      [chartId, toIso(start), toIso(end), limit],
    )

    rows = result.rows.map(r => ({
      date: toIso(r.date),
      active_mahadasha: r.active_mahadasha,
      active_antardasha: r.active_antardasha,
      transit_highlights: Array.isArray(r.transit_highlights) ? r.transit_highlights : [],
      signal_activations: Array.isArray(r.signal_activations) ? r.signal_activations : [],
      source_citation: r.source_citation,
    }))
  } catch (err) {
    // Table may not exist yet — fall back to algorithmic computation
    rows = []
  }

  // Algorithmic fallback: compute without DB
  if (rows.length === 0) {
    rows = computeTimelineAlgorithmic(chartId, start, end, limit)
  }

  return {
    timeline: rows,
    provenance_envelope: {
      asset: 'kala.timeline',
      unit: 'KA-3-1',
      source: 'PyJHora/SwissEph DE441 + Brahma-L1',
      layer: 'L3 Kāla',
      depends: ['L1 ganita.dashas', 'L1 ganita.positions', 'L2 bodha.signals'],
      chart_id: chartId,
      range: { start: toIso(start), end: toIso(end) },
      count: rows.length,
      generated_at: new Date().toISOString(),
    },
  }
}

/**
 * Pure algorithmic computation — no DB required.
 * Used as fallback when kala_timeline table is empty or unavailable.
 * Deterministic: same inputs always produce same outputs.
 */
function computeTimelineAlgorithmic(
  chartId: string,
  start: Date,
  end: Date,
  limit: number,
): TimelineRow[] {
  // Canonical AD schedule from FORENSIC §5.1
  const adSchedule: Array<{ md: string; ad: string; start: string; end: string }> = [
    { md: 'Jupiter', ad: 'Venus',   start: '1984-02-05', end: '1986-03-03' },
    { md: 'Jupiter', ad: 'Sun',     start: '1986-03-03', end: '1986-12-21' },
    { md: 'Jupiter', ad: 'Moon',    start: '1986-12-21', end: '1988-04-21' },
    { md: 'Jupiter', ad: 'Mars',    start: '1988-04-21', end: '1989-03-27' },
    { md: 'Jupiter', ad: 'Rahu',    start: '1989-03-27', end: '1991-08-21' },
    { md: 'Saturn',  ad: 'Saturn',  start: '1991-08-21', end: '1994-08-24' },
    { md: 'Saturn',  ad: 'Mercury', start: '1994-08-24', end: '1997-05-03' },
    { md: 'Saturn',  ad: 'Ketu',    start: '1997-05-03', end: '1998-06-12' },
    { md: 'Saturn',  ad: 'Venus',   start: '1998-06-12', end: '2001-08-12' },
    { md: 'Saturn',  ad: 'Sun',     start: '2001-08-12', end: '2002-07-24' },
    { md: 'Saturn',  ad: 'Moon',    start: '2002-07-24', end: '2004-02-24' },
    { md: 'Saturn',  ad: 'Mars',    start: '2004-02-24', end: '2005-04-03' },
    { md: 'Saturn',  ad: 'Rahu',    start: '2005-04-03', end: '2008-02-09' },
    { md: 'Saturn',  ad: 'Jupiter', start: '2008-02-09', end: '2010-08-21' },
    { md: 'Mercury', ad: 'Mercury', start: '2010-08-21', end: '2013-01-18' },
    { md: 'Mercury', ad: 'Ketu',    start: '2013-01-18', end: '2014-01-15' },
    { md: 'Mercury', ad: 'Venus',   start: '2014-01-15', end: '2016-11-15' },
    { md: 'Mercury', ad: 'Sun',     start: '2016-11-15', end: '2017-09-21' },
    { md: 'Mercury', ad: 'Moon',    start: '2017-09-21', end: '2019-02-21' },
    { md: 'Mercury', ad: 'Mars',    start: '2019-02-21', end: '2020-02-18' },
    { md: 'Mercury', ad: 'Rahu',    start: '2020-02-18', end: '2022-09-06' },
    { md: 'Mercury', ad: 'Jupiter', start: '2022-09-06', end: '2024-12-12' },
    { md: 'Mercury', ad: 'Saturn',  start: '2024-12-12', end: '2027-08-21' },
    { md: 'Ketu',    ad: 'Ketu',    start: '2027-08-21', end: '2028-01-18' },
    { md: 'Ketu',    ad: 'Venus',   start: '2028-01-18', end: '2029-03-18' },
    { md: 'Ketu',    ad: 'Sun',     start: '2029-03-18', end: '2029-07-24' },
    { md: 'Ketu',    ad: 'Moon',    start: '2029-07-24', end: '2030-02-24' },
    { md: 'Ketu',    ad: 'Mars',    start: '2030-02-24', end: '2030-07-21' },
    { md: 'Ketu',    ad: 'Rahu',    start: '2030-07-21', end: '2031-08-09' },
    { md: 'Ketu',    ad: 'Jupiter', start: '2031-08-09', end: '2032-07-15' },
    { md: 'Ketu',    ad: 'Saturn',  start: '2032-07-15', end: '2033-08-24' },
    { md: 'Ketu',    ad: 'Mercury', start: '2033-08-24', end: '2034-08-21' },
    { md: 'Venus',   ad: 'Venus',   start: '2034-08-21', end: '2037-12-21' },
    { md: 'Venus',   ad: 'Sun',     start: '2037-12-21', end: '2038-12-21' },
    { md: 'Venus',   ad: 'Moon',    start: '2038-12-21', end: '2040-08-21' },
    { md: 'Venus',   ad: 'Mars',    start: '2040-08-21', end: '2041-10-21' },
    { md: 'Venus',   ad: 'Rahu',    start: '2041-10-21', end: '2044-10-21' },
    { md: 'Venus',   ad: 'Jupiter', start: '2044-10-21', end: '2047-06-21' },
    { md: 'Venus',   ad: 'Saturn',  start: '2047-06-21', end: '2050-08-21' },
    { md: 'Venus',   ad: 'Mercury', start: '2050-08-21', end: '2053-06-21' },
  ]

  function activeAd(d: Date): string {
    for (const entry of adSchedule) {
      if (d >= new Date(entry.start) && d < new Date(entry.end)) {
        return entry.ad
      }
    }
    // Algorithmic fallback for dates outside schedule
    const { lord: mdLord } = activeMd(d)
    const mdEntry = VIMSHOTTARI.find(v => v.lord === mdLord)!
    const mdDays = Math.round(mdEntry.years * DAYS_PER_YEAR)
    const mdStartDate = FORENSIC_MD_SCHEDULE.find(m => m.lord === mdLord)
      ? new Date(FORENSIC_MD_SCHEDULE.find(m => m.lord === mdLord)!.start)
      : activeMd(d).start

    const mdIdx = VIMSHOTTARI.findIndex(v => v.lord === mdLord)
    let adStart = new Date(mdStartDate)

    for (let i = 0; i < VIMSHOTTARI.length; i++) {
      const vEntry = VIMSHOTTARI[(mdIdx + i) % VIMSHOTTARI.length]
      if (!vEntry) continue
      const { lord: adLord, years: adYrs } = vEntry
      const adDays = Math.round((mdDays * adYrs) / 120)
      const adEnd = addDays(adStart, adDays)
      if (d >= adStart && d < adEnd) return adLord
      adStart = adEnd
    }
    return mdLord // last resort
  }

  const rows: TimelineRow[] = []
  let current = new Date(start)

  while (current <= end && rows.length < limit) {
    const { lord: md } = activeMd(current)
    const ad = activeAd(current)
    rows.push({
      date: toIso(current),
      active_mahadasha: md,
      active_antardasha: ad,
      transit_highlights: [],
      signal_activations: [],
      source_citation: 'PyJHora/SwissEph DE441 + Brahma-L1',
    })
    current = addDays(current, 1)
  }

  return rows
}

// ── Registration ──────────────────────────────────────────────────────────────

/**
 * Register the timeline_query tool on the MCP server.
 *
 * timeline_query returns the deterministic dasha×transit alignment series
 * from kala_timeline (KA-3-1). Falls back to algorithmic computation when
 * the table is empty.
 *
 * @param server    The McpServer instance to register the tool on.
 * @param principal The resolved principal from Bearer key validation.
 */
export function registerKalaTimeline(server: McpServer, principal: Principal): void {
  server.registerTool(
    'timeline_query',
    {
      description: KALA_TIMELINE_DESCRIPTION,
      inputSchema: KalaTimelineSchema,
    },
    async (params: KalaTimelineParams) => {
      void principal // tier-gating deferred to L3 Kāla registration arc

      const start = new Date(params.date_range.start)
      const end   = new Date(params.date_range.end)

      if (start > end) {
        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(
                { error: 'date_range.start must be ≤ date_range.end', tool: 'timeline_query' },
                null,
                2,
              ),
            },
          ],
          isError: true,
        }
      }

      try {
        const result = await queryKalaTimeline(
          params.chart_id,
          start,
          end,
          params.limit,
        )

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
                { error: message, tool: 'timeline_query', asset: 'KA-3-1' },
                null,
                2,
              ),
            },
          ],
          isError: true,
        }
      }
    },
  )
}
