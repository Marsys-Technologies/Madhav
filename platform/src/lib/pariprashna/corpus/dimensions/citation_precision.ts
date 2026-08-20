/**
 * pariprashna/corpus/dimensions/citation_precision.ts — lane P2-N (G3-F).
 *
 * Grounded in G2-B's live citation rewriter, surfaced on the receipt as
 * `evidence_grades` (G3-A, merged): the turn's own grade-tier tally
 * (`primary`/`supporting`/`contextual`/`unverified`/`prior_reading`, i.e.
 * citations the rewriter actually RESOLVED against a real signal) alongside
 * `hallucination_count` (sentinels the model emitted that never resolved —
 * `TurnCitationStream.hallucinationCount`, `citations/stream_wiring.ts`).
 * Precision = resolved / (resolved + hallucinated): what fraction of the
 * turn's citation attempts pointed at something real. `evidence_grades` is
 * `unavailable` exactly when the live rewriter didn't run this turn (regex
 * fallback carries no per-citation grade tier), per schema.ts's own comment —
 * this scorer reports that as `not_yet_measurable`, not a fabricated 0 or 1.
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

  const resolved = Object.values(grades.grade_counts).reduce((sum, n) => sum + n, 0)
  const total = resolved + grades.hallucination_count
  const findings: string[] = []
  if (grades.hallucination_count > 0) {
    findings.push(`${grades.hallucination_count} citation sentinel(s) never resolved (hallucination_count > 0)`)
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
