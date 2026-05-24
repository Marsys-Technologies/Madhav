/**
 * muhurta_finder.ts — MCP Tier 3 surgical primitive: auspicious muhurta window finder.
 *
 * What it does: Finds top auspicious muhurta windows for a given activity type
 * over a date range (max 30 days). Calls the Python sidecar's /api/compute/muhurat
 * endpoint via the platform primitive dispatcher. Returns scored time windows with
 * auspicious factors breakdown (tara_bala, chandra_bala, yoga, tithi, vara).
 * Native chart overlay (Tara Bala + Chandra Bala) is applied automatically when
 * chart_id is provided. Tagged surgical: true; bypasses planner and synthesis.
 *
 * When to prefer: Use for "When is the best time for a business launch / travel
 * / marriage muhurta?" style questions over a date range. Prefer query_panchanga
 * for a single day's panchang snapshot. Prefer holistic_bundle when you need
 * the muhurta's significance interpreted against the native's chart.
 *
 * Supported activity types (MVP):
 *   vivah, griha_pravesh, vyapara, yatra, property_purchase, mantra_initiation
 *
 * Input shape hints:
 *   date_from — required ISO date (YYYY-MM-DD); start of search window.
 *   date_to   — required ISO date (YYYY-MM-DD); end of search window (max 30 days).
 *   activity_type — one of the 6 MVP event types above.
 *   tier — optional audience tier hint (default 'super_admin').
 *
 * Output shape preview: {ok, result: {windows: [{start_time, end_time, score,
 *   auspicious_factors}], count, event}, trace_id, epistemics: {surgical: true}}.
 *
 * Example: muhurta_finder({date_from: "2026-06-01", date_to: "2026-06-30",
 *   activity_type: "vyapara"}) →
 *   {ok: true, result: {windows: [{start_time: "2026-06-04T06:15:00+05:30",
 *   end_time: "2026-06-04T08:30:00+05:30", score: 0.89, auspicious_factors: {...}}]}}
 *
 * TR-P4-S2: new MCP wrapper.
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

export const MUHURTA_FINDER_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Finds top auspicious muhurta windows for a given activity type over a date range ' +
    '(max 30 days). Returns scored time windows with auspicious factors — tara_bala, chandra_bala, ' +
    'yoga, tithi, vara — from the Python sidecar muhurta engine (cache-first for Bhubaneswar, ' +
    'engine-direct otherwise). Native chart overlay applied automatically.',
  whenToPrefer:
    'Use for "best time for X" questions over a date range. ' +
    'Supported activity types: vivah, griha_pravesh, vyapara, yatra, property_purchase, mantra_initiation. ' +
    'Prefer query_panchanga for a single day snapshot. ' +
    'Prefer holistic_bundle when muhurta interpretation against the native chart is needed.',
})

// Supported MVP event types (mirror of Python sidecar EVENTS_MVP).
const ACTIVITY_TYPES = [
  'vivah',
  'griha_pravesh',
  'vyapara',
  'yatra',
  'property_purchase',
  'mantra_initiation',
] as const

const MuhurtaFinderInputSchema = z.object({
  date_from: z.string().describe(
    'ISO start date (YYYY-MM-DD) for the search window (inclusive).'
  ),
  date_to: z.string().describe(
    'ISO end date (YYYY-MM-DD) for the search window (inclusive). Max 30 days from date_from.'
  ),
  activity_type: z.enum(ACTIVITY_TYPES).describe(
    'The type of activity to find muhurta for. ' +
    'Valid values: vivah (marriage), griha_pravesh (house-entry), vyapara (business), ' +
    'yatra (travel/journey), property_purchase (property), mantra_initiation (initiation).'
  ),
  chart_id: z.string().optional().describe(
    "Native chart UUID for Tara Bala + Chandra Bala overlay. " +
    "Defaults to the native chart (362f9f17-95a5-490b-a5a7-027d3e0efda0) when not provided."
  ),
  top_n: z.number().int().min(1).max(30).optional().default(10).describe(
    'Number of top windows to return (default 10, max 30).'
  ),
  tier: z.string().optional().default('super_admin'),
})

type MuhurtaFinderInput = z.infer<typeof MuhurtaFinderInputSchema>

const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

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

      // Validate date ordering client-side for a fast, clear error.
      if (args.date_from > args.date_to) {
        return errorResult({
          ok: false,
          error: {
            class: 'validation',
            message: 'date_to must be >= date_from',
            remediation: 'Provide date_to on or after date_from',
          },
        })
      }

      // Enforce 30-day max window at the MCP layer (sidecar allows 90; we restrict
      // to 30 to keep response latency bounded for the conversational use case).
      const fromDate = new Date(args.date_from)
      const toDate = new Date(args.date_to)
      const diffDays = Math.floor((toDate.getTime() - fromDate.getTime()) / (1000 * 60 * 60 * 24))
      if (diffDays > 30) {
        return errorResult({
          ok: false,
          error: {
            class: 'validation',
            message: `Date range ${diffDays} days exceeds the 30-day maximum. Split into smaller windows.`,
            remediation: 'Reduce date_to so the range is ≤ 30 days.',
          },
        })
      }

      const { status, envelope } = await callPlatformPrimitive(
        'query_muhurat',
        {
          date_from:     args.date_from,
          date_to:       args.date_to,
          event:         args.activity_type,
          chart_id:      args.chart_id ?? NATIVE_CHART_ID,
          top_n:         args.top_n ?? 10,
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
