/**
 * query_chart_gestalt — L2 Bodha whole-chart gestalt serving surface
 * ====================================================================
 * WP-1.3(a) / F-L10-007 (LCA-19). Serves bodha_chart_gestalt (5 rows/chart, one per
 * ayanamsha) — the whole-chart gestalt digest (defining threads, headline, watch list,
 * central question, domain verdict map) that was written but had NO MCP tool exposing
 * it over the deployed channel. Read-only, bounded. This is a prime L-ORIENT surface
 * for the Whole-Chart-Read protocol (B.11).
 *
 * Chart-scoped (principle #14).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { resolveHandlerAyanamsha, pushAyanamshaFilter, ayanamshaServeOrderBy, ayanamshaScopeEcho, describeAyanamshaScope, PRIMARY_AYANAMSHA, type HandlerAyanamsha, PRIMARY_AYANAMSHA_ID_INPUT_TEXT } from '../../handler_ayanamsha'
import { buildTailWatch } from '@/lib/retrieval/tail/build_tail_watch'
import { GESTALT_SCUS } from '../../knowledge/editorial'

const MAX_LIMIT = 50

export const queryChartGestaltCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_chart_gestalt',
  type:  'tool',
  layer: 'L2',
  name:  'query_chart_gestalt',
  semantic_capabilities: GESTALT_SCUS,

  description: [
    'Retrieve the whole-chart gestalt digest from bodha_chart_gestalt — one row stored per',
    'ayanamsha (a default call serves the Lahiri primary\'s row). Fields: defining_threads, central_dynamics_ids, pivot_ids,',
    'center_of_gravity_node_ids, domain_verdict_map, headline (+confidence, +epistemic),',
    'watch_list, central_question, outliers, contested_areas, zoom_spine. This is the',
    'orientation entry-point for a whole-chart read. Filters: ayanamsha_id. Bounded',
    'with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: PRIMARY_AYANAMSHA_ID_INPUT_TEXT },
    limit:        { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'orientation_digest',
  traversal_level: 'L-ORIENT',
  tool_role: 'umbrella',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  // Band phase 4 ("Reading the whole chart") — B.11 whole-chart-read (orientation gestalt).
  register: { reader_label: 'Reading the whole chart' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 90, always_include: false },
  },
  // NIRMĀṆA L2-W3 (N-17, §N.6). Hand-authored, because the DERIVED contract is not
  // trustworthy here: descriptor_defaults.deriveDensityContract() auto-stamps
  // `empty_reason: true` from the capability's archetype alone, so every capability
  // "has" one at runtime whether or not its handler ever sets `content.empty_reason`.
  // That is an unbacked claim at estate scale — §N.8's "a flag needs a real detector
  // or it is null", applied to a contract instead of a column. These values state what
  // this handler actually does.
  density_contract: {
    paginated: false, // `limit` is a cap, not pagination — there is no offset and no cursor
    facets: ['ayanamsha_id'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    // SS N-339/N-342 (PR-2): Lahiri-primary at handler level; ayanamsha_id:'all' / ayanamsha_scope:'all' opts out.
    let aya: HandlerAyanamsha
    try {
      aya = resolveHandlerAyanamsha(args)
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
    const ayanamsha_id = aya.id
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    const ayaSql = pushAyanamshaFilter(aya, params)
    const p = params.length + 1
    const where = filters.join(' AND ') + ayaSql

    const sql = `
      SELECT gestalt_id, ayanamsha_id, gestalt_formula_version, defining_threads_jsonb,
             central_dynamics_ids, pivot_ids, center_of_gravity_node_ids,
             domain_verdict_map_jsonb, headline_jsonb, watch_list_jsonb,
             central_question_jsonb, headline_confidence, headline_epistemic_jsonb,
             outliers_jsonb, contested_areas_jsonb, zoom_spine_jsonb, engine_version
      FROM bodha_chart_gestalt
      WHERE ${where}
      ORDER BY ${ayanamshaServeOrderBy()}
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_chart_gestalt WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      // D-SALIENCE tail clause: "every umbrella envelope reserves a hard-floored
      // tail_watch section". Best-effort — buildTailWatch returns an explained empty
      // rather than throwing, so the tail can never fail the read the caller asked for.
      const tail = await buildTailWatch(chart_id, aya.id ?? PRIMARY_AYANAMSHA)
      return {
        content: {
          chart_id,
          ...ayanamshaScopeEcho(aya),
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          tail_watch: tail.tail_watch,
          tail_watch_empty_reason: tail.tail_watch_empty_reason,
          tail_watch_components: tail.tail_watch_components,
          // Under the explicit 'all' opt-out the rows are pooled but the tail is a separate section pinned to the primary ayanamsha — label it.
          ...(aya.id === null ? { tail_watch_ayanamsha_id: PRIMARY_AYANAMSHA } : {}),
          empty_reason: rowsRes.rows.length > 0 ? null
            : `no bodha_chart_gestalt row for chart ${chart_id}` +
              ` at ${describeAyanamshaScope(aya)}` +
              '. The gestalt is written once per (chart, ayanamsha) by bo_chart_gestalt; ' +
              'an absent row means that writer has not run for this chart, not that the chart has no gestalt.',
          filters: { ayanamsha_id, limit },
          provenance: { tables: ['bodha_chart_gestalt'], source: 'L2 Bodha whole-chart gestalt; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
