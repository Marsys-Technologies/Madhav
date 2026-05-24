/**
 * query_chart_facts.ts — MCP Tier 3 surgical primitive: parametric chart-fact lookup.
 *
 * What it does: Queries the 2,717-row chart_facts table with structured filters
 * (category, planet, house, as_of_date). Returns raw chart-fact rows — birth
 * data, dignity computations, shadbala, aspects, nakshatra placements, divisional
 * chart positions — without running the planner or synthesis. This is a direct
 * L1 data read. The response is tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use query_chart_facts when the question is a single fact
 * lookup ("What is Saturn's shadbala?" / "Which planets are in house 7?").
 * Prefer holistic_bundle when synthesis or interpretation is needed alongside the fact.
 * Prefer query_signals when you need MSR signal corpus data rather than raw chart facts.
 *
 * Input shape hints:
 *   category — single category string; e.g. "shadbala", "aspect", "dasha_vimshottari".
 *   categories — optional array of category strings for multi-category batching in one call.
 *     When provided, overrides `category`. Response uses rows_by_category: {cat: rows[]}.
 *   planet — optional; filter to a specific planet (e.g. "Saturn", "Moon").
 *   house — optional; filter to a specific house number (1–12).
 *   as_of_date — optional ISO date; filters time-sensitive facts to that date.
 *   limit — optional; max rows to return (default 50).
 *
 * Output shape preview (single): {ok, result: {rows: ChartFactRow[]}, trace_id, epistemics: {surgical: true}}.
 * Output shape preview (batched): {ok, result: {rows_by_category: {cat: ChartFactRow[]}}, trace_id, epistemics: {surgical: true}}.
 *
 * Example (single): query_chart_facts({category: "shadbala", planet: "Saturn"}) →
 *   {ok: true, result: {rows: [{planet: "Saturn", category: "shadbala", ...}]}, ...}
 * Example (batched): query_chart_facts({categories: ["planet", "house", "yoga"]}) →
 *   {ok: true, result: {rows_by_category: {planet: [...], house: [...], yoga: [...]}}, ...}
 *
 * MCPT v3.2 P4b: Added `categories` array batching param.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'
import { okResult, errorResult } from './_envelope.js'

/**
 * F.3 fix: category list derived from ChartFactsCategory enum in
 * platform/src/lib/retrieve/chart_facts_query.ts:21–30.
 * Keep this array in sync with that enum — it is the single source of truth.
 */
export const CHART_FACTS_CATEGORIES = [
  'house', 'dasha_chara', 'planet', 'dasha_vimshottari', 'saham',
  'sensitive_point', 'birth_metadata', 'strength_extra', 'yoga',
  'dasha_yogini', 'deity_assignment', 'shadbala', 'ashtakavarga_sav',
  'kp_cusp', 'navatara', 'panchang', 'cusp', 'arudha_occupancy',
  'bhava_bala', 'chandra_placement', 'mrityu_bhaga', 'longevity_indicator',
  'arudha', 'aspect', 'chalit_shift', 'kp_planet', 'special_lagna',
  'strength', 'upagraha', 'ashtakavarga_bav', 'kakshya_zone',
  'mercury_convergence', 'ashtakavarga_pinda', 'ishta_kashta',
  'kp_significator', 'varshphal', 'avastha',
] as const

export const QUERY_CHART_FACTS_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Queries the chart_facts table with structured filters ' +
    '(category, planet, house, as_of_date) and returns raw fact rows without synthesis. ' +
    'category is required; planet/house/as_of_date are optional filters; limit defaults to 50.',
  enumSource: CHART_FACTS_CATEGORIES,
  coverageHint: '2,717 rows across 27 categories',
  whenToPrefer:
    'Use for single fact lookups ("What is Saturn\'s shadbala?", "Which planets are in house 7?"). ' +
    'Prefer query_signals for MSR signal corpus data. ' +
    'Prefer holistic_bundle when synthesis or multi-tool retrieval is needed.',
  tierAccess: 'All tiers. super_admin + acharya see all 37 categories; client tier sees curated subset.',
})

// Keep internal alias for the tool registration
const CHART_FACTS_TOOL_DESCRIPTION = QUERY_CHART_FACTS_DESCRIPTION

