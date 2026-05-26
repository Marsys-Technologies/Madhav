/**
 * holistic_bundle_tool.ts — MCP Tier 2 bundle: holistic 8-tool parallel read.
 *
 * Registers holistic_bundle as an MCP tool. Delegates to the bundle executor
 * which fans out across 8 primitives in parallel, with per-tool timeout + error
 * isolation. Results are cached 5 minutes (content-addressable).
 *
 * SSE streaming: available via /api/mcp/bundles/holistic_bundle (Next.js route).
 * This tool registration returns the final envelope synchronously (all sub-tools
 * settle before response, same as any other MCP tool).
 *
 * MCPT v3.1.0-S2
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { executeHolisticBundle } from '../bundles/holistic_bundle.js'
import type { Principal } from '../types.js'
import { okResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const HOLISTIC_BUNDLE_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Performs a parallel 8-tool holistic read of the MARSYS-JIS corpus, ' +
    'fanning out across MSR signals, CGM subgraph, UCN/RM/CDLM vector layers, LEL events, ' +
    'current panchang, and active dasha state. All sub-tools run concurrently with 8-second ' +
    'per-tool timeouts, error isolation, and 5-minute content-addressable caching.',
  whenToPrefer:
    'FIRST CALL when any synthesis question requires cross-layer context before reasoning. ' +
    'Use the subset param to restrict to specific layers (e.g., subset: ["MSR","DASHA"]). ' +
    'Prefer individual surgical primitives when you need only one data type without synthesis overhead. ' +
    'Supplementary surgical tools (UDA-2, channel:both): msr_sql, temporal, kp_query, ' +
    'query_kp_ruling_planets, pattern_register, resonance_register, cluster_atlas, ' +
    'contradiction_register, query_ucn_walk, query_cdlm_lookup, query_rm_walk, ' +
    'query_jaimini_drishti, timeline_query, query_signal_state — call these directly for ' +
    'targeted follow-up after holistic_bundle establishes cross-layer context.',
  tierAccess: 'All tiers. Tier determines subset of bundle data returned.',
})

// --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
const HolisticBundleInputSchema = z.object({
  // Accepts `query_text` (new) or `bundles[]` array (old callers, joined as comma list).
  // Handler normalizes to `query_text`.
  query_text: z.string().optional().describe(
    'The query driving the holistic read. Used to seed CGM graph walk and UCN/RM/CDLM vector searches.'
  ),
  bundles: z.array(z.string()).optional().describe('Backward-compat alias: array of bundle names joined as query_text.'),
  focus_domains: z.array(z.string()).optional().describe(
    'Optional domain filter for the MSR signal query. Examples: ["career", "health"]. If omitted, top 100 signals by significance.'
  ),
  time_window: z.object({
    start: z.string().optional(),
    end: z.string().optional(),
  }).optional().describe(
    'Optional ISO date range for LEL event filtering. e.g. { start: "2020-01-01", end: "2026-12-31" }.'
  ),
  subset: z.array(z.string()).optional().describe(
    'Optional list of sub-tool names to restrict the bundle. Valid values: MSR, CGM, UCN, RM, CDLM, LEL, PANCHANG, DASHA. Case-insensitive.'
  ),
  subset_size: z.number().int().min(10).max(573).optional().default(100).describe(
    'Number of MSR signals to fetch. Default 100. Range 10–573.'
  ),
  return_format: z.enum(['verbose', 'compressed']).optional().default('verbose').describe(
    'verbose: full data in bundle_entries (default). compressed: strip data payloads, return only metadata fields.'
  ),
})

// --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
// Compat schema with transform+refine for tests — normalises bundles[] → query_text (min 3 chars).
export const HolisticBundleCompatSchema = HolisticBundleInputSchema.transform(i => ({
  ...i,
  query_text: i.query_text ?? (i.bundles && i.bundles.length > 0 ? i.bundles.join(', ') : ''),
})).refine(i => i.query_text.length >= 3, {
  message: 'query_text (or non-empty bundles array) required, min 3 chars',
})

type HolisticBundleInput = z.infer<typeof HolisticBundleInputSchema>

export function registerHolisticBundle(
  server: McpServer,
  getPrincipal: () => Principal,
  descriptionOverride?: string
): void {
  server.tool(
    'holistic_bundle',

    descriptionOverride ?? HOLISTIC_BUNDLE_DESCRIPTION,

    HolisticBundleInputSchema.shape,

    async (input: HolisticBundleInput) => {
      const principal = getPrincipal()
      // --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
      const query_text = input.query_text ?? (input.bundles?.length ? input.bundles.join(', ') : '')

      const envelope = await executeHolisticBundle(
        {
          query_text,
          focus_domains: input.focus_domains,
          time_window: input.time_window,
          subset: input.subset,
          subset_size: input.subset_size,
          return_format: input.return_format,
          tier: principal.audience_tier,
          chart_id: undefined,
        },
        principal
      )

      return okResult(envelope)
    }
  )
}
