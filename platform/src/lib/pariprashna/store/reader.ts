import 'server-only'
/**
 * Canonical turn reader — PB-2 (SMṚTI) lane M-1.
 *
 * Reads persisted canonical turns back out of the DB. The read half of the M-1
 * DAL. Returns parts ordered by `seq`, and the message row's canonical identity
 * + additive columns. Used by PB-2 lane M-2's byte-equality gate to reconstruct
 * the "persisted" view for comparison against the replayed event stream.
 */

import { query } from '@/lib/db/client'
import {
  parsePartContent,
  type CanonicalMessage,
  type MessageRole,
  type PersistedMessagePart,
} from './schema'

/**
 * Read all parts of a message, ordered by `seq` ascending. Each row's `body` is
 * re-validated against its per-kind schema on the way out — a stored row that
 * fails validation is a data-integrity bug (a write bypassing the DAL), surfaced
 * loudly rather than silently returned.
 */
export async function readTurnParts(messageId: string): Promise<PersistedMessagePart[]> {
  const { rows } = await query<{
    id: string
    message_id: string
    seq: number
    kind: string
    body: unknown
    model_visible: boolean
    created_at: string
  }>(
    `SELECT id, message_id, seq, kind, body, model_visible, created_at
       FROM message_parts
      WHERE message_id = $1
      ORDER BY seq ASC`,
    [messageId],
  )

  return rows.map((row) => {
    // Re-validate (kind, body); throws if a persisted row is malformed.
    const content = parsePartContent(row.kind, row.body)
    return {
      id: row.id,
      message_id: row.message_id,
      seq: row.seq,
      kind: content.kind,
      body: content.body,
      model_visible: row.model_visible,
      created_at: row.created_at,
    }
  })
}

/**
 * Read the canonical message row (identity + additive columns). Returns null if
 * the row does not exist or is a legacy row (schema_version IS NULL) — the
 * canonical reader deliberately does not resolve legacy blob rows.
 */
export async function readCanonicalMessage(messageId: string): Promise<CanonicalMessage | null> {
  const { rows } = await query<{
    id: string
    conversation_id: string
    parent_message_id: string | null
    role: string
    schema_version: number | null
    model_id: string | null
    provider: string | null
    metadata_json: unknown
  }>(
    `SELECT id, conversation_id, parent_message_id, role, schema_version, model_id, provider, metadata_json
       FROM conversation_messages
      WHERE id = $1`,
    [messageId],
  )

  const row = rows[0]
  if (!row) return null
  // Legacy rows (pre-M-1 blob rows) have NULL additive columns — not canonical.
  if (row.schema_version == null || row.model_id == null || row.provider == null) return null

  return {
    id: row.id,
    conversation_id: row.conversation_id,
    parent_message_id: row.parent_message_id ?? undefined,
    role: row.role as MessageRole,
    schema_version: row.schema_version,
    model_id: row.model_id,
    provider: row.provider,
    metadata: (row.metadata_json ?? {}) as Record<string, unknown>,
  }
}
