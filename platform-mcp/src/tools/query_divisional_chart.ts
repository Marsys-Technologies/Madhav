/**
 * query_divisional_chart.ts — MCP Tier 3 surgical primitive: divisional chart (varga) lookup.
 *
 * What it does: Queries chart_facts filtered by divisional_chart column (e.g. D9, D10),
 * returning house positions and planet placements in any supported varga chart.
 * This is a direct L1 data read — no synthesis or planner.
 *
 * Source engine: platform/src/lib/retrieve/divisional_query.ts
 * DB table:      chart_facts (WHERE divisional_chart = $varga)
 * Coverage:      D1 through D60 (149 rows across all vargas)
 *
 * TR-P4-S1: new MCP wrapper.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'

const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

export const VALID_DIVISIONS = [
  'D1', 'D2', 'D3', 'D4', 'D7', 'D9', 'D10',
  'D12', 'D16', 'D20', 'D24', 'D27', 'D30',
  'D40', 'D45', 'D60',
] as const

export type VargaCode = typeof VALID_DIVISIONS[number]

const QUERY_DIVISIONAL_CHART_DESCRIPTION =
  'Divisional chart (varga) placement lookup. Returns house positions and planet placements ' +
  'in any of the 16 supported divisional charts: ' +
  'D1 (Rasi / birth), D2 (Hora), D3 (Drekkana), D4 (Chaturthamsha), D7 (Saptamsha), ' +
  'D9 (Navamsha — soul & spouse), D10 (Dasamsha — career), D12 (Dwadasamsha — lineage), ' +
  'D16 (Shodasamsha), D20 (Vimshamsha), D24 (Chaturvimshamsha), D27 (Nakshatramsha), ' +
  'D30 (Trimshamsha), D40 (Khavedamsha), D45 (Akshavedamsha), D60 (Shashtiamsha — karma). ' +
  'Use when the query involves a specific varga chart or requires varga confirmation of D1 placements. ' +
  'Prefer query_chart_facts with divisional_chart filter for individual fact rows.'

const QueryDivisionalChartInputSchema = z.object({
  chart_id: z.string().optional().describe(
    "Chart UUID; defaults to the native's chart (362f9f17-95a5-490b-a5a7-027d3e0efda0)."
  ),
  division: z.enum(VALID_DIVISIONS).describe(
    'Divisional chart code. D1=Rasi, D9=Navamsha, D10=Dasamsha, D60=Shashtiamsha, etc.'
  ),
  planet: z.string().optional().describe(
    'Optional planet filter (e.g. "Saturn", "Moon"). Filters rows by planet name in value_json.'
  ),
  house: z.number().int().min(1).max(12).optional().describe(
    'Optional house filter (1–12). Filters rows where value_json.house matches.'
  ),
  tier: z.string().optional().default('super_admin'),
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

      const params: Record<string, unknown> = {
        chart_id: args.chart_id ?? NATIVE_CHART_ID,
        varga: args.division,
      }
      if (args.planet) params['planet'] = args.planet
      if (args.house !== undefined) params['house'] = args.house

      const { status, envelope } = await callPlatformPrimitive(
        'divisional_query',
        params,
        principal
      )

      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }
      return okResult(envelope)
    }
  )
}
