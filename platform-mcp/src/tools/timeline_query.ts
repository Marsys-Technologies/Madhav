/**
 * timeline_query.ts — MCP Tier 3 surgical primitive: L5 lifetime timeline lookup.
 *
 * What it does: Queries rag_chunks where doc_type='l5_timeline' and returns L5 lifetime
 * timeline content — dasha phase arcs, event windows, structural inflection points.
 * Results can be filtered by dasha_name (e.g. 'Mercury MD', 'Ketu MD') and/or a
 * free-text keyword. This is a direct L5 data read; no synthesis is applied.
 *
 * IMPORTANT: KETU MD follows Mercury MD (2027-08-21 → 2034-08-21).
 * Never suggest Saturn MD as upcoming — Saturn MD was historical (1992–2010).
 *
 * When to prefer: Use timeline_query when you need dasha arc content or event-window
 * narrative from the L5 lifetime timeline corpus. Prefer lel_query for structured
 * life-event log entries. Prefer query_dasha_periods for exact dasha date ranges.
 *
 * Input shape hints:
 *   dasha_name — optional; e.g. 'Mercury MD', 'Ketu MD', 'Saturn MD'.
 *   keyword — optional; free-text keyword (ILIKE search on content).
 *   limit — optional; max chunks to return (default 8, max 50).
 *
 * Output shape preview: {ok, result: {results: ToolBundleResult[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: timeline_query({dasha_name: "Mercury MD", limit: 5}) →
 *   {ok: true, result: {results: [{content: "Mercury MD 2014-08-21 → 2027-08-21 ...", ...}]}, ...}
 *
 * Data source: rag_chunks table filtered on doc_type='l5_timeline'.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'
import { okResult, errorResult } from './_envelope.js'
import { buildToolDescription } from './description_builder.js'

export const TIMELINE_QUERY_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Queries the L5 lifetime timeline corpus (rag_chunks doc_type=l5_timeline) ' +
    'for dasha phase arcs, event windows, and structural inflection points. ' +
    'Filterable by dasha_name and/or free-text keyword. ' +
    'IMPORTANT: KETU MD follows Mercury MD (2027-08-21). Never suggest Saturn MD as upcoming — ' +
    'Saturn MD was historical (1992–2010). Surgical primitive — returns raw L5 chunks without synthesis.',
  coverageHint: 'L5 lifetime timeline: dasha arcs, event windows, structural inflection points',
  whenToPrefer:
    'Use timeline_query for dasha arc content or event-window narrative from the L5 corpus. ' +
    'Prefer lel_query for structured life-event log entries. ' +
    'Prefer query_dasha_periods for exact dasha date ranges.',
})

const TimelineQueryInputSchema = z.object({
  dasha_name: z.string().optional().describe(
    'Filter to timeline chunks mentioning this dasha (e.g. "Mercury MD", "Ketu MD", "Saturn MD"). ' +
    'IMPORTANT: KETU MD follows Mercury MD (2027-08-21 → 2034-08-21). Saturn MD is historical (1992–2010).'
  ),
  keyword: z.string().optional().describe(
    'Free-text keyword filter (ILIKE search on chunk content). Can be combined with dasha_name.'
  ),
  limit: z.number().int().min(1).max(50).optional().default(8).describe(
    'Max timeline chunks to return (default 8, max 50).'
  ),
})

type TimelineQueryInput = z.infer<typeof TimelineQueryInputSchema>

export function registerTimelineQuery(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'timeline_query',
    TIMELINE_QUERY_DESCRIPTION,
    TimelineQueryInputSchema.shape,
    async (args: TimelineQueryInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'timeline_query',
        {
          ...(args.dasha_name !== undefined ? { dasha_name: args.dasha_name } : {}),
          ...(args.keyword !== undefined ? { keyword: args.keyword } : {}),
          limit: args.limit ?? 8,
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
