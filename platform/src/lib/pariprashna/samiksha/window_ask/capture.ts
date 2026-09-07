import 'server-only'
/**
 * The window-opening ask — THE CAPTURE PATH (lane P4-G).
 *
 * The reader answers, and the answer reaches the ledger. This module is the whole of that
 * second half, and it is deliberately thin: the ledger write itself is NOT reimplemented here.
 * It delegates to `outcome_recorder.recordConversationalOutcome`, which is the existing,
 * already-proven L-5 orchestrator — the same function the review tab's Resolve action calls.
 * REUSE OVER REBUILD: a second writer would be a second place for the Brier computation, the
 * legal-transition matrix and the `unverifiable → NULL` invariant to drift out of agreement.
 *
 * ── THE THREE THINGS THIS MODULE REFUSES TO DO ─────────────────────────────────────────────
 *
 * 1. IT NEVER COERCES AN AMBIGUOUS ANSWER INTO A CLEAN OUTCOME.
 *    `classify.ts` returns `ambiguous` / `not_an_answer` for anything that is not unambiguous,
 *    and every one of those paths below writes NOTHING. The ledger row stays `window_closed`,
 *    stays on the badge, and can be asked about again. A gap in the calibration series is a
 *    visible, honest, recoverable state; a wrong entry in it is permanent and invisible.
 *
 * 2. IT NEVER FOLDS A DISPUTE INTO AN OUTCOME.
 *    A disagreement stays a disagreement. `dispute` writes nothing, and the result carries the
 *    reader's words VERBATIM in `dispute_text`. This is the third of the three non-folding
 *    enforcement points (see `classify.ts`'s header for the other two), and it is the one that
 *    is DB-OBSERVABLE: after a dispute, `SELECT lifecycle_status FROM
 *    brahma_mimamsa_prediction_ledger WHERE id = <row>` still returns `window_closed`. That is
 *    a fact a refuter can check, not a promise this file makes about itself.
 *
 * 3. IT NEVER TRUSTS THE CALLER'S ROW ID.
 *    The fire condition is RE-VERIFIED against the database at write time. A caller handing in
 *    a row that is `open`, already resolved, dismissed, or on a different chart gets a refusal
 *    with a reason — not a write. The read-time check in `select.ts` and this write-time check
 *    are independent on purpose: a stale client echo, a replayed request, or a race with the
 *    review tab must not be able to resolve a window through this path.
 *
 * ── "CAN'T TELL" IS A REAL ANSWER, AND LANDS AS A DISTINGUISHABLE VALUE ────────────────────
 * It is not a silent no-op and not a null hole. It writes `outcome = 'unverifiable'` with
 * `outcome_value = NULL`, reaching lifecycle state `unverifiable` — a terminal state distinct
 * from both `outcome_recorded` and `lapsed`. Three independent layers keep the value NULL: this
 * path (via the recorder), the L-1 DAL (`writer.ts` forces null for `unverifiable`), and the DB
 * itself (`CONSTRAINT bmpl_unverifiable_has_no_value`, migration 470). The DB constraint is the
 * §N.8 detector: it is a code path that WOULD fail — the INSERT would be rejected — if anything
 * above it ever tried to attach a number to a can't-tell.
 *
 * The reader's exact words are preserved on the row as `outcome_note` for EVERY recorded
 * outcome, so what was written is always traceable to what was said.
 */

import { getLedgerRow } from '../reader'
import type { LedgerExecutor } from '../writer'
import { recordConversationalOutcome } from '../outcome_recorder'
import type { LedgerRow } from '../schema'
import { classifyWindowAnswer, outcomeOf, type AnswerKind, type AnswerReading } from './classify'

/** Why a capture wrote nothing. Every one is a deliberate refusal, never a swallowed error. */
export const NOT_RECORDED_REASONS = [
  'row_not_found',
  'chart_mismatch',
  'window_not_awaiting_outcome',
  'dispute_not_folded',
  'ambiguous_not_coerced',
  'not_an_answer',
] as const
export type NotRecordedReason = (typeof NOT_RECORDED_REASONS)[number]

