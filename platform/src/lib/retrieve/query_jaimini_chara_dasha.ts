/**
 * MARSYS-JIS Retrieval tool — query_jaimini_chara_dasha (UDA-1-S3)
 *
 * Jaimini Chara Dasha schedule lookup. Calls the Python sidecar
 * /jaimini_drishti/chara_dasha (active period) and
 * /jaimini_drishti/chara_dasha/full (full 12-rashi timeline).
 *
 * Algorithm (standard Jaimini Chara Dasha):
 *   - Each of the 12 rashis serves as a dasha lord.
 *   - Period length is determined by the sign lord's longitude within its own sign:
 *       Odd rashis  (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius):
 *           years = 30 − floor(lord_lon_in_sign)
 *       Even rashis (Taurus, Cancer, Virgo, Scorpio, Capricorn, Pisces):
 *           years = floor(lord_lon_in_sign) + 1
 *   - Years capped at 12 per rashi; total cycle = 120 years.
 *   - Sequence starts from the native's Lagna rashi.
 *
 * Data source: Python sidecar /jaimini_drishti/chara_dasha endpoint.
 *
 * Ported from: platform-mcp/src/tools/query_jaimini_chara_dasha.ts
 * Session: UDA-1-S3
 */

import crypto from 'crypto'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_jaimini_chara_dasha'
const TOOL_VERSION = '1.0.0'
const SIDECAR_KEY = process.env.PYTHON_SIDECAR_API_KEY ?? ''

// ── Types ─────────────────────────────────────────────────────────────────────

export interface RashiPeriod {
  rashi: string
  sign_lord: string
  years?: number
  start_date: string
  end_date: string
}

export interface QueryJaiminiCharaDashaInput {
  /** ISO date (YYYY-MM-DD) to query the active dasha for. Defaults to today. */
  date?: string
  /**
   * If true, returns full_periods array with all 12 rashi periods and their
   * antar dasha breakdown. Default false (returns only the active period).
   */
  include_sub_periods?: boolean
}

// ── Sidecar call helper ───────────────────────────────────────────────────────

async function callSidecar(endpoint: string): Promise<unknown> {
  const baseUrl = process.env.PYTHON_SIDECAR_URL
  if (!baseUrl) {
    throw new Error('PYTHON_SIDECAR_URL env var not set — sidecar call will fail')
  }
  const url = `${baseUrl}${endpoint}`
  const res = await fetch(url, {
    method: 'GET',
    headers: {
      'x-api-key': SIDECAR_KEY,
    },
  })
  if (!res.ok) throw new Error(`Sidecar ${endpoint} returned HTTP ${res.status}`)
  return await res.json()
}

// ── Extraction helpers ────────────────────────────────────────────────────────

function extractActiveDasha(data: unknown): {
  active_rashi_dasha?: RashiPeriod
  active_antar_dasha?: RashiPeriod | null
  query_date?: string
} | null {
  if (!data || typeof data !== 'object') return null
  const d = data as Record<string, unknown>

  if (d['ok'] !== true) return null

  const activeRd = d['active_rashi_dasha'] as RashiPeriod | undefined
  const activeAd = d['active_antar_dasha'] as RashiPeriod | null | undefined

  if (!activeRd || !activeRd.rashi) return null

  return {
    active_rashi_dasha: activeRd,
    active_antar_dasha: activeAd ?? null,
    query_date: d['query_date'] as string | undefined,
  }
}

function extractFullPeriods(data: unknown): {
  full_periods?: RashiPeriod[]
  total_years?: number
} | null {
  if (!data || typeof data !== 'object') return null
  const d = data as Record<string, unknown>

  if (d['ok'] !== true) return null

  const periods = d['periods'] as RashiPeriod[] | undefined
  if (!Array.isArray(periods)) return null

  const totalYears = d['total_years'] as number | undefined

  return {
    full_periods: periods,
    total_years: totalYears ?? periods.reduce((sum, p) => sum + (p.years ?? 0), 0),
  }
}

