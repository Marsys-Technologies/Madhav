/**
 * get_vastu_directions — L1 Gaṇita vastu direction-impact serving surface
 * =========================================================================
 * WP-1.3(a) / F-L10-002 (LCA-19). Serves ga_vastu_planet_direction_map — fully
 * computed (40 rows/chart on both charts) but with NO MCP serving path, so the
 * vastu direction-impact map was UNREACHABLE by any consuming LLM. Read-only.
 *
 * F-E11 (highest-leverage item in L1_W1_ANALYSIS_BATCH_E.md): the per-chart
 * weakened/strengthened directions here and the 24-row classical per-direction
 * remedies in bg_vastu_direction_remedials (L0, query_vastu_direction_remedials.ts)
 * were never joined — the instrument held both halves of "your East is
 * afflicted, here is the classical remedy" with no surface putting them
 * together. Each served row now carries direction_remedies: the L0 catalog's
 * color/symbol/material/space guidance for that row's own direction.
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
    'dignity_d1, direction_impact, indication_tier, classical_citation, and',
    'direction_remedies (F-E11) -- the classical per-direction remedy set',
    '(color/symbol/material/space guidance, Brihat Samhita Ch.53 / Mayamata Ch.6)',
    'from bg_vastu_direction_remedials for that direction, joined server-side so an',
    'afflicted direction and its remedy are never read apart.',
    'Filters: graha, direction, ayanamsha_id, indication_tier. Bounded to 50 rows',
    'with a disclosed total.',
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
  // F-E28 (L1_W1_ANALYSIS_BATCH_E.md, NOW, §N.6 item 4): was undeclared. empty_reason:
  // true is a genuine claim -- the handler below now sets content.empty_reason whenever
  // total_matching === 0 (this file previously had NO empty_reason at all).
  density_contract: {
    paginated: true,
    facets: ['graha', 'direction', 'ayanamsha_id', 'indication_tier'],
    empty_reason: true,
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

    const filters: string[] = ['m.chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (graha)           { filters.push(`m.graha = $${p++}`);           params.push(graha) }
    if (direction)       { filters.push(`m.direction = $${p++}`);       params.push(direction) }
    if (ayanamsha_id)    { filters.push(`m.ayanamsha_id = $${p++}`);    params.push(ayanamsha_id) }
    if (indication_tier) { filters.push(`m.indication_tier = $${p++}`); params.push(indication_tier) }
    const where = filters.join(' AND ')

    // F-E11: LEFT JOIN LATERAL the L0 classical remedy set for this row's own
    // direction (bg_vastu_direction_remedials: 3 rows/direction — color, symbol,
    // material/space — aggregated so the fan-out never duplicates the served row).
    const sql = `
      SELECT m.id, m.graha, m.ayanamsha_id, m.direction, m.condition_score, m.dignity_d1,
             m.direction_impact, m.indication_tier, m.classical_citation,
             COALESCE(r.direction_remedies, '[]'::jsonb) AS direction_remedies
      FROM ga_vastu_planet_direction_map m
      LEFT JOIN LATERAL (
        SELECT jsonb_agg(
                 jsonb_build_object(
                   'remedy_type', remedy_type,
                   'remedy_description', remedy_description,
                   'classical_citation', classical_citation
                 ) ORDER BY remedy_type
               ) AS direction_remedies
        FROM bg_vastu_direction_remedials
        WHERE direction = m.direction
      ) r ON true
      WHERE ${where}
      ORDER BY m.graha, m.ayanamsha_id
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM ga_vastu_planet_direction_map m WHERE ${where}`, params),
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
          ...(total_matching === 0
            ? { empty_reason: `No vastu direction-impact rows for chart ${chart_id}${graha ? ` graha '${graha}'` : ''}${direction ? ` direction '${direction}'` : ''}${ayanamsha_id ? ` ayanamsha '${ayanamsha_id}'` : ''}${indication_tier ? ` tier '${indication_tier}'` : ''}.` }
            : {}),
          provenance: {
            tables: ['ga_vastu_planet_direction_map', 'bg_vastu_direction_remedials'],
            source: 'L1 Gaṇita vastu direction map; served chart-scoped.',
            note: 'direction_remedies (F-E11) is the L0 classical remedy set for the row’s own direction — an ' +
              'empty array means no catalog remedy exists for that direction, never a missing join.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
