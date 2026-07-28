/**
 * L1 retrieval: argala (intervention analysis)
 * Covers: argala_natal_matrix, virodha_argala_natal_matrix
 * Tool: marsys://tool/L1/get_argala
 *
 * EL-38 fix (D-1.7): this is a per-varga × per-target-sign × per-source-sign matrix — live-
 * verified against chart 482012f1: 41,760 rows across 29 vargas (144 cells × 2 categories ×
 * ~29 vargas × up to 5 ayanamshas). The MCP-side faceted wrapper's prior 25000-row default
 * (register_p1_ganita.ts's ganita_structural_get facet="argala") pulled most of that matrix
 * in one call and timed out. Two complementary fixes here: (1) an optional `varga` filter
 * (fact_subject is `{VARGA}_SIGN_{n}` — matched by prefix) so a caller can scope to ONE
 * divisional chart instead of all ~29 at once; (2) `fact_subject` added to the SELECT — it
 * was previously omitted even though it carries the row's own identity (the TARGET sign +
 * varga this argala/virodha cell applies to); an unrelated pre-existing data-completeness
 * gap, not the timeout bug itself, but required to serve `argala_on_house` below at all.
 * Also fixed: `ORDER BY` now includes `fact_subject` — it previously ordered by
 * `ayanamsha_id, fact_key` alone, and `fact_key` (`from_sign_N_offset_M`) repeats identically
 * across every (varga, target_sign) pair, so ties were resolved in undefined/unstable order —
 * non-deterministic pagination on a matrix this size.
 *
 * argala_on_house (shape='resolved', the default): each row's TARGET sign (parsed from
 * fact_subject) is re-counted as a house from THAT ROW'S OWN VARGA lagna (not D1 — a D9 cell
 * must be counted from the D9 lagna, per classical varga-lagna practice), via
 * chart_divisionals' `graha='Lagna' AND formula_provenance_text='whole_sign'` rows — the same
 * convention get_divisionals.ts (EL-47) and get_positions.ts's `house_from_frame` facet
 * already use (`houseCountedFrom`, single-source in address_resolver.ts). Pass
 * shape='matrix' for the pre-existing raw sign-indexed rows with no house resolution
 * (backward compat).
 *
 * all_zero: a per-page disclosure flag (NOT a data-correctness fix — that question belongs
 * to a different team/stream per the D-1.7 EL-38 brief; the writer's classical rule computes
 * a genuine, intentional 0.0 for any offset outside the argala/virodha position set — see
 * `ga_structural_writer.py`'s `_build_argala_rows`, ~67% of ALL cells are structurally zero
 * by design) — true only when EVERY row on the SERVED page has fact_value_num=0, so a caller
 * landing on such a page isn't misled into reading it as unserved/broken.
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'
import { houseCountedFrom, ZODIAC_SIGNS, type ZodiacSign } from '../../../address_resolver'

function isZodiacSign(v: unknown): v is ZodiacSign {
  return typeof v === 'string' && (ZODIAC_SIGNS as readonly string[]).includes(v)
}

// fact_subject shape: "{VARGA}_SIGN_{1-12}" (e.g. "D9_SIGN_4"). Parses both pieces.
const SUBJECT_RE = /^(.+)_SIGN_(\d{1,2})$/

function parseSubject(subject: unknown): { varga: string; signNum: number } | null {
  if (typeof subject !== 'string') return null
  const m = SUBJECT_RE.exec(subject)
  if (!m) return null
  const signNum = Number(m[2])
  if (!Number.isInteger(signNum) || signNum < 1 || signNum > 12) return null
  return { varga: m[1] as string, signNum }
}

export const getArgalaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_argala',
  type: 'tool',
  layer: 'L1',
  name: 'get_argala',
  description:
    'Retrieve Argala (intervention) and Virodha Argala (obstruction) matrices for a chart. ' +
    'Argala measures which grahas intervene in the results of each house via 2nd/4th/5th/11th placements; ' +
    'Virodha Argala measures which grahas block those interventions via 3rd/12th/10th/3rd (opposite). ' +
    'This is a per-varga × per-sign × per-offset matrix (all divisional charts, not just D1) — pass ' +
    '`varga` (e.g. "D1", "D9") to scope to one divisional chart; omit for all ~29 vargas at once ' +
    '(large — use offset/limit for pagination, and prefer a `varga` filter over raising limit). ' +
    'shape="resolved" (default) adds `argala_on_house` (1-indexed house count from that row\'s OWN ' +
    'varga lagna) to each row; shape="matrix" returns the raw sign-indexed rows unchanged (backward ' +
    'compat). `category_counts`/`total` report TRUE counts across the full filtered set, not just ' +
    'this page. `all_zero` flags when every row on THIS page has fact_value_num=0 (many cells are ' +
    'legitimately 0 by classical rule — offsets outside the argala/virodha position set — this flag ' +
    'is a disclosure, not an error signal). Covers: argala_natal_matrix, virodha_argala_natal_matrix.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    type:         { type: 'string', description: 'argala | virodha_argala. Omit for both.', enum: ['argala', 'virodha_argala'] },
    varga:        { type: 'string', description: 'Filter to one divisional chart (e.g. "D1", "D9"). Omit for all vargas (large).' },
    shape:        { type: 'string', description: 'resolved (default, adds argala_on_house) | matrix (raw, backward compat).', enum: ['resolved', 'matrix'] },
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
  register: { reader_label: 'Consulting the chart — House & lordships' },
  llm_hints: {
    agentic: { cost_class: 'medium', cacheable: true },
    bulk_context: { pre_fetch_priority: 60, always_include: false },
  },
  async handler(args, _ctx) {
    try {
      const chartId = args.chart_id as string
      const limit   = Math.min((args.limit as number) ?? 500, 2000)
      const offset  = (args.offset as number) ?? 0
      const shape   = args.shape === 'matrix' ? 'matrix' as const : 'resolved' as const

      let categories = ['argala_natal_matrix', 'virodha_argala_natal_matrix']
      if (args.type === 'argala')         categories = ['argala_natal_matrix']
      if (args.type === 'virodha_argala') categories = ['virodha_argala_natal_matrix']

      // Shared WHERE clause (chart_id/categories/ayanamsha_id/varga), reused by both the
      // paginated row query and the true-count facet_counts query below.
      const whereParts = ['chart_id = $1', 'fact_category = ANY($2::text[])']
      const whereParams: unknown[] = [chartId, categories]
      if (args.ayanamsha_id) {
        whereParams.push(args.ayanamsha_id as string)
        whereParts.push(`ayanamsha_id = $${whereParams.length}`)
      }
      if (args.varga) {
        // fact_subject = "{VARGA}_SIGN_{n}" — prefix-match on "{varga}_SIGN_" so "D1" never
        // accidentally matches "D10"/"D108"/etc.
        whereParams.push(`${args.varga as string}_SIGN_`)
        whereParts.push(`fact_subject LIKE $${whereParams.length} || '%'`)
      }
      const whereClause = whereParts.join(' AND ')

      const rowParams = [...whereParams, limit, offset]
      const sql = `
        SELECT fact_id, fact_category, ayanamsha_id, fact_subject, fact_key, fact_value_num,
               fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
        FROM chart_facts
        WHERE ${whereClause}
        ORDER BY ayanamsha_id, fact_subject, fact_key
        LIMIT $${rowParams.length - 1} OFFSET $${rowParams.length}
      `
      const result = await query<Record<string, unknown>>(sql, rowParams)
      const rows = result.rows ?? []

      // True counts across the FULL filtered set (not just this page) — "facet counts" so a
      // caller pagination-planning against a ~40k-row matrix knows how much more there is.
      const countSql = `
        SELECT fact_category, count(*)::int AS row_count
        FROM chart_facts
        WHERE ${whereClause}
        GROUP BY fact_category
      `
      const countResult = await query<{ fact_category: string; row_count: number }>(countSql, whereParams)
      const category_counts = countResult.rows ?? []
      const total = category_counts.reduce((sum, r) => sum + r.row_count, 0)

      // shape='resolved' (default): resolve each row's TARGET sign (from fact_subject) to a
      // house counted from that row's OWN varga lagna.
      let outRows: Record<string, unknown>[] = rows
      if (shape === 'resolved') {
        const vargasOnPage = new Set<string>()
        for (const r of rows) {
          const parsed = parseSubject(r['fact_subject'])
          if (parsed) vargasOnPage.add(parsed.varga)
        }
        const vargaLagnaSign = new Map<string, ZodiacSign>()
        if (vargasOnPage.size > 0) {
          const lagnaResult = await query<{ varga: string; ayanamsha_id: string; sign: string | null }>(
            `SELECT varga, ayanamsha_id, sign FROM chart_divisionals
             WHERE chart_id = $1 AND graha = 'Lagna' AND formula_provenance_text = 'whole_sign'
               AND varga = ANY($2::text[])`,
            [chartId, [...vargasOnPage]],
          )
          for (const r of lagnaResult.rows ?? []) {
            if (isZodiacSign(r.sign)) vargaLagnaSign.set(`${r.varga}::${r.ayanamsha_id}`, r.sign)
          }
        }
        outRows = rows.map(r => {
          const parsed = parseSubject(r['fact_subject'])
          if (!parsed) return r
          const targetSign = ZODIAC_SIGNS[parsed.signNum - 1]
          const lagnaSign = vargaLagnaSign.get(`${parsed.varga}::${r['ayanamsha_id']}`)
          if (!lagnaSign || !targetSign) return r
          return { ...r, argala_on_house: houseCountedFrom(lagnaSign, targetSign) }
        })
      }

      // EL-38 disclosure: flag (don't fix — that's a data-correctness question out of this
      // lane's scope) when the SERVED page is entirely fact_value_num=0.
      const all_zero = outRows.length > 0 &&
        outRows.every(r => r['fact_value_num'] !== null && Number(r['fact_value_num']) === 0)

      return {
        content: {
          chart_id: chartId, categories, shape,
          ...(args.varga ? { varga: args.varga as string } : {}),
          rows: outRows, total, category_counts, all_zero,
          offset, limit,
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
