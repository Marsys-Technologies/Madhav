/**
 * query_kp_ruling_planets.ts — MCP Tier 3 surgical primitive: KP ruling-planet table lookup.
 *
 * What it does: Reads from the kp_sublords table for a given chart_id and returns the
 * star lord / sub lord / sub-sub lord chains for the 9 grahas. This is the engine-computed
 * swisseph-Lahiri substrate distinct from kp_query (which reads FORENSIC §4 chart_facts).
 * Bypasses planner and synthesis stages. Tagged surgical: true in the epistemics block.
 *
 * Distinction from kp_query:
 *   - kp_query         → FORENSIC §4 KP authoritative values from chart_facts
 *   - query_kp_ruling_planets → swisseph-Lahiri computed kp_sublords (this tool)
 * Both tools coexist; consumers prefer chart_facts (kp_query) when chart_id matches
 * a FORENSIC-anchored native. This tool is the substrate for non-FORENSIC charts and
 * forward-looking transit-time KP queries.
 *
 * Input shape hints:
 *   chart_id — optional UUID; scope to a specific chart (defaults to native chart).
 *
 * Output shape preview: {ok, result: {results: ToolBundleResult[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_kp_ruling_planets({chart_id: '123e4567-e89b-12d3-a456-426614174000'}) →
 *   {ok: true, result: {results: [{planet: 'Saturn', star_lord: 'Venus', sub_lord: 'Sun', ...}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const QUERY_KP_RULING_PLANETS_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Reads the swisseph-Lahiri computed kp_sublords table and returns ' +
    'star lord / sub lord / sub-sub lord chains for all 9 grahas at the native chart moment. ' +
    'Optional chart_id UUID scopes to a specific chart (defaults to native chart). ' +
    'Surgical primitive — bypasses planner and synthesis stages.',
  coverageHint: 'kp_sublords substrate: 9 graha rows × star_lord / sub_lord / sub_sub_lord chains',
  whenToPrefer:
    'Use query_kp_ruling_planets when you need the swisseph-Lahiri computed substrate (kp_sublords) ' +
    'for non-FORENSIC charts or forward-looking transit-time KP queries. ' +
    'Prefer kp_query when chart_id is FORENSIC-anchored (reads authoritative chart_facts). ' +
    'Prefer holistic_bundle when cross-domain synthesis or interpretation is also required.',
})

const QueryKpRulingPlanetsInputSchema = z.object({
  chart_id: z.string().uuid().optional().describe(
    'UUID of a specific chart to scope the query to. Defaults to the native chart (Abhisek Mohanty).'
  ),
  planet: z.string().optional().describe(
    'Filter results to a specific planet (e.g. "Sun", "Moon", "Saturn", "Mercury"). ' +
    'When omitted, returns all 9 grahas. Case-insensitive partial match against the planet name.'
  ),
  ayanamsha: z.string().optional().describe(
    'Ayanamsha system to use for the lookup (e.g. "lahiri", "raman", "krishnamurti"). ' +
    'Defaults to "lahiri". Must match the ayanamsha value stored in kp_sublords for the requested chart.'
  ),
})

type QueryKpRulingPlanetsInput = z.infer<typeof QueryKpRulingPlanetsInputSchema>

export function registerQueryKpRulingPlanets(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_kp_ruling_planets',
    QUERY_KP_RULING_PLANETS_DESCRIPTION,
    QueryKpRulingPlanetsInputSchema.shape,
    async (args: QueryKpRulingPlanetsInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'query_kp_ruling_planets',
        {
          ...(args.chart_id ? { chart_id: args.chart_id } : {}),
          ...(args.planet ? { planet: args.planet } : {}),
          ...(args.ayanamsha ? { ayanamsha: args.ayanamsha } : {}),
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
