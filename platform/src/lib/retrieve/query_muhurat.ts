/**
 * MARSYS-JIS Retrieval tool — query_muhurat (COV-S4)
 *
 * Surfaces auspicious muhurat windows for a given event and date range,
 * calling the Python sidecar POST /api/compute/muhurat endpoint backed by
 * the panchang_engine muhurat finder.
 *
 * Supported events: vivah, griha_pravesh, vyapara, yatra,
 *                   property_purchase, mantra_initiation.
 *
 * When chart_id is supplied, the engine overlays Tara Bala and Chandra Bala
 * corrections against the native's natal Moon nakshatra.
 *
 * Date range cap: 90 days. top_n capped at 90 by the sidecar.
 */

import crypto from 'crypto'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_muhurat'
const TOOL_VERSION = '1.0.0'
const SIDECAR_KEY = process.env.PYTHON_SIDECAR_API_KEY ?? ''

export interface QueryMuhuratInput {
  /** One of: vivah, griha_pravesh, vyapara, yatra, property_purchase, mantra_initiation */
  event: string
  /** Range start YYYY-MM-DD */
  date_from: string
  /** Range end YYYY-MM-DD (max 90 days from date_from) */
  date_to: string
  /** Observer latitude */
  lat?: number
  /** Observer longitude */
  lon?: number
  /** UTC offset in minutes (default 330 = IST) */
  tz_offset_minutes?: number
  /** Optional chart_id for Tara Bala / Chandra Bala native overlay */
  chart_id?: string
  /** Number of top windows to return (default 10, max 90) */
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
  const input = (params ?? {}) as unknown as QueryMuhuratInput

  const requestBody = {
    event: input.event ?? 'vivah',
    date_from: input.date_from,
    date_to: input.date_to,
    lat: input.lat ?? 20.27,
    lon: input.lon ?? 85.84,
    tz_offset_minutes: input.tz_offset_minutes ?? 330,
    ...(input.chart_id ? { chart_id: input.chart_id } : {}),
    top_n: input.top_n ?? 10,
  }

  const data = await callSidecar('/api/compute/muhurat', requestBody)
  const dataObj = data as { ok?: boolean; windows?: unknown[]; count?: number; event?: string; supported_events?: string[] }

  const results: ToolBundleResult[] = [{
    content: JSON.stringify(data),
    source_canonical_id: 'PANCHANGA_DAILY',
    source_version: '1.0',
    confidence: dataObj.ok ? 1.0 : 0.5,
    significance: 0.85,
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
    'Auspicious muhurat window finder — calls panchang_engine via sidecar POST /api/compute/muhurat. ' +
    'Supports 6 MVP events: vivah (marriage), griha_pravesh (house warming), vyapara (business start), ' +
    'yatra (travel), property_purchase, mantra_initiation. ' +
    'Returns top_n windows ranked by composite score (tithi, vara, nakshatra, yoga, karana, hora). ' +
    'Optional chart_id enables Tara Bala + Chandra Bala native overlay. ' +
    'Date range max 90 days. Default location: Bhubaneswar (20.27°N, 85.84°E, IST).',
  retrieve,
}
