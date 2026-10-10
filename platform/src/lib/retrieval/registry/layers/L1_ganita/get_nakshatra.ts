/**
 * L1 retrieval: nakshatra-semantic layer (ga_nakshatra)
 * Covers: graha_nakshatra_join, graha_pada_join, graha_kp_lords,
 *         cusp_kp_lords, graha_gandanta, graha_degree_flags, nakshatra_dispositor,
 *         nakshatra_exchange, nakshatra_conjunction, nakshatra_cogravity, graha_tara_bala,
 *         nakshatra_statistics, nakshatra_cross_ayanamsha, kp_house_significators,
 *         kp_planet_significations (15 fact_categories, ga_nakshatra's full count_sql list).
 * Tool: marsys://tool/L1/get_nakshatra
 *
 * F-B18/F-B19 (L1_W1_ANALYSIS_BATCH_B.md): the tool named for this asset
 * (ganita_nakshatra_get) never existed — this asset's ~2,847 rows had no dedicated serving
 * face at all, only reachable indirectly via bodha_signals_get(signal_type_class=
 * nakshatra_semantic). This closes that gap directly, mirroring get_sensitive_points.ts's
 * shape for a similarly diverse multi-category asset.
 *
 * `nakshatra_lord_placement` removed (migration 878): grepped every ga_nakshatra source
 * file (ga_writers/ga_nakshatra_emitters.py, pipeline/orchestrator/writers/ga_nakshatra.py)
 * and found it was declared but never actually emitted anywhere — a genuine docstring/const
 * overclaim, zero live rows, same defect class as get_graha_yuddha.ts's own hardcoded
 * zero-row category. `nakshatra_cross_ayanamsha` was already correctly present here.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { resolveHandlerAyanamsha, pushAyanamshaFilter, ayanamshaServeOrderBy, ayanamshaScopeEcho } from '../../handler_ayanamsha'
import { CITATION_HUMAN_SELECT, normalizeNarrationRows } from './citation_narration'

const NAKSHATRA_CATEGORIES = [
  'graha_nakshatra_join', 'graha_pada_join', 'graha_kp_lords',
  'cusp_kp_lords', 'graha_gandanta', 'graha_degree_flags', 'nakshatra_dispositor',
  'nakshatra_exchange', 'nakshatra_conjunction', 'nakshatra_cogravity', 'graha_tara_bala',
  'nakshatra_statistics', 'nakshatra_cross_ayanamsha', 'kp_house_significators',
  'kp_planet_significations',
]

const DOMAIN_MAP: Record<string, string[]> = {
  identity: ['graha_nakshatra_join', 'graha_pada_join', 'graha_gandanta', 'graha_degree_flags'],
  kp: ['graha_kp_lords', 'cusp_kp_lords', 'kp_house_significators', 'kp_planet_significations'],
  relational: ['nakshatra_dispositor', 'nakshatra_exchange', 'nakshatra_conjunction', 'nakshatra_cogravity'],
  strength: ['graha_tara_bala'],
  meta: ['nakshatra_statistics', 'nakshatra_cross_ayanamsha'],
}

export const getNakshatraCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_nakshatra',
  type: 'tool',
  layer: 'L1',
  name: 'get_nakshatra',
  description:
    'Retrieve the nakshatra-semantic layer for a chart: graha-nakshatra/pada joins, ' +
    'nakshatra lord placement, KP (Krishnamurti Paddhati) sub-lords for grahas and cusps ' +
    'plus KP house/planet significators, gandanta and degree-flag markers, nakshatra ' +
    'dispositor/exchange/conjunction/co-gravity relations, graha tara bala, and ' +
    'cross-ayanamsha nakshatra statistics. Covers 16 fact_categories.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    domain: {
      type: 'string',
      description: 'Filter by domain: identity | kp | relational | strength | meta.',
      enum: ['identity', 'kp', 'relational', 'strength', 'meta'],
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
    bulk_context: { pre_fetch_priority: 60, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 500, 2000)
      const offset  = (args.offset as number) ?? 0

      let categories = (args.categories as string[]) ?? NAKSHATRA_CATEGORIES
      if (args.domain) {
        categories = DOMAIN_MAP[args.domain as string] ?? categories
      }

      const params: unknown[] = [chartId, categories, limit, offset]
      let sql = `
        SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, formula_id,
               fact_value_num, fact_value_text, fact_value_jsonb, unit,
               verification_pass_status, citation_ref, ${CITATION_HUMAN_SELECT}
        FROM chart_facts
        WHERE chart_id = $1 AND fact_category = ANY($2::text[])
      `
      // nakshatra_cross_ayanamsha is stored once under the ayanamsha_id='INVARIANT' sentinel
      // (ga_nakshatra); a bare `ayanamsha_id = $n` would drop it, so the filter keeps it.
      const aya = resolveHandlerAyanamsha(args)
      sql += pushAyanamshaFilter(aya, params, { includeInvariant: true })
      // Total order: after a ga_nakshatra rebuild each (graha_gandanta, subject, is_gandanta)
      // key has TWO rows (canonical + strict_0_48 variant, told apart only by formula_id), so
      // an order ending at fact_key leaves ties that sort unstably across LIMIT/OFFSET pages.
      sql += ` ORDER BY fact_category, ${ayanamshaServeOrderBy()}, fact_subject, fact_key, formula_id NULLS FIRST, fact_id LIMIT $3 OFFSET $4`

      const result = await query<Record<string, unknown>>(sql, params)
      const rows = normalizeNarrationRows(result.rows)

      return {
        content: {
          chart_id: chartId,
          ...ayanamshaScopeEcho(aya),
          categories,
          rows,
          total: rows.length,
          // DENS-F: an explicit `categories` list may name categories this asset does not own (another asset's rows of chart_facts).
          // They are served unchanged (never dropped, B.10) but disclosed here so a caller cannot read the page as only this asset's rows.
          ...(foreign(categories).length > 0
            ? { categories_outside_asset: foreign(categories), categories_outside_asset_note: 'These requested categories belong to another asset; their rows are served but are not this surface\'s own layer.' }
            : {}),
          ...(rows.length === 0
            ? { empty_reason: `No nakshatra-semantic fact for chart ${chartId} in ${categories.length} categor${categories.length === 1 ? 'y' : 'ies'}${aya.id ? ` at ayanamsha '${aya.id}'` : ''}${offset > 0 ? ` (offset ${offset})` : ''}.` }
            : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
  // DENS-F (CLAUDE.md §N.6): the facets are real inputs; `categories` is the facet that selects this asset's
  // chart_facts rows (asset_declarations.json ga_nakshatra.density_facet). Pagination is a limit/offset pair and the
  // handler returns `empty_reason` on a zero-row page.
  density_contract: {
    paginated: true,
    facets: ['ayanamsha_id', 'domain', 'categories'],
    empty_reason: true,
  },
}

const foreign = (cs: string[]): string[] => cs.filter(c => !NAKSHATRA_CATEGORIES.includes(c))
