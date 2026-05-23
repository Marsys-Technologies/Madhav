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

    `What it does: Performs a parallel 8-tool holistic read of the MARSYS-JIS corpus,
fanning out across MSR signals, CGM subgraph, UCN/RM/CDLM vector layers, LEL events,
current panchang, and active dasha state. All sub-tools run concurrently with 8-second
per-tool timeouts and error isolation — a failed sub-tool produces an errored slot in
bundle_entries[], not a bundle failure. Results are cached for 5 minutes
(content-addressable by query + params + tier + chart_id).

When to prefer: Use holistic_bundle as the entry point for any synthesis question
that requires cross-layer context before the LLM reasons. Equivalent to calling 8
primitives manually but with automatic error isolation and SSE streaming support
via /api/mcp/bundles/holistic_bundle. Use the subset param to restrict to specific
layers (e.g., subset: ["MSR", "DASHA"] for a dasha-only read).

Input shape: query_text (required), focus_domains (MSR filter), time_window (LEL
filter), subset (restrict which sub-tools fire). Subset values: MSR | CGM | UCN |
RM | CDLM | LEL | PANCHANG | DASHA.

Output shape: { ok: true, bundle_name: "holistic_bundle", served_from_cache: bool,
bundle_entries: [{sub_tool, errored, data, signal_ids_available, latency_ms}...],
provenance: {signal_ids_available: string[], sub_tools_fired: string[],
sub_tools_errored: string[]} }.

Example: holistic_bundle({ query_text: "Saturn dasha career inflection",
focus_domains: ["career"] }) → returns 8 sub-tool results with provenance
aggregating all signal_ids from successful tools.`,

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
