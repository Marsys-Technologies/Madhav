import 'server-only'
import type { UIMessage } from 'ai'
import { query } from '@/lib/db/client'
import { embedConversationMessage } from '@/lib/embeddings/embedConversationMessage'

export interface WriteConversationMessagesParams {
  conversationId: string
  messages: UIMessage[]
  /** metadata_json to attach to the LAST assistant message (cost, model, tokens, etc.) */
  lastAssistantMetadata?: Record<string, unknown>
}

export interface WriteConversationMessagesResult {
  /** IDs of the written conversation_message rows, in order */
  messageIds: string[]
  /**
   * Whether read-after-write verification passed — i.e. whether EVERY id this call
   * claims to have written is actually readable back from `conversation_messages`
   * under this `conversation_id`.
   *
   * SAMĀPTI A7-N8-AUDIT F-24: this used to be `dbCount >= messageIds.length` where
   * `dbCount` was an UNFILTERED `COUNT(*) ... WHERE conversation_id = $1`. That count
   * includes every message from every prior turn, so on any conversation past its first
   * turn the comparison held by construction and `verified: true` was unreachable-false —
   * it could not detect the very thing it was named for. (The inline comment conceded the
   * `>=` had been loosened to compensate for exactly that pollution.) It is now scoped to
   * the ids in question, so it tests its own claim.
   */
  verified: boolean
  /**
   * The ids this call wrote that did NOT read back. Empty iff `verified`. Populated
   * rather than merely counted so a caller/operator can act on the specific rows — an
   * honest gap surfaced, never a bare false (B.10).
   */
  missingMessageIds: string[]
}

/**
 * Write-through persistence for Chat V2 conversation messages.
 *
 * Strategy: upsert each UIMessage by its stable AI SDK `id` into
 * `conversation_messages` so the operation is idempotent on reconnect/retry.
 * After writing, performs an ID-SCOPED read-after-write check: every id this call
 * claims to have written must read back. (F-24 — it was formerly an unfiltered
 * per-conversation `COUNT(*)` comparison that held by construction; see
 * `WriteConversationMessagesResult.verified`.)
 */
export async function writeConversationMessages(
  params: WriteConversationMessagesParams,
): Promise<WriteConversationMessagesResult> {
  const { conversationId, messages, lastAssistantMetadata } = params
  if (messages.length === 0) {
    return { messageIds: [], verified: true, missingMessageIds: [] }
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
    const messageId = rows[0]?.id
    if (messageId) {
      messageIds.push(messageId)
      // Non-blocking embed: extract first text part for embedding; errors are swallowed.
      const textPart = (m.parts ?? []).find(
        (p): p is { type: 'text'; text: string } => (p as { type: string }).type === 'text',
      )
      if (textPart?.text) {
        Promise.resolve().then(() =>
          embedConversationMessage(messageId, textPart.text).catch((err) => {
            console.error('[embed] conversation_message embed failed', messageId, err)
          }),
        )
      }
    }
  }

  // ── Read-after-write, ID-SCOPED (SAMĀPTI A7-N8-AUDIT F-24) ────────────────────────
  // Previously: `SELECT COUNT(*) ... WHERE conversation_id = $1` compared with `>=`
  // against `messageIds.length`. That count is polluted by every message from every
  // prior turn of the same conversation, so on turn 2 onward the inequality held no
  // matter what happened to THIS turn's rows — the check could not fail, and the `>=`
  // was itself the loosening introduced to keep the polluted count from tripping it.
  //
  // Now: select back exactly the ids we claim to have written, under the same
  // conversation_id, and require every one of them to be present. This is the check the
  // field name always promised. A partially-failed write is now visible, and the
  // specific missing ids are returned rather than collapsed into a bare boolean.
  const uniqueWrittenIds = Array.from(new Set(messageIds))
  const { rows: presentRows } = await query<{ id: string }>(
    `SELECT id FROM conversation_messages
      WHERE conversation_id = $1 AND id = ANY($2::uuid[])`,
    [conversationId, uniqueWrittenIds],
  )
  const presentIds = new Set(presentRows.map(r => r.id))
  const missingMessageIds = uniqueWrittenIds.filter(id => !presentIds.has(id))
  const verified = missingMessageIds.length === 0
  if (!verified) {
    console.error(
      '[conversation_writer] read-after-write verification FAILED for conversation %s — ' +
      '%d of %d written ids did not read back: %s',
      conversationId, missingMessageIds.length, uniqueWrittenIds.length,
      missingMessageIds.join(', '),
    )
  }

  return { messageIds, verified, missingMessageIds }
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
