/**
 * pariprashna/citations/grounding_summary.ts — G2-B "Citations at first
 * paint" (PPR-08, FD-2/FD-6).
 *
 * Builds the SERVER half of the honest grounding-summary contract: citation
 * counts + a grade rollup, computed from what the S-3 rewriter actually
 * resolved this turn (`stream_wiring.ts`'s `ResolvedTurnCitation[]` — never
 * re-derived from prose), and a completeness line read straight off the
 * turn's own floor/completeness receipt (`pipeline/completeness_wiring.ts`'s
 * `WebCompletenessReceipt` — the SAME object `receipt_stage.ts`'s
 * `emitCompletenessReceipt` reports as the `completeness` grade; this module
 * does not recompute coverage, it restates the one number that already
 * exists).
 *
 * The wire shape this builds is `ServerGroundingSummarySchema`
 * (`protocol/events.ts`) — imported here rather than redeclared, so the two
 * can never drift (§N.7 item 3: no wrapper-local constant may shadow a
 * canonical source).
 */

import type { CitationGrade } from './types'
import type { ResolvedTurnCitation } from './stream_wiring'
import type { ServerGroundingSummary, GroundingSummaryGradeCounts } from '../protocol/events'
import type { WebCompletenessReceipt } from '../../pipeline/completeness_wiring'

const CITATION_GRADES: readonly CitationGrade[] = [
  'primary',
  'supporting',
  'contextual',
  'unverified',
  'prior_reading',
]

function emptyGradeCounts(): GroundingSummaryGradeCounts {
  return { primary: 0, supporting: 0, contextual: 0, unverified: 0, prior_reading: 0 }
}

export interface BuildGroundingSummaryArgs {
  resolvedCitations: readonly ResolvedTurnCitation[]
  /** From `TurnCitationStream.hallucinationCount` — sentinels that never resolved. */
  hallucinationCount: number
  completenessReceipt: WebCompletenessReceipt | null
}

/**
 * Pure. Every number here traces to an input the caller already computed
 * elsewhere (the rewriter's own resolution ledger, the turn's own
 * completeness receipt) — this function only tallies and restates, it never
 * re-derives a grade or a coverage fraction (§N.7 item 1).
 */
export function buildGroundingSummary(args: BuildGroundingSummaryArgs): ServerGroundingSummary {
  const grade_counts = emptyGradeCounts()
  for (const c of args.resolvedCitations) {
    if (CITATION_GRADES.includes(c.grade)) grade_counts[c.grade] += 1
  }
  const coverage = args.completenessReceipt?.coverage ?? null
  return {
    citation_count: args.resolvedCitations.length,
    hallucination_count: args.hallucinationCount,
    grade_counts,
    completeness: coverage ? { served: coverage.served, floor_item_total: coverage.floor_item_total } : null,
    completeness_line: coverage ? `${coverage.served}/${coverage.floor_item_total} floor items served` : null,
  }
}
