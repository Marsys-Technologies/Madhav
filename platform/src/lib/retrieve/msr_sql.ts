/**
 * MARSYS-JIS Stream C — Tool C.1: msr_sql
 *
 * Retrieves MSR signals from Cloud SQL `msr_signals` table, filtered by the
 * incoming QueryPlan. Returns a validated ToolBundle.
 */

import crypto from 'crypto'
import type { MsrSignal } from '@/lib/db/types'
import { getStorageClient } from '@/lib/storage'
import { validate } from '@/lib/schemas'
import { telemetry } from '@/lib/telemetry'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool, MsrSqlInput } from './types'

const TOOL_NAME = 'msr_sql'
const TOOL_VERSION = '1.0.0'
const DEFAULT_NATIVE_ID = 'abhisek_mohanty'
const DEFAULT_CONFIDENCE_FLOOR = 0.6
// Finance/wealth signals often cluster in the 0.35–0.60 range and are useful
// for synthesis; the global 0.6 floor over-filters them. Apply a lower default
// so medium-confidence finance signals reach the synthesizer.
const FINANCE_WEALTH_CONFIDENCE_FLOOR = 0.35
const FINANCE_WEALTH_DOMAINS = new Set(['finance', 'wealth'])

const SQL = `
  SELECT * FROM msr_signals
  WHERE native_id = $1
    AND ($2::varchar[] IS NULL OR domain = ANY($2::varchar[]))
    AND ($3::varchar[] IS NULL OR planet = ANY($3::varchar[]))
    AND ($4::boolean IS NULL OR is_forward_looking = $4)
    AND confidence >= $5
    AND ($6::text[] IS NULL OR signal_type = ANY($6::text[]))
    AND ($7::text[] IS NULL OR temporal_activation = ANY($7::text[]))
    AND ($8::text[] IS NULL OR valence = ANY($8::text[]))
    AND ($9::text[] IS NULL OR entities_involved ?| $9::text[])
  ORDER BY (confidence * significance) DESC
  LIMIT 100
`.trim()

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  try {
    return await retrieveImpl(plan, params, start)
  } catch (err) {
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: { domains: plan.domains, planets: plan.planets ?? [], forward_looking: plan.forward_looking },
      status: 'error',
      rows_returned: 0,
      latency_ms: Date.now() - start,
      token_estimate: 0,
      data_asset_id: 'MSR_v3_0',
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
  const nativeId = (params?.native_id as string | undefined) ?? DEFAULT_NATIVE_ID

  // If an explicit confidence_floor is provided by the caller, honour it.
  // Otherwise, apply domain-specific defaults: finance/wealth use a lower floor
  // (0.35) so medium-confidence signals in that range are not filtered out.
  const explicitFloor = params?.confidence_floor as number | undefined
  const isFinanceWealthQuery = plan.domains.some(d => FINANCE_WEALTH_DOMAINS.has(d))
  const confidenceFloor =
    explicitFloor !== undefined
      ? explicitFloor
      : isFinanceWealthQuery
        ? FINANCE_WEALTH_CONFIDENCE_FLOOR
        : DEFAULT_CONFIDENCE_FLOOR

  // Build nullable array params — pass null when the filter is unused so that
  // the SQL `IS NULL OR ... ANY(...)` clause becomes a no-op.
  const domainFilter: string[] | null = plan.domains.length > 0 ? plan.domains : null
  const planetFilter: string[] | null =
    plan.planets && plan.planets.length > 0 ? plan.planets : null
  const forwardLookingFilter: boolean | null = plan.forward_looking ? true : null

  // New signal-property filters (from MsrSqlInput; all optional, backward-compatible)
  const msrInput = params as MsrSqlInput | undefined
  const signalTypeFilter: string[] | null =
    msrInput?.signal_type && msrInput.signal_type.length > 0 ? msrInput.signal_type : null
  const temporalFilter: string[] | null =
    msrInput?.temporal_activation && msrInput.temporal_activation.length > 0
      ? msrInput.temporal_activation
      : null
  const valenceFilter: string[] | null =
    msrInput?.valence && msrInput.valence.length > 0 ? msrInput.valence : null
  const dashaEntities: string[] = (msrInput?.dasha_activation ?? []).map(
    lord => `DSH.MD.${lord.toUpperCase()}`
  )
  const rawEntities = [
    ...(msrInput?.entities_involved_any ?? []),
    ...dashaEntities,
  ]
  const entitiesFilter: string[] | null = rawEntities.length > 0 ? rawEntities : null

  let { rows } = await getStorageClient().query<MsrSignal>(SQL, [
    nativeId,
    domainFilter,
    planetFilter,
    forwardLookingFilter,
    confidenceFloor,
    signalTypeFilter,
    temporalFilter,
    valenceFilter,
    entitiesFilter,
  ])

  // UQE-7 (W2-BUGS B2W-2/3) — domain-only fallback. When a planet filter
  // narrowed the result to zero, retry without the planet filter so the
  // synthesizer still has domain-relevant signals to ground in.
  let fallback_used = false
  if (rows.length === 0 && planetFilter !== null) {
    const fallback = await getStorageClient().query<MsrSignal>(SQL, [
      nativeId,
      domainFilter,
      null,
      forwardLookingFilter,
      confidenceFloor,
      signalTypeFilter,
      temporalFilter,
      valenceFilter,
      entitiesFilter,
    ])
    rows = fallback.rows
    fallback_used = true
  }

  // pg returns NUMERIC/DECIMAL columns as strings by default; coerce to number for schema validation
  const results: ToolBundleResult[] = rows.map(signal => ({
    content: signal.claim_text,
    source_canonical_id: 'MSR',
    source_version: signal.source_version,
    confidence: Number(signal.confidence),
    significance: Number(signal.significance),
    signal_id: signal.signal_id,
  }))

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.signal_id ?? r.content.slice(0, 50)).sort()))
      .digest('hex')

  const latency_ms = Date.now() - start

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      native_id: nativeId,
      domains: plan.domains,
      planets: plan.planets ?? [],
      forward_looking: plan.forward_looking,
      confidence_floor: confidenceFloor,
      signal_type: signalTypeFilter,
      temporal_activation: temporalFilter,
      valence: valenceFilter,
      entities_involved_any: entitiesFilter,
      fallback_used,
    },
    results,
    served_from_cache: false,
    latency_ms,
    result_hash,
    schema_version: '1.0',
  }

  const validation = validate('tool_bundle', bundle)
  if (!validation.valid) {
    throw new Error(
      `msr_sql produced invalid ToolBundle: ${JSON.stringify(validation.errors)}`
    )
  }

  telemetry.recordLatency(TOOL_NAME, 'retrieve', latency_ms)

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: bundle.invocation_params as Record<string, unknown>,
    status: rows.length === 0 ? 'zero_rows' : 'ok',
    rows_returned: rows.length,
    latency_ms,
    token_estimate: Math.ceil(JSON.stringify(rows).length / 4),
    data_asset_id: 'MSR_v3_0',
    error_code: null,
    served_from_cache: false,
    fallback_used,
    raw_result_count: rows.length,
    kept_result_count: results.length,
    dropped_items: [],
    kept_items: results.slice(0, 200).map(r => ({
      item_id: r.signal_id ?? r.source_canonical_id,
      score: r.confidence ?? null,
      contribution_tokens: null,
    })),
    tool_input_payload: bundle.invocation_params,
    error_class: 'OK',
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  retrieve,
}
