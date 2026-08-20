/**
 * pariprashna/corpus/dimensions/falsifier_quality.ts — lane P2-N (G3-F).
 *
 * §N.8 stub: no real detector exists for this dimension in this worktree's
 * base. G3-B (PPR-02, roadmap Gate 3) is the lane that produces
 * `interpretation_sets` with a `falsifier` field per significant judgment —
 * it is not merged here. Scoring "falsifier quality" without that structured
 * output would mean either re-deriving it from raw prose with an LLM-judge
 * call (a real but non-deterministic detector this lane was not asked to
 * build) or fabricating a plausible-looking number — both rejected per
 * CLAUDE.md §N.8: "a signal without such a detector is null, not green."
 *
 * The function ALWAYS returns `not_yet_measurable`, regardless of input —
 * this is the honest interface, not a partial implementation. Once G3-B
 * lands, replace this body with a real check against
 * `receipt.interpretation_sets[].falsifier` (field name provisional, per
 * G3-B's own eventual schema).
 */

import type { DimensionResult, TurnObservation } from '../types'

export const FALSIFIER_QUALITY_DIMENSION = 'falsifier_quality' as const

// The param is kept (unused) so this matches the DimensionScorer signature every other dimension implements.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function scoreFalsifierQuality(_obs: TurnObservation): DimensionResult {
  return {
    dimension: FALSIFIER_QUALITY_DIMENSION,
    status: 'not_yet_measurable',
    score: null,
    reason:
      'requires G3-B (interpretation_sets with a falsifier field per significant judgment) — ' +
      'not yet merged into this lane\'s base',
    findings: [],
  }
}