// ── Core retrieval ────────────────────────────────────────────────────────────

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
      data_asset_id: 'FORENSIC',
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
  const input = (params ?? {}) as QueryJaiminiCharaDashaInput
  const queryDate = input.date
  const today = new Date().toISOString().slice(0, 10)

  const dateParam = queryDate ? `?date=${encodeURIComponent(queryDate)}` : ''

  let results: ToolBundleResult[]

  if (input.include_sub_periods) {
    // Fetch full 12-rashi timeline from sidecar
    const fullEndpoint = `/jaimini_drishti/chara_dasha/full${dateParam}`
    const fullData = await callSidecar(fullEndpoint)
    const fullResult = extractFullPeriods(fullData)

    // Also fetch active dasha
    const activeEndpoint = `/jaimini_drishti/chara_dasha${dateParam}`
    const activeData = await callSidecar(activeEndpoint)
    const activeResult = extractActiveDasha(activeData)

    if (!fullResult || !fullResult.full_periods) {
      results = [{
        content: JSON.stringify({
          ok: false,
          error: 'full_periods_not_found',
          message:
            'Sidecar response did not contain a "periods" array. ' +
            'Ensure the /jaimini_drishti/chara_dasha/full endpoint is wired.',
          query_date: queryDate ?? today,
        }),
        source_canonical_id: 'FORENSIC',
        source_version: '8.0',
        confidence: 0,
        significance: 0,
      }]
    } else {
      results = [{
        content: JSON.stringify({
          ok: true,
          query_date: queryDate ?? today,
          active_rashi_dasha: activeResult?.active_rashi_dasha ?? null,
          active_antar_dasha: activeResult?.active_antar_dasha ?? null,
          full_periods: fullResult.full_periods,
          total_years: fullResult.total_years,
          algorithm: 'jaimini_chara_dasha',
          epistemics: { surgical: true },
        }),
        source_canonical_id: 'FORENSIC',
        source_version: '8.0',
        confidence: 0.9,
        significance: 1.0,
      }]
    }
  } else {
    // Fetch only the active dasha
    const activeEndpoint = `/jaimini_drishti/chara_dasha${dateParam}`
    const activeData = await callSidecar(activeEndpoint)
    const activeResult = extractActiveDasha(activeData)

    if (!activeResult || !activeResult.active_rashi_dasha) {
      results = [{
        content: JSON.stringify({
          ok: false,
          error: 'active_dasha_not_found',
          message:
            'Sidecar response did not contain a valid active_rashi_dasha. ' +
            'Check that the /jaimini_drishti/chara_dasha endpoint is implemented.',
          query_date: queryDate ?? today,
        }),
        source_canonical_id: 'FORENSIC',
        source_version: '8.0',
        confidence: 0,
        significance: 0,
      }]
    } else {
      results = [{
        content: JSON.stringify({
          ok: true,
          query_date: activeResult.query_date ?? queryDate ?? today,
          active_rashi_dasha: activeResult.active_rashi_dasha,
          active_antar_dasha: activeResult.active_antar_dasha ?? null,
          algorithm: 'jaimini_chara_dasha',
          epistemics: { surgical: true },
        }),
        source_canonical_id: 'FORENSIC',
        source_version: '8.0',
        confidence: 0.9,
        significance: 1.0,
      }]
    }
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
    invocation_params: params ?? {},
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: (params ?? {}) as Record<string, unknown>,
    status: 'success',
    rows_returned: results.length,
    latency_ms: bundle.latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'FORENSIC',
    error_code: null,
    served_from_cache: false,
    fallback_used: false,
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Jaimini Chara Dasha timing lookup — calls Python sidecar ' +
    '/jaimini_drishti/chara_dasha (active period) and ' +
    '/jaimini_drishti/chara_dasha/full (full 12-rashi timeline). ' +
    'Default returns the active rashi maha dasha + antar dasha for today. ' +
    'With include_sub_periods=true returns all 12 rashi periods (120-year cycle). ' +
    'Use for Jaimini-tradition timing: "What is my Chara Dasha now?", ' +
    '"When does the Scorpio dasha begin?", "Show the full Jaimini dasha timeline." ' +
    'Prefer query_dasha_periods for Vimshottari Dasha.',
  retrieve,
}
