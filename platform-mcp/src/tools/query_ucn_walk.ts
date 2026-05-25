/**
 * query_ucn_walk.ts — MCP Tier 3 surgical primitive: UCN walk.
 *
 * What it does: Scans UCN_v4_0.md (Unified Chart Narrative) for signal
 * references near a seed signal ID, or returns all signal-section associations
 * in full-dump mode. Returns raw UCN entries — signal_id, confluence_type
 * (section heading), domain — without synthesis. Tagged surgical: true in
 * the epistemics block.
 *
 * When to prefer: Use query_ucn_walk when a query asks for the UCN narrative
 * context around a specific MSR signal (e.g. "which UCN sections reference
 * MSR.413?") or to enumerate all signal-section associations in the UCN.
 * Prefer holistic_bundle when full cross-domain synthesis is also required.
 * Prefer query_signals when raw MSR signal rows (confidence, valence, etc.)
 * are needed rather than UCN section context.
 *
 * Input shape hints:
 *   seed_signal_id — optional; e.g. "MSR.234". When omitted, full-dump mode returns all entries.
 *   depth          — optional int 1–5, default 2 (accepted for API compat; semantics reserved
 *                    for a future graph-walk implementation over structured UCN tables).
 *
 * Output shape preview: {ok, result: {results: UcnEntry[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_ucn_walk({seed_signal_id: "MSR.413"}) →
 *   {ok: true, result: {results: [{signal_id: "MSR.413", confluence_type: "Career Section", domain: "D1_Career"}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const QUERY_UCN_WALK_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Scans UCN_v4_0.md (Unified Chart Narrative) for MSR signal references ' +
    'near a seed signal ID, or returns all signal-section associations in full-dump mode. ' +
    'Returns raw UCN entries — signal_id, confluence_type (section heading), domain — ' +
    'without synthesis. Surgical primitive — bypasses planner and synthesis stages.',
  coverageHint: 'UCN_v4_0.md — all narrative signal-section associations across the chart',
  whenToPrefer:
    'Use query_ucn_walk when a query asks which UCN sections reference a specific MSR signal ' +
    'or to enumerate all signal-section associations. ' +
    'Prefer holistic_bundle when full cross-domain synthesis is also required. ' +
    'Prefer query_signals when raw MSR signal rows with confidence/valence filters are needed.',
})

const QueryUcnWalkInputSchema = z.object({
  seed_signal_id: z.string().optional().describe(
    'MSR signal ID to seed the walk (e.g. "MSR.234"). ' +
    'When omitted, returns all signal-section associations from the UCN (full-dump mode).'
  ),
  depth: z.number().int().min(1).max(5).optional().default(2).describe(
    'Walk depth (1–5, default 2). Accepted for API compatibility; semantics reserved for ' +
    'a future graph-walk implementation over structured UCN tables. Currently unused.'
  ),
})

type QueryUcnWalkInput = z.infer<typeof QueryUcnWalkInputSchema>

export function registerQueryUcnWalk(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_ucn_walk',
    QUERY_UCN_WALK_DESCRIPTION,
    QueryUcnWalkInputSchema.shape,
    async (args: QueryUcnWalkInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'query_ucn_walk',
        {
          ...(args.seed_signal_id ? { seed_signal_id: args.seed_signal_id } : {}),
          ...(args.depth !== undefined ? { depth: args.depth } : {}),
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
