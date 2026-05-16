import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import {
  getConversation,
  loadConversationMessages,
  updateConversationTitle,
} from '@/lib/conversations'
import { archiveConversation } from '@/lib/persistence/conversation_writer'
import { res } from '@/lib/errors'

async function resolveAccess(userId: string) {
  const result = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [userId]
  )
  return result.rows[0]?.role === 'super_admin'
}

export async function GET(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  try {
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    if (!conv) return res.notFound('conversation')

    const messages = await loadConversationMessages(id)
    return Response.json({ conversation: conv, messages })
  } catch {
    return res.dbError()
  }
}

export async function PATCH(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: { title?: string }
  try {
    body = await req.json()
  } catch {
    return res.badRequest('invalid body')
  }
  if (typeof body.title !== 'string') {
    return res.badRequest('title required')
  }
  const title = body.title.trim().slice(0, 120)
  if (!title) return res.badRequest('title required')

  try {
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    if (!conv) return res.notFound('conversation')

    await updateConversationTitle(id, title)
    return Response.json({ ok: true, title })
  } catch {
    return res.dbError()
  }
}

export async function DELETE(_req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  try {
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    if (!conv) return res.notFound('conversation')

    // Soft delete: set archived_at. The conversation row and its messages are preserved.
    await archiveConversation(id)
    return Response.json({ ok: true })
  } catch {
    return res.dbError()
  }
}
