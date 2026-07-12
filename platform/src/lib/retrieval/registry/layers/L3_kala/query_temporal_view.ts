/**
 * query_temporal_view — Temporal View (L3 Kāla)
 * ================================================
 * Asset: ka_kala_darshana (kala_darshana). WP-1.3(a) / F-L10-012 (LCA-19): the
 * lifetime confluence catalog (750 rows/chart) is now POPULATED — this tool was
 * previously STUBBED-PENDING-DATA and returned data:[]. It now serves the real rows,
 * bounded, with a disclosed total.
 *
 * Each darshana row integrates a convergence window with its obstruction summary and a
 * net effective score/label — the unified "when does this chart light up" timeline.
 *
 * Chart-scoped (principle #14). No native chart_id defaults.
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryTemporalViewCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_temporal_view',
  type:  'tool',
  layer: 'L3',
  name:  'query_temporal_view',

  description: [
    'Returns the temporal Kāla-Darshana view for a chart from kala_darshana (ka_kala_darshana)',
    '— the lifetime confluence catalog (750 rows/chart). Each row: peak_date, window_start,',
    'window_end, effective_score, net_label, obstruction_summary (jsonb), narrative (jsonb),',
    'linked convergence_id/signal_id. Filters: net_label, min_score, date_from, date_to,',
    'active_on. Bounded to 50 rows ordered by effective_score, with a disclosed total.',
  ].join(' '),

  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,

  required_inputs: ['chart_id'],

  input_schema: {
    chart_id:  { type: 'string', description: 'Chart UUID. Required.', required: true },
    net_label: { type: 'string', description: 'Filter by net_label (e.g. favorable, challenging). Omit for all.' },
    min_score: { type: 'number', description: 'Only rows with effective_score >= this value.' },
    date_from: { type: 'string', description: 'Only windows ending on/after this date (YYYY-MM-DD).' },
    date_to:   { type: 'string', description: 'Only windows starting on/before this date (YYYY-MM-DD).' },
    active_on: { type: 'string', description: 'Only windows whose [start,end] contains this date (YYYY-MM-DD).' },
    limit:     { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 50 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const net_label = args['net_label'] ? String(args['net_label']) : null
    const min_score = args['min_score'] !== undefined && args['min_score'] !== null ? Number(args['min_score']) : null
    const date_from = args['date_from'] ? String(args['date_from']) : null
    const date_to   = args['date_to'] ? String(args['date_to']) : null
    const active_on = args['active_on'] ? String(args['active_on']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (net_label)                                { filters.push(`net_label = $${p++}`);       params.push(net_label) }
    if (min_score !== null && !Number.isNaN(min_score)) { filters.push(`effective_score >= $${p++}`); params.push(min_score) }
    if (date_from)                                { filters.push(`window_end >= $${p++}`);     params.push(date_from) }
    if (date_to)                                  { filters.push(`window_start <= $${p++}`);   params.push(date_to) }
    if (active_on)                                { filters.push(`window_start <= $${p} AND window_end >= $${p}`); params.push(active_on); p++ }
    const where = filters.join(' AND ')

    const sql = `
      SELECT id, convergence_id, signal_id, effective_score, net_label,
             to_char(peak_date, 'YYYY-MM-DD')    AS peak_date,
             to_char(window_start, 'YYYY-MM-DD') AS window_start,
             to_char(window_end, 'YYYY-MM-DD')   AS window_end,
             obstruction_summary, narrative, source_citation
      FROM kala_darshana
      WHERE ${where}
      ORDER BY effective_score DESC NULLS LAST, peak_date
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM kala_darshana WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { net_label, min_score, date_from, date_to, active_on, limit },
          provenance: { tables: ['kala_darshana'], source: 'L3 Kāla Kāla-Darshana confluence catalog; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
