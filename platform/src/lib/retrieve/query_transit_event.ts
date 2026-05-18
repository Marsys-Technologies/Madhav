/**
 * MARSYS-JIS Retrieval tool — query_transit_event (Phase 4D)
 *
 * Finds WHEN a transit event happens (versus query_ephemeris which looks up
 * WHAT is happening on a date). Four event classes:
 *
 *   - 'ingress'      — planet enters a sign. Reads ephemeris_daily.sign_ingress_today
 *                      (§4.B-precomputed). No sidecar call.
 *   - 'station'      — planet stations retrograde or direct. Reads retrogrades
 *                      table (migration 016). No sidecar call.
 *   - 'aspect'       — transit aspects natal-planet by N degrees. Live-compute
 *                      via sidecar POST /transit_search.
 *   - 'conjunction'  — two transit planets within orb. Live-compute via sidecar.
 *
 * Date range: 1900-01-01 to 2100-12-31 for table-backed queries. Sidecar
 * live-compute has a ±10-year window cap (latency guard, approved §4.D §3.4).
 * Lahiri sidereal throughout. Aspect degrees default: [0, 60, 90, 120, 180].
 * Default orb = 1.0°; max = 3.0°.
 *
 * Triggers R-TE planner rule: "when next" / "when will" / "when does X
 * enter/aspect/conjunct/retrograde". Use query_ephemeris (R-TC) for WHAT-not-WHEN.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_transit_event'
const TOOL_VERSION = '1.0.0'

export type EventType = 'ingress' | 'station' | 'aspect' | 'conjunction'
export type StationType = 'retrograde_start' | 'retrograde_end' | 'both'

export interface QueryTransitEventInput {
  event_type: EventType
  /** YYYY-MM-DD; defaults to today UTC. */
  start_date?: string
  /** YYYY-MM-DD; defaults to start + 1 year for ingress/station, + 2 years for aspect/conjunction. */
  end_date?: string
  // ingress:
  planet?: string
  target_sign?: string
  // station:
  station_type?: StationType
  // aspect:
  transit_planet?: string
  /** Look up natal longitude from chart_facts for this planet. */
  natal_planet?: string
  /** Use directly if planner already resolved the natal longitude. */
  natal_longitude_deg?: number
  /** Aspect degrees to search. Default [0, 60, 90, 120, 180]. */
  aspect_degrees?: number[]
  /** Orb in degrees. Default 1.0, max 3.0. */
  orb_deg?: number
  // conjunction:
  planet_a?: string
  planet_b?: string
  // common:
  /** Default 50, max 200. */
  limit?: number
}

interface EphemerisIngressRow {
  date: string
  planet: string
  sign: string
  longitude_deg: string
  sign_ingress_today: boolean
}

interface RetrogradeRow {
  planet: string
  retrograde_start: string | null
  retrograde_end: string | null
  station_type?: string
  longitude_start: string | null
  longitude_end: string | null
}

interface SidecarTransitEvent {
  event_type: string
  event_jd: number
  event_datetime_ist: string
  transit_planet: string
  secondary_planet: string | null
  exact_longitude_deg: number
  orb_at_event_deg: number
  sign: string
  nakshatra: string
  extra: Record<string, unknown>
}

const SIDECAR_KEY = process.env.PYTHON_SIDECAR_API_KEY ?? ''

