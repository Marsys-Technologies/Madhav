/**
 * kala_period_snapshot.ts — BRAHMA-KA-3-3: period_snapshot MCP tool
 *
 * Point-in-time snapshot for a chart at a given date. Returns:
 *   - active Vimshottari Mahadasha + Antardasha
 *   - transit_positions (from kala_timeline, if populated)
 *   - active_signals_count (from bodha_signals)
 *   - convergence_score (avg confidence from bodha_signals)
 *   - obstructions (from kala_obstruction table, ±90-day window)
 *   - provenance_envelope
 *
 * Contract (KA-3-3):
 *   tool: period_snapshot(chart_id, date) → full temporal snapshot
 *   source_citation: "PyJHora/SwissEph DE441 + Brahma-L1" on all obstruction rows
 *
 * FORENSIC grounding:
 *   Native: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar, Odisha.
 *   Saturn MD: 1991-08-21 → 2010-08-21 (DSH.V.006–014)
 *   Mercury MD: 2010-08-21 → 2027-08-21 (DSH.V.015–023)
 *   Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.1
 *
 * Wiring: register via registerKalaPeriodSnapshotTool(server) in server.ts
 *
 * BRAHMA-KA-3-3
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import pg from 'pg'

const { Pool } = pg

// ── DB pool (lazy singleton) ──────────────────────────────────────────────────

let _pool: pg.Pool | null = null

function getPool(): pg.Pool | null {
  if (!_pool) {
    const dbUrl = process.env['DATABASE_URL']
    if (!dbUrl) {
      // Return null — callers degrade gracefully when DB is unavailable
      return null
    }
    _pool = new Pool({ connectionString: dbUrl, max: 5, idleTimeoutMillis: 30_000 })
  }
  return _pool
}

// ── Canonical Vimshottari schedule (FORENSIC §5.1) ────────────────────────────
// Native: Abhisek Mohanty, 1984-02-05. All dates canonical per FORENSIC_v8_0.

interface DashaRow {
  rowId: string
  md: string
  ad: string
  start: string
  end: string
}

const VIMSHOTTARI_SCHEDULE: DashaRow[] = [
  { rowId: 'DSH.V.001', md: 'Jupiter', ad: 'Venus',   start: '1984-02-05', end: '1986-03-03' },
  { rowId: 'DSH.V.002', md: 'Jupiter', ad: 'Sun',     start: '1986-03-03', end: '1986-12-21' },
  { rowId: 'DSH.V.003', md: 'Jupiter', ad: 'Moon',    start: '1986-12-21', end: '1988-04-21' },
  { rowId: 'DSH.V.004', md: 'Jupiter', ad: 'Mars',    start: '1988-04-21', end: '1989-03-27' },
  { rowId: 'DSH.V.005', md: 'Jupiter', ad: 'Rahu',    start: '1989-03-27', end: '1991-08-21' },
  { rowId: 'DSH.V.006', md: 'Saturn',  ad: 'Saturn',  start: '1991-08-21', end: '1994-08-24' },
  { rowId: 'DSH.V.007', md: 'Saturn',  ad: 'Mercury', start: '1994-08-24', end: '1997-05-03' },
  { rowId: 'DSH.V.008', md: 'Saturn',  ad: 'Ketu',    start: '1997-05-03', end: '1998-06-12' },
  { rowId: 'DSH.V.009', md: 'Saturn',  ad: 'Venus',   start: '1998-06-12', end: '2001-08-12' },
  { rowId: 'DSH.V.010', md: 'Saturn',  ad: 'Sun',     start: '2001-08-12', end: '2002-07-24' },
  { rowId: 'DSH.V.011', md: 'Saturn',  ad: 'Moon',    start: '2002-07-24', end: '2004-02-24' },
  { rowId: 'DSH.V.012', md: 'Saturn',  ad: 'Mars',    start: '2004-02-24', end: '2005-04-03' },
  { rowId: 'DSH.V.013', md: 'Saturn',  ad: 'Rahu',    start: '2005-04-03', end: '2008-02-09' },
  { rowId: 'DSH.V.014', md: 'Saturn',  ad: 'Jupiter', start: '2008-02-09', end: '2010-08-21' },
  { rowId: 'DSH.V.015', md: 'Mercury', ad: 'Mercury', start: '2010-08-21', end: '2013-01-18' },
  { rowId: 'DSH.V.016', md: 'Mercury', ad: 'Ketu',    start: '2013-01-18', end: '2014-01-15' },
  { rowId: 'DSH.V.017', md: 'Mercury', ad: 'Venus',   start: '2014-01-15', end: '2016-11-15' },
  { rowId: 'DSH.V.018', md: 'Mercury', ad: 'Sun',     start: '2016-11-15', end: '2017-09-21' },
  { rowId: 'DSH.V.019', md: 'Mercury', ad: 'Moon',    start: '2017-09-21', end: '2019-02-21' },
  { rowId: 'DSH.V.020', md: 'Mercury', ad: 'Mars',    start: '2019-02-21', end: '2020-02-18' },
  { rowId: 'DSH.V.021', md: 'Mercury', ad: 'Rahu',    start: '2020-02-18', end: '2022-09-06' },
  { rowId: 'DSH.V.022', md: 'Mercury', ad: 'Jupiter', start: '2022-09-06', end: '2024-12-12' },
  { rowId: 'DSH.V.023', md: 'Mercury', ad: 'Saturn',  start: '2024-12-12', end: '2027-08-21' },
  { rowId: 'DSH.V.024', md: 'Ketu',    ad: 'Ketu',    start: '2027-08-21', end: '2028-01-18' },
  { rowId: 'DSH.V.025', md: 'Ketu',    ad: 'Venus',   start: '2028-01-18', end: '2029-03-18' },
  { rowId: 'DSH.V.026', md: 'Ketu',    ad: 'Sun',     start: '2029-03-18', end: '2029-07-24' },
  { rowId: 'DSH.V.027', md: 'Ketu',    ad: 'Moon',    start: '2029-07-24', end: '2030-02-24' },
  { rowId: 'DSH.V.028', md: 'Ketu',    ad: 'Mars',    start: '2030-02-24', end: '2030-07-21' },
  { rowId: 'DSH.V.029', md: 'Ketu',    ad: 'Rahu',    start: '2030-07-21', end: '2031-08-09' },
  { rowId: 'DSH.V.030', md: 'Ketu',    ad: 'Jupiter', start: '2031-08-09', end: '2032-07-15' },
  { rowId: 'DSH.V.031', md: 'Ketu',    ad: 'Saturn',  start: '2032-07-15', end: '2033-08-24' },
  { rowId: 'DSH.V.032', md: 'Ketu',    ad: 'Mercury', start: '2033-08-24', end: '2034-08-21' },
  { rowId: 'DSH.V.033', md: 'Venus',   ad: 'Venus',   start: '2034-08-21', end: '2037-12-21' },
]

function getDashaForDate(targetDate: Date): DashaRow | null {
  const ts = targetDate.getTime()
  for (const row of VIMSHOTTARI_SCHEDULE) {
    const s = new Date(row.start).getTime()
    const e = new Date(row.end).getTime()
    if (ts >= s && ts < e) return row
  }
  return null
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ObstructionRecord {
  obstruction_type: string
  severity: number
  factors: Record<string, unknown>
  source_citation: string
  date: string
}

export interface PeriodSnapshotResult {
  chart_id: string
  snapshot_date: string
  active_dasha: string | null
  active_antardasha: string | null
  dasha_row_id: string | null
  dasha_period: { start: string; end: string } | null
  transit_positions: Record<string, number> | null
  active_signals_count: number
  convergence_score: number
  obstructions: ObstructionRecord[]
  provenance_envelope: {
    source: string
    source_citation: string
    computed_at: string
    chart_id: string
    snapshot_date: string
  }
}

// ── Core query function ───────────────────────────────────────────────────────

/**
 * Compute a point-in-time period snapshot for a chart.
 *
 * Dasha state comes from the embedded canonical schedule (no DB needed).
 * Transit positions are fetched from kala_timeline if available.
 * Active signals count + convergence score are fetched from bodha_signals if available.
 * Obstructions are fetched from kala_obstruction (±90-day window).
 *
 * All failures in DB fetches are silently swallowed — snapshot still returns
 * with null/zero for those fields, so the dasha fields always work.
 */
