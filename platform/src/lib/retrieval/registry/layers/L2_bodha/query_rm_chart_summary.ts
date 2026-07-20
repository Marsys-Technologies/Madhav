/**
 * query_rm_chart_summary — L2 Bodha remedial chart-level priority profile
 * ===========================================================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap
 * set, `bodha_rm_chart_summary`, 10 rows). Serves the chart-level rolled-up
 * remedy priority snapshot (top resonance targets, top prescriptions,
 * recommended intensity/phase sequence, dosha counts, cross-tradition
 * convergence — A13 Table 6, 226_bodha_spec_tables.sql). Same sibling family
 * as the already-served bodha_rm_resonances / bodha_rm_prescriptions.
 * chart_remedy_embedding_vec (768-dim) is excluded from the served columns —
 * an internal similarity-search input, not human-readable content.
 *
 * Chart-scoped. Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 10

export const queryRmChartSummaryCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_rm_chart_summary',
  type:  'tool',
  layer: 'L2',
  name:  'query_rm_chart_summary',

  description: [
    'Retrieve the chart-level remedial priority summary from bodha_rm_chart_summary',
    '(Remedial Matrix). Each row: snapshot_type, top_3_resonance_targets_jsonb,',
    'top_10_priority_prescriptions_jsonb, recommended_intensity_class,',
    'recommended_remedy_phase_sequence_jsonb, total_active_dosha_count,',
    'primary_dosha_class, cross_tradition_convergence_jsonb, remedy_chart_typology,',
    'acharya_review_required_count, feasibility_assessment_jsonb. Filters: ayanamsha_id,',
    'snapshot_type. Bounded to 10 rows with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:      { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id:  { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    snapshot_type: { type: 'string', description: 'Filter by snapshot_type. Omit for all.' },
    limit:         { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 40, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const snapshotType = args['snapshot_type'] ? String(args['snapshot_type']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (snapshotType) { filters.push(`snapshot_type = $${p++}`); params.push(snapshotType) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT summary_id, ayanamsha_id, snapshot_type, top_3_resonance_targets_jsonb,
             top_10_priority_prescriptions_jsonb, recommended_intensity_class,
             recommended_remedy_phase_sequence_jsonb, total_active_dosha_count,
             primary_dosha_class, cross_tradition_convergence_jsonb, remedy_chart_typology,
             acharya_review_required_count, feasibility_assessment_jsonb,
             verification_pass_status, citation_ref, citation_human,
             to_char(computed_at, 'YYYY-MM-DD') AS computed_date
      FROM bodha_rm_chart_summary
      WHERE ${where}
      ORDER BY computed_at DESC
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_rm_chart_summary WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { ayanamsha_id, snapshot_type: snapshotType, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No chart-summary rows matched (ayanamsha_id=${ayanamsha_id ?? 'any'}, snapshot_type=${snapshotType ?? 'any'}).` }
            : {}),
          provenance: { tables: ['bodha_rm_chart_summary'], source: 'L2 Bodha Remedial Matrix chart-level priority profile; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
