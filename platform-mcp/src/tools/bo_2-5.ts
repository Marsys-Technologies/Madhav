/**
 * bo_2-5.ts — BRAHMA-BO-2-5: bodha.lenses
 *
 * Lens views over bodha_signals + bodha_graph.
 * No new tables — computed via stored functions defined in brahma_bo_2-5.sql.
 *
 * Contract (BRAHMA_L1_L5_REGISTRY_SEED §C — bodha.lenses):
 *   owns:   lens views over the signal graph
 *   tool:   query_signals(chart_id, lens=concordance|contradiction|salience|negative_space|null)
 *   tables: NONE (functions over bodha_signals + bodha_graph)
 *   gate:
 *     - concordance lens: groups signals by school agreement/disagreement
 *     - contradiction lens: surfaces signal pairs with contradicting valence
 *     - negative_space: computes what is NOT signalled (absent expected signals)
 *     - salience: ranks signals by confidence × reinforcement_count × domain_weight
 *     - native chart test: >= 1 contradiction-hub (conflicting signals on same domain)
 *
 * Depends:
 *   bodha_signals table (BO-2-1 — brahma_bodha_bo21.sql)
 *   bodha_graph table (BO-2-2 — brahma_bodha_bo22.sql)
 *   bodha_concordance_lens(), bodha_contradiction_lens(),
 *   bodha_negative_space(), bodha_salience_lens(),
 *   bodha_query_signals_with_lens() — all from brahma_bo_2-5.sql
 *
 * Native chart: Abhisek Mohanty, 1984-02-05, 10:43 IST, Bhubaneswar
 *   chart_id: 482012f1-710e-4a25-994a-93821f5871aa
 *
 * Wiring: registerBodhaLensesTool(server) → server.ts during L2 Bodha registration.
 *
 * BRAHMA-BO-2-5
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
      throw new Error('[bo_2-5] DATABASE_URL not set — cannot connect to bodha tables')
    }
    _pool = new Pool({ connectionString: dbUrl, max: 5, idleTimeoutMillis: 30_000 })
  }
  return _pool
}

// ── Types ─────────────────────────────────────────────────────────────────────

export type LensName = 'concordance' | 'contradiction' | 'negative_space' | 'salience'

export interface ConcordanceRow {
  domain: string
  valence: string
  signal_count: number
  avg_confidence: number
  avg_salience: number
  agreement_score: number
  signal_ids: string[]
  signal_names: string[]
}

export interface ContradictionRow {
  domain: string
  signal_id_a: string
  signal_name_a: string
  valence_a: string
  confidence_a: number
  signal_id_b: string
  signal_name_b: string
  valence_b: string
  confidence_b: number
  tension_score: number
  graph_edge_id: string | null
  has_graph_edge: boolean
}

export interface NegativeSpaceRow {
  check_type: 'domain_absent' | 'domain_weak' | 'graha_absent'
  label: string
  signal_count: number
  max_confidence: number
  interpretation_hint: string
}

export interface SalienceRow {
  rank: number
  signal_id: string
  signal_name: string
  domain: string
  valence: string
  confidence: number
  base_salience: number
  reinforcement_count: number
  domain_weight: number
  composite_salience: number
  claim_text: string
  source_citation: string
  grounding_status: string
}

export interface LensQueryResult {
  chart_id: string
  lens: LensName | null
  filters_applied: {
    domain: string | null
    valence: string | null
    confidence_min: number
    limit: number
  }
  total_returned: number
  rows: ConcordanceRow[] | ContradictionRow[] | NegativeSpaceRow[] | SalienceRow[] | pg.QueryResultRow[]
  provenance_envelope?: {
    source: string
    asset: string
    lens: string
    chart_id: string
    computed_at: string
  }
}

// ── Core query functions ───────────────────────────────────────────────────────

/**
 * Concordance lens: groups signals by domain+valence, ranks by agreement_score.
 * agreement_score = avg(confidence × salience) — high = school consensus.
 */
export async function queryConcordanceLens(
  chartId: string,
  opts: { domain?: string; valence?: string; minConf?: number } = {}
): Promise<ConcordanceRow[]> {
  const { domain, valence, minConf = 0 } = opts
  const pool = getPool()
  const client = await pool.connect()
  try {
    const res = await client.query<ConcordanceRow>(
      `SELECT domain, valence, signal_count, avg_confidence, avg_salience,
              agreement_score, signal_ids, signal_names
       FROM bodha_concordance_lens($1, $2)
       WHERE ($3::TEXT IS NULL OR domain = $3)
         AND ($4::TEXT IS NULL OR valence = $4)`,
      [chartId, minConf, domain ?? null, valence ?? null]
    )
    return res.rows
  } finally {
    client.release()
  }
}

