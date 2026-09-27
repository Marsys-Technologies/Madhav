import 'server-only'
import { query } from '@/lib/db/client'

/**
 * Reader-safe transcript for a historical (correction-archived) conversation
 * (Jātaka chart workspace, Task 8).
 *
 * Returns only what a reader saw: user and assistant text. Canonical
 * `message_parts` of kind 'text' are preferred (in seq order); legacy rows fall
 * back to `{ type: 'text', text: string }` entries of `parts_json`. Reasoning,
 * tool calls and results, provider payloads and message metadata are never
 * selected or returned. Messages with no reader-visible text are dropped.
 */
export interface HistoricalTranscriptMessage {
  id: string
  role: 'user' | 'assistant'
  text: string
  createdAt: string
}

type MessageRow = { id: string; role: 'user' | 'assistant'; parts_json: unknown; created_at: string }
type PartRow = { message_id: string; seq: number; text: string | null }

function legacyText(parts: unknown): string {
  if (!Array.isArray(parts)) return ''
  return parts
    .filter(
      (part): part is { type: 'text'; text: string } =>
        typeof part === 'object' && part !== null && (part as { type?: unknown }).type === 'text' &&
        typeof (part as { text?: unknown }).text === 'string',
    )
    .map((part) => part.text)
    .join('')
}

export async function loadHistoricalConversationMessages(conversationId: string): Promise<HistoricalTranscriptMessage[]> {
  const { rows: messages } = await query<MessageRow>(
    `SELECT id, role, parts_json, created_at
       FROM conversation_messages
      WHERE conversation_id = $1 AND role IN ('user', 'assistant')
      ORDER BY created_at, id`,
    [conversationId],
  )
  if (messages.length === 0) return []

  const { rows: parts } = await query<PartRow>(
    `SELECT message_id, seq, body->>'text' AS text
       FROM message_parts
      WHERE message_id = ANY($1::uuid[]) AND kind = 'text'
      ORDER BY message_id, seq`,
    [messages.map((message) => message.id)],
  )
  const canonical = new Map<string, string>()
  for (const part of [...parts].sort((a, b) => a.seq - b.seq)) {
    if (typeof part.text !== 'string') continue
    canonical.set(part.message_id, (canonical.get(part.message_id) ?? '') + part.text)
  }

  return messages
    .map((message) => ({
      id: message.id,
      role: message.role,
      text: canonical.get(message.id) || legacyText(message.parts_json),
      createdAt: message.created_at,
    }))
    .filter((message) => message.text.trim().length > 0)
}
