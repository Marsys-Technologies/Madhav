/**
 * Paripraśna durable conversation summaries — PB-2 (SMṚTI) lane M-3 — Postgres store.
 *
 * `PgSummaryStore` is the production `SummaryStore` (types.ts) implementation
 * backing migration 468's `conversation_summaries` table. Append-only: `insert`
 * always creates a new row; there is no update/delete path, matching migration
 * 468's comment (a summary row may already be cited by a downstream
 * grounding-gate check).
 *
 * Also exports `listCanonicalMessagesForConversation` — a narrow, read-only
 * helper this lane owns (NOT part of M-1's DAL, which only exports
 * single-message reads via `readCanonicalMessage`/`readTurnParts`). It queries
 * `conversation_messages` directly for canonical (schema_version IS NOT NULL)
 * rows ordered oldest-first, the ordering `getOrCreateSummary` needs to walk a
 * conversation's turns in sequence. This does not modify or duplicate M-1's
 * schema/DAL files — it is a plain additional SELECT against the same table
 * M-1 already writes to.
 */
import 'server-only'

import { query } from '@/lib/db/client'
import type { ConversationSummaryInsert, ConversationSummaryRow, SummaryStore } from './types'

interface ConversationSummaryDbRow {
  id: string
  conversation_id: string
  covers_through_message_id: string
  summary_text: string
  model_id: string | null
  created_at: string
}

export class PgSummaryStore implements SummaryStore {
  async findLatest(conversationId: string): Promise<ConversationSummaryRow | null> {
    const { rows } = await query<ConversationSummaryDbRow>(
      `SELECT id, conversation_id, covers_through_message_id, summary_text, model_id, created_at
         FROM conversation_summaries
        WHERE conversation_id = $1
        ORDER BY created_at DESC
        LIMIT 1`,
      [conversationId],
    )
    return rows[0] ?? null
  }

  async insert(row: ConversationSummaryInsert): Promise<ConversationSummaryRow> {
    const { rows } = await query<ConversationSummaryDbRow>(
      `INSERT INTO conversation_summaries
         (conversation_id, covers_through_message_id, summary_text, model_id)
       VALUES ($1, $2, $3, $4)
       RETURNING id, conversation_id, covers_through_message_id, summary_text, model_id, created_at`,
      [row.conversation_id, row.covers_through_message_id, row.summary_text, row.model_id],
    )
    return rows[0]
  }
}

/** A canonical (M-1 schema_version-stamped) message row's identity, ordered. */
export interface CanonicalMessageRef {
  id: string
  role: 'user' | 'assistant' | 'tool'
}

/**
 * List every CANONICAL message for a conversation (schema_version IS NOT
 * NULL — legacy parts_json-blob rows are excluded, matching M-1 reader.ts's
 * own "canonical rows only" discipline), oldest first.
 */
export async function listCanonicalMessagesForConversation(
  conversationId: string,
): Promise<CanonicalMessageRef[]> {
  const { rows } = await query<{ id: string; role: string }>(
    `SELECT id, role
       FROM conversation_messages
      WHERE conversation_id = $1
        AND schema_version IS NOT NULL
      ORDER BY created_at ASC`,
    [conversationId],
  )
  return rows.map((r) => ({ id: r.id, role: r.role as CanonicalMessageRef['role'] }))
}
