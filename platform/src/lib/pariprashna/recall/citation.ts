/**
 * recall/citation.ts — PB-2 (SMṚTI) lane M-4.
 *
 * Maps a ranked cross-thread recall result onto a `ResolvedCitation` graded
 * `prior_reading` (the new, deliberately-weakest grade added in
 * `../citations/types.ts`). This is the ONLY place a recalled conclusion may
 * be surfaced to the synthesis prompt as a citation — every citation this
 * module produces carries `grade: 'prior_reading'` unconditionally, so a
 * recalled conclusion can never masquerade as `primary`/`supporting`/
 * `contextual` evidence.
 *
 * `audit_detail` intentionally carries the recall provenance (conversation +
 * message id, similarity, freshness) — audit-channel only, same discipline
 * `protocol_adapter.ts` already applies to every other citation kind (never
 * forwarded to the client wire's inline prose).
 */
import type { ResolvedCitation } from '../citations/types'
import type { RecallResult } from './types'

const PRIOR_READING_GRADE = 'prior_reading' as const

/** ISO-8601 date-only label for the reader-facing citation (no clock time). */
function dateLabel(isoTimestamp: string): string {
  return new Date(isoTimestamp).toISOString().slice(0, 10)
}

/** One recall result → one `prior_reading`-graded citation. */
export function toPriorReadingCitation(result: RecallResult): ResolvedCitation {
  return {
    ref: `prior_reading:${result.message_id}`,
    reader_label: `Earlier reading (${dateLabel(result.created_at)})`,
    grade: PRIOR_READING_GRADE,
    audit_detail:
      `recalled cross-thread conclusion — conversation_id=${result.conversation_id} ` +
      `message_id=${result.message_id} similarity=${result.similarity.toFixed(3)} ` +
      `freshness=${result.freshness.toFixed(3)} (${result.freshness_source})`,
  }
}

/** Batch form, order-preserving. */
export function toPriorReadingCitations(results: readonly RecallResult[]): ResolvedCitation[] {
  return results.map(toPriorReadingCitation)
}
