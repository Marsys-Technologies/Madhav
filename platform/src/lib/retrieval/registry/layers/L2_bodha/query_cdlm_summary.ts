/**
 * query_cdlm_summary — L2 Bodha CDLM chart-summary serving surface
 * ==================================================================
 * WP-1.3(a) / F-L10-004 (LCA-19). Serves bodha_cdlm_chart_summary — the cross-domain
 * linkage strength summary (5 rows/chart, one per ayanamsha) that was computed and
 * stored but had NO MCP serving path. Read-only, bounded.
 *
 * Chart-scoped (principle #14). This is a whole-chart CDLM digest: total linkage,
 * contradiction density, dominant/weakest domains, bridge/asymmetric link counts.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryCdlmSummaryCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_cdlm_summary',
  type:  'tool',
  layer: 'L2',
  name:  'query_cdlm_summary',

  description: [
    'Retrieve the Cross-Domain Linkage Matrix (CDLM) chart-level summary from',
    'bodha_cdlm_chart_summary — one row per ayanamsha. Fields: chart_typology_class,',
    'total_chart_linkage, contradiction_density, dominant_3_domains, weakest_3_domains,',
    'bridge_link_count, asymmetric_link_count, house_to_domain_strength,',
    'karaka_to_domain_strength, verification_pass_status, citation. Filters: ayanamsha_id.',
    'Bounded with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: "Filter by ayanamsha (e.g. 'LAHIRI'). Omit for all." },
    limit:        { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'cross_domain',
  traversal_level: 'L-ORIENT',
  tool_role: 'umbrella',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 70, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT summary_id, ayanamsha_id, snapshot_type, chart_typology_class,
             total_chart_linkage, contradiction_density,
             dominant_3_domains_array, weakest_3_domains_array,
             bridge_link_count, asymmetric_link_count,
             house_to_domain_strength_jsonb, karaka_to_domain_strength_jsonb,
             pattern_cluster_markers_jsonb, verification_pass_status,
             citation_ref, citation_human
      FROM bodha_cdlm_chart_summary
      WHERE ${where}
      ORDER BY ayanamsha_id
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_cdlm_chart_summary WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { ayanamsha_id, limit },
          provenance: { tables: ['bodha_cdlm_chart_summary'], source: 'L2 Bodha CDLM chart summary; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
