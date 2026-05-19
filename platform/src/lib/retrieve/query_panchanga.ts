/**
 * MARSYS-JIS — query_panchanga RetrievalTool
 *
 * Returns daily Panchang state — five angas (tithi, nakshatra, yoga, karana, vara),
 * sunrise/sunset, inauspicious windows (Rahu Kalam, Yamagandam, Gulika), auspicious
 * windows (Abhijit, Brahma Muhurta), Choghadiya, Hora, special yogas (Sarvartha Siddhi,
 * Amrit Siddhi, Ravi/Guru Pushya, Tripushkar, Bhadra, Panchaka), and 9-graha positions
 * at sunrise. Call when the query asks about today/a date's Panchang, auspicious timing,
 * or a good day for X. Use query_ephemeris for raw planetary positions at arbitrary moments;
 * use query_panchanga for the panchang_daily-shaped daily state.
 *
 * Engine-direct path: calls sidecar /api/compute/panchanga which invokes panchang_engine
 * on demand. No SQL cache this session — 4C-2 will add panchang_daily cache below
 * the endpoint with zero changes to this tool.
 *
 * Phase: 4C-3
 */

import crypto from 'crypto'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_panchanga'
const TOOL_VERSION = '1.0.0'
const DATA_ASSET_ID = 'PANCHANG_DAILY'

// Default location: Bhubaneswar (project canonical per §8 and D1 decisions)
const DEFAULT_LAT = 20.27
const DEFAULT_LON = 85.84
const DEFAULT_TZ = 330 // IST +05:30

interface PanchangaParams {
  date?: string             // ISO date YYYY-MM-DD; defaults to today
  lat?: number              // defaults to Bhubaneswar lat
  lon?: number              // defaults to Bhubaneswar lon
  tz_offset_minutes?: number // defaults to +330 (IST)
  chart_id?: string         // personalise overlay; 4C-5 will use; ignored here
  fields?: string[]         // field projection for token budget
  range?: { from: string; to: string } // optional range query (uses /panchanga/range)
}

/**
 * Typed error thrown when the sidecar call fails, allowing the orchestrator
 * to handle gracefully instead of receiving a raw exception.
 */
export class RetrievalToolError extends Error {
  constructor(
    public readonly tool: string,
    public readonly cause_message: string,
    public readonly status_code?: number,
  ) {
    super(`[${tool}] ${cause_message}`)
    this.name = 'RetrievalToolError'
  }
}

async function callSidecar(endpoint: string, body: object): Promise<unknown> {
  const baseUrl = process.env.PYTHON_SIDECAR_URL
  if (!baseUrl) {
    throw new RetrievalToolError(
      TOOL_NAME,
      'PYTHON_SIDECAR_URL env var not set — sidecar call will fail',
    )
  }
  const url = `${baseUrl}${endpoint}`
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new RetrievalToolError(
      TOOL_NAME,
      `Sidecar ${endpoint} returned HTTP ${res.status}`,
      res.status,
    )
  }
  return await res.json()
}

/**
 * Convert a Panchang dict (from panchang_to_dict serializer) into ToolBundleResult entries.
 * Each major Panchang section becomes one result entry so synthesis can cite by section.
 *
 * Fact structure follows PANCHANG_DAILY_v1_0.md §5 field semantics.
 */
function panchangToResults(
  panchangDict: Record<string, unknown>,
  computationVersion: string,
  ephemerisVersion: string,
): ToolBundleResult[] {
  const source_canonical_id = DATA_ASSET_ID
  const source_version = computationVersion

  const results: ToolBundleResult[] = []

  // 1. Five angas (tithi, nakshatra, yoga, karana, vara) + paksha
  results.push({
    content: JSON.stringify({
      section: 'five_angas',
      tithi: panchangDict['tithi'],
      nakshatra: panchangDict['nakshatra'],
      yoga: panchangDict['yoga'],
      karana_first: panchangDict['karana_first'],
      karana_second: panchangDict['karana_second'],
      vara: panchangDict['vara'],
      paksha: panchangDict['paksha'],
    }),
    source_canonical_id,
    source_version,
    confidence: 1.0,
    significance: 1.0,
  })

  // 2. Timings: sunrise/sunset/moonrise/moonset + inauspicious + auspicious
  results.push({
    content: JSON.stringify({
      section: 'timings',
      sunrise_utc: panchangDict['sunrise_utc'],
      sunset_utc: panchangDict['sunset_utc'],
      moonrise_utc: panchangDict['moonrise_utc'],
      moonset_utc: panchangDict['moonset_utc'],
      inauspicious: panchangDict['inauspicious'],
      auspicious: panchangDict['auspicious'],
    }),
    source_canonical_id,
    source_version,
    confidence: 1.0,
    significance: 0.9,
  })

  // 3. Special yogas (active auspicious / inauspicious yoga periods)
  results.push({
    content: JSON.stringify({
      section: 'special_yogas',
      special_yogas: panchangDict['special_yogas'],
    }),
    source_canonical_id,
    source_version,
    confidence: 1.0,
    significance: 0.95,
  })

  // 4. Planetary positions at sunrise
  results.push({
    content: JSON.stringify({
      section: 'planets_at_sunrise',
      planets: panchangDict['planets'],
      ephemeris_version: ephemerisVersion,
    }),
    source_canonical_id,
    source_version,
    confidence: 1.0,
    significance: 0.85,
  })

  // 5. Choghadiya + Hora (combined; generally lower-priority unless explicitly requested)
  results.push({
    content: JSON.stringify({
      section: 'choghadiya_hora',
      choghadiya: panchangDict['choghadiya'],
      hora: panchangDict['hora'],
    }),
    source_canonical_id,
    source_version,
    confidence: 1.0,
    significance: 0.7,
  })

  return results
}

