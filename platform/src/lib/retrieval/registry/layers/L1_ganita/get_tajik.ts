/**
 * L1 retrieval: Tajika Varshaphal
 * Covers: tajik_hadda_lord, tajik_triraashipathi, tajik_vargottama_specific
 *         (plus aspect_tajik covered by get_aspects)
 *         and l1_tajik_varsha_year_lords (separate table)
 * Tool: marsys://tool/L1/get_tajik
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const TAJIK_CF_CATEGORIES = ['tajik_hadda_lord', 'tajik_triraashipathi', 'tajik_vargottama_specific']

/**
 * ŚODHANA T4/MC-021/024 fix: solar-return (varsha) year N runs from
 * birth_date + (N-1) years to birth_date + N years (matches the live
 * l1_tajik_varsha_year_lords rows: varsha_year=1 is 1984-02-05..1985-02-04
 * for the 1984-02-05 native). Given a birth_date and an as-of date, resolve
 * which varsha_year contains that date — the "current year" convenience so
 * a caller can pass a plain date (or rely on the default = today) instead of
 * hand-computing the native's current age.
 */
function resolveVarshaYearForDate(birthDateStr: string, dateStr: string): number {
  const b = new Date(birthDateStr)
  const d = new Date(dateStr)
  let years = d.getUTCFullYear() - b.getUTCFullYear()
  const hasHadAnniversary =
    d.getUTCMonth() > b.getUTCMonth() ||
    (d.getUTCMonth() === b.getUTCMonth() && d.getUTCDate() >= b.getUTCDate())
  if (!hasHadAnniversary) years -= 1
  return years + 1
}

