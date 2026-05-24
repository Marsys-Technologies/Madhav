/**
 * query_transit_event.ts — MCP Tier 3 surgical primitive: transit event search.
 *
 * What it does: Searches the ephemeris_daily table for specific transit events
 * — sign ingresses, exact conjunctions, oppositions, or degree crossings —
 * within a date range. Answers "When does Saturn enter Aquarius?" or "When
 * does Jupiter transit the 10th house?" Returns event records with the exact
 * date, the planet's state before and after, and any associated astrological
 * significance tags. Tagged surgical: true; bypasses planner and synthesis.
 *
 * When to prefer: Use when you need the specific date(s) a transit occurs
 * rather than a day-by-day position scan. Prefer query_ephemeris for daily
 * positional data over a range. Prefer holistic_bundle when you also need synthesis
 * of what the transit means for the native's chart and life domains.
 *
 * Input shape hints:
 *   planet — required; the transiting planet (e.g. "Saturn", "Jupiter").
 *   target — required; the transit target — a sign name (e.g. "Aquarius"),
 *     a house number ("house_10"), or a degree reference ("15 Scorpio").
 *   date_range — required {start, end} ISO date pair; narrows the search window.
 *
 * Output shape preview: {ok, result: {events: TransitEvent[]}, trace_id,
 *   epistemics: {surgical: true}}.
 *
 * Example: query_transit_event({planet: "Saturn", target: "Aquarius",
 *   date_range: {start: "2020-01-01", end: "2025-12-31"}}) →
 *   {ok: true, result: {events: [{date: "2022-04-29", event_type: "sign_ingress",
 *   planet: "Saturn", from_sign: "Capricorn", to_sign: "Aquarius"}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

export const QUERY_TRANSIT_EVENT_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Searches ephemeris_daily for specific transit events (sign ingresses, conjunctions, degree crossings) ' +
    'within a date range and returns exact event dates with before/after planet state.',
  whenToPrefer:
    'Use for "When does Saturn enter Aquarius?" style questions — event-date lookup rather than daily scan. ' +
    'Prefer query_ephemeris for day-by-day position data over a range. ' +
    'Prefer holistic_bundle when the transit\'s meaning for the native\'s chart is also needed.',
})

const QueryTransitEventInputSchema = z.object({
  planet: z.string().describe(
    'The transiting planet (e.g. "Saturn", "Jupiter", "Rahu").'
  ),
  target: z.string().describe(
    'The transit target — a sign name (e.g. "Aquarius"), house number ("house_10"), ' +
    'or degree reference (e.g. "15 Scorpio").'
  ),
  date_range: z.object({
    start: z.string().describe('ISO start date (YYYY-MM-DD).'),
    end: z.string().describe('ISO end date (YYYY-MM-DD).'),
  }).describe('Search window for the transit event.'),
})

type QueryTransitEventInput = z.infer<typeof QueryTransitEventInputSchema>

export function registerQueryTransitEvent(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_transit_event',
    QUERY_TRANSIT_EVENT_DESCRIPTION,
    QueryTransitEventInputSchema.shape,
    async (args: QueryTransitEventInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'query_transit_event',
        {
          planet: args.planet,
          target: args.target,
          date_range: args.date_range,
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
