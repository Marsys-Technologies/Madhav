/**
 * MARSYS-JIS Retrieval tool — query_v7_additions (COV-S4)
 *
 * Wrapper for the Python sidecar POST /v7_additions endpoint.
 * Status: sidecar endpoint stub (returns not_implemented). This wrapper
 * surfaces the tool in RETRIEVAL_TOOLS and the planner manifest so the
 * v7 additions capability slot is reserved in the capability registry.
 * Implement sidecar logic in python-sidecar/routers/v7_additions.py when
 * the v7 additions scope is defined (M6+ scope).
 *
 * v7_additions: reserved for compute capabilities added in v7 of the
 * panchang / ephemeris engine — exact scope TBD per M6 planning.
 */

import crypto from 'crypto'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_v7_additions'
const TOOL_VERSION = '1.0.0'
const SIDECAR_KEY = process.env.PYTHON_SIDECAR_API_KEY ?? ''

export interface QueryV7AdditionsInput {
  /** Arbitrary params forwarded to the sidecar (schema TBD at implementation) */
  params?: Record<string, unknown>
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
  const input = (params ?? {}) as QueryV7AdditionsInput
  const requestBody = { params: input.params ?? {} }

  const data = await callSidecar('/v7_additions', requestBody)

  const results: ToolBundleResult[] = [{
    content: JSON.stringify(data),
    source_canonical_id: 'FORENSIC',
    source_version: '1.0',
    confidence: 0.5,
    significance: 0.6,
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
    'v7 additions capability surface — sidecar POST /v7_additions. ' +
    'Reserved capability slot for compute features added in engine v7. ' +
    'Exact scope defined at M6 planning. Currently a stub returning not_implemented. ' +
    'Use this tool when a query explicitly targets v7 engine capabilities ' +
    'not covered by existing panchanga, ephemeris, muhurat, or transit tools.',
  retrieve,
}
