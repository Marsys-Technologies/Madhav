/**
 * query_moorti_nirnaya — L3 Kāla Moorti-nirṇaya serving surface
 * ========================================================================
 * ṢAḌ-DARŚANA W3 Lane w3-moorti-vedha, registry item 4. Serves
 * kala_moorti_nirnaya (ka_moorti_nirnaya) — per-graha sign-occupancy runs
 * with the classical gold/silver/copper/iron (svarṇa/rajata/tāmra/loha)
 * moorti quality, resolved from the Moon's nakshatra at the ingress moment
 * (bg_transit_moorti, REAL and cited: Phaladeepika Ch.26; BPHS Ch.28).
 *
 * `as_of` (default: today) selects which run is "current" per graha —
 * `is_current` on each row, matching query_kota_chakra's own convention so
 * kala_now_get / kala_ahead_get can serve the same way.
 *
 * Honesty discipline (B.10 / §N.7): `moorti_computed=false` rows (the run's
 * start is unverified — see writer module docstring) carry NULL moorti
 * fields verbatim — never backfilled or summarized into a guessed value.
 *
 * Chart-scoped (principle #14).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryMoortiNirnayaCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_moorti_nirnaya',
  type:  'tool',
  layer: 'L3',
  name:  'query_moorti_nirnaya',

  description: [
    'Retrieve Moorti-nirṇaya rows for a chart from kala_moorti_nirnaya (ka_moorti_nirnaya,',
    'registry item 4). Each row: graha, target_sign_name (the sign it is transiting),',
    'window_start/window_end (the ingress-to-next-ingress stay), and — when',
    'moorti_computed is true — moorti_name (swarna/rajata/tamra/loha), quality_tier (1-4,',
    '1=best), phala_brief, and moorti_classical_citation (REAL, from bg_transit_moorti:',
    'Phaladeepika Ch.26; BPHS Ch.28). moorti_computed=false means the run\'s true ingress',
    'moment falls outside the scanned horizon — an honest gap, never a guessed value; all',
    'moorti fields are NULL on those rows. `as_of` (default: today) marks which row is',
    '`is_current` per graha. Filter by graha to focus on one planet.',
  ].join(' '),

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID. Required.', required: true },
    graha: {
      type: 'string',
      description: 'Filter by graha (Sun/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu — Moon is out of scope, see writer docstring). Omit for all.',
      enum: ['Sun', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'],
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
  register: { reader_label: 'Consulting the chart — transit quality (moorti)' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 50, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const graha = args['graha'] ? String(args['graha']) : null
    const as_of = args['as_of'] ? String(args['as_of']) : new Date().toISOString().slice(0, 10)
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (graha) { filters.push(`graha = $${p++}`); params.push(graha) }
    const where = filters.join(' AND ')

    // WP-1.5 F-DATE-TZ discipline: window_start/window_end are DATE columns — to_char
    // pins the calendar value as text, avoiding an IST-midnight -> UTC off-by-one.
    const sql = `
      SELECT graha, target_sign_idx, target_sign_name,
             to_char(window_start, 'YYYY-MM-DD') AS window_start,
             to_char(window_end, 'YYYY-MM-DD')   AS window_end,
             start_truncated, end_truncated, moorti_computed,
             moon_nakshatra_idx_at_ingress, moon_nakshatra_name_at_ingress,
             janma_nakshatra_idx, janma_nakshatra_fact_id, nakshatra_offset,
             moorti_name, quality_tier, phala_brief, moorti_classical_citation,
             (window_start <= $${p}::date AND window_end >= $${p}::date) AS is_current
      FROM kala_moorti_nirnaya
      WHERE ${where}
      ORDER BY graha, window_start
      LIMIT $${p + 1}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, as_of, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM kala_moorti_nirnaya WHERE ${where}`, params),
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
          filters: { graha: graha ?? 'all', as_of, limit },
          provenance: {
            tables: ['kala_moorti_nirnaya', 'bg_transit_moorti'],
            source: 'ṢAḌ-DARŚANA W3 item 4 — Moorti-nirṇaya; served chart-scoped.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