const QueryChartFactsInputSchema = z.object({
  category: z.string().optional().describe(
    `Single fact category to query. Must be one of: ${CHART_FACTS_CATEGORIES.join(', ')}.`
  ),
  categories: z.array(z.string()).optional().describe(
    'Optional array of categories to fetch in one call (multi-category batching). ' +
    'When provided, overrides `category`. Response groups results by category in ' +
    'result.rows_by_category: {category: rows[]}. ' +
    `Valid values: ${CHART_FACTS_CATEGORIES.join(', ')}.`
  ),
  planet: z.string().optional().describe('Filter to a specific planet (e.g. "Saturn", "Moon").'),
  house: z.number().int().min(1).max(12).optional().describe('Filter to a specific house (1–12).'),
  as_of_date: z.string().optional().describe('ISO date for time-sensitive fact filtering.'),
  divisional_chart: z.string().optional().describe('Optional divisional chart filter. Examples: "D1", "D9", "D10", "D12". When provided, only rows matching this divisional_chart are returned.'),
  limit: z.number().int().min(1).max(200).optional().default(50).describe('Max rows to return.'),
  include_empty_counts: z.boolean().optional().default(false).describe(
    'When true, returns ALL known categories from CHART_FACTS_CATEGORIES even if they have 0 rows. ' +
    'Each category object includes a populated_count field (number of rows in chart_facts for that category). ' +
    'When false (default), only returns categories that have at least one row, each annotated with populated_count.'
  ),
})

type QueryChartFactsInput = z.infer<typeof QueryChartFactsInputSchema>

