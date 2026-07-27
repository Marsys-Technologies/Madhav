/**
 * L1 retrieval: Vimshottari (+ multi-system) dasha periods
 * Source: chart_dashas table (not chart_facts)
 * Tool: marsys://tool/L1/get_dashas
 *
 * R5 W1 (dasha_query lane, design §18/§21/§25, E-5 "temporal facets are load-bearing"):
 * adds the three mandatory facets design §1/§18 calls for — system (default vimshottari),
 * level (default cap = 3: Maha/Antar/Pratyantar), window (default now±5y) — on top of the
 * W0a P1 fix (as_of_date correctly gates the containment filter; NOT reverted here, only
 * made composable with the new facets). Design §18 line 92 / §475 (E-5): dasha_query must
 * NEVER serve unwindowed; (system, level-cap, date-range) required, defaulting to
 * vimshottari / 3 levels / ±5y. Gate target: system=vimshottari, level=Maha ("1"),
 * as_of=today, ayanamsha_id=lahiri_chitrapaksha → ≤1KB in ONE call.
 *
 * IMPORTANT — `ayanamsha_id` is NOT defaulted server-side (unlike `system`/`level`/`window`):
 * omitting it returns one row per ayanamsha (5 rows, ~3.2KB for the current-dasha case — 3x
 * over the ≤1KB gate) because chart_dashas carries all 5 ayanamshas and this handler applies
 * no ayanamsha filter unless the caller supplies one. An endpoint LLM following only the
 * "Gate target" line above (without noticing this paragraph) will silently bust the gate.
 * ALWAYS pass `ayanamsha_id: "lahiri_chitrapaksha"` (the platform-mcp shim's own default,
 * matching chart_facts_query's default) when the gate/current-dasha shape is what's wanted.
 * Flagged (not fixed here — a silent default would change existing multi-ayanamsha callers'
 * results): a future wave should consider defaulting `ayanamsha_id` server-side the same way
 * `system` defaults to vimshottari, per the same E-5 "declared-but-silently-unfiltered is the
 * worst contract violation" reasoning. See R5_RUN_LEDGER W1 dasha_query verifier finding.
 */
import type { CapabilityDescriptor } from '../../types'
import type { DrillPointer, JudgmentFlagEntry } from '../../../envelope'
import { judgmentFlag } from '../../../envelope'
import { query } from '@/lib/db/client'

// The 7 dasha systems actually written to chart_dashas.system_id (verified live, both charts:
// native 482012f1 + Abhinandan 1c826d5a). NOTE: this replaces a stale doc claim (Narayana/Shoola
// never landed; Mudda/Naisargika did) — description below now matches ground truth, not the
// pre-R5 aspirational list.
//
// R6 0e-dashameta (register V-12): 'vimshottari_kp' is an 8th, DISTINCT system_id — KP
// sub/sub-sub period rows used to be written under system_id='vimshottari' (differentiated
// only by the kp_sublevel column), which meant the default system=vimshottari facet silently
// served BOTH the classical Antardasha row and the KP sub-period row for the same level_n=2
// slot with divergent end dates. KP rows now live in their own system_id namespace so the
// default facet (and any caller who never heard of kp_sublevel) gets only classical rows;
// pass system="vimshottari_kp" explicitly to retrieve KP sub-lord chains.
const KNOWN_SYSTEMS = [
  'vimshottari', 'vimshottari_kp', 'yogini', 'ashtottari', 'chara_karaka', 'kalachakra', 'mudda', 'naisargika',
] as const

