/**
 * L1 retrieval: Tara Bala and Chandra Bala
 * Covers: tara_bala_natal_baseline, chandra_bala_natal_baseline
 * Tool: marsys://tool/L1/get_tara_chandra_bala
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const getTaraChanndraBalaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_tara_chandra_bala',
  type: 'tool',
  layer: 'L1',
  name: 'get_tara_chandra_bala',
  description:
    'Retrieve Tara Bala and Chandra Bala natal baselines for a chart. ' +
    'Tara Bala: nakshatra-based strength computed as the count-position of each ' +
    'nakshatra from the natal Moon nakshatra (Purva Bhadrapada for the native); ' +
    'odd-counted nakshatras (1,3,5,7,9) are favorable, even unfavorable. ' +
    'Chandra Bala: Moon\'s positional strength relative to each graha by rashi distance; ' +
    'the Moon in a friend/own/exalted rashi gains full Chandra Bala. ' +
    'Both are inputs to overall Panchanga-based timing considerations. ' +
    'Covers 2 fact_categories.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 200 },
  },
  required_inputs: ['chart_id'],
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 60, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 200, 1000)
      const offset  = (args.offset as number) ?? 0

      const params: unknown[] = [chartId, ['tara_bala_natal_baseline', 'chandra_bala_natal_baseline'], limit, offset]
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
        content: { chart_id: chartId, rows: result.rows ?? [], total: result.rows?.length ?? 0 },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
