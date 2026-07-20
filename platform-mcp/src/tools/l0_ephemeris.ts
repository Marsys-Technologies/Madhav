/**
 * tools/l0_ephemeris.ts — L0 Ephemeris capabilities for MCP
 *
 * Registers 6 ephemeris capabilities (Stream B — L0FR):
 *   1. query_planet_position   — marsys://tool/L0/query_planet_position
 *   2. query_planet_transit    — marsys://tool/L0/query_planet_transit
 *   3. query_aspects_at_time   — marsys://tool/L0/query_aspects_at_time
 *   4. query_retrograde_periods — marsys://tool/L0/query_retrograde_periods
 *   5. ephemeris_cache_year     — marsys://resource/ephemeris-cache/year/{yyyy}
 *   6. ephemeris_cache_native_lifetime — marsys://resource/ephemeris-cache/native-lifetime
 *
 * Data source: ephemeris_daily table (1900-2150, 9 bodies, pyswisseph DE441).
 * Reference chart: 1984-02-05 10:43 IST, Bhubaneswar (canonical build anchor).
 * Expected Sun on reference birth: tropical ~315.87° (sidereal ~292.0° = Capricorn ~22°).
 *
 * MCP pattern: calls Python sidecar via PLATFORM_URL (REST API).
 *
 * L0FR Stream B — authored 2026-06-07
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'
import { budgetMcpContent } from '../lib/response_budget.js'

// Ephemeris tools call the Python sidecar directly (brahmagyan/ephemeris_routes.py).
// The sidecar exposes GET /brahmagyan/ephemeris/* endpoints.
// PYTHON_SIDECAR_URL env var: http://localhost:8001 (dev) or Cloud Run amjis-sidecar URL (prod).
const SIDECAR_URL = process.env['PYTHON_SIDECAR_URL'] ?? 'http://localhost:8001'
const SIDECAR_API_KEY = process.env['PYTHON_SIDECAR_API_KEY'] ?? ''

// ── Helper ────────────────────────────────────────────────────────────────────

async function sidecarGet(path: string): Promise<unknown> {
  const url = `${SIDECAR_URL}${path}`
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (SIDECAR_API_KEY) headers['x-api-key'] = SIDECAR_API_KEY
  const res = await fetch(url, { headers })
  if (!res.ok) {
    throw new Error(`[l0_ephemeris] sidecar GET ${path} → ${res.status}`)
  }
  return res.json()
}

// ── 1. query_planet_position ──────────────────────────────────────────────────

const PlanetEnum = z.enum([
  'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu',
])

const QueryPlanetPositionInput = z.object({
  date: z.string().describe(
    'Date in YYYY-MM-DD format (1900-01-01 to 2150-12-31).'
  ),
  planet: PlanetEnum.optional().describe(
    'Optional: specific planet to query. Omit for all 9 bodies.'
  ),
})

export function registerQueryPlanetPositionTool(server: McpServer): void {
  server.tool(
    'query_planet_position',
    'Query planetary positions from ephemeris_daily (1900-2150, tropical coordinates). ' +
    'Returns longitude_deg, sign_number, nakshatra_number, is_retrograde, speed_dps. ' +
    'Subtract Lahiri ayanamsha (~23.87° at J2000) to get sidereal longitude.',
    QueryPlanetPositionInput.shape,
    async (params) => {
      const input = QueryPlanetPositionInput.parse(params)
      try {
        const qs = new URLSearchParams({ date: input.date })
        if (input.planet) qs.set('planet', input.planet)
        const result = budgetMcpContent(await sidecarGet(`/brahmagyan/ephemeris/planet_position?${qs}`), 'query_planet_position')
        return {
          content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }],
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, message: msg }, null, 2) }],
          isError: true,
        }
      }
    }
  )
}

// ── 2. query_planet_transit ───────────────────────────────────────────────────

const QueryPlanetTransitInput = z.object({
  planet: PlanetEnum.describe('Planet to query.'),
  start_date: z.string().describe('Start date in YYYY-MM-DD format.'),
  end_date: z.string().describe('End date in YYYY-MM-DD format.'),
  sign_number: z.number().int().min(1).max(12).optional().describe(
    'Optional: filter to rows where planet is in this tropical sign (1=Aries … 12=Pisces).'
  ),
})

export function registerQueryPlanetTransitTool(server: McpServer): void {
  server.tool(
    'query_planet_transit',
    'Query a planet\'s daily transit series across a date window. ' +
    'Optionally filter by tropical sign number to find when the planet transits a specific sign. ' +
    'Returns daily longitude, sign, nakshatra, is_retrograde. Max 5,000 rows.',
    QueryPlanetTransitInput.shape,
    async (params) => {
      const input = QueryPlanetTransitInput.parse(params)
      try {
        const qs = new URLSearchParams({
          planet: input.planet,
          start_date: input.start_date,
          end_date: input.end_date,
        })
        if (input.sign_number !== undefined) qs.set('sign_number', String(input.sign_number))
        const result = budgetMcpContent(await sidecarGet(`/brahmagyan/ephemeris/planet_transit?${qs}`), 'query_planet_transit')
        return {
          content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }],
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, message: msg }, null, 2) }],
          isError: true,
        }
      }
    }
  )
}

// ── 3. query_aspects_at_time ──────────────────────────────────────────────────

const QueryAspectsAtTimeInput = z.object({
  date: z.string().describe('Date in YYYY-MM-DD format.'),
  orb_degrees: z.number().min(0.1).max(10.0).optional().default(1.0).describe(
    'Orb tolerance in degrees (default 1.0; max 10.0).'
  ),
})

export function registerQueryAspectsAtTimeTool(server: McpServer): void {
  server.tool(
    'query_aspects_at_time',
    'Compute active planetary aspects (conjunction, sextile, square, trine, opposition) ' +
    'for all body pairs on a specific date. Returns body pair, aspect type, exact angle, orb.',
    QueryAspectsAtTimeInput.shape,
    async (params) => {
      const input = QueryAspectsAtTimeInput.parse(params)
      try {
        const qs = new URLSearchParams({
          date: input.date,
          orb_degrees: String(input.orb_degrees ?? 1.0),
        })
        const result = budgetMcpContent(await sidecarGet(`/brahmagyan/ephemeris/aspects?${qs}`), 'query_aspects_at_time')
        return {
          content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }],
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, message: msg }, null, 2) }],
          isError: true,
        }
      }
    }
  )
}

// ── 4. query_retrograde_periods ───────────────────────────────────────────────

const RetrogradePlanetEnum = z.enum(['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn'])

const QueryRetrogradePeriodsInput = z.object({
  planet: RetrogradePlanetEnum.describe(
    'Planet to query (Mercury, Venus, Mars, Jupiter, Saturn). Retrograde is meaningful for these only.'
  ),
  start_date: z.string().describe('Start date in YYYY-MM-DD format.'),
  end_date: z.string().describe('End date in YYYY-MM-DD format.'),
})

export function registerQueryRetrogradePeriodsTools(server: McpServer): void {
  server.tool(
    'query_retrograde_periods',
    'Find retrograde station events (retrograde_start / retrograde_end) for a planet. ' +
    'Detects sign changes in the is_retrograde flag from daily ephemeris. ' +
    'Returns station date, type, longitude at station, sign_number, retrograde day count.',
    QueryRetrogradePeriodsInput.shape,
    async (params) => {
      const input = QueryRetrogradePeriodsInput.parse(params)
      try {
        const qs = new URLSearchParams({
          planet: input.planet,
          start_date: input.start_date,
          end_date: input.end_date,
        })
        const result = budgetMcpContent(await sidecarGet(`/brahmagyan/ephemeris/retrograde_periods?${qs}`), 'query_retrograde_periods')
        return {
          content: [{ type: 'text' as const, text: JSON.stringify(result, null, 2) }],
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, message: msg }, null, 2) }],
          isError: true,
        }
      }
    }
  )
}

// ── 5. ephemeris_cache_year (resource as tool for MCP compat) ─────────────────
//
// D-1.5b item 2 (response budget): this tool previously fetched the FULL calendar year
// (up to 3,285 rows — 9 bodies × ~365 days) from the sidecar unconditionally, and shipped
// the raw JSON.stringify(result, null, 2) with no pagination and no size cap — a real
// problem at scale for an MCP wire channel. Two independent levers now bound it:
//   1. `month` (optional): narrows the SIDECAR-SIDE date window to a single calendar month
//      (~270 rows) instead of always requesting the full year — genuine narrowing, not a
//      client-side afterthought.
//   2. `limit`/`offset`: paginate the returned `rows` array (the sidecar itself has no
//      offset/limit — see all_bodies_range's `LIMIT 10000`, python-sidecar, out of this
//      lane's TS-only scope) — default 400 rows/page, honest `total`/`returned_count`.
const EphemerisCacheYearInput = z.object({
  year: z.number().int().min(1900).max(2150).describe(
    '4-digit calendar year to fetch ephemeris cache for (1900-2150).'
  ),
  month: z.number().int().min(1).max(12).optional().describe(
    'Optional: narrow to a single calendar month (1-12) within `year` — reduces the sidecar-side ' +
    'query window from ~365 days to ~28-31 days. Omit for the full year.'
  ),
  limit: z.number().int().min(1).max(3285).optional().describe(
    'Max rows to return (default 400, max 3285 = 9 bodies × ~365 days). Paginates the `rows` array.'
  ),
  offset: z.number().int().min(0).optional().describe('Pagination offset into `rows` (default 0).'),
})

const EPHEMERIS_DEFAULT_LIMIT = 400

export function registerEphemerisCacheYearTool(server: McpServer): void {
  server.tool(
    'ephemeris_cache_year',
    'Fetch ephemeris data for a calendar year (or, with `month`, a single month within it) — all 9 ' +
    'Jyotish bodies at daily resolution. Up to 3,285 rows for a full year (9 bodies × ~365 days); ' +
    'response budget: default page is 400 rows (pass `limit`/`offset` to page further, or `month` ' +
    'to narrow the underlying query itself). Use for bulk transit analysis.',
    EphemerisCacheYearInput.shape,
    async (params) => {
      const input = EphemerisCacheYearInput.parse(params)
      try {
        const startDate = input.month
          ? `${input.year}-${String(input.month).padStart(2, '0')}-01`
          : `${input.year}-01-01`
        const endDate = input.month
          ? new Date(Date.UTC(input.year, input.month, 0)).toISOString().slice(0, 10) // last day of month
          : `${input.year}-12-31`

        const result = await sidecarGet(
          `/brahmagyan/ephemeris/all_bodies_range?start_date=${startDate}&end_date=${endDate}`,
        ) as { rows?: unknown[]; [k: string]: unknown }

        const allRows = Array.isArray(result.rows) ? result.rows : []
        const limit = input.limit ?? EPHEMERIS_DEFAULT_LIMIT
        const offset = input.offset ?? 0
        const pagedRows = allRows.slice(offset, offset + limit)

        const payload = budgetMcpContent(
          {
            ...result,
            rows: pagedRows,
            pagination: {
              offset, limit,
              total: allRows.length,
              returned_count: pagedRows.length,
              more_available: offset + pagedRows.length < allRows.length,
            },
            window: { start: startDate, end: endDate, month_filter: input.month ?? null },
          },
          'ephemeris_cache_year',
        )

        return {
          content: [{ type: 'text' as const, text: JSON.stringify(payload) }],
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err)
        return {
          content: [{ type: 'text' as const, text: JSON.stringify({ error: true, message: msg }, null, 2) }],
          isError: true,
        }
      }
    }
  )
}

// ── Convenience: register all 5 ──────────────────────────────────────────────
// ephemeris_cache_native_lifetime RETIRED (M0.5 §2.5a): hardcoded "1984-2070"
// native window leaked the native identity; replaced by chart-agnostic
// ephemeris_cache_year (tool #5 above). Reverse-citation: no callers outside
// this file. See CLAUDECODE_BRIEF_MCP_M0_5_INFRA_UNBLOCK §2.5(a).

export function registerEphemerisTools(server: McpServer): void {
  registerQueryPlanetPositionTool(server)
  registerQueryPlanetTransitTool(server)
  registerQueryAspectsAtTimeTool(server)
  registerQueryRetrogradePeriodsTools(server)
  registerEphemerisCacheYearTool(server)
}