// Case/spelling normalization for the `system` facet — accepts the actual system_id values,
// common uppercase spellings, and the classical/alias names a caller might reach for.
const SYSTEM_ALIAS: Record<string, string> = {
  vimshottari: 'vimshottari', VIMSHOTTARI: 'vimshottari',
  vimshottari_kp: 'vimshottari_kp', VIMSHOTTARI_KP: 'vimshottari_kp',
  kp: 'vimshottari_kp', KP: 'vimshottari_kp', kp_sub: 'vimshottari_kp', KP_SUB: 'vimshottari_kp',
  yogini: 'yogini', YOGINI: 'yogini',
  ashtottari: 'ashtottari', ASHTOTTARI: 'ashtottari',
  chara_karaka: 'chara_karaka', CHARA_KARAKA: 'chara_karaka',
  chara: 'chara_karaka', CHARA: 'chara_karaka', jaimini: 'chara_karaka', JAIMINI: 'chara_karaka',
  kalachakra: 'kalachakra', KALACHAKRA: 'kalachakra',
  mudda: 'mudda', MUDDA: 'mudda', annual: 'mudda',
  naisargika: 'naisargika', NAISARGIKA: 'naisargika',
}

function normalizeSystem(input: string): string | null {
  const direct = SYSTEM_ALIAS[input]
  if (direct) return direct
  const lower = SYSTEM_ALIAS[input.toLowerCase()]
  return lower ?? null
}

// Level-name facet: chart_dashas.level_n runs 1..5 (Maha/Antar/Pratyantar/Sookshma/Prana).
const LEVEL_NAME_TO_N: Record<string, number> = {
  maha: 1, mahadasha: 1,
  antar: 2, antardasha: 2, bhukti: 2,
  pratyantar: 3, pratyantardasha: 3,
  sookshma: 4, sookshmadasha: 4,
  prana: 5, pranadasha: 5,
}

function normalizeLevel(input: string | number): number | null {
  if (typeof input === 'number') return Number.isFinite(input) ? input : null
  const n = LEVEL_NAME_TO_N[input.toLowerCase()]
  if (n !== undefined) return n
  const parsed = Number(input)
  return Number.isFinite(parsed) ? parsed : null
}

// ── fields projection (design §3 `select` idiom — "projection, the 63KB killer") ──
// chart_dashas carries ~40 columns/row (citation strings, verification metadata, jsonb
// blobs) — a single unprojected row already runs ~2KB serialized, which alone busts the
// W1 gate target ("current dasha lookup <=1KB, ONE call"). Default to a compact fact-card
// projection; `fields=all` (or an explicit column list) opts back into the full row.
const COMPACT_FIELDS = [
  'dasha_row_id', 'ayanamsha_id', 'system_id', 'level_n', 'parent_row_id',
  'lord_graha', 'lord_sign', 'start_date', 'end_date', 'sandhi_flag',
  'lord_natal_house_d1', 'lord_natal_sign', 'lord_natal_nakshatra', 'lord_natal_dignity_d1',
  'lord_natal_shadbala_total', 'verification_pass_status', 'citation_ref',
] as const

function projectRow(row: Record<string, unknown>, fields: readonly string[] | null): Record<string, unknown> {
  if (!fields) return row
  const out: Record<string, unknown> = {}
  for (const f of fields) {
    if (f in row) out[f] = row[f]
  }
  return out
}

