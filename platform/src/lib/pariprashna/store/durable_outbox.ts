/**
 * Paripraśna durable-persistence write-ahead outbox — P2-D (PPR-10, FD-9).
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * NEEDS A MIGRATION — conductor to open a schema-train lease before this can
 * land against a real table. Per the P2 coordination-lease rule (schema
 * changes are explicitly NOT in this wave's must_not_touch-exempt scope; see
 * `origin/campaign-coordination`'s P2 kickoff entry), this lane does NOT
 * author or apply a migration file. Everything below is built against the
 * `OutboxDb` port so it is unit-testable today and ready to wire the moment
 * the table exists. The exact schema this module needs:
 *
 *   CREATE TABLE pariprashna_persistence_outbox (
 *     id            bigserial   PRIMARY KEY,
 *     -- Idempotency key: one outbox row per assistant message. `writeTurn`
 *     -- (store/writer.ts) is ALREADY idempotent by message id (upsert +
 *     -- delete-then-insert parts), so ON CONFLICT (message_id) DO UPDATE
 *     -- here is safe — a re-enqueue of the same message just replaces the
 *     -- pending payload rather than creating a duplicate write-ahead entry.
 *     message_id    uuid        NOT NULL UNIQUE,
 *     conversation_id uuid      NOT NULL,
 *     -- Carried explicitly (not joined) so this table is RLS-scopable like
 *     -- every other C1 table — mirrors migration 576 §2's
 *     -- pariprashna_ledger_outbox.chart_id precedent.
 *     chart_id      uuid        NOT NULL,
 *     turn_id       text        NOT NULL,
 *     -- The full write-ahead payload: { message: CanonicalMessage, parts:
 *     -- MessagePartInput[] } — Zod-validated on the way IN (enqueue) and
 *     -- again on the way OUT (replay), same untrusted-queue discipline as
 *     -- arm3/outbox.ts, even when producer and consumer are today the same
 *     -- process (a future out-of-process drain must not have to change this
 *     -- module's trust model).
 *     payload       jsonb       NOT NULL,
 *     status        text        NOT NULL DEFAULT 'pending'
 *                                 CHECK (status IN ('pending', 'applied', 'failed')),
 *     attempts      integer     NOT NULL DEFAULT 0 CHECK (attempts >= 0),
 *     enqueued_at   timestamptz NOT NULL DEFAULT now(),
 *     claimed_at    timestamptz,
 *     applied_at    timestamptz,
 *     last_error    text,
 *     CONSTRAINT pariprashna_persistence_outbox_applied_has_no_error
 *       CHECK (status <> 'applied' OR last_error IS NULL)
 *   );
 *   CREATE INDEX idx_pariprashna_persistence_outbox_pending
 *     ON pariprashna_persistence_outbox (enqueued_at) WHERE status = 'pending';
 *   CREATE INDEX idx_pariprashna_persistence_outbox_chart
 *     ON pariprashna_persistence_outbox (chart_id);
 *
 *   RLS (deferred to the same arm-1 cutover as migration 576 — CREATE, not
 *   ENABLE, per that migration's own arming discipline): a
 *   `chart_id = app_chart_context()` policy for role_web_serve, matching the
 *   `pariprashna_ledger_outbox` precedent exactly.
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * WHY AN OUTBOX (write-ahead), NOT A DIRECT SYNCHRONOUS WRITE
 * ─────────────────────────────────────────────────────────────
 * `writeTurn` today is a single-transaction, in-process, synchronous DB
 * write — when it returns, the turn IS durably persisted (this is the
 * DIRECT mode `durable_writer.ts` still uses when the feature flag is off,
 * so flag-off behavior is byte-for-byte what it always was). What a
 * synchronous write CANNOT survive is the PROCESS dying between "the SSE
 * stream told the reader the turn is done" (`turn.close`) and "the write
 * actually committed" — a narrow but real window under load-shedding,
 * container eviction, or a deploy mid-request. The write-ahead pattern
 * closes that window: record the INTENT to persist (this table) BEFORE
 * attempting the real write, so a crash between the two leaves a durable,
 * replayable record of what was owed — `replayPendingPersistence` below is
 * the crash-recovery half that turns a `pending` row back into a completed
 * `writeTurn` call, without needing the original request's process to still
 * be alive.
 *
 * Idempotent by construction: `writeTurn` is itself idempotent (see its own
 * header), so replaying the SAME write-ahead entry twice — a duplicate
 * drain, a retried recovery sweep — converges to the same final row, never a
 * duplicate.
 *
 * Pure module: no `server-only`, no pool import, no `@/lib/config` — mirrors
 * `arm3/outbox.ts`'s own stated discipline exactly, for the same reason
 * (unit-testable without a database, integration-testable against a real one
 * once the migration lands).
 */

