/**
 * L1 retrieval: graha avasthas
 * Covers: graha_avastha_baladi, graha_avastha_deepta, graha_avastha_jagrad,
 *         graha_avastha_lajjitadi, graha_avastha_lifetime_exposure_summary,
 *         graha_avastha_sayanadi
 * Tool: marsys://tool/L1/get_avasthas
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const AVASTHA_CATEGORIES = [
  'graha_avastha_baladi', 'graha_avastha_deepta', 'graha_avastha_jagrad',
  'graha_avastha_lajjitadi', 'graha_avastha_lifetime_exposure_summary', 'graha_avastha_sayanadi',
]

export const getAvasthsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_avasthas',
  type: 'tool',
  layer: 'L1',
  name: 'get_avasthas',
  description:
    'Retrieve graha Avastha (state) classifications for a chart. ' +
    'Includes: Baladi Avastha (childhood/youth/middle-age/old-age/dead per degree position), ' +
    'Deepta (illuminated) Avastha (moolatrikona-based illumination state), ' +
    'Jagrad (awake) Avastha (day/night cycle state), ' +
    'Lajjitadi Avastha (6 states: lajjita/gaurava/kshudha/trushita/mudita/kshobhita ' +
    'based on co-tenancy patterns), ' +
    'Lifetime Exposure Summary (probability of each avastha across a lifetime of dashas), ' +
    'and Sayanadi Avastha (12-fold sleeping/waking/drunk/angry etc. classification). ' +
    'Covers 6 avastha fact_categories.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    categories:   { type: 'array', description: 'Subset of avastha categories.', items: { type: 'string' } },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 300 },
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
    bulk_context: { pre_fetch_priority: 72, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 300, 1000)
      const offset     = (args.offset as number) ?? 0
      const categories = (args.categories as string[]) ?? AVASTHA_CATEGORIES

      const filterParams: unknown[] = [chartId, categories]
      let where = `WHERE chart_id = $1 AND fact_category = ANY($2::text[])`
      if (args.ayanamsha_id) {
        where += ` AND ayanamsha_id = $${filterParams.length + 1}`
        filterParams.push(args.ayanamsha_id as string)
      }
      const pageSql = `
        SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
        FROM chart_facts
        ${where}
        ORDER BY fact_category, ayanamsha_id, fact_key
        LIMIT $${filterParams.length + 1} OFFSET $${filterParams.length + 2}
      `
      const countSql = `SELECT COUNT(*)::text AS total FROM chart_facts ${where}`

      const result = await query<Record<string, unknown>>(pageSql, [...filterParams, limit, offset])
      const countResult = await query<{ total: string }>(countSql, filterParams)
      return {
        content: { chart_id: chartId, categories, rows: result.rows ?? [], total: Number(countResult.rows?.[0]?.total ?? 0) },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
