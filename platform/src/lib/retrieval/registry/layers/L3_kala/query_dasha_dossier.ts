/**
 * query_dasha_dossier — L3 Kāla per-dasha-period dossier serving surface
 * ========================================================================
 * WP-1.3(a) / F-L10-009 (LCA-19). Serves kala_avadhi (ka_avadhi) — per-dasha-period
 * dossier rows (~1,571-1,585/chart) that were computed and stored but had NO MCP tool
 * serving them, so they were fully unreachable. Read-only, bounded.
 *
 * Budget discipline (WP-1.3): 1.5k rows/chart across dasha systems and nesting levels —
 * served with a bounded LIMIT and a disclosed total, never an unbounded dump. Filter by
 * system_id / level_n / lord_graha / date range to narrow.
 *
 * Chart-scoped (principle #14).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryDashaDossierCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_dasha_dossier',
  type:  'tool',
  layer: 'L3',
  name:  'query_dasha_dossier',

  description: [
    'Retrieve per-dasha-period dossier rows for a chart from kala_avadhi (ka_avadhi).',
    'Each row: system_id (dasha system), level_n (nesting depth: maha=1, antar=2, …),',
    'lord_graha, period_start, period_end, dossier (jsonb narrative), quality (jsonb).',
    'Filters: system_id (default vimshottari), level_n, lord_graha, date_from, date_to,',
    'active_on (a date the period must contain). Bounded to 50 rows with a disclosed',
    'total — narrow by system/level/date rather than pulling all 1.5k periods at once.',
  ].join(' '),

  input_schema: {
    chart_id:   { type: 'string', description: 'Chart UUID. Required.', required: true },
    system_id:  { type: 'string', description: "Dasha system (default 'vimshottari'). Pass 'all' for every system." },
    level_n:    { type: 'number', description: 'Nesting level (1=maha, 2=antar, 3=pratyantar, …). Omit for all.' },
    lord_graha: { type: 'string', description: 'Filter by period lord graha. Omit for all.' },
    date_from:  { type: 'string', description: 'Only periods ending on/after this date (YYYY-MM-DD).' },
    date_to:    { type: 'string', description: 'Only periods starting on/before this date (YYYY-MM-DD).' },
    active_on:  { type: 'string', description: 'Only periods whose [start,end] contains this date (YYYY-MM-DD).' },
    limit:      { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Daśā structure' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 50, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const systemArg  = args['system_id'] ? String(args['system_id']) : 'vimshottari'
    const system_id  = systemArg.toLowerCase() === 'all' ? null : systemArg
    const level_n    = args['level_n'] !== undefined && args['level_n'] !== null ? Number(args['level_n']) : null
    const lord_graha = args['lord_graha'] ? String(args['lord_graha']) : null
    const date_from  = args['date_from'] ? String(args['date_from']) : null
    const date_to    = args['date_to'] ? String(args['date_to']) : null
    const active_on  = args['active_on'] ? String(args['active_on']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (system_id)          { filters.push(`system_id = $${p++}`);     params.push(system_id) }
    if (level_n !== null && !Number.isNaN(level_n)) { filters.push(`level_n = $${p++}`); params.push(level_n) }
    if (lord_graha)         { filters.push(`lord_graha = $${p++}`);    params.push(lord_graha) }
    if (date_from)          { filters.push(`period_end >= $${p++}`);   params.push(date_from) }
    if (date_to)            { filters.push(`period_start <= $${p++}`); params.push(date_to) }
    if (active_on)          { filters.push(`period_start <= $${p} AND period_end >= $${p}`); params.push(active_on); p++ }
    const where = filters.join(' AND ')

    // WP-1.5 F-DATE-TZ: period_start/period_end are DATE columns — to_char pins the true
    // calendar value as 'YYYY-MM-DD' text (raw return → node-postgres IST-midnight → UTC
    // off-by-one + spurious time component, un-round-trippable).
    const sql = `
      SELECT avadhi_id, system_id, level_n, lord_graha,
             to_char(period_start, 'YYYY-MM-DD') AS period_start,
             to_char(period_end, 'YYYY-MM-DD')   AS period_end,
             dossier, quality, citations, formula_version
      FROM kala_avadhi
      WHERE ${where}
      ORDER BY period_start, level_n
      LIMIT $${p}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM kala_avadhi WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: total_matching > rowsRes.rows.length,
          filters: { system_id: system_id ?? 'all', level_n, lord_graha, date_from, date_to, active_on, limit },
          budget_note: 'Bounded serving — narrow by system_id/level_n/date to page through the ~1.5k periods.',
          provenance: { tables: ['kala_avadhi'], source: 'L3 Kāla per-dasha dossier; served chart-scoped.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
