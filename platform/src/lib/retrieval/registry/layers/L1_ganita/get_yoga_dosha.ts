/**
 * L1 retrieval: yoga and dosha firings
 * Covers: yoga_fires, yoga_label, dosha_fires, dosha_label, bhadra_flag, panchaka_flag
 * Tool: marsys://tool/L1/get_yoga_dosha
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const YD_CATEGORIES = ['yoga_fires', 'yoga_label', 'dosha_fires', 'dosha_label', 'bhadra_flag', 'panchaka_flag']

export const getYogaDoshaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_yoga_dosha',
  type: 'tool',
  layer: 'L1',
  name: 'get_yoga_dosha',
  description:
    'Retrieve yoga and dosha data for a chart: yoga_fires (predicate firings with activating factors), ' +
    'yoga_label (canonical name and tradition), dosha_fires (affliction firings), dosha_label, ' +
    'bhadra_flag, and panchaka_flag. ' +
    'Every yoga/dosha firing carries its constituent grahas and fact_id for Bodha back-reference. ' +
    'Weak-tail signals (low-salience yogas) are included — strength is a column, not a gate. ' +
    'Covers 6 fact_categories.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    type:         { type: 'string', description: 'yoga | dosha | flag. Omit for all.', enum: ['yoga', 'dosha', 'flag'] },
    categories:   { type: 'array',  description: 'Subset of categories.', items: { type: 'string' } },
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
    bulk_context: { pre_fetch_priority: 88, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 500, 2000)
      const offset     = (args.offset as number) ?? 0

      let categories = (args.categories as string[]) ?? YD_CATEGORIES
      if (args.type === 'yoga')  categories = categories.filter(c => c.startsWith('yoga') || c === 'bhadra_flag')
      if (args.type === 'dosha') categories = categories.filter(c => c.startsWith('dosha'))
      if (args.type === 'flag')  categories = categories.filter(c => c.endsWith('_flag'))

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
