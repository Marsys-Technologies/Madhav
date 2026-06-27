/**
 * L1 retrieval: karakas, KP, Jaimini placements
 * Covers: karaka_chara_position, karakamsa_position, swamsa_position, arudha_pada,
 *         karaka_house_lord_overlap_flag, karakatva_strength_per_significance,
 *         kp_cuspal_significators, kp_ruling_planets_natal,
 *         jaimini_tri_deva_role_per_graha
 * Tool: marsys://tool/L1/get_karakas
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const KARAKA_CATEGORIES = [
  'karaka_chara_position', 'karakamsa_position', 'swamsa_position', 'arudha_pada',
  'karaka_house_lord_overlap_flag', 'karakatva_strength_per_significance',
  'kp_cuspal_significators', 'kp_ruling_planets_natal', 'jaimini_tri_deva_role_per_graha',
]

export const getKarakasCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_karakas',
  type: 'tool',
  layer: 'L1',
  name: 'get_karakas',
  description:
    'Retrieve Jaimini karaka and KP (Krishnamurti Paddhati) data for a chart. ' +
    'Includes: Chara Karaka positions (AK/AmK/BK/MK/PK/GK/DK — the 7 temporal significators), ' +
    'Karakamsa position (rashi/house where AK sits in Navamsha), Swamsa position, ' +
    '285 Arudha Padas (A1–A12 across 5 ayanamshas and divisionals), ' +
    'Karaka-house-lord overlap flags (e.g. AK also lords the 10th house), ' +
    'Karakatva strength per significator (how strongly each graha signifies its karakatvas), ' +
    'KP cuspal significators (Star lord + Sub lord + Sub-sub for each of 12 cusps), ' +
    'KP ruling planets for the natal moment, ' +
    'and Jaimini Tri-Deva role (Brahma/Vishnu/Maheshvara graha identification). ' +
    'Covers 9 fact_categories.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    system:       { type: 'string', description: 'Filter by system: jaimini | kp. Omit for all.', enum: ['jaimini', 'kp'] },
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
    bulk_context: { pre_fetch_priority: 82, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 500, 2000)
      const offset  = (args.offset as number) ?? 0

      let categories = (args.categories as string[]) ?? KARAKA_CATEGORIES
      if (args.system === 'jaimini') {
        categories = categories.filter(c => c.startsWith('karaka') || c.startsWith('jaimini') || ['swamsa_position', 'karakamsa_position', 'arudha_pada', 'karakatva_strength_per_significance'].includes(c))
      }
      if (args.system === 'kp') {
        categories = categories.filter(c => c.startsWith('kp'))
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