export const getTajikCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_tajik',
  type: 'tool',
  layer: 'L1',
  name: 'get_tajik',
  description:
    'Retrieve Tājika Varṣaphal (Persian/Tajik annual chart) data for a chart. ' +
    'From chart_facts: Tajik Hadda lord (Ptolemaic term lord for the degree), ' +
    'Triraashipathi (annual chart ruler — lord of the sign the Sun transits at birthday), ' +
    'and Tajik Vargottama specific — gated behind include_hadda (default false; these 245 ' +
    'static rows do not change year to year, see include_hadda). ' +
    'From l1_tajik_varsha_year_lords table: all annual Solar Return year lord combinations ' +
    '(Muntha, Varsha Lord, TrirasheePathi) across available years — defaults to CURRENT-YEAR-FIRST ' +
    'ordering (see varsha_year / varsha_date) rather than oldest-first, since the current solar year ' +
    'is what a consultation actually needs. ' +
    'Includes FORENSIC-exact Muntha = Libra/7H/Venus. ' +
    'Covers 3 fact_categories + l1_tajik_varsha_year_lords table.',
  input_schema: {
    chart_id:       { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id:   { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    include_varsha: {
      type: 'boolean',
      description: 'Include l1_tajik_varsha_year_lords rows (default true)',
      default: true,
    },
    include_hadda: {
      type: 'boolean',
      description:
        'MC-021/024 fix: include the hadda_lord_facts / triraashipathi / vargottama chart_facts rows ' +
        '(245 static, non-year-varying rows). Default FALSE — these rows drowned the envelope by ' +
        'default while the actually-wanted current-year varsha row was unreachable. The total count ' +
        'is still always reported (hadda_lord_facts.total); pass include_hadda=true to fetch the rows.',
      default: false,
    },
    year_min:     { type: 'number', description: 'Filter varsha lords to year >= this.' },
    year_max:     { type: 'number', description: 'Filter varsha lords to year <= this.' },
    varsha_year:  {
      type: 'number',
      description:
        'R6 3b-budgets (R-25): filter varsha_year_lords to this EXACT year (e.g. current age for ' +
        'the native). Preferred over year_min/year_max when a single year is wanted — it is the ' +
        'only way to reach a specific solar-return year without paging through every prior year. ' +
        'Takes precedence over varsha_date if both are given.',
    },
    varsha_date: {
      type: 'string',
      description:
        'MC-021/024 "current year" convenience: an ISO date (YYYY-MM-DD); resolved server-side to ' +
        'the solar-return varsha_year whose window [birth_date + (N-1)y, birth_date + N*y) contains ' +
        'this date, then applied as an exact-year filter (same as passing that varsha_year directly). ' +
        'Ignored if varsha_year is also given. The resolved year is echoed back in ' +
        'varsha_year_lords.varsha_year_resolved_from_date.',
    },
    offset: {
      type: 'number', default: 0,
      description:
        'R6 3b-budgets (R-25) fix: offset/limit now page EACH source independently — hadda-lord ' +
        'chart_facts rows and varsha_year_lords rows are returned as two separately-paginated ' +
        'sections (hadda_lord_facts / varsha_year_lords), each with its own {offset, limit, total, ' +
        'returned_count}. Previously a single shared offset/limit applied to the EAV hadda rows ' +
        'while the varsha list silently ignored offset and always restarted at year 1 — total ' +
        'flipped 16→6 across offsets because the two sources drained at different rates.',
    },
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
    bulk_context: { pre_fetch_priority: 68, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId       = args.chart_id as string
      const limit         = Math.min((args.limit as number) ?? 200, 1000)
      const offset        = (args.offset as number) ?? 0
      const includeVarsha = (args.include_varsha as boolean) ?? true
      // MC-021/024 fix: hadda/triraashipathi/vargottama (245 static rows) now opt-in — they do
      // not change year to year and were drowning the envelope ahead of the actually-wanted
      // current-year varsha row. `total` is still always reported so a caller can tell "exists,
      // not fetched" apart from "genuinely zero".
      const includeHadda  = (args.include_hadda as boolean) ?? false

      // ── Source 1: EAV hadda-lord / triraashipathi / vargottama facts ────────────
      const cfCountParams: unknown[] = [chartId, TAJIK_CF_CATEGORIES]
      let cfCountSql = `SELECT COUNT(*)::int AS n FROM chart_facts WHERE chart_id = $1 AND fact_category = ANY($2::text[])`
      if (args.ayanamsha_id) {
        cfCountSql += ` AND ayanamsha_id = $${cfCountParams.length + 1}`
        cfCountParams.push(args.ayanamsha_id as string)
      }
      const cfCountResult = await query<{ n: number }>(cfCountSql, cfCountParams)
      const haddaTotal = cfCountResult.rows[0]?.n ?? 0

      let haddaRows: Record<string, unknown>[] = []
      if (includeHadda) {
        const params: unknown[] = [chartId, TAJIK_CF_CATEGORIES]
        let sql = `
          SELECT fact_id, fact_category, ayanamsha_id, fact_key, fact_value_num,
                 fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
          FROM chart_facts
          WHERE chart_id = $1 AND fact_category = ANY($2::text[])
        `
        if (args.ayanamsha_id) {
          sql += ` AND ayanamsha_id = $${params.length + 1}`
          params.push(args.ayanamsha_id as string)
        }
        sql += ` ORDER BY fact_category, ayanamsha_id, fact_key LIMIT $${params.length + 1} OFFSET $${params.length + 2}`
        params.push(limit, offset)

        const cfResult = await query<Record<string, unknown>>(sql, params)
        haddaRows = cfResult.rows ?? []
      }

      // ── Source 2: l1_tajik_varsha_year_lords (Solar Return annual lords) ────────
      // R6 3b-budgets (R-25) fix: this source now gets its OWN {offset, limit, total}
      // (defaulting to the same values the caller passed, but tracked and reported
      // separately) instead of silently ignoring `offset` and restarting at year 1 on
      // every page. `varsha_year` is an exact-year filter — the direct way to reach a
      // specific solar-return year (e.g. current age) without paging through every
      // prior year via year_min/year_max. MC-021/024: `varsha_date` resolves a plain
      // date to its containing varsha_year via the chart's birth_date, and a BARE call
      // (no varsha_year/varsha_date/year_min/year_max) now sorts CURRENT-YEAR-FIRST
      // instead of oldest-first (year 1 = the native's infancy is close to useless for
      // consultation as the lead row of a small-limit default call).
      let varshaRows: Record<string, unknown>[] = []
      let varshaTotal = 0
      let varshaYearResolvedFromDate: number | null = null
      let currentVarshaYear: number | null = null
      if (includeVarsha) {
        const explicitYear = args.varsha_year != null
        const hasRangeFilter = args.year_min != null || args.year_max != null

        let effectiveVarshaYear: number | null = explicitYear ? (args.varsha_year as number) : null

        // Resolve varsha_date → varsha_year (only when varsha_year itself wasn't given —
        // varsha_year wins if both are passed, same precedence pattern as system/system_id
        // elsewhere in this codebase).
        let birthDate: string | null = null
        const needsBirthDate = (!explicitYear && args.varsha_date != null) || (!explicitYear && !hasRangeFilter)
        if (needsBirthDate) {
          const birthRows = await query<{ birth_date: string }>(
            `SELECT birth_date::text AS birth_date FROM charts WHERE id = $1`,
            [chartId]
          )
          birthDate = birthRows.rows[0]?.birth_date ?? null
        }

        if (!explicitYear && args.varsha_date != null && birthDate) {
          varshaYearResolvedFromDate = resolveVarshaYearForDate(birthDate, args.varsha_date as string)
          effectiveVarshaYear = varshaYearResolvedFromDate
        }

        // Current-year-first default: only when the caller gave NO year selector at all
        // (no varsha_year, no varsha_date, no year_min/year_max) — an explicit selector
        // already narrows to what was asked for, so proximity sort would be moot/confusing.
        if (!explicitYear && args.varsha_date == null && !hasRangeFilter && birthDate) {
          currentVarshaYear = resolveVarshaYearForDate(birthDate, new Date().toISOString().slice(0, 10))
        }

        const vCountParams: unknown[] = [chartId]
        let vCountSql = `SELECT COUNT(*)::int AS n FROM l1_tajik_varsha_year_lords WHERE chart_id = $1`
        if (effectiveVarshaYear != null) { vCountSql += ` AND varsha_year = $${vCountParams.length + 1}`; vCountParams.push(effectiveVarshaYear) }
        if (args.year_min != null) { vCountSql += ` AND varsha_year >= $${vCountParams.length + 1}`; vCountParams.push(args.year_min as number) }
        if (args.year_max != null) { vCountSql += ` AND varsha_year <= $${vCountParams.length + 1}`; vCountParams.push(args.year_max as number) }
        if (args.ayanamsha_id) { vCountSql += ` AND ayanamsha_id = $${vCountParams.length + 1}`; vCountParams.push(args.ayanamsha_id as string) }
        const vCountResult = await query<{ n: number }>(vCountSql, vCountParams)
        varshaTotal = vCountResult.rows[0]?.n ?? 0

        const vParams: unknown[] = [chartId]
        let vSql = `SELECT * FROM l1_tajik_varsha_year_lords WHERE chart_id = $1`
        if (effectiveVarshaYear != null) { vSql += ` AND varsha_year = $${vParams.length + 1}`; vParams.push(effectiveVarshaYear) }
        if (args.year_min != null) { vSql += ` AND varsha_year >= $${vParams.length + 1}`; vParams.push(args.year_min as number) }
        if (args.year_max != null) { vSql += ` AND varsha_year <= $${vParams.length + 1}`; vParams.push(args.year_max as number) }
        if (args.ayanamsha_id) { vSql += ` AND ayanamsha_id = $${vParams.length + 1}`; vParams.push(args.ayanamsha_id as string) }
        if (currentVarshaYear != null) {
          vSql += ` ORDER BY ABS(varsha_year - $${vParams.length + 1}), varsha_year, ayanamsha_id`
          vParams.push(currentVarshaYear)
        } else {
          vSql += ` ORDER BY varsha_year, ayanamsha_id`
        }
        vSql += ` LIMIT $${vParams.length + 1} OFFSET $${vParams.length + 2}`
        vParams.push(limit, offset)
        const vResult = await query<Record<string, unknown>>(vSql, vParams)
        varshaRows = (vResult.rows ?? []).map(r => ({ ...r, _source_table: 'l1_tajik_varsha_year_lords' }))
      }

      const content: Record<string, unknown> = {
        chart_id: chartId,
        chart_facts_categories: TAJIK_CF_CATEGORIES,
        hadda_lord_facts: includeHadda
          ? {
              rows: haddaRows,
              offset, limit,
              total: haddaTotal,
              returned_count: haddaRows.length,
            }
          : {
              included: false,
              rows: [],
              total: haddaTotal,
              returned_count: 0,
              note: `include_hadda=false (default) — ${haddaTotal} static hadda_lord/triraashipathi/` +
                `vargottama rows exist but were not fetched (they do not vary by year). Pass ` +
                `include_hadda=true to retrieve them.`,
            },
        varsha_year_lords: {
          rows: varshaRows,
          offset, limit,
          total: varshaTotal,
          returned_count: varshaRows.length,
          varsha_year_filter: args.varsha_year ?? varshaYearResolvedFromDate ?? null,
          ...(varshaYearResolvedFromDate != null ? { varsha_year_resolved_from_date: varshaYearResolvedFromDate } : {}),
          ...(currentVarshaYear != null ? { current_varsha_year: currentVarshaYear, sort: 'current_year_first' } : { sort: 'varsha_year_ascending' }),
        },
        // Deprecated combined view — retained for byte-for-byte back-compat with
        // callers reading `rows`/`total` directly, but now an HONEST concatenation of
        // the two SEPARATELY-paginated sections above (never a source of the flip-flop
        // bug R-25 documented: each section's own total is now correct and stable).
        // include_hadda gates hadda rows out of this combined view too, same as above.
        rows: [...haddaRows, ...varshaRows],
        total: (includeHadda ? haddaTotal : 0) + varshaTotal,
      }

      // SATYA-ŚEṢA W1 (sibling sweep off chart_facts_query's own fix; SATYA_SHESHA_BRIEF_v1_0.md
      // §2 W1): a bare {rows: [], total: 0} here has no free-text term to run through the
      // concept resolver (this tool's categories are fixed, not caller-guessed), so the honest
      // fix is disclosure, not a resolver_suggestion — exactly what was searched, over what
      // universe, so a caller cannot silently read "no rows" as "Tajik data doesn't exist".
      if (haddaTotal === 0 && varshaTotal === 0) {
        content['empty_reason'] = `No chart_facts rows under fact_category IN (${TAJIK_CF_CATEGORIES.map(c => `"${c}"`).join(', ')}) ` +
          `and no l1_tajik_varsha_year_lords rows, for chart_id=${chartId}` +
          (args.ayanamsha_id ? `, ayanamsha_id=${String(args.ayanamsha_id)}` : '') +
          (args.varsha_year != null ? `, varsha_year=${String(args.varsha_year)}` : '') +
          `. Searched the whole matching set (true totals, not just this page) — Tajika/Varshaphal ` +
          `has genuinely not been computed/stored for this chart+filter combination.`
      }

      return { content, is_error: false }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
