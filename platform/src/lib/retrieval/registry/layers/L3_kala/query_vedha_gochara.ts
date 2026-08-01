/**
 * query_vedha_gochara — L3 Kāla Vedha application serving surface
 * ========================================================================
 * ṢAḌ-DARŚANA W3 Lane w3-moorti-vedha, registry item 5 (closes defect R-19).
 * Serves kala_vedha_gochara (ka_vedha_gochara) — TWO distinct classical
 * vedha (obstruction) mechanisms, distinguished by `vedha_kind`:
 *
 *   - 'house_vedha'   — house-level Gochara vedha from bg_transit_rules
 *                       (BPHS Ch.29; Phaladeepika Ch.26). REAL, cited,
 *                       uncited_extension=false always.
 *   - 'sarvatobhadra' — nakshatra-level Sarvatobhadra Chakra vedha. R-19.
 *                       uncited_extension=true — see `detail.r19_disclosure`
 *                       on every such row (also documented in full in
 *                       services/ka_vedha_gochara/logic.py's module
 *                       docstring): the primary-cited 9x9 grid tables
 *                       (l1_sarvatobhadra_positions/l1_sarvatobhadra_vedha)
 *                       remain unpopulated — no responsibly-transcribable
 *                       source was found this session; this row is the
 *                       existing algorithmic opposition approximation,
 *                       served live for the first time.
 *
 * Honesty discipline (§N.6): `vedha_kind` and `uncited_extension` are ALWAYS
 * returned verbatim — a caller can never mistake a sarvatobhadra row for a
 * primary-cited house_vedha one. `detail` (kind-specific fields) is returned
 * as-is, never flattened into the shared columns.
 *
 * `as_of` (default: today) selects which row is "current" — `is_current` on
 * each row, matching query_kota_chakra/query_moorti_nirnaya's convention.
 *
 * Chart-scoped (principle #14).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryVedhaGocharaCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_vedha_gochara',
  type:  'tool',
  layer: 'L3',
  name:  'query_vedha_gochara',

  description: [
    'Retrieve vedha (transit obstruction) rows for a chart from kala_vedha_gochara',
    '(ka_vedha_gochara, registry item 5, closes defect R-19). Each row carries vedha_kind',
    '("house_vedha" — REAL, cited BPHS/Phaladeepika house-level rule, uncited_extension=false;',
    'or "sarvatobhadra" — nakshatra-level, an honestly disclosed algorithmic approximation,',
    'uncited_extension=true, see detail.r19_disclosure), graha, window_start/window_end,',
    'classical_citation, and a kind-specific `detail` object (house_vedha:',
    'primary_house/vedha_house/obstruction_active/obstructing_graha/obstruction_window_*;',
    'sarvatobhadra: target_nakshatra_name/vedha_nakshatra_name/vedha_pair_source/',
    'cancellation_effect). `as_of` (default: today) marks which row is `is_current`.',
    'Filter by vedha_kind and/or graha.',
  ].join(' '),

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID. Required.', required: true },
    vedha_kind: {
      type: 'string',
      description: 'Filter by mechanism: house_vedha (REAL cited) or sarvatobhadra (R-19, disclosed approximation). Omit for both.',
      enum: ['house_vedha', 'sarvatobhadra'],
    },
    graha: {
      type: 'string',
      description: 'Filter by graha (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu). Omit for all.',
      enum: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'],
    },
    as_of: { type: 'string', description: "Date (YYYY-MM-DD) to mark as 'current' (default: today)." },
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
  register: { reader_label: 'Consulting the chart — transit obstruction (vedha)' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 50, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const vedha_kind = args['vedha_kind'] ? String(args['vedha_kind']) : null
    const graha = args['graha'] ? String(args['graha']) : null
    const as_of = args['as_of'] ? String(args['as_of']) : new Date().toISOString().slice(0, 10)
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (vedha_kind) { filters.push(`vedha_kind = $${p++}`); params.push(vedha_kind) }
    if (graha) { filters.push(`graha = $${p++}`); params.push(graha) }
    const where = filters.join(' AND ')

    // WP-1.5 F-DATE-TZ discipline: window_start/window_end are DATE columns — to_char
    // pins the calendar value as text, avoiding an IST-midnight -> UTC off-by-one.
    const sql = `
      SELECT vedha_kind, graha,
             to_char(window_start, 'YYYY-MM-DD') AS window_start,
             to_char(window_end, 'YYYY-MM-DD')   AS window_end,
             start_truncated, end_truncated,
             janma_reference_fact_id, classical_citation, uncited_extension, detail,
             (window_start <= $${p}::date AND window_end >= $${p}::date) AS is_current
      FROM kala_vedha_gochara
      WHERE ${where}
      ORDER BY vedha_kind, graha, window_start
      LIMIT $${p + 1}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, as_of, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM kala_vedha_gochara WHERE ${where}`, params),
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
          filters: { vedha_kind: vedha_kind ?? 'all', graha: graha ?? 'all', as_of, limit },
          provenance: {
            tables: ['kala_vedha_gochara', 'bg_transit_rules'],
            source: 'ṢAḌ-DARŚANA W3 item 5 — Vedha application + Sarvatobhadra (closes R-19); served chart-scoped.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