export async function computePeriodSnapshot(
  chartId: string,
  targetDateStr: string
): Promise<PeriodSnapshotResult> {
  const targetDate = new Date(targetDateStr + 'T00:00:00Z')
  const snapshotDate = targetDateStr

  // 1. Dasha (always computed from embedded schedule — no DB required)
  const dashaRow = getDashaForDate(targetDate)
  const activeDasha = dashaRow?.md ?? null
  const activeAntardasha = dashaRow?.ad ?? null
  const dashaRowId = dashaRow?.rowId ?? null
  const dashaPeriod = dashaRow
    ? { start: dashaRow.start, end: dashaRow.end }
    : null

  // 2. DB fetches (optional — degrade gracefully when pool unavailable)
  const pool = getPool()
  let transitPositions: Record<string, number> | null = null
  let activeSignalsCount = 0
  let convergenceScore = 0.0
  let obstructions: ObstructionRecord[] = []

  if (pool !== null) try {
    const client = await pool.connect()
    try {
      // 2a. Transit positions from kala_timeline
      try {
        const tRes = await client.query<{ transit_positions: unknown }>(
          `SELECT transit_positions
           FROM kala_timeline
           WHERE chart_id = $1 AND date = $2
           LIMIT 1`,
          [chartId, snapshotDate]
        )
        if (tRes.rows.length > 0 && tRes.rows[0].transit_positions) {
          const raw = tRes.rows[0].transit_positions
          transitPositions =
            typeof raw === 'string' ? (JSON.parse(raw) as Record<string, number>) : (raw as Record<string, number>)
        }
      } catch {
        // kala_timeline may not exist yet — continue
      }

      // 2b. Active signals count
      try {
        const sRes = await client.query<{ count: string }>(
          `SELECT COUNT(*) AS count FROM bodha_signals WHERE chart_id = $1`,
          [chartId]
        )
        activeSignalsCount = parseInt(sRes.rows[0]?.count ?? '0', 10)
      } catch {
        // bodha_signals may not be populated — continue
      }

      // 2c. Convergence score (avg confidence)
      try {
        const cRes = await client.query<{ avg: string | null }>(
          `SELECT AVG(confidence)::float AS avg FROM bodha_signals WHERE chart_id = $1`,
          [chartId]
        )
        const avg = cRes.rows[0]?.avg
        convergenceScore = avg !== null && avg !== undefined ? parseFloat(avg) : 0.0
      } catch {
        // continue
      }

      // 2d. Obstructions (±90-day window around snapshot_date)
      try {
        const oRes = await client.query<{
          obstruction_type: string
          severity: number | string
          factors: unknown
          source_citation: string
          date: string
        }>(
          `SELECT obstruction_type, severity, factors, source_citation, date::text
           FROM kala_obstruction
           WHERE chart_id = $1
             AND date BETWEEN ($2::date - INTERVAL '90 days') AND ($2::date + INTERVAL '90 days')
           ORDER BY severity DESC, date
           LIMIT 10`,
          [chartId, snapshotDate]
        )
        obstructions = oRes.rows.map((r) => ({
          obstruction_type: r.obstruction_type,
          severity:
            typeof r.severity === 'string' ? parseFloat(r.severity) : r.severity,
          factors:
            typeof r.factors === 'string'
              ? (JSON.parse(r.factors) as Record<string, unknown>)
              : (r.factors as Record<string, unknown>) ?? {},
          source_citation: r.source_citation,
          date: r.date,
        }))
      } catch {
        // kala_obstruction may not exist yet — continue
      }
    } finally {
      client.release()
    }
  } catch {
    // Pool connection failed — proceed with defaults
  }

  const provenance = {
    source: 'brahma.kala.obstruction',
    source_citation: 'PyJHora/SwissEph DE441 + Brahma-L1',
    computed_at: new Date().toISOString(),
    chart_id: chartId,
    snapshot_date: snapshotDate,
  }

  return {
    chart_id: chartId,
    snapshot_date: snapshotDate,
    active_dasha: activeDasha,
    active_antardasha: activeAntardasha,
    dasha_row_id: dashaRowId,
    dasha_period: dashaPeriod,
    transit_positions: transitPositions,
    active_signals_count: activeSignalsCount,
    convergence_score: convergenceScore,
    obstructions,
    provenance_envelope: provenance,
  }
}

