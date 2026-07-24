/**
 * L1 retrieval: panchanga (five limbs of time + time windows)
 * Covers: all 40 panchanga_* fact_categories
 * Tool: marsys://tool/L1/get_panchanga
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

// Exported so other capabilities (e.g. chart_facts_query's category-alias resolution, which
// expands the bare umbrella term 'panchanga' to this family) can reuse it without duplication.
export const PANCHANGA_CATEGORIES = [
  'panchanga_abhijit_muhurta', 'panchanga_agni_vasa', 'panchanga_brahma_muhurta',
  'panchanga_calendrical', 'panchanga_choghadiya_birth', 'panchanga_disha_shul',
  'panchanga_durmuhurta', 'panchanga_godhuli_muhurta', 'panchanga_gulika_kalam',
  'panchanga_hora_birth', 'panchanga_karana', 'panchanga_krakaca',
  'panchanga_madhyahna_sandhya', 'panchanga_nakshatra_moon', 'panchanga_nakshatra_shoonya_rashi',
  'panchanga_nishita_kala', 'panchanga_panchaka_classification', 'panchanga_pratah_sandhya',
  'panchanga_rahu_kalam', 'panchanga_sashtighati', 'panchanga_sayam_sandhya',
  'panchanga_solar_context', 'panchanga_special_yoga_combinations', 'panchanga_sun_moon_dynamics',
  'panchanga_tithi', 'panchanga_tithi_shoonya_rashi', 'panchanga_vara',
  'panchanga_varjyam', 'panchanga_vijaya_muhurta', 'panchanga_visha_ghati',
  'panchanga_yamaganda_kalam', 'panchanga_yamakantaka', 'panchanga_yoga',
]

export const getPanchangaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_panchanga',
  type: 'tool',
  layer: 'L1',
  name: 'get_panchanga',
  description:
    'Retrieve Pañcāṅga (five-limb almanac) data for a chart\'s birth moment: ' +
    'the 5 classical limbs (tithi, vara, nakshatra, yoga, karana), solar context, ' +
    'all 7 auspicious/inauspicious time windows (Rahu Kalam, Gulika Kalam, Yamaganda, ' +
    'Abhijit Muhurta, Brahma Muhurta, Durmuhurta, Vijaya Muhurta), ' +
    'Choghadiya classification, hora at birth, sandhya timings, Panchaka classification, ' +
    'and special yoga combinations (Amrita Siddhi, Sarvartha Siddhi, etc.). ' +
    'Covers 33 panchanga fact_categories (FORENSIC-anchored: Purva Bhadrapada nakshatra, ' +
    'Shukla Tritiya tithi, Ravivara vara, Shiva yoga, Garaja karana).',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    limb:         {
      type: 'string',
      description: 'Filter to one panchanga domain: tithi|vara|nakshatra|yoga|karana|muhurta|time_window|special.',
      enum: ['tithi', 'vara', 'nakshatra', 'yoga', 'karana', 'muhurta', 'time_window', 'special'],
    },
    categories:   { type: 'array', description: 'Explicit list of panchanga categories.', items: { type: 'string' } },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 200 },
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
    bulk_context: { pre_fetch_priority: 88, always_include: true },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 200, 1000)
      const offset  = (args.offset as number) ?? 0

      let categories = (args.categories as string[]) ?? PANCHANGA_CATEGORIES
      if (args.limb) {
        const limb = args.limb as string
        const limbMap: Record<string, string[]> = {
          tithi:       ['panchanga_tithi', 'panchanga_tithi_shoonya_rashi'],
          vara:        ['panchanga_vara'],
          nakshatra:   ['panchanga_nakshatra_moon', 'panchanga_nakshatra_shoonya_rashi'],
          yoga:        ['panchanga_yoga', 'panchanga_special_yoga_combinations'],
          karana:      ['panchanga_karana'],
          muhurta:     ['panchanga_abhijit_muhurta', 'panchanga_brahma_muhurta', 'panchanga_durmuhurta', 'panchanga_godhuli_muhurta', 'panchanga_vijaya_muhurta'],
          time_window: ['panchanga_rahu_kalam', 'panchanga_gulika_kalam', 'panchanga_yamaganda_kalam', 'panchanga_yamakantaka', 'panchanga_varjyam', 'panchanga_visha_ghati', 'panchanga_sashtighati', 'panchanga_krakaca', 'panchanga_choghadiya_birth', 'panchanga_hora_birth', 'panchanga_agni_vasa', 'panchanga_disha_shul'],
          special:     ['panchanga_panchaka_classification', 'panchanga_sun_moon_dynamics', 'panchanga_solar_context', 'panchanga_calendrical', 'panchanga_pratah_sandhya', 'panchanga_madhyahna_sandhya', 'panchanga_sayam_sandhya', 'panchanga_nishita_kala'],
        }
        categories = limbMap[limb] ?? categories
      }

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