export function registerQueryChartFacts(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_chart_facts',
    CHART_FACTS_TOOL_DESCRIPTION,
    QueryChartFactsInputSchema.shape,
    async (args: QueryChartFactsInput) => {
      const principal = getPrincipal()

      // Determine whether batched (categories array) or single-category mode
      const isBatched = Array.isArray(args.categories) && args.categories.length > 0

      // --- Step 1: Build a per-category count map ---
      // Strategy: fetch all categories in one batched call (limit=1 per category just for
      // structure), then use row-lengths as a proxy count. When include_empty_counts=true
      // we need counts for every known category, so we always run the full-category pre-query.
      // When include_empty_counts=false we only need counts for the categories in the response;
      // those are derived from the main call row lengths (see Step 3).
      let countMap: Record<string, number> = {}

      if (args.include_empty_counts) {
        // Pre-query: fetch all known categories batched to build the count map.
        // We use limit=200 (max) to get accurate row lengths as count proxies.
        const countQueryResult = await callPlatformPrimitive(
          'query_chart_facts',
          {
            category: [...CHART_FACTS_CATEGORIES],
            batched: true,
            limit: 200,
          },
          principal
        )
        if (countQueryResult.envelope.ok && countQueryResult.status < 400) {
          const countEnv = countQueryResult.envelope as Record<string, unknown>
          const countData = countEnv['result'] as Record<string, unknown> | undefined
          if (countData) {
            // Try ToolBundle.results[0].content (JSON) first, then direct rows_by_category
            const bundleResults = countData['results'] as Array<{ content: string }> | undefined
            let rowsByCat: Record<string, unknown[]> | undefined
            if (bundleResults && bundleResults.length > 0 && typeof bundleResults[0].content === 'string') {
              try {
                const parsed = JSON.parse(bundleResults[0].content) as Record<string, unknown>
                rowsByCat = parsed['rows_by_category'] as Record<string, unknown[]> | undefined
              } catch { /* ignore parse errors */ }
            }
            if (!rowsByCat && typeof countData['rows_by_category'] === 'object') {
              rowsByCat = countData['rows_by_category'] as Record<string, unknown[]>
            }
            if (rowsByCat) {
              for (const [cat, rows] of Object.entries(rowsByCat)) {
                countMap[cat] = Array.isArray(rows) ? rows.length : 0
              }
            }
          }
        }
      }

      // --- Step 2: Fetch the actual data ---
      const { status, envelope } = await callPlatformPrimitive(
        'query_chart_facts',
        {
          // When categories array is provided, pass it as `category` (platform supports array)
          // and set the batched flag so the platform groups results by category.
          ...(isBatched
            ? { category: args.categories, batched: true }
            : { category: args.category }
          ),
          ...(args.planet ? { planet: args.planet } : {}),
          ...(args.house !== undefined ? { house: args.house } : {}),
          ...(args.as_of_date ? { as_of_date: args.as_of_date } : {}),
          ...(args.divisional_chart ? { divisional_chart: args.divisional_chart } : {}),
          limit: args.limit ?? 50,
        },
        principal
      )
      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }

      // --- Step 3: Annotate response with populated_count ---
      // Cast envelope result to a mutable shape so we can enrich it.
      const envelopeResult = (envelope as Record<string, unknown>)['result'] as Record<string, unknown> | undefined

      if (envelopeResult) {
        // Try to unwrap ToolBundle.results[0].content if the platform wraps results that way.
        // If so, the actual data lives inside the JSON string.
        let rowsByCategory: Record<string, unknown[]> | undefined
        let singleRows: unknown[] | undefined

        const bundleResults = envelopeResult['results'] as Array<{ content: string }> | undefined
        if (bundleResults && bundleResults.length > 0 && typeof bundleResults[0].content === 'string') {
          try {
            const parsed = JSON.parse(bundleResults[0].content) as Record<string, unknown>
            if (isBatched && parsed['rows_by_category']) {
              rowsByCategory = parsed['rows_by_category'] as Record<string, unknown[]>
            } else if (!isBatched && parsed['rows']) {
              singleRows = parsed['rows'] as unknown[]
            }
          } catch { /* ignore */ }
        }
        if (!rowsByCategory && !singleRows) {
          if (isBatched && envelopeResult['rows_by_category']) {
            rowsByCategory = envelopeResult['rows_by_category'] as Record<string, unknown[]>
          } else if (!isBatched && envelopeResult['rows']) {
            singleRows = envelopeResult['rows'] as unknown[]
          }
        }

        if (isBatched && rowsByCategory) {
          // Batched mode: annotate each category bucket with populated_count.
          // For include_empty_counts=false: use row lengths as count proxy.
          for (const [cat, rows] of Object.entries(rowsByCategory)) {
            if (!(cat in countMap)) {
              countMap[cat] = Array.isArray(rows) ? rows.length : 0
            }
          }

          // Build annotated structure
          const annotated: Record<string, { rows: unknown[]; populated_count: number }> = {}
          for (const [cat, rows] of Object.entries(rowsByCategory)) {
            annotated[cat] = {
              rows: Array.isArray(rows) ? rows : [],
              populated_count: countMap[cat] ?? 0,
            }
          }

          // When include_empty_counts=true, add all known categories not yet present
          if (args.include_empty_counts) {
            for (const cat of CHART_FACTS_CATEGORIES) {
              if (!(cat in annotated)) {
                annotated[cat] = { rows: [], populated_count: countMap[cat] ?? 0 }
              }
            }
          }

          // Write annotated rows_by_category back to envelope
          if (bundleResults && bundleResults.length > 0) {
            // ToolBundle wrapping: update the JSON string in results[0].content
            const baseContent = (() => {
              try { return JSON.parse(bundleResults[0].content) as Record<string, unknown> } catch { return {} }
            })()
            baseContent['rows_by_category'] = annotated
            ;(envelopeResult['results'] as Array<{ content: string }>)[0].content = JSON.stringify(baseContent)
          } else {
            envelopeResult['rows_by_category'] = annotated
          }

        } else if (!isBatched) {
          // Single-category mode: add populated_count at result level.
          const rows = singleRows ?? (envelopeResult['rows'] as unknown[] | undefined) ?? []
          const cat = args.category ?? ''
          if (!(cat in countMap)) {
            countMap[cat] = Array.isArray(rows) ? rows.length : 0
          }
          envelopeResult['populated_count'] = countMap[cat] ?? 0

          // When include_empty_counts=true, also expose all_category_counts
          if (args.include_empty_counts) {
            const allCategoryCounts: Record<string, number> = {}
            for (const c of CHART_FACTS_CATEGORIES) {
              allCategoryCounts[c] = countMap[c] ?? 0
            }
            envelopeResult['all_category_counts'] = allCategoryCounts
          }
        }
      }

      return okResult(envelope)
    }
  )
}
