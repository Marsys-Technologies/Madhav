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
import { getFlag } from '@/lib/config'
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

// LL.3 R.LL3.2 — Pancha-Mahapurusha clique (M5-B 2026-05-13).
// These 6 signals form a single natal yoga configuration. When the cluster-modifier
// flag is ON, treat them as one consolidated entry (MAX weight) rather than 6
// additive entries to prevent 6× double-counting in synthesis.
// Note: SIG.MSR.402 is invalidated (wrong house attribution); SIG.MSR.402b is the
// corrected form. Both are included so the modifier fires regardless of DB state.
const PANCHA_MP_CLIQUE = new Set([
  'SIG.MSR.117', 'SIG.MSR.118', 'SIG.MSR.119',
  'SIG.MSR.143', 'SIG.MSR.145',
  'SIG.MSR.402', 'SIG.MSR.402b',  // 402 invalidated; 402b is the corrected form
])
const PANCHA_MP_CONSOLIDATED_ID = 'PANCHA_MP_CLIQUE_CONSOLIDATED'

// LL.1 production weights — inlined from
// 06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/signal_weights/production/ll1_weights_promoted_v1_0.json
// (30 signals, NAP.M4.5 approved 2026-05-02). Signals absent from this map default to 1.0.
// Includes both SIG.MSR.* signal_id matches and SIG.0N prior_id→signal_id resolutions.
const LL1_PRODUCTION_WEIGHTS = new Map<string, number>([
  ['SIG.MSR.001', 1.0],     // prior_id SIG.01
  ['SIG.MSR.009', 1.0],     // prior_id SIG.09
  ['SIG.MSR.010', 1.0],     // prior_id SIG.10
  ['SIG.MSR.012', 1.0],     // prior_id SIG.12
  ['SIG.MSR.013', 1.0],     // prior_id SIG.13 + direct
  ['SIG.MSR.015', 1.0],     // prior_id SIG.15
  ['SIG.MSR.030', 1.0],
  ['SIG.MSR.118', 0.4545],
  ['SIG.MSR.119', 0.4545],
  ['SIG.MSR.143', 0.4545],
  ['SIG.MSR.145', 0.9091],
  ['SIG.MSR.163', 1.0],
  ['SIG.MSR.170', 1.0],
  ['SIG.MSR.198', 1.0],
  ['SIG.MSR.229', 1.0],
  ['SIG.MSR.251', 1.0],
  ['SIG.MSR.278', 1.0],
  ['SIG.MSR.291', 1.0],
  ['SIG.MSR.295', 1.0],
  ['SIG.MSR.297', 1.0],
  ['SIG.MSR.300', 1.0],
  ['SIG.MSR.301', 1.0],
  ['SIG.MSR.391', 1.0],
  ['SIG.MSR.402', 0.7273],
  ['SIG.MSR.476', 1.0],
])

// LL.3 R.LL3.3 — Domains with zero LL.1 calibration weight at M5-B open.
// When retrieving these domains, signals are ranked by MSR-native confidence ×
// significance only (not LL.1 calibrated). Surface this as an explicit disclaimer
// rather than silently treating absence-of-weight as absence-of-signal.
// Source: ll1_weights_promoted_v1_0.json summary.zero_ll1_weight_domains (updated M5-B-S2).
const ZERO_LL1_WEIGHT_DOMAINS = new Set(['career', 'spiritual', 'psychological', 'financial', 'family'])

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

  // pg returns NUMERIC/DECIMAL columns as strings by default; coerce to number for schema validation
  let results: ToolBundleResult[] = rows.map(signal => ({
    content: signal.claim_text,
    source_canonical_id: 'MSR',
    source_version: signal.source_version,
    confidence: Number(signal.confidence),
    significance: Number(signal.significance),
    signal_id: signal.signal_id,
  }))

  // LL.1 calibration — re-rank by confidence × significance × ll1_weight (QG3.2 fix).
  // SQL returns ORDER BY (confidence × significance) DESC; apply LL.1 multiplier post-fetch.
  // Signals absent from the production register default to weight=1.0 (neutral).
  results = results.sort((a, b) => {
    const wA = a.signal_id != null ? (LL1_PRODUCTION_WEIGHTS.get(a.signal_id) ?? 1.0) : 1.0
    const wB = b.signal_id != null ? (LL1_PRODUCTION_WEIGHTS.get(b.signal_id) ?? 1.0) : 1.0
    return ((b.confidence ?? 0) * (b.significance ?? 0) * wB) -
           ((a.confidence ?? 0) * (a.significance ?? 0) * wA)
  })

  // LL.3 R.LL3.2 — Pancha-MP cluster-modifier (M5-B 2026-05-13).
  // When flag is ON and ≥2 Pancha-MP clique members appear in results, consolidate
  // them into a single entry with the MAX of their confidence × significance scores.
  // Prevents 6× additive double-counting of the same natal yoga structure.
  if (getFlag('LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED')) {
    const clique_members = results.filter(r => r.signal_id != null && PANCHA_MP_CLIQUE.has(r.signal_id))
    if (clique_members.length >= 2) {
      const non_clique = results.filter(r => r.signal_id == null || !PANCHA_MP_CLIQUE.has(r.signal_id))
      const max_confidence = Math.max(...clique_members.map(r => r.confidence ?? 0))
      const max_significance = Math.max(...clique_members.map(r => r.significance ?? 0))
      const consolidated: ToolBundleResult = {
        content: `[PANCHA_MP_CLUSTER] Pancha-Mahapurusha yoga configuration: ${clique_members.map(r => r.signal_id).join(', ')}. ` +
          `Consolidated per LL.3 R.LL3.2 cluster-modifier (prevents ${clique_members.length}× double-counting). ` +
          `Representative signal: ${clique_members[0]?.content ?? ''}`,
        source_canonical_id: 'MSR',
        source_version: clique_members[0]?.source_version,
        confidence: max_confidence,
        significance: max_significance,
        signal_id: PANCHA_MP_CONSOLIDATED_ID,
      }
      results = [...non_clique, consolidated]
    }
  }

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.signal_id ?? r.content.slice(0, 50)).sort()))
      .digest('hex')

  const latency_ms = Date.now() - start

  // LL.3 R.LL3.3 — Zero-LL.1-weight domain disclaimer (M5-B 2026-05-13).
  // When querying domains with no LL.1 calibration weight, annotate the bundle so
  // that the synthesis layer does not treat absence-of-weight as absence-of-signal.
  // Signals are ranked by MSR-native confidence × significance, not LL.1 calibrated.
  const zero_ll1_domains_in_query = getFlag('LL3_ZERO_WEIGHT_DOMAIN_DISCLAIMER_ENABLED')
    ? plan.domains.filter(d => ZERO_LL1_WEIGHT_DOMAINS.has(d))
    : []
  const ll3_r_ll3_3_disclaimer = zero_ll1_domains_in_query.length > 0
    ? `LL.3 R.LL3.3: domain(s) [${zero_ll1_domains_in_query.join(', ')}] have zero LL.1 calibration weight at M5-B-S2. ` +
      `Signals are ranked by MSR-native confidence × significance only (not LL.1 calibrated). ` +
      `Treat results as pre-calibration; n=0 LL.1 signal does NOT mean no relevant signals exist.`
    : null

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
      ...(ll3_r_ll3_3_disclaimer ? { ll3_zero_weight_disclaimer: ll3_r_ll3_3_disclaimer } : {}),
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
