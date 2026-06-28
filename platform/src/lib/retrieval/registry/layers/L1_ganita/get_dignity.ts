/**
 * L1 retrieval: dignity per varga + functional classification
 * Covers: graha_dignity_per_varga, graha_effective_dignity_modified_by_aspects,
 *         graha_sign_attributes, graha_vargottama_amplification_factor,
 *         vargottama_per_varga, graha_functional_class_per_ascendant
 * Tool: marsys://tool/L1/get_dignity
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const DIGNITY_CATEGORIES = [
  'graha_dignity_per_varga', 'graha_effective_dignity_modified_by_aspects',
  'graha_sign_attributes', 'graha_vargottama_amplification_factor',
  'vargottama_per_varga', 'graha_functional_class_per_ascendant',
]

export const getDignityCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_dignity',
  type: 'tool',
  layer: 'L1',
  name: 'get_dignity',
  description:
    'Retrieve graha dignity and varga-level classification for a chart. ' +
    'Includes: dignity per varga (exalted/own/friend/neutral/enemy/debilitated across D1–D60), ' +
    'effective dignity modified by aspects (neechabhanga, rashi dristi cancellations etc.), ' +
    'sign attributes (movable/fixed/dual, element, gender, etc.), ' +
    'vargottama amplification factor (0 / 0.20 / 0.50 based on how many vargas share same rashi), ' +
    'vargottama flag per varga, and functional class per ascendant ' +
    '(benefic/malefic/neutral/yoga-karaka for the native\'s Aries lagna). ' +
    'Covers 6 fact_categories.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    varga:        { type: 'string', description: 'Filter to one varga (e.g. D1, D9, D10). Omit for all.' },
    categories:   { type: 'array', description: 'Explicit category list.', items: { type: 'string' } },
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
    bulk_context: { pre_fetch_priority: 80, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 500, 2000)
      const offset     = (args.offset as number) ?? 0
      const categories = (args.categories as string[]) ?? DIGNITY_CATEGORIES

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
      if (args.varga) {
        sql += ` AND fact_key ILIKE $${params.length + 1}`
        params.push(`%${args.varga as string}%`)
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
