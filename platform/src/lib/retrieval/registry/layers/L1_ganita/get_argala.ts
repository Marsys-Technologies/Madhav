/**
 * L1 retrieval: argala (intervention analysis)
 * Covers: argala_natal_matrix, virodha_argala_natal_matrix
 * Tool: marsys://tool/L1/get_argala
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const getArgalaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_argala',
  type: 'tool',
  layer: 'L1',
  name: 'get_argala',
  description:
    'Retrieve Argala (intervention) and Virodha Argala (obstruction) matrices for a chart. ' +
    'Argala measures which grahas intervene in the results of each house via 2nd/4th/5th/11th placements; ' +
    'Virodha Argala measures which grahas block those interventions via 3rd/12th/10th/3rd (opposite). ' +
    'These are large matrices covering all 5 ayanamshas × all house × graha combos. ' +
    'Use offset/limit for pagination. Covers: argala_natal_matrix, virodha_argala_natal_matrix.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    type:         { type: 'string', description: 'argala | virodha_argala. Omit for both.', enum: ['argala', 'virodha_argala'] },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 500 },
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
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 60, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 500, 2000)
      const offset  = (args.offset as number) ?? 0

      let categories = ['argala_natal_matrix', 'virodha_argala_natal_matrix']
      if (args.type === 'argala')         categories = ['argala_natal_matrix']
      if (args.type === 'virodha_argala') categories = ['virodha_argala_natal_matrix']

      const params: unknown[] = [chartId, categories, limit, offset]
      let sql = `
        SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
        FROM chart_facts
        WHERE chart_id = $1 AND fact_category = ANY($2::text[])
      `
      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }
      sql += ` ORDER BY ayanamsha_id, fact_key LIMIT $3 OFFSET $4`

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
