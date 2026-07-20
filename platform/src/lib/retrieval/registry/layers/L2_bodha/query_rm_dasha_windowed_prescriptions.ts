/**
 * query_rm_dasha_windowed_prescriptions — L2 Bodha time-targeted remedy serving surface
 * ==========================================================================================
 * W2b Batch 3 dark-set wiring (TABLE_CONCEPT_DISPOSITIONS_v2_0.md SERVE-gap
 * set, `bodha_rm_dasha_windowed_prescriptions`). Serves the dasha-window-
 * targeted remedy schedule — "the time-targeted remedy slice", explicitly
 * flagged the single highest reading-impact dark item in
 * RETRIEVAL_STRATEGY_v1_0.md §5.2 (A13 Table 3, 226_bodha_spec_tables.sql).
 *
 * B.10 HONESTY NOTE: this table holds 0 rows on the live chart at the time
 * of this wiring pass (confirmed via direct read-only DB check, not a stale
 * doc claim) — the table + its writer contract exist for real (FK to
 * bodha_rm_remedy_prescriptions, which DOES have 270 live rows), so this is
 * a genuine, not-yet-populated concept, not a fabrication. The tool reports
 * this honestly via its existing empty-state discipline (empty_reason) —
 * exactly the same pattern already used for bodha_cdlm_evolution_gradients
 * (W2 addendum §10). Wiring the capability now means the moment this table
 * IS populated by its writer, the serving path is already live — no
 * separate follow-up wiring pass required.
 *
 * Chart-scoped. Bounded serving with disclosed total.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryRmDashaWindowedPrescriptionsCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_rm_dasha_windowed_prescriptions',
  type:  'tool',
  layer: 'L2',
  name:  'query_rm_dasha_windowed_prescriptions',

  description: [
    'Retrieve dasha-window-targeted remedy prescriptions from',
    'bodha_rm_dasha_windowed_prescriptions (Remedial Matrix — the time-targeted remedy',
    'slice). Each row: base_prescription_id (FK to bodha_rm_remedy_prescriptions),',
    'dasha_system, dasha_level, dasha_lord, window_start_iso/window_end_iso,',
    'window_intensity_multiplier, schedule_jsonb, phase_within_window. Filters:',
    'ayanamsha_id, dasha_system, dasha_lord, active_on_date (ISO date; window_start_iso <=',
    'date <= window_end_iso). May currently be empty on some charts if the writer has not',
    `yet run for this chart's build — reported honestly via empty_reason, not silently.`,
    `Bounded to ${MAX_LIMIT} rows with a disclosed total.`,
  ].join(' '),

  input_schema: {
    chart_id:       { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id:   { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    dasha_system:   { type: 'string', description: 'Filter by dasha_system. Omit for all.' },
    dasha_lord:     { type: 'string', description: 'Filter by dasha_lord. Omit for all.' },
    active_on_date: { type: 'string', description: 'ISO date; return only windows active on this date. Omit for all.' },
    limit:          { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 45, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const dashaSystem  = args['dasha_system'] ? String(args['dasha_system']) : null
    const dashaLord    = args['dasha_lord'] ? String(args['dasha_lord']) : null
    const activeOnDate = args['active_on_date'] ? String(args['active_on_date']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id) { filters.push(`ayanamsha_id = $${p++}`); params.push(ayanamsha_id) }
    if (dashaSystem)  { filters.push(`dasha_system = $${p++}`); params.push(dashaSystem) }
    if (dashaLord)    { filters.push(`dasha_lord = $${p++}`); params.push(dashaLord) }
    if (activeOnDate) { filters.push(`window_start_iso <= $${p}::timestamptz AND window_end_iso >= $${p}::timestamptz`); params.push(activeOnDate); p++ }
    const where = filters.join(' AND ')

    const sql = `
      SELECT window_prescription_id, ayanamsha_id, base_prescription_id, dasha_system,
             dasha_level, dasha_lord, window_start_iso, window_end_iso,
             window_intensity_multiplier, schedule_jsonb, phase_within_window,
             verification_pass_status, citation_ref, citation_human,
             to_char(computed_at, 'YYYY-MM-DD') AS computed_date
      FROM bodha_rm_dasha_windowed_prescriptions
      WHERE ${where}
      ORDER BY window_start_iso
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_rm_dasha_windowed_prescriptions WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { ayanamsha_id, dasha_system: dashaSystem, dasha_lord: dashaLord, active_on_date: activeOnDate, limit },
          ...(rowsRes.rows.length === 0
            ? { empty_reason: `No dasha-windowed-prescription rows matched for this chart (ayanamsha_id=${ayanamsha_id ?? 'any'}, dasha_system=${dashaSystem ?? 'any'}). This table may not yet be populated by its writer for this chart's build.` }
            : {}),
          provenance: { tables: ['bodha_rm_dasha_windowed_prescriptions'], source: 'L2 Bodha Remedial Matrix time-targeted remedy windows; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
