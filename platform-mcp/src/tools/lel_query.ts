/**
 * lel_query.ts — MCP Tier 3 surgical primitive: Life Event Log ground-truth retrieval.
 *
 * What it does: Queries the Life Event Log (LEL) — the authoritative ground-truth
 * corpus of 36 documented life events, 5 period summaries, and 6 chronic patterns
 * with confidence scores up to 0.89. Returns raw event records with dates, categories,
 * significance scores, chart_state (Swiss Ephemeris planetary positions at event time),
 * and associated dasha states. The LEL is the M4 ground-truth spine and is foundational
 * to calibration and backtesting. Tagged surgical: true.
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
 *   significance_tier — optional enum "major" | "moderate" | "minor"; preferred over
 *     min_significance. major=≥0.8, moderate=≥0.5, minor=≥0.2.
 *   min_significance — optional float 0.0–1.0; filters to events at or above threshold.
 *     Ignored when significance_tier is also set.
 *
 * Output shape preview: {ok, result: {events: LelEvent[]}, trace_id,
 *   epistemics: {surgical: true}}.
 *   Each event includes chart_state (Swiss Ephemeris snapshot at event time).
 *
 * Example: lel_query({category: "career", significance_tier: "major"}) →
 *   {ok: true, result: {events: [{event_id: "LEL.E012", date: "2019-02-15",
 *   category: "career", description: "Resigned from Infosys...", significance: 0.85,
 *   chart_state: {...}}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

export const LEL_QUERY_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Queries the Life Event Log (LEL) — 36 verified life events, ' +
    '5 period summaries, 6 chronic patterns — with optional category, date range, and significance filters. ' +
    'Returns raw event records (including Swiss Ephemeris chart_state at event time) as ground-truth ' +
    'data for calibration and backtesting.',
  coverageHint: 'M4 ground-truth spine; confidence up to 0.89; chart_state per event',
  whenToPrefer:
    'Use to retrieve verified life events ("what career events happened 2015–2020?"). ' +
    'Prefer holistic_bundle when interpretation in light of current chart state is also needed. ' +
    'Pair with query_dasha_periods to correlate events with active dasha lords.',
})

const LelQueryInputSchema = z.object({
  category: z.string().optional().describe(
    'Event category filter. Examples: "career", "health", "relationship", ' +
    '"relocation", "education", "chronic", "spiritual".'
  ),
  date_range: z.object({
    start: z.string().describe('ISO start date (YYYY-MM-DD).'),
    end: z.string().describe('ISO end date (YYYY-MM-DD).'),
  }).optional().describe('Filter events to this date range.'),
  significance_tier: z.enum(['major', 'moderate', 'minor']).optional().describe(
    'Filter by significance tier. major=≥0.8, moderate=≥0.5, minor=≥0.2. ' +
    'Alternative to min_significance float. If both are set, significance_tier takes precedence.'
  ),
  min_significance: z.number().min(0).max(1).optional().describe(
    'Minimum significance threshold (0.0–1.0). Filters to events at or above this level. ' +
    'Prefer significance_tier for human-readable filtering. Ignored when significance_tier is set.'
  ),
})

type LelQueryInput = z.infer<typeof LelQueryInputSchema>

const SIGNIFICANCE_TIER_MAP: Record<'major' | 'moderate' | 'minor', number> = {
  major: 0.8,
  moderate: 0.5,
  minor: 0.2,
}

export function registerLelQuery(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'lel_query',
    LEL_QUERY_DESCRIPTION,
    LelQueryInputSchema.shape,
    async (args: LelQueryInput) => {
      const principal = getPrincipal()

      // significance_tier takes precedence over min_significance (maps enum → float)
      let resolvedMinSignificance = args.min_significance
      if (args.significance_tier) {
        resolvedMinSignificance = SIGNIFICANCE_TIER_MAP[args.significance_tier]
      }

      const { status, envelope } = await callPlatformPrimitive(
        'lel_query',
        {
          ...(args.category ? { category: args.category } : {}),
          ...(args.date_range ? { date_range: args.date_range } : {}),
          ...(resolvedMinSignificance !== undefined ? { min_significance: resolvedMinSignificance } : {}),
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
