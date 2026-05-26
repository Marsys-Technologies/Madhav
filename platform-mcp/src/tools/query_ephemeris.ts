/**
 * query_ephemeris.ts — MCP Tier 3 surgical primitive: planetary position lookup.
 *
 * What it does: Returns date-indexed planetary positions from the ephemeris_daily
 * table. Given a planet and date range, returns the planet's sign, degree, nakshatra,
 * retrograde status, and speed for each day in the range. Data covers all 9 Jyotish
 * grahas plus Rahu/Ketu. Source: pre-computed Swiss Ephemeris output in the
 * ephemeris_daily table. Tagged surgical: true; bypasses planner and synthesis.
 *
 * When to prefer: Use for precise positional questions ("What sign was Saturn in
 * during March 2025?", "Was Mars retrograde on date X?"). Prefer query_transit_event
 * when you want to find a specific transit occurrence rather than a positional scan.
 * Prefer holistic_bundle when you need the positional data synthesized against the chart.
 *
 * Input shape hints:
 *   planet — optional; Jyotish planet name or array of names: "Sun", "Moon", "Mars",
 *     "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu". Omit for all 9 grahas.
 *   date_range — required {from, to} ISO date pair; max span 1825 days (5 years).
 *   sample_step — optional "1d"|"7d"|"30d"; defaults "1d". Use "7d"/"30d" for wide ranges.
 *   return_changes_only — optional boolean; if true, only rows where position changed >1°.
 *
 * Output shape preview: {ok, result: {positions: EphemerisRow[]}, trace_id,
 *   epistemics: {surgical: true}}.
 *
 * Example: query_ephemeris({planet: "Saturn", date_range: {from: "2025-01-01", to: "2025-03-31"}}) →
 *   {ok: true, result: {positions: [{date: "2025-01-01", sign: "Aquarius",
 *   degree: 17.4, retrograde: false, nakshatra: "Shatabhisha"}]}, ...}
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'
import type { Principal } from '../types.js'
import { buildToolDescription } from './description_builder.js'

const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'] as const

export const QUERY_EPHEMERIS_DESCRIPTION = buildToolDescription({
  baseDescription:
    'What it does: Returns date-indexed planetary positions (sign, degree, nakshatra, retrograde status, speed) ' +
    'from the ephemeris_daily table for a given planet and date range.',
  enumSource: PLANETS,
  coverageHint: 'Swiss Ephemeris output; max ~1 year range recommended per call',
  whenToPrefer:
    'Use for "What sign was Saturn in during Q1 2025?" or retrograde status checks. ' +
    'Prefer query_transit_event for "when does X enter Y?" searches. ' +
    'Prefer holistic_bundle when positional data needs chart synthesis.',
})

const MAX_DATE_RANGE_DAYS = 1825  // 5 years

/** Maps sample_step string enum to integer number of days for the platform primitive.
 * The platform's QueryEphemerisInput.sample_step is a number, not a string.
 * "7d" > 1 evaluates to false (NaN comparison); sending 7 correctly triggers downsampling. */
const SAMPLE_STEP_DAYS: Record<string, number> = {
  '1d': 1,
  '7d': 7,
  '30d': 30,
}

// --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
const QueryEphemerisInputSchema = z.object({
  planet: z.union([z.enum(PLANETS), z.array(z.enum(PLANETS))]).optional().describe(
    'Jyotish graha(s). One of or an array of: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu. ' +
    'Omit to return all 9 grahas.'
  ),
  // Accepts nested date_range {from, to} (new) or flat date_from + date_to (old callers).
  date_range: z.object({
    from: z.string().describe('ISO start date (YYYY-MM-DD).'),
    to: z.string().describe('ISO end date (YYYY-MM-DD).'),
  }).optional().describe(
    'Date range for position lookup. Maximum span: 1825 days (5 years). ' +
    'Use sample_step to reduce row count for wide ranges.'
  ),
  // --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
  date_from: z.string().optional().describe('Backward-compat alias: ISO start date (use date_range.from instead).'),
  date_to: z.string().optional().describe('Backward-compat alias: ISO end date (use date_range.to instead).'),
  sample_step: z.enum(['1d', '7d', '30d']).optional().default('1d').describe(
    'Sampling interval. "1d" = every day (default); "7d" = weekly (Sundays); "30d" = monthly (1st of each month). ' +
    'Use "7d" or "30d" to reduce token cost for wide date ranges.'
  ),
  return_changes_only: z.boolean().optional().default(false).describe(
    'When true, only return rows where at least one planet position changed by >1 degree from the previous row. ' +
    'Useful for finding ingress / station events without full-range scan.'
  ),
  derived_fields: z.array(
    z.enum(['dignity', 'combust', 'vargottama', 'ingress', 'yuddha', 'house', 'house_bc'])
  ).optional().describe(
    'Which derived columns to include. Defaults to all 7. Pass [] to skip all derived columns for token-tight queries.'
  ),
})

