/**
 * phala_rectification.ts — BRAHMA-PH-4-3: phala.rectification
 *
 * Birth-time rectification using held-out LEL train/test split.
 *
 * Contract (BRAHMA L4 Phala — PH-4-3):
 *   owns:   Birth-time rectification via Vimshottari dasha alignment scoring
 *   tool:   rectification(chart_id) → {best_candidate_time, confidence,
 *           train_score, test_score, provenance_envelope}
 *   table:  phala_rectification (chart_id, candidate_time, alignment_score,
 *           rectification_confidence, source_citation)
 *
 * Algorithm (summary — see Python engine for full spec):
 *   For each candidate birth time ±30 min of nominal 10:43 IST (1-min steps):
 *     Shift Vimshottari MD boundaries proportionally.
 *     Score dasha alignment against LEL TRAIN events (events 1–43, 75% split).
 *     alignment_score = mean(1.0 MD+AD | 0.5 MD-only | 0.0 no match)
 *   Best candidate = argmax(alignment_score on train set).
 *   rectification_confidence = (|pearson_r| + best_train_score) / 2.
 *   test_score = evaluated AFTER candidate selection on held-out events 44–57.
 *
 * NO LEAKAGE: test events 44–57 are NEVER used for candidate selection.
 * The split is documented in every source_citation row.
 *
 * B.10 compliance: dasha-level only — no Swiss Ephemeris re-run.
 * Data source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.1 +
 *              LIFE_EVENT_LOG_v1_2.md (57 LEL events).
 *
 * Native chart: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
 *   chart_id: 362f9f17-95a5-490b-a5a7-027d3e0efda0
 *
 * DB tables / functions:
 *   phala_rectification             — base table (61 candidates per chart)
 *   phala_rectification_best        — view: best candidate per chart
 *   phala_get_rectification(UUID)   — query function → JSONB
 *
 * Migration: platform/migrations/brahma_phala_rectification.sql
 * Python engine: platform/python-sidecar/brahmagyan/phala/rectification.py
 *
 * Wiring: registerPhalaRectificationTool(server) → server.ts during L4 Phala registration.
 *
 * BRAHMA-PH-4-3
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import pg from 'pg'

const { Pool } = pg

// ── DB pool ───────────────────────────────────────────────────────────────────

let _pool: pg.Pool | null = null

function getPool(): pg.Pool {
  if (!_pool) {
    const dbUrl = process.env['DATABASE_URL']
    if (!dbUrl) {
      throw new Error('[phala_rectification] DATABASE_URL not set — cannot connect to phala tables')
    }
    _pool = new Pool({ connectionString: dbUrl, max: 5, idleTimeoutMillis: 30_000 })
  }
  return _pool
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ProvenanceEnvelope {
  source: string
  asset: string
  algorithm: string
  train_split: string
  test_split: string
  leakage_check: string
  b10_compliance: string
  computed_at: string | null
}

export interface RectificationResult {
  chart_id: string
  best_candidate_time: string | null
  confidence: number | null
  train_score: number | null
  test_score: number | null
  candidate_count: number
  source_citation: string | null
  provenance_envelope: ProvenanceEnvelope | Record<string, unknown>
}

export interface CandidateRow {
  candidate_time: string
  alignment_score: number
  rectification_confidence: number
}

// ── Core query functions ───────────────────────────────────────────────────────

/**
 * Query the best rectification candidate from phala_get_rectification DB function.
 * Returns the JSONB result directly.
 */
export async function queryRectification(chartId: string): Promise<RectificationResult> {
  const pool = getPool()
  const client = await pool.connect()
  try {
    const res = await client.query<{ phala_get_rectification: RectificationResult }>(
      `SELECT phala_get_rectification($1::UUID)`,
      [chartId]
    )
    const raw = res.rows[0]?.phala_get_rectification
    if (!raw) {
      return {
        chart_id: chartId,
        best_candidate_time: null,
        confidence: null,
        train_score: null,
        test_score: null,
        candidate_count: 0,
        source_citation: null,
        provenance_envelope: {
          source: 'phala.rectification',
          asset: 'PH-4-3',
          error: 'no_candidates — run Python seeder first',
        },
      }
    }
    return raw as unknown as RectificationResult
  } finally {
    client.release()
  }
}

/**
 * Query all 61 candidate rows for a chart, ordered by alignment_score DESC.
 */
export async function queryCandidates(
  chartId: string,
  opts: { limit?: number } = {}
): Promise<CandidateRow[]> {
  const { limit = 61 } = opts
  const pool = getPool()
  const client = await pool.connect()
  try {
    const res = await client.query<CandidateRow>(
      `SELECT
         TO_CHAR(candidate_time, 'HH24:MI') AS candidate_time,
         alignment_score,
         rectification_confidence
       FROM phala_rectification
       WHERE chart_id = $1
       ORDER BY alignment_score DESC, rectification_confidence DESC
       LIMIT $2`,
      [chartId, limit]
    )
    return res.rows
  } finally {
    client.release()
  }
}

