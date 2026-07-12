/**
 * query_obstruction_periods — Obstruction Periods (L3 Kāla)
 * ===========================================================
 * Asset: ka_vighnakara (kala_obstruction). WP-1.3(a) / F-L10-018 (LCA-19): the
 * obstruction (danger) windows are now POPULATED (602-638 rows/chart) — this tool was
 * previously STUBBED-PENDING-DATA and advertised an 'obstructions' field while returning
 * []. It now serves the real rows, bounded, with a disclosed total.
 *
 * Each row: obstruction_type, severity (+severity_score), override_score,
 * obstruction_detail (jsonb), linked convergence_id/signal_id.
 *
 * Chart-scoped (principle #14). No native chart_id defaults.
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryObstructionPeriodsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_obstruction_periods',
  type:  'tool',
  layer: 'L3',
  name:  'query_obstruction_periods',

  description: [
    'Returns obstruction (vighna) periods for a chart from kala_obstruction (ka_vighnakara)',
    '— 602-638 rows/chart. Each row: obstruction_type, severity, severity_score,',
    'override_score, obstruction_detail (jsonb), and the linked convergence_id/signal_id.',
    'Filters: obstruction_type, severity, min_severity_score. Bounded to 50 rows ordered by',
    'severity_score, with a disclosed total.',
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
    chart_id:           { type: 'string', description: 'Chart UUID. Required.', required: true },
    obstruction_type:   { type: 'string', description: 'Filter by obstruction_type. Omit for all.' },
    severity:           { type: 'string', description: 'Filter by severity label (e.g. high, moderate, low). Omit for all.' },
    min_severity_score: { type: 'number', description: 'Only rows with severity_score >= this value.' },
    limit:              { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 50 },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const obstruction_type   = args['obstruction_type'] ? String(args['obstruction_type']) : null
    const severity           = args['severity'] ? String(args['severity']) : null
    const min_severity_score = args['min_severity_score'] !== undefined && args['min_severity_score'] !== null
      ? Number(args['min_severity_score']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (obstruction_type) { filters.push(`obstruction_type = $${p++}`); params.push(obstruction_type) }
    if (severity)         { filters.push(`severity = $${p++}`);         params.push(severity) }
    if (min_severity_score !== null && !Number.isNaN(min_severity_score)) {
      filters.push(`severity_score >= $${p++}`); params.push(min_severity_score)
    }
    const where = filters.join(' AND ')

    const sql = `
      SELECT id, convergence_id, signal_id, obstruction_type, severity, severity_score,
             override_score, obstruction_detail, source_citation
      FROM kala_obstruction
      WHERE ${where}
      ORDER BY severity_score DESC NULLS LAST
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM kala_obstruction WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          obstructions: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { obstruction_type, severity, min_severity_score, limit },
          provenance: { tables: ['kala_obstruction'], source: 'L3 Kāla obstruction (vighna) windows; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
