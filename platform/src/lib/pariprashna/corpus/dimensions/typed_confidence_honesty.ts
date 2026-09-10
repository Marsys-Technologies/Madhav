/**
 * pariprashna/corpus/dimensions/typed_confidence_honesty.ts — lane P2-N
 * (G3-F).
 *
 * §N.8 stub: no real detector exists for this dimension in this worktree's
 * base. G3-C (PPR-03, roadmap Gate 3) is the lane that puts a five-type
 * confidence enum on every claim and forbids `empirically_calibrated` below
 * an activation gate — it is not merged here. `receipt.calibration_disclosure`
 * (G3-A, merged) is a related but distinct signal: it reports whether an L5
 * calibration-bearing TOOL was consulted this turn, not whether every CLAIM
 * in the served prose carries a correctly-typed confidence tag. Conflating
 * the two would misrepresent what G3-A actually checks — see
 * `calibration_language_honesty.ts` for the dimension that legitimately uses
 * `calibration_disclosure`.
 *
 * Always returns `not_yet_measurable`, regardless of input.
 */

import type { DimensionResult, TurnObservation } from '../types'

export const TYPED_CONFIDENCE_HONESTY_DIMENSION = 'typed_confidence_honesty' as const

// The param is kept (unused) so this matches the DimensionScorer signature every other dimension implements.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function scoreTypedConfidenceHonesty(_obs: TurnObservation): DimensionResult {
  return {
    dimension: TYPED_CONFIDENCE_HONESTY_DIMENSION,
    status: 'not_yet_measurable',
    score: null,
    reason:
      "requires G3-C (typed five-type confidence enum on every claim, empirically_calibrated " +
      "gate) — not yet merged into this lane's base",
    findings: [],
  }
}