/**
 * Contradiction lens: surfaces same-domain signal pairs with opposing valence.
 * tension_score = product of confidences × saliencies.
 * Links to bodha_graph CONTRADICTS edges when they exist.
 * Acceptance gate: native chart must return >= 1 row.
 */
export async function queryContradictionLens(
  chartId: string,
  opts: { domain?: string; minConf?: number } = {}
): Promise<ContradictionRow[]> {
  const { domain, minConf = 0.3 } = opts
  const effectiveMinConf = Math.max(minConf, 0.3)
  const pool = getPool()
  const client = await pool.connect()
  try {
    const res = await client.query<ContradictionRow>(
      `SELECT domain, signal_id_a, signal_name_a, valence_a, confidence_a,
              signal_id_b, signal_name_b, valence_b, confidence_b,
              tension_score, graph_edge_id, has_graph_edge
       FROM bodha_contradiction_lens($1, $2)
       WHERE ($3::TEXT IS NULL OR domain = $3)`,
      [chartId, effectiveMinConf, domain ?? null]
    )
    return res.rows
  } finally {
    client.release()
  }
}

/**
 * Negative space: computes what is NOT signalled.
 * Returns domain_absent | domain_weak | graha_absent rows.
 * The silence is itself informative — a blank domain is an astrological finding.
 */
export async function queryNegativeSpace(chartId: string): Promise<NegativeSpaceRow[]> {
  const pool = getPool()
  const client = await pool.connect()
  try {
    const res = await client.query<NegativeSpaceRow>(
      `SELECT check_type, label, signal_count, max_confidence, interpretation_hint
       FROM bodha_negative_space($1)`,
      [chartId]
    )
    return res.rows
  } finally {
    client.release()
  }
}

/**
 * Salience lens: ranks signals by composite_salience.
 * composite_salience = confidence × base_salience × (1 + reinforcement_count/10) × domain_weight
 * Domain weights: career=1.0, wealth=0.9, ..., house_domain=0.65.
 */
export async function querySalienceLens(
  chartId: string,
  opts: {
    domain?: string
    valence?: string
    minConf?: number
    minSalience?: number
    limit?: number
  } = {}
): Promise<SalienceRow[]> {
  const { domain, valence, minConf = 0, minSalience = 0, limit = 50 } = opts
  const pool = getPool()
  const client = await pool.connect()
  try {
    const res = await client.query<SalienceRow>(
      `SELECT rank, signal_id, signal_name, domain, valence, confidence,
              base_salience, reinforcement_count, domain_weight, composite_salience,
              claim_text, source_citation, grounding_status
       FROM bodha_salience_lens($1, $2, $3, $4)
       WHERE ($5::TEXT IS NULL OR domain = $5)
         AND ($6::TEXT IS NULL OR valence = $6)`,
      [chartId, minConf, minSalience, limit, domain ?? null, valence ?? null]
    )
    return res.rows
  } finally {
    client.release()
  }
}

// ── Tool registration ─────────────────────────────────────────────────────────

const TOOL_NAME = 'query_signals'

const LensSchema = z.enum(['concordance', 'contradiction', 'negative_space', 'salience'])

const InputSchema = z.object({
  chart_id: z
    .string()
    .uuid()
    .describe(
      'UUID of the chart. ' +
        'Native chart (Abhisek Mohanty, 1984-02-05): 482012f1-710e-4a25-994a-93821f5871aa'
    ),
  lens: LensSchema.optional().describe(
    'Lens to apply to the signal set:\n' +
      '  concordance   — group signals by domain+valence; ranks by agreement_score (avg confidence×salience)\n' +
      '  contradiction — surface same-domain pairs with opposing valence; sorted by tension_score DESC\n' +
      '  negative_space— compute absent/weak domains and grahas (the silence is informative)\n' +
      '  salience      — rank by composite_salience = confidence × base_salience × (1+reinforcement/10) × domain_weight\n' +
      '  omit          — plain signal list (BO-2-1 behaviour, ordered by salience DESC)\n'
  ),
  domain: z
    .enum([
      'career',
      'wealth',
      'relationships',
      'health',
      'spirit',
      'mind',
      'travel',
      'parents',
      'dasha',
      'nadi_bnn',
      'yogini_tajaka',
      'house_domain',
    ])
    .optional()
    .describe(
      'Filter by domain. Applies to concordance, contradiction, and salience lenses, and plain mode.'
    ),
  valence: z
    .enum(['benefic', 'malefic', 'context-dependent', 'mixed'])
    .optional()
    .describe(
      'Filter by valence. Applies to concordance, salience lenses, and plain mode. ' +
        'Not applicable to contradiction lens (it always pairs opposing valences) or negative_space.'
    ),
  confidence_min: z
    .number()
    .min(0)
    .max(1)
    .optional()
    .default(0.0)
    .describe(
      'Minimum confidence threshold [0.0–1.0]. Default 0. ' +
        'For contradiction lens, effective minimum is max(confidence_min, 0.3).'
    ),
  limit: z
    .number()
    .int()
    .min(1)
    .max(500)
    .optional()
    .default(50)
    .describe(
      'Maximum rows returned (default 50, max 500). ' +
        'For salience lens, controls the top-N ranked signals returned.'
    ),
})

