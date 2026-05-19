import 'server-only'
import { query } from '@/lib/db/client'
import { embedText } from './embedText'

/**
 * Embed a single conversation message and persist to conversation_message_embeddings.
 * Called non-blocking after a message row is written; errors are swallowed so the
 * message save response is unaffected.
 */
export async function embedConversationMessage(
  messageId: string,
  text: string,
): Promise<void> {
  const embedding = await embedText(text)
  const vec = '[' + embedding.join(',') + ']'
  await query(
    `INSERT INTO conversation_message_embeddings (message_id, embedding)
     VALUES ($1, $2::vector)
     ON CONFLICT (message_id) DO UPDATE SET embedding = EXCLUDED.embedding`,
    [messageId, vec],
  )
}
