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
      return okResult(envelope)
    }
  )
}
