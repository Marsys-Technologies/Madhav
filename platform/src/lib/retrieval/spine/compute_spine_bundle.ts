/**
 * compute_spine_bundle.ts — the "spine bundle" join (W5 Lane L5).
 * ===================================================================
 *
 * WHAT A "SPINE BUNDLE" IS (investigation, not invention — see the three cited docs):
 *
 * RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §8 item 11 (into R-4 Adaptive Serving):
 *   "Spine bundles as first-class capabilities on all profiles: pre-joined
 *    `signal → activation windows → phala anchors → calibration` chains per
 *    domain/scope (census finding: only one real cross-layer join exists today
 *    [bodha_msr_signals ↔ kala_activation]; the LLM hand-stitches everything else)."
 * RETRIEVAL_STRATEGY_v1_0.md §S-5 / §5.1 repeats the identical chain and names it
 *   "the single biggest productivity upgrade available: it converts the LLM's most
 *    expensive stitching work into one call" and "the flattening that IS needed is
 *    horizontal, not vertical" (i.e. this is a cross-layer join, NOT a re-layering).
 *
 * This is a DIFFERENT concept from two other same-named things already in this
 * codebase (confirmed by grep before writing a line of this file):
 *   - "grounding spine" (D3, platform/src/lib/retrieval/grounding/*.ts) — the
 *     chart-scoped L1 chart_facts numeric-metric resolver. Unrelated homonym.
 *   - "bundle" in platform/src/lib/bundle/* (bundle_hydrator.ts, compose_bundle) —
 *     the Paripraśna manifest ASSET-CONTENT bundle (markdown/doc assets loaded for
 *     LLM context). Also unrelated — that "bundle" holds static content, not a
 *     cross-layer data join.
 * A "spine bundle" is neither of those: it is the per-(chart, ayanamsha, domain)
 * pre-joined chain named above.
 *
 * IMPLEMENTATION CHOICE: this function is a COMPOSITION of the four existing,
 * independently-tested layer capabilities (query_signals / query_temporal_activation /
 * query_predictive_anchors / query_calibration) rather than a fifth, parallel set of
 * hand-written SQL. This keeps the spine bundle byte-consistent with what a caller
 * would see calling those four tools directly today (no second, divergent
 * implementation of e.g. the window-family collapse or posterior_provenance logic),
 * and means a fix to any one layer's query automatically flows through here.
 *
 * DETERMINISM CONTRACT: computeSpineBundle's return value carries NO wall-clock or
 * request-scoped field (no computed_at, no request_id) — it is a pure function of
 * the underlying tables' current rows for the given (chart_id, ayanamsha_id, domain,
 * top_k). Two calls against identical underlying data produce byte-identical
 * JSON.stringify output. This is what makes the materialized-vs-fresh byte-consistency
 * guarantee possible (see materialize.ts + its tests) — the materialized row is
 * exactly this function's output, persisted, never re-derived differently.
 */

import { querySignalsCapability } from '../registry/layers/L2_bodha/query_signals'
import { queryTemporalActivationCapability } from '../registry/layers/L3_kala/query_temporal_activation'
import { queryPredictiveAnchorsCapability } from '../registry/layers/L4_phala/query_predictive_anchors'
import { queryCalibrationCapability } from '../registry/layers/L5_mimamsa/query_calibration'
import { DEFAULT_AYANAMSHA } from '../registry/constants'
import { DEFAULT_SPINE_TOP_K, MAX_SPINE_TOP_K } from './constants'
import type { SpineBundleContent, SpineSignalEntry } from './types'
import type { CapabilityContext } from '../registry/types'

export interface ComputeSpineBundleArgs {
  chart_id: string
  ayanamsha_id?: string
  domain: string
  top_k?: number
}

/** Wide, effectively-unbounded date range — a spine bundle is a reference join, not
 *  a date-windowed query; date filtering (as_of/date_from/date_to) is the caller's
 *  job on query_temporal_activation directly if they need it. */
const WIDE_DATE_FROM = '1900-01-01'
const WIDE_DATE_TO = '2100-01-01'

