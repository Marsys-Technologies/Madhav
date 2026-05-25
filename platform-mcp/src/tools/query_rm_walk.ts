/**
 * query_rm_walk.ts — MCP Tier 3 surgical primitive: Resonance Map walk.
 *
 * What it does: Scans RM_v2_0.md (Resonance Map, 35 element blocks RM.01–RM.35)
 * and returns structured resonance entries. When seed_signal_id is provided,
 * returns only entries whose msr_anchors list contains that signal ID. Full-dump
 * mode (no params) returns all 35 RM element blocks.
 *
 * When to prefer: Use query_rm_walk when a query asks about resonance patterns,
 * net resonance classifications (STRONGLY AMPLIFIED, AMPLIFIED, TENSION-BEARING),
 * or which RM elements are associated with a specific MSR signal (e.g. "MSR.045").
 * Prefer holistic_bundle when full cross-domain synthesis is also required.
 * Prefer query_signals when raw MSR signal rows with confidence/valence filters
 * are needed rather than RM resonance context.
 *
 * Input shape hints:
 *   seed_signal_id — optional; e.g. "MSR.045" or "RM.01". When omitted, full-dump
 *                    mode returns all 35 RM element blocks.
 *
 * Output shape preview: {ok, result: {results: RmEntry[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_rm_walk({seed_signal_id: "MSR.413"}) →
 *   {ok: true, result: {results: [{rm_id: "RM.01", signal_id: "RM.01", resonance_type: "Mercury 10H ...",
 *    strength: "STRONGLY_AMPLIFIED", domains: [...], msr_anchors: ["MSR.413"], net_resonance: "..."}]}, ...}
 *
 * Data source: 025_HOLISTIC_SYNTHESIS/RM_v2_0.md (canonical_id: RM)
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const QUERY_RM_WALK_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Scans RM_v2_0.md (Resonance Map, 35 element blocks RM.01–RM.35) and returns ' +
    'structured resonance entries — rm_id, resonance_type, strength, domains, msr_anchors, net_resonance. ' +
    'Filters by seed_signal_id (MSR.NNN anchor match) or returns all entries in full-dump mode. ' +
    'Surgical primitive — bypasses planner and synthesis stages.',
  coverageHint: 'RM_v2_0.md — 35 resonance element blocks across the holistic synthesis layer',
  whenToPrefer:
    'Use query_rm_walk when a query asks about resonance patterns, net resonance classifications ' +
    '(STRONGLY_AMPLIFIED, AMPLIFIED, TENSION_BEARING), or which RM elements are anchored to a specific MSR signal. ' +
    'Prefer holistic_bundle when full cross-domain synthesis is also required. ' +
    'Prefer query_signals when raw MSR signal rows with confidence/valence filters are needed.',
})

const QueryRmWalkInputSchema = z.object({
  seed_signal_id: z.string().optional().describe(
    'MSR signal ID or RM element ID to seed the walk (e.g. "MSR.045" or "RM.01"). ' +
    'When omitted, returns all 35 RM element blocks (full-dump mode).'
  ),
})

type QueryRmWalkInput = z.infer<typeof QueryRmWalkInputSchema>

export function registerQueryRmWalk(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_rm_walk',
    QUERY_RM_WALK_DESCRIPTION,
    QueryRmWalkInputSchema.shape,
    async (args: QueryRmWalkInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'query_rm_walk',
        {
          ...(args.seed_signal_id ? { seed_signal_id: args.seed_signal_id } : {}),
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
