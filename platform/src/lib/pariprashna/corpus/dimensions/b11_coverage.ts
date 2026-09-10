/**
 * pariprashna/corpus/dimensions/b11_coverage.ts — lane P2-N (G3-F).
 *
 * CLAUDE.md §I B.11: every interpretive query routes through L2 Bodha
 * synthesis first and surfaces cross-domain signals via the CDLM, before
 * producing its domain answer. Concretely, in receipt terms (G3-A, merged):
 * `coverage` (from the live floor + completeness receipt — did the turn
 * actually serve floor items, not just answer from thin air) and
 * `cross_domain` (did the plan authorize more than one domain — the CDLM
 * routing B.11 requires). Both fields reused as-is from the receipt, never
 * re-derived (§N.7 item 1).
 *
 * The RS-4 proportionality carve-out (CLAUDE.md §I) means a `factual`-class
 * fixture satisfies B.11 via the frame check + escalation valve rather than
 * full floor coverage — this scorer does not penalize a low `served` count
 * on its own; it penalizes `coverage`/`cross_domain` being `unavailable`
 * (i.e. the receipt itself could not demonstrate the discipline ran), which
 * is the actual failure mode B.11 exists to catch.
 */

import type { DimensionResult, TurnObservation } from '../types'

export const B11_COVERAGE_DIMENSION = 'b11_coverage' as const

export function scoreB11Coverage(obs: TurnObservation): DimensionResult {
  const { receipt } = obs
  if (!receipt) {
    return {
      dimension: B11_COVERAGE_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: 'no AcharyaReadingReceipt was supplied for this observation',
      findings: [],
    }
  }

  const findings: string[] = []
  let coverageComponent = 0
  let crossDomainComponent = 0

  if (receipt.coverage.status === 'measured') {
    const total = receipt.coverage.floor_item_total ?? 0
    const served = receipt.coverage.served ?? 0
    coverageComponent = total > 0 ? Math.min(1, served / total) : 1
  } else {
    findings.push(`coverage.status is 'unavailable' (${receipt.coverage.unavailable_reason ?? 'no reason recorded'})`)
  }

  if (receipt.cross_domain.status === 'measured') {
    const domainCount = receipt.cross_domain.domains?.length ?? 0
    crossDomainComponent = domainCount > 0 ? 1 : 0
    if (domainCount === 0) {
      findings.push('cross_domain.status is measured but domains is empty — no domain was authorized this turn')
    }
  } else {
    findings.push(
      `cross_domain.status is 'unavailable' (${receipt.cross_domain.unavailable_reason ?? 'no reason recorded'})`,
    )
  }

  const score = (coverageComponent + crossDomainComponent) / 2

  return { dimension: B11_COVERAGE_DIMENSION, status: 'scored', score, reason: null, findings }
}
