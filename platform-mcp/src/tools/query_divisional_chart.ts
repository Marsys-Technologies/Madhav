/**
 * query_divisional_chart.ts — MCP Tier 3 surgical primitive: divisional chart lookup.
 *
 * What it does: Returns planet positions in a specified Varga (divisional chart)
 * for the native's chart. Divisional charts include D9 (Navamsha), D10 (Dasamsha),
 * D7 (Saptamsha), D3 (Drekkana), and all others up to D60 (Shashtiamsha).
 * Data is pre-computed and stored in the divisional_charts table.
 *
 * Source: platform/src/lib/retrieve/query_divisional_chart.ts
 * Data: divisional_charts table, migrations/022_divisional_charts.sql
 * Engine: platform/scripts/temporal/compute_divisional_charts.py
 *
 * When to prefer: Use for "What is my Navamsha?", "Where is Saturn in D10?",
 * "Show me the D7 Saptamsha chart" or any Varga-specific placement question.
 * Prefer holistic_bundle for divisional chart data synthesized against the natal
 * chart with classical commentary.
 *
 * Varga codes: D1 (Rashi/natal), D2 (Hora), D3 (Drekkana), D4 (Chaturthamsha),
 *   D7 (Saptamsha), D9 (Navamsha), D10 (Dasamsha), D12 (Dwadashamsha),
 *   D16 (Shodashamsha), D20 (Vimsamsha), D24 (Chaturvimsamsha),
 *   D27 (Saptavimsamsha/Nakshatramsha), D30 (Trimsamsha), D40 (Khavedamsha),
 *   D45 (Akshavedamsha), D60 (Shashtiamsha), BIRTH (same as D1).
 *
 * Output shape preview: {ok, result: {divisional: {varga, planet_positions,
 *   ascendant_sign, ayanamsha}[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_divisional_chart({varga: "D9"}) →
 *   {ok: true, result: {divisional: [{varga: "D9", ascendant_sign: "Virgo",
 *   planet_positions: {Sun: {sign: "Sagittarius", house: 4, degree: 14.2}, ...}}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

const VARGA_CODES = [
  'D1', 'D2', 'D3', 'D4', 'D7', 'D9', 'D10', 'D12',
  'D16', 'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60', 'BIRTH',
] as const

type VargaCode = (typeof VARGA_CODES)[number]

export const QUERY_DIVISIONAL_CHART_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Returns planet positions in a specified Varga (divisional chart) — ' +
    'sign, house, degree, and dignity for each graha — pre-computed and stored in the ' +
    'divisional_charts table. Covers D1 through D60 plus BIRTH.',
  enumSource: VARGA_CODES,
  coverageHint: 'divisional_charts table; pre-computed Varga positions; D1–D60 + BIRTH',
  whenToPrefer:
    'Use for "What is my Navamsha?", "Where is Saturn in D10?", or any Varga placement query. ' +
    'Prefer holistic_bundle for divisional chart data synthesized with classical commentary.',
})

const QueryDivisionalChartInputSchema = z.object({
  varga: z.enum(VARGA_CODES).describe(
    'The divisional chart to retrieve. One of: D1 (Rashi), D2 (Hora), D3 (Drekkana), ' +
    'D4 (Chaturthamsha), D7 (Saptamsha), D9 (Navamsha), D10 (Dasamsha), D12 (Dwadashamsha), ' +
    'D16 (Shodashamsha), D20 (Vimsamsha), D24 (Chaturvimsamsha), D27 (Nakshatramsha), ' +
    'D30 (Trimsamsha), D40 (Khavedamsha), D45 (Akshavedamsha), D60 (Shashtiamsha), BIRTH.'
  ),
  planet: z.string().optional().describe(
    'Filter to a specific planet. One of: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu, Ascendant.'
  ),
  house: z.number().int().min(1).max(12).optional().describe(
    'Filter to planets in a specific house (1–12) in the requested Varga.'
  ),
  category: z.string().optional().describe(
    'Filter by category of data to return (e.g., "dignity", "aspects", "full"). Default returns all.'
  ),
})

type QueryDivisionalChartInput = z.infer<typeof QueryDivisionalChartInputSchema>

export function registerQueryDivisionalChart(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_divisional_chart',
    QUERY_DIVISIONAL_CHART_DESCRIPTION,
    QueryDivisionalChartInputSchema.shape,
    async (args: QueryDivisionalChartInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'query_divisional_chart',
        {
          varga: args.varga,
          planet: args.planet,
          house: args.house,
          category: args.category,
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