import { z } from 'zod'

import {
  CanonicalMessageSchema,
  MessagePartInputSchema,
  type CanonicalMessage,
  type MessagePartInput,
} from './schema'

/** The physical table this module targets — named once, per the DDL above. */
export const PERSISTENCE_OUTBOX_TABLE = 'pariprashna_persistence_outbox' as const

export const PersistenceOutboxStatusSchema = z.enum(['pending', 'applied', 'failed'])
export type PersistenceOutboxStatus = z.infer<typeof PersistenceOutboxStatusSchema>

/** The write-ahead payload shape: exactly what `writeTurn` needs to replay. */
export const PersistenceWriteAheadPayloadSchema = z
  .object({
    message: CanonicalMessageSchema,
    parts: z.array(MessagePartInputSchema),
  })
  .strict()
export type PersistenceWriteAheadPayload = z.infer<typeof PersistenceWriteAheadPayloadSchema>

/** One outbox row as a caller enqueues it (pre-DB-assigned fields). */
export interface WriteAheadEntryInput {
  message_id: string
  conversation_id: string
  chart_id: string
  turn_id: string
  message: CanonicalMessage
  parts: readonly MessagePartInput[]
}

/** One outbox row as the replay path reads it back. */
export interface PersistenceOutboxRow {
  id: string
  message_id: string
  chart_id: string
  turn_id: string
  payload: PersistenceWriteAheadPayload
  status: PersistenceOutboxStatus
  attempts: number
}

/** Minimal query port — satisfied by a `pg.Pool`, a `pg.PoolClient`, or a fake.
 *  Mirrors `arm3/outbox.ts`'s `OutboxDb` exactly. */
export interface OutboxDb {
  query<T = Record<string, unknown>>(
    sql: string,
    params?: unknown[],
  ): Promise<{ rows: T[]; rowCount?: number | null }>
}

/**
 * Record a write-ahead intent BEFORE attempting the real `writeTurn`.
 * `ON CONFLICT (message_id) DO UPDATE` — a re-enqueue of the same message
 * (a retried request, an idempotent replay) replaces the pending payload
 * rather than accumulating duplicate rows, matching `writeTurn`'s own
 * idempotency (§N.3 delete-then-insert, applied here to the QUEUE entry
 * rather than the final row).
 *
 * Returns the outbox row id. Throws if the underlying table does not exist
 * (pre-migration) or on any other DB error — callers (`durable_writer.ts`)
 * are responsible for degrading gracefully rather than breaking a live
 * reading over write-ahead plumbing; this function itself stays honest and
 * does not swallow a real failure.
 */
export async function writeAheadTurn(entry: WriteAheadEntryInput, db: OutboxDb): Promise<string> {
  const payload: PersistenceWriteAheadPayload = PersistenceWriteAheadPayloadSchema.parse({
    message: entry.message,
    parts: entry.parts,
  })
  const { rows } = await db.query<{ id: string }>(
    `INSERT INTO ${PERSISTENCE_OUTBOX_TABLE}
       (message_id, conversation_id, chart_id, turn_id, payload, status)
     VALUES ($1, $2, $3, $4, $5::jsonb, 'pending')
     ON CONFLICT (message_id) DO UPDATE SET
       payload    = EXCLUDED.payload,
       status     = 'pending',
       last_error = NULL
     RETURNING id::text AS id`,
    [entry.message_id, entry.conversation_id, entry.chart_id, entry.turn_id, JSON.stringify(payload)],
  )
  return rows[0].id
}

export async function markPersistenceApplied(outboxId: string, db: OutboxDb): Promise<void> {
  await db.query(
    `UPDATE ${PERSISTENCE_OUTBOX_TABLE}
        SET status = 'applied', applied_at = now(), last_error = NULL
      WHERE id = $1`,
    [outboxId],
  )
}

/**
 * Record a failure WITHOUT marking `applied` — the row stays `pending`
 * (retryable on the next recovery sweep) unless `terminal` is set, in which
 * case it moves to `failed` (still visible, still honestly reported — never
 * silently dropped, per B.10). `attempts` increments either way so a
 * permanently-poisoned entry is countable, not silently spinning forever.
 */