export interface WindowAnswerCapture {
  ledger_row_id: string
  /** How the answer was read, with the matched markers — the audit trail. */
  reading: AnswerReading
  /** True iff the ledger was written this call. */
  recorded: boolean
  /** Present iff `recorded` — the row AFTER the write, read back from the DB. */
  row: LedgerRow | null
  /** Present iff `!recorded`. */
  not_recorded_reason: NotRecordedReason | null
  /**
   * The reader's words, VERBATIM, when they expressed a disagreement. Never normalized, never
   * summarized, never mapped onto an outcome vocabulary.
   */
  dispute_text: string | null
  /** The row's lifecycle state after this call — the DB-observable non-folding evidence. */
  lifecycle_status_after: string | null
  /** Brier score for a scorable outcome; null for `unverifiable` and for every refusal. */
  brier: number | null
  outcome_value: number | null
}

function refusal(
  ledgerRowId: string,
  reading: AnswerReading,
  reason: NotRecordedReason,
  lifecycleAfter: string | null,
  disputeText: string | null = null,
): WindowAnswerCapture {
  return {
    ledger_row_id: ledgerRowId,
    reading,
    recorded: false,
    row: null,
    not_recorded_reason: reason,
    dispute_text: disputeText,
    lifecycle_status_after: lifecycleAfter,
    brier: null,
    outcome_value: null,
  }
}

/**
 * Capture a reader's free-text answer to a window-opening ask.
 *
 * @param args.ledgerRowId  the row the ask named (from the `window_ask` wire event's
 *                          `ledger_row_id`). RE-VERIFIED here; never trusted.
 * @param args.answerText   the reader's message, verbatim.
 * @param args.chartId      when supplied, the row must belong to it — a cross-chart echo is
 *                          refused rather than written.
 * @param args.partialValue optional numeric value for a `partial` outcome (default 0.5, owned
 *                          by `outcome_calibration.ts`).
 */
export async function captureWindowAnswer(args: {
  ledgerRowId: string
  answerText: string
  chartId?: string
  partialValue?: number
  exec?: LedgerExecutor
}): Promise<WindowAnswerCapture> {
  const { ledgerRowId, answerText, chartId, exec } = args
  const reading = classifyWindowAnswer(answerText)

  // ── (3) re-verify the fire condition at WRITE time, independently of the read. ──
  const row = exec ? await getLedgerRow(ledgerRowId, exec) : await getLedgerRow(ledgerRowId)
  if (!row) return refusal(ledgerRowId, reading, 'row_not_found', null)
  if (chartId && row.chart_id !== chartId) {
    return refusal(ledgerRowId, reading, 'chart_mismatch', row.lifecycle_status)
  }
  if (row.lifecycle_status !== 'window_closed' || row.outcome !== null) {
    return refusal(ledgerRowId, reading, 'window_not_awaiting_outcome', row.lifecycle_status)
  }

  // ── (2) dispute non-folding: no write, verbatim text preserved, row untouched. ──
  if (reading.kind === 'dispute') {
    return refusal(ledgerRowId, reading, 'dispute_not_folded', row.lifecycle_status, answerText)
  }

  // ── (1) ambiguity is never coerced. ──
  if (reading.kind === 'ambiguous') {
    return refusal(ledgerRowId, reading, 'ambiguous_not_coerced', row.lifecycle_status)
  }
  if (reading.kind === 'not_an_answer') {
    return refusal(ledgerRowId, reading, 'not_an_answer', row.lifecycle_status)
  }

  const outcome = outcomeOf(reading)
  if (outcome === null) {
    // Unreachable given the guards above, and kept as a hard stop rather than a fallthrough:
    // a future kind added to the vocabulary must fail loudly here, not acquire a default
    // outcome by accident (§N.7 item 6 — never substitute a plausible-sounding default).
    throw new Error(
      `captureWindowAnswer: reading kind "${reading.kind satisfies AnswerKind}" yielded no outcome ` +
        `and was not refused above; refusing to guess.`,
    )
  }

  // ── the REAL write, through the existing L-5 orchestrator. ──
  const result = await recordConversationalOutcome(
    ledgerRowId,
    { outcome, outcome_note: answerText, ...(args.partialValue !== undefined ? { partial_value: args.partialValue } : {}) },
    exec,
  )

  return {
    ledger_row_id: ledgerRowId,
    reading,
    recorded: true,
    row: result.ledger_row,
    not_recorded_reason: null,
    dispute_text: null,
    lifecycle_status_after: result.ledger_row.lifecycle_status,
    brier: result.brier,
    outcome_value: result.outcome_value,
  }
}
