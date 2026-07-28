/**
 * L1 retrieval: Sade Sati and Saturn period family
 * Covers: sade_sati_cycle, sade_sati_phase, sade_sati_phase_quarter,
 *         sade_sati_modifier_overlay, sade_sati_cancellation_check,
 *         sade_sati_concurrent_dasha_overlay, sade_sati_downstream_cross_reference,
 *         sade_sati_saturn_retrograde_subset,
 *         janma_shani_period, anumukha_shani_period, ardha_ashtama_shani_period,
 *         ashtama_shani_period, dhaiya_period, vishakha_shani_period, kantaka_shani_period
 * Tool: marsys://tool/L1/get_sade_sati
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const SS_CATEGORIES = [
  'sade_sati_cycle', 'sade_sati_phase', 'sade_sati_phase_quarter',
  'sade_sati_modifier_overlay', 'sade_sati_cancellation_check',
  'sade_sati_concurrent_dasha_overlay', 'sade_sati_downstream_cross_reference',
  'sade_sati_saturn_retrograde_subset',
  'janma_shani_period', 'anumukha_shani_period', 'ardha_ashtama_shani_period',
  'ashtama_shani_period', 'dhaiya_period', 'vishakha_shani_period', 'kantaka_shani_period',
]

export const getSadeSatiCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_sade_sati',
  type: 'tool',
  layer: 'L1',
  name: 'get_sade_sati',
  description:
    'Retrieve the complete Sade Sati and Saturn transit period family for a chart. ' +
    'Includes: Sade Sati cycles (all historical + future), phase breakdowns (peak/rising/setting), ' +
    'quarter-phase granularity, modifier overlays (dignity/aspect cancellations), ' +
    'cancellation checks, concurrent dasha overlays (which dasha runs simultaneously), ' +
    'downstream cross-references, Saturn retrograde subsets, ' +
    'and all related Saturn transit period types ' +
    '(Janma Shani, Anumukha Shani, Ardha-Ashtama Shani, Ashtama Shani, Dhaiya, Vishakha, Kantaka). ' +
    'Covers 15 fact_categories (a large row set per chart).',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    categories:   { type: 'array',  description: 'Subset of Sade Sati categories.', items: { type: 'string' } },
    all: {
      type: 'boolean',
      description: 'ŚODHANA T3 (MC-014): default false — serves only the CURRENT + adjacent ' +
        'period(s) for every dated category (cycles/phases/quarters/periods/retrograde ' +
        'subsets), not the full historical+future sweep spanning ~1950-2100. Pass true to get ' +
        'every row across every period this chart has ever had or will ever have (the pre-fix ' +
        'behavior) — useful for a rectification/historical-events pass, not a "how is Saturn ' +
        'affecting me now" question. Rows with no start/end date pair (flags/modifiers/overlays ' +
        'keyed off a parent cycle) are always served regardless of this flag.',
      default: false,
    },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 500 },
  },
  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Transit windows' },
  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 82, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const requestedLimit = Math.min((args.limit as number) ?? 500, 2000)
      const offset     = (args.offset as number) ?? 0
      const categories = (args.categories as string[]) ?? SS_CATEGORIES
      const all        = (args.all as boolean) === true

      // ŚODHANA T3 (MC-014): the caller's OWN limit/offset governs the raw, unfiltered fetch
      // only when `all:true`. When defaulting to the current-window filter, the SQL fetch
      // must pull a large-enough internal batch FIRST (independent of the caller's page
      // size) so the date-window filter below sees the true row set for this chart rather
      // than an arbitrary SQL-LIMIT'd prefix — otherwise "current + adjacent" could silently
      // miss a period purely because it sorted past whatever small page the caller asked for.
      const fetchLimit = all ? requestedLimit : 20000
      const fetchOffset = all ? offset : 0

      const params: unknown[] = [chartId, categories, fetchLimit, fetchOffset]
      let sql = `
        SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
        FROM chart_facts
        WHERE chart_id = $1 AND fact_category = ANY($2::text[])
      `
      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }
      sql += ` ORDER BY fact_category, ayanamsha_id, fact_key LIMIT $3 OFFSET $4`

      const result = await query<Record<string, unknown>>(sql, params)
      const rawRows = result.rows ?? []

      if (all) {
        return {
          content: { chart_id: chartId, categories, rows: rawRows, total: rawRows.length, all: true },
          is_error: false,
        }
      }

      const { rows: filteredRows, totalBeforeFilter, groupsDropped } = filterToCurrentWindow(rawRows)
      const pageRows = filteredRows.slice(offset, offset + requestedLimit)

      return {
        content: {
          chart_id: chartId, categories,
          rows: pageRows,
          total: pageRows.length,
          total_before_window_filter: totalBeforeFilter,
          total_after_window_filter: filteredRows.length,
          periods_dropped_outside_window: groupsDropped,
          window_filter_applied: groupsDropped > 0,
          note: groupsDropped > 0
            ? `${groupsDropped} period(s)/cycle(s) outside the current+adjacent window were dropped from this default view (they carry a real start/end date pair that does not overlap now ± ${WINDOW_YEARS} years). Pass all:true to retrieve the full ~1950-2100 historical+future sweep.`
            : 'No dated period in this chart\'s Sade Sati/Saturn-period family fell outside the current+adjacent window — nothing was dropped.',
          drill_uri: groupsDropped > 0 ? 'marsys://tool/L1/get_sade_sati (all:true)' : undefined,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}

// ── MC-014 default-window filter ──────────────────────────────────────────────

/** How far before/after "now" a dated period is still considered "adjacent" and kept in the
 *  default (all:false) view. Generous enough to cover a genuinely current multi-year Sade
 *  Sati cycle plus its immediately neighboring cycle on either side, without reintroducing
 *  the full multi-decade sweep this fix exists to avoid by default. */
