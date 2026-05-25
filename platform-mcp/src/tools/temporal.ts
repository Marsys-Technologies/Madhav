/**
 * temporal.ts — MCP Tier 3 surgical primitive: current transit and ephemeris data.
 *
 * What it does: Calls the Python sidecar HTTP endpoints to retrieve current transit,
 * ephemeris, dasha chain, and related temporal data for the native. Returns the raw
 * ToolBundle result without synthesis. Supports optional date range scoping, and
 * flags to include transits, ephemeris, and/or dasha chain data. This is a direct
 * L1 temporal data read that bypasses the planner and synthesis stages. Tagged
 * surgical: true in the epistemics block.
 *
 * When to prefer: Use temporal when you need live or date-scoped transit data,
 * current dasha chain, or ephemeris positions. Prefer query_dasha_periods for
 * structured dasha period SQL queries with filters. Prefer query_ephemeris for
 * fine-grained ephemeris SQL data. Prefer holistic_bundle when cross-domain
 * synthesis or interpretation across all layers is also required.
 *
 * Input shape hints:
 *   date_from — optional YYYY-MM-DD; start of the date window (defaults to today).
 *   date_to — optional YYYY-MM-DD; end of the date window (defaults to today).
 *   include_transits — optional boolean; if true (default), include /transits sidecar call.
 *   include_ephemeris — optional boolean; if true, include /ephemeris sidecar call.
 *   include_dashas — optional boolean; if true, include /dasha_chain sidecar call.
 *   chart_id — optional UUID; scope to a specific chart (defaults to native chart).
 *
 * Output shape preview: {ok, result: {results: ToolBundleResult[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: temporal({date_from: "2026-06-01", date_to: "2026-06-30", include_transits: true, include_dashas: true}) →
 *   {ok: true, result: {results: [{content: "...", source_canonical_id: "TEMPORAL_DATA", ...}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const TEMPORAL_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Retrieves current transit, ephemeris, and dasha chain data for the native ' +
    'by calling the Python sidecar. Returns raw ToolBundle results (transits, ephemeris positions, ' +
    'dasha chain) for a given date range without synthesis. Surgical primitive — bypasses planner and synthesis stages.',
  coverageHint: 'Live sidecar data: /transits, /ephemeris, /dasha_chain endpoints',
  whenToPrefer:
    'Use temporal when you need live or date-scoped transit positions, current dasha chain, or ephemeris positions. ' +
    'Prefer query_dasha_periods for structured dasha SQL queries with filters. ' +
    'Prefer query_ephemeris for fine-grained ephemeris SQL data. ' +
    'Prefer holistic_bundle when cross-domain synthesis is also required.',
})

const TemporalInputSchema = z.object({
  date_from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe(
    'Start of the date window in YYYY-MM-DD format. Defaults to today.'
  ),
  date_to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional().describe(
    'End of the date window in YYYY-MM-DD format. Defaults to today.'
  ),
  include_transits: z.boolean().optional().default(true).describe(
    'If true (default), include the /transits sidecar call — current planetary positions relative to natal chart.'
  ),
  include_ephemeris: z.boolean().optional().default(false).describe(
    'If true, include the /ephemeris sidecar call — planet longitudes for the given date range.'
  ),
  include_dashas: z.boolean().optional().default(false).describe(
    'If true, include the /dasha_chain sidecar call — active Vimshottari dasha/antardasha chain at date_from.'
  ),
  chart_id: z.string().uuid().optional().describe(
    'UUID of a specific chart to scope the query to. Defaults to the native chart (Abhisek Mohanty).'
  ),
})

type TemporalInput = z.infer<typeof TemporalInputSchema>

export function registerTemporal(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'temporal',
    TEMPORAL_DESCRIPTION,
    TemporalInputSchema.shape,
    async (args: TemporalInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'temporal',
        {
          ...(args.date_from ? { date_from: args.date_from } : {}),
          ...(args.date_to ? { date_to: args.date_to } : {}),
          ...(args.include_transits !== undefined ? { include_transits: args.include_transits } : {}),
          ...(args.include_ephemeris !== undefined ? { include_ephemeris: args.include_ephemeris } : {}),
          ...(args.include_dashas !== undefined ? { include_dashas: args.include_dashas } : {}),
          ...(args.chart_id ? { chart_id: args.chart_id } : {}),
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
