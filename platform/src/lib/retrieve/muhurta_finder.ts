/**
 * MARSYS-JIS Retrieval tool — muhurta_finder (UDA-1-S8)
 *
 * Finds top auspicious muhurta windows for a given activity type over a date
 * range (max 30 days). This is a richer variant of query_muhurat: it enforces
 * the 30-day cap (vs 90 in query_muhurat), defaults the native chart overlay
 * (Tara Bala + Chandra Bala applied automatically), and uses
 * activity_type naming (MCP convention) mapped to the sidecar's event field.
 *
 * Calls the Python sidecar's POST /api/compute/muhurat endpoint (same as
 * query_muhurat). Returns scored time windows with auspicious factors breakdown
 * (tara_bala, chandra_bala, yoga, tithi, vara).
 *
 * Supported activity types: vivah, griha_pravesh, vyapara, yatra,
 *                           property_purchase, mantra_initiation.
 *
 * Native chart ID (Abhisek Mohanty): 362f9f17-95a5-490b-a5a7-027d3e0efda0
 */

import crypto from 'crypto'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'muhurta_finder'
const TOOL_VERSION = '1.0.0'
const SIDECAR_KEY = process.env.PYTHON_SIDECAR_API_KEY ?? ''

/** Native chart UUID — Abhisek Mohanty's canonical chart. */
const NATIVE_CHART_ID = '362f9f17-95a5-490b-a5a7-027d3e0efda0'

/** Supported MVP activity types (mirror of Python sidecar EVENTS_MVP). */
const ACTIVITY_TYPES = [
  'vivah',
  'griha_pravesh',
  'vyapara',
  'yatra',
  'property_purchase',
  'mantra_initiation',
] as const

type ActivityType = (typeof ACTIVITY_TYPES)[number]

export interface MuhurtaFinderInput {
  /** ISO start date (YYYY-MM-DD) for the search window (inclusive). */
  date_from: string
  /** ISO end date (YYYY-MM-DD) for the search window (inclusive). Max 30 days from date_from. */
  date_to: string
  /** Activity type: vivah, griha_pravesh, vyapara, yatra, property_purchase, mantra_initiation. */
  activity_type: ActivityType
  /**
   * Native chart UUID for Tara Bala + Chandra Bala overlay.
   * Defaults to the native chart (362f9f17-95a5-490b-a5a7-027d3e0efda0) when not provided.
   */
  chart_id?: string
  /** Number of top windows to return (default 10, max 30). */
  top_n?: number
}

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
  const input = (params ?? {}) as unknown as MuhurtaFinderInput

  const dateFrom = input.date_from
  const dateTo   = input.date_to
  const activityType = input.activity_type ?? 'vivah'
  const chartId  = input.chart_id ?? NATIVE_CHART_ID
  const topN     = Math.min(Math.max(Number(input.top_n ?? 10), 1), 30)

  // Validate date ordering.
  if (dateFrom > dateTo) {
    throw new Error(`muhurta_finder: date_to must be >= date_from (got ${dateFrom} → ${dateTo})`)
  }

  // Enforce 30-day cap.
  const fromMs = new Date(dateFrom).getTime()
  const toMs   = new Date(dateTo).getTime()
  const diffDays = Math.floor((toMs - fromMs) / (1000 * 60 * 60 * 24))
  if (diffDays > 30) {
    throw new Error(
      `muhurta_finder: date range ${diffDays} days exceeds 30-day maximum. Split into smaller windows.`
    )
  }

  const requestBody = {
    event:     activityType,
    date_from: dateFrom,
    date_to:   dateTo,
    lat:       20.27,
    lon:       85.84,
    tz_offset_minutes: 330,
    chart_id:  chartId,
    top_n:     topN,
  }

  const data = await callSidecar('/api/compute/muhurat', requestBody)
  const dataObj = data as {
    ok?: boolean
    windows?: unknown[]
    count?: number
    event?: string
  }

  const results: ToolBundleResult[] = [{
    content: JSON.stringify(data),
    source_canonical_id: 'PANCHANGA_DAILY',
    source_version: '1.0',
    confidence: dataObj.ok ? 1.0 : 0.5,
    significance: 0.90,
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
    invocation_params: requestBody,
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: requestBody as Record<string, unknown>,
    status: 'success',
    rows_returned: dataObj.windows?.length ?? 0,
    latency_ms: bundle.latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'PANCHANGA_DAILY',
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
    'Auspicious muhurta window finder (native overlay) — finds top scored muhurta windows for a given ' +
    'activity type over a date range (max 30 days). Calls Python sidecar POST /api/compute/muhurat. ' +
    'Native chart overlay (Tara Bala + Chandra Bala) applied automatically. ' +
    'Supported activity types: vivah, griha_pravesh, vyapara, yatra, property_purchase, mantra_initiation. ' +
    'Returns windows ranked by composite score (tithi, vara, nakshatra, yoga, karana, hora, tara_bala, chandra_bala). ' +
    'Richer than query_muhurat: 30-day cap enforced; native chart defaulted. ' +
    'Prefer query_panchanga for single-day snapshots.',
  retrieve,
}
