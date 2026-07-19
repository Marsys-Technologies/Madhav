/**
 * L1 retrieval: divisional charts (chart_divisionals)
 * Source: chart_divisionals table (not chart_facts)
 * Tool: marsys://tool/L1/get_divisionals
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const getDivisionalsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_divisionals',
  type: 'tool',
  layer: 'L1',
  name: 'get_divisionals',
  description:
    'Retrieve divisional chart (varga) placements for a chart from the chart_divisionals table. ' +
    'Contains graha positions in each of the 16 standard vargas (D1–D60 including D1, D2, D3, D4, D5, ' +
    'D6, D7, D8, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60). ' +
    'Each row: graha, varga, sign, sign_number, degree_in_sign, house, vargottama. ' +
    'Contains a large, paginated row set per chart.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    varga:        { type: 'string', description: 'Varga code (e.g. D9, D10, D12). Omit for all.' },
    graha:        { type: 'string', description: 'Graha abbreviation (e.g. SU, MO). Omit for all.' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 300 },
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
    bulk_context: { pre_fetch_priority: 80, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 300, 2000)
      const offset  = (args.offset as number) ?? 0

      const params: unknown[] = [chartId, limit, offset]
      let sql = `SELECT * FROM chart_divisionals WHERE chart_id = $1`

      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }
      if (args.varga) {
        sql += ` AND varga = $${params.length + 1}`
        params.push(args.varga as string)
      }
      if (args.graha) {
        sql += ` AND graha = $${params.length + 1}`
        params.push(args.graha as string)
      }
      sql += ` ORDER BY varga, ayanamsha_id, graha LIMIT $2 OFFSET $3`

      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: { chart_id: chartId, source_table: 'chart_divisionals', rows: result.rows ?? [], total: result.rows?.length ?? 0 },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
