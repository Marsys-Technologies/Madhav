/**
 * get_yoga_firings — L1 Gaṇita Nābhasa yoga-firing detail serving surface
 * =========================================================================
 * WP-1.3(a) / F-L10-003 (LCA-19). Serves ga_yoga_firings — the rich Nābhasa
 * firing asset (per-yoga strength scoring, bhanga/cancellation, partial-formation
 * %, family tagging, dāśā-activation windows) that was computed (~50-56 rows/chart)
 * but had NO deployed serving path. This is DISTINCT from get_yoga_dosha, which
 * reads yoga rows out of chart_facts; this tool exposes the dedicated firing table
 * with its bhanga + activation detail. Read-only, bounded.
 *
 * §N.5 note: each row's constituent_fact_ids resolve back to chart_facts.fact_id;
 * this tool serves the stored firing rows verbatim — it does not re-derive them.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const getYogaFiringsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L1/get_yoga_firings',
  type:  'tool',
  layer: 'L1',
  name:  'get_yoga_firings',

  description: [
    'Retrieve detailed Nābhasa/yoga firing rows for a chart from ga_yoga_firings.',
    'Each row: yoga_canonical_id, fired (bool), strength + strength_label,',
    'partial_formation_pct + is_partial, bhanga_active + bhanga_rule_fired (cancellation),',
    'constituent_planets/houses/fact_ids, family_ids, activation_dasha_periods, derivation.',
    'Filters: fired (default true), ayanamsha_id, bhanga_active, is_partial,',
    'yoga_canonical_id. Weak-tail and cancelled firings are included (strength is a column,',
    'not a gate). Bounded to 50 rows with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:          { type: 'string',  description: 'Chart UUID. Required.', required: true },
    fired:             { type: 'boolean', description: 'Filter by fired status (default: true — only fired yogas). Pass false for non-firings, omit-as-null via all=true.' },
    all:               { type: 'boolean', description: 'If true, ignore the fired filter and return fired + non-fired rows.' },
    ayanamsha_id:      { type: 'string',  description: "Filter by ayanamsha. Omit for all." },
    bhanga_active:     { type: 'boolean', description: 'Filter to firings with an active bhanga (cancellation) rule.' },
    is_partial:        { type: 'boolean', description: 'Filter to partially-formed yogas.' },
    yoga_canonical_id: { type: 'string',  description: 'Filter to a specific yoga by canonical id.' },
    limit:             { type: 'number',  description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
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
    bulk_context: { pre_fetch_priority: 60, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const all               = args['all'] === true
    const fired             = args['fired'] === undefined ? true : args['fired'] === true
    const ayanamsha_id      = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const bhanga_active     = typeof args['bhanga_active'] === 'boolean' ? (args['bhanga_active'] as boolean) : null
    const is_partial        = typeof args['is_partial'] === 'boolean' ? (args['is_partial'] as boolean) : null
    const yoga_canonical_id = args['yoga_canonical_id'] ? String(args['yoga_canonical_id']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (!all)                       { filters.push(`fired = $${p++}`);             params.push(fired) }
    if (ayanamsha_id)               { filters.push(`ayanamsha_id = $${p++}`);      params.push(ayanamsha_id) }
    if (bhanga_active !== null)     { filters.push(`bhanga_active = $${p++}`);     params.push(bhanga_active) }
    if (is_partial !== null)        { filters.push(`is_partial = $${p++}`);        params.push(is_partial) }
    if (yoga_canonical_id)          { filters.push(`yoga_canonical_id = $${p++}`); params.push(yoga_canonical_id) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT id, yoga_canonical_id, ayanamsha_id, fired, strength, strength_label,
             partial_formation_pct, is_partial, bhanga_active, bhanga_rule_fired, bhanga_na_reason,
             constituent_planets, constituent_houses, constituent_fact_ids, family_ids,
             activation_dasha_periods, derivation, citation_ref, citation_human
      FROM ga_yoga_firings
      WHERE ${where}
      ORDER BY strength DESC NULLS LAST, yoga_canonical_id
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM ga_yoga_firings WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { fired: all ? null : fired, all, ayanamsha_id, bhanga_active, is_partial, yoga_canonical_id, limit },
          provenance: {
            tables: ['ga_yoga_firings'],
            note: 'constituent_fact_ids resolve back to chart_facts.fact_id (§N.5).',
            source: 'L1 Gaṇita yoga-firing detail; served chart-scoped.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
