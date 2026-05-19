/**
 * MARSYS-JIS Retrieval tool — query_panchanga (Phase 4C)
 *
 * Surfaces the 5 limbs of Vedic time (tithi / vara / moon nakshatra / yoga /
 * karana) for any date 1900-2100, anchored to Bhubaneswar sunrise (native
 * observer per approved decision §6.2). Precomputed in panchanga_daily
 * (migration 060) by bootstrap_panchanga.py.
 *
 * Use this for any query that references time-quality semantics:
 *   - tithi / paksha / lunar phase (Purnima, Amavasya, Ekadashi, etc.)
 *   - Moon's nakshatra-of-day (distinct from natal Moon nakshatra)
 *   - vara / day-of-week in astrological context
 *   - yoga / karana
 *   - muhurta / auspicious-day questions (this tool gives the inputs; synthesis
 *     reasons over them)
 *
 * Vara boundary is SUNRISE, not midnight. A vara row keyed to date D covers
 * the period from sunrise(D) to sunrise(D+1).
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_panchanga'
const TOOL_VERSION = '1.0.0'

export type PanchangaField = 'tithi' | 'vara' | 'nakshatra' | 'yoga' | 'karana' | 'sunrise'

export interface QueryPanchangaInput {
  /** Single date (YYYY-MM-DD). Defaults to today UTC if neither date nor start_date provided. */
  date?: string
  /** Range start (YYYY-MM-DD). When set with end_date, returns inclusive range. */
  start_date?: string
  /** Range end (YYYY-MM-DD). Required when start_date is set. */
  end_date?: string
  /** Filter to a specific tithi number 1-30. */
  tithi?: number
  /** Filter by tithi name, e.g. 'Shukla Ekadashi'. */
  tithi_name?: string
  /** Filter to a paksha. */
  paksha?: 'shukla' | 'krishna'
  /** Filter to a specific Moon nakshatra name. */
  moon_nakshatra?: string
  /** Filter by vara lord name, e.g. 'Saturn' returns all Shanivara days. */
  vara_lord?: string
  /** Filter by yoga name. */
  yoga?: string
  /** Filter by karana name. */
  karana?: string
  /** Which field groups to include in the response. Defaults to all. */
  fields?: PanchangaField[]
  /** Maximum rows returned. Clamped to [1, 500]. Defaults to 100. */
  limit?: number
}

interface PanchangaRow {
  date: string
  sunrise_utc: string
  sunrise_jd: string
  sunrise_ist: string
  tithi: number
  tithi_name: string
  paksha: string
  tithi_fraction: string
  vara: string
  vara_lord: string
  vara_index: number
  moon_nakshatra: string
  moon_nakshatra_index: number
  moon_nakshatra_pada: number
  moon_longitude_deg: string
  sun_longitude_deg: string
  yoga: string
  yoga_index: number
  karana: string
  karana_position_in_month: number
  ayanamsha: string
  observer_lat: string
  observer_lon: string
  observer_alt_m: string
  ephemeris_version: string
}

const ALL_FIELDS: PanchangaField[] = ['tithi', 'vara', 'nakshatra', 'yoga', 'karana', 'sunrise']

function buildWhere(p: QueryPanchangaInput): { where: string; args: unknown[] } {
  const conditions: string[] = []
  const args: unknown[] = []
  let idx = 1

  if (p.start_date && p.end_date) {
    conditions.push(`date >= $${idx}::date`)
    args.push(p.start_date)
    idx++
    conditions.push(`date <= $${idx}::date`)
    args.push(p.end_date)
    idx++
  } else if (p.date) {
    conditions.push(`date = $${idx}::date`)
    args.push(p.date)
    idx++
  } else {
    conditions.push(`date = CURRENT_DATE`)
  }

  if (p.tithi !== undefined) {
    conditions.push(`tithi = $${idx}`)
    args.push(p.tithi)
    idx++
  }
  if (p.tithi_name) {
    conditions.push(`tithi_name = $${idx}`)
    args.push(p.tithi_name)
    idx++
  }
  if (p.paksha) {
    conditions.push(`paksha = $${idx}`)
    args.push(p.paksha)
    idx++
  }
  if (p.moon_nakshatra) {
    conditions.push(`moon_nakshatra = $${idx}`)
    args.push(p.moon_nakshatra)
    idx++
  }
  if (p.vara_lord) {
    conditions.push(`vara_lord = $${idx}`)
    args.push(p.vara_lord)
    idx++
  }
  if (p.yoga) {
    conditions.push(`yoga = $${idx}`)
    args.push(p.yoga)
    idx++
  }
  if (p.karana) {
    conditions.push(`karana = $${idx}`)
    args.push(p.karana)
    idx++
  }

  return { where: conditions.join(' AND '), args }
}

