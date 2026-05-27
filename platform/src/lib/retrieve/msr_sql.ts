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

// Unit 3.dejudge (2026-05-28): query-time judgment removed.
// The 0.6 / 0.35 confidence floors, the Pancha-MP clique consolidation, the LL.1
// production weight re-rank, and the LL.3 zero-weight-domain disclaimer have all
// been stripped from this tool. Ranking and salience are now properties of the
// L2.5 computed coefficient (deterministic_strength, verification_certainty,
// computed_salience — columns added in 2a.1) plus the serve-time panel. Callers
// may still pass an explicit `params.confidence_floor` to opt back into a hard
// cut, but the default is no floor (return everything the SQL filters match).

// No-judgment default: SQL filter `confidence >= 0` is a no-op.
const NO_FLOOR = 0

const DEFAULT_LIMIT = 100

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
  LIMIT $10
`.trim()

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  try {
    return await retrieveImpl(plan, params, start)
  } catch (err) {
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: { domains: params?.domain ?? plan.domains, planets: plan.planets ?? [], forward_looking: params?.forward_looking ?? plan.forward_looking },
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

  // Unit 3.dejudge: no default floor. If a caller explicitly passes
  // `params.confidence_floor` we still honour it (caller intent wins), but the
  // default is 0 — every signal that matches the structural SQL filters reaches
  // the consumer. Salience ranking now lives in the L2.5 computed coefficient
  // (deterministic_strength, verification_certainty, computed_salience) and in
  // the serve-time panel, not in this tool.
  const explicitFloor = params?.confidence_floor as number | undefined
  const confidenceFloor = explicitFloor !== undefined ? explicitFloor : NO_FLOOR

  // F.2 fix: add params fallbacks for fields that were previously read from
  // plan.* only, which silently ignored MCP surgical-primitive params.
  // Priority: params.* wins over plan.* (caller intent > plan derivation).
  const paramsDomain = params?.domain as string | string[] | undefined
  const paramsDomains: string[] = paramsDomain
    ? (Array.isArray(paramsDomain) ? paramsDomain : [paramsDomain])
    : []
  const effectiveDomains = paramsDomains.length > 0 ? paramsDomains : plan.domains

  const paramsLimit = params?.limit as number | undefined

  // Build nullable array params — pass null when the filter is unused so that
  // the SQL `IS NULL OR ... ANY(...)` clause becomes a no-op.
  const domainFilter: string[] | null = effectiveDomains.length > 0 ? effectiveDomains : null
  const planetFilter: string[] | null =
    plan.planets && plan.planets.length > 0 ? plan.planets : null
  // FIX-2: read forward_looking from params first, fall back to plan.
  // When params.forward_looking === true: filter to forward-looking signals only.
  // When params.forward_looking === false: no filter (pass null → SQL IS NULL no-op).
  // When params.forward_looking is absent: fall back to plan.forward_looking (preserves
  // existing behaviour for non-primitive callers).
  const rawForwardLooking = (params as Record<string, unknown>)?.forward_looking
  const forwardLookingFilter: boolean | null =
    rawForwardLooking === true ? true :
    rawForwardLooking === false ? null :
    plan.forward_looking ? true : null

  // New signal-property filters (from MsrSqlInput; all optional, backward-compatible)
  const msrInput = params as MsrSqlInput | undefined

  // Normalize temporal_activation: accepts scalar string OR string[] (UDA-Q-S6 backport).
  const rawTemporal = msrInput?.temporal_activation
  const temporalArr: string[] = rawTemporal == null
    ? []
    : Array.isArray(rawTemporal) ? rawTemporal : [rawTemporal]
  const signalTypeFilter: string[] | null =
    msrInput?.signal_type && msrInput.signal_type.length > 0 ? msrInput.signal_type : null
  const temporalFilter: string[] | null = temporalArr.length > 0 ? temporalArr : null

  // Normalize valence: accepts scalar string OR string[] (UDA-Q-S6 backport).
  const rawValence = msrInput?.valence
  const valenceArr: string[] = rawValence == null
    ? []
    : Array.isArray(rawValence) ? rawValence : [rawValence]
  const valenceFilter: string[] | null = valenceArr.length > 0 ? valenceArr : null

  // dasha_lord (UDA-Q-S6): single-value convenience scalar merged into dasha_activation.
  const dashaLordExtra: string[] = msrInput?.dasha_lord ? [msrInput.dasha_lord] : []
  const dashaEntities: string[] = [...(msrInput?.dasha_activation ?? []), ...dashaLordExtra].map(
    lord => `DSH.MD.${lord.toUpperCase()}`
  )
  const rawEntities = [
    ...(msrInput?.entities_involved_any ?? []),
    ...dashaEntities,
  ]
  const entitiesFilter: string[] | null = rawEntities.length > 0 ? rawEntities : null

  const queryLimit = (paramsLimit && paramsLimit > 0) ? paramsLimit : DEFAULT_LIMIT

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
    queryLimit,
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
      queryLimit,
    ])
    rows = fallback.rows
    fallback_used = true
  }

  // pg returns NUMERIC/DECIMAL columns as strings by default; coerce to number for schema validation.
  //
  // Unit 3.dejudge (2026-05-28): post-fetch LL.1 weight re-rank and the LL.3
  // Pancha-MP clique consolidation are removed. SQL `ORDER BY (confidence ×
  // significance) DESC` is the only ranking the tool applies — and even that
  // is structural, not judgmental. Salience now belongs to the L2.5 computed
  // coefficient (deterministic_strength × verification_certainty × computed_salience)
  // and the serve-time panel, not query-time post-processing.
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

  // Unit 3.dejudge (2026-05-28): the LL.3 zero-LL.1-weight-domain disclaimer is
  // removed alongside the LL.1 calibration itself. No domain partition is
  // privileged by this tool any more.

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      native_id: nativeId,
      domains: effectiveDomains,
      planets: plan.planets ?? [],
      forward_looking: forwardLookingFilter,  // FIX-7: actual SQL filter value, not plan.forward_looking
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
