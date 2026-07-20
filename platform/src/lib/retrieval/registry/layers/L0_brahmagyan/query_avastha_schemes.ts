/**
 * query_avastha_schemes — L0 Brahmagyan avastha-scheme reference
 * =================================================================
 * W2b dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap set,
 * `bg_avastha_schemes`, 35 rows). Serves the classical planetary-state
 * (avasthā) scheme rules — baladi/jagradadi/deeptaadi/lajjitaadi/sayanadi —
 * the DETERMINATION RULES + citations, not any chart's computed avastha
 * (that verdict lives in `ganita_condition_get`'s `avasthas` facet, which
 * reads chart_facts directly and does not expose these underlying rules).
 * Same migration file (250_bg_dignity_reference.sql) as bg_dignity_reference.
 *
 * Global classical reference — no chart_id needed.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

export const queryAvasthaSchemesCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L0/query_avastha_schemes',
  type:  'tool',
  layer: 'L0',
  name:  'query_avastha_schemes',

  description: [
    'Query the classical planetary-state (avasthā) scheme reference (bg_avastha_schemes,',
    '35 rows across 5 schemes: baladi, jagradadi, deeptaadi, lajjitaadi, sayanadi).',
    'Each row is one state within a scheme: state_order (rank), determination_rule (JSON',
    'rule describing how the state is derived), classical_citation, notes. Filter by',
    'scheme_name or state_name. Global classical reference — no chart_id needed; returns',
    'the RULES only, not any chart\'s computed avastha (that lives in chart_facts).',
  ].join(' '),

  input_schema: {
    scheme_name: { type: 'string', description: 'Filter by scheme (baladi|jagradadi|deeptaadi|lajjitaadi|sayanadi). Omit for all.' },
    state_name:  { type: 'string', description: 'Filter by state name within a scheme (case-insensitive). Omit for all.' },
  },

  required_inputs: [],
  scope: 'global',
  archetype: 'flat_fact',
  traversal_level: 'L-SOURCE',
  tool_role: 'leaf',
  emits_references: false,
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 25, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const schemeName = args['scheme_name'] ? String(args['scheme_name']) : null
    const stateName  = args['state_name'] ? String(args['state_name']) : null

    const filters: string[] = ['1=1']
    const params: unknown[] = []
    let p = 1
    if (schemeName) { filters.push(`LOWER(scheme_name) = LOWER($${p++})`); params.push(schemeName) }
    if (stateName)  { filters.push(`LOWER(state_name) = LOWER($${p++})`); params.push(stateName) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT scheme_name, state_name, state_order, determination_rule, classical_citation, notes
      FROM bg_avastha_schemes
      WHERE ${where}
      ORDER BY scheme_name, state_order`

    try {
      const result = await query<Record<string, unknown>>(sql, params)
      return {
        content: {
          rows: result.rows,
          count: result.rows.length,
          filters: { scheme_name: schemeName, state_name: stateName },
          ...(result.rows.length === 0
            ? { empty_reason: `No avastha-scheme rows matched (scheme_name=${schemeName ?? 'any'}, state_name=${stateName ?? 'any'}).` }
            : {}),
          disclaimer: 'Classical avastha determination rules only — not a computed per-chart avastha verdict.',
          provenance: { tables: ['bg_avastha_schemes'] },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err) }, is_error: true }
    }
  },
}
