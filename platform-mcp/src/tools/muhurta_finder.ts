/**
 * muhurta_finder.ts — MCP Tier 3 surgical primitive: electional timing (Muhurta).
 *
 * What it does: Finds auspicious Muhurta windows for a given event type within a
 * specified date range. Evaluates Panchanga factors (Tithi, Vara, Nakshatra, Yoga,
 * Karana), planetary positions, and special Muhurta rules (Abhijit, Brahma, etc.)
 * against classical Muhurta criteria for each event category. Returns ranked windows
 * with composite auspiciousness scores and the factors driving each score.
 *
 * Source: platform/src/lib/retrieve/query_muhurat.ts
 * Data: muhurta_windows table + panchanga_daily table
 * Engine: platform/scripts/temporal/compute_muhurta.py
 *
 * Supported event types (common):
 *   marriage, travel, surgery, business_start, house_entry, vehicle_purchase,
 *   education_start, meditation, thread_ceremony, naming_ceremony
 *   (pass any string — the engine matches against its event taxonomy).
 *
 * When to prefer: Use for "When is a good time to start a business?",
 * "Find an auspicious date for travel in June 2026", or any electional
 * timing question. Prefer holistic_bundle when you need Muhurta analysis
 * synthesized against the native's specific dasha and transit context.
 *
 * Output shape preview: {ok, result: {windows: {start_utc, end_utc, score,
 *   tithi, vara, nakshatra, factors}[]}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: muhurta_finder({event: "travel", date_from: "2026-06-01", date_to: "2026-06-30"}) →
 *   {ok: true, result: {windows: [{start_utc: "2026-06-04T04:30:00Z",
 *   end_utc: "2026-06-04T06:15:00Z", score: 0.87, tithi: "Shukla Panchami",
 *   vara: "Guruvara", nakshatra: "Pushya", factors: [...]}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

export const MUHURTA_FINDER_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Finds auspicious Muhurta (electional timing) windows for a given event type ' +
    'within a date range. Scores windows by Panchanga factors (Tithi, Vara, Nakshatra, Yoga, Karana) ' +
    'and classical Muhurta rules. Returns ranked windows with composite scores and driving factors.',
  coverageHint:
    'muhurta_windows table + panchanga_daily; classical Muhurta taxonomy; ' +
    'event types: marriage, travel, surgery, business_start, house_entry, vehicle_purchase, ' +
    'education_start, meditation, thread_ceremony, naming_ceremony, and others.',
  whenToPrefer:
    'Use for "When is a good time to start a business?", "Find an auspicious travel date in June", ' +
    'or any electional timing query. Prefer holistic_bundle for Muhurta analysis synthesized ' +
    'against the native\'s dasha and transit context.',
})

const MuhurtaFinderInputSchema = z.object({
  event: z.string().describe(
    'Event type for which to find a Muhurta. Common values: marriage, travel, surgery, ' +
    'business_start, house_entry, vehicle_purchase, education_start, meditation, ' +
    'thread_ceremony, naming_ceremony. Pass the closest match — the engine uses fuzzy taxonomy.'
  ),
  date_from: z.string().describe(
    'ISO date (YYYY-MM-DD) — start of the search window (inclusive).'
  ),
  date_to: z.string().describe(
    'ISO date (YYYY-MM-DD) — end of the search window (inclusive). ' +
    'Max recommended range: 90 days per call.'
  ),
  lat: z.number().min(-90).max(90).optional().describe(
    'Observer latitude in decimal degrees. Defaults to native birth latitude (20.2961°N Bhubaneswar) if omitted.'
  ),
  lon: z.number().min(-180).max(180).optional().describe(
    'Observer longitude in decimal degrees. Defaults to native birth longitude (85.8245°E) if omitted.'
  ),
  tz_offset_minutes: z.number().optional().describe(
    'Timezone offset from UTC in minutes (e.g. 330 for IST UTC+5:30). ' +
    'Defaults to IST (+330) if omitted.'
  ),
  chart_id: z.string().uuid().optional().describe(
    'Chart UUID to use for nativity-aware Muhurta scoring. ' +
    'Defaults to the native\'s chart if omitted.'
  ),
  top_n: z.number().int().min(1).max(20).optional().describe(
    'Return only the top N windows by auspiciousness score. Default: 5. Max: 20.'
  ),
})

type MuhurtaFinderInput = z.infer<typeof MuhurtaFinderInputSchema>

export function registerMuhurtaFinder(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'muhurta_finder',
    MUHURTA_FINDER_DESCRIPTION,
    MuhurtaFinderInputSchema.shape,
    async (args: MuhurtaFinderInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'muhurta_finder',
        {
          event: args.event,
          date_from: args.date_from,
          date_to: args.date_to,
          lat: args.lat,
          lon: args.lon,
          tz_offset_minutes: args.tz_offset_minutes,
          chart_id: args.chart_id,
          top_n: args.top_n,
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
