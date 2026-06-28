/**
 * L1 retrieval: eclipse proximity and misc natal flags
 * Covers: eclipse_proximity_natal
 * Tool: marsys://tool/L1/get_eclipse_flags
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const getEclipseFlagsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_eclipse_flags',
  type: 'tool',
  layer: 'L1',
  name: 'get_eclipse_flags',
  description:
    'Retrieve eclipse proximity data for a chart\'s birth moment. ' +
    'Indicates how close the birth was to a solar or lunar eclipse ' +
    '(days before/after, eclipse type, penumbral vs umbral), ' +
    'which has classical significance for the native\'s temperament and life patterns ' +
    '(eclipse-born natives often have Rahu/Ketu highlighted). ' +
    'Covers: eclipse_proximity_natal.',
  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID', required: true },
    offset:   { type: 'number', default: 0 },
    limit:    { type: 'number', default: 20 },
  },
  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 55, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 20, 100)
      const offset  = (args.offset as number) ?? 0

      const result = await query<Record<string, unknown>>(
        `SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
                fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
         FROM chart_facts
         WHERE chart_id = $1 AND fact_category = 'eclipse_proximity_natal'
         ORDER BY ayanamsha_id, fact_key LIMIT $2 OFFSET $3`,
        [chartId, limit, offset],
      )
      return {
        content: { chart_id: chartId, rows: result.rows ?? [], total: result.rows?.length ?? 0 },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
