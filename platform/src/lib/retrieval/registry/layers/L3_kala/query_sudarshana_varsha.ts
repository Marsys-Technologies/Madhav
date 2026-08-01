/**
 * query_sudarshana_varsha — L3 Kāla Sudarśana-Chakra year-wheel serving surface
 * ========================================================================
 * ṢAḌ-DARŚANA W3 Lane w3-kota-sudarshana, registry item 17. Serves
 * kala_sudarshana_varsha (ka_sudarshana_varsha) — one row per varsha year
 * (1..120, full lifespan), progressing Janma/Chandra/Sūrya Lagna forward one
 * sign per year of life.
 *
 * BINDING NAMING NOTE (do not revisit): this capability serves
 * `ka_sudarshana_varsha`, a DIFFERENT, unrelated asset from L2 Bodha's
 * `bo_sudarshana` static tri-frame signal (see the writer's own docstring,
 * services/ka_sudarshana_varsha/logic.py, for the confirmed namesake-only
 * collision).
 *
 * `as_of` (default: today) resolves to the containing varsha_year via
 * window_start/window_end and marks it `is_current` — a caller (kala_now_get)
 * can serve just that row; a caller wanting the forward view (kala_ahead_get,
 * a documented follow-on not built in this PR) can page `varsha_year` forward
 * from the SAME table.
 *
 * Chart-scoped (principle #14).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 120 // the full lifespan — cheap, pure-arithmetic rows, no reason to under-serve

export const querySudarshanaVarshaCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_sudarshana_varsha',
  type:  'tool',
  layer: 'L3',
  name:  'query_sudarshana_varsha',

  description: [
    'Retrieve Sudarśana-Chakra year-wheel rows for a chart from kala_sudarshana_varsha',
    '(ka_sudarshana_varsha, registry item 17). Each row: varsha_year (1..120, the Nth year of',
    'life), window_start/window_end (calendar anniversary window), jl/cl/sl_active_sign_name',
    '(the progressed Janma/Chandra/Sūrya Lagna signs for that year), and tri_lagna_convergence',
    '(true when all three coincide — a classically notable alignment year). `as_of` (default:',
    "today) marks which row is `is_current`. Filter by varsha_year_from/to to page a range —",
    'default returns the full 120-year wheel (cheap, pure-arithmetic rows).',
  ].join(' '),

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID. Required.', required: true },
    as_of: { type: 'string', description: "Date (YYYY-MM-DD) to mark as 'current' (default: today)." },
    varsha_year_from: { type: 'number', description: 'Only years >= this (1..120). Omit for 1.' },
    varsha_year_to:   { type: 'number', description: 'Only years <= this (1..120). Omit for 120.' },
    limit: { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  register: { reader_label: 'Consulting the chart — Daśā structure' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 50, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const as_of = args['as_of'] ? String(args['as_of']) : new Date().toISOString().slice(0, 10)
    const yearFrom = args['varsha_year_from'] !== undefined ? Number(args['varsha_year_from']) : 1
    const yearTo   = args['varsha_year_to'] !== undefined ? Number(args['varsha_year_to']) : 120
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1', 'varsha_year >= $2', 'varsha_year <= $3']
    const params: unknown[] = [chart_id, yearFrom, yearTo]
    const where = filters.join(' AND ')

    // WP-1.5 F-DATE-TZ discipline: window_start/window_end are DATE columns — to_char
    // pins the calendar value as text, avoiding an IST-midnight -> UTC off-by-one.
    const sql = `
      SELECT varsha_year,
             to_char(window_start, 'YYYY-MM-DD') AS window_start,
             to_char(window_end, 'YYYY-MM-DD')   AS window_end,
             jl_active_sign_name, cl_active_sign_name, sl_active_sign_name,
             tri_lagna_convergence, lagna_fact_id, moon_fact_id, sun_fact_id,
             (window_start <= $4::date AND window_end > $4::date) AS is_current
      FROM kala_sudarshana_varsha
      WHERE ${where}
      ORDER BY varsha_year
      LIMIT $5`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, as_of, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM kala_sudarshana_varsha WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          as_of,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { as_of, varsha_year_from: yearFrom, varsha_year_to: yearTo, limit },
          provenance: {
            tables: ['kala_sudarshana_varsha'],
            source: 'ṢAḌ-DARŚANA W3 item 17 — Sudarśana-Chakra year-wheel; served chart-scoped.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
