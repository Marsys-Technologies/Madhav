/**
 * query_ephemeris.ts — brahmagyan.ephemeris MCP tool.
 *
 * Returns date-indexed planetary positions from ephemeris_daily.
 * Source: pyswisseph DE441 Lahiri sidereal; 9 Jyotish grahas; 1900-2100 daily.
 *
 * Surgical primitive — bypasses B.11 planner floor. Routes to the platform
 * via callPlatformPrimitive('query_ephemeris', ...).
 *
 * [BRAHMA-BG-0-1]
 */

import { z } from 'zod'
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../types.js'
import { callPlatformPrimitive } from '../client.js'
import { okResult, errorResult } from './_envelope.js'

// ── Description ───────────────────────────────────────────────────────────────

export const QUERY_EPHEMERIS_DESCRIPTION =
  'Returns date-indexed planetary positions (sign, degree, nakshatra, retrograde, speed) ' +
  'from ephemeris_daily for a given planet and date range. ' +
  'Source: pyswisseph DE441 Lahiri sidereal; 9 Jyotish grahas; 1900-2100 daily. ' +
  'Use for positional scans ("What sign was Saturn in March 2025?", retrograde checks). ' +
  'Prefer query_transit_event for ingress/station searches. ' +
  'Prefer holistic_bundle when position needs chart synthesis. ' +
  'Surgical: bypasses planner (B.11 floor not applied).'

// ── Schema ────────────────────────────────────────────────────────────────────

const PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'] as const

const MAX_DATE_RANGE_DAYS = 1825

const SAMPLE_STEP_DAYS: Record<string, number> = { '1d': 1, '7d': 7, '30d': 30 }

const QueryEphemerisInputSchema = z.object({
  planet: z.union([z.enum(PLANETS), z.array(z.enum(PLANETS))]).optional()
    .describe('Jyotish graha(s). Omit to return all 9 grahas.'),
  date_range: z.object({
    from: z.string().describe('ISO start date (YYYY-MM-DD).'),
    to: z.string().describe('ISO end date (YYYY-MM-DD).'),
  }).describe('Date range. Max span: 1825 days (5 years).'),
  sample_step: z.enum(['1d', '7d', '30d']).optional().default('1d')
    .describe('"1d" = daily (default); "7d" = weekly; "30d" = monthly.'),
  return_changes_only: z.boolean().optional().default(false)
    .describe('When true, only rows where position changed >1°.'),
  derived_fields: z.array(
    z.enum(['dignity', 'combust', 'vargottama', 'ingress', 'yuddha', 'house', 'house_bc'])
  ).optional()
    .describe('Derived columns to include. Defaults all 7. Pass [] to skip.'),
})

// ── Handler helpers ───────────────────────────────────────────────────────────

function daysBetween(from: string, to: string): number {
  const msPerDay = 1000 * 60 * 60 * 24
  return Math.round((new Date(to).getTime() - new Date(from).getTime()) / msPerDay)
}

// ── Tool registration ─────────────────────────────────────────────────────────

export function registerQueryEphemeris(
  server: McpServer,
  getPrincipal: () => Principal,
): void {
  server.tool(
    'query_ephemeris',
    QUERY_EPHEMERIS_DESCRIPTION,
    QueryEphemerisInputSchema.shape,
    async (args) => {
      const principal = getPrincipal()
      const span = daysBetween(args.date_range.from, args.date_range.to)
      if (span > MAX_DATE_RANGE_DAYS) {
        return errorResult({
          ok: false,
          error: 'date_range_too_wide',
          message: `Date range exceeds 1825-day maximum. Span: ${span} days.`,
        })
      }
      if (span < 0) {
        return errorResult({
          ok: false,
          error: 'date_range_invalid',
          message: `date_range.from must be before date_range.to.`,
        })
      }
      const planetsArray =
        args.planet === undefined ? []
        : Array.isArray(args.planet) ? args.planet
        : [args.planet]
      const { status, envelope } = await callPlatformPrimitive(
        'query_ephemeris',
        {
          start_date: args.date_range.from,
          end_date: args.date_range.to,
          ...(planetsArray.length === 1 ? { planet: planetsArray[0] } : {}),
          ...(planetsArray.length > 1 ? { planets: planetsArray } : {}),
          sample_step: SAMPLE_STEP_DAYS[args.sample_step ?? '1d'] ?? 1,
          return_changes_only: args.return_changes_only ?? false,
          ...(args.derived_fields !== undefined ? { derived_fields: args.derived_fields } : {}),
        },
        principal,
      )
      if (!envelope.ok || status >= 400) return errorResult(envelope)
      // Gate-3 check #3: inject provenance_envelope into every successful response.
      // source + file map to the DE441 JPL ephemeris used by pyswisseph.
      // computed_at is wall-clock time of this MCP call (not the DB write time).
      const provenance: Record<string, unknown> = {
        source: 'SwissEph DE441',
        file: 'sepl_18.se1',   // DE441 JPL kernel file name in pyswisseph
        computed_at: new Date().toISOString(),
      }
      const resultWithProvenance = {
        ...(typeof envelope === 'object' && envelope !== null ? envelope : {}),
        provenance_envelope: provenance,
      }
      return okResult(resultWithProvenance)
    },
  )
}
