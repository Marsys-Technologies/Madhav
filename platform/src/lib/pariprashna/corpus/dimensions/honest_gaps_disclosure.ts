/**
 * pariprashna/corpus/dimensions/honest_gaps_disclosure.ts — lane P2-N (G3-F).
 *
 * Grounded in G3-A's `honest_gaps` (merged, PR #1363), itself sourced from
 * `WebCompletenessReceipt.empty` + `.dark` (`vidhi/completeness_receipt.ts`'s
 * own itemized, per-item honesty invariant). This dimension checks internal
 * COHERENCE between two fields the SAME receipt carries — `honest_gaps.gaps`
 * and `coverage.empty`/`coverage.dark` — rather than re-deriving either from
 * scratch. Both are built from the same `WebCompletenessReceipt` in
 * `assemble.ts` (`buildCoverage` and `buildHonestGaps` both take the
 * identical `completenessReceipt` argument), so a genuine implementation
 * gap-hiding bug would show up as exactly this kind of mismatch: coverage
 * reports N empty+dark items but honest_gaps enumerates fewer than N.
 */

import type { DimensionResult, TurnObservation } from '../types'

export const HONEST_GAPS_DISCLOSURE_DIMENSION = 'honest_gaps_disclosure' as const

export function scoreHonestGapsDisclosure(obs: TurnObservation): DimensionResult {
  const { receipt } = obs
  if (!receipt) {
    return {
      dimension: HONEST_GAPS_DISCLOSURE_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: 'no AcharyaReadingReceipt was supplied for this observation',
      findings: [],
    }
  }

  const { coverage, honest_gaps } = receipt
  const findings: string[] = []

  if (coverage.status !== 'measured') {
    // Coherent: both unavailable together is honest (no coverage data to hide gaps against).
    if (honest_gaps.status === 'measured') {
      findings.push('coverage is unavailable but honest_gaps is measured — inconsistent receipt state')
      return { dimension: HONEST_GAPS_DISCLOSURE_DIMENSION, status: 'scored', score: 0.5, reason: null, findings }
    }
    return {
      dimension: HONEST_GAPS_DISCLOSURE_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: 'coverage is unavailable for this turn — no gap coherence check possible',
      findings: [],
    }
  }

  if (honest_gaps.status !== 'measured' || !honest_gaps.gaps) {
    findings.push(
      `coverage is measured (empty=${coverage.empty}, dark=${coverage.dark}) but honest_gaps.status is ` +
        `'${honest_gaps.status}' — gaps not disclosed`,
    )
    return { dimension: HONEST_GAPS_DISCLOSURE_DIMENSION, status: 'scored', score: 0, reason: null, findings }
  }

  const expectedGapCount = (coverage.empty ?? 0) + (coverage.dark ?? 0)
  const actualGapCount = honest_gaps.gaps.length

  if (expectedGapCount === actualGapCount) {
    return { dimension: HONEST_GAPS_DISCLOSURE_DIMENSION, status: 'scored', score: 1, reason: null, findings: [] }
  }

  findings.push(
    `coverage reports ${expectedGapCount} empty+dark item(s) but honest_gaps.gaps enumerates ${actualGapCount}`,
  )
  const score = expectedGapCount === 0 ? 0 : Math.max(0, 1 - Math.abs(expectedGapCount - actualGapCount) / expectedGapCount)
  return { dimension: HONEST_GAPS_DISCLOSURE_DIMENSION, status: 'scored', score, reason: null, findings }
}
