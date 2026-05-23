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
    'Prefer individual surgical primitives when you need only one data type without synthesis overhead.',
})

const HolisticBundleInputSchema = z.object({
  query_text: z.string().min(3).describe(
    'The query driving the holistic read. Used to seed CGM graph walk and UCN/RM/CDLM vector searches.'
  ),
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
})

type HolisticBundleInput = z.infer<typeof HolisticBundleInputSchema>

export function registerHolisticBundle(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'holistic_bundle',

    HOLISTIC_BUNDLE_DESCRIPTION,

    HolisticBundleInputSchema.shape,

    async (input: HolisticBundleInput) => {
      const principal = getPrincipal()

      const envelope = await executeHolisticBundle(
        {
          query_text: input.query_text,
          focus_domains: input.focus_domains,
          time_window: input.time_window,
          subset: input.subset,
          tier: principal.audience_tier,
          chart_id: undefined,
        },
        principal
      )

      return okResult(envelope)
    }
  )
}
