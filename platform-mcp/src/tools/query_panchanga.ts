/**
 * query_panchanga.ts — MCP Tier 3 surgical primitive: daily panchang lookup.
 *
 * What it does: Returns the five limbs of the Vedic day (panchang) for any
 * date: tithi (lunar day), vara (weekday), nakshatra (Moon's asterism), yoga
 * (Sun+Moon sum), and karana (half-tithi). Also returns hora (planetary hour),
 * choghadiya (auspiciousness windows), muhurat windows, inauspicious periods
 * (Rahu Kalam, Gulika Kalam, Yamaghanta), and special yogas. Data is sourced
 * from the pre-computed panchanga_daily table (73,414 rows, 1900–2100).
 * Tagged surgical: true; bypasses planner and synthesis.
 *
 * When to prefer: Use for date-specific panchang questions ("What are today's
 * auspicious windows?", "What is the nakshatra on 2026-05-21?"). Prefer
 * ask_madhav when you need interpretation of the panchang in light of the chart
 * (e.g., "How does today's Rahu Kalam interact with my natal Rahu?").
 *
 * Input shape hints:
 *   date — required ISO date string (YYYY-MM-DD).
 *   observer — optional {lat, lon} in decimal degrees; defaults to the native's
 *     birth location (Bhubaneswar: lat 20.29, lon 85.82).
 *
 * Output shape preview: {ok, result: {tithi, vara, nakshatra, yoga, karana,
 *   hora: [], choghadiya: [], inauspicious: {}, auspicious: {}},
 *   trace_id, epistemics: {surgical: true}}.
 *
 * Example: query_panchanga({date: "2026-05-21"}) →
 *   {ok: true, result: {tithi: "Shukla Chaturdashi", vara: "Guruvara",
 *   nakshatra: "Vishakha", yoga: "Shiva", karana: "Bava", ...}}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import type { Principal } from '../types.js'

const QueryPanchangaInputSchema = z.object({
  date: z.string().describe('ISO date (YYYY-MM-DD) to retrieve panchang data for.'),
  observer: z.object({
    lat: z.number().optional().describe('Observer latitude in decimal degrees.'),
    lon: z.number().optional().describe('Observer longitude in decimal degrees.'),
  }).optional().describe(
    'Observer location. Defaults to native\'s birth location (Bhubaneswar, lat 20.29, lon 85.82).'
  ),
})

type QueryPanchangaInput = z.infer<typeof QueryPanchangaInputSchema>

export function registerQueryPanchanga(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_panchanga',
    'What it does: Returns the 5 limbs of the Vedic day (tithi, vara, nakshatra, yoga, karana) ' +
    'plus hora, choghadiya, muhurat windows, and inauspicious periods (Rahu Kalam etc.) for any date. ' +
    'Data is pre-computed in the panchanga_daily table (1900–2100). Tagged surgical: true. ' +
    'When to prefer: Use for date-specific panchang questions ("What is today\'s nakshatra?"). ' +
    'Prefer ask_madhav when you also need chart-level interpretation of the panchang. ' +
    'Input shape hints: date is required (YYYY-MM-DD); observer is optional lat/lon ' +
    '(defaults to native\'s birth location: Bhubaneswar lat 20.29 lon 85.82). ' +
    'Output shape preview: {ok, result: {tithi, vara, nakshatra, yoga, karana, hora[], choghadiya[], ...}}. ' +
    'Example: query_panchanga({date: "2026-05-21"}) → {tithi: "Shukla Chaturdashi", ...}',
    QueryPanchangaInputSchema.shape,
    async (args: QueryPanchangaInput) => {
      const principal = getPrincipal()
      const { status, envelope } = await callPlatformPrimitive(
        'query_panchanga',
        {
          date: args.date,
          ...(args.observer ? { observer: args.observer } : {}),
        },
        principal
      )
      const text = JSON.stringify(envelope, null, 2)
      return {
        content: [{ type: 'text' as const, text }],
        isError: !envelope.ok || status >= 400,
      }
    }
  )
}
