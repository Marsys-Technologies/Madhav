/**
 * query_varshphal.ts — MCP Tier 3 surgical primitive: Tajaka annual chart lookup.
 *
 * What it does: Returns the Tajaka (solar return) annual chart for a given year —
 * planet positions in the Varshaphala lagna, solar return UTC timestamp, and
 * ayanamsha used. The underlying `query_varshaphala` retrieval tool reads from
 * the `varshaphala` table (pre-computed by compute_varshaphala.py).
 *
 * Source: platform/src/lib/retrieve/query_varshaphala.ts
 * Data: varshaphala table, migrations/025_varshaphala.sql
 * Engine: platform/scripts/temporal/compute_varshaphala.py
 *
 * Note: Year-lord (Varshesha) and Muntha are NOT in the engine output —
 * they live at the synthesis layer. Use holistic_bundle for synthesized
 * Varshaphala interpretation.
 *
 * When to prefer: Use for "What is the annual chart for year X?", "Which
 * planets are strong in the 2026 solar return?", or any Tajaka analysis.
 * Prefer holistic_bundle when you need Varshaphala synthesized against the natal chart.
 *
 * Output shape preview: {ok, result: {varshaphala: {year, solar_return_utc,
 *   ascendant_sidereal, ascendant_sign, planet_positions, ayanamsha}[]}, trace_id,
 *   epistemics: {surgical: true}}.
 *
 * Example: query_varshphal({year: 2026}) →
 *   {ok: true, result: {varshaphala: [{year: 2026, solar_return_utc: "2026-02-05T...",
 *   ascendant_sign: "Sagittarius", planet_positions: {...}}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

export const QUERY_VARSHPHAL_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Returns the Tajaka (solar return) annual chart for a given year or year range — ' +
    'planet positions in the Varshaphala lagna, solar return UTC timestamp, ascendant, and ayanamsha. ' +
    'Data is pre-computed by the Varshaphala engine and stored in the varshaphala table.',
  coverageHint: 'varshaphala table; pre-computed Tajaka positions; year-lord and Muntha at synthesis layer only',
  whenToPrefer:
    'Use for "What is the 2026 annual chart?", "Which planets dominate this solar return?", or any Tajaka placement query. ' +
    'Prefer holistic_bundle for synthesised Varshaphala interpretation against the natal chart.',
})

const QueryVarshphalInputSchema = z.object({
  year: z.number().int().optional().describe(
    'Target solar return year (e.g. 2026). Omit to return all available years.'
  ),
  year_start: z.number().int().optional().describe(
    'Start of year range (inclusive). Use with year_end for multi-year retrieval.'
  ),
  year_end: z.number().int().optional().describe(
    'End of year range (inclusive). Use with year_start for multi-year retrieval.'
  ),
  ayanamsha: z.string().optional().describe(
    'Ayanamsha system. Default: "lahiri". Options: lahiri, raman, krishnamurti.'
  ),
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
      const { status, envelope } = await callPlatformPrimitive(
        'query_varshphal',
        {
          year: args.year,
          year_start: args.year_start,
          year_end: args.year_end,
          ayanamsha: args.ayanamsha,
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
