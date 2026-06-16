/**
 * L1 retrieval: esoteric / sensitive points
 * Covers: all esoteric_point_* (13 sub-categories), bhrigu_nadi_point,
 *         lal_kitab_special_point, maharsi_specific_point, midpoint,
 *         saham_position, saturn_derived_point, nakshatra_pada_sensitive
 * Tool: marsys://tool/L1/get_sensitive_points
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const SP_CATEGORIES = [
  'esoteric_point_avayogi', 'esoteric_point_bhrigu_bindu', 'esoteric_point_brahma',
  'esoteric_point_chatushphuta', 'esoteric_point_mrityu', 'esoteric_point_panchasphuta',
  'esoteric_point_pranapada_sphuta', 'esoteric_point_shiva', 'esoteric_point_sri_yantra_position',
  'esoteric_point_trikona_dasha_sphuta', 'esoteric_point_trisphuta', 'esoteric_point_vishnu',
  'esoteric_point_yogi', 'bhrigu_nadi_point', 'lal_kitab_special_point',
  'maharsi_specific_point', 'midpoint', 'saham_position', 'saturn_derived_point',
  'nakshatra_pada_sensitive',
]

export const getSensitivePointsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_sensitive_points',
  type: 'tool',
  layer: 'L1',
  name: 'get_sensitive_points',
  description:
    'Retrieve esoteric and sensitive mathematical points for a chart. ' +
    'Includes: 13 tradition-specific esoteric points (Yogi/Avayogi, Brahma/Vishnu/Shiva, ' +
    'Sri Yantra position, Mrityu Sphuta, Trikona Dasha Sphuta, Trisphuta, Panchasphuta, ' +
    'Pranapada, Chatushphuta, Bhrigu Bindu), ' +
    'Bhrigu Nadi point, 100 Lal Kitab special points, ' +
    'Maharṣi-specific points, midpoints (all graha pairs), ' +
    '2800 Arabic Parts (Sahams) across all ayanamshas, Saturn-derived points, ' +
    'and nakshatra-pada sensitive degrees. ' +
    'Covers 20 fact_categories (~7,400 rows).',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    tradition:    {
      type: 'string',
      description: 'Filter by tradition: esoteric | bhrigu | lal_kitab | maharsi | arabic_parts | saturn.',
      enum: ['esoteric', 'bhrigu', 'lal_kitab', 'maharsi', 'arabic_parts', 'saturn'],
    },
    categories:   { type: 'array', description: 'Explicit category list.', items: { type: 'string' } },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 500 },
  },
  required_inputs: ['chart_id'],
  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 65, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 500, 2000)
      const offset  = (args.offset as number) ?? 0

      let categories = (args.categories as string[]) ?? SP_CATEGORIES
      if (args.tradition) {
        const t = args.tradition as string
        const tMap: Record<string, string[]> = {
          esoteric:     SP_CATEGORIES.filter(c => c.startsWith('esoteric_point')),
          bhrigu:       ['bhrigu_nadi_point', 'esoteric_point_bhrigu_bindu'],
          lal_kitab:    ['lal_kitab_special_point'],
          maharsi:      ['maharsi_specific_point'],
          arabic_parts: ['saham_position'],
          saturn:       ['saturn_derived_point'],
        }
        categories = tMap[t] ?? categories
      }

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
