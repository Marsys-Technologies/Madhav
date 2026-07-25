/**
 * resolve_concept.ts — shared concept resolution (alias table + live fact_category fallback)
 * ============================================================================
 * SATYA-ŚEṢA W1 (Truth-Residue Campaign, Builder B1; SATYA_SHESHA_BRIEF_v1_0.md §2 W1).
 *
 * Extracted from `concept_locate.ts`'s inline two-pass resolution (seed alias table, then a
 * live `fact_category` substring match) into a single shared, chart-scoped function so BOTH
 * `concept_locate` (the standalone resolver tool) AND any query-shaped serving path that can
 * return a bare `{facts: [], total: 0}` (chart_facts_query / query_chart_facts /
 * ganita_chart_facts_get and siblings) call the SAME resolution logic to build an honest
 * `resolver_suggestion` instead of a silent empty.
 *
 * This is the fix for UAT-DARPANA S4-03: "What's my exact Gulika placement?" ran
 * `ganita_chart_facts_get(keyword="gulika")`, got `{facts: [], total: 0}` (the `keyword` filter
 * only ILIKEs fact_key/fact_value_text — it never searched fact_category, and GULIKA lives
 * under category `sensitive_point_gulika_mandi`), and the answering LLM asserted, in
 * self-branded "honest" language, that Gulika "isn't in your computed chart data." It IS there.
 * The bug was never the LLM's synthesis — it was that the serving layer returned a bare,
 * contextless empty with no signal that a resolvable alias exists.
 *
 * Absence Protocol (EL-07): a caller MUST run this resolution before phrasing a served string
 * as ontological absence ("not in your data" / "doesn't exist"). A genuine MISS (both passes
 * empty) still returns `null` — the caller phrases the honest "no concept match either", never
 * a fabricated pointer (SATYA_SHESHA_BRIEF §2 W1: "Never fabricate a suggestion").
 */
import { query } from '@/lib/db/client'
import { resolveConceptAlias, CONCEPT_ALIASES, type ConceptResolution } from './concept_aliases'

export { CONCEPT_ALIASES }

export type ResolverSuggestion = {
  resolved: true
  matched_alias: string | null
  concept_id: string | null
  fact_categories: string[]
  // 'direct_category_match' is this module's own pass-2 outcome (live fact_category
  // substring match) — not part of ConceptResolution['resolved_via'] (which only covers the
  // seed-alias-table passes), so it is unioned in explicitly here.
  resolved_via: ConceptResolution['resolved_via'] | 'direct_category_match'
  note: string
}

/** Live fact_category list for the given chart — same query concept_locate.ts uses. Cheap
 *  (DISTINCT over chart_facts, no grouping) and short-cacheable at the route layer. */
export async function liveFactCategories(chartId: string): Promise<string[]> {
  const result = await query<{ fact_category: string }>(
    `SELECT DISTINCT fact_category FROM chart_facts WHERE chart_id = $1 ORDER BY fact_category`,
    [chartId],
  )
  return result.rows.map((r) => r.fact_category)
}

/**
 * Resolve `term` against the seed alias table, then (if that misses) the live fact_category
 * list for `chartId`. Returns `null` on a genuine miss (both passes empty) — the caller is
 * responsible for phrasing the honest "no concept match either" message, never fabricating a
 * pointer.
 */
export async function resolveConceptWithLiveFallback(
  term: string,
  chartId: string,
): Promise<ResolverSuggestion | null> {
  const q = term.trim()
  if (!q) return null

  const aliasResult = resolveConceptAlias(q)
  if (aliasResult.resolved) {
    return {
      resolved: true,
      matched_alias: aliasResult.matched_alias,
      concept_id: aliasResult.concept_id,
      fact_categories: aliasResult.fact_categories,
      resolved_via: aliasResult.resolved_via,
      note: `"${q}" is served under fact_category ${aliasResult.fact_categories.map((c) => `"${c}"`).join(', ')} ` +
        `(matched via the concept-alias table on "${aliasResult.matched_alias}"). Retry this call with ` +
        `category="${aliasResult.fact_categories[0]}" (or categories="${aliasResult.fact_categories.join(',')}" for the full family).`,
    }
  }

  const liveCategories = await liveFactCategories(chartId)
  const qLower = q.toLowerCase()
  const directMatches = liveCategories.filter(
    (c) => c.toLowerCase().includes(qLower) || qLower.includes(c.toLowerCase()),
  )
  if (directMatches.length > 0) {
    return {
      resolved: true,
      matched_alias: null,
      concept_id: directMatches[0],
      fact_categories: directMatches,
      resolved_via: 'direct_category_match',
      note: `"${q}" matches live fact_category value(s) ${directMatches.map((c) => `"${c}"`).join(', ')} ` +
        `for this chart by direct substring match. Retry this call with category="${directMatches[0]}".`,
    }
  }

  return null
}

/** Honest genuine-miss note — never a fabricated pointer. Mirrors concept_locate.ts's own
 *  empty_reason phrasing so both surfaces read consistently. */
export function noConceptMatchNote(term: string, chartId: string, liveCategoryCount: number): string {
  return (
    `No concept alias or live fact_category matched "${term}" — checked ${CONCEPT_ALIASES.length} seed ` +
    `alias entries and ${liveCategoryCount} live fact_category values for chart_id ${chartId}. This is a ` +
    `resolver MISS, not a claim that "${term}" categorically does not exist anywhere in Jyotish — only that ` +
    `it is not reachable under this name in the live schema today. Try get_database_schema to browse the ` +
    `full category/subject substrate, or rephrase with a more specific term.`
  )
}
