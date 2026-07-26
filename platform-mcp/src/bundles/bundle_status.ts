/**
 * bundle_status.ts — ŚODHANA T2 (MC-002): bundle-health computation.
 *
 * A composite bundle fans out to N sub-tools with per-sub-tool error isolation.
 * Before this helper, both bundle envelopes hard-coded `ok: true` regardless of
 * how many sub-tools errored — so `bodha_bundle_get` could (and did, live) return
 * `ok: true` while 5 of 8 constituents had errored. A caller reading the top-level
 * `ok` had no honest signal that the read was a hollow shell.
 *
 * This helper makes the top-level health a pure function of the errored/total
 * ratio, and makes it STRUCTURALLY IMPOSSIBLE to return `ok: true` / `status: 'ok'`
 * when a majority of constituents errored:
 *
 *   errored == 0            → status 'ok',       ok true
 *   0 < errored/total < 0.5 → status 'partial',  ok true   (minority failed)
 *   errored/total >= 0.5    → status 'degraded',  ok false  (majority failed)
 *   total == 0              → status 'degraded',  ok false  (nothing ran; not a read)
 *
 * Threshold: the 0.5 cut is deliberate — a bundle whose majority of constituents
 * failed is not a partially-degraded read, it is a failed read wearing a 200.
 * `ok` is DERIVED from `status` (ok === status !== 'degraded'), never set
 * independently, so the two can never disagree (GA.1-class stored-vs-derived guard
 * applied at the envelope boundary).
 */

export type BundleStatus = 'ok' | 'partial' | 'degraded'

export interface BundleHealth {
  status: BundleStatus
  ok: boolean
}

/** Fraction of errored sub-tools at/above which the whole bundle is 'degraded'. */
export const DEGRADED_ERROR_RATIO = 0.5

export function computeBundleHealth(erroredCount: number, totalCount: number): BundleHealth {
  if (totalCount <= 0) return { status: 'degraded', ok: false }
  if (erroredCount <= 0) return { status: 'ok', ok: true }
  const ratio = erroredCount / totalCount
  const status: BundleStatus = ratio >= DEGRADED_ERROR_RATIO ? 'degraded' : 'partial'
  return { status, ok: status !== 'degraded' }
}
