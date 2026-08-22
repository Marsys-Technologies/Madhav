/**
 * F-176 (PARISESA-V4) — shared PACT promise-gate for kala_windows_get / kala_projections_get
 * ============================================================================================
 *
 * ## The defect (verification-first finding, confirmed live on the canonical chart)
 *
 * `kala_windows_get` and `kala_projections_get` are the two RAW low-level L3 primitives that
 * `kala_ahead_get` (F-110) already wraps and gates. `grep -n "promise\|pact"` over both
 * underlying capability files (`query_temporal_activation.ts`, `query_projections.ts`) returns
 * ZERO hits — neither consults `pact_query`. Live verification against the canonical chart
 * (`482012f1-710e-4a25-994a-93821f5871aa`) confirmed `kala_projections_get(domain:'relationship')`
 * serves 2 `tier_1_high` projections with NO `promise_gate` key, while `pact_query` on the SAME
 * chart/domain independently returns `pact_status: 'denied_at_promise'` — the exact F-110
 * "confidence laundering" defect, one layer down, on the tool an LLM caller is just as likely to
 * reach directly.
 *
 * `kala_windows_get`'s exposure is narrower: its `forward_windows` fallback (only reachable when
 * `query_temporal_activation`'s primary `kala_activation` query returns zero rows) reads the SAME
 * ungated `kala_bhavishya` rows. Live testing across the canonical chart's entire
 * `kala_bhavishya`-overlapping window (2027-10-20..2030-04-03, several date ranges) found dated
 * `kala_activation` rows densely cover that whole span for this chart/domain, so the fallback
 * never actually fired — LATENT, not exercised, for this specific chart/domain/date-range
 * combination. The code path is still real (it fires whenever `kala_activation` is un-dated or
 * unbuilt for a chart — the `awaiting_activation_dates` / `total === 0` branches in
 * `query_temporal_activation.ts`) and is gated here too, defensively, using the SAME shared
 * function — no second implementation to drift from this one (§N.5).
 *
 * ## The fix
 *
 * This module is a byte-for-byte extraction of `ahead.ts`'s own F-110 `computePromiseGate` (see
 * `00_ARCHITECTURE/briefs/parisesa/F110_PACT_GATING_DESIGN_CONTRACT_v1_0.md`) — the ONE
 * extraction `PARISESA_V4_FIX_PLAN.md`'s F-176 section authorizes. The only change from the
 * original is that the capability-calling function is now an injected parameter
 * (`CapabilityCaller`) instead of a module-local `fetch` wrapper, so each call site (`ahead.ts`,
 * `register_p1_aliases.ts`) can supply its own already-existing proxy helper without this module
 * picking a side in either file's own infra-duplication convention. `ahead.ts` passes its own
 * local `callRegistryCapability` unchanged, so its behavior is byte-identical pre/post extraction
 * (see `kala_ahead_get_f110_promise_gate.test.ts`, which mocks at the `fetch` layer and therefore
 * exercises this exact code path unmodified).
 *
 * Disciplines preserved verbatim (do not violate on pain of re-opening F-110/F-176):
 *   - exactly ONE `pact_query` call per response;
 *   - tier / narrative / `max_effective_score` pass through byte-identical, never re-graded
 *     (§N.5 / §N.7 — this module never touches a served projection/window row, only ADDS a
 *     sibling `promise_gate` field);
 *   - `state: 'unreachable'` is reported explicitly, never smoothed into `'not_applicable'` or a
 *     clean bill of health (§N.8).
 */

import { interpretPactJoin, type SaraPromiseJoin } from '../../lib/promise_spine.js'
import type { Principal } from '../../types.js'

/** The L-PACT capability URI. Identical to the one `kala_ahead_get` / assess_* gate on. */
export const PACT_CAPABILITY_URI = 'marsys://tool/L-PACT/pact_query'

/** Which forward span a denial at this PACT stage may legitimately gate. */
export type PromiseGateScope = 'horizon_invariant' | 'as_of_date_only' | 'none'

export type PromiseGateState = 'checked' | 'unreachable' | 'not_applicable'

export interface PromiseGate {
  state: PromiseGateState
  /** The domain whose PACT chain was consulted (null when none was). */
  domain: string | null
  as_of_date: string | null
  /** `interpretPactJoin` output, verbatim. NEVER fabricated — null unless state==='checked' (§N.8). */
  join: SaraPromiseJoin | null
  /** Raw `pact_status`, verbatim from the capability. */
  pact_status: string | null
  gating_scope: PromiseGateScope
  /**
   * True ONLY when a horizon-invariant denial actually contradicts a served projection/window.
   * This is the field a caller reads to know the served tier is disputed by this server.
   */
  contradicts_served_projections: boolean
  /** §N.6: "vetted" and "not vetted" are never flattened into one undifferentiated claim. */
  gated_projection_domains: string[]
  ungated_projection_domains: string[]
  reason: string
}

/**
 * Minimal shape this module needs from a served row (a `kala_bhavishya` projection family, or a
 * `forward_windows` row) — deliberately narrower than any one call site's own richer type
 * (ahead.ts's `ProjectionFamily`, `query_projections.ts`'s raw row) so every call site's own type
 * is structurally assignable here without a shared import or a coupling between files.
 */
export interface PromiseGateProjection {
  domain: string | null
  [key: string]: unknown
}

