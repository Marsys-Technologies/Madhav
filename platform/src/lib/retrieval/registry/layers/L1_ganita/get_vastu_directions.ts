/**
 * get_vastu_directions — L1 Gaṇita vastu direction-impact serving surface
 * =========================================================================
 * WP-1.3(a) / F-L10-002 (LCA-19). Serves ga_vastu_planet_direction_map — fully
 * computed (40 rows/chart on both charts) but with NO MCP serving path, so the
 * vastu direction-impact map was UNREACHABLE by any consuming LLM. Read-only.
 *
 * Chart-scoped (principle #14). Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const getVastuDirectionsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L1/get_vastu_directions',
  type:  'tool',
  layer: 'L1',
  name:  'get_vastu_directions',

  description: [
    'Retrieve the vastu (directional) planet-impact map for a chart from',
    'ga_vastu_planet_direction_map. Per-graha rows: direction, condition_score,',
    'dignity_d1, direction_impact, indication_tier, classical_citation. Filters:',
    'graha, direction, ayanamsha_id, indication_tier. Bounded to 50 rows with',
    'a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:        { type: 'string', description: 'Chart UUID. Required.', required: true },
    graha:           { type: 'string', description: 'Filter by graha. Omit for all.' },
    direction:       { type: 'string', description: 'Filter by direction (e.g. East, North). Omit for all.' },
    ayanamsha_id:    { type: 'string', description: "Filter by ayanamsha. Omit for all." },
    indication_tier: { type: 'string', description: 'Filter by indication tier. Omit for all.' },
    limit:           { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
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

    const graha           = args['graha'] ? String(args['graha']) : null
    const direction       = args['direction'] ? String(args['direction']) : null
    const ayanamsha_id    = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const indication_tier = args['indication_tier'] ? String(args['indication_tier']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (graha)           { filters.push(`graha = $${p++}`);           params.push(graha) }
    if (direction)       { filters.push(`direction = $${p++}`);       params.push(direction) }
    if (ayanamsha_id)    { filters.push(`ayanamsha_id = $${p++}`);    params.push(ayanamsha_id) }
    if (indication_tier) { filters.push(`indication_tier = $${p++}`); params.push(indication_tier) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT id, graha, ayanamsha_id, direction, condition_score, dignity_d1,
             direction_impact, indication_tier, classical_citation
      FROM ga_vastu_planet_direction_map
      WHERE ${where}
      ORDER BY graha, ayanamsha_id
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM ga_vastu_planet_direction_map WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { graha, direction, ayanamsha_id, indication_tier, limit },
          provenance: { tables: ['ga_vastu_planet_direction_map'], source: 'L1 Gaṇita vastu direction map; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
