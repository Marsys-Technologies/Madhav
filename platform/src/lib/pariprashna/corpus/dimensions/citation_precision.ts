/**
 * pariprashna/corpus/dimensions/citation_precision.ts — lane P2-N (G3-F).
 *
 * Grounded in G2-B's live citation rewriter, surfaced on the receipt as
 * `evidence_grades` (G3-A, merged): the turn's own grade-tier tally
 * (`primary`/`supporting`/`contextual`/`unverified`/`prior_reading`).
 *
 * IMPORTANT — `grade_counts.unverified` and `hallucination_count` are the
 * SAME event, not disjoint sets: `citations/rewriter.ts`'s `resolveSentinel`
 * has exactly one branch for an unresolvable reference, and that branch both
 * assigns `grade: 'unverified'` AND calls `this.counter.increment(...)` in
 * the same block (rewriter.ts:263-278) — confirmed live 2026-08-28 against
 * the deployed web door (S3 corpus run, 10/10 measured turns had
 * `hallucination_count === grade_counts.unverified` exactly). An earlier
 * version of this scorer treated `unverified` as "resolved" (numerator) and
 * separately added `hallucination_count` to the denominator, double-counting
 * every unresolvable citation and forcing the score toward ~0.5 regardless
 * of true quality — masking a true 0.0 (zero citations ever reached a
 * trustworthy grade) as a falsely reassuring 0.5. Fixed: only
 * `primary`/`supporting`/`contextual`/`prior_reading` count as resolved-to-
 * something-real; `unverified` is the hallucination bucket and belongs only
 * in the denominator. `hallucination_count` itself is no longer read here —
 * it is redundant with `grade_counts.unverified` by the rewriter's own
 * construction, not an independent signal.
 *
 * `evidence_grades` is `unavailable` exactly when the live rewriter didn't
 * run this turn (regex fallback carries no per-citation grade tier), per
 * schema.ts's own comment — this scorer reports that as `not_yet_measurable`,
 * not a fabricated 0 or 1.
 */

import type { DimensionResult, TurnObservation } from '../types'

export const CITATION_PRECISION_DIMENSION = 'citation_precision' as const

export function scoreCitationPrecision(obs: TurnObservation): DimensionResult {
  const { receipt } = obs
  if (!receipt) {
    return {
      dimension: CITATION_PRECISION_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: 'no AcharyaReadingReceipt was supplied for this observation',
      findings: [],
    }
  }

  const grades = receipt.evidence_grades
  if (grades.status !== 'measured' || !grades.grade_counts || grades.hallucination_count === null) {
    return {
      dimension: CITATION_PRECISION_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: grades.unavailable_reason ?? 'evidence_grades is unavailable for this turn',
      findings: [],
    }
  }

  const { primary, supporting, contextual, unverified, prior_reading } = grades.grade_counts
  const resolved = primary + supporting + contextual + prior_reading
  const total = resolved + unverified
  const findings: string[] = []
  if (unverified > 0) {
    findings.push(`${unverified} citation(s) never resolved to a trustworthy source (grade 'unverified')`)
  }

  if (total === 0) {
    // No citation attempts at all this turn — vacuously precise (nothing to be wrong about).
    return { dimension: CITATION_PRECISION_DIMENSION, status: 'scored', score: 1, reason: null, findings: [] }
  }

  return {
    dimension: CITATION_PRECISION_DIMENSION,
    status: 'scored',
    score: resolved / total,
    reason: null,
    findings,
  }
}
