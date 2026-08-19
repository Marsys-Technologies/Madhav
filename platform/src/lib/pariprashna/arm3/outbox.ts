/**
 * NO-LEAKAGE arm-3 — the ledger-write outbox.
 * Lane G1-C · PPR-31 ("out-of-process writer") · TA §14.10 arm 3.
 *
 * §14.10 arm 3, verbatim: "The ledger writer runs outside the synthesis process
 * and holds the only write role."
 *
 * ── WHAT WAS ACTUALLY THERE ──────────────────────────────────────────────────
 * Not that. Verified 2026-08-19 against the tree: EVERY insert into
 * `brahma_mimamsa_prediction_ledger` runs IN-PROCESS inside the Next.js request
 * pipeline — `pipeline/persistence_stage.ts` → `samiksha/capture.ts` →
 * `samiksha/writer.ts:createLedgerRow`. The one out-of-process component that
 * exists (`.github/workflows/samiksha-daily.yml` → `scripts/samiksha/daily_job.ts`)
 * only UPDATEs lifecycle to `window_closed`; it is a window sweeper, not the
 * writer arm-3 means. So arm-3 is NEW here, not a rewiring of something existing.
 *
 * ── WHY AN OUTBOX AND NOT A DIRECT CALL ──────────────────────────────────────
 * After the role cutover, `role_web_serve` has NO insert/update on the ledger at
 * all (migration 576 §3c). The serving process therefore cannot write the ledger
 * even if it wanted to — which is the point. It writes an INTENT to
 * `pariprashna_ledger_outbox`, the one ledger-adjacent privilege it keeps
 * (INSERT only, no SELECT, no UPDATE — it cannot read back or amend what it
 * queued). The worker, sole holder of `role_ledger_write`, drains and applies.
 *
 * ── THE TRUST DIRECTION ──────────────────────────────────────────────────────
 * `role_web_serve` can write this table, so from the WORKER's point of view the
 * queue is untrusted input. Intents are Zod-validated on the way IN and again on
 * the way OUT. The worker never trusts the producer's framing.
 *
 * Pure module: no `server-only`, no pool import, no `@/lib/config`. Everything
 * comes through the `OutboxDb` port, so the whole thing is unit-testable without
 * a database and integration-testable against a real one.
 */

import { z } from 'zod'

import { UuidLikeSchema } from '../samiksha/schema'

/** The physical table. Named once. */
export const OUTBOX_TABLE = 'pariprashna_ledger_outbox' as const

/** The closed operation set — mirrors the CHECK constraint in migration 576. */
export const LEDGER_OPS = [
  'create_detected',
  'create_confirmed',
  'transition',
  'record_outcome',
] as const
export type LedgerOp = (typeof LEDGER_OPS)[number]

/**
 * The house uuid idiom, imported rather than restated. `z.string().uuid()` in
 * zod v4 enforces RFC version/variant nibbles, which would reject perfectly valid
 * ids the database already holds; `UuidLikeSchema` is the shape-only check the
 * ledger's own schema uses, and using a DIFFERENT rule here than the table it
 * writes into is exactly the drift §N.7 item 3 warns about.
 */
const Uuid = UuidLikeSchema

/**
 * The `create_detected` payload — the synthesis-path write, and the one arm-3
 * exists for. Mirrors the subset of `CreateLedgerRowInput` that
 * `captureDetectedCandidates` actually sends. Deliberately NOT the full input
 * type: a `detected` row carries no D-16 stamp and no confidence band (that is
 * the W-1 no-auto-promotion rule), so accepting those fields here would widen the
 * queue into a channel for writing rows the capture path is not allowed to write.
 */
export const CreateDetectedPayloadSchema = z
  .object({
    chart_id: Uuid,
    message_part_id: Uuid.nullable().optional(),
    claim_text: z.string().min(1),
    domain: z.string().nullable().optional(),
    window: z
      .object({ start: z.string(), end: z.string() })
      .nullable()
      .optional(),
    direction: z.string().nullable().optional(),
    technique_refs: z.array(z.string()).default([]),
    grounding_fact_ids: z.array(z.string()).default([]),
    created_from_channel: z.string().default('pariprashna'),
  })
  .strict()

export const TransitionPayloadSchema = z
  .object({
    chart_id: Uuid,
    ledger_row_id: Uuid,
    to: z.string().min(1),
    dismissed_reason: z.string().nullable().optional(),
  })
  .strict()

export const RecordOutcomePayloadSchema = z
  .object({
    chart_id: Uuid,
    ledger_row_id: Uuid,
    outcome: z.enum(['happened', 'did_not_happen', 'partial', 'unverifiable']),
    outcome_value: z.number().min(0).max(1).nullable(),
    outcome_note: z.string().nullable().optional(),
  })
  .strict()

