/**
 * query_varshphal.ts — MCP Tier 3 surgical primitive: Varshaphala (Tajika) annual-chart lookup.
 *
 * What it does: Queries the varshaphala table for a given chart_id and target year,
 * returning the Solar Return UTC, Ascendant, and 9-graha sidereal positions.
 * This is a direct L1 data read — no synthesis or planner.
 *
 * Source engine: platform/src/lib/retrieve/query_varshaphala.ts
 * DB table:      varshaphala (migration 025_varshaphala.sql)
 * Coverage:      1984–2061 for native chart (pyswisseph + Lahiri ayanamsha)
 *
 * Note: Year-lord (Varshesha) and Muntha are NOT included — they live at the
 * synthesis layer.
 *
 * Tier visibility: super_admin + acharya only (varshaphal is advanced Tajika;
 * client tier uses holistic_bundle for temporal context).
 *
 * TR-P4-S1: new MCP wrapper.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'

const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

const QUERY_VARSHPHAL_DESCRIPTION =
  'Varshaphala (Tajika) annual-chart lookup. Returns the Solar Return UTC, Ascendant, ' +
  'and 9-graha sidereal positions for the requested Gregorian year (single year) or a ' +
  'range of years (year_start + year_end, max 20 years). ' +
  'The substrate is engine-computed via pyswisseph + Lahiri; covers 1984–2061 for the native chart. ' +
  'Year-lord (Varshesha) and Muntha are synthesis-layer outputs — not included here. ' +
  'Prefer query_chart_facts({category: "varshphal"}) for individual varshphal chart_facts rows. ' +
  'Tier: super_admin + acharya only.'

const QueryVarshphalInputSchema = z.object({
  chart_id: z.string().optional().describe(
    "Chart UUID; defaults to the native's chart (362f9f17-95a5-490b-a5a7-027d3e0efda0)."
  ),
  year: z.number().int().min(1900).max(2100).optional().describe(
    'Gregorian year for the Solar Return, e.g. 2026. Use for single-year lookup.'
  ),
  year_start: z.number().int().min(1900).max(2100).optional().describe(
    'Start year for range query (inclusive). Use with year_end for multi-year retrieval.'
  ),
  year_end: z.number().int().min(1900).max(2100).optional().describe(
    'End year for range query (inclusive, max 20 years from year_start).'
  ),
  tier: z.string().optional().default('super_admin'),
})

type QueryVarshphalInput = z.infer<typeof QueryVarshphalInputSchema>

export function registerQueryVarshphal(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_varshphal',
    QUERY_VARSHPHAL_DESCRIPTION,
    QueryVarshphalInputSchema.shape,
    async (args: QueryVarshphalInput) => {
      const principal = getPrincipal()

      // Tier check: super_admin + acharya only.
      if (principal.audience_tier === 'client') {
        return errorResult({
          ok: false,
          error: 'Forbidden',
          message: 'query_varshphal is restricted to super_admin and acharya tiers.',
        })
      }

      const chart_id = args.chart_id ?? NATIVE_CHART_ID

      // Range mode: year_start + year_end provided.
      if (args.year_start !== undefined && args.year_end !== undefined) {
        const start = args.year_start
        const end = Math.min(args.year_end, start + 19) // cap at 20 years
        const years = Array.from({ length: end - start + 1 }, (_, i) => start + i)
        const results = await Promise.all(
          years.map(y =>
            callPlatformPrimitive(
              'query_varshaphala',
              { chart_id, year: y },
              principal
            )
          )
        )
        const failed = results.find(r => !r.envelope.ok || r.status >= 400)
        if (failed) {
          return errorResult(failed.envelope)
        }
        return okResult({
          mode: 'range',
          year_start: start,
          year_end: end,
          charts: results.map(r => r.envelope),
        })
      }

      // Single-year mode (backward compatible).
      if (args.year === undefined) {
        return errorResult({
          ok: false,
          error: 'BadRequest',
          message: 'Provide either year (single) or both year_start and year_end (range).',
        })
      }

      const { status, envelope } = await callPlatformPrimitive(
        'query_varshaphala',
        {
          chart_id,
          year: args.year,
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
