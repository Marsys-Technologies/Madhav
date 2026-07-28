/**
 * query_convergence_windows — Temporal Convergence Windows (L3 Kāla)
 * ====================================================================
 * Queries kala_convergence (ka_sangam) — 19,482 rows per chart.
 * Returns scored convergence windows: periods where multiple signals co-activate.
 *
 * Key columns: convergence_score, rarity_years, confidence_score,
 *              independent_current_count, domain labels.
 *
 * Chart-agnostic: no native chart_id defaults (principle #14).
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { buildHonestPagination } from '@/lib/retrieval/envelope'

export const queryConvergenceWindowsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_convergence_windows',
  type:  'tool',
  layer: 'L3',
  name:  'query_convergence_windows',

  description: [
    'Returns temporal convergence windows for a chart — periods where multiple signals co-activate.',
    'Source: kala_convergence (a large row set per chart).',
    'Filter by date range, domain, and min_convergence_score.',
    'Returns convergence_score, rarity_years, confidence_score, and independent_current_count.',
    'High convergence_score + low rarity_years = high-attention period.',
    'Drill child of query_temporal_activation. Call for timing-specific domain questions.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'drill',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Transit windows' },

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (<chart_uuid>). Required.',
      required: true,
    },
    date_from: {
      type: 'string',
      description: 'Start of date range (ISO 8601: YYYY-MM-DD).',
    },
    date_to: {
      type: 'string',
      description: 'End of date range (ISO 8601: YYYY-MM-DD).',
    },
    min_convergence_score: {
      type: 'number',
      description: 'Minimum convergence_score (0..100, default: 0).',
    },
    domain: {
      type: 'string',
      description: 'Filter by domain (career, wealth, relationship, health, character, spirituality, other).',
    },
    top_k: {
      type: 'number',
      description: 'Max windows to return (default: 30, max: 200).',
    },
  },

  llm_hints: {
    agentic: {
      cost_class: 'medium',
      cacheable:  true,
    },
    bulk_context: {
      pre_fetch_priority: 12,
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    const chart_id = args['chart_id'] as string
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const date_from          = args['date_from'] as string | undefined
    const date_to            = args['date_to'] as string | undefined
    const min_convergence    = Number(args['min_convergence_score'] ?? 0)
    const domain             = args['domain'] as string | undefined
    const top_k              = Math.min(Number(args['top_k'] ?? 30), 200)

    try {
      // kala_convergence has no ayanamsha_id column — filter on chart_id only.
      const conds: string[] = ['chart_id = $1']
      const params: unknown[] = [chart_id]
      let p = 2

      if (date_from) { conds.push(`window_end >= $${p++}`);        params.push(date_from) }
      if (date_to)   { conds.push(`window_start <= $${p++}`);      params.push(date_to) }
      if (min_convergence > 0) { conds.push(`convergence_score >= $${p++}`); params.push(min_convergence) }
      if (domain)    { conds.push(`domain = $${p++}`);             params.push(domain) }

      // WP-1.5 receipt honesty: snapshot the filter params BEFORE the LIMIT param so the
      // COUNT runs under the identical WHERE conditions (never a re-guess of the family size).
      const countParams = [...params]
      const countWhere = conds.join(' AND ')
      params.push(top_k)
      const topKPh = `$${p++}`

      // WP-1.5 F-DATE-TZ: window_start/window_end/peak_date are DATE columns. Returned raw,
      // node-postgres parses each to a JS Date at server-local (IST) midnight then serializes
      // to a UTC ISO string — shifting e.g. 1990-05-14 to "1990-05-13T18:30:00.000Z"
      // (off-by-one + spurious time, un-round-trippable). to_char pins the true calendar
      // value as plain 'YYYY-MM-DD' text.
      const sql = `
        SELECT convergence_id, signal_id,
               to_char(window_start, 'YYYY-MM-DD') AS window_start,
               to_char(window_end, 'YYYY-MM-DD')   AS window_end,
               to_char(peak_date, 'YYYY-MM-DD')    AS peak_date,
               mode, convergence_score, orb_strength, rarity_years,
               confidence_score, confidence_label, independent_current_count,
               is_off_dasha_discovery, horizon_tier, domain,
               constituent_factors, source_citation
        FROM kala_convergence
        WHERE ${conds.join(' AND ')}
        ORDER BY convergence_score DESC NULLS LAST
        LIMIT ${topKPh}
      `

      const [result, countRes] = await Promise.all([
        query<Record<string, unknown>>(sql, params),
        query<{ total: string }>(
          `SELECT COUNT(*)::text AS total FROM kala_convergence WHERE ${countWhere}`,
          countParams,
        ),
      ])

      // Collect signal_id references (one per row)
      const signalRefs = [...new Set(
        (result.rows as Array<{ signal_id?: string }>).map(r => r.signal_id).filter(Boolean) as string[]
      )]

      // WP-1.5 (LCA-18) receipt honesty: this tool previously returned only window_count
      // with no total — a silent trim at top_k. Now every response declares the TRUE family
      // size and whether it was trimmed. buildHonestPagination guarantees the three fields
      // (total, more_available, next_cursor) can never contradict the served rows.
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      const pagination = buildHonestPagination({
        served: result.rows.length,
        limit:  top_k,
        offset: 0,
        total:  total_matching,
      })

      return {
        content: {
          chart_id,
          convergence_windows: result.rows,
          window_count:        result.rows.length,
          total_matching,
          more_available:      pagination.more_available,
          next_cursor:         pagination.next_cursor,
          signal_id_refs:      signalRefs,
          filters: { date_from, date_to, min_convergence, domain, top_k },
          provenance: { tables: ['kala_convergence'] },
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err), chart_id },
        is_error: true,
      }
    }
  },
}