/**
 * Register the query_signals MCP tool (BO-2-5 lens extension) on an McpServer.
 *
 * This extends the BO-2-1 query_signals tool with lens= filtering. When lens is
 * omitted, the tool behaves as a plain signal list (BO-2-1 compatibility).
 *
 * Called from server.ts during the BRAHMA L2 Bodha registration phase.
 *
 * Example:
 *   import { registerBodhaLensesTool } from './tools/bo_2-5.js'
 *   registerBodhaLensesTool(server)
 */
export function registerBodhaLensesTool(server: McpServer): void {
  server.tool(
    TOOL_NAME,
    'Query bodha signals with optional lens-based views (BO-2-5).\n\n' +
      'Four lenses over bodha_signals + bodha_graph:\n' +
      '  concordance   — groups signals by domain+valence, ranks by agreement_score\n' +
      '  contradiction — surfaces opposing-valence signal pairs (same domain), ranked by tension_score\n' +
      '  negative_space— computes absent/weak domains and grahas (what is NOT signalled)\n' +
      '  salience      — ranks by composite_salience = conf × salience × (1+reinforce/10) × domain_weight\n\n' +
      'Omit lens= for plain BO-2-1 signal list (salience DESC order).\n\n' +
      'Native chart (Abhisek Mohanty, 1984-02-05): ' +
      'expect ≥1 contradiction-hub in career/wealth domains ' +
      '(Saturn-Ketu malefic vs. Jupiter benefic in 9H).\n\n' +
      'No new tables — computed over existing bodha_signals + bodha_graph.\n' +
      'BRAHMA-BO-2-5 | bodha.lenses contract.',
    InputSchema.shape,
    async (params) => {
      const input = InputSchema.parse(params)

      try {
        let rows: unknown[]
        const lens = input.lens

        switch (lens) {
          case 'concordance':
            rows = await queryConcordanceLens(input.chart_id, {
              domain: input.domain,
              valence: input.valence,
              minConf: input.confidence_min ?? 0,
            })
            break

          case 'contradiction':
            rows = await queryContradictionLens(input.chart_id, {
              domain: input.domain,
              minConf: input.confidence_min ?? 0,
            })
            break

          case 'negative_space':
            rows = await queryNegativeSpace(input.chart_id)
            break

          case 'salience':
            rows = await querySalienceLens(input.chart_id, {
              domain: input.domain,
              valence: input.valence,
              minConf: input.confidence_min ?? 0,
              limit: input.limit ?? 50,
            })
            break

          default: {
            // Plain mode — BO-2-1 signal list
            const pool = getPool()
            const client = await pool.connect()
            try {
              const conditions: string[] = ['chart_id = $1']
              const qParams: unknown[] = [input.chart_id]
              let pIdx = 2

              if (input.domain) {
                conditions.push(`domain = $${pIdx++}`)
                qParams.push(input.domain)
              }
              if (input.valence) {
                conditions.push(`valence = $${pIdx++}`)
                qParams.push(input.valence)
              }
              if ((input.confidence_min ?? 0) > 0) {
                conditions.push(`confidence >= $${pIdx++}`)
                qParams.push(input.confidence_min)
              }

              qParams.push(input.limit ?? 50)
              const res = await client.query(
                `SELECT signal_id, chart_id, domain, signal_type, valence,
                        temporal_activation, graha, house, nakshatra,
                        confidence, salience, signal_name, claim_text,
                        source_l1_fact_ids, source_citation, grounding_status
                 FROM public.bodha_signals
                 WHERE ${conditions.join(' AND ')}
                 ORDER BY salience DESC, confidence DESC
                 LIMIT $${pIdx}`,
                qParams
              )
              rows = res.rows
            } finally {
              client.release()
            }
            break
          }
        }

        const result: LensQueryResult = {
          chart_id: input.chart_id,
          lens: lens ?? null,
          filters_applied: {
            domain: input.domain ?? null,
            valence: input.valence ?? null,
            confidence_min: input.confidence_min ?? 0,
            limit: input.limit ?? 50,
          },
          total_returned: rows.length,
          rows: rows as LensQueryResult['rows'],
          provenance_envelope: {
            source: 'bodha.lenses',
            asset: 'BO-2-5',
            lens: input.lens ?? 'concordance',
            chart_id: input.chart_id,
            computed_at: new Date().toISOString(),
          },
        }

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
                  lens: input.lens ?? null,
                  message,
                  chart_id: input.chart_id,
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