export async function markPersistenceFailed(
  outboxId: string,
  error: unknown,
  db: OutboxDb,
  opts: { terminal?: boolean } = {},
): Promise<void> {
  const message = error instanceof Error ? error.message : String(error)
  await db.query(
    `UPDATE ${PERSISTENCE_OUTBOX_TABLE}
        SET status = $2, last_error = $3, attempts = attempts + 1, claimed_at = NULL
      WHERE id = $1`,
    [outboxId, opts.terminal ? 'failed' : 'pending', message.slice(0, 4000)],
  )
}

/**
 * Claim up to `limit` pending/failed intents for a recovery sweep.
 * `FOR UPDATE SKIP LOCKED` so a concurrent recovery run (or the original
 * in-request attempt still in flight) never double-claims the same row —
 * the exact reason `arm3/outbox.ts`'s `claimPendingIntents` uses the same
 * pattern.
 */
export async function claimPendingPersistenceEntries(
  limit: number,
  db: OutboxDb,
): Promise<PersistenceOutboxRow[]> {
  const { rows } = await db.query<{
    id: string
    message_id: string
    chart_id: string
    turn_id: string
    payload: unknown
    status: PersistenceOutboxStatus
    attempts: number
  }>(
    `UPDATE ${PERSISTENCE_OUTBOX_TABLE} o
        SET claimed_at = now()
      WHERE o.id IN (
              SELECT id FROM ${PERSISTENCE_OUTBOX_TABLE}
               WHERE status IN ('pending', 'failed')
               ORDER BY enqueued_at
               LIMIT $1
               FOR UPDATE SKIP LOCKED
            )
    RETURNING o.id::text AS id, o.message_id::text AS message_id, o.chart_id::text AS chart_id,
              o.turn_id, o.payload, o.status, o.attempts`,
    [limit],
  )
  return rows.map((r) => ({
    id: r.id,
    message_id: r.message_id,
    chart_id: r.chart_id,
    turn_id: r.turn_id,
    // Re-validated here — untrusted-queue discipline (module header): a
    // producer-side check at enqueue time is not evidence about what a
    // future out-of-process drain actually reads back.
    payload: PersistenceWriteAheadPayloadSchema.parse(r.payload),
    status: r.status,
    attempts: r.attempts,
  }))
}

/** Pending/failed counts, for honest reporting (mirrors `outboxDepth`). */
export async function persistenceOutboxDepth(
  db: OutboxDb,
): Promise<{ pending: number; failed: number }> {
  const { rows } = await db.query<{ pending: string; failed: string }>(
    `SELECT count(*) FILTER (WHERE status = 'pending') AS pending,
            count(*) FILTER (WHERE status = 'failed')  AS failed
       FROM ${PERSISTENCE_OUTBOX_TABLE}`,
  )
  return { pending: Number(rows[0].pending), failed: Number(rows[0].failed) }
}

export interface ReplayResult {
  claimed: number
  applied: number
  failed: number
  errors: Array<{ outbox_id: string; message_id: string; message: string }>
}

/**
 * CRASH RECOVERY: claim up to `limit` pending/failed write-ahead entries and
 * replay each through `applyFn` (production callers pass `writeTurn` from
 * `store/writer.ts`). One entry's failure never aborts the sweep — recorded
 * on its own row, sweep continues — so one poisoned payload cannot stall
 * every other turn waiting to be confirmed durable. This is the function a
 * scheduled recovery job (or, minimally, a startup sweep) calls; wiring an
 * actual out-of-process runner to it is NOT this lane's migration-gated
 * scope — see the module header and the P2-D report's residuals.
 */
export async function replayPendingPersistence(
  db: OutboxDb,
  applyFn: (message: CanonicalMessage, parts: readonly MessagePartInput[]) => Promise<unknown>,
  limit = 50,
): Promise<ReplayResult> {
  const claimed = await claimPendingPersistenceEntries(limit, db)
  const result: ReplayResult = { claimed: claimed.length, applied: 0, failed: 0, errors: [] }

  for (const row of claimed) {
    try {
      await applyFn(row.payload.message, row.payload.parts)
      await markPersistenceApplied(row.id, db)
      result.applied += 1
    } catch (err) {
      // Not marked terminal here: a transient DB error deserves another
      // sweep, not a permanent failed state. A caller wanting terminal
      // failure after N attempts checks `row.attempts` and passes
      // `{ terminal: true }` to its own retry wrapper around this function.
      await markPersistenceFailed(row.id, err, db)
      result.failed += 1
      result.errors.push({
        outbox_id: row.id,
        message_id: row.message_id,
        message: err instanceof Error ? err.message : String(err),
      })
    }
  }
  return result
}
