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
 *   category — required; e.g. "shadbala", "dignity", "nakshatra", "aspect",
 *     "house_placement", "dasha_vimshottari", "divisional_D9".
 *   planet — optional; filter to a specific planet (e.g. "Saturn", "Moon").
 *   house — optional; filter to a specific house number (1–12).
 *   as_of_date — optional ISO date; filters time-sensitive facts to that date.
 *   limit — optional; max rows to return (default 50).
 *
 * Output shape preview: {ok, result: {rows: ChartFactRow[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_chart_facts({category: "shadbala", planet: "Saturn"}) →
 *   {ok: true, result: {rows: [{planet: "Saturn", category: "shadbala",
 *   value: "7.4 rupas", ...}]}, epistemics: {surgical: true, confidence_band: "high"}}
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

const CHART_FACTS_TOOL_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Queries the 2,717-row chart_facts table with structured filters ' +
    '(category, planet, house, as_of_date) and returns raw fact rows without synthesis. ' +
    'When to prefer: Use for single fact lookups ("What is Saturn\'s shadbala?"). ' +
    'Prefer query_signals for MSR signal corpus data. ' +
    'Prefer holistic_bundle when synthesis or multi-tool retrieval is needed. ' +
    'Input shape hints: category is required; planet/house/as_of_date are optional filters; limit defaults to 50. ' +
    'Output shape: {ok, result: {rows: ChartFactRow[]}, trace_id, epistemics: {surgical: true}}.',
  enumSource: CHART_FACTS_CATEGORIES,
  coverageHint: '2,717 rows across 27 categories',
})

const QueryChartFactsInputSchema = z.object({
  category: z.string().describe(
    `Fact category to query. Must be one of: ${CHART_FACTS_CATEGORIES.join(', ')}.`
  ),
  planet: z.string().optional().describe('Filter to a specific planet (e.g. "Saturn", "Moon").'),
  house: z.number().int().min(1).max(12).optional().describe('Filter to a specific house (1–12).'),
  as_of_date: z.string().optional().describe('ISO date for time-sensitive fact filtering.'),
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
      const { status, envelope } = await callPlatformPrimitive(
        'query_chart_facts',
        {
          category: args.category,
          ...(args.planet ? { planet: args.planet } : {}),
          ...(args.house !== undefined ? { house: args.house } : {}),
          ...(args.as_of_date ? { as_of_date: args.as_of_date } : {}),
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
