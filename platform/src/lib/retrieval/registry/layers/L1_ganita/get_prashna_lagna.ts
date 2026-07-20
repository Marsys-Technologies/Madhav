/**
 * get_prashna_lagna — L1 Gaṇita prashna-lagna computed serving surface
 * ========================================================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap
 * set, `ga_prashna_lagna`, 5 rows). Serves the computed Prashna-Lagna per
 * method/ayanamsha for a given prashna chart_id (289_ga_prashna_lagna.sql).
 * Zero prior references anywhere in the TS codebase.
 *
 * Chart-scoped (principle #14) — chart_id here references prashna_charts,
 * not the natal chart.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 20

export const getPrashnaLagnaCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L1/get_prashna_lagna',
  type:  'tool',
  layer: 'L1',
  name:  'get_prashna_lagna',

  description: [
    'Retrieve the computed Prashna-Lagna (horary ascendant) for a prashna chart from',
    'ga_prashna_lagna. Per-method row: lagna_method (e.g. tajik_moment_lagna, kp_249),',
    'lagna_rashi, lagna_degree, kp_sub_lord (for kp_249), is_primary flag,',
    'classical_citation. chart_id here references prashna_charts (the horary-question',
    'chart), not the natal chart. Filters: ayanamsha_id, lagna_method, primary_only.',
    'Bounded to 20 rows with a disclosed total.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Prashna chart UUID. Required.', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    lagna_method: { type: 'string', description: 'Filter by lagna_method. Omit for all.' },
    primary_only: { type: 'boolean', description: 'Return only the is_primary=true row(s).' },
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
    bulk_context: { pre_fetch_priority: 20, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const lagna_method = args['lagna_method'] ? String(args['lagna_method']) : null
    const primary_only = args['primary_only'] === true
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (lagna_method) { filters.push(`lagna_method = $${p++}`); params.push(lagna_method) }
    if (primary_only) { filters.push(`is_primary = TRUE`) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT chart_id, ayanamsha_id, lagna_method, lagna_rashi, lagna_degree, kp_sub_lord,
             is_primary, classical_citation
      FROM ga_prashna_lagna
      WHERE ${where}
      ORDER BY ayanamsha_id, lagna_method
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM ga_prashna_lagna WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { ayanamsha_id, lagna_method, primary_only, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No prashna-lagna rows matched for this prashna chart_id (ayanamsha_id=${ayanamsha_id ?? 'any'}, lagna_method=${lagna_method ?? 'any'}).` }
            : {}),
          provenance: { tables: ['ga_prashna_lagna'], source: 'L1 Gaṇita computed Prashna-Lagna; served per prashna chart.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
