/**
 * query_rm_dosha_remedy_bundles — L2 Bodha per-dosha remedy bundle serving surface
 * =====================================================================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bodha_rm_dosha_remedy_bundles`, A13 Table 4, 226_bodha_spec_tables.sql). Serves the
 * per-dosha-class remedy bundle rollup (active flag, intensity, cancellation count,
 * bundled prescription ids, active dasha windows). Sibling of the already-served
 * bodha_rm_resonances / bodha_rm_prescriptions and the newly-wired bodha_rm_chart_summary
 * / bodha_rm_pattern_remedies / bodha_rm_dasha_windowed_prescriptions.
 *
 * B.10 HONESTY NOTE: this table holds 0 rows on the live chart at the time of this
 * wiring pass (confirmed via direct read-only DB check, not a stale doc claim). Its
 * schema is real and complete (not a stub design) and it shares a build family with
 * bodha_rm_pattern_remedies (270 live rows on the sibling prescriptions table), so this
 * is a genuine, not-yet-populated concept, not a fabrication — same reasoning already
 * applied to bodha_rm_dasha_windowed_prescriptions. The tool reports this honestly via
 * empty_reason; wiring now means the serving path is already live the moment the writer
 * populates it.
 *
 * Chart-scoped. Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 30

export const queryRmDoshaRemedyBundlesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_rm_dosha_remedy_bundles',
  type:  'tool',
  layer: 'L2',
  name:  'query_rm_dosha_remedy_bundles',

  description: [
    'Retrieve per-dosha-class remedy bundles from bodha_rm_dosha_remedy_bundles (Remedial',
    'Matrix). Each row: dosha_class, active_flag, intensity_score, cancellation_count,',
    'prescription_ids_in_bundle_array (cross-reference into bodha_rm_remedy_prescriptions),',
    'bundle_summary_jsonb, active_dasha_windows_jsonb. Filters: ayanamsha_id, dosha_class,',
    `active_only. May currently be empty on some charts if the writer has not yet run for`,
    `this chart's build — reported honestly via empty_reason, not silently. Bounded to`,
    `${MAX_LIMIT} rows with a disclosed total.`,
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    dosha_class:  { type: 'string', description: 'Filter by dosha_class. Omit for all.' },
    active_only:  { type: 'boolean', description: 'If true, only return bundles with active_flag = true. Default false.' },
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
    bulk_context: { pre_fetch_priority: 35, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const doshaClass   = args['dosha_class'] ? String(args['dosha_class']) : null
    const activeOnly   = args['active_only'] === true
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (doshaClass)   { filters.push(`dosha_class = $${p++}`); params.push(doshaClass) }
    if (activeOnly)   { filters.push('active_flag = true') }
    const where = filters.join(' AND ')

    const sql = `
      SELECT bundle_id, ayanamsha_id, dosha_class, active_flag, intensity_score,
             cancellation_count, prescription_ids_in_bundle_array, bundle_summary_jsonb,
             classical_source_citation_id, active_dasha_windows_jsonb,
             verification_pass_status, citation_ref, citation_human,
             to_char(computed_at, 'YYYY-MM-DD') AS computed_date
      FROM bodha_rm_dosha_remedy_bundles
      WHERE ${where}
      ORDER BY intensity_score DESC NULLS LAST
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_rm_dosha_remedy_bundles WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { ayanamsha_id, dosha_class: doshaClass, active_only: activeOnly, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No dosha-remedy-bundle rows matched for this chart (ayanamsha_id=${ayanamsha_id ?? 'any'}, dosha_class=${doshaClass ?? 'any'}). This table may not yet be populated by its writer for this chart's build.` }
            : {}),
          provenance: { tables: ['bodha_rm_dosha_remedy_bundles'], source: 'L2 Bodha Remedial Matrix per-dosha remedy bundle rollup; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
