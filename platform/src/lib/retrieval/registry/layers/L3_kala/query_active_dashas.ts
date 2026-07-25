/**
 * query_active_dashas — L3 Kāla "what dasha am I running?" convenience face (EL-33 / DR-14)
 * ============================================================================================
 * Elevation Campaign v2.1 · STREAM γ (PŪRṆA) · Lane F [OPUS].
 *
 * The first-class `active_dashas(date|today)` surface: for a single point in time (default
 * today), report the active lord chain (L1/L2/L3 = Mahā/Antar/Pratyantar) with EXACT bounds
 * across ALL built dasha systems — not just the single default Vimśottarī, and NOT the full
 * heavy per-chart tree (query_dasha_dossier / get_dashas serve the deep windowed set).
 *
 * Bounded by construction: one instant × ≤3 levels × the systems present in chart_dashas for
 * this chart. A single date resolves to at most (#systems × 3) rows — a light convenience read.
 *
 * HONEST COVERAGE (B.10 — no fabrication): Ω1's baseline names 9 systems
 * (ashtottari, chara_karaka, kalachakra, mudda, naisargika, narayana, vimshottari,
 * vimshottari_kp, yogini). chart_dashas is the L1 authority; get_dashas' KNOWN_SYSTEMS
 * verified live that `narayana` never landed. This surface reports whatever system_ids are
 * ACTUALLY present for the chart (SELECT DISTINCT) and discloses any expected-but-absent
 * system as a coverage gap — it never invents a lord for a system that has no rows.
 *
 * Chart-scoped (principle #14). Read-only.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

/** Ω1 independently-verified baseline: the 9 dasha systems expected across the instrument. */
const EXPECTED_SYSTEMS = [
  'ashtottari', 'chara_karaka', 'kalachakra', 'mudda', 'naisargika',
  'narayana', 'vimshottari', 'vimshottari_kp', 'yogini',
] as const

const LEVEL_NAME: Record<number, string> = { 1: 'Mahadasha', 2: 'Antardasha', 3: 'Pratyantardasha' }
const MAX_LEVEL_DEFAULT = 3

interface DashaRow {
  system_id: string
  level_n: number
  lord_graha: string
  lord_sign: string | null
  start_date: string
  end_date: string
  start_iso: string | null
  end_iso: string | null
}