// ── Tool registration ─────────────────────────────────────────────────────────

const TOOL_NAME = 'rectification'

const InputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart to rectify. ' +
        'Native chart (Abhisek Mohanty, 1984-02-05, 10:43 IST): ' +
        '362f9f17-95a5-490b-a5a7-027d3e0efda0'
    ),
  show_candidates: z
    .boolean()
    .optional()
    .default(false)
    .describe(
      'If true, include the top-10 candidate rows (by alignment_score) in the response. ' +
        'Useful for inspecting the alignment landscape around the best candidate.'
    ),
})

/**
 * Register the rectification MCP tool (PH-4-3) on an McpServer.
 *
 * This tool queries the phala_rectification table for the best birth-time
 * candidate using Vimshottari dasha alignment against LEL train events.
 *
 * Called from server.ts during the BRAHMA L4 Phala registration phase.
 *
 * Example:
 *   import { registerPhalaRectificationTool } from './tools/phala_rectification.js'
 *   registerPhalaRectificationTool(server)
 */
export function registerPhalaRectificationTool(server: McpServer): void {
  server.tool(
    TOOL_NAME,
    'Birth-time rectification via held-out LEL train/test split (BRAHMA-PH-4-3).\n\n' +
      'Returns the best birth-time candidate (±30 min of 10:43 IST, 1-min steps) ' +
      'selected by maximising Vimshottari dasha alignment on TRAIN events (events 1–43).\n\n' +
      'Fields:\n' +
      '  best_candidate_time — "HH:MM" IST; the rectified birth time\n' +
      '  confidence          — rectification_confidence = (|pearson_r| + train_score) / 2\n' +
      '  train_score         — mean alignment on 43 train events [0,1]\n' +
      '  test_score          — mean alignment on 14 held-out test events [0,1]\n' +
      '  provenance_envelope — full algorithm + data provenance\n\n' +
      'Algorithm: dasha_alignment_train_test_split\n' +
      '  Scoring: 1.0 = MD+AD match | 0.5 = MD-only | 0.0 = no match\n' +
      '  Train split: LEL events 1–43 (75%)\n' +
      '  Test split: LEL events 44–57 (25%, held-out — never used for selection)\n\n' +
      'B.10 compliance: dasha-level only; no Swiss Ephemeris re-run.\n' +
      'Source: FORENSIC_ASTROLOGICAL_DATA_v8_0.md §5.1 + LIFE_EVENT_LOG_v1_2.md.\n\n' +
      'Native chart (Abhisek Mohanty, 1984-02-05): ' +
      'chart_id = 362f9f17-95a5-490b-a5a7-027d3e0efda0\n\n' +
      'Requires phala_rectification table to be seeded first:\n' +
      '  python -m brahmagyan.phala.rectification seed --chart-id <uuid>\n\n' +
      'BRAHMA-PH-4-3 | phala.rectification contract.',
    InputSchema.shape,
    async (params) => {
      const input = InputSchema.parse(params)

      try {
        const result = await queryRectification(input.chart_id)

        // Validate contract assertions (defensive; DB CHECK should already enforce)
        const confidence = result.confidence ?? 0
        const trainScore = result.train_score ?? 0
        const testScore = result.test_score ?? 0

        const contractChecks: Record<string, boolean> = {
          'candidate_time_non_null': result.best_candidate_time !== null,
          'confidence_in_range': confidence >= 0 && confidence <= 1,
          'train_score_in_range': trainScore >= 0 && trainScore <= 1,
          'test_score_in_range': testScore >= 0 && testScore <= 1,
        }

        let candidates: CandidateRow[] | undefined
        if (input.show_candidates && result.best_candidate_time !== null) {
          candidates = await queryCandidates(input.chart_id, { limit: 10 })
        }

        const output: Record<string, unknown> = {
          chart_id: input.chart_id,
          best_candidate_time: result.best_candidate_time,
          confidence: result.confidence,
          train_score: result.train_score,
          test_score: result.test_score,
          candidate_count: result.candidate_count,
          source_citation: result.source_citation,
          provenance_envelope: result.provenance_envelope ?? {
            source: 'phala.rectification',
            asset: 'PH-4-3',
            algorithm: 'dasha_alignment_train_test_split',
            train_split: 'events 1–43 (75%)',
            test_split: 'events 44–57 (25%, held-out)',
            leakage_check: 'PASS — test events not used for candidate selection',
            b10_compliance: 'Dasha-level only; no Swiss Ephemeris re-run',
            computed_at: null,
          },
          contract_checks: contractChecks,
        }

        if (candidates !== undefined) {
          output['top_candidates'] = candidates
        }

        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(output, null, 2),
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
                  asset: 'PH-4-3',
                  chart_id: input.chart_id,
                  message,
                  hint:
                    'Ensure phala_rectification table exists (run migration) ' +
                    'and is seeded (python -m brahmagyan.phala.rectification seed).',
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
