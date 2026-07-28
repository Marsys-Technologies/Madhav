import 'server-only'
/**
 * SAMĪKṢĀ outcome recorder — PB-3 (SAMĪKṢĀ) lane L-5.
 *
 * The DB-touching orchestrator L-3's Resolve tab and the dock card call to record the outcome
 * of a confirmed conversational prediction. It:
 *   1. reads the real ledger row (L-1 reader),
 *   2. requires it to be `window_closed` (the only legal predecessor of a resolution),
 *   3. computes the Brier score from the row's stated `confidence` numrange + the observed
 *      outcome (outcome_calibration.ts — the pure half),
 *   4. transitions the ledger row to `outcome_recorded` (or `unverifiable`, Brier-excluded)
 *      via L-1's writer DAL, persisting the co-located outcome columns — the REAL write,
 *   5. returns the computed Brier + a fully-formed CalibrationWriteIntent whose
 *      `source_citation` IS the ledger row id ("the ledger is the citation", §14.5).
 *
 * It DELIBERATELY does not persist into `mimamsa_calibration`: the live table's schema
 * (PK (chart_id, match_id); no source_citation / brier_score / confidence column) cannot
 * receive this row without a schema change that is (a) outside L-5's may_touch (no migrations),
 * (b) on a mi_pramana-owned table, and (c) a single-lane-unauthorizable decision requiring a
 * Pratinidhi MEMO. Writing a phantom-column INSERT would recreate the very `outcome.py` defect
 * this lane diagnosed. `calibration_persisted` is therefore always `false` and
 * `calibration_park_reason` names the park. See PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE.md.
 */

import { getLedgerRow } from './reader'
import { recordOutcome as recordLedgerOutcome, type LedgerExecutor } from './writer'
import { parseNumrangeLiteral, computeBrier, buildCalibrationIntent, type CalibrationWriteIntent } from './outcome_calibration'
import { OutcomeSchema, type LedgerRow, type Outcome } from './schema'

export const CALIBRATION_PARK_REASON =
  'mimamsa_calibration persistence PARKED (PB-3 L-5): the live table (PK chart_id,match_id; ' +
  'no source_citation/brier_score/confidence column) is the mi_pramana per-match analytical ' +
  'schema, not the retired MI-5-3 prototype the brief assumed. Persisting requires a schema ' +
  'change outside L-5 may_touch + a Pratinidhi MEMO. See ' +
  'PARK_PB-3_L-5_MIMAMSA_CALIBRATION_WRITE.md.'

export interface RecordConversationalOutcomeArgs {
  outcome: Outcome
  /** Optional operator annotation on what actually happened. */
  outcome_note?: string | null
  /** Override the numeric value for a `partial` outcome (defaults to 0.5). Ignored otherwise. */
  partial_value?: number
}

export interface RecordConversationalOutcomeResult {
  ledger_row: LedgerRow
  confidence_point: number | null
  outcome_value: number | null
  brier: number | null
  /** The calibration record this outcome produces — assembled, NOT persisted (see park reason). */
  calibration_intent: CalibrationWriteIntent
  calibration_persisted: false
  calibration_park_reason: string
}

/**
 * Record a conversational prediction's outcome against its real ledger row.
 *
 * @param ledgerRowId  the `brahma_mimamsa_prediction_ledger.id` being resolved
 * @param args         the observed outcome (+ optional note / partial value)
 * @param exec         injectable executor (tests drive a real throwaway pg Pool; production
 *                     omits it and gets the shared client)
 */
export async function recordConversationalOutcome(
  ledgerRowId: string,
  args: RecordConversationalOutcomeArgs,
  exec?: LedgerExecutor,
): Promise<RecordConversationalOutcomeResult> {
  const outcome = OutcomeSchema.parse(args.outcome)

  const row = exec ? await getLedgerRow(ledgerRowId, exec) : await getLedgerRow(ledgerRowId)
  if (!row) throw new Error(`recordConversationalOutcome: ledger row ${ledgerRowId} not found`)
  if (row.lifecycle_status !== 'window_closed') {
    throw new Error(
      `recordConversationalOutcome: row ${ledgerRowId} is '${row.lifecycle_status}', not ` +
        `'window_closed'; an outcome may only be recorded on a window-closed claim ` +
        `(L-4 closes the window first).`,
    )
  }

  const band = parseNumrangeLiteral(row.confidence)
  const brier = computeBrier(band, outcome, args.partial_value)

  // The REAL write: transition the ledger row and persist the co-located outcome columns via
  // L-1's DAL (which enforces the legal transition + the unverifiable→null-value invariant).
  const resolved = exec
    ? await recordLedgerOutcome(
        ledgerRowId,
        { outcome, outcome_value: brier.outcome_value, outcome_note: args.outcome_note ?? null },
        exec,
      )
    : await recordLedgerOutcome(ledgerRowId, {
        outcome,
        outcome_value: brier.outcome_value,
        outcome_note: args.outcome_note ?? null,
      })

  const calibration_intent = buildCalibrationIntent(resolved, brier)

  return {
    ledger_row: resolved,
    confidence_point: brier.confidence_point,
    outcome_value: brier.outcome_value,
    brier: brier.brier,
    calibration_intent,
    calibration_persisted: false,
    calibration_park_reason: CALIBRATION_PARK_REASON,
  }
}