async function retrieve(
  plan: QueryPlan,
  params?: Record<string, unknown>,
): Promise<ToolBundle> {
  const start = Date.now()

  const typedParams = (params ?? {}) as PanchangaParams

  // Resolve defaults
  const today = new Date().toISOString().slice(0, 10)
  const date = typedParams.date ?? today
  const lat = typedParams.lat ?? DEFAULT_LAT
  const lon = typedParams.lon ?? DEFAULT_LON
  const tz_offset_minutes = typedParams.tz_offset_minutes ?? DEFAULT_TZ
  const chart_id = typedParams.chart_id ?? null // accepted; ignored this session (4C-5 scope)
  const fields = typedParams.fields ?? null
  const range = typedParams.range ?? null

  const invocation_params: Record<string, unknown> = {
    date,
    lat,
    lon,
    tz_offset_minutes,
    ...(chart_id ? { chart_id } : {}),
    ...(fields ? { fields } : {}),
    ...(range ? { range } : {}),
  }

  let results: ToolBundleResult[] = []
  let computationVersion = TOOL_VERSION
  let ephemerisVersion = 'unknown'
  let served_from_cache = false

  if (range) {
    // Range query path: /api/compute/panchanga/range
    const rangeBody = {
      date_from: range.from,
      date_to: range.to,
      lat,
      lon,
      tz_offset_minutes,
    }
    const response = (await callSidecar('/api/compute/panchanga/range', rangeBody)) as {
      ok: boolean
      panchangs: Array<Record<string, unknown>>
      count: number
    }
    if (!response.ok || !response.panchangs?.length) {
      throw new RetrievalToolError(TOOL_NAME, 'Sidecar returned empty range response')
    }

    // For range queries: one result per day, collapsed into a single entry for token budget
    const firstPanchang = response.panchangs[0]
    computationVersion = (firstPanchang['computation_version'] as string) ?? TOOL_VERSION
    ephemerisVersion = (firstPanchang['ephemeris_version'] as string) ?? 'unknown'

    results.push({
      content: JSON.stringify({
        section: 'panchang_range',
        date_from: range.from,
        date_to: range.to,
        count: response.count,
        panchangs: response.panchangs,
      }),
      source_canonical_id: DATA_ASSET_ID,
      source_version: computationVersion,
      confidence: 1.0,
      significance: 0.9,
    })
  } else {
    // Single-day query path: /api/compute/panchanga
    const singleBody: Record<string, unknown> = {
      date,
      lat,
      lon,
      tz_offset_minutes,
      ...(chart_id ? { chart_id } : {}),
      ...(fields ? { fields } : {}),
    }
    const response = (await callSidecar('/api/compute/panchanga', singleBody)) as {
      ok: boolean
      panchang: Record<string, unknown>
      cache_hit: boolean
    }
    if (!response.ok || !response.panchang) {
      throw new RetrievalToolError(TOOL_NAME, 'Sidecar returned empty panchang response')
    }

    served_from_cache = response.cache_hit ?? false
    const panchangDict = response.panchang
    computationVersion = (panchangDict['computation_version'] as string) ?? TOOL_VERSION
    ephemerisVersion = (panchangDict['ephemeris_version'] as string) ?? 'unknown'

    // Convert Panchang dict to ToolBundleResult[] entries (one per major section)
    results = panchangToResults(panchangDict, computationVersion, ephemerisVersion)

    // Client-side field projection: clip results if specific fields requested
    // (server-side already projects; this is defense-in-depth)
    if (fields && fields.length > 0) {
      results = results.filter(r => {
        try {
          const parsed = JSON.parse(r.content) as Record<string, unknown>
          const section = parsed['section'] as string
          // Keep sections that contain at least one requested field by section name or key
          return (
            fields.some(f => section?.includes(f)) ||
            fields.some(f => Object.keys(parsed).includes(f))
          )
        } catch {
          return true // keep if we can't parse
        }
      })
      // Always keep at least the five_angas section
      if (results.length === 0) {
        results = panchangToResults(panchangDict, computationVersion, ephemerisVersion).slice(0, 1)
      }
    }
  }

  const latency_ms = Date.now() - start

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 100))))
      .digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params,
    results,
    served_from_cache,
    latency_ms,
    result_hash,
    schema_version: '1.0',
  }

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Returns daily Panchang state — five angas (tithi, nakshatra, yoga, karana, vara), ' +
    'sunrise/sunset, inauspicious windows (Rahu Kalam, Yamagandam, Gulika), auspicious ' +
    'windows (Abhijit, Brahma Muhurta), Choghadiya, Hora, special yogas (Sarvartha Siddhi, ' +
    'Amrit Siddhi, Ravi/Guru Pushya, Tripushkar, Bhadra, Panchaka), and 9-graha positions ' +
    'at sunrise. Call when the query asks about today/a date\'s Panchang, auspicious timing, ' +
    'or a good day for X. Use query_ephemeris for raw planetary positions at arbitrary moments; ' +
    'use query_panchanga for the panchang_daily-shaped daily state.',
  retrieve,
}

// Named export used in the brief spec (queryPanchanga)
export const queryPanchanga = tool