/**
 * The shape every call site's own capability-calling helper already returns
 * (`ahead.ts`'s local `callRegistryCapability`, and the `register_p1_aliases.ts` adapter) — NEVER
 * throws; a failure is reported as `{content: null, ok: false}`, never an exception, so a PACT
 * outage cannot take down the whole response (§N.8: unreachable is a value, not a crash).
 */
export type CapabilityCaller = (
  uri: string,
  args: Record<string, unknown>,
  principal: Principal,
) => Promise<{ content: Record<string, unknown> | null; ok: boolean }>

/** §4.2 stage-scope table. A denial's validity across a forward horizon depends on
 *  whether the stage that denied rests on timeless (natal/varga) or as-of-date facts. */
export function gatingScopeFor(pactStatus: string | null): PromiseGateScope {
  if (!pactStatus) return 'none'
  if (pactStatus === 'denied_at_promise' || pactStatus === 'denied_at_confirmation') return 'horizon_invariant'
  if (pactStatus === 'denied_at_activation') return 'as_of_date_only'
  return 'none'
}

/** Calls the SAME `pact_query` capability `kala_explain_get` / `kala_ahead_get` consume — no
 *  second chain implementation, no new astrological computation (§N.5/B.10) — and interprets it
 *  through the shared `interpretPactJoin` helper (promise_spine.ts), whose `denied_at_* →
 *  stance:'contradicts'` mapping has no override path (INV-1). */
export async function computePromiseGate(
  chartId: string,
  ayanamshaId: string,
  asOfDate: string,
  requestedDomain: string | undefined,
  projectionFamilies: PromiseGateProjection[],
  principal: Principal,
  callCapability: CapabilityCaller,
): Promise<PromiseGate> {
  const projectionDomains = Array.from(
    new Set(projectionFamilies.map((p) => p.domain).filter((d): d is string => typeof d === 'string' && d.length > 0)),
  )
  // Scope: the caller's explicit domain, else the LEADING projection's own domain (the
  // one this tool's thesis names). §5.3: pact_query runs judgment_query's full checklist
  // and is expensive — one call per response, never N parallel heavy calls.
  const gateDomain = requestedDomain ?? projectionDomains[0] ?? null

  const emptyGate = (state: PromiseGateState, reason: string): PromiseGate => ({
    state, domain: gateDomain, as_of_date: gateDomain ? asOfDate : null, join: null, pact_status: null,
    gating_scope: 'none', contradicts_served_projections: false,
    gated_projection_domains: [], ungated_projection_domains: projectionDomains, reason,
  })

  if (!gateDomain) {
    return emptyGate(
      'not_applicable',
      'No domain to consult: neither a `domain` filter was supplied nor did any served projection carry a domain label, ' +
        'so there is no PACT chain for this response to be gated against. Not a clean bill of health — nothing was checked.',
    )
  }

  const resp = await callCapability(
    PACT_CAPABILITY_URI,
    { chart_id: chartId, ayanamsha_id: ayanamshaId, domain: gateDomain, as_of_date: asOfDate },
    principal,
  )
  // §N.8: a null join is reported as null, never smoothed into a permissive default.
  const join = resp.ok ? interpretPactJoin(resp.content) : null
  if (!join) {
    return emptyGate(
      'unreachable',
      `The PACT promise chain for '${gateDomain}' could not be evaluated this call ` +
        `(${resp.ok ? 'the capability answered but returned no pact_status' : 'the L-PACT capability was unreachable'}). ` +
        'The served probability_tier(s) below have therefore NOT been checked against the classical promise chain — ' +
        'unchecked, which is not the same as checked-and-clear. Re-run kala_explain_get or pact_query for this domain.',
    )
  }

  const pactStatus = ((resp.content as Record<string, unknown> | null)?.['pact_status']
    ?? ((resp.content as Record<string, unknown> | null)?.['content'] as Record<string, unknown> | undefined)?.['pact_status']
    ?? null) as string | null
  const scope = gatingScopeFor(pactStatus)
  const gatedDomains = [gateDomain]
  const ungated = projectionDomains.filter((d) => d !== gateDomain)
  // A projection is contradicted only if the denial is horizon-invariant AND a served
  // projection actually sits in the gated domain.
  const contradicts =
    join.stance === 'contradicts' &&
    scope === 'horizon_invariant' &&
    projectionFamilies.some((p) => p.domain === gateDomain)

  const reason = contradicts
    ? `${join.promise_verdict} This denial rests on natal/varga facts that do not change with the evaluation date, ` +
      `so it bears on EVERY forward window served here for '${gateDomain}' — the probability_tier below is a measure of ` +
      'temporal SIGNAL CONVERGENCE (how many activation signals point at the same window), not of classical promise, and ' +
      'the two disagree on this chart. Both are served; neither is silently dropped. Drill: kala_explain_get / pact_query.'
    : join.stance === 'contradicts' && scope === 'as_of_date_only'
      ? `${join.promise_verdict} NOTE: an ACTIVATION-stage denial is evaluated as of ${asOfDate} only and says nothing ` +
        'about a window years later — it is reported here for completeness but is NOT applied as a gate on these forward ' +
        'projections (design contract §4.2).'
      : join.promise_verdict

  return {
    state: 'checked', domain: gateDomain, as_of_date: asOfDate, join, pact_status: pactStatus,
    gating_scope: scope, contradicts_served_projections: contradicts,
    gated_projection_domains: gatedDomains, ungated_projection_domains: ungated, reason,
  }
}
