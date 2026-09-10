/**
 * NO-LEAKAGE arm-3 — the drain half: turning queued intents into ledger rows.
 * Lane G1-C · PPR-31 arm 3.
 *
 * This is the ONLY code path that is meant to run under `role_ledger_write`. It
 * lives in `src/lib` rather than inside the script so it is unit-testable, but
 * nothing in the Next.js serving path imports it — that is asserted by
 * `__tests__/arm3_serving_path.test.ts`, which is the real detector behind the
 * claim "the ledger writer runs outside the synthesis process" (§N.8: a claim
 * with no code path that could make it read false is not a result).
 *
 * Pure module: no `server-only`, no pool, no flag reads. The DB port comes in.
 */

import {
  LedgerIntentSchema,
  claimPendingIntents,
  markIntentApplied,
  markIntentFailed,
  type LedgerOp,
  type OutboxDb,
  type OutboxRow,
} from './outbox'

export const LEDGER_TABLE = 'brahma_mimamsa_prediction_ledger' as const

export interface DrainResult {
  claimed: number
  applied: number
  failed: number
  /** Per-intent failures, verbatim. Never summarised away. */
  errors: Array<{ outbox_id: string; op: LedgerOp; message: string }>
}

function toDaterangeLiteral(w: { start: string; end: string } | null | undefined): string | null {
  return w ? `[${w.start},${w.end}]` : null
}

/**
 * Apply ONE validated intent. Returns the resulting ledger row id.
 *
 * Re-validates the payload after dequeue: `role_web_serve` can write the outbox,
 * so from here the queue is untrusted input, and a producer-side check is not
 * evidence about what is actually in the row.
 */
export async function applyIntent(row: OutboxRow, db: OutboxDb): Promise<string> {
  const intent = LedgerIntentSchema.parse({ op: row.op, payload: row.payload })

  // The outbox row's own chart_id is what RLS scoped; the payload's is what the
  // ledger row would carry. If they disagree, something rewrote one of them —
  // refuse rather than pick a winner.
  const payloadChart = (intent.payload as { chart_id?: string }).chart_id
  if (payloadChart !== row.chart_id) {
    throw new Error(
      `ARM3_CHART_MISMATCH: outbox row ${row.id} is scoped to chart ${row.chart_id} but its ` +
        `payload names ${payloadChart}. Refusing to write a ledger row whose chart scope is ` +
        `ambiguous.`,
    )
  }

  switch (intent.op) {
    case 'create_detected': {
      const p = intent.payload
      const { rows } = await db.query<{ id: string }>(
        `INSERT INTO ${LEDGER_TABLE} (
           chart_id, message_part_id, claim_text, domain, "window", direction,
           technique_refs, grounding_fact_ids, created_from_channel, lifecycle_status
         ) VALUES ($1, $2, $3, $4, $5::daterange, $6, $7::text[], $8::text[], $9, 'detected')
         RETURNING id::text AS id`,
        [
          p.chart_id,
          p.message_part_id ?? null,
          p.claim_text,
          p.domain ?? null,
          toDaterangeLiteral(p.window),
          p.direction ?? null,
          p.technique_refs,
          p.grounding_fact_ids,
          p.created_from_channel,
        ],
      )
      return rows[0].id
    }

    case 'transition': {
      const p = intent.payload
      const { rows } = await db.query<{ id: string }>(
        `UPDATE ${LEDGER_TABLE}
            SET lifecycle_status = $2,
                dismissed_reason = COALESCE($3, dismissed_reason),
                updated_at = now()
          WHERE id = $1 AND chart_id = $4
        RETURNING id::text AS id`,
        [p.ledger_row_id, p.to, p.dismissed_reason ?? null, p.chart_id],
      )
      if (rows.length === 0) {
        throw new Error(
          `ARM3_ROW_NOT_FOUND: ledger row ${p.ledger_row_id} not found for chart ${p.chart_id}.`,
        )
      }
      return rows[0].id
    }

    case 'record_outcome': {
      const p = intent.payload
      const { rows } = await db.query<{ id: string }>(
        `UPDATE ${LEDGER_TABLE}
            SET outcome = $2, outcome_value = $3, outcome_note = $4,
                outcome_recorded_at = now(), lifecycle_status = 'outcome_recorded',
                updated_at = now()
          WHERE id = $1 AND chart_id = $5
        RETURNING id::text AS id`,
        [p.ledger_row_id, p.outcome, p.outcome_value, p.outcome_note ?? null, p.chart_id],
      )
      if (rows.length === 0) {
        throw new Error(
          `ARM3_ROW_NOT_FOUND: ledger row ${p.ledger_row_id} not found for chart ${p.chart_id}.`,
        )
      }
      return rows[0].id
    }

    case 'create_confirmed':
      // Deliberately unimplemented, and it FAILS rather than silently succeeding.
      // The confirm path copies a D-16 provenance stamp under the
      // `trg_bmpl_freeze_confirmed` trigger and is a human action, not a
      // synthesis-path write; routing it through arm-3 is a real design step this
      // lane did not take. The enum keeps the slot so the shape is honest about
      // what is still owed, rather than pretending the queue covers everything.
      throw new Error(
        `ARM3_OP_NOT_IMPLEMENTED: "create_confirmed" is reserved but not implemented. The ` +
          `confirm path still writes in-process; see the G1-C cutover runbook's residuals.`,
      )

    default: {
      // Exhaustiveness guard. If a new op is added to LEDGER_OPS and the CHECK
      // constraint without a branch here, this fails to compile — the alternative
      // (an implicit fall-through returning undefined) would let an unhandled op
      // be marked applied with no ledger row behind it.
      const unreachable: never = intent
      throw new Error(`ARM3_UNKNOWN_OP: ${JSON.stringify(unreachable)}`)
    }
  }
}

/**
 * Drain up to `limit` intents. One intent's failure never aborts the batch —
 * it is recorded on its own row and the drain continues, so one poisoned payload
 * cannot stall the whole queue.
 */
export async function drainOutbox(db: OutboxDb, limit = 100): Promise<DrainResult> {
  const claimed = await claimPendingIntents(limit, db)
  const result: DrainResult = { claimed: claimed.length, applied: 0, failed: 0, errors: [] }

  for (const row of claimed) {
    try {
      const ledgerRowId = await applyIntent(row, db)
      await markIntentApplied(row.id, ledgerRowId, db)
      result.applied += 1
    } catch (err) {
      await markIntentFailed(row.id, err, db)
      result.failed += 1
      result.errors.push({
        outbox_id: row.id,
        op: row.op,
        message: err instanceof Error ? err.message : String(err),
      })
    }
  }
  return result
}
