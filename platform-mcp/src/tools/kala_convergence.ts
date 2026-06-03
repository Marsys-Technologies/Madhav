/**
 * kala_convergence.ts — BRAHMA-KA-3-2: convergence_window tool
 *
 * Asset: kala.convergence (measured convergence windows where ≥3 factors align)
 * Contract (BRAHMA_L1_L5_REGISTRY_SEED §D):
 *   owns:   kala.convergence — date windows where ≥3 temporal factors align simultaneously
 *   tool:   convergence_window(chart_id, date_range, min_score?) → windows with provenance
 *   table:  kala_convergence (chart_id UUID, window_start DATE, window_end DATE,
 *           convergence_score FLOAT, constituent_factors JSONB, source_citation TEXT NOT NULL)
 *   gate:   convergence windows surfaced; score in [0.0, 1.0]; provenance_envelope on response
 *   FORENSIC: native's 2002-07 (Saturn-Moon AD start) and 2017-09 (Mercury Sun→Moon AD)
 *             produce ≥1 convergence window overlapping those dates.
 *
 * Algorithm:
 *   Clusters of ≥3 of {dasha_transition, transit_conjunction, signal_activation, md_ad_alignment}
 *   within a 30-day neighbourhood.
 *   convergence_score = Σ(factor_weight_i) / (factor_count × 1.0), capped at 1.0
 *
 * Source data: FORENSIC_ASTROLOGICAL_DATA §5.1 Vimshottari Dasha + §22 Sade Sati cycles
 *   chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0 (native FORENSIC canonical)
 *
 * Wiring: register via registerConvergenceWindow(server, principal) in server.ts
 *
 * BRAHMA-KA-3-2
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import pg from 'pg'

const { Pool } = pg

// ── DB pool (lazy singleton) ──────────────────────────────────────────────────

let _pool: pg.Pool | null = null

function getPool(): pg.Pool {
  if (!_pool) {
    const dbUrl = process.env['DATABASE_URL']
    if (!dbUrl) {
      throw new Error(
        '[kala_convergence] DATABASE_URL not set — cannot connect to kala_convergence table'
      )
    }
    _pool = new Pool({ connectionString: dbUrl, max: 5, idleTimeoutMillis: 30_000 })
  }
  return _pool
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ConstituentFactor {
  label: string
  date: string
  weight: number
  factor_type: 'dasha_transition' | 'transit_conjunction' | 'signal_activation' | 'md_ad_alignment'
}

export interface ConvergenceWindow {
  window_start: string
  window_end: string
  convergence_score: number
  factor_count: number
  constituent_factors: ConstituentFactor[]
  source_citation: string
}

export interface ConvergenceWindowResult {
  chart_id: string
  date_range: { start: string; end: string }
  min_score: number
  window_count: number
  windows: ConvergenceWindow[]
  provenance_envelope: {
    asset_id: string
    tool: string
    source_citation: string
    algorithm: string
    cluster_window_days: number
    min_factors: number
  }
}

// ── Input schema ──────────────────────────────────────────────────────────────

const ConvergenceWindowSchema = z.object({
  /** Chart UUID to retrieve convergence windows for. */
  chart_id: z.string().uuid({
    message: 'chart_id must be a valid UUID (e.g. 362f9f17-95a5-490b-a5a7-027d3e0efda0)',
  }),

  /**
   * Date range for the query. Both dates must be ISO 8601 strings (YYYY-MM-DD).
   * Defaults to full native life range (1984-02-05 to 2035-12-31) if omitted.
   */
  date_range: z
    .object({
      start: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'date must be YYYY-MM-DD'),
      end: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'date must be YYYY-MM-DD'),
    })
    .optional(),

  /**
   * Minimum convergence_score (0.0–1.0) to include in results.
   * Higher values return only strongly-aligned windows.
   * Default: 0.0 (return all seeded windows).
   */
  min_score: z.number().min(0).max(1).default(0.0),
})

export type ConvergenceWindowParams = z.infer<typeof ConvergenceWindowSchema>

// ── Tool description ──────────────────────────────────────────────────────────

