/**
 * query_chart_facts.ts — MCP Tier 3 surgical primitive: parametric chart-fact lookup.
 *
 * What it does: Queries the 795-row chart_facts table with structured filters
 * (category, planet, house, as_of_date). Returns raw chart-fact rows — birth
 * data, dignity computations, shadbala, aspects, nakshatra placements, divisional
 * chart positions — without running the planner or synthesis. This is a direct
 * L1 data read. The response is tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use query_chart_facts when the question is a single fact
 * lookup ("What is Saturn's shadbala?" / "Which planets are in house 7?").
 * Prefer ask_madhav when synthesis or interpretation is needed alongside the fact.
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

const QueryChartFactsInputSchema = z.object({
  category: z.string().describe(
    'Fact category to query. Examples: "shadbala", "dignity", "nakshatra", ' +
    '"aspect", "house_placement", "dasha_vimshottari", "divisional_D9".'
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
    'What it does: Queries the 795-row chart_facts table with structured filters ' +
    '(category, planet, house, as_of_date) and returns raw fact rows without synthesis. ' +
    'When to prefer: Use for single fact lookups ("What is Saturn\'s shadbala?"). ' +
    'Prefer ask_madhav when interpretation is needed. ' +
    'Prefer query_signals for MSR signal corpus data. ' +
    'Input shape hints: category is required (e.g. "shadbala", "dignity"); ' +
    'planet/house/as_of_date are optional filters; limit defaults to 50. ' +
    'Output shape preview: {ok, result: {rows: ChartFactRow[]}, trace_id, epistemics: {surgical: true}}. ' +
    'Example: query_chart_facts({category: "shadbala", planet: "Saturn"}) → rows with strength data.',
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
      const text = JSON.stringify(envelope, null, 2)
      return {
        content: [{ type: 'text' as const, text }],
        isError: !envelope.ok || status >= 400,
      }
    }
  )
}