export const LedgerIntentSchema = z.discriminatedUnion('op', [
  z.object({ op: z.literal('create_detected'), payload: CreateDetectedPayloadSchema }),
  // `create_confirmed` is a RESERVED slot, not a working op: `drain.ts` throws
  // ARM3_OP_NOT_IMPLEMENTED for it. The payload is left open because there is no
  // honest shape to declare for something unbuilt — declaring a precise schema
  // would imply an implementation behind it (§N.8).
  z.object({ op: z.literal('create_confirmed'), payload: z.record(z.string(), z.unknown()) }),
  z.object({ op: z.literal('transition'), payload: TransitionPayloadSchema }),
  z.object({ op: z.literal('record_outcome'), payload: RecordOutcomePayloadSchema }),
])
/** A validated intent — defaults applied. What the worker sees. */
export type LedgerIntent = z.infer<typeof LedgerIntentSchema>
/**
 * What a CALLER supplies — before `.default()` fills in `technique_refs`,
 * `grounding_fact_ids` and `created_from_channel`. Distinct from `LedgerIntent`
 * on purpose: requiring a producer to pre-fill values the schema exists to
 * supply would push those defaults back out to every call site, which is how
 * they drift.
 */
export type LedgerIntentInput = z.input<typeof LedgerIntentSchema>

/** One outbox row as the worker reads it. */
export interface OutboxRow {
  id: string
  chart_id: string
  op: LedgerOp
  payload: Record<string, unknown>
  attempts: number
}

/** Minimal query port — satisfied by a `pg.Pool`, a `pg.PoolClient`, or a fake. */
export interface OutboxDb {
  query<T = Record<string, unknown>>(
    sql: string,
    params?: unknown[],
  ): Promise<{ rows: T[]; rowCount?: number | null }>
}

/**
 * The chart id an intent is FOR. Taken from the validated payload, never from a
 * separate caller-supplied argument that could disagree with it — one source, so
 * the outbox row's `chart_id` (which the RLS policy filters on) and the ledger
 * row the worker will write cannot end up scoped to different charts.
 */
export function chartIdOf(intent: LedgerIntent): string {
  return (intent.payload as { chart_id: string }).chart_id
}

/**
 * Enqueue a ledger write intent. Returns the outbox row id — NOT a ledger row id,
 * because no ledger row exists yet. Callers must not present this as a ledger id
 * (§N.7 item 6: an honest null beats a plausible-looking substitute).
 */
export async function enqueueLedgerIntent(
  raw: LedgerIntentInput,
  db: OutboxDb,
): Promise<string> {
  const intent = LedgerIntentSchema.parse(raw)
  const { rows } = await db.query<{ id: string }>(
    `INSERT INTO ${OUTBOX_TABLE} (chart_id, op, payload)
     VALUES ($1, $2, $3::jsonb)
     RETURNING id::text AS id`,
    [chartIdOf(intent), intent.op, JSON.stringify(intent.payload)],
  )
  return rows[0].id
}

/**
 * Claim up to `limit` pending intents for this worker.
 *
 * `FOR UPDATE SKIP LOCKED` so two worker instances never apply the same intent —
 * the ledger has no natural idempotency key for a `detected` row, so double-drain
 * would mean duplicate ledger rows, and "we only ever run one worker" is a
 * deployment convention, not a guarantee.
 */
export async function claimPendingIntents(
  limit: number,
  db: OutboxDb,
): Promise<OutboxRow[]> {
  const { rows } = await db.query<OutboxRow>(
    `UPDATE ${OUTBOX_TABLE} o
        SET claimed_at = now(), attempts = o.attempts + 1
      WHERE o.id IN (
              SELECT id FROM ${OUTBOX_TABLE}
               WHERE applied_at IS NULL
               ORDER BY enqueued_at
               LIMIT $1
               FOR UPDATE SKIP LOCKED
            )
    RETURNING o.id::text AS id, o.chart_id::text AS chart_id, o.op, o.payload, o.attempts`,
    [limit],
  )
  return rows
}

export async function markIntentApplied(
  outboxId: string,
  ledgerRowId: string,
  db: OutboxDb,
): Promise<void> {
  await db.query(
    `UPDATE ${OUTBOX_TABLE}
        SET applied_at = now(), ledger_row_id = $2, last_error = NULL
      WHERE id = $1`,
    [outboxId, ledgerRowId],
  )
}

/**
 * Record a failure WITHOUT marking the intent applied, so it is retried on the
 * next drain and stays visible as pending. `attempts` is already incremented by
 * the claim, so a permanently-poisoned intent is countable rather than silently
 * spinning — the worker reports it, it does not swallow it.
 */
export async function markIntentFailed(
  outboxId: string,
  error: unknown,
  db: OutboxDb,
): Promise<void> {
  const message = error instanceof Error ? error.message : String(error)
  await db.query(
    `UPDATE ${OUTBOX_TABLE} SET last_error = $2, claimed_at = NULL WHERE id = $1`,
    [outboxId, message.slice(0, 4000)],
  )
}

/** Pending / failed counts, for the worker's own honest reporting. */
export async function outboxDepth(
  db: OutboxDb,
): Promise<{ pending: number; failed: number }> {
  const { rows } = await db.query<{ pending: string; failed: string }>(
    `SELECT count(*) FILTER (WHERE applied_at IS NULL)                    AS pending,
            count(*) FILTER (WHERE applied_at IS NULL AND last_error IS NOT NULL) AS failed
       FROM ${OUTBOX_TABLE}`,
  )
  return { pending: Number(rows[0].pending), failed: Number(rows[0].failed) }
}
