/**
 * Paripraśna safety — HS-5, THE RETRACTION RECORD (lane G1-A).
 *
 * SAFETY_PRIVACY_TENANCY §2 HS-5, translating MP §3.5.A.6 ("Reversibility.
 * Every output is rescindable if calibration data reveals it was unfounded"):
 * "a receipt-linked retraction record (what was retracted, why, evidence ref,
 * when) APPENDED — never edited into — the sealed reading (its append-only
 * correction mechanism is the vehicle); recipient notification for
 * cohort/acharya disclosure classes; a retraction note on any prediction ledger
 * row the reading fed. Retraction is a GOVERNANCE ACT (native-initiated or
 * red-team-initiated), NOT an automated one."
 *
 * Two design consequences of that last sentence, both structural:
 *
 *  1. There is no scheduler, job, or heuristic in this file that can retract
 *     anything. `recordRetraction` requires an `initiated_by` principal and an
 *     `initiator_kind` of `native` or `red_team`, and refuses without them.
 *     A future automated caller would have to add a new enum member — a diff,
 *     not a default.
 *  2. Nothing here mutates the reading. The retraction is a NEW row pointing at
 *     the reading's receipt hash. D-18 ("corrections in place with the error
 *     visible") is honored by APPENDING the correction, exactly as the sealed
 *     reading's own append-only correction mechanism does.
 *
 * ── WHAT IS BUILT AND WHAT IS NOT ────────────────────────────────────────────
 * BUILT: the record, its append-only table, the prediction-ledger note, and the
 * notification-obligation row for cohort/acharya recipients.
 * NOT BUILT: the delivery of that notification (there is no notification
 * transport in this codebase — see `notification.ts`). The obligation is
 * RECORDED as pending rather than marked delivered, because a `delivered: true`
 * with no delivery behind it is precisely the §N.8 defect class.
 */

import type { SafetyDb, SafetyQueryable } from './types'
import { SafetyFeatureDisabledError } from './types'
import { isSafetyGateEnabled } from './flag'

export type RetractionInitiatorKind = 'native' | 'red_team'

export type RetractionScope =
  | 'whole_reading'
  | 'specific_claim'
  | 'prediction_only'
  | 'calibration_language_only'

export interface RecordRetractionArgs {
  retractionId: string
  chartId: string
  /** The turn whose reading is being retracted. */
  turnId: string
  /** The receipt hash the retraction is LINKED to (HS-5: "receipt-linked"). */
  receiptHash: string | null
  scope: RetractionScope
  /** Why, in the retractor's own words. This is governance prose, not C1. */
  reason: string
  /** Where the evidence that it was unfounded lives (a ref, never the body). */
  evidenceRef: string | null
  initiatedBy: string
  initiatorKind: RetractionInitiatorKind
  /** Prediction-ledger row ids the reading fed, to be noted. */
  predictionLedgerIds?: string[]
  /** Disclosure classes that must be notified. Recorded as PENDING. */
  notifyDisclosureClasses?: Array<'cohort_subject' | 'acharya_reviewer'>
  now?: Date
}

export interface RetractionResult {
  retraction_id: string
  recorded: boolean
  /** Ledger rows the note actually landed on. Counted, never assumed. */
  prediction_notes_written: number
  /** Notification obligations recorded as PENDING. Not "sent". */
  notification_obligations_recorded: number
}

export async function recordRetraction(
  db: SafetyDb,
  args: RecordRetractionArgs,
): Promise<RetractionResult> {
  if (!isSafetyGateEnabled()) throw new SafetyFeatureDisabledError('recordRetraction')
  if (!args.initiatedBy) {
    throw new Error('RETRACTION_REQUIRES_INITIATOR: retraction is a governance act and must name who performed it')
  }
  if (args.initiatorKind !== 'native' && args.initiatorKind !== 'red_team') {
    throw new Error(
      `RETRACTION_INITIATOR_KIND_INVALID: "${String(args.initiatorKind)}" — HS-5 permits only ` +
        `native-initiated or red-team-initiated retraction; there is no automated path`,
    )
  }
  if (!args.reason?.trim()) {
    throw new Error('RETRACTION_REQUIRES_REASON: a retraction with no stated reason is not a correction')
  }

  const now = (args.now ?? new Date()).toISOString()
  let predictionNotes = 0
  let obligations = 0

  await db.withTransaction(async (tx: SafetyQueryable) => {
    await tx.query(
      `INSERT INTO pariprashna_retractions (
         retraction_id, chart_id, turn_id, receipt_hash, scope, reason, evidence_ref,
         initiated_by, initiator_kind, recorded_at
       ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)`,
      [
        args.retractionId,
        args.chartId,
        args.turnId,
        args.receiptHash,
        args.scope,
        args.reason,
        args.evidenceRef,
        args.initiatedBy,
        args.initiatorKind,
        now,
      ],
    )

    for (const ledgerId of args.predictionLedgerIds ?? []) {
      const r = await tx.query(
        `INSERT INTO pariprashna_retraction_prediction_notes (
           retraction_id, prediction_ledger_id, noted_at
         ) VALUES ($1,$2,$3)
         ON CONFLICT (retraction_id, prediction_ledger_id) DO NOTHING
         RETURNING prediction_ledger_id`,
        [args.retractionId, ledgerId, now],
      )
      predictionNotes += r.rows.length
    }

    for (const cls of args.notifyDisclosureClasses ?? []) {
      const r = await tx.query(
        `INSERT INTO pariprashna_retraction_notifications (
           retraction_id, disclosure_class, state, recorded_at
         ) VALUES ($1,$2,'pending',$3)
         ON CONFLICT (retraction_id, disclosure_class) DO NOTHING
         RETURNING disclosure_class`,
        [args.retractionId, cls, now],
      )
      obligations += r.rows.length
    }
  })

  return {
    retraction_id: args.retractionId,
    recorded: true,
    prediction_notes_written: predictionNotes,
    notification_obligations_recorded: obligations,
  }
}

export interface RetractionRow {
  retraction_id: string
  chart_id: string
  turn_id: string
  receipt_hash: string | null
  scope: RetractionScope
  reason: string
  evidence_ref: string | null
  initiated_by: string
  initiator_kind: RetractionInitiatorKind
  recorded_at: string
}

/** Every retraction against one turn, oldest first. Append-only, so this is history. */
export async function retractionsForTurn(db: SafetyDb, turnId: string): Promise<RetractionRow[]> {
  const { rows } = await db.query<RetractionRow>(
    `SELECT retraction_id, chart_id, turn_id, receipt_hash, scope, reason, evidence_ref,
            initiated_by, initiator_kind, recorded_at::text AS recorded_at
       FROM pariprashna_retractions WHERE turn_id = $1 ORDER BY recorded_at ASC`,
    [turnId],
  )
  return rows
}

/**
 * Has this reading been retracted? A serving surface that renders a sealed
 * reading MUST ask this before rendering it.
 *
 * Returns the retractions rather than a bare boolean, because "retracted" is
 * not one bit: a `calibration_language_only` retraction and a `whole_reading`
 * retraction call for different rendering, and collapsing them to a boolean
 * would force the caller to guess.
 */
export async function retractionStatus(
  db: SafetyDb,
  turnId: string,
): Promise<{ retracted: boolean; whole_reading_retracted: boolean; retractions: RetractionRow[] }> {
  const retractions = await retractionsForTurn(db, turnId)
  return {
    retracted: retractions.length > 0,
    whole_reading_retracted: retractions.some((r) => r.scope === 'whole_reading'),
    retractions,
  }
}
