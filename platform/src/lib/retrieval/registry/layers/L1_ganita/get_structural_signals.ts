/**
 * L1 retrieval: `ga_structural`'s residual relational/graph signal categories
 * Covers: sambandha_grade, virupa_drishti, contradiction_pair, conjunction_special_point,
 *         nakshatra_dispositor_chain, nakshatra_lord_relationship, nakshatra_co_tenancy,
 *         graha_centrality, chart_cluster, chart_center_of_gravity, significator_path,
 *         aspect_received_by_special_point, nway_config_per_varga, graha_yuddha_per_varga,
 *         kendradhipati_dosha (15 fact_categories).
 * Tool: marsys://tool/L1/get_structural
 *
 * `ga_structural` is a large multi-hundred-category asset whose bulk is already served across
 * many existing per-domain L1 tools (get_yoga_dosha.ts, get_dispositors.ts, get_bhava_bala.ts,
 * get_kp_cusps.ts, get_karakas.ts, register_d8_assess_domain.ts, ...) — this tool does NOT
 * attempt to re-serve any of that. It closes the specific residual gap the F-B32 cycle-156
 * sweep (`L1_W6_CLOSE_REPORT_v1_0.md` §5) found: a systematic check of every remaining
 * `coverage_matrix.ts`-missing category against every `L1_ganita/*.ts` file found these 15
 * (plus `karaka_web_per_varga`, already served via `get_karakas.ts`'s opt-in mechanism and
 * corrected in `coverage_matrix.ts` directly rather than duplicated here) had ZERO hits
 * anywhere — real, writer-owned, non-trivial-row-count data (all confirmed live for the
 * canonical chart, 1 to 5,220 rows each) with no serving path at all, the category-granularity
 * version of the original F-B18/F-B19 "asset has no tool" defect. All 15 confirmed
 * single-writer-owned by `ga_structural_writer.py` (grepped for a literal fact_category
 * construction; deliberately excludes categories this same sweep found are ALSO written by a
 * second L1/L0/L3 writer — `bhava_significance_link` [also `ga_vichara_writer.py`],
 * `net_argala_per_varga` [also `bg_vidhi_primitives.py`/`ka_yojaka.py`], `panchadha_maitri`
 * [also `ga_condition_writer.py`], `sandhi_flag` [also `ga_dashas_writer.py`/
 * `ga_positions_writer.py`] — genuinely ambiguous ownership left for a dedicated follow-up
 * rather than guessed at here).
 *
 * Mirrors get_nakshatra.ts / get_sensitive_points.ts's shape for a similarly diverse
 * multi-category asset: a plain paginated flat-fact SELECT with category/domain filters, no
 * per-category business logic (none of these 15 need one — `graha_yuddha_per_varga` in
 * particular is the PER-VARGA sibling of `get_graha_yuddha.ts`'s single-varga JL-027 Option A
 * overlay; that overlay's serve-time winner computation does not apply here and is out of
 * scope for this tool, which serves the writer's own floored rows as-is like every other
 * category on this page).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const STRUCTURAL_SIGNAL_CATEGORIES = [
  'sambandha_grade', 'virupa_drishti', 'contradiction_pair', 'conjunction_special_point',
  'nakshatra_dispositor_chain', 'nakshatra_lord_relationship', 'nakshatra_co_tenancy',
  'graha_centrality', 'chart_cluster', 'chart_center_of_gravity', 'significator_path',
  'aspect_received_by_special_point', 'nway_config_per_varga', 'graha_yuddha_per_varga',
  'kendradhipati_dosha',
]

const DOMAIN_MAP: Record<string, string[]> = {
  relational: ['sambandha_grade', 'virupa_drishti', 'contradiction_pair', 'conjunction_special_point',
    'nakshatra_dispositor_chain', 'nakshatra_lord_relationship', 'nakshatra_co_tenancy'],
  graph: ['graha_centrality', 'chart_cluster', 'chart_center_of_gravity', 'significator_path'],
  special_point: ['aspect_received_by_special_point'],
  per_varga: ['nway_config_per_varga', 'graha_yuddha_per_varga'],
  dosha: ['kendradhipati_dosha'],
}

export const getStructuralSignalsCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_structural',
  type: 'tool',
  layer: 'L1',
  name: 'get_structural',
  description:
    "Retrieve ga_structural's residual relational/graph signal layer: sambandha (planetary " +
    'relationship grade) and virupa-drishti aspect strength, contradiction and conjunction ' +
    'special-point pairs, nakshatra dispositor-chain/lord-relationship/co-tenancy relations, ' +
    'chart-graph metrics (centrality, clustering, center-of-gravity, significator path), ' +
    'per-varga n-way configuration and graha-yuddha, and kendradhipati dosha flags. Does NOT ' +
    'cover ga_structural categories already served by get_yoga_dosha/get_dispositors/' +
    'get_bhava_bala/get_karakas/get_kp_cusps or register_d8_assess_domain — this tool is the ' +
    'residual-coverage complement to those. Covers 15 fact_categories.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    domain: {
      type: 'string',
      description: 'Filter by domain: relational | graph | special_point | per_varga | dosha.',
      enum: ['relational', 'graph', 'special_point', 'per_varga', 'dosha'],
    },
    categories: { type: 'array', description: 'Explicit category list.', items: { type: 'string' } },
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
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 40, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 500, 2000)
      const offset  = (args.offset as number) ?? 0

      let categories = (args.categories as string[]) ?? STRUCTURAL_SIGNAL_CATEGORIES
      if (args.domain) {
        categories = DOMAIN_MAP[args.domain as string] ?? categories
      }

      const params: unknown[] = [chartId, categories, limit, offset]
      let sql = `
        SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
        FROM chart_facts
        WHERE chart_id = $1 AND fact_category = ANY($2::text[])
      `
      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }
      sql += ` ORDER BY fact_category, ayanamsha_id, fact_subject, fact_key LIMIT $3 OFFSET $4`

      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows ?? []

      return {
        content: {
          chart_id: chartId,
          categories,
          rows,
          total: rows.length,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
