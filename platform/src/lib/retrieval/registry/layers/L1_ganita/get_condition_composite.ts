/**
 * get_condition_composite — L1 Gaṇita unified planetary-condition rollup
 * ==========================================================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap
 * set, `ga_condition_composite`, 90 rows — highest-value single item this
 * batch per the disposition doc). Serves the rich, actively-built unified
 * per-graha condition rollup: D1+varga dignity spread, all 5 avastha
 * schemes, motion/combustion state, naisargika/tatkalika/panchadha
 * friendship, graha yuddha, a unified 0-1 condition_score with breakdown,
 * and peak/weak dasha-trajectory windows. `ganita_condition_get`'s
 * dignity/avasthas/karakas facets all read chart_facts directly, not this
 * composite — this tool exposes the composite rollup itself.
 *
 * Chart-scoped (principle #14). Bounded serving with disclosed total.
 *
 * X2 / I-29 (decision sheet L1, SS N-62): a composite row whose `condition_score` was computed on
 * D1 dignity ALONE (the divisional-chart composite was not available; the writer substitutes D1 and
 * records `condition_score_breakdown.varga_fallback_used = true`) is made VISIBLE, never flattened
 * in with divisional-based rows (CLAUDE.md §N.6 item 1): every row carries a top-level
 * `varga_fallback_used` field (true / false / null; null = no score computed, so the question does not
 * arise), `varga_fallback_used` is a Dens facet (filterable), and the response counts the D1-fallback
 * rows in the page and over the full filtered set with an explicit note.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

// The stored flag lives in the breakdown JSON (`condition_score_breakdown.varga_fallback_used`,
// written by ga_condition_writer.compute_condition_score_v1). Read it as a tri-state boolean:
// true = score computed on D1 alone, false = score read divisional dignity, NULL = the flag is
// absent (no score computed) -- an honest null, never coerced to false (CLAUDE.md §N.7 item 6).
const VARGA_FALLBACK_SQL =
  "CASE condition_score_breakdown->>'varga_fallback_used' WHEN 'true' THEN true WHEN 'false' THEN false END"

function parseBoolFilter(v: unknown): boolean | null {
  if (v === true || v === 'true') return true
  if (v === false || v === 'false') return false
  return null
}

export const getConditionCompositeCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L1/get_condition_composite',
  type:  'tool',
  layer: 'L1',
  name:  'get_condition_composite',

  description: [
    'Retrieve the unified per-graha condition rollup for a chart from ga_condition_composite.',
    'Per-graha row bundles: dignity_d1 + dignity_score_d1 + varga_dignity_spread/composite;',
    'all 5 avastha states (baladi/jagradadi/deeptaadi/lajjitaadi/sayanadi); motion_state,',
    'speed_degrees_per_day, is_retrograde, combustion_arc_from_sun, is_combust/deeply_combust;',
    'naisargika/tatkalika/panchadha friendship relations; graha_yuddha_with/result; a unified',
    'condition_score (0-1, condition_score_breakdown JSON) with formula version; and',
    'peak_dasha_periods/weak_dasha_periods (high/low-condition dasha windows). Filters: graha,',
    'ayanamsha_id, varga_fallback_used (true = only rows whose condition_score was computed on D1',
    'dignity ALONE because no divisional composite was available; false = rows that read divisional',
    'dignity). Every row carries varga_fallback_used (true/false/null); d1_fallback_rows_in_page and',
    'd1_fallback_total_matching count the D1-only rows separately so they are never read as',
    'divisional-based scores. Bounded to 50 rows with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    graha:        { type: 'string', description: 'Filter by graha. Omit for all.' },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    varga_fallback_used: { type: 'boolean', description: 'Dens facet. true = only rows whose condition_score was computed on D1 dignity alone (no divisional composite); false = only rows that read divisional dignity. Omit for both.' },
    limit:        { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 55, always_include: false },
  },
  // F-C21 (L1_W1_ANALYSIS_BATCH_C.md, NOW, §N.6 item 4): was undeclared. empty_reason:
  // true is a genuine claim here (unlike this migration's other 5 files) — the handler
  // below sets content.empty_reason whenever total_matching === 0, naming the exact
  // filter combination that matched no rows.
  density_contract: {
    paginated: true,
    facets: ['graha', 'ayanamsha_id', 'varga_fallback_used'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const graha        = args['graha'] ? String(args['graha']) : null
    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const varga_fallback_used = parseBoolFilter(args['varga_fallback_used'])
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (graha)        { filters.push(`graha = $${p++}`); params.push(graha) }
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (varga_fallback_used !== null) { filters.push(`${VARGA_FALLBACK_SQL} = $${p++}`); params.push(varga_fallback_used) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT graha, ayanamsha_id, dignity_d1, dignity_score_d1, varga_dignity_spread,
             varga_dignity_composite, avastha_baladi, avastha_jagradadi, avastha_deeptaadi,
             avastha_lajjitaadi, avastha_sayanadi, motion_state, speed_degrees_per_day,
             is_retrograde, combustion_arc_from_sun, is_combust, is_deeply_combust,
             naisargika_relation, tatkalika_relation, panchadha_relation, graha_yuddha_with,
             graha_yuddha_result, condition_score, condition_formula_version,
             condition_score_breakdown, peak_dasha_periods, weak_dasha_periods, computed_at,
             ${VARGA_FALLBACK_SQL} AS varga_fallback_used,
             condition_score_breakdown->>'varga_fallback_reason' AS varga_fallback_reason
      FROM ga_condition_composite
      WHERE ${where}
      ORDER BY graha, ayanamsha_id
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string; d1_fallback_total?: string; divisional_total?: string }>(
          `SELECT COUNT(*)::text AS total,
                  COUNT(*) FILTER (WHERE ${VARGA_FALLBACK_SQL} IS TRUE)::text  AS d1_fallback_total,
                  COUNT(*) FILTER (WHERE ${VARGA_FALLBACK_SQL} IS FALSE)::text AS divisional_total
           FROM ga_condition_composite WHERE ${where}`,
          params,
        ),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      // X2 / I-29 (CLAUDE.md §N.6 item 1): the D1-only rows are counted SEPARATELY, never flattened in.
      // The full-set counts are null (not 0) when the count query did not return them: an honest null.
      const rawD1 = countRes.rows[0]?.d1_fallback_total
      const d1_fallback_total_matching = rawD1 === undefined || rawD1 === null ? null : Number(rawD1)
      const d1_fallback_rows_in_page = rowsRes.rows.filter(
        (r) => (r as Record<string, unknown>)['varga_fallback_used'] === true,
      ).length
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { graha, ayanamsha_id, varga_fallback_used, limit },
          d1_fallback_rows_in_page,
          d1_fallback_total_matching,
          ...(d1_fallback_rows_in_page > 0 || (d1_fallback_total_matching ?? 0) > 0
            ? {
                d1_fallback_note:
                  'Rows with varga_fallback_used = true computed condition_score on D1 dignity ALONE: the ' +
                  'divisional-chart dignity composite was not available for them, so the writer substituted ' +
                  'the D1 dignity score (varga_dignity_composite is NULL). They are served, not hidden, but ' +
                  'their condition_score, and the ga_medical / ga_vastu band labels derived from it, rest on ' +
                  'D1 alone and are not comparable with rows where varga_fallback_used = false. Filter with ' +
                  'varga_fallback_used=false for divisional-based rows only.',
              }
            : {}),
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No condition-composite rows matched (graha=${graha ?? 'any'}, ayanamsha_id=${ayanamsha_id ?? 'any'}, varga_fallback_used=${varga_fallback_used ?? 'any'}).` }
            : {}),
          provenance: { tables: ['ga_condition_composite'], source: 'L1 Gaṇita unified planetary-condition rollup; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
