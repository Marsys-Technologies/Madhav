/**
 * L1 retrieval: Tajika Varshaphal
 * Covers: tajik_hadda_lord, tajik_triraashipathi, tajik_vargottama_specific
 *         (plus aspect_tajik covered by get_aspects)
 *         and l1_tajik_varsha_year_lords (separate table)
 * Tool: marsys://tool/L1/get_tajik
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const TAJIK_CF_CATEGORIES = ['tajik_hadda_lord', 'tajik_triraashipathi', 'tajik_vargottama_specific']

export const getTajikCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_tajik',
  type: 'tool',
  layer: 'L1',
  name: 'get_tajik',
  description:
    'Retrieve Tājika Varṣaphal (Persian/Tajik annual chart) data for a chart. ' +
    'From chart_facts: Tajik Hadda lord (Ptolemaic term lord for the degree), ' +
    'Triraashipathi (annual chart ruler — lord of the sign the Sun transits at birthday), ' +
    'and Tajik Vargottama specific. ' +
    'From l1_tajik_varsha_year_lords table: all annual Solar Return year lord combinations ' +
    '(Muntha, Varsha Lord, TrirasheePathi) across available years. ' +
    'Includes FORENSIC-exact Muntha = Libra/7H/Venus. ' +
    'Covers 3 fact_categories + l1_tajik_varsha_year_lords table.',
  input_schema: {
    chart_id:       { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id:   { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    include_varsha: {
      type: 'boolean',
      description: 'Include l1_tajik_varsha_year_lords rows (default true)',
      default: true,
    },
    year_min:       { type: 'number', description: 'Filter varsha lords to year >= this.' },
    year_max:       { type: 'number', description: 'Filter varsha lords to year <= this.' },
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
    bulk_context: { pre_fetch_priority: 68, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId       = args.chart_id as string
      const limit         = Math.min((args.limit as number) ?? 200, 1000)
      const offset        = (args.offset as number) ?? 0
      const includeVarsha = (args.include_varsha as boolean) ?? true

      const params: unknown[] = [chartId, TAJIK_CF_CATEGORIES, limit, offset]
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

      const cfResult = await query<Record<string, unknown>>(sql, params)
      const rows: Record<string, unknown>[] = cfResult.rows ?? []

      if (includeVarsha) {
        const vParams: unknown[] = [chartId]
        let vSql = `SELECT * FROM l1_tajik_varsha_year_lords WHERE chart_id = $1`
        if (args.year_min) { vSql += ` AND year_num >= $${vParams.length + 1}`; vParams.push(args.year_min as number) }
        if (args.year_max) { vSql += ` AND year_num <= $${vParams.length + 1}`; vParams.push(args.year_max as number) }
        if (args.ayanamsha_id) { vSql += ` AND ayanamsha_id = $${vParams.length + 1}`; vParams.push(args.ayanamsha_id as string) }
        vSql += ` ORDER BY year_num, ayanamsha_id LIMIT ${limit}`
        const vResult = await query<Record<string, unknown>>(vSql, vParams)
        rows.push(...(vResult.rows ?? []).map(r => ({ ...r, _source_table: 'l1_tajik_varsha_year_lords' })))
      }

      return {
        content: { chart_id: chartId, chart_facts_categories: TAJIK_CF_CATEGORIES, rows, total: rows.length },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