const WINDOW_YEARS = 5

type SadeSatiRow = Record<string, unknown>

/**
 * Groups rows by (fact_category, fact_subject, ayanamsha_id) — the natural key for "one
 * period/cycle instance" in this fact family — then, for any group that carries its OWN
 * `<prefix>_start_iso` / `<prefix>_end_iso` pair among its fetched fact_keys (schema-driven
 * detection, not hardcoded to one naming convention — this family alone uses cycle_/phase_/
 * quarter_/period_/retrograde_ prefixes across its 15 categories), keeps the WHOLE group only
 * if that date window overlaps [now - WINDOW_YEARS, now + WINDOW_YEARS]. A group with no
 * such date pair at all (e.g. sade_sati_modifier_overlay/cancellation_check/
 * concurrent_dasha_overlay/downstream_cross_reference — flags keyed off a parent cycle, not
 * independently dated) is ALWAYS kept — B.10: never drop data this filter cannot honestly
 * evaluate a date for.
 */
function filterToCurrentWindow(rows: SadeSatiRow[]): { rows: SadeSatiRow[]; totalBeforeFilter: number; groupsDropped: number } {
  const groups = new Map<string, SadeSatiRow[]>()
  for (const row of rows) {
    const key = `${row['fact_category']}::${row['fact_subject']}::${row['ayanamsha_id']}`
    const arr = groups.get(key)
    if (arr) arr.push(row)
    else groups.set(key, [row])
  }

  const now = Date.now()
  const windowMs = WINDOW_YEARS * 365.25 * 24 * 60 * 60 * 1000
  const windowStart = now - windowMs
  const windowEnd = now + windowMs

  const kept: SadeSatiRow[] = []
  let groupsDropped = 0

  for (const groupRows of groups.values()) {
    const window = findDateWindow(groupRows)
    if (!window) {
      kept.push(...groupRows) // no date pair found — always kept, never silently dropped.
      continue
    }
    const overlaps = window.end.getTime() >= windowStart && window.start.getTime() <= windowEnd
    if (overlaps) kept.push(...groupRows)
    else groupsDropped += 1
  }

  return { rows: kept, totalBeforeFilter: rows.length, groupsDropped }
}

/** Finds a `<prefix>_start_iso` / `<prefix>_end_iso` sibling pair within one group's rows
 *  (same prefix on both sides) and parses both as dates. Returns undefined if no such pair
 *  exists in this group, or if either value fails to parse — in both cases the caller treats
 *  the group as "undated" and keeps it unconditionally (never a silent incorrect drop). */
function findDateWindow(groupRows: SadeSatiRow[]): { start: Date; end: Date } | undefined {
  const byKey = new Map<string, string>()
  for (const row of groupRows) {
    const key = row['fact_key']
    const val = row['fact_value_text']
    if (typeof key === 'string' && typeof val === 'string') byKey.set(key, val)
  }
  for (const key of byKey.keys()) {
    const m = /^(.+)_start_iso$/.exec(key)
    if (!m) continue
    const prefix = m[1]
    const startText = byKey.get(key)
    const endText = byKey.get(`${prefix}_end_iso`)
    if (!startText || !endText) continue
    const start = new Date(startText)
    const end = new Date(endText)
    if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) continue
    return { start, end }
  }
  return undefined
}
