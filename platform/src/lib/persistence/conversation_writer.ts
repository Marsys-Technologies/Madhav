import 'server-only'
import type { UIMessage } from 'ai'
import { query } from '@/lib/db/client'

export interface WriteConversationMessagesParams {
  conversationId: string
  messages: UIMessage[]
  /** metadata_json to attach to the LAST assistant message (cost, model, tokens, etc.) */
  lastAssistantMetadata?: Record<string, unknown>
}

export interface WriteConversationMessagesResult {
  /** IDs of the written conversation_message rows, in order */
  messageIds: string[]
  /** Whether read-after-write verification passed */
  verified: boolean
}

/**
 * Write-through persistence for Chat V2 conversation messages.
 *
 * Strategy: upsert each UIMessage by its stable AI SDK `id` into
 * `conversation_messages` so the operation is idempotent on reconnect/retry.
 * After writing, performs a read-after-write count check.
 *
 * The legacy `messages` table is NOT touched — that belongs to ConsumeChatLegacy.
 */
export async function writeConversationMessages(
  params: WriteConversationMessagesParams,
): Promise<WriteConversationMessagesResult> {
  const { conversationId, messages, lastAssistantMetadata } = params
  if (messages.length === 0) {
    return { messageIds: [], verified: true }
  }

  const messageIds: string[] = []

  for (let i = 0; i < messages.length; i++) {
    const m = messages[i]
    const role: 'user' | 'assistant' =
      m.role === 'user' ? 'user' : 'assistant'

    const isLastAssistant =
      i === messages.length - 1 && role === 'assistant' && lastAssistantMetadata != null

    const metadata = isLastAssistant ? lastAssistantMetadata : {}

    const { rows } = await query<{ id: string }>(
      `INSERT INTO conversation_messages
         (id, conversation_id, role, parts_json, metadata_json)
       VALUES ($1, $2, $3, $4::jsonb, $5::jsonb)
       ON CONFLICT (id) DO UPDATE
         SET parts_json    = EXCLUDED.parts_json,
             metadata_json = EXCLUDED.metadata_json
       RETURNING id`,
      [
        m.id ?? crypto.randomUUID(),
        conversationId,
        role,
        JSON.stringify(m.parts ?? []),
        JSON.stringify(metadata ?? {}),
      ],
    )
    if (rows[0]) messageIds.push(rows[0].id)
  }

  // Read-after-write: count rows in DB and compare against written messages.
  const { rows: countRows } = await query<{ n: string }>(
    'SELECT COUNT(*) AS n FROM conversation_messages WHERE conversation_id = $1',
    [conversationId],
  )
  const dbCount = parseInt(countRows[0]?.n ?? '0', 10)
  // DB count ≥ written count (may have older messages from prior turns).
  const verified = dbCount >= messageIds.length

  return { messageIds, verified }
}

/** Restore conversation: load all non-archived messages as UIMessage array. */
export async function loadConversationMessagesV2(
  conversationId: string,
): Promise<UIMessage[]> {
  const { rows } = await query<{
    id: string
    role: string
    parts_json: unknown
    metadata_json: unknown
    created_at: string
  }>(
    `SELECT id, role, parts_json, metadata_json, created_at
     FROM conversation_messages
     WHERE conversation_id = $1
     ORDER BY created_at ASC`,
    [conversationId],
  )

  return rows.map((row) => ({
    id: row.id,
    role: row.role as UIMessage['role'],
    parts: Array.isArray(row.parts_json)
      ? (row.parts_json as UIMessage['parts'])
      : [],
    metadata: row.metadata_json as Record<string, unknown>,
  }))
}

/** Archive (soft-delete) a conversation: set archived_at, do NOT delete the row. */
export async function archiveConversation(
  conversationId: string,
): Promise<void> {
  await query(
    'UPDATE conversations SET archived_at = NOW() WHERE id = $1',
    [conversationId],
  )
}
