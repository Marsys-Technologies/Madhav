/**
 * query_tithi_pravesha — L3 Kāla Tithi-Praveśa (lunar-return annual chart) serving surface
 * ========================================================================
 * ṢAḌ-DARŚANA W3 Lane w3-tithi-pravesha, registry item 13. Serves
 * kala_tithi_pravesha (ka_tithi_pravesha) — one row per praveśa year (1..120,
 * full lifespan), the annual chart cast for the instant the transiting Moon
 * returns to its exact natal sidereal longitude nearest each solar-birthday
 * anniversary. The lunar-return counterpart to Tājika Vārṣaphala
 * (ga_tajaka, L1 solar-return) — see services/ka_tithi_pravesha/logic.py for
 * the full derivation and disclosed scope (return-instant + chart-cast only;
 * the Tājika-specific Muntha/Vārṣeśa/yoga apparatus is Vārṣaphala-only).
 *
 * `as_of` (default: today) resolves to the containing pravesha_year via
 * window_start/window_end and marks it `is_current` — a caller (kala_now_get)
 * can serve just that row; a caller wanting the forward view (kala_ahead_get,
 * a documented follow-on not built in this PR) can page `pravesha_year`
 * forward from the SAME table.
 *
 * Chart-scoped (principle #14).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 120 // the full lifespan

export const queryTithiPraveshaCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_tithi_pravesha',
  type:  'tool',
  layer: 'L3',
  name:  'query_tithi_pravesha',

  description: [
    'Retrieve Tithi-Praveśa (lunar-return annual chart) rows for a chart from',
    'kala_tithi_pravesha (ka_tithi_pravesha, registry item 13). Each row: pravesha_year',
    '(1..120, the Nth praveśa year), window_start/window_end (the lunar-return instant',
    'beginning/ending this year), pravesha_lagna_sign_name/degree (the annual ascendant),',
    'graha_positions_jsonb (all 9 grahas at the return instant), and ephemeris_audit_jsonb',
    '(root-find convergence + two-pass cross-check). `as_of` (default: today) marks which',
    'row is `is_current`. Filter by pravesha_year_from/to to page a range — default returns',
    'the full 120-year window.',
  ].join(' '),

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID. Required.', required: true },
    as_of: { type: 'string', description: "Date (YYYY-MM-DD) to mark as 'current' (default: today)." },
    pravesha_year_from: { type: 'number', description: 'Only years >= this (1..120). Omit for 1.' },
    pravesha_year_to:   { type: 'number', description: 'Only years <= this (1..120). Omit for 120.' },
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
    const yearFrom = args['pravesha_year_from'] !== undefined ? Number(args['pravesha_year_from']) : 1
    const yearTo   = args['pravesha_year_to'] !== undefined ? Number(args['pravesha_year_to']) : 120
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1', 'pravesha_year >= $2', 'pravesha_year <= $3']
    const params: unknown[] = [chart_id, yearFrom, yearTo]
    const where = filters.join(' AND ')

    // window_start/window_end are TIMESTAMPTZ — to_char pins a stable text
    // representation (WP-1.5 F-DATE-TZ discipline, matching the
    // query_sudarshana_varsha precedent for its own DATE columns).
    const sql = `
      SELECT pravesha_year,
             to_char(window_start, 'YYYY-MM-DD"T"HH24:MI:SS') AS window_start,
             to_char(window_end, 'YYYY-MM-DD"T"HH24:MI:SS')   AS window_end,
             start_converged, end_converged,
             pravesha_lagna_sign_idx, pravesha_lagna_sign_name, pravesha_lagna_degree,
             graha_positions_jsonb, natal_moon_longitude_deg, moon_fact_id,
             ephemeris_audit_jsonb, verification_pass_status, classical_source_citation,
             (window_start <= $4::timestamptz AND window_end > $4::timestamptz) AS is_current
      FROM kala_tithi_pravesha
      WHERE ${where}
      ORDER BY pravesha_year
      LIMIT $5`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, as_of, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM kala_tithi_pravesha WHERE ${where}`, params),
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
          filters: { as_of, pravesha_year_from: yearFrom, pravesha_year_to: yearTo, limit },
          provenance: {
            tables: ['kala_tithi_pravesha'],
            source: 'ṢAḌ-DARŚANA W3 item 13 — Tithi-Praveśa lunar-return annual chart; served chart-scoped.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
