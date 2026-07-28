/**
 * L1 retrieval: ashtakavarga
 * Covers: ashtakavarga_bindu, ashtakavarga_bindu_sign, ashtakavarga_pinda_bhinna,
 *         ashtakavarga_pinda_sarva, ashtakavarga_pinda_sodhita,
 *         ashtakavarga_trikona_shodhana, ashtakavarga_ekadhipathya_shodhana,
 *         ashtakavarga_kakshya_boundary, ashtakavarga_pinda_raasi
 * Tool: marsys://tool/L1/get_ashtakavarga
 *
 * W2 structural-close SC-3/SC-4 (RETRIEVAL_STRATEGY_v1_0.md §5.2 register rows, serving-side
 * only — no writer change). Verified live against chart_facts: the L1 writer already computes
 * and stores the full refinement set SC-4 names (trikona shodhana, ekadhipathya shodhana,
 * kakshya boundaries, per-sign bindu) — this tool served only 5 of the 11 real
 * ashtakavarga_* categories. Six more real categories added below: the five modest-size
 * refinement categories join the default page; the two large per-varga rollups
 * (`ashtakavarga_bindu_per_varga`, `ashtakavarga_pinda_sarva_per_varga`) are NOT added to the
 * unconditional default (they would dominate/paginate out the smaller default categories —
 * §N.6 density discipline) and are reachable via an explicit `categories` request instead.
 * `ashtakavarga_anubindu` is kept in the default list for back-compat but is a legacy category
 * name the writer never actually emits (zero live rows across every chart, not just this one) —
 * requesting it honestly returns zero rows, never fabricated data (B.10).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const AV_CATEGORIES = [
  'ashtakavarga_bindu', 'ashtakavarga_anubindu', 'ashtakavarga_bindu_sign',
  'ashtakavarga_pinda_bhinna', 'ashtakavarga_pinda_sarva', 'ashtakavarga_pinda_sodhita',
  'ashtakavarga_pinda_raasi',
  'ashtakavarga_trikona_shodhana', 'ashtakavarga_ekadhipathya_shodhana',
  'ashtakavarga_kakshya_boundary',
]

/**
 * Real, computed, chart_facts-resident categories with no default-page inclusion (large
 * per-varga row sets — §N.6 density discipline) but fully queryable via an explicit
 * `categories` request.
 */
const AV_OPT_IN_CATEGORIES = ['ashtakavarga_bindu_per_varga', 'ashtakavarga_pinda_sarva_per_varga']

export const getAshtakavargaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_ashtakavarga',
  type: 'tool',
  layer: 'L1',
  name: 'get_ashtakavarga',
  description:
    'Retrieve Ashtakavarga data for a chart: individual bindus per graha per house and per ' +
    'sign, Pinda Bala (Bhinna, Sarva, Sodhita, Raasi), and the refinement set a transit-' +
    'ashtakavarga judgment needs — trikona shodhana, ekadhipathya (rasi-lordship) shodhana, ' +
    'and kakshya (sub-division) boundaries. ' +
    'Bindus range 0–8 per house per planet; sarva ashtakavarga totals per house; ' +
    'sodhita = after trikona + ekadhipathya shodhana reduction. ' +
    'Covers (default page): ashtakavarga_bindu, ashtakavarga_bindu_sign, ' +
    'ashtakavarga_pinda_bhinna, ashtakavarga_pinda_sarva, ashtakavarga_pinda_sodhita, ' +
    'ashtakavarga_pinda_raasi, ashtakavarga_trikona_shodhana, ' +
    'ashtakavarga_ekadhipathya_shodhana, ashtakavarga_kakshya_boundary ' +
    '(ashtakavarga_anubindu is also on the default list for back-compat but the writer never ' +
    'emits it — always returns zero rows). Two further real, computed, per-varga categories ' +
    'are available on request (not on the default page — large row sets): ' +
    '`ashtakavarga_bindu_per_varga` (bindu recomputed per divisional chart) and ' +
    '`ashtakavarga_pinda_sarva_per_varga` — pass categories:["ashtakavarga_bindu_per_varga"] ' +
    'etc. explicitly to fetch them.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    categories:   {
      type: 'array',
      description: 'Explicit AV category list — overrides the default page entirely. Also the ' +
        'only way to reach the two opt-in per-varga categories not on the default page: ' +
        'ashtakavarga_bindu_per_varga, ashtakavarga_pinda_sarva_per_varga.',
      items: { type: 'string' },
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
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Strengths & dignities' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 70, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 500, 2000)
      const offset     = (args.offset as number) ?? 0
      const categories = (args.categories as string[]) ?? AV_CATEGORIES

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
        content: {
          chart_id: chartId, categories, rows: result.rows ?? [], total: result.rows?.length ?? 0,
          // §N.6: density signaling is data, not narration — machine-readable pointer to the
          // real categories this tool can reach but does not include on the default page.
          opt_in_categories_available: AV_OPT_IN_CATEGORIES,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
