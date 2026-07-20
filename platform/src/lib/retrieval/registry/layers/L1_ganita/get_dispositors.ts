/**
 * L1 retrieval: dispositor chains, parivartana, vargottama, kala sarpa
 * Covers: graha_dispositor_chain, dispositor_chain_per_varga, composite_dispositor_strength,
 *         parivartana_per_varga, kala_sarpa_per_varga
 * Tool: marsys://tool/L1/get_dispositors
 *
 * W2 structural-close SC-3 (RETRIEVAL_STRATEGY_v1_0.md §5.2 register row, serving-side only —
 * no writer change). SC-3 named a "D1 parivartana_pairs category-split orphan": the writer
 * (ga_structural_writer.py) has dead code emitting a `parivartana_pairs` category that is
 * NEVER actually written (verified live: zero rows across every chart, not just this one — an
 * unreachable code path, not a serving gap). The real D1 mutual-exchange data already lives in
 * `parivartana_per_varga` under the `D1_*` fact_subject prefix (verified live), which this
 * tool already serves by default — so D1 parivartana was never actually dark, just
 * undiscoverable under a misleading category name. Documented explicitly below so a caller
 * does not go looking for a `parivartana_pairs` category that will always return nothing.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const DISP_CATEGORIES = [
  'graha_dispositor_chain', 'dispositor_chain_per_varga', 'composite_dispositor_strength',
  'parivartana_per_varga', 'kala_sarpa_per_varga',
]

export const getDispositorsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_dispositors',
  type: 'tool',
  layer: 'L1',
  name: 'get_dispositors',
  description:
    'Retrieve dispositor chain data for a chart: natal dispositor chains (who lords each graha\'s sign), ' +
    'dispositor chains per varga (D2–D60), composite dispositor strength (final dispositor convergence weight), ' +
    'parivartana (mutual sign exchange) per varga INCLUDING D1 (fact_subject prefix "D1_..." — ' +
    'the natal-chart exchange is not a separate category, it is the D1 slice of ' +
    'parivartana_per_varga), and Kala Sarpa pattern per varga. ' +
    'The final dispositor node is a key CGM centrality anchor. ' +
    'Covers 5 fact_categories. (A `parivartana_pairs` category name exists in some historical ' +
    'documentation but is never populated by the writer — do not request it; use ' +
    'parivartana_per_varga with a D1_ subject prefix filter instead.)',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    categories:   { type: 'array',  description: 'Subset of dispositor categories.', items: { type: 'string' } },
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
    bulk_context: { pre_fetch_priority: 78, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 500, 2000)
      const offset     = (args.offset as number) ?? 0
      const categories = (args.categories as string[]) ?? DISP_CATEGORIES

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
