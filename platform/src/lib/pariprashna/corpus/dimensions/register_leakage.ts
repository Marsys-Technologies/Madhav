/**
 * pariprashna/corpus/dimensions/register_leakage.ts — lane P2-N (G3-F).
 *
 * Reuses P2-E's existing `RegisterLintTotals` (`observability/
 * turn_metrics.ts`, `TurnMetricsSnapshot.register_lint`) directly — per this
 * lane's own brief, this dimension must reuse the existing lint counters,
 * never re-derive a leak count independently. `fires` counts every delta
 * where `citations/register_leak_lint.ts` actually rewrote or redacted an
 * internal identifier before it reached the reader; `delta_calls` is the
 * total number of deltas linted. A fire is a real near-miss the backstop had
 * to intervene on — even though the backstop is designed to catch it (so no
 * fire ever reaches the reader), a high fire rate signals the UPSTREAM
 * evidence context is leaking internal ids into model text more than it
 * should, which is exactly what this dimension exists to surface.
 */

import type { DimensionResult, TurnObservation } from '../types'

export const REGISTER_LEAKAGE_DIMENSION = 'register_leakage' as const

export function scoreRegisterLeakage(obs: TurnObservation): DimensionResult {
  const { turnMetrics } = obs
  if (!turnMetrics) {
    return {
      dimension: REGISTER_LEAKAGE_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: 'no TurnMetricsSnapshot was supplied for this observation',
      findings: [],
    }
  }

  const { delta_calls, fires, leaks_total } = turnMetrics.register_lint
  if (delta_calls === 0) {
    // No text was linted at all this turn — vacuously clean.
    return { dimension: REGISTER_LEAKAGE_DIMENSION, status: 'scored', score: 1, reason: null, findings: [] }
  }

  const fireRate = fires / delta_calls
  const findings: string[] = []
  if (fires > 0) {
    findings.push(
      `register-leak lint fired ${fires}/${delta_calls} delta(s), redacting ${leaks_total} leaked token(s) total`,
    )
  }

  return {
    dimension: REGISTER_LEAKAGE_DIMENSION,
    status: 'scored',
    score: Math.max(0, 1 - fireRate),
    reason: null,
    findings,
  }
}
