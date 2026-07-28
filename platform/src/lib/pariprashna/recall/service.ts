import 'server-only'
/**
 * recall/service.ts — PB-2 (SMṚTI) lane M-4. Orchestrator: DAL fetch + rank.
 *
 * `recallPriorConclusions` is the one call a synthesis-prompt assembler needs:
 * given a chart + query embedding, return the top-N prior conclusions from
 * OTHER threads of the SAME chart, ranked by similarity + freshness. Callers
 * turn the result into citations via `toPriorReadingCitations` (`./citation`)
 * — never any other grade.
 */
import { fetchCrossThreadCandidates } from './query'
import { rankRecallCandidates } from './rank'
import type { RankOptions, RecallQueryInput, RecallResult } from './types'

export async function recallPriorConclusions(
  input: RecallQueryInput,
  rankOpts: RankOptions = {},
): Promise<RecallResult[]> {
  const candidates = await fetchCrossThreadCandidates(input)
  return rankRecallCandidates(candidates, rankOpts)
}
