/**
 * query_kota_chakra — L3 Kāla Kota-Chakra (fort chart) serving surface
 * ========================================================================
 * ṢAḌ-DARŚANA W3 Lane w3-kota-sudarshana, registry item 16. Serves
 * kala_kota_chakra (ka_kota_chakra) — per-graha ring-run rows (stambha/
 * durgantara/prakara/bahya) with entry/exit windows and an attack/defence
 * reading, over a scanned +-horizon around the last build.
 *
 * `as_of` (default: today) selects which run is "current" per graha —
 * `is_current` on each row, plus a chart-level `current_rows`/`upcoming_rows`
 * split so a caller (kala_now_get) can serve the current state and a caller
 * wanting the forward view (kala_ahead_get, a documented follow-on not built
 * in this PR) can page the upcoming rows from the SAME table without a
 * second writer or a second query surface.
 *
 * Honesty discipline (B.10 / §N.6): `ring_table_citation`/`uncited_extension`
 * are always returned verbatim from the stored row — never summarized away —
 * so a caller can never mistake the writer's own posture/severity synthesis
 * for a primary-cited classical rule.
 *
 * Chart-scoped (principle #14).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryKotaChakraCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_kota_chakra',
  type:  'tool',
  layer: 'L3',
  name:  'query_kota_chakra',

  description: [
    'Retrieve Kota-Chakra (fort chart) ring-run rows for a chart from kala_kota_chakra',
    '(ka_kota_chakra, registry item 16). Each row: graha, nakshatra_name, kota_ring',
    "(stambha/durgantara/prakara/bahya — the graha's ring counted from the janma nakshatra),",
    'posture/severity (this writer\'s own attack/defence synthesis), window_start/window_end',
    '(entry/exit dates for that ring occupancy, with start_truncated/end_truncated flags when',
    'the true boundary lies outside the scanned horizon), and ring_table_citation (the ring',
    "table's own tier-(iii) secondary-source disclosure). `as_of` (default: today) marks which",
    'row is `is_current` per graha. Filter by graha to focus on one planet.',
  ].join(' '),

  input_schema: {
    chart_id: { type: 'string', description: 'Chart UUID. Required.', required: true },
    graha: {
      type: 'string',
      description: 'Filter by graha (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu). Omit for all.',
      enum: ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'],
    },
    as_of: { type: 'string', description: "Date (YYYY-MM-DD) to mark as 'current' (default: today)." },
    limit: { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
    current_only: {
      type: 'boolean',
      description:
        'When true, restrict the result to rows whose window contains `as_of` — i.e. apply the '
        + 'currency filter in SQL, BEFORE the row cap, instead of leaving the caller to filter a '
        + 'capped page afterwards. Default false (unchanged paging behaviour for existing callers).',
    },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  register: { reader_label: 'Consulting the chart — transit fortress' },
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
    const current_only = args['current_only'] === true

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (graha) { filters.push(`graha = $${p++}`); params.push(graha) }
    // Currency filter applied in SQL, not after the cap. Without this, a caller that wants only
    // the current rings gets the first `limit` rows by (graha, window_start) and then filters
    // them — so a chart with more ring-runs than the cap silently loses current rings, and the
    // caller cannot tell that from a genuine absence. `total_matching` + `truncated` below let
    // the caller distinguish the two in every case (§N.8: a claim of absence needs a detector
    // that could report presence).
    if (current_only) { filters.push(`window_start <= $${p}::date AND window_end >= $${p}::date`) }
    const where = filters.join(' AND ')

    // WP-1.5 F-DATE-TZ discipline: window_start/window_end are DATE columns — to_char
    // pins the calendar value as text, avoiding an IST-midnight -> UTC off-by-one.
    const sql = `
      SELECT graha, nakshatra_name, count_from_janma, kota_ring,
             is_natural_malefic, posture, severity,
             to_char(window_start, 'YYYY-MM-DD') AS window_start,
             to_char(window_end, 'YYYY-MM-DD')   AS window_end,
             start_truncated, end_truncated,
             janma_nakshatra_fact_id, ring_table_citation, uncited_extension,
             (window_start <= $${p}::date AND window_end >= $${p}::date) AS is_current
      FROM kala_kota_chakra
      WHERE ${where}
      ORDER BY graha, window_start
      LIMIT $${p + 1}`

    try {
      // The count query shares `where`, which may now reference $p (as_of); bind it the same way.
      const countParams = current_only ? [...params, as_of] : params
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, as_of, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM kala_kota_chakra WHERE ${where}`, countParams),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      const truncated = total_matching > rowsRes.rows.length
      return {
        content: {
          chart_id,
          as_of,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: truncated,
          // Explicit, machine-readable truncation signal so a consumer can never report an empty
          // or short result as a substantive absence when the real cause is the row cap (§N.8).
          truncated,
          filters: { graha: graha ?? 'all', as_of, limit, current_only },
          provenance: {
            tables: ['kala_kota_chakra'],
            source: 'ṢAḌ-DARŚANA W3 item 16 — Kota-Chakra fort chart; served chart-scoped.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
