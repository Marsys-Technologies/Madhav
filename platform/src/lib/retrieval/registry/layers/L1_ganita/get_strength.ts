/**
 * L1 retrieval: graha strength (shadbala, vimsopaka, composite, ishta/kashta)
 * Covers: graha_shadbala_*, graha_vimsopaka_*, vimsopaka_bala_per_graha,
 *         graha_saptavargaja_bala_component, graha_ishta_phala, graha_kashta_phala,
 *         pranic_strength_per_graha, graha_in_house_composite_strength,
 *         graha_composite_state_classification, graha_special_state_rollup,
 *         graha_yoga_karaka_flag, graha_tri_deva_role_strength
 * Tool: marsys://tool/L1/get_strength
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const STRENGTH_CATEGORIES = [
  'graha_shadbala_cheshta', 'graha_shadbala_dig', 'graha_shadbala_drik',
  'graha_shadbala_kala', 'graha_shadbala_naisargika', 'graha_shadbala_sthana',
  'graha_shadbala_total', 'graha_vimsopaka_dasavarga', 'graha_vimsopaka_saptavarga',
  'graha_vimsopaka_shadvarga', 'graha_vimsopaka_shodasavarga', 'vimsopaka_bala_per_graha',
  'graha_saptavargaja_bala_component', 'graha_ishta_phala', 'graha_kashta_phala',
  'pranic_strength_per_graha', 'graha_in_house_composite_strength',
  'graha_composite_state_classification', 'graha_special_state_rollup',
  'graha_yoga_karaka_flag', 'graha_tri_deva_role_strength',
]

export const getStrengthCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_strength',
  type: 'tool',
  layer: 'L1',
  name: 'get_strength',
  description:
    'Retrieve all graha strength metrics for a chart: Shadbala (6 components + total), ' +
    'Vimsopaka Bala (4 varga groupings), Saptavargaja Bala, Ishta/Kashta Phala, Pranic strength, ' +
    'composite in-house strength, composite state classification, special state rollup (exalted/debilitated/combust etc.), ' +
    'yoga-karaka flag, and Tri-deva role strength. ' +
    'Every row carries fact_id for Bodha salience computation via salience_formula_v1. ' +
    'Covers 21 strength-related fact_categories.',
  input_schema: {
    chart_id: {
      type: 'string', description: 'Chart UUID', required: true,
    },
    ayanamsha_id: {
      type: 'string', description: 'Filter by ayanamsha_id. Omit for all.',
    },
    categories: {
      type: 'array',
      description: 'Subset of strength categories (default: all 21).',
      items: { type: 'string' },
    },
    graha_key: {
      type: 'string',
      description: 'Filter to one graha (e.g. "SU" for Sun). Omit for all.',
    },
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
    bulk_context: { pre_fetch_priority: 85, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 500, 2000)
      const offset     = (args.offset as number) ?? 0
      const categories = (args.categories as string[]) ?? STRENGTH_CATEGORIES

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
      if (args.graha_key) {
        sql += ` AND fact_key ILIKE $${params.length + 1}`
        params.push(`${args.graha_key as string}%`)
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