// --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
// Compat schema with transform+refine for tests — normalises flat date_from/date_to → date_range.
export const QueryEphemerisCompatSchema = QueryEphemerisInputSchema.transform(i => ({
  ...i,
  date_range: i.date_range ?? (i.date_from && i.date_to
    ? { from: i.date_from, to: i.date_to }
    : undefined),
})).refine(i => i.date_range !== undefined, {
  message: 'date_range (or date_from + date_to) is required',
})

type QueryEphemerisInput = z.infer<typeof QueryEphemerisInputSchema>

/** Returns number of days between two ISO date strings. */
function daysBetween(from: string, to: string): number {
  const msPerDay = 1000 * 60 * 60 * 24
  return Math.round((new Date(to).getTime() - new Date(from).getTime()) / msPerDay)
}

export function registerQueryEphemeris(
  server: McpServer,
  getPrincipal: () => Principal
): void {
  server.tool(
    'query_ephemeris',
    QUERY_EPHEMERIS_DESCRIPTION,
    QueryEphemerisInputSchema.shape,
    async (args: QueryEphemerisInput) => {
      const principal = getPrincipal()
      // --- backward-compat alias (MCP-REM-Session-A 2026-05-26) ---
      const date_range = args.date_range ?? (args.date_from && args.date_to
        ? { from: args.date_from, to: args.date_to }
        : undefined)
      if (!date_range) {
        return errorResult({
          ok: false,
          error: 'date_range_required',
          message: 'date_range ({from, to}) or flat date_from + date_to params are required',
        })
      }

      // Enforce 1825-day cap
      const span = daysBetween(date_range.from, date_range.to)
      if (span > MAX_DATE_RANGE_DAYS) {
        const errEnvelope = {
          ok: false,
          error: 'date_range_too_wide',
          message: `Date range exceeds 5-year maximum (1825 days). Please narrow the range. Requested span: ${span} days.`,
        }
        return errorResult(errEnvelope)
      }
      if (span < 0) {
        const errEnvelope = {
          ok: false,
          error: 'date_range_invalid',
          message: `date_range.from must be before date_range.to. Got from="${date_range.from}", to="${date_range.to}".`,
        }
        return errorResult(errEnvelope)
      }

      // Normalize planet(s) to array
      const planetsArray: string[] = args.planet === undefined
        ? []
        : Array.isArray(args.planet)
          ? args.planet
          : [args.planet]

      const { status, envelope } = await callPlatformPrimitive(
        'query_ephemeris',
        {
          // Translate date_range.{from,to} → start_date/end_date for the primitive
          start_date: date_range.from,
          end_date: date_range.to,
          // Pass planets as array (primitive accepts both planet and planets)
          ...(planetsArray.length === 1 ? { planet: planetsArray[0] } : {}),
          ...(planetsArray.length > 1 ? { planets: planetsArray } : {}),
          // FIX-4: convert string enum ("7d") to integer days (7) for the platform primitive.
          // platform QueryEphemerisInput.sample_step is number; "7d" > 1 is false (NaN), so never downsamples.
          sample_step: SAMPLE_STEP_DAYS[args.sample_step ?? '1d'] ?? 1,
          return_changes_only: args.return_changes_only ?? false,
          ...(args.derived_fields !== undefined ? { derived_fields: args.derived_fields } : {}),
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