export const getDashasCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_dashas',
  type: 'tool',
  layer: 'L1',
  name: 'get_dashas',
  description:
    'Retrieve dasha period data for a chart from the chart_dashas table. ' +
    'Covers the 7 dasha systems L1 actually builds: Vimshottari, Yogini, Ashtottari, ' +
    'Chara Karaka (Jaimini), Kalachakra, Mudda (annual/varshaphal), and Naisargika. ' +
    'Returns period boundaries (start/end dates), lord graha, level (Maha=1/Antar=2/Pratyantar=3/' +
    'Sookshma=4/Prana=5), and the dasha system identifier. ' +
    'FACETED (R5 W1): system (default vimshottari — pass system="all" for every system), ' +
    'level (default cap = 3, i.e. Maha/Antar/Pratyantar only — pass level for one exact level, ' +
    'or all_levels=true for every level), and window (default now±5y when no date filter is ' +
    'given at all — pass window_start/window_end, or as_of_date/date_contains/date_from to override). ' +
    'Use as_of_date to retrieve the dasha running on a specific date (e.g. today). ' +
    'Spans all systems, levels and ayanamshas as a large, paginated result set — ' +
    'never served unwindowed; a bare chart_id call returns the default-faceted slice, not the dump. ' +
    'NOTE: unlike system/level/window, ayanamsha_id has NO server-side default — omitting it ' +
    'returns one row PER AYANAMSHA (5 rows). For the standard "current dasha" gate shape (one ' +
    'row, <=1KB), ALWAYS pass ayanamsha_id="lahiri_chitrapaksha" explicitly.',
  input_schema: {
    chart_id:      { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id:  {
      type: 'string',
      description:
        'Filter by ayanamsha_id (e.g. lahiri_chitrapaksha). Omit to get ALL 5 ayanamshas ' +
        '(one row per ayanamsha for the same period — NOT a single unfiltered answer). For the ' +
        'standard "current dasha" gate shape (one row, <=1KB) ALWAYS pass ' +
        'ayanamsha_id="lahiri_chitrapaksha" explicitly — this param has no server-side default.',
    },
    system: {
      type: 'string',
      description:
        'Dasha system facet. One of: vimshottari | yogini | ashtottari | chara_karaka | kalachakra | ' +
        'mudda | naisargika (case-insensitive; "chara"/"jaimini" alias to chara_karaka). ' +
        'Pass "all" to disable the system filter (all 7 systems). Default: vimshottari.',
    },
    dasha_system: {
      type: 'string',
      description: 'Deprecated alias for `system` (kept for back-compat). `system` wins if both are passed.',
    },
    system_id: {
      type: 'string',
      description:
        'Alias for `system` using the raw chart_dashas.system_id column name — the value an LLM ' +
        'consumer most naturally reaches for (F-0354). Accepts the same vocabulary/aliases as `system` ' +
        '(vimshottari | vimshottari_kp | yogini | ashtottari | chara_karaka | kalachakra | mudda | ' +
        'naisargika; "all" for every system). Precedence: system > dasha_system > system_id. ' +
        'Previously dropped silently, defaulting every request to vimshottari and leaving all ~437k ' +
        'non-vimshottari rows dark.',
    },
    level: {
      type: 'string',
      description:
        'Dasha level facet — exact level. Accepts a number (1=Maha, 2=Antar, 3=Pratyantar, 4=Sookshma, ' +
        '5=Prana) or the level name. When set, overrides the default level-cap (see all_levels).',
    },
    all_levels: {
      type: 'boolean',
      description: 'Disable the default level-cap (level<=3) and return every built level. Ignored if `level` is set.',
    },
    window_start: { type: 'string', description: 'ISO date (YYYY-MM-DD). Window facet: only periods overlapping [window_start, window_end].' },
    window_end:   { type: 'string', description: 'ISO date (YYYY-MM-DD). Window facet: only periods overlapping [window_start, window_end].' },
    date_contains: { type: 'string', description: 'ISO date (YYYY-MM-DD). Returns dashas active on this date.' },
    date_from:     { type: 'string', description: 'ISO date (YYYY-MM-DD). Filters to dashas whose end_date >= this date. Pass the birth date to exclude pre-birth rows.' },
    as_of_date:    { type: 'string', description: 'ISO date (YYYY-MM-DD). Alias for date_contains — returns dashas active on this date ("what dasha am I running as of X"). Takes effect the same as date_contains; if both are passed, date_contains wins.' },
    lord_graha:    { type: 'string', description: 'Filter by lord graha abbreviation (e.g. SU, MO, MA).' },
    fields: {
      type: 'string',
      description:
        'Projection facet. "compact" (default) — fact-card fields only (lord, sign, span, natal condition, ' +
        'citation); "all" — every chart_dashas column (verification metadata, jsonb sandhi/concurrent-lord ' +
        'detail); or a comma-separated column list for a custom projection.',
    },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 200 },
  },
  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 85, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 200, 1000)
      const offset  = (args.offset as number) ?? 0

      const params: unknown[] = [chartId, limit, offset]
      let sql = `SELECT * FROM chart_dashas WHERE chart_id = $1`

      if (args.ayanamsha_id) {
        sql += ` AND ayanamsha_id = $${params.length + 1}`
        params.push(args.ayanamsha_id as string)
      }

      // ── system facet (default vimshottari; "all" or an unrecognized value disables the filter
      // rather than silently returning zero rows — an unrecognized system name is a caller error
      // we surface via judgment metadata, not a defect we hide behind an empty result set) ──
      // F-0354: `system_id` (the raw column name) is honored as an alias so a caller passing
      // the natural column name is not silently defaulted to vimshottari. Precedence:
      // system > dasha_system > system_id.
      const systemInput =
        (args.system as string | undefined) ??
        (args.dasha_system as string | undefined) ??
        (args.system_id as string | undefined)
      let systemApplied: string | null = null
      let systemRequestedButUnknown: string | null = null
      if (systemInput && systemInput.toLowerCase() !== 'all') {
        const normalized = normalizeSystem(systemInput)
        if (normalized) {
          sql += ` AND system_id = $${params.length + 1}`
          params.push(normalized)
          systemApplied = normalized
        } else {
          systemRequestedButUnknown = systemInput
        }
      } else if (!systemInput) {
        // Default facet value (design §18/E-5: dasha_query defaults to vimshottari, never
        // unwindowed-all-systems-by-default).
        sql += ` AND system_id = $${params.length + 1}`
        params.push('vimshottari')
        systemApplied = 'vimshottari'
      }
      // systemInput === 'all' → no filter, systemApplied stays null (explicit opt-out).

      // ── level facet (default cap = 3: Maha/Antar/Pratyantar; explicit level wins) ──
      let levelApplied: number | 'cap<=3' | 'all' = 'all'
      if (args.level !== undefined && args.level !== null && args.level !== '') {
        const levelN = normalizeLevel(args.level as string | number)
        if (levelN !== null) {
          sql += ` AND level_n = $${params.length + 1}`
          params.push(levelN)
          levelApplied = levelN
        }
      } else if (!args.all_levels) {
        sql += ` AND level_n <= 3`
        levelApplied = 'cap<=3'
      }

      if (args.lord_graha) {
        sql += ` AND lord_graha = $${params.length + 1}`
        params.push(args.lord_graha as string)
      }

      // ── as-of / containment (P1 W0a fix — UNCHANGED semantics, still wins over window) ──
      // as_of_date is an alias for date_contains ("what dasha am I running as of X") — it
      // MUST gate the same containment filter, not be silently dropped (P1, R5 W0a punch-list).
      // date_contains wins if both are somehow present.
      const containsDate = (args.date_contains as string | undefined) ?? (args.as_of_date as string | undefined)
      let windowApplied: { start: string; end: string } | null = null
      // F-0471/0485: every temporal filter that is actually applied must be echoed back — a
      // requested date/window must NEVER be silently dropped. `window` (below) only reflected
      // window_start/window_end + the default; the point-in-time (as_of/date_contains) and
      // date_from filters applied silently. `date_filter` echoes exactly what gated the query.
      const dateFilterApplied: {
        as_of_date?: string
        date_from?: string
        default_window_applied?: boolean
      } = {}
      if (containsDate) {
        dateFilterApplied.as_of_date = containsDate
      }
      if (containsDate) {
        sql += ` AND start_date <= $${params.length + 1}::date AND end_date >= $${params.length + 2}::date`
        params.push(containsDate)
        params.push(containsDate)
      }
      if (args.date_from) {
        // Exclude dashas that ended before date_from. The dasha running AT
        // date_from is included even if it started before (end_date >= date_from).
        sql += ` AND end_date >= $${params.length + 1}::date`
        params.push(args.date_from as string)
        dateFilterApplied.date_from = args.date_from as string
      }

      // ── window facet (explicit window_start/window_end; overlap semantics) ──
      const windowStart = args.window_start as string | undefined
      const windowEnd = args.window_end as string | undefined
      if (windowStart) {
        sql += ` AND end_date >= $${params.length + 1}::date`
        params.push(windowStart)
      }
      if (windowEnd) {
        sql += ` AND start_date <= $${params.length + 1}::date`
        params.push(windowEnd)
      }
      if (windowStart || windowEnd) {
        windowApplied = { start: windowStart ?? '(open)', end: windowEnd ?? '(open)' }
      }

      // Design §18/E-5 default: if NO temporal facet at all was supplied (no as_of/date_contains,
      // no date_from, no window_start/window_end), the instrument must not serve unwindowed —
      // apply the documented default of now±5y so a bare chart_id+system call never dumps the
      // full multi-decade/multi-level timeline.
      const anyTemporalFacetGiven = Boolean(containsDate || args.date_from || windowStart || windowEnd)
      if (!anyTemporalFacetGiven) {
        const today = new Date()
        const start = new Date(today)
        start.setFullYear(start.getFullYear() - 5)
        const end = new Date(today)
        end.setFullYear(end.getFullYear() + 5)
        const startIso = start.toISOString().slice(0, 10)
        const endIso = end.toISOString().slice(0, 10)
        sql += ` AND end_date >= $${params.length + 1}::date AND start_date <= $${params.length + 2}::date`
        params.push(startIso)
        params.push(endIso)
        windowApplied = { start: startIso, end: endIso }
        dateFilterApplied.default_window_applied = true
      }

      sql += ` ORDER BY system_id, ayanamsha_id, start_date LIMIT $2 OFFSET $3`

      const result = await query<Record<string, unknown>>(sql, params)
      const rows = result.rows ?? []

      // ── R-43 (WP-1.8): dasha-lord natal strength re-derivation, SERVE-side ──────────
      // The denormalized chart_dashas.lord_natal_dignity_d1 / lord_natal_shadbala_total
      // columns are wrong or NULL for every row (native chart: 100% NULL on both) — so
      // dasha-lord strength was invisible to judgment. Per the register's own prescription
      // and §N.5 (L1 chart_facts is the authority over any L2+ denormalization), we RE-DERIVE
      // both at serve time from chart_facts and NEVER trust the stale column. A pre-existing
      // enrichment attempt keyed shadbala on 2-letter codes (SU/VE…), but chart_dashas.lord_graha
      // stores the DISPLAY name ("Venus") — so it silently matched nothing (a second R-43 bug).
      // This block keys on display-name → chart_facts subject-code, per (ayanamsha, graha),
      // and carries a PERMANENT verifier cross-check (served == chart_facts).
      const GRAHA_NAME_TO_FACT_SUBJECT: Record<string, string> = {
        Sun: 'SUN', Moon: 'MOON', Mars: 'MAR', Mercury: 'MER', Jupiter: 'JUP',
        Venus: 'VEN', Saturn: 'SAT', Rahu: 'RAH_MEAN', Ketu: 'KET_MEAN',
      }

      // Re-derived condition keyed by `${ayanamsha_id}|${factSubject}`.
      const dignityMap: Record<string, string | null> = {}
      const shadbalMap: Record<string, number | null> = {}
      try {
        // Distinct (ayanamsha, factSubject) pairs actually present in the served rows.
        const pairs = new Map<string, { aya: string; subj: string }>()
        for (const r of rows) {
          const aya = r['ayanamsha_id'] as string | undefined
          const subj = GRAHA_NAME_TO_FACT_SUBJECT[(r['lord_graha'] as string) ?? '']
          if (aya && subj) pairs.set(`${aya}|${subj}`, { aya, subj })
        }
        if (pairs.size > 0) {
          const ayas = [...new Set([...pairs.values()].map(p => p.aya))]
          const subs = [...new Set([...pairs.values()].map(p => p.subj))]
          const condRes = await query<{ ayanamsha_id: string; fact_subject: string; dignity_state: string | null; shadbala_rupa: number | null }>(
            `SELECT ayanamsha_id, fact_subject,
                    MAX(fact_value_text) FILTER (WHERE fact_category = 'graha_dignity_per_varga') AS dignity_state,
                    MAX(fact_value_num)  FILTER (WHERE fact_category = 'graha_shadbala_total')     AS shadbala_rupa
             FROM chart_facts
             WHERE chart_id = $1 AND ayanamsha_id = ANY($2::text[])
               AND (
                 (fact_category = 'graha_dignity_per_varga' AND fact_key = 'dignity_state' AND fact_subject = ANY($4::text[]))
                 OR (fact_category = 'graha_shadbala_total' AND fact_key = 'rupa' AND fact_subject = ANY($3::text[]))
               )
             GROUP BY ayanamsha_id, fact_subject`,
            [chartId, ayas, subs, subs.map(s => `D1_${s}`)],
          )
          // The dignity subject is `D1_<code>`; shadbala subject is `<code>`. Split by the two shapes.
          for (const cr of condRes.rows) {
            if (cr.dignity_state !== null && cr.fact_subject.startsWith('D1_')) {
              dignityMap[`${cr.ayanamsha_id}|${cr.fact_subject.slice(3)}`] = cr.dignity_state
            }
            if (cr.shadbala_rupa !== null && !cr.fact_subject.startsWith('D1_')) {
              shadbalMap[`${cr.ayanamsha_id}|${cr.fact_subject}`] = Number(cr.shadbala_rupa)
            }
          }
        }
      } catch {
        // Non-blocking: strength re-derivation is best-effort; absence serves null (never the stale column).
      }

      // PERMANENT verifier cross-check (register-mandated): the served dignity/shadbala are drawn
      // ONLY from chart_facts, so served == chart_facts holds BY CONSTRUCTION (§N.5 — L1 authority).
      // The always-on wire disclosure is a single compact provenance marker (envelope-budget safe,
      // WP-1.5 ≤1KB gate); the exhaustive per-row served==chart_facts cross-check — the register's
      // own prescription — is CI-enforced in wp18_cross_path_fidelity.integration.test.ts, which
      // independently re-reads chart_facts and asserts equality on every dasha row of both charts.
      const enrichedRows = rows.map(row => {
        const aya = row['ayanamsha_id'] as string | undefined
        const subj = GRAHA_NAME_TO_FACT_SUBJECT[(row['lord_graha'] as string) ?? '']
        const key = aya && subj ? `${aya}|${subj}` : null
        const rederivedDignity = key ? (dignityMap[key] ?? null) : null
        const rederivedShadbala = key ? (shadbalMap[key] ?? null) : null
        return {
          ...row,
          // Authoritative re-derived values override the (NULL/wrong) denormalized columns.
          lord_natal_dignity_d1: rederivedDignity,
          lord_natal_shadbala_total: rederivedShadbala,
          natal_condition_source: 'chart_facts:re-derived@serve (WP-1.8/R-43)',
        }
      })

      // ── fields projection (default: compact fact-card shape) ──
      const fieldsInput = (args.fields as string | undefined)?.trim()
      let fieldsApplied: string
      let projectFields: readonly string[] | null
      if (!fieldsInput || fieldsInput.toLowerCase() === 'compact') {
        projectFields = COMPACT_FIELDS
        fieldsApplied = 'compact'
      } else if (fieldsInput.toLowerCase() === 'all') {
        projectFields = null
        fieldsApplied = 'all'
      } else {
        projectFields = fieldsInput.split(',').map(f => f.trim()).filter(Boolean)
        fieldsApplied = projectFields.join(',')
      }
      const projectedRows = enrichedRows.map(row => projectRow(row, projectFields))

      const judgment_flags: JudgmentFlagEntry[] = []
      if (systemRequestedButUnknown) {
        judgment_flags.push(judgmentFlag(
          'system_facet_unrecognized',
          `"${systemRequestedButUnknown}" is not one of ${KNOWN_SYSTEMS.join('|')} — filter NOT applied, all systems served.`
        ))
      }

      // ── R5.3 B2 (Pratinidhi-R Q6-N-2 ruling): current-dasha narration ──
      // This tool is a flat_fact/leaf archetype that has never carried a narration field.
      // Built ONLY from rows already fetched in this call (no new computation, no new
      // fact_ids) + the chart's birth_date (project-level FORENSIC constant, threaded from
      // the `charts` table the same way get_graha_yuddha.ts already does — display-string
      // date→age arithmetic, not astrological computation). Fires only for the as_of_date/
      // date_contains "current dasha" shape, on the canonical (non-kp_sub) vimshottari rows,
      // to avoid narrating two self-contradicting end dates from the kp_sub/L-tagged variant
      // pairs chart_dashas serves side by side at Antar/Pratyantar level.
      let narration: string | null = null
      const drill_pointers: DrillPointer[] = []
      if (containsDate && systemApplied === 'vimshottari') {
        try {
          const birthRows = await query<{ birth_date: string }>(
            `SELECT birth_date::text AS birth_date FROM charts WHERE id = $1`,
            [chartId]
          )
          const birthDate = birthRows.rows[0]?.birth_date ?? null

          const isCanonicalRow = (r: Record<string, unknown>) =>
            !String(r['citation_ref'] ?? '').includes('kp_sub')

          const byLevel: Record<number, Record<string, unknown>> = {}
          for (const rawRow of enrichedRows) {
            const row = rawRow as Record<string, unknown>
            const lvl = row['level_n'] as number
            if (lvl < 1 || lvl > 3) continue
            // Prefer the canonical (non-kp_sub) row per level; first-seen otherwise.
            if (byLevel[lvl] === undefined || isCanonicalRow(row)) {
              byLevel[lvl] = row
            }
          }

          const ageAtDate = (isoDate: string | null): string => {
            if (!birthDate || !isoDate) return 'age unknown'
            const b = new Date(birthDate)
            const d = new Date(isoDate)
            let years = d.getFullYear() - b.getFullYear()
            const hasHadBirthdayThisYear =
              d.getMonth() > b.getMonth() ||
              (d.getMonth() === b.getMonth() && d.getDate() >= b.getDate())
            if (!hasHadBirthdayThisYear) years -= 1
            return `age ~${years}`
          }

          const md = byLevel[1]
          const ad = byLevel[2]
          const pd = byLevel[3]

          if (md && ad && pd) {
            const mdEnd = md['end_date'] as string
            const adEnd = ad['end_date'] as string
            const pdEnd = pd['end_date'] as string

            const leadSentence =
              `You are in ${md['lord_graha']} Mahadasha (ends ${mdEnd}, ${ageAtDate(mdEnd)}) -> ` +
              `${ad['lord_graha']} Antardasha (ends ${adEnd}, ${ageAtDate(adEnd)}) -> ` +
              `${pd['lord_graha']} Pratyantardasha (current, ends ${pdEnd}, ${ageAtDate(pdEnd)}).`

            const natalSentences: string[] = []
            if (ad['lord_natal_dignity_d1'] && ad['lord_natal_house_d1']) {
              natalSentences.push(
                `${ad['lord_graha']}, your Antardasha lord, is ${ad['lord_natal_dignity_d1']} ` +
                `in your ${ad['lord_natal_house_d1']} house (${ad['lord_natal_nakshatra'] ?? 'nakshatra n/a'}).`
              )
            }
            if (pd['lord_natal_dignity_d1'] && pd['lord_natal_house_d1']) {
              natalSentences.push(
                `${pd['lord_graha']}, your Pratyantardasha lord, is ${pd['lord_natal_dignity_d1']} ` +
                `in your ${pd['lord_natal_house_d1']} house (${pd['lord_natal_nakshatra'] ?? 'nakshatra n/a'}).`
              )
            }

            const sandhiSentence = md['sandhi_flag']
              ? `Note: the Mahadasha is in its sandhi (junction) window — classically a transitional ` +
                `caution period where both lords' effects blend — worth weighing against ${ad['lord_graha']}'s ` +
                `own placement above rather than reading as blanket alarm.`
              : null

            narration = [leadSentence, ...natalSentences, sandhiSentence]
              .filter(Boolean)
              .join(' ')

            drill_pointers.push({
              instrument: 'get_dashas',
              hint: `The period after the current Pratyantardasha (ends ${pdEnd}) is not returned by ` +
                `an as_of_date call — re-call with as_of_date just after ${pdEnd} (or window_start=${pdEnd}) ` +
                `to see the next lord and its natal condition.`,
              pointer_type: 'dasha_of_promise',
            })
          }
        } catch {
          // Non-blocking: narration is additive; a failure here must not break the base response.
          narration = null
        }
      }

      // MC-021/024 (ŚODHANA T4): the envelope never told a caller how DEEP this chart's dasha
      // data actually goes — level<=3 was the silent default cap, and nothing disclosed that
      // level 4 (Sūkṣma) exists and is requestable (`level=4` or `all_levels=true`), or that
      // level 5 (Prāṇa) is NOT built. Computed independently of whatever level/all_levels facet
      // THIS call applied (scoped only to chart_id + the same system/ayanamsha filter, so it
      // answers "how deep does this chart go", not "how deep did this particular page go").
      let levelsAvailable: number | null = null
      try {
        const lvlParams: unknown[] = [chartId]
        let lvlSql = `SELECT MAX(level_n)::int AS max_level FROM chart_dashas WHERE chart_id = $1`
        if (args.ayanamsha_id) {
          lvlSql += ` AND ayanamsha_id = $${lvlParams.length + 1}`
          lvlParams.push(args.ayanamsha_id as string)
        }
        if (systemApplied) {
          lvlSql += ` AND system_id = $${lvlParams.length + 1}`
          lvlParams.push(systemApplied)
        }
        const lvlResult = await query<{ max_level: number | null }>(lvlSql, lvlParams)
        levelsAvailable = lvlResult.rows[0]?.max_level ?? null
      } catch {
        // Non-blocking meta field — a failure here must not break the base response.
        levelsAvailable = null
      }

      return {
        content: {
          chart_id: chartId,
          source_table: 'chart_dashas',
          levels_available: levelsAvailable,
          facets_applied: {
            system: systemApplied ?? 'all',
            level: levelApplied,
            window: windowApplied,
            // F-0471/0485: echo the point-in-time / date_from filters that `window` alone omitted,
            // so a requested date/window is provably reflected back and never silently dropped.
            date_filter: dateFilterApplied,
            fields: fieldsApplied,
          },
          rows: projectedRows,
          total: projectedRows.length,
          // R-43 (WP-1.8): dasha-lord natal dignity + shadbala are re-derived from chart_facts at
          // serve time (the denormalized chart_dashas columns are NULL/wrong; §N.5 — L1 is the
          // authority). Compact always-on provenance marker (envelope-budget safe); the exhaustive
          // served==chart_facts cross-check is CI-enforced (wp18_cross_path_fidelity.integration).
          natal_condition_provenance: 'chart_facts:re-derived@serve (WP-1.8/R-43)',
          ...(narration ? { narration } : {}),
          ...(drill_pointers.length > 0 ? { drill_pointers } : {}),
        },
        is_error: false,
        ...(judgment_flags.length > 0 ? { judgment_flags } : {}),
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