export const queryActiveDashasCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L3/query_active_dashas',
  type:  'tool',
  layer: 'L3',
  name:  'query_active_dashas',

  description: [
    'Convenience face (EL-33): "which dashas am I running on a given date?" — reports the active',
    'lord chain (level 1/2/3 = Mahā/Antar/Pratyantar) with exact start/end bounds across ALL built',
    'dasha systems for the chart, at a single instant (default today).',
    'Unlike get_dashas/query_dasha_dossier (deep windowed sets), this is bounded to one date × ≤3',
    'levels × the systems present — a light "you are here" read, not the heavy tree.',
    'Params: chart_id (req), date (YYYY-MM-DD, default today), ayanamsha_id (default lahiri_chitrapaksha),',
    'systems (comma list or "all", default all), max_level (default 3).',
    'Honest coverage: discloses which of the 9 expected systems are present vs absent for the chart',
    '(narayana is a known-absent system on current builds) — never fabricates a lord for an empty system.',
  ].join(' '),

  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID. Required.', required: true },
    date:         { type: 'string', description: 'Point in time (YYYY-MM-DD). Default: today.' },
    ayanamsha_id: { type: 'string', description: "Ayanamsha (default 'lahiri_chitrapaksha'). Omit-safe: defaulted to avoid 5x per-ayanamsha rows." },
    systems:      { type: 'string', description: "Comma-separated system_ids or 'all' (default). e.g. 'vimshottari,yogini'." },
    max_level:    { type: 'number', description: `Deepest level to report (1=Mahā, 2=Antar, 3=Pratyantar). Default ${MAX_LEVEL_DEFAULT}.` },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'temporal',
  traversal_level: 'L-SIGNAL',
  tool_role: 'temporal',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 60, always_include: false },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const date = args['date'] ? String(args['date']) : new Date().toISOString().split('T')[0]
    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : 'lahiri_chitrapaksha'
    const max_level = Math.min(Math.max(Number(args['max_level'] ?? MAX_LEVEL_DEFAULT), 1), 5)

    const systemsArg = args['systems'] ? String(args['systems']).trim() : 'all'
    const systemFilter =
      systemsArg.toLowerCase() === 'all' || systemsArg === ''
        ? null
        : systemsArg.split(',').map(s => s.trim().toLowerCase()).filter(Boolean)

    try {
      // Systems actually present for this chart (the honest denominator).
      const presentRes = await query<{ system_id: string }>(
        `SELECT DISTINCT system_id FROM chart_dashas WHERE chart_id = $1 AND ayanamsha_id = $2 ORDER BY system_id`,
        [chart_id, ayanamsha_id],
      )
      const systemsPresent = presentRes.rows.map(r => r.system_id)

      const params: unknown[] = [chart_id, ayanamsha_id, date, max_level]
      let systemClause = ''
      if (systemFilter && systemFilter.length > 0) {
        const ph = systemFilter.map((_, i) => `$${5 + i}`).join(', ')
        systemClause = `AND LOWER(system_id) IN (${ph})`
        systemFilter.forEach(s => params.push(s))
      }

      // The active chain: rows whose [start_date, end_date] contains `date`, per system, ≤ max_level.
      // F-DATE-TZ: DATE columns via to_char; start_iso/end_iso are timestamptz instants.
      const sql = `
        SELECT system_id, level_n, lord_graha, lord_sign,
               to_char(start_date, 'YYYY-MM-DD') AS start_date,
               to_char(end_date, 'YYYY-MM-DD')   AS end_date,
               start_iso, end_iso
        FROM chart_dashas
        WHERE chart_id = $1 AND ayanamsha_id = $2
          AND start_date <= $3::date AND end_date >= $3::date
          AND level_n <= $4
          ${systemClause}
        ORDER BY system_id, level_n`
      const res = await query<DashaRow>(sql, params)

      // Group the active chain by system.
      const bySystem = new Map<string, DashaRow[]>()
      for (const row of res.rows) {
        if (!bySystem.has(row.system_id)) bySystem.set(row.system_id, [])
        bySystem.get(row.system_id)!.push(row)
      }

      const systems = Array.from(bySystem.entries())
        .map(([system_id, rows]) => ({
          system_id,
          active_chain: rows
            .sort((a, b) => a.level_n - b.level_n)
            .map(r => ({
              level_n: r.level_n,
              level_name: LEVEL_NAME[r.level_n] ?? `L${r.level_n}`,
              lord_graha: r.lord_graha,
              lord_sign: r.lord_sign,
              start_date: r.start_date,
              end_date: r.end_date,
              start_iso: r.start_iso,
              end_iso: r.end_iso,
            })),
          levels_present: rows.map(r => r.level_n).sort((a, b) => a - b),
        }))
        .sort((a, b) => a.system_id.localeCompare(b.system_id))

      // Honest coverage accounting against the 9-system baseline.
      const expectedPresent = EXPECTED_SYSTEMS.filter(s => systemsPresent.includes(s))
      const expectedAbsent = EXPECTED_SYSTEMS.filter(s => !systemsPresent.includes(s))
      const systemsWithActiveRow = systems.map(s => s.system_id)
      const presentButNoActiveRow = systemsPresent.filter(s => !systemsWithActiveRow.includes(s))

      return {
        content: {
          chart_id,
          date,
          ayanamsha_id,
          max_level,
          systems,
          system_count: systems.length,
          coverage: {
            expected_systems: EXPECTED_SYSTEMS,
            systems_present_for_chart: systemsPresent,
            expected_present: expectedPresent,
            expected_absent: expectedAbsent,
            expected_absent_note: expectedAbsent.length
              ? `${expectedAbsent.join(', ')} not built into chart_dashas for this chart (narayana is a known-absent system on current builds — get_dashas KNOWN_SYSTEMS). Reported honestly, not fabricated.`
              : 'all 9 expected systems present.',
            present_but_no_active_row_on_date: presentButNoActiveRow,
            present_but_no_active_row_note: presentButNoActiveRow.length
              ? `${presentButNoActiveRow.join(', ')} have rows for this chart but none containing ${date} at ≤ level ${max_level} (period boundary or pre/post-coverage date).`
              : undefined,
          },
          bounded_note: 'Point-in-time convenience read (one date × ≤3 levels × systems present). For the deep windowed set use get_dashas / query_dasha_dossier.',
          provenance: {
            tables: ['chart_dashas'],
            source: 'L3 Kāla active-dasha convenience face (EL-33); chart_dashas is the L1 authority.',
            citation: 'Vimśottarī & multi-system daśā — BPHS Daśā adhyāyas; chart_dashas L1 build.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
