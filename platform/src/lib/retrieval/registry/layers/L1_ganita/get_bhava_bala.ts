/**
 * L1 retrieval: bhava bala (house strength)
 * Covers: bhava_bala_aspectual, bhava_bala_directional, bhava_bala_lord,
 *         bhava_bala_occupant, bhava_bala_positional, bhava_bala_temporal,
 *         bhava_bala_total_extended, house_bhava_bala_subscore, house_bhava_bala_total,
 *         house_strength_classification_rollup
 * Tool: marsys://tool/L1/get_bhava_bala
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const BB_CATEGORIES = [
  'bhava_bala_aspectual', 'bhava_bala_directional', 'bhava_bala_lord',
  'bhava_bala_occupant', 'bhava_bala_positional', 'bhava_bala_temporal',
  'bhava_bala_total_extended', 'house_bhava_bala_subscore', 'house_bhava_bala_total',
  'house_strength_classification_rollup',
]

export const getBhavaBalaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_bhava_bala',
  type: 'tool',
  layer: 'L1',
  name: 'get_bhava_bala',
  description:
    'Retrieve Bhava Bala (house strength) for a chart: 6 component scores ' +
    '(aspectual, directional, lord, occupant, positional, temporal), total extended, ' +
    'per-house subscore breakdowns, and house strength classification rollup ' +
    '(strong/average/weak per bhava). ' +
    'Covers 10 bhava bala fact_categories.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    house_number: { type: 'number', description: 'Filter to one bhava (1–12). Omit for all.' },
    categories:   { type: 'array',  description: 'Subset of bhava bala categories.', items: { type: 'string' } },
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
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Strengths & dignities' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 75, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 500, 2000)
      const offset     = (args.offset as number) ?? 0
      const categories = (args.categories as string[]) ?? BB_CATEGORIES

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
      if (args.house_number) {
        sql += ` AND fact_key ILIKE $${params.length + 1}`
        params.push(`%H${args.house_number as number}%`)
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
