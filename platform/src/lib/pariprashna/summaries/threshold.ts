/**
 * Paripraśna durable conversation summaries — PB-2 (SMṚTI) lane M-3 — threshold.
 *
 * Pure, isomorphic decision logic: "have enough NEW canonical turns
 * accumulated since the last summary to justify writing another one?"
 *
 * Trigger, stated explicitly (per the brief: "pick a reasonable, clearly
 * documented trigger... doesn't need to match any pre-existing convention"):
 * every `DEFAULT_SUMMARIZE_EVERY_N_MESSAGES` NEW canonical messages
 * (user+assistant rows combined) since the last summary's high-water mark,
 * EXCLUDING a reserved "tail" of the most recent messages that are always kept
 * verbatim (never folded into a summary) so the immediate exchange a synthesis
 * prompt is answering is never itself lossy-summarized. A message-count
 * trigger (rather than a token estimate) is chosen because it needs no
 * tokenizer dependency, is trivially testable, and every canonical message
 * already carries a stable ordinal position (`created_at` / insertion order)
 * with no extra bookkeeping.
 */

/** New canonical messages since the last summary, before a threshold fires. */
export const DEFAULT_SUMMARIZE_EVERY_N_MESSAGES = 6

/** Most-recent messages NEVER folded into a summary — always kept verbatim. */
export const DEFAULT_VERBATIM_TAIL_MESSAGES = 2

export interface ThresholdInput {
  /** Count of NEW canonical messages available to summarize, i.e. everything
   *  since the last summary's `covers_through_message_id` MINUS the reserved
   *  verbatim tail. Callers compute this (see `service.ts`'s
   *  `summarizableCandidates`) rather than passing raw totals here, keeping
   *  this function a single, trivially-testable comparison. */
  eligibleNewMessageCount: number
}

/** True once `eligibleNewMessageCount` reaches the threshold. */
export function shouldSummarize(
  input: ThresholdInput,
  everyN: number = DEFAULT_SUMMARIZE_EVERY_N_MESSAGES,
): boolean {
  return input.eligibleNewMessageCount >= everyN
}
