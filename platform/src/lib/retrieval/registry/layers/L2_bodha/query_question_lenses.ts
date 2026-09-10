/**
 * query_question_lenses — L2 Bodha question-lens catalog serving surface
 * ======================================================================
 * WP-1.3j / F-0156,0176 (W1-FOLLOWUP). Serves bodha_question_lenses — the catalog
 * of question-type lenses (60 rows/chart across 5 ayanamshas), each with its template /
 * wildcard element ids and a ranked-signal set. Computed and stored but had NO dedicated
 * MCP serving path (only surfaced indirectly, and unbounded, inside get_domain_reading).
 *
 * TOKEN-SAFETY: the all_relevant_ranked_jsonb payload can carry tens of thousands of
 * ranked signals (the F-021R 17MB trap). This tool NEVER returns that raw array — it
 * discloses ranked_signal_count and returns the small template/wildcard id sets only.
 * Drill into the ranked signals via query_domain_reading / query_signals.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { buildTailWatch } from '@/lib/retrieval/tail/build_tail_watch'

const MAX_LIMIT = 50

export const queryQuestionLensesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_question_lenses',
  type:  'tool',
  layer: 'L2',
  name:  'query_question_lenses',

  description: [
    'Retrieve the chart question-lens catalog from bodha_question_lenses — one row per',
    'question_type: its template_element_ids and wildcard_element_ids, points_only_assertion,',
    'verification_pass_status, and the COUNT of ranked signals (the raw ranked array is NOT',
    'inlined — token-safety; drill via query_domain_reading). Filters: ayanamsha_id, question_type.',
    'Bounded (LIMIT ≤50) with a disclosed total + offset pagination.',
  ].join(' '),

  input_schema: {
    chart_id:      { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id:  { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    question_type: { type: 'string', description: 'Filter by question_type. Omit for all.' },
    limit:         { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
    offset:        { type: 'number', description: 'Pagination offset (default 0).' },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'cross_domain',
  traversal_level: 'L-ORIENT',
  tool_role: 'umbrella',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 55, always_include: false },
  },
  // NIRMĀṆA L2-W3 (N-17, §N.6). Hand-authored, because the DERIVED contract is not
  // trustworthy here: descriptor_defaults.deriveDensityContract() auto-stamps
  // `empty_reason: true` from the capability's archetype alone, so every capability
  // "has" one at runtime whether or not its handler ever sets `content.empty_reason`.
  // That is an unbacked claim at estate scale — §N.8's "a flag needs a real detector
  // or it is null", applied to a contract instead of a column. These values state what
  // this handler actually does.
  density_contract: {
    paginated: true, // limit + offset + total_matching + more_available
    facets: ['ayanamsha_id', 'question_type'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const question_type = args['question_type'] ? String(args['question_type']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)
    const offset = Math.max(Number(args['offset'] ?? 0), 0)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id)  { filters.push(`ayanamsha_id = $${p++}`);  params.push(ayanamsha_id) }
    if (question_type) { filters.push(`question_type = $${p++}`); params.push(question_type) }
    const where = filters.join(' AND ')

    // COALESCE the ranked-signal count from either object-shaped ({total_count, ranked_signals})
    // or flat-array-shaped all_relevant_ranked_jsonb; never inline the raw payload.
    const sql = `
      SELECT lens_id, ayanamsha_id, question_type,
             template_element_ids_jsonb, wildcard_element_ids_jsonb,
             points_only_assertion, verification_pass_status,
             lens_template_version, lens_formula_version, citation_ref,
             COALESCE(
               NULLIF(all_relevant_ranked_jsonb->>'total_count','')::int,
               CASE WHEN jsonb_typeof(all_relevant_ranked_jsonb->'ranked_signals') = 'array'
                    THEN jsonb_array_length(all_relevant_ranked_jsonb->'ranked_signals') END,
               CASE WHEN jsonb_typeof(all_relevant_ranked_jsonb) = 'array'
                    THEN jsonb_array_length(all_relevant_ranked_jsonb) END,
               0
             ) AS ranked_signal_count,
             to_char(computed_at, 'YYYY-MM-DD') AS computed_date
      FROM bodha_question_lenses
      WHERE ${where}
      ORDER BY question_type, ayanamsha_id
      LIMIT $${p} OFFSET $${p + 1}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit, offset]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_question_lenses WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      // D-SALIENCE tail clause: "every umbrella envelope reserves a hard-floored
      // tail_watch section". Best-effort — buildTailWatch returns an explained empty
      // rather than throwing, so the tail can never fail the read the caller asked for.
      const tail = await buildTailWatch(chart_id, ayanamsha_id ?? 'lahiri_chitrapaksha')
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: offset + rowsRes.rows.length < total_matching,
          tail_watch: tail.tail_watch,
          tail_watch_empty_reason: tail.tail_watch_empty_reason,
          tail_watch_components: tail.tail_watch_components,
          empty_reason: rowsRes.rows.length > 0 ? null
            : total_matching > 0
              ? `offset ${offset} is past the end of ${total_matching} matching lenses`
              : `no question lenses for chart ${chart_id}` +
                (question_type ? ` and question_type ${question_type}` : '') +
                (ayanamsha_id ? ` at ayanamsha ${ayanamsha_id}` : '') +
                '. bo_drishti writes one lens per (question_type, ayanamsha); an absent row ' +
                'means the writer has not run, not that the question has no lens.',
          filters: { ayanamsha_id, question_type, limit, offset },
          token_safety_note: 'ranked_signal_count is disclosed; the raw ranked-signal array is intentionally not inlined. Drill via query_domain_reading.',
          provenance: { tables: ['bodha_question_lenses'], source: 'L2 Bodha question-lens catalog; served chart-scoped, budgeted.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
