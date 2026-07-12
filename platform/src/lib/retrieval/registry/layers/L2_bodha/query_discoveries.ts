/**
 * query_discoveries — L2 Bodha non-obvious discoveries serving surface
 * ====================================================================
 * WP-1.3j / F-0129..0137 (W1-FOLLOWUP). Serves bodha_discoveries — the ranked
 * "what an acharya would miss" discovery ledger (thousands of rows/chart across
 * 5 ayanamshas) that was computed and stored but had NO MCP serving path.
 * Read-only, bounded (LIMIT ≤50 + disclosed total + offset pagination).
 *
 * Chart-scoped (principle #14). Ordered by composite_discovery_rank (1 = most salient).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryDiscoveriesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_discoveries',
  type:  'tool',
  layer: 'L2',
  name:  'query_discoveries',

  description: [
    'Retrieve ranked non-obvious chart discoveries from bodha_discoveries (ph: bo_* discovery engine).',
    'Each row is a cross-subsystem finding an individual acharya would likely miss, with a',
    'non_obviousness_score, consequence_score, composite_discovery_rank (1 = most salient),',
    'surface_reading vs depth_reading (+ surface_depth_delta), hypothesis_text, novelty_class,',
    'and why_an_acharya_misses_it. Filters: ayanamsha_id, discovery_class. Ordered by',
    'composite_discovery_rank ASC. Bounded (LIMIT ≤50) with a disclosed total and offset pagination.',
  ].join(' '),

  input_schema: {
    chart_id:       { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id:   { type: 'string', description: "Filter by ayanamsha (e.g. 'lahiri_chitrapaksha'). Omit for all." },
    discovery_class:{ type: 'string', description: 'Filter by discovery_class. Omit for all.' },
    limit:          { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
    offset:         { type: 'number', description: 'Pagination offset (default 0).' },
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
    bulk_context: { pre_fetch_priority: 60, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const discovery_class = args['discovery_class'] ? String(args['discovery_class']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)
    const offset = Math.max(Number(args['offset'] ?? 0), 0)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id)    { filters.push(`ayanamsha_id = $${p++}`);    params.push(ayanamsha_id) }
    if (discovery_class) { filters.push(`discovery_class = $${p++}`); params.push(discovery_class) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT discovery_id, ayanamsha_id, discovery_class, discovery_subsystem,
             non_obviousness_score, consequence_score, composite_discovery_rank,
             novelty_class, corroboration_count, corroborating_methods_array,
             affected_domains_array, surface_reading, depth_reading, surface_depth_delta,
             hypothesis_text, why_an_acharya_misses_it, meaningfulness_basis,
             constituent_refs_jsonb, cross_subsystem_refs_jsonb,
             to_char(computed_at, 'YYYY-MM-DD') AS computed_date
      FROM bodha_discoveries
      WHERE ${where}
      ORDER BY composite_discovery_rank ASC NULLS LAST, non_obviousness_score DESC NULLS LAST
      LIMIT $${p} OFFSET $${p + 1}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit, offset]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_discoveries WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: offset + rowsRes.rows.length < total_matching,
          filters: { ayanamsha_id, discovery_class, limit, offset },
          provenance: { tables: ['bodha_discoveries'], source: 'L2 Bodha discovery ledger; served chart-scoped, budgeted.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
