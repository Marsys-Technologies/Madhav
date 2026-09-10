/**
 * pariprashna/corpus/dimensions/reader_comprehension.ts — lane P2-N (G3-F).
 *
 * §N.8 stub, the paradigm case: whether a reader actually understood a
 * served reading has no deterministic detector — it needs either an
 * LLM-judge call (a real detector, but not a deterministic one, and not one
 * this lane was scoped to wire up) or a human rating pipeline (not built).
 * Inventing a plausible-looking readability heuristic (sentence length,
 * flesch score, etc.) would be scoring something OTHER than what this
 * dimension name claims — a proxy standing in for the real signal, which is
 * exactly the SATYA-DĪPA defect class CLAUDE.md §N.8 names.
 *
 * Always returns `not_yet_measurable`, regardless of input.
 */

import type { DimensionResult, TurnObservation } from '../types'

export const READER_COMPREHENSION_DIMENSION = 'reader_comprehension' as const

// The param is kept (unused) so this matches the DimensionScorer signature every other dimension implements.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export function scoreReaderComprehension(_obs: TurnObservation): DimensionResult {
  return {
    dimension: READER_COMPREHENSION_DIMENSION,
    status: 'not_yet_measurable',
    score: null,
    reason: 'requires an LLM-judge call or human rating pipeline — no deterministic detector exists for reader comprehension',
    findings: [],
  }
}
