/**
 * MARSYS-JIS Retrieval tool — query_ephemeris (Phase 4A)
 *
 * Surfaces date-indexed planetary positions from the ephemeris_daily table
 * (migration 015). 9 grahas × ~73,050 days = 657K rows, 1900-01-01 → 2100-12-31,
 * Lahiri sidereal, midnight UT, populated by bootstrap_ephemeris.py.
 *
 * Use this for any query that needs transit-context — that is, planetary
 * positions at a specific date (past LEL event, current moment, future event,
 * or date range). Pairs with the R-TC planner rule which attaches this tool
 * at priority 2 for any non-natal query.
 *
 * Distinct from:
 *   - chart_facts_query: natal placements only
 *   - temporal: Vedic event-window data (sade sati, eclipses, retrogrades,
 *     dasha chain) — not raw planet positions
 *   - cross_varga_dignity_query: D1/D9/D10 natal dignity
 *
 * Date range: 1900-01-01 through 2100-12-31. Outside this window the tool
 * returns a diagnostic empty row.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_ephemeris'
const TOOL_VERSION = '1.0.0'

// All 9 grahas as stored in ephemeris_daily.planet (lowercase).
const VALID_PLANETS = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu'] as const
type PlanetName = (typeof VALID_PLANETS)[number]

export type DerivedField = 'dignity' | 'combust' | 'vargottama' | 'ingress' | 'yuddha' | 'house' | 'house_bc'

export interface QueryEphemerisInput {
  /** Single date (YYYY-MM-DD). Defaults to today UTC if neither date nor start_date provided. */
  date?: string
  /** Start of date range (YYYY-MM-DD). When set with end_date, returns inclusive range. */
  start_date?: string
  /** End of date range (YYYY-MM-DD). Required when start_date is set. */
  end_date?: string
  /** Single planet (canonical or capitalized name, normalized to lowercase). */
  planet?: string
  /** Multiple planets. */
  planets?: string[]
  /** Maximum rows. Clamped to [1, 500]. Defaults to 100. */
  limit?: number
  /**
   * Which derived columns to include. Defaults to all 6 (dignity, combust,
   * vargottama, ingress, yuddha, house). Pass [] to opt out for token-budget
   * tight queries. Pass a subset to include only specific fields.
   */
  derived_fields?: DerivedField[]
}

interface EphemerisRow {
  date: string          // pg DATE → ISO string
  planet: string
  longitude_deg: string // NUMERIC → string from pg
  latitude_deg: string | null
  speed_deg_per_day: string
  is_retrograde: boolean
  sign: string
  sign_degree: string
  nakshatra: string
  nakshatra_pada: number
  ayanamsha: string
  ephemeris_version: string
  // Phase 4B derived columns (nullable until rebuilt)
  dignity_d1: string | null
  is_combust: boolean | null
  combust_orb_deg: string | null
  vargottama_today: boolean | null
  sign_ingress_today: boolean | null
  whole_sign_house: number | null
  graha_yuddha_with: string | null
  // Phase 4 §6.6 Bhava-Chalit (Sripati cusp) house — nullable until backfilled
  bhava_chalit_house: number | null
}

const ALL_DERIVED_FIELDS: DerivedField[] = ['dignity', 'combust', 'vargottama', 'ingress', 'yuddha', 'house', 'house_bc']

function normalizePlanet(p: string): PlanetName | null {
  const lower = p.toLowerCase().trim()
  return (VALID_PLANETS as readonly string[]).includes(lower) ? (lower as PlanetName) : null
}

