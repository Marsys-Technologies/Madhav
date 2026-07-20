/**
 * query_rm_pattern_remedies — L2 Bodha pattern-level remedy theme serving surface
 * ====================================================================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap
 * set, `bodha_rm_pattern_remedies`, 90 rows). Serves remedy themes keyed to
 * CDLM pattern clusters / CGM motifs (source_kind), with a
 * cross_tradition_unanimity_score and prescription_ids_array cross-reference
 * (A13 Table 5, 226_bodha_spec_tables.sql). Sibling of the already-served
 * bodha_rm_resonances / bodha_rm_prescriptions.
 *
 * Chart-scoped. Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryRmPatternRemediesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_rm_pattern_remedies',
  type:  'tool',
  layer: 'L2',
  name:  'query_rm_pattern_remedies',

  description: [
    'Retrieve pattern-level remedy themes from bodha_rm_pattern_remedies (Remedial Matrix).',
    'Each row: source_kind (cdlm_pattern_cluster|cgm_motif), source_id, remedy_theme,',
    'prescription_ids_array (cross-reference into bodha_rm_remedy_prescriptions),',
    'theme_strength, cross_tradition_unanimity_score. Filters: ayanamsha_id, source_kind.',
    `Ordered by theme_strength DESC. Bounded to ${MAX_LIMIT} rows with a disclosed total.`,
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    source_kind:  { type: 'string', description: 'Filter by source_kind (cdlm_pattern_cluster|cgm_motif). Omit for all.' },
    limit:        { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
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
    bulk_context: { pre_fetch_priority: 30, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const sourceKind   = args['source_kind'] ? String(args['source_kind']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (sourceKind)   { filters.push(`source_kind = $${p++}`); params.push(sourceKind) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT pattern_remedy_id, ayanamsha_id, source_kind, source_id, remedy_theme,
             prescription_ids_array, theme_strength, cross_tradition_unanimity_score,
             verification_pass_status, citation_ref, citation_human,
             to_char(computed_at, 'YYYY-MM-DD') AS computed_date
      FROM bodha_rm_pattern_remedies
      WHERE ${where}
      ORDER BY theme_strength DESC NULLS LAST
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_rm_pattern_remedies WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { ayanamsha_id, source_kind: sourceKind, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No pattern-remedy rows matched (ayanamsha_id=${ayanamsha_id ?? 'any'}, source_kind=${sourceKind ?? 'any'}).` }
            : {}),
          provenance: { tables: ['bodha_rm_pattern_remedies'], source: 'L2 Bodha Remedial Matrix pattern-level remedy themes; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