async function callSidecar(endpoint: string, body: object): Promise<unknown> {
  const baseUrl = process.env.PYTHON_SIDECAR_URL
  if (!baseUrl) {
    throw new Error('PYTHON_SIDECAR_URL env var not set — sidecar call will fail')
  }
  const url = `${baseUrl}${endpoint}`
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': SIDECAR_KEY,
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Sidecar ${endpoint} returned HTTP ${res.status}`)
  return await res.json()
}

function defaultEndDate(input: QueryTransitEventInput, startDate: string): string {
  const d = new Date(startDate)
  if (input.event_type === 'aspect' || input.event_type === 'conjunction') {
    d.setFullYear(d.getFullYear() + 2)
  } else {
    d.setFullYear(d.getFullYear() + 1)
  }
  return d.toISOString().slice(0, 10)
}

function diagnosticRow(input: QueryTransitEventInput, note: string): ToolBundleResult {
  return {
    content: JSON.stringify({ note, params: input }),
    source_canonical_id: 'EPHEMERIS_DAILY',
    source_version: '1.0',
    confidence: 0,
    significance: 0,
  }
}

async function retrieveIngress(
  input: QueryTransitEventInput,
  startDate: string,
  endDate: string,
  limit: number,
): Promise<ToolBundleResult[]> {
  const storage = getStorageClient()
  const args: unknown[] = [startDate, endDate]
  let idx = 3
  let planetFilter = ''
  let signFilter = ''
  if (input.planet) {
    planetFilter = ` AND planet = $${idx}`
    args.push(input.planet.toLowerCase())
    idx++
  }
  if (input.target_sign) {
    signFilter = ` AND sign = $${idx}`
    args.push(input.target_sign)
    idx++
  }

  const sql = `
    SELECT date::text AS date, planet, sign,
           longitude_deg::text AS longitude_deg,
           sign_ingress_today
    FROM ephemeris_daily
    WHERE sign_ingress_today = true
      AND date >= $1::date
      AND date <= $2::date
      ${planetFilter}${signFilter}
    ORDER BY date ASC
    LIMIT ${limit}
  `
  const result = await storage.query(sql, args)
  const rows = result.rows as EphemerisIngressRow[]

  if (rows.length === 0) {
    return [diagnosticRow(input,
      `No ingress events found for the requested params in ${startDate}–${endDate}. ` +
      `If ephemeris_daily is empty, run bootstrap_ephemeris.py.`,
    )]
  }
  return rows.map(r => ({
    content: JSON.stringify({
      event_type: 'ingress',
      date: r.date,
      planet: r.planet,
      sign: r.sign,
      longitude_deg: Number(r.longitude_deg),
    }),
    source_canonical_id: 'EPHEMERIS_DAILY',
    source_version: '1.0',
    confidence: 1.0,
    significance: 0.9,
  }))
}

async function retrieveStation(
  input: QueryTransitEventInput,
  startDate: string,
  endDate: string,
  limit: number,
): Promise<ToolBundleResult[]> {
  const storage = getStorageClient()
  const args: unknown[] = []
  const conditions: string[] = []
  let idx = 1

  if (input.planet) {
    conditions.push(`planet = $${idx}`)
    args.push(input.planet.toLowerCase())
    idx++
  }

  // Filter by station_type: retrograde_start = rows where retrograde_start is in range;
  // retrograde_end = rows where retrograde_end is in range; both = either.
  const stationType = input.station_type ?? 'both'
  if (stationType === 'retrograde_start') {
    conditions.push(`retrograde_start >= $${idx}::date AND retrograde_start <= $${idx + 1}::date`)
    args.push(startDate, endDate)
    idx += 2
  } else if (stationType === 'retrograde_end') {
    conditions.push(`retrograde_end >= $${idx}::date AND retrograde_end <= $${idx + 1}::date`)
    args.push(startDate, endDate)
    idx += 2
  } else {
    // both
    conditions.push(
      `(retrograde_start >= $${idx}::date AND retrograde_start <= $${idx + 1}::date)` +
      ` OR (retrograde_end >= $${idx + 2}::date AND retrograde_end <= $${idx + 3}::date)`,
    )
    args.push(startDate, endDate, startDate, endDate)
    idx += 4
  }

  const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : ''
  const sql = `
    SELECT planet,
           retrograde_start::text AS retrograde_start,
           retrograde_end::text AS retrograde_end,
           longitude_start::text AS longitude_start,
           longitude_end::text AS longitude_end
    FROM retrogrades
    ${where}
    ORDER BY COALESCE(retrograde_start, retrograde_end) ASC
    LIMIT ${limit}
  `
  const result = await storage.query(sql, args)
  const rows = result.rows as RetrogradeRow[]

  if (rows.length === 0) {
    return [diagnosticRow(input,
      `No station events found for the requested params in ${startDate}–${endDate}.`,
    )]
  }
  return rows.map(r => ({
    content: JSON.stringify({
      event_type: 'station',
      planet: r.planet,
      retrograde_start: r.retrograde_start,
      retrograde_end: r.retrograde_end,
      longitude_start: r.longitude_start != null ? Number(r.longitude_start) : null,
      longitude_end: r.longitude_end != null ? Number(r.longitude_end) : null,
    }),
    source_canonical_id: 'RETROGRADES',
    source_version: '1.0',
    confidence: 1.0,
    significance: 0.9,
  }))
}

async function lookupNatalLongitude(natalPlanet: string): Promise<number | null> {
  const storage = getStorageClient()
  const result = await storage.query(
    `SELECT longitude_deg::text AS longitude_deg
     FROM chart_facts
     WHERE category = 'planet' AND planet = $1
     LIMIT 1`,
    [natalPlanet.toLowerCase()],
  )
  if (result.rows.length === 0) return null
  return Number((result.rows[0] as { longitude_deg: string }).longitude_deg)
}

async function retrieveSidecar(
  input: QueryTransitEventInput,
  startDate: string,
  endDate: string,
): Promise<ToolBundleResult[]> {
  const eventType = input.event_type

  let body: Record<string, unknown>

  if (eventType === 'aspect') {
    const transitPlanet = input.transit_planet
    if (!transitPlanet) {
      return [diagnosticRow(input, 'aspect query requires transit_planet')]
    }

    let targetLon = input.natal_longitude_deg ?? null
    if (targetLon == null && input.natal_planet) {
      targetLon = await lookupNatalLongitude(input.natal_planet)
      if (targetLon == null) {
        return [diagnosticRow(input,
          `natal_planet '${input.natal_planet}' not found in chart_facts`,
        )]
      }
    }
    if (targetLon == null) {
      return [diagnosticRow(input,
        'aspect query requires natal_longitude_deg or natal_planet',
      )]
    }

    body = {
      event_type: 'aspect',
      start_date: startDate,
      end_date: endDate,
      transit_planet: transitPlanet,
      target_planet_natal_longitude_deg: targetLon,
      aspect_degrees: input.aspect_degrees ?? [0, 60, 90, 120, 180],
      orb_deg: Math.max(0, Math.min(3.0, input.orb_deg ?? 1.0)),
    }
  } else {
    // conjunction
    const { planet_a, planet_b } = input
    if (!planet_a || !planet_b) {
      return [diagnosticRow(input, 'conjunction query requires planet_a and planet_b')]
    }
    body = {
      event_type: 'conjunction',
      start_date: startDate,
      end_date: endDate,
      planet_a,
      planet_b,
      orb_deg: Math.max(0, Math.min(3.0, input.orb_deg ?? 1.0)),
    }
  }

  const raw = await callSidecar('/transit_search', body)
  const events = raw as SidecarTransitEvent[]

  if (!events || events.length === 0) {
    return [diagnosticRow(input,
      `No ${eventType} events found in ${startDate}–${endDate} with the requested params.`,
    )]
  }

  return events.map(e => ({
    content: JSON.stringify(e),
    source_canonical_id: 'TRANSIT_SEARCH_SIDECAR',
    source_version: '1.0',
    confidence: 1.0,
    significance: 0.9,
  }))
}

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  try {
    return await retrieveImpl(plan, params, start)
  } catch (err) {
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: (params ?? null) as Record<string, unknown> | null,
      status: 'error',
      rows_returned: 0,
      latency_ms: Date.now() - start,
      token_estimate: 0,
      data_asset_id: 'TRANSIT_EVENT',
      error_code: err instanceof Error ? err.message : String(err),
      served_from_cache: false,
      fallback_used: false,
    })
    throw err
  }
}

async function retrieveImpl(
  plan: QueryPlan,
  params: Record<string, unknown> | undefined,
  start: number,
): Promise<ToolBundle> {
  const input = (params ?? {}) as unknown as QueryTransitEventInput
  const limit = Math.max(1, Math.min(200, input.limit ?? 50))
  const startDate = input.start_date ?? new Date().toISOString().slice(0, 10)
  const endDate = input.end_date ?? defaultEndDate(input, startDate)

  let results: ToolBundleResult[]

  switch (input.event_type) {
    case 'ingress':
      results = await retrieveIngress(input, startDate, endDate, limit)
      break
    case 'station':
      results = await retrieveStation(input, startDate, endDate, limit)
      break
    case 'aspect':
    case 'conjunction':
      results = await retrieveSidecar(input, startDate, endDate)
      break
    default:
      results = [diagnosticRow(input,
        `Unknown event_type '${input.event_type}'. Use ingress | station | aspect | conjunction.`,
      )]
  }

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: { ...input, limit, start_date: startDate, end_date: endDate },
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: input as unknown as Record<string, unknown>,
    status: 'success',
    rows_returned: results.length,
    latency_ms: bundle.latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'TRANSIT_EVENT',
    error_code: null,
    served_from_cache: false,
    fallback_used: results[0]?.confidence === 0,
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Find WHEN transit events happen (versus query_ephemeris which is WHAT on a date). ' +
    'Four event classes: ingress (planet enters a sign — reads ephemeris_daily.' +
    'sign_ingress_today from §4.B), station (planet stations retrograde/direct — reads ' +
    'retrogrades table), aspect (transit-to-natal by degree+orb — live compute via ' +
    'sidecar), conjunction (two transit planets within orb — live compute via sidecar). ' +
    'Lahiri sidereal. Use whenever the query asks "when next" / "when will" / "next time" / ' +
    '"when does X enter/aspect/conjunct/station". Pairs with query_ephemeris + ' +
    'query_panchanga under R-TC/R-PA for context; R-TE handles the search trigger.',
  retrieve,
}
