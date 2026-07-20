/**
 * get_condition_composite — L1 Gaṇita unified planetary-condition rollup
 * ==========================================================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap
 * set, `ga_condition_composite`, 90 rows — highest-value single item this
 * batch per the disposition doc). Serves the rich, actively-built unified
 * per-graha condition rollup: D1+varga dignity spread, all 5 avastha
 * schemes, motion/combustion state, naisargika/tatkalika/panchadha
 * friendship, graha yuddha, a unified 0-1 condition_score with breakdown,
 * and peak/weak dasha-trajectory windows. `ganita_condition_get`'s
 * dignity/avasthas/karakas facets all read chart_facts directly, not this
 * composite — this tool exposes the composite rollup itself.
 *
 * Chart-scoped (principle #14). Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const getConditionCompositeCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L1/get_condition_composite',
  type:  'tool',
  layer: 'L1',
  name:  'get_condition_composite',

  description: [
    'Retrieve the unified per-graha condition rollup for a chart from ga_condition_composite.',
    'Per-graha row bundles: dignity_d1 + dignity_score_d1 + varga_dignity_spread/composite;',
    'all 5 avastha states (baladi/jagradadi/deeptaadi/lajjitaadi/sayanadi); motion_state,',
    'speed_degrees_per_day, is_retrograde, combustion_arc_from_sun, is_combust/deeply_combust;',
    'naisargika/tatkalika/panchadha friendship relations; graha_yuddha_with/result; a unified',
    'condition_score (0-1, condition_score_breakdown JSON) with formula version; and',
    'peak_dasha_periods/weak_dasha_periods (high/low-condition dasha windows). Filters: graha,',
    'ayanamsha_id. Bounded to 50 rows with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    graha:        { type: 'string', description: 'Filter by graha. Omit for all.' },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    limit:        { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
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
    bulk_context: { pre_fetch_priority: 55, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const graha        = args['graha'] ? String(args['graha']) : null
    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (graha)        { filters.push(`graha = $${p++}`); params.push(graha) }
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT graha, ayanamsha_id, dignity_d1, dignity_score_d1, varga_dignity_spread,
             varga_dignity_composite, avastha_baladi, avastha_jagradadi, avastha_deeptaadi,
             avastha_lajjitaadi, avastha_sayanadi, motion_state, speed_degrees_per_day,
             is_retrograde, combustion_arc_from_sun, is_combust, is_deeply_combust,
             naisargika_relation, tatkalika_relation, panchadha_relation, graha_yuddha_with,
             graha_yuddha_result, condition_score, condition_formula_version,
             condition_score_breakdown, peak_dasha_periods, weak_dasha_periods, computed_at
      FROM ga_condition_composite
      WHERE ${where}
      ORDER BY graha, ayanamsha_id
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM ga_condition_composite WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { graha, ayanamsha_id, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No condition-composite rows matched (graha=${graha ?? 'any'}, ayanamsha_id=${ayanamsha_id ?? 'any'}).` }
            : {}),
          provenance: { tables: ['ga_condition_composite'], source: 'L1 Gaṇita unified planetary-condition rollup; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
