/**
 * lel_query.ts — MCP Tier 3 surgical primitive: Life Event Log ground-truth retrieval.
 *
 * What it does: Queries the Life Event Log (LEL) — the authoritative ground-truth
 * corpus of 36 documented life events, 5 period summaries, and 6 chronic patterns
 * with confidence scores up to 0.89. Returns raw event records with dates, categories,
 * significance scores, and associated dasha states. The LEL is the M4 ground-truth
 * spine and is foundational to calibration and backtesting. Tagged surgical: true.
 *
 * When to prefer: Use lel_query to retrieve verified, witnessed life events when
 * the question is "what documented events happened during this period?" Prefer
 * holistic_bundle when you need the events interpreted in light of current chart state.
 * Prefer query_dasha_periods to find the dasha active during an event period, then
 * use lel_query to retrieve events from that same period.
 *
 * Input shape hints:
 *   category — optional; event category filter (e.g. "career", "health",
 *     "relationship", "relocation", "education", "chronic").
 *   date_range — optional {start, end} ISO dates; filters events to the range.
 *   min_significance — optional float 0.0–1.0; filters to events at or above threshold.
 *
 * Output shape preview: {ok, result: {events: LelEvent[]}, trace_id,
 *   epistemics: {surgical: true}}.
 *
 * Example: lel_query({category: "career", min_significance: 0.7}) →
 *   {ok: true, result: {events: [{event_id: "LEL.E012", date: "2019-02-15",
 *   category: "career", description: "Resigned from Infosys...", significance: 0.85}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'

const LelQueryInputSchema = z.object({
  category: z.string().optional().describe(
    'Event category filter. Examples: "career", "health", "relationship", ' +
    '"relocation", "education", "chronic", "spiritual".'
  ),
  date_range: z.object({
    start: z.string().describe('ISO start date (YYYY-MM-DD).'),
    end: z.string().describe('ISO end date (YYYY-MM-DD).'),
  }).optional().describe('Filter events to this date range.'),
  min_significance: z.number().min(0).max(1).optional().describe(
    'Minimum significance threshold (0.0–1.0). Filters to events at or above this level.'
  ),
})

type LelQueryInput = z.infer<typeof LelQueryInputSchema>

export function registerLelQuery(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'lel_query',
    'What it does: Queries the Life Event Log (LEL) — 36 verified life events, ' +
    '5 period summaries, 6 chronic patterns — with optional category, date range, ' +
    'and significance filters. Returns raw event records as ground-truth data. ' +
    'When to prefer: Use to retrieve verified life events for calibration ("what career ' +
    'events happened 2015–2020?"). Prefer holistic_bundle when interpretation is also needed. ' +
    'Input shape hints: all params optional; category filters by event type; ' +
    'date_range {start, end} filters by occurrence date; min_significance is a 0–1 float. ' +
    'Output shape preview: {ok, result: {events: LelEvent[]}, trace_id, epistemics: {surgical: true}}. ' +
    'Example: lel_query({category: "career", min_significance: 0.7}) → documented career events.',
    LelQueryInputSchema.shape,
    async (args: LelQueryInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'lel_query',
        {
          ...(args.category ? { category: args.category } : {}),
          ...(args.date_range ? { date_range: args.date_range } : {}),
          ...(args.min_significance !== undefined ? { min_significance: args.min_significance } : {}),
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
