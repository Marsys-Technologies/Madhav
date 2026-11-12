import 'server-only'
import { query } from '@/lib/db/client'

interface ActiveConversationShare {
  slug: string
  created_at: string | null
  expires_at: string | null
  revoked_at: string | null
  hide_reasoning: boolean
  hide_methodology: boolean
}

/** Load active share metadata after the caller authorizes the conversation. */
export async function listActiveConversationShares(conversationId: string): Promise<ActiveConversationShare[]> {
  const { rows } = await query<ActiveConversationShare>(
    `SELECT slug, created_at, expires_at, revoked_at, hide_reasoning, hide_methodology FROM conversation_shares WHERE conversation_id=$1 AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now()) ORDER BY created_at DESC`,
    [conversationId],
  )
  return rows
}
