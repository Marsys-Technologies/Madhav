/**
 * query_rm_prescriptions — L2 Bodha remedy-prescription serving surface
 * =====================================================================
 * WP-1.3j / F-0161,0165,0174 (W1-FOLLOWUP). Serves bodha_rm_remedy_prescriptions —
 * the chart-scoped, resonance-targeted remedy prescriptions (135 rows/chart across 5
 * ayanamshas) computed and stored but with NO MCP serving path.
 * Read-only, bounded. The prescription embedding vector + oversized jsonb are omitted.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryRmPrescriptionsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_rm_prescriptions',
  type:  'tool',
  layer: 'L2',
  name:  'query_rm_prescriptions',

  description: [
    'Retrieve chart remedy prescriptions from bodha_rm_remedy_prescriptions (Remedial Matrix).',
    'Each row targets a graha / resonance / dosha with a tradition-scoped remedy: remedy_category,',
    'remedy_label_human, classical_strength_rating, resonance_match_score, feasibility_score,',
    'ritual_complexity_class, requires_acharya_review_flag, counter_indications, phase_sequence_class,',
    'and citation. Filters: ayanamsha_id, tradition, remedy_category, target_graha. Ordered by',
    'resonance_match_score DESC. Bounded (LIMIT ≤50) with a disclosed total + offset pagination.',
  ].join(' '),

  input_schema: {
    chart_id:        { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id:    { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    tradition:       { type: 'string', description: 'Filter by tradition. Omit for all.' },
    remedy_category: { type: 'string', description: 'Filter by remedy_category. Omit for all.' },
    target_graha:    { type: 'string', description: 'Filter by target_graha. Omit for all.' },
    limit:           { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
    offset:          { type: 'number', description: 'Pagination offset (default 0).' },
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
    bulk_context: { pre_fetch_priority: 45, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const tradition = args['tradition'] ? String(args['tradition']) : null
    const remedy_category = args['remedy_category'] ? String(args['remedy_category']) : null
    const target_graha = args['target_graha'] ? String(args['target_graha']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)
    const offset = Math.max(Number(args['offset'] ?? 0), 0)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id)    { filters.push(`ayanamsha_id = $${p++}`);    params.push(ayanamsha_id) }
    if (tradition)       { filters.push(`tradition = $${p++}`);       params.push(tradition) }
    if (remedy_category) { filters.push(`remedy_category = $${p++}`); params.push(remedy_category) }
    if (target_graha)    { filters.push(`target_graha = $${p++}`);    params.push(target_graha) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT prescription_id, ayanamsha_id, target_graha, target_resonance_id,
             tradition, sub_tradition, remedy_category, remedy_id_g27, remedy_label_human,
             classical_strength_rating, classical_sources_jsonb,
             resonance_match_score, feasibility_score, ritual_complexity_class,
             requires_acharya_review_flag, acharya_review_reason_array,
             counter_indications_array, targets_motif_id, targets_cell_id, targets_dosha_class,
             cross_tradition_corroboration_count, phase_sequence_class, phase_duration_days,
             recommended_facing_direction, verification_pass_status, citation_ref, citation_human,
             to_char(computed_at, 'YYYY-MM-DD') AS computed_date
      FROM bodha_rm_remedy_prescriptions
      WHERE ${where}
      ORDER BY resonance_match_score DESC NULLS LAST, classical_strength_rating DESC NULLS LAST
      LIMIT $${p} OFFSET $${p + 1}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit, offset]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_rm_remedy_prescriptions WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: offset + rowsRes.rows.length < total_matching,
          filters: { ayanamsha_id, tradition, remedy_category, target_graha, limit, offset },
          provenance: { tables: ['bodha_rm_remedy_prescriptions'], source: 'L2 Bodha Remedial Matrix prescriptions; served chart-scoped, budgeted.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
