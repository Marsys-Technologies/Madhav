import 'server-only'
/**
 * `writeTurnDurable` — the durable-persistence entrypoint P2-D wires into
 * `pipeline/persistence_stage.ts`, replacing a bare `writeTurn(...)` call.
 *
 * Two modes, selected by `isDurablePersistenceEnabled()` (default OFF):
 *
 *   DIRECT (flag off — today's exact behavior, byte-for-byte unchanged):
 *     calls `writeTurn` synchronously. When it resolves, the turn IS durably
 *     persisted — there is no gap, because there never was one in the
 *     synchronous single-transaction write. `settled_visual` and
 *     `durably_persisted` are (and always were) effectively the same moment
 *     in this mode; the reducer reflects that honestly rather than
 *     fabricating a fake window (see `state/reducer.ts`'s P2-D notes).
 *
 *   OUTBOX (flag on): records a write-ahead entry FIRST
 *     (`durable_outbox.ts#writeAheadTurn`), THEN attempts the same
 *     `writeTurn`. On success, marks the outbox entry applied — this is
 *     still a synchronous in-request write today (no async worker is wired;
 *     see the module header's residual note), but the write-ahead record
 *     means a crash BETWEEN the two steps is recoverable by
 *     `durable_outbox.ts#replayPendingPersistence` instead of silently
 *     losing the turn. On failure, the entry stays `pending` (retryable) and
 *     this function reports `status: 'pending'` rather than `'failed'` — an
 *     honest "not yet confirmed, but not abandoned either" (§N.7 item 6).
 *
 *   DEGRADED (outbox flag on, but the outbox table does not exist yet —
 *   pre-migration): `writeAheadTurn` throws. This function catches THAT
 *   specific failure, logs a warning, and falls back to DIRECT mode rather
 *   than breaking a live reading over write-ahead plumbing that has not
 *   landed. The reported outcome discloses the degradation
 *   (`mode: 'direct'`, `detail: 'outbox_unavailable'`) rather than silently
 *   claiming the outbox path ran.
 *
 * NEVER claims `durable` on a write that did not actually happen (§N.8): the
 * DIRECT/OUTBOX-applied paths only report `'durable'` after `writeTurn`
 * itself resolved successfully.
 */

import { writeTurn, type WriteTurnResult } from './writer'
import type { CanonicalMessage, MessagePartInput } from './schema'
import {
  writeAheadTurn,
  markPersistenceApplied,
  markPersistenceFailed,
  type OutboxDb,
} from './durable_outbox'
import { isDurablePersistenceEnabled } from './durable_flag'

export type DurablePersistenceStatus = 'pending' | 'durable' | 'failed'
export type DurablePersistenceMode = 'direct' | 'outbox'

export interface DurableWriteOutcome {
  status: DurablePersistenceStatus
  mode: DurablePersistenceMode
  /** Present only when the outcome needed disclosure beyond the bare status
   *  (a degradation, a retry count, a captured error). Never a substitute for
   *  the honest status itself. */
  detail?: string
  outbox_id?: string
}

export interface WriteTurnDurableArgs {
  message: CanonicalMessage
  parts: readonly MessagePartInput[]
  /** Required for outbox mode; ignored in direct mode (no DB port needed to
   *  call `writeTurn` directly — it opens its own pool). */
  outboxDb?: OutboxDb
  chartId?: string
  turnId?: string
  /** Override for testing; defaults to the real flag read. */
  enabled?: boolean
  /** Override for testing; defaults to the real `writeTurn` (which opens a
   *  live pg pool — unusable in a unit test without a database). Injecting
   *  this is what makes the crash-recovery / degradation paths above
   *  testable without a database, per the P2-D brief's "build against an
   *  interface/stub for the persistence layer" instruction. */
  writeTurnFn?: (message: CanonicalMessage, parts: readonly MessagePartInput[]) => Promise<WriteTurnResult>
}

export interface WriteTurnDurableResult {
  /** Null when the canonical write itself failed — mirrors the existing
   *  `canonicalOk = false` handling in persistence_stage.ts. */
  result: WriteTurnResult | null
  durable: DurableWriteOutcome
  /** Rethrown here, never inside this function — callers keep their existing
   *  try/catch discipline around the canonical write. */
  error?: unknown
}

export async function writeTurnDurable(args: WriteTurnDurableArgs): Promise<WriteTurnDurableResult> {
  const { message, parts, outboxDb, chartId, turnId } = args
  const enabled = args.enabled ?? isDurablePersistenceEnabled()
  const doWrite = args.writeTurnFn ?? writeTurn

  if (!enabled) {
    return directWrite(message, parts, doWrite)
  }

  if (!outboxDb || !chartId || !turnId) {
    // Flag says outbox, but the caller didn't wire the port (e.g. an
    // in-progress rollout, or a call site that hasn't been updated). Degrade
    // to direct rather than throwing — a missing PORT is exactly as
    // unavailable as a missing TABLE from this function's point of view.
    const direct = await directWrite(message, parts, doWrite)
    direct.durable.detail = 'outbox_port_not_supplied'
    return direct
  }

  let outboxId: string
  try {
    outboxId = await writeAheadTurn(
      {
        message_id: message.id,
        conversation_id: message.conversation_id,
        chart_id: chartId,
        turn_id: turnId,
        message,
        parts,
      },
      outboxDb,
    )
  } catch (err) {
    // Pre-migration (or any other write-ahead failure): never break a live
    // reading over durability plumbing. Degrade honestly.
    console.warn(
      '[pariprashna] durable_writer: write-ahead failed, degrading to direct write (non-fatal):',
      err,
    )
    const direct = await directWrite(message, parts, doWrite)
    direct.durable.detail = 'outbox_unavailable'
    return direct
  }

  try {
    const result = await doWrite(message, parts)
    await markPersistenceApplied(outboxId, outboxDb)
    return { result, durable: { status: 'durable', mode: 'outbox', outbox_id: outboxId } }
  } catch (err) {
    // The write-ahead entry survives (status stays 'pending') so a recovery
    // sweep can retry it — this is NOT a lost turn, it is an honestly
    // reported incomplete one.
    try {
      await markPersistenceFailed(outboxId, err, outboxDb)
    } catch (markErr) {
      console.warn('[pariprashna] durable_writer: failed to record write-ahead failure (non-fatal):', markErr)
    }
    return {
      result: null,
      durable: { status: 'pending', mode: 'outbox', outbox_id: outboxId, detail: 'canonical_write_failed_retryable' },
      error: err,
    }
  }
}

async function directWrite(
  message: CanonicalMessage,
  parts: readonly MessagePartInput[],
  doWrite: (message: CanonicalMessage, parts: readonly MessagePartInput[]) => Promise<WriteTurnResult>,
): Promise<WriteTurnDurableResult> {
  try {
    const result = await doWrite(message, parts)
    return { result, durable: { status: 'durable', mode: 'direct' } }
  } catch (err) {
    return { result: null, durable: { status: 'failed', mode: 'direct' }, error: err }
  }
}