function buildWhere(p: QueryEphemerisInput): { where: string; args: unknown[] } {
  const conditions: string[] = []
  const args: unknown[] = []
  let idx = 1

  // Date conditions
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

  // Planet conditions
  const planetList: string[] = []
  if (p.planet) {
    const np = normalizePlanet(p.planet)
    if (np) planetList.push(np)
  }
  if (p.planets) {
    for (const x of p.planets) {
      const np = normalizePlanet(x)
      if (np) planetList.push(np)
    }
  }
  if (planetList.length > 0) {
    conditions.push(`planet = ANY($${idx}::text[])`)
    args.push(planetList)
    idx++
  }

  return { where: conditions.join(' AND '), args }
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
      data_asset_id: 'EPHEMERIS_DAILY',
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
  const input = (params ?? {}) as QueryEphemerisInput
  const limit = Math.max(1, Math.min(500, input.limit ?? 100))

  const { where, args } = buildWhere(input)

  const sql = `
    SELECT
      date::text AS date,
      planet,
      longitude_deg::text AS longitude_deg,
      latitude_deg::text AS latitude_deg,
      speed_deg_per_day::text AS speed_deg_per_day,
      is_retrograde,
      sign,
      sign_degree::text AS sign_degree,
      nakshatra,
      nakshatra_pada,
      ayanamsha,
      ephemeris_version,
      dignity_d1,
      is_combust,
      combust_orb_deg::text AS combust_orb_deg,
      vargottama_today,
      sign_ingress_today,
      whole_sign_house,
      graha_yuddha_with,
      bhava_chalit_house
    FROM ephemeris_daily
    WHERE ${where}
    ORDER BY date ASC, planet ASC
    LIMIT ${limit}
  `

  const storage = getStorageClient()
  const result = await storage.query(sql, args)
  const rows = result.rows as EphemerisRow[]

  // Determine which derived fields to include (default: all).
  const derivedFields: DerivedField[] =
    input.derived_fields !== undefined ? input.derived_fields : ALL_DERIVED_FIELDS

  const results: ToolBundleResult[] = rows.length > 0
    ? rows.map(r => {
        const base: Record<string, unknown> = {
          date: r.date,
          planet: r.planet,
          longitude_deg: Number(r.longitude_deg),
          latitude_deg: r.latitude_deg !== null ? Number(r.latitude_deg) : null,
          speed_deg_per_day: Number(r.speed_deg_per_day),
          is_retrograde: r.is_retrograde,
          sign: r.sign,
          sign_degree: Number(r.sign_degree),
          nakshatra: r.nakshatra,
          nakshatra_pada: r.nakshatra_pada,
          ayanamsha: r.ayanamsha,
          ephemeris_version: r.ephemeris_version,
        }
        if (derivedFields.includes('dignity'))   base.dignity = r.dignity_d1
        if (derivedFields.includes('combust'))   { base.is_combust = r.is_combust; base.combust_orb_deg = r.combust_orb_deg !== null ? Number(r.combust_orb_deg) : null }
        if (derivedFields.includes('vargottama')) base.vargottama = r.vargottama_today
        if (derivedFields.includes('ingress'))   base.sign_ingress = r.sign_ingress_today
        if (derivedFields.includes('house'))     base.whole_sign_house = r.whole_sign_house
        if (derivedFields.includes('yuddha'))    base.graha_yuddha_with = r.graha_yuddha_with
        if (derivedFields.includes('house_bc'))  base.bhava_chalit_house = r.bhava_chalit_house
        return {
          content: JSON.stringify(base),
          source_canonical_id: 'EPHEMERIS_DAILY',
          source_version: '1.0',
          confidence: 1.0,
          significance: 0.85,
        }
      })
    : [{
        content: JSON.stringify({
          note: 'ephemeris_daily empty or out-of-range for requested params. Date range supported: 1900-01-01 to 2100-12-31.',
          params: input,
        }),
        source_canonical_id: 'EPHEMERIS_DAILY',
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
    data_asset_id: 'EPHEMERIS_DAILY',
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
    'Date-indexed planetary positions PLUS Vedic-interpretable derived state from ' +
    'the ephemeris_daily table (657K rows, 1900-2100, 9 grahas, Lahiri sidereal). ' +
    'Returns per-planet per-day: longitude, sign, nakshatra+pada, retrograde, speed, ' +
    'AND derived state: dignity (exalted/debilitated/own/mooltrikona/neutral), ' +
    'combust state + orb degrees, vargottama (D1=D9 sign), whole-sign-house (Parashari, ' +
    'relative to native lagna = Aries), bhava-chalit-house (Sripati-cusp-based — ' +
    'angular bhava for sandhi-planet refinement; compare with whole_sign_house for ' +
    'planets within 3° of a sign boundary), sign-ingress flag (entered new sign today), ' +
    'graha-yuddha (within 1° of another planet — among Mars/Mercury/Jupiter/Venus/Saturn). ' +
    'CANONICAL SURFACE for any transit-context query — both the raw positions AND ' +
    'their Vedic interpretation. Default attached at priority 2 under R-TC for any ' +
    'non-natal query. Use derived_fields:[] to skip derived columns for token-tight calls.',
  retrieve,
}
