import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { getConversation } from '@/lib/conversations'
import { loadConversationMessagesV2 } from '@/lib/persistence/conversation_writer'
import { res } from '@/lib/errors'

async function resolveAccess(userId: string): Promise<boolean> {
  const result = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [userId],
  )
  return result.rows[0]?.role === 'super_admin'
}

/**
 * GET /api/conversations/[id]/messages
 *
 * Returns the Chat V2 conversation messages from `conversation_messages` table.
 * Used by ConsumeChatV2 to restore conversation state on mount.
 */
export async function GET(
  _req: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  try {
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    if (!conv) return res.notFound('conversation')

    const messages = await loadConversationMessagesV2(id)
    return Response.json({ messages })
  } catch {
    return res.dbError()
  }
}
