/**
 * L1 retrieval: Sade Sati and Saturn period family
 * Covers: sade_sati_cycle, sade_sati_phase, sade_sati_phase_quarter,
 *         sade_sati_modifier_overlay, sade_sati_cancellation_check,
 *         sade_sati_concurrent_dasha_overlay, sade_sati_downstream_cross_reference,
 *         sade_sati_saturn_retrograde_subset,
 *         janma_shani_period, anumukha_shani_period, ardha_ashtama_shani_period,
 *         ashtama_shani_period, dhaiya_period, vishakha_shani_period, kantaka_shani_period
 * Tool: marsys://tool/L1/get_sade_sati
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const SS_CATEGORIES = [
  'sade_sati_cycle', 'sade_sati_phase', 'sade_sati_phase_quarter',
  'sade_sati_modifier_overlay', 'sade_sati_cancellation_check',
  'sade_sati_concurrent_dasha_overlay', 'sade_sati_downstream_cross_reference',
  'sade_sati_saturn_retrograde_subset',
  'janma_shani_period', 'anumukha_shani_period', 'ardha_ashtama_shani_period',
  'ashtama_shani_period', 'dhaiya_period', 'vishakha_shani_period', 'kantaka_shani_period',
]

export const getSadeSatiCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_sade_sati',
  type: 'tool',
  layer: 'L1',
  name: 'get_sade_sati',
  description:
    'Retrieve the complete Sade Sati and Saturn transit period family for a chart. ' +
    'Includes: Sade Sati cycles (all historical + future), phase breakdowns (peak/rising/setting), ' +
    'quarter-phase granularity, modifier overlays (dignity/aspect cancellations), ' +
    'cancellation checks, concurrent dasha overlays (which dasha runs simultaneously), ' +
    'downstream cross-references, Saturn retrograde subsets, ' +
    'and all related Saturn transit period types ' +
    '(Janma Shani, Anumukha Shani, Ardha-Ashtama Shani, Ashtama Shani, Dhaiya, Vishakha, Kantaka). ' +
    'Covers 15 fact_categories (a large row set per chart).',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    categories:   { type: 'array',  description: 'Subset of Sade Sati categories.', items: { type: 'string' } },
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
    bulk_context: { pre_fetch_priority: 82, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 500, 2000)
      const offset     = (args.offset as number) ?? 0
      const categories = (args.categories as string[]) ?? SS_CATEGORIES

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
