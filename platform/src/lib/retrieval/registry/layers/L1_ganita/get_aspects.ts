/**
 * L1 retrieval: aspects, conjunctions, lord placements
 * Covers: aspect_parashari_given, aspect_parashari_received, aspect_parashari_per_varga,
 *         aspect_jaimini, aspect_jaimini_per_varga, aspect_matrix_summary, aspect_tajik,
 *         conjunction_within_orb, conjunction_per_varga,
 *         lord_aspects_lord_per_varga, lord_in_house_per_varga
 * Tool: marsys://tool/L1/get_aspects
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const ASPECT_CATEGORIES = [
  'aspect_parashari_given', 'aspect_parashari_received', 'aspect_parashari_per_varga',
  'aspect_jaimini', 'aspect_jaimini_per_varga', 'aspect_matrix_summary', 'aspect_tajik',
  'conjunction_within_orb', 'conjunction_per_varga',
  'lord_aspects_lord_per_varga', 'lord_in_house_per_varga',
]

export const getAspectsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_aspects',
  type: 'tool',
  layer: 'L1',
  name: 'get_aspects',
  description:
    'Retrieve aspect and conjunction data for a chart: Parashari aspects (given/received/per-varga), ' +
    'Jaimini rashi aspects (natal + per-varga), Tajik aspects (Itthasala/Ishrafa etc.), ' +
    'conjunction matrix (within-orb + per-varga), lord-aspects-lord per varga, ' +
    'and lord-in-house per varga (sign lord placements across all divisionals). ' +
    'Covers 11 aspect-related fact_categories.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    tradition:    { type: 'string', description: 'Filter by tradition: parashari | jaimini | tajik. Omit for all.', enum: ['parashari', 'jaimini', 'tajik'] },
    categories:   { type: 'array',  description: 'Subset of aspect categories.', items: { type: 'string' } },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 1000 },
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
  register: { reader_label: 'Consulting the chart — House & lordships' },
  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 80, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 1000, 5000)
      const offset     = (args.offset as number) ?? 0

      let categories = (args.categories as string[]) ?? ASPECT_CATEGORIES
      if (args.tradition) {
        const t = args.tradition as string
        categories = categories.filter(c => c.includes(t))
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