function rowToContent(r: PanchangaRow, fields: PanchangaField[]): Record<string, unknown> {
  const out: Record<string, unknown> = { date: r.date }

  if (fields.includes('sunrise')) {
    out.sunrise_utc = r.sunrise_utc
    out.sunrise_jd = Number(r.sunrise_jd)
    out.sunrise_ist = r.sunrise_ist
  }
  if (fields.includes('tithi')) {
    out.tithi = r.tithi
    out.tithi_name = r.tithi_name
    out.paksha = r.paksha
    out.tithi_fraction = Number(r.tithi_fraction)
  }
  if (fields.includes('vara')) {
    out.vara = r.vara
    out.vara_lord = r.vara_lord
    out.vara_index = r.vara_index
  }
  if (fields.includes('nakshatra')) {
    out.moon_nakshatra = r.moon_nakshatra
    out.moon_nakshatra_index = r.moon_nakshatra_index
    out.moon_nakshatra_pada = r.moon_nakshatra_pada
    out.moon_longitude_deg = Number(r.moon_longitude_deg)
    out.sun_longitude_deg = Number(r.sun_longitude_deg)
  }
  if (fields.includes('yoga')) {
    out.yoga = r.yoga
    out.yoga_index = r.yoga_index
  }
  if (fields.includes('karana')) {
    out.karana = r.karana
    out.karana_position_in_month = r.karana_position_in_month
  }

  return out
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
      data_asset_id: 'PANCHANGA_DAILY',
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
  const input = (params ?? {}) as QueryPanchangaInput
  const limit = Math.max(1, Math.min(500, input.limit ?? 100))
  const fields: PanchangaField[] = input.fields !== undefined ? input.fields : ALL_FIELDS

  const { where, args } = buildWhere(input)

  const sql = `
    SELECT
      date::text AS date,
      sunrise_utc::text AS sunrise_utc,
      sunrise_jd::text AS sunrise_jd,
      sunrise_ist::text AS sunrise_ist,
      tithi,
      tithi_name,
      paksha,
      tithi_fraction::text AS tithi_fraction,
      vara,
      vara_lord,
      vara_index,
      moon_nakshatra,
      moon_nakshatra_index,
      moon_nakshatra_pada,
      moon_longitude_deg::text AS moon_longitude_deg,
      sun_longitude_deg::text AS sun_longitude_deg,
      yoga,
      yoga_index,
      karana,
      karana_position_in_month,
      ayanamsha,
      observer_lat::text AS observer_lat,
      observer_lon::text AS observer_lon,
      observer_alt_m::text AS observer_alt_m,
      ephemeris_version
    FROM panchanga_daily
    WHERE ${where}
    ORDER BY date ASC
    LIMIT ${limit}
  `

  const storage = getStorageClient()
  const result = await storage.query(sql, args)
  const rows = result.rows as PanchangaRow[]

  const results: ToolBundleResult[] = rows.length > 0
    ? rows.map(r => ({
        content: JSON.stringify(rowToContent(r, fields)),
        source_canonical_id: 'PANCHANGA_DAILY',
        source_version: '1.0',
        confidence: 1.0,
        significance: 0.85,
      }))
    : [{
        content: JSON.stringify({
          note: 'panchanga_daily empty or out-of-range for requested params. Date range supported: 1900-01-01 to 2100-12-31. Table requires bootstrap_panchanga.py run.',
          params: input,
        }),
        source_canonical_id: 'PANCHANGA_DAILY',
        source_version: '1.0',
        confidence: 0,
        significance: 0,
      }]

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
    invocation_params: { ...input, limit },
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: input as Record<string, unknown>,
    status: 'success',
    rows_returned: rows.length,
    latency_ms: bundle.latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'PANCHANGA_DAILY',
    error_code: null,
    served_from_cache: false,
    fallback_used: rows.length === 0,
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Sunrise-anchored Vedic panchanga (tithi / vara / Moon nakshatra / yoga / karana) ' +
    'from panchanga_daily — precomputed for Bhubaneswar observer (native birth location). ' +
    '73K rows, 1900-2100. CANONICAL SURFACE for time-quality queries — anything ' +
    'referencing lunar phase (Purnima/Amavasya/Ekadashi), Moon-nakshatra-of-day ' +
    '(distinct from natal Moon nakshatra), vara/day-of-week in astrological context, ' +
    'yoga, karana, or muhurta inputs. Vara boundary is sunrise, not midnight. ' +
    'Pairs with query_ephemeris under R-TC for any non-natal query — ephemeris gives ' +
    'transit positions, panchanga gives time-quality.',
  retrieve,
}
