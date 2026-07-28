/**
 * SAMĪKṢĀ lifecycle → card eyebrow label — PB-3 lane L-2.
 *
 * Design authority: PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md §6.9.
 *
 * §6.9: the prediction card's eyebrow reads `TIME-INDEXED READING` + a lifecycle
 * suffix: `· WINDOW OPEN` → `· WINDOW CLOSING` → `· AWAITING OUTCOME` →
 * `· RESOLVED — CONFIRMED / MISSED / MIXED`. The eyebrow is the ONLY element
 * that changes after settle (an in-place text swap at fixed geometry, P1).
 *
 * Isomorphic (pure) so the card and any server surface derive the exact same
 * label from a (lifecycle_status, outcome) pair. `WINDOW CLOSING` is NOT a
 * lifecycle state — it is a derived near-window-end signal the caller passes in.
 */

import type { LifecycleState, Outcome } from './schema'

export const EYEBROW_PREFIX = 'TIME-INDEXED READING' as const

/** Outcome → the resolved-suffix word (§6.9 CONFIRMED / MISSED / MIXED). */
function resolvedWord(outcome: Outcome | null): string {
  switch (outcome) {
    case 'happened':
      return 'CONFIRMED'
    case 'did_not_happen':
      return 'MISSED'
    case 'partial':
      return 'MIXED'
    case 'unverifiable':
      return 'UNVERIFIABLE'
    default:
      return 'RESOLVED'
  }
}

/**
 * The eyebrow suffix (without the `TIME-INDEXED READING` prefix). `closingSoon`
 * (window within its final stretch while still open) turns `WINDOW OPEN` into
 * `WINDOW CLOSING` — the one derived, non-lifecycle state §6.9 names.
 */
export function lifecycleSuffix(
  status: LifecycleState,
  opts: { outcome?: Outcome | null; closingSoon?: boolean } = {},
): string {
  switch (status) {
    case 'detected':
      return 'AWAITING CONFIRMATION'
    case 'confirmed':
    case 'open':
      return opts.closingSoon ? 'WINDOW CLOSING' : 'WINDOW OPEN'
    case 'window_closed':
      return 'AWAITING OUTCOME'
    case 'outcome_recorded':
      return `RESOLVED — ${resolvedWord(opts.outcome ?? null)}`
    case 'unverifiable':
      return 'RESOLVED — UNVERIFIABLE'
    case 'dismissed':
      return 'DISMISSED'
    case 'lapsed':
      return 'LAPSED'
    case 'lapsed_unconfirmed':
      return 'LAPSED — UNCONFIRMED'
    default:
      return 'WINDOW OPEN'
  }
}

/** Full eyebrow text: `TIME-INDEXED READING · <suffix>`. */
export function lifecycleEyebrow(
  status: LifecycleState,
  opts: { outcome?: Outcome | null; closingSoon?: boolean } = {},
): string {
  return `${EYEBROW_PREFIX} · ${lifecycleSuffix(status, opts)}`
}
