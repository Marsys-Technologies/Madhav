/**
 * pariprashna/corpus/dimensions/citation_recall.ts — lane P2-N (G3-F).
 *
 * Precision (sibling module) asks "of what was cited, how much was real?".
 * Recall asks the complementary question: "of what SHOULD have been cited,
 * how much was?" — which needs a ground-truth expected citation set, and
 * that only exists where a fixture author can honestly pre-declare one
 * (`CorpusFixture.expected.expectedSignalRefs`, fixtures.ts). Fixtures.ts
 * only sets this field where a specific SIG.* ref is the documented basis
 * for a correct answer (e.g. the cross-domain-contradiction fixture's
 * SIG.MSR.413) — never invented to make every fixture scorable. Reused
 * source: `receipt.facts_consumed` (G3-A, by-reference, never re-derived).
 */

import type { DimensionResult, TurnObservation } from '../types'

export const CITATION_RECALL_DIMENSION = 'citation_recall' as const

export function scoreCitationRecall(obs: TurnObservation): DimensionResult {
  const { receipt, fixture } = obs
  const expected = fixture.expected.expectedSignalRefs

  if (!expected || expected.length === 0) {
    return {
      dimension: CITATION_RECALL_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: `fixture '${fixture.fixtureId}' carries no expectedSignalRefs ground truth for recall scoring`,
      findings: [],
    }
  }

  if (!receipt) {
    return {
      dimension: CITATION_RECALL_DIMENSION,
      status: 'not_yet_measurable',
      score: null,
      reason: 'no AcharyaReadingReceipt was supplied for this observation',
      findings: [],
    }
  }

  const actualRefs = new Set(receipt.facts_consumed.map((f) => f.ref))
  const findings: string[] = []
  let hit = 0
  for (const ref of expected) {
    if (actualRefs.has(ref)) {
      hit += 1
    } else {
      findings.push(`expected ref ${ref} was not found in facts_consumed`)
    }
  }

  return {
    dimension: CITATION_RECALL_DIMENSION,
    status: 'scored',
    score: hit / expected.length,
    reason: null,
    findings,
  }
}
