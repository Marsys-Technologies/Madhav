/**
 * query_activation_waveform — L3 Kāla monthly activation waveform serving surface
 * =================================================================================
 * WP-1.3(a) / F-L10-015 (LCA-19). Serves kala_taranga (ka_taranga) — the monthly
 * activation waveform, 79,728 rows/chart — computed and stored but ENTIRELY unreachable
 * over the wire.
 *
 * BUDGET DISCIPLINE (WP-1.3, HARD): 79,728 rows/chart must NEVER be dumped. This tool
 * defaults to mode='summary' — an aggregate (row count, date span, distinct scopes, and
 * the top-N peak-activation months) that fits a bounded payload. mode='drill' returns at
 * most 50 raw monthly rows and REQUIRES a scope filter (scope_kind or scope_id) so the
 * caller has already narrowed the 79k waveform before any row-level pull. Every response
 * discloses the total matching count.
 *
 * Chart-scoped (principle #14).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50
const MAX_PEAKS = 24

export const queryActivationWaveformCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_activation_waveform',
  type:  'tool',
  layer: 'L3',
  name:  'query_activation_waveform',

  description: [
    'Retrieve the monthly activation waveform for a chart from kala_taranga (ka_taranga,',
    'a large per-chart row set). mode="summary" (default) returns an aggregate: total months,',
    'date span, distinct scopes, and the top peak-activation months — a bounded payload,',
    'never the full waveform. mode="drill" returns at most 50 raw monthly rows and requires',
    'a scope filter (scope_kind or scope_id) plus optionally month_from/month_to. Filters:',
    'scope_kind, scope_id, month_from, month_to. Every response discloses the total count.',
  ].join(' '),

  input_schema: {
    chart_id:   { type: 'string', description: 'Chart UUID. Required.', required: true },
    mode:       { type: 'string', description: "'summary' (default, aggregate) | 'drill' (bounded raw rows, requires a scope filter).", enum: ['summary', 'drill'] },
    scope_kind: { type: 'string', description: 'Filter by scope kind (e.g. graha, bhava, yoga). Omit for all.' },
    scope_id:   { type: 'string', description: 'Filter by scope id. Omit for all.' },
    month_from: { type: 'string', description: 'Only months on/after this date (YYYY-MM-DD).' },
    month_to:   { type: 'string', description: 'Only months on/before this date (YYYY-MM-DD).' },
    limit:      { type: 'number', description: `drill mode only: max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 30, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const mode       = args['mode'] === 'drill' ? 'drill' : 'summary'
    const scope_kind = args['scope_kind'] ? String(args['scope_kind']) : null
    const scope_id   = args['scope_id'] ? String(args['scope_id']) : null
    const month_from = args['month_from'] ? String(args['month_from']) : null
    const month_to   = args['month_to'] ? String(args['month_to']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (scope_kind) { filters.push(`scope_kind = $${p++}`); params.push(scope_kind) }
    if (scope_id)   { filters.push(`scope_id = $${p++}`);   params.push(scope_id) }
    if (month_from) { filters.push(`month >= $${p++}`);     params.push(month_from) }
    if (month_to)   { filters.push(`month <= $${p++}`);     params.push(month_to) }
    const where = filters.join(' AND ')

    try {
      const countRes = await query<{ total: string }>(
        `SELECT COUNT(*)::text AS total FROM kala_taranga WHERE ${where}`, params)
      const total_matching = Number(countRes.rows[0]?.total ?? 0)

      if (mode === 'drill') {
        // Budget guard: drill REQUIRES a scope filter so the caller has narrowed the 79k first.
        if (!scope_kind && !scope_id) {
          return {
            content: {
              error: 'drill mode requires a scope filter (scope_kind or scope_id) to bound the 79k-row waveform. Use mode="summary" for an aggregate first.',
              chart_id, total_matching,
            },
            is_error: true,
          }
        }
        const rowsRes = await query(
          `SELECT taranga_id, month, scope_kind, scope_id, activation, components, formula_version
           FROM kala_taranga WHERE ${where}
           ORDER BY month LIMIT $${p}`,
          [...params, limit])
        return {
          content: {
            chart_id, mode,
            rows: rowsRes.rows,
            count: rowsRes.rows.length,
            total_matching,
            more_available: total_matching > rowsRes.rows.length,
            filters: { scope_kind, scope_id, month_from, month_to, limit },
            budget_note: 'Bounded drill — page with month_from/month_to.',
            provenance: { tables: ['kala_taranga'], source: 'L3 Kāla monthly activation waveform; served chart-scoped.' },
          },
          is_error: false,
        }
      }

      // summary mode — aggregate + top peaks (bounded), never the full waveform.
      const [aggRes, peaksRes] = await Promise.all([
        query<Record<string, unknown>>(
          `SELECT MIN(month) AS first_month, MAX(month) AS last_month,
                  COUNT(DISTINCT scope_id)::int AS distinct_scopes,
                  COUNT(DISTINCT scope_kind)::int AS distinct_scope_kinds,
                  ROUND(AVG(activation)::numeric, 4) AS avg_activation,
                  ROUND(MAX(activation)::numeric, 4) AS max_activation
           FROM kala_taranga WHERE ${where}`, params),
        query<Record<string, unknown>>(
          `SELECT month, scope_kind, scope_id, activation
           FROM kala_taranga WHERE ${where}
           ORDER BY activation DESC NULLS LAST, month
           LIMIT ${MAX_PEAKS}`, params),
      ])
      return {
        content: {
          chart_id, mode,
          total_matching,
          aggregate: aggRes.rows[0] ?? {},
          peak_months: peaksRes.rows,
          filters: { scope_kind, scope_id, month_from, month_to },
          budget_note: `Aggregate view of ${total_matching} monthly rows. Call mode="drill" with a scope filter for bounded raw rows.`,
          provenance: { tables: ['kala_taranga'], source: 'L3 Kāla monthly activation waveform; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
