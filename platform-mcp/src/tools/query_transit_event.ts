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
  event_type: z.enum([
    'ingress',
    'station',
    'aspect',
    'conjunction',
  ]).describe(
    'Type of transit event to search for. ' +
    'ingress — planet enters a sign (reads ephemeris_daily.sign_ingress_today). ' +
    'station — planet stations retrograde or direct (reads retrogrades table). ' +
    'aspect — transit-to-natal aspect by degree+orb (live sidecar compute; requires transit_planet + natal_planet or natal_longitude_deg). ' +
    'conjunction — two transit planets within orb (live sidecar compute; requires planet_a + planet_b). ' +
    'Valid values: ingress | station | aspect | conjunction'
  ),
  planet: z.string().optional().describe(
    'The transiting planet for ingress/station queries (e.g. "Saturn", "Jupiter", "Rahu"). ' +
    'For aspect queries use transit_planet instead.'
  ),
  target: z.string().optional().describe(
    'The transit target — a sign name (e.g. "Aquarius"), house number ("house_10"), ' +
    'or degree reference (e.g. "15 Scorpio"). Used for ingress queries via target_sign mapping.'
  ),
  target_sign: z.string().optional().describe(
    'Sign name filter for ingress queries (e.g. "Aquarius"). Alias for target when event_type=ingress.'
  ),
  station_type: z.enum(['retrograde_start', 'retrograde_end', 'both']).optional().describe(
    'For event_type=station: which station type to filter. Defaults to "both".'
  ),
  transit_planet: z.string().optional().describe(
    'For event_type=aspect: the transiting planet (e.g. "Saturn").'
  ),
  natal_planet: z.string().optional().describe(
    'For event_type=aspect: look up natal longitude from chart_facts for this planet.'
  ),
  natal_longitude_deg: z.number().optional().describe(
    'For event_type=aspect: use this natal longitude directly if already resolved.'
  ),
  aspect_degrees: z.array(z.number()).optional().describe(
    'For event_type=aspect: aspect degrees to search. Default [0, 60, 90, 120, 180].'
  ),
  orb_deg: z.number().min(0).max(3).optional().describe(
    'For event_type=aspect|conjunction: orb in degrees. Default 1.0, max 3.0.'
  ),
  planet_a: z.string().optional().describe(
    'For event_type=conjunction: first transiting planet.'
  ),
  planet_b: z.string().optional().describe(
    'For event_type=conjunction: second transiting planet.'
  ),
  date_range: z.object({
    start: z.string().describe('ISO start date (YYYY-MM-DD). Stored as start_date.'),
    end: z.string().describe('ISO end date (YYYY-MM-DD). Stored as end_date.'),
  }).optional().describe('Search window for the transit event. Defaults to today + 1 year (2 years for aspect/conjunction).'),
  limit: z.number().int().min(1).max(200).optional().describe(
    'Max events to return. Default 50, max 200.'
  ),
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

      // Runtime guard: event_type must be present (Zod required enum, but belt-and-suspenders).
      if (!args.event_type) {
        return errorResult({
          ok: false,
          error: {
            class: 'validation',
            message: 'event_type is required. Valid values: ingress|station|aspect|conjunction',
            remediation: 'Pass event_type as one of: ingress, station, aspect, conjunction',
          },
        })
      }

      // Map MCP schema fields to the platform engine's QueryTransitEventInput shape.
      // The engine uses start_date/end_date (not date_range), and target_sign for ingress.
      const engineParams: Record<string, unknown> = {
        event_type: args.event_type,
        ...(args.date_range?.start ? { start_date: args.date_range.start } : {}),
        ...(args.date_range?.end ? { end_date: args.date_range.end } : {}),
        // ingress params — support both `target`/`target_sign` as aliases for target_sign
        ...(args.planet ? { planet: args.planet } : {}),
        ...(args.target_sign ? { target_sign: args.target_sign } : args.target ? { target_sign: args.target } : {}),
        // station params
        ...(args.station_type ? { station_type: args.station_type } : {}),
        // aspect params
        ...(args.transit_planet ? { transit_planet: args.transit_planet } : {}),
        ...(args.natal_planet ? { natal_planet: args.natal_planet } : {}),
        ...(args.natal_longitude_deg !== undefined ? { natal_longitude_deg: args.natal_longitude_deg } : {}),
        ...(args.aspect_degrees ? { aspect_degrees: args.aspect_degrees } : {}),
        ...(args.orb_deg !== undefined ? { orb_deg: args.orb_deg } : {}),
        // conjunction params
        ...(args.planet_a ? { planet_a: args.planet_a } : {}),
        ...(args.planet_b ? { planet_b: args.planet_b } : {}),
        // common
        ...(args.limit !== undefined ? { limit: args.limit } : {}),
      }

      const { status, envelope } = await callPlatformPrimitive(
        'query_transit_event',
        engineParams,
        principal
      )
      if (!envelope.ok || status >= 400) {
        return errorResult(envelope)
      }
      return okResult(envelope)
    }
  )
}
