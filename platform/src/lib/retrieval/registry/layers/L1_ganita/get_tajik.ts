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

export const getTajikCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_tajik',
  type: 'tool',
  layer: 'L1',
  name: 'get_tajik',
  description:
    'Retrieve Tājika Varṣaphal (Persian/Tajik annual chart) data for a chart. ' +
    'From chart_facts: Tajik Hadda lord (Ptolemaic term lord for the degree), ' +
    'Triraashipathi (annual chart ruler — lord of the sign the Sun transits at birthday), ' +
    'and Tajik Vargottama specific. ' +
    'From l1_tajik_varsha_year_lords table: all annual Solar Return year lord combinations ' +
    '(Muntha, Varsha Lord, TrirasheePathi) across available years. ' +
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
    year_min:     { type: 'number', description: 'Filter varsha lords to year >= this.' },
    year_max:     { type: 'number', description: 'Filter varsha lords to year <= this.' },
    varsha_year:  {
      type: 'number',
      description:
        'R6 3b-budgets (R-25): filter varsha_year_lords to this EXACT year (e.g. current age for ' +
        'the native). Preferred over year_min/year_max when a single year is wanted — it is the ' +
        'only way to reach a specific solar-return year without paging through every prior year.',
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

      // ── Source 1: EAV hadda-lord / triraashipathi / vargottama facts ────────────
      const cfCountParams: unknown[] = [chartId, TAJIK_CF_CATEGORIES]
      let cfCountSql = `SELECT COUNT(*)::int AS n FROM chart_facts WHERE chart_id = $1 AND fact_category = ANY($2::text[])`
      if (args.ayanamsha_id) {
        cfCountSql += ` AND ayanamsha_id = $${cfCountParams.length + 1}`
        cfCountParams.push(args.ayanamsha_id as string)
      }
      const cfCountResult = await query<{ n: number }>(cfCountSql, cfCountParams)
      const haddaTotal = cfCountResult.rows[0]?.n ?? 0

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
      const haddaRows: Record<string, unknown>[] = cfResult.rows ?? []

      // ── Source 2: l1_tajik_varsha_year_lords (Solar Return annual lords) ────────
      // R6 3b-budgets (R-25) fix: this source now gets its OWN {offset, limit, total}
      // (defaulting to the same values the caller passed, but tracked and reported
      // separately) instead of silently ignoring `offset` and restarting at year 1 on
      // every page. `varsha_year` is an exact-year filter — the direct way to reach a
      // specific solar-return year (e.g. current age) without paging through every
      // prior year via year_min/year_max.
      let varshaRows: Record<string, unknown>[] = []
      let varshaTotal = 0
      if (includeVarsha) {
        const vCountParams: unknown[] = [chartId]
        let vCountSql = `SELECT COUNT(*)::int AS n FROM l1_tajik_varsha_year_lords WHERE chart_id = $1`
        if (args.varsha_year != null) { vCountSql += ` AND varsha_year = $${vCountParams.length + 1}`; vCountParams.push(args.varsha_year as number) }
        if (args.year_min != null) { vCountSql += ` AND varsha_year >= $${vCountParams.length + 1}`; vCountParams.push(args.year_min as number) }
        if (args.year_max != null) { vCountSql += ` AND varsha_year <= $${vCountParams.length + 1}`; vCountParams.push(args.year_max as number) }
        if (args.ayanamsha_id) { vCountSql += ` AND ayanamsha_id = $${vCountParams.length + 1}`; vCountParams.push(args.ayanamsha_id as string) }
        const vCountResult = await query<{ n: number }>(vCountSql, vCountParams)
        varshaTotal = vCountResult.rows[0]?.n ?? 0

        const vParams: unknown[] = [chartId]
        let vSql = `SELECT * FROM l1_tajik_varsha_year_lords WHERE chart_id = $1`
        if (args.varsha_year != null) { vSql += ` AND varsha_year = $${vParams.length + 1}`; vParams.push(args.varsha_year as number) }
        if (args.year_min != null) { vSql += ` AND varsha_year >= $${vParams.length + 1}`; vParams.push(args.year_min as number) }
        if (args.year_max != null) { vSql += ` AND varsha_year <= $${vParams.length + 1}`; vParams.push(args.year_max as number) }
        if (args.ayanamsha_id) { vSql += ` AND ayanamsha_id = $${vParams.length + 1}`; vParams.push(args.ayanamsha_id as string) }
        vSql += ` ORDER BY varsha_year, ayanamsha_id LIMIT $${vParams.length + 1} OFFSET $${vParams.length + 2}`
        vParams.push(limit, offset)
        const vResult = await query<Record<string, unknown>>(vSql, vParams)
        varshaRows = (vResult.rows ?? []).map(r => ({ ...r, _source_table: 'l1_tajik_varsha_year_lords' }))
      }

      const content: Record<string, unknown> = {
        chart_id: chartId,
        chart_facts_categories: TAJIK_CF_CATEGORIES,
        hadda_lord_facts: {
          rows: haddaRows,
          offset, limit,
          total: haddaTotal,
          returned_count: haddaRows.length,
        },
        varsha_year_lords: {
          rows: varshaRows,
          offset, limit,
          total: varshaTotal,
          returned_count: varshaRows.length,
          varsha_year_filter: args.varsha_year ?? null,
        },
        // Deprecated combined view — retained for byte-for-byte back-compat with
        // callers reading `rows`/`total` directly, but now an HONEST concatenation of
        // the two SEPARATELY-paginated sections above (never a source of the flip-flop
        // bug R-25 documented: each section's own total is now correct and stable).
        rows: [...haddaRows, ...varshaRows],
        total: haddaTotal + varshaTotal,
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
