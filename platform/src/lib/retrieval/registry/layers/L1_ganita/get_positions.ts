/**
 * L1 retrieval: graha positions
 * Covers: graha_position, upagraha_position, aprakasha_position
 * Tool: marsys://tool/L1/get_positions
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const getPositionsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_positions',
  type: 'tool',
  layer: 'L1',
  name: 'get_positions',
  description:
    'Retrieve Gaṇita graha positions for a chart. Returns sidereal longitudes, rashi, nakshatra, pada, ' +
    'retrograde status, and combust status for all grahas including upagrahas and aprakasha (dark) planets. ' +
    'Each row carries fact_id for Bodha constituent_facts_array back-reference. ' +
    'Covers fact_categories: graha_position, upagraha_position, aprakasha_position.',
  input_schema: {
    chart_id: {
      type: 'string',
      description: 'UUID of the chart (<chart_uuid> from asset_registry)',
      required: true,
    },
    ayanamsha_id: {
      type: 'string',
      description: 'Filter by ayanamsha_id (e.g. LAHIRI). Omit for all ayanamshas.',
    },
    categories: {
      type: 'array',
      description: 'Optional list of fact_categories to include. Defaults to all position categories.',
      items: { type: 'string', enum: ['graha_position', 'upagraha_position', 'aprakasha_position'] },
    },
    offset: { type: 'number', description: 'Pagination offset (default 0)', default: 0 },
    limit:  { type: 'number', description: 'Rows per page (default 200, max 1000)', default: 200 },
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
    bulk_context: { pre_fetch_priority: 90, always_include: true },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 200, 1000)
      const offset  = (args.offset as number) ?? 0
      const categories = (args.categories as string[]) ?? ['graha_position', 'upagraha_position', 'aprakasha_position']

      const params: unknown[] = [chartId, categories, limit, offset]
      let sql = `
        SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
        FROM chart_facts
        WHERE chart_id = $1
          AND fact_category = ANY($2::text[])
      `
      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }
      sql += ` ORDER BY ayanamsha_id, fact_category, fact_key LIMIT $3 OFFSET $4`

      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: { chart_id: chartId, categories, rows: result.rows ?? [], total: result.rows?.length ?? 0 },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