export async function computeSpineBundle(
  args: ComputeSpineBundleArgs,
  ctx?: CapabilityContext,
): Promise<SpineBundleContent> {
  const chart_id = args.chart_id
  const ayanamsha_id = args.ayanamsha_id ?? DEFAULT_AYANAMSHA
  const domain = args.domain
  const top_k = Math.min(Math.max(1, args.top_k ?? DEFAULT_SPINE_TOP_K), MAX_SPINE_TOP_K)

  if (!chart_id) throw new Error('computeSpineBundle: chart_id is required')
  if (!domain) throw new Error('computeSpineBundle: domain is required')

  // ── 1. Signals (root of the chain) ────────────────────────────────────────
  const signalsResult = await querySignalsCapability.handler(
    { chart_id, ayanamsha_id, domain, top_k },
    ctx,
  )
  if (signalsResult.is_error) {
    throw new Error(`computeSpineBundle: query_signals failed: ${JSON.stringify(signalsResult.content)}`)
  }
  const signalRows = ((signalsResult.content as Record<string, unknown>)['signals'] ?? []) as Array<Record<string, unknown>>
  const signalIds = signalRows.map(r => String(r['signal_id'])).filter(Boolean)

  // ── 2. Activation windows for exactly those signals ───────────────────────
  let activationRows: Array<Record<string, unknown>> = []
  if (signalIds.length > 0) {
    const activationResult = await queryTemporalActivationCapability.handler(
      {
        chart_id, ayanamsha_id, signal_ids: signalIds,
        date_from: WIDE_DATE_FROM, date_to: WIDE_DATE_TO,
        top_k: MAX_SPINE_TOP_K * 10,
      },
      ctx,
    )
    if (activationResult.is_error) {
      throw new Error(`computeSpineBundle: query_temporal_activation failed: ${JSON.stringify(activationResult.content)}`)
    }
    activationRows = ((activationResult.content as Record<string, unknown>)['activations'] ?? []) as Array<Record<string, unknown>>
  }

  // ── 3. Phala anchors for this domain, grouped by signal_id ────────────────
  const anchorsResult = await queryPredictiveAnchorsCapability.handler(
    { chart_id, domain, top_k: 150 },
    ctx,
  )
  if (anchorsResult.is_error) {
    throw new Error(`computeSpineBundle: query_predictive_anchors failed: ${JSON.stringify(anchorsResult.content)}`)
  }
  const anchorRows = ((anchorsResult.content as Record<string, unknown>)['anchors'] ?? []) as Array<Record<string, unknown>>

  // ── 4. Calibration (chart-level verdicts/reliability + domain-filtered multipliers) ──
  const calibrationResult = await queryCalibrationCapability.handler(
    { chart_id, include_held_out: false, promoted_only: false },
    ctx,
  )
  if (calibrationResult.is_error) {
    throw new Error(`computeSpineBundle: query_calibration failed: ${JSON.stringify(calibrationResult.content)}`)
  }
  const calContent = calibrationResult.content as Record<string, unknown>
  const allMultipliers = (calContent['multipliers'] ?? []) as Array<Record<string, unknown>>
  const domainMultipliers = allMultipliers.filter(m => m['domain'] === domain)

  // ── Assemble per-signal entries ────────────────────────────────────────────
  const activationsBySignal = new Map<string, Array<Record<string, unknown>>>()
  for (const row of activationRows) {
    const sid = String(row['signal_id'] ?? '')
    if (!sid) continue
    if (!activationsBySignal.has(sid)) activationsBySignal.set(sid, [])
    activationsBySignal.get(sid)!.push(row)
  }
  const anchorsBySignal = new Map<string, Array<Record<string, unknown>>>()
  for (const row of anchorRows) {
    const sid = row['signal_id'] ? String(row['signal_id']) : null
    if (!sid) continue
    if (!anchorsBySignal.has(sid)) anchorsBySignal.set(sid, [])
    anchorsBySignal.get(sid)!.push(row)
  }

  const signals: SpineSignalEntry[] = signalRows.map(row => {
    const sid = String(row['signal_id'])
    return {
      signal_id: sid,
      signal_headline_text: (row['signal_headline_text'] as string | null) ?? null,
      signal_summary_text: (row['signal_summary_text'] as string | null) ?? null,
      computed_salience: (row['computed_salience'] as number | null) ?? null,
      domains_affected_array: (row['domains_affected_array'] as string[] | null) ?? null,
      valence: (row['valence'] as string | null) ?? null,
      activation_windows: activationsBySignal.get(sid) ?? [],
      phala_anchors: anchorsBySignal.get(sid) ?? [],
    }
  })

  const empty_reason = signals.length === 0
    ? `No signals found for chart ${chart_id} at ayanamsha '${ayanamsha_id}' in domain '${domain}'. ` +
      'The spine bundle chain has no root to join from — activation/anchor/calibration sections ' +
      'are correspondingly empty, not independently queried.'
    : null

  return {
    chart_id,
    ayanamsha_id,
    domain,
    top_k,
    signal_count: signals.length,
    signals,
    calibration: {
      verdict_distribution: (calContent['verdict_distribution'] ?? []) as Array<Record<string, unknown>>,
      reliability: (calContent['reliability_curve'] ?? []) as Array<Record<string, unknown>>,
      multipliers: domainMultipliers,
      qa_fail_count: Number((calContent['qa_summary'] as Record<string, unknown> | undefined)?.['fail_count'] ?? 0),
    },
    empty_reason,
    provenance: {
      tables: ['bodha_msr_signals', 'kala_activation', 'phala_anchors', 'mimamsa_calibration', 'mimamsa_reliability', 'mimamsa_multipliers'],
      composed_from_capabilities: [
        querySignalsCapability.uri,
        queryTemporalActivationCapability.uri,
        queryPredictiveAnchorsCapability.uri,
        queryCalibrationCapability.uri,
      ],
    },
  }
}
