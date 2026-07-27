/**
 * bundle_status.ts — ŚODHANA T2 (MC-002): bundle-health computation (platform copy).
 *
 * Mirror of platform-mcp/src/bundles/bundle_status.ts. Kept as a small, pure,
 * duplicated helper rather than a cross-package import because the platform
 * (Next.js) app and the platform-mcp server are separate build roots. Any change
 * to the thresholds MUST be applied to both copies.
 *
 * Makes it structurally impossible for a bundle envelope to report `ok: true` /
 * `status: 'ok'` when a majority of its sub-tools errored:
 *
 *   errored == 0            → 'ok'       ok true
 *   0 < errored/total < 0.5 → 'partial'  ok true
 *   errored/total >= 0.5    → 'degraded' ok false
 *   total == 0              → 'degraded' ok false
 *
 * `ok` is DERIVED from `status` (ok === status !== 'degraded'); the two can never
 * disagree.
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