// ── MCP tool registration ─────────────────────────────────────────────────────

const TOOL_NAME = 'period_snapshot'

const InputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart to snapshot. ' +
        'Native chart (Abhisek Mohanty, 1984-02-05): 362f9f17-95a5-490b-a5a7-027d3e0efda0'
    ),
  date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format')
    .describe(
      'Point-in-time date for the snapshot (YYYY-MM-DD). ' +
        'Returns the active Vimshottari dasha, transit positions, MSR signal count, ' +
        'convergence score, and any obstruction records within ±90 days.'
    ),
})

/**
 * Register the period_snapshot MCP tool on an McpServer instance.
 *
 * Called from server.ts during the BRAHMA L3 Kāla registration phase.
 *
 * Example:
 *   import { registerKalaPeriodSnapshotTool } from './tools/kala_period_snapshot.js'
 *   registerKalaPeriodSnapshotTool(server)
 */
export function registerKalaPeriodSnapshotTool(server: McpServer): void {
  server.tool(
    TOOL_NAME,
    'Point-in-time period snapshot for a chart. ' +
      'Returns: active Vimshottari Mahadasha + Antardasha (from FORENSIC §5.1 schedule), ' +
      'transit_positions (kala_timeline, if populated), ' +
      'active_signals_count + convergence_score (bodha_signals), ' +
      'obstructions within ±90 days (kala_obstruction table), ' +
      'and a provenance_envelope with source_citation. ' +
      'Dasha lookup is fully offline (embedded schedule) — DB unavailability only ' +
      'affects transit/signals/obstructions fields (degrade to null/zero/empty). ' +
      'FORENSIC grounding: Saturn MD 1991-08-21→2010-08-21; Mercury MD 2010-08-21→2027-08-21. ' +
      'source_citation: "PyJHora/SwissEph DE441 + Brahma-L1". ' +
      'BRAHMA-KA-3-3 | kala.obstruction contract.',
    InputSchema.shape,
    async (params) => {
      const input = InputSchema.parse(params)

      try {
        const result = await computePeriodSnapshot(input.chart_id, input.date)
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
                  date: input.date,
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        }
      }
    }
  )
}
