import 'server-only'
/**
 * Canonical turn writer — PB-2 (SMṚTI) lane M-1.
 *
 * Persists a pariprashna turn as a conversation_messages row PLUS its
 * kind-typed message_parts rows, in a SINGLE transaction. This is the write
 * half of the M-1 DAL; the route is NOT wired to it here (that is lane M-2, the
 * persistence seam). Legacy `parts_json` is not touched: the canonical row sets
 * the additive columns (schema_version/model_id/provider) and lets parts_json
 * default to '[]'.
 *
 * Idempotency (CLAUDE.md §N.3 L1+): a rebuild of a turn REPLACES its parts —
 * `writeTurn` deletes any existing parts for the message id before inserting the
 * new set, and upserts the message row by id. Re-running with the same logical
 * content yields the same persisted state (bar DB-assigned part ids/created_at,
 * which are excluded from the canonical serialization by design).
 */

import { getPool } from '@/lib/db/client'
import {
  CanonicalMessageSchema,
  CANONICAL_SCHEMA_VERSION,
  MessagePartInputSchema,
  parsePartContent,
  type CanonicalMessage,
  type MessagePartInput,
} from './schema'

export interface WriteTurnResult {
  message_id: string
  parts_written: number
}

/**
 * Insert (or replace) a canonical turn: one conversation_messages row + all its
 * seq-ordered message_parts, atomically.
 *
 * - Validates the message row and every part body (per-kind Zod) BEFORE opening
 *   the transaction, so a malformed part can never leave a half-written turn.
 * - Runs the message upsert + parts delete-then-insert inside BEGIN/COMMIT on a
 *   single dedicated client; any failure ROLLBACKs the whole turn.
 *
 * @param message the conversation_messages row (identity + additive columns)
 * @param parts   the parts to persist; order is normalized by `seq` on read,
 *                but callers should pass contiguous seqs starting at 0
 */
export async function writeTurn(
  message: CanonicalMessage,
  parts: readonly MessagePartInput[],
): Promise<WriteTurnResult> {
  // 1. Validate the message row (throws on bad shape).
  const msg = CanonicalMessageSchema.parse(message)

  // 2. Validate every part: envelope shape AND per-kind body shape. Collect the
  //    validated bodies so we serialize the parsed (canonical) body, not raw input.
  const validatedParts = parts.map((raw) => {
    const p = MessagePartInputSchema.parse(raw)
    const content = parsePartContent(p.kind, p.body)
    return { seq: p.seq, kind: content.kind, body: content.body, model_visible: p.model_visible }
  })

  const pool = await getPool()
  const client = await pool.connect()
  try {
    await client.query('BEGIN')

    // Upsert the message row. schema_version is stamped from the constant so an
    // out-of-range caller value cannot desync the row from the code contract.
    await client.query(
      `INSERT INTO conversation_messages
         (id, conversation_id, parent_message_id, role, metadata_json, schema_version, model_id, provider)
       VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8)
       ON CONFLICT (id) DO UPDATE SET
         conversation_id   = EXCLUDED.conversation_id,
         parent_message_id = EXCLUDED.parent_message_id,
         role              = EXCLUDED.role,
         metadata_json     = EXCLUDED.metadata_json,
         schema_version    = EXCLUDED.schema_version,
         model_id          = EXCLUDED.model_id,
         provider          = EXCLUDED.provider`,
      [
        msg.id,
        msg.conversation_id,
        msg.parent_message_id ?? null,
        msg.role,
        JSON.stringify(msg.metadata ?? {}),
        CANONICAL_SCHEMA_VERSION,
        msg.model_id,
        msg.provider,
      ],
    )

    // Delete-then-insert the parts for this message (rebuild REPLACES).
    await client.query('DELETE FROM message_parts WHERE message_id = $1', [msg.id])

    for (const p of validatedParts) {
      await client.query(
        `INSERT INTO message_parts (message_id, seq, kind, body, model_visible)
         VALUES ($1, $2, $3, $4::jsonb, $5)`,
        [msg.id, p.seq, p.kind, JSON.stringify(p.body), p.model_visible],
      )
    }

    await client.query('COMMIT')
    return { message_id: msg.id, parts_written: validatedParts.length }
  } catch (err) {
    await client.query('ROLLBACK')
    throw err
  } finally {
    client.release()
  }
}