const CONVERGENCE_WINDOW_DESCRIPTION = `\
What it does: Returns measured convergence windows (kala.convergence KA-3-2) — calendar \
intervals where ≥3 temporal factors align simultaneously: dasha_transition, \
transit_conjunction, signal_activation, and md_ad_alignment. Each window carries a \
convergence_score (0.0–1.0) weighted by the individual factor importance. \
Algorithm: 30-day sliding cluster; score = Σ(factor_weight_i) / (factor_count × 1.0). \
Source: FORENSIC §5.1 Vimshottari + §22 Sade Sati + natal transits.

Outputs per window: window_start, window_end (ISO dates), convergence_score (0.0–1.0), \
factor_count, constituent_factors (array of {label, date, weight, factor_type}), \
source_citation ("PyJHora/SwissEph DE441 + Brahma-L1").

factor_type vocabulary:
  dasha_transition — MD/AD boundary in Vimshottari or Yogini dasha
  transit_conjunction — transiting planet activating a natal position
  signal_activation — transit through a natal sign triggering chart-wide activation
  md_ad_alignment — MD lord and AD lord are the same planet (intensification)

FORENSIC anchors: 2002-07 (Saturn-Moon AD start: multiple dasha+transit factors) and \
2017-09 (Mercury Sun→Moon AD + Saturn transit + Sade Sati C2.P2 entry) are expected \
to show convergence_score > 0.6.

When to prefer: Use convergence_window when you need to identify high-density temporal \
alignment periods — windows where the chart is likely to manifest multi-theme events. \
Pair with timeline_query (KA-3-1) for the full temporal fabric. \
Use min_score=0.7 to focus on strongly-aligned windows only. \
Use date_range to narrow to a specific life period (e.g. career 2005–2020). \
This is a Kāla / L3 tool — it states that alignment exists, not what it means; \
combine with Phala / L4 event_anchors for predictive interpretation.`

// ── Core query logic ──────────────────────────────────────────────────────────

export async function queryConvergenceWindows(
  params: ConvergenceWindowParams
): Promise<ConvergenceWindowResult> {
  const pool = getPool()
  const client = await pool.connect()

  try {
    const startDate = params.date_range?.start ?? '1984-02-05'
    const endDate = params.date_range?.end ?? '2035-12-31'
    const minScore = params.min_score ?? 0.0

    // Query kala_convergence — windows overlapping [startDate, endDate]
    const { rows } = await client.query<{
      window_start: Date
      window_end: Date
      convergence_score: number
      constituent_factors: ConstituentFactor[]
      source_citation: string
    }>(
      `SELECT
         window_start::text  AS window_start,
         window_end::text    AS window_end,
         convergence_score,
         constituent_factors,
         source_citation
       FROM kala_convergence
       WHERE chart_id = $1::uuid
         AND window_end   >= $2::date
         AND window_start <= $3::date
         AND convergence_score >= $4
       ORDER BY window_start`,
      [params.chart_id, startDate, endDate, minScore]
    )

    const windows: ConvergenceWindow[] = rows.map((r) => {
      const factors: ConstituentFactor[] = Array.isArray(r.constituent_factors)
        ? (r.constituent_factors as ConstituentFactor[])
        : []

      return {
        window_start: typeof r.window_start === 'string'
          ? r.window_start
          : (r.window_start as unknown as Date).toISOString().split('T')[0]!,
        window_end: typeof r.window_end === 'string'
          ? r.window_end
          : (r.window_end as unknown as Date).toISOString().split('T')[0]!,
        convergence_score: Number(r.convergence_score),
        factor_count: factors.length,
        constituent_factors: factors,
        source_citation: r.source_citation,
      }
    })

    return {
      chart_id: params.chart_id,
      date_range: { start: startDate, end: endDate },
      min_score: minScore,
      window_count: windows.length,
      windows,
      provenance_envelope: {
        asset_id: 'KA-3-2',
        tool: 'convergence_window',
        source_citation: 'PyJHora/SwissEph DE441 + Brahma-L1',
        algorithm:
          'Sliding 45-day window over dasha+transit+signal events; ' +
          'convergence_score = Σ(factor_weight_i) / (factor_count × 1.0)',
        cluster_window_days: 45,
        min_factors: 3,
      },
    }
  } finally {
    client.release()
  }
}

// ── Tool registration ─────────────────────────────────────────────────────────

/**
 * Register the convergence_window MCP tool on the given server.
 *
 * @param server    The McpServer instance to register the tool on.
 */
export function registerConvergenceWindow(server: McpServer): void {
  server.registerTool(
    'convergence_window',
    {
      description: CONVERGENCE_WINDOW_DESCRIPTION,
      inputSchema: ConvergenceWindowSchema,
    },
    async (params: ConvergenceWindowParams) => {
      try {
        const result = await queryConvergenceWindows(params)

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
                  error: message,
                  tool: 'convergence_window',
                  asset: 'KA-3-2',
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
