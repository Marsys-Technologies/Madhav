/**
 * L1 retrieval: ashtakavarga
 * Covers: ashtakavarga_bindu, ashtakavarga_anubindu,
 *         ashtakavarga_pinda_bhinna, ashtakavarga_pinda_sarva, ashtakavarga_pinda_sodhita
 * Tool: marsys://tool/L1/get_ashtakavarga
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const AV_CATEGORIES = [
  'ashtakavarga_bindu', 'ashtakavarga_anubindu',
  'ashtakavarga_pinda_bhinna', 'ashtakavarga_pinda_sarva', 'ashtakavarga_pinda_sodhita',
]

export const getAshtakavargaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_ashtakavarga',
  type: 'tool',
  layer: 'L1',
  name: 'get_ashtakavarga',
  description:
    'Retrieve Ashtakavarga data for a chart: individual bindus (per graha per house), ' +
    'anubindus (trikona/ekadhipatya reduced), and Pinda Bala (Bhinna, Sarva, Sodhita). ' +
    'Bindus range 0–8 per house per planet; sarva ashtakavarga totals per house; ' +
    'sodhita = after trikona shodhan reduction. ' +
    'Covers: ashtakavarga_bindu, ashtakavarga_anubindu, ashtakavarga_pinda_bhinna, ' +
    'ashtakavarga_pinda_sarva, ashtakavarga_pinda_sodhita.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    categories:   { type: 'array',  description: 'Subset of AV categories.', items: { type: 'string' } },
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
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 70, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 500, 2000)
      const offset     = (args.offset as number) ?? 0
      const categories = (args.categories as string[]) ?? AV_CATEGORIES

      const params: unknown[] = [chartId, categories, limit, offset]
      let sql = `
        SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_numeric,
               fact_value_text, fact_tags, epistemic_tier, source_asset_id
        FROM chart_facts
        WHERE chart_id = $1 AND fact_category = ANY($2::text[])
      `
      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }
      sql += ` ORDER BY fact_category, ayanamsha_id, fact_key LIMIT $3 OFFSET $4`

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
