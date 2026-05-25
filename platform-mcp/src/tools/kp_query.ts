/**
 * kp_query.ts — MCP Tier 3 surgical primitive: KP cusp and planet significator lookup.
 *
 * What it does: Queries chart_facts for Krishnamurti Paddhati (KP) data — cusp
 * significators, planet significators, and star lord / sub lord / sub-sub lord chains
 * for cusps 1–12 and all 9 planets. Reads categories kp_cusp, kp_planet, kp_significator
 * from FORENSIC §4 authoritative values (chart_facts). This is a direct L1 data read
 * that bypasses the planner and synthesis stages. Tagged surgical: true in the epistemics block.
 *
 * When to prefer: Use kp_query for KP-system house occupation, signification, and ruling
 * planet queries anchored to the FORENSIC chart_facts store. Prefer query_kp_ruling_planets
 * when you need the swisseph-Lahiri computed substrate (kp_sublords) for non-FORENSIC charts
 * or forward-looking transit-time KP queries. Prefer holistic_bundle when cross-domain
 * synthesis or interpretation is also required.
 *
 * Input shape hints:
 *   cusp — optional int 1–12; filter to a specific house cusp.
 *   planet — optional string; filter to a specific planet.
 *   query_type — optional enum: 'significators'|'star_lord'|'sub_lord'|'sub_sub_lord'|'all' (default 'all').
 *
 * Output shape preview: {ok, result: {results: ToolBundleResult[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: kp_query({cusp: 10, query_type: 'significators'}) →
 *   {ok: true, result: {results: [{fact_id: 'KP.CUSP.10', category: 'kp_cusp', ...}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const KP_QUERY_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Queries chart_facts for KP (Krishnamurti Paddhati) data — cusp significators, ' +
    'planet significators, and star lord / sub lord / sub-sub lord chains for cusps 1–12 and all 9 planets. ' +
    'Reads FORENSIC §4 authoritative values (categories: kp_cusp, kp_planet, kp_significator). ' +
    'Surgical primitive — bypasses planner and synthesis stages.',
  coverageHint: 'KP cusp (12 rows), planet (9 rows), significator (7 rows) categories from chart_facts',
  whenToPrefer:
    'Use kp_query for KP house occupation, signification, and ruling planet queries anchored to FORENSIC chart_facts. ' +
    'Prefer query_kp_ruling_planets when you need the swisseph-Lahiri computed substrate (kp_sublords) ' +
    'for non-FORENSIC charts or forward-looking transit-time KP queries. ' +
    'Prefer holistic_bundle when cross-domain synthesis or interpretation is also required.',
})

const KpQueryInputSchema = z.object({
  cusp: z.number().int().min(1).max(12).optional().describe(
    'Filter to a specific house cusp (1–12). Returns kp_cusp + kp_significator rows for that cusp.'
  ),
  planet: z.string().optional().describe(
    'Filter to a specific planet (e.g. "Sun", "Moon", "Saturn"). Returns kp_planet rows matching the planet name.'
  ),
  query_type: z.enum(['significators', 'star_lord', 'sub_lord', 'sub_sub_lord', 'all']).optional().default('all').describe(
    'Type of KP data to retrieve. "significators" = house signification chains; ' +
    '"star_lord" / "sub_lord" / "sub_sub_lord" = specific lord level; "all" = all available KP data (default).'
  ),
})

type KpQueryInput = z.infer<typeof KpQueryInputSchema>

export function registerKpQuery(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'kp_query',
    KP_QUERY_DESCRIPTION,
    KpQueryInputSchema.shape,
    async (args: KpQueryInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'kp_query',
        {
          ...(args.cusp !== undefined ? { cusp: args.cusp } : {}),
          ...(args.planet ? { planet: args.planet } : {}),
          ...(args.query_type !== undefined ? { query_type: args.query_type } : {}),
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
