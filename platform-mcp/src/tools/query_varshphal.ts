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
import type { Principal, McpEnvelopeSuccess } from '../types.js'
import { buildToolDescription } from './description_builder.js'

/**
 * DB key used by the varshaphala table (not the Firebase UUID).
 * All rows in the varshaphala table are keyed by this string identifier.
 */
const NATIVE_CHART_ID = 'abhisek_mohanty_primary'

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
  year: z.number().int().min(1900).max(2100).optional().describe(
    'Gregorian year for the Solar Return, e.g. 2026. Use for single-year lookup.'
  ),
  year_start: z.number().int().min(1900).max(2100).optional().describe(
    'Start year for range query (inclusive). Use with year_end for multi-year retrieval.'
  ),
  year_end: z.number().int().min(1900).max(2100).optional().describe(
    'End year for range query (inclusive, max 20 years from year_start).'
  ),
  ayanamsha: z.string().optional().describe(
    'Ayanamsha system. Default: "lahiri". Options: lahiri, raman, krishnamurti.'
  ),
  chart_id: z.string().optional().describe(
    'Chart identifier. Defaults to the native chart (abhisek_mohanty_primary). ' +
    'Override only when querying a non-native chart.'
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
              { chart_id, year: y, ayanamsha: args.ayanamsha },
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
          charts: results.map(r => (r.envelope as McpEnvelopeSuccess).result),
        })
      }

      // Single-year mode.
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
