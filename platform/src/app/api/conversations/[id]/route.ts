import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import {
  getConversation,
  updateConversationTitle,
} from '@/lib/conversations'
import { archiveConversation, loadConversationMessagesV2 } from '@/lib/persistence/conversation_writer'
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

    const messages = await loadConversationMessagesV2(id)
    return Response.json({ conversation: conv, messages })
  } catch {
    return res.dbError()
  }
}

export async function PATCH(req: Request, ctx: { params: Promise<{ id: string }> }) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: {
    title?: string
    pinned?: boolean
    archived?: boolean
    folder_id?: string | null
  }
  try {
    body = await req.json()
  } catch {
    return res.badRequest('invalid body')
  }

  try {
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    if (!conv) return res.notFound('conversation')

    // Title update (existing behaviour)
    if (typeof body.title === 'string') {
      const title = body.title.trim().slice(0, 120)
      if (!title) return res.badRequest('title required')
      await updateConversationTitle(id, title)
      return Response.json({ ok: true, title })
    }

    // Pin / unpin
    if (typeof body.pinned === 'boolean') {
      await query('UPDATE conversations SET pinned=$1, updated_at=now() WHERE id=$2', [body.pinned, id])
      return Response.json({ ok: true, pinned: body.pinned })
    }

    // Archive / unarchive
    if (typeof body.archived === 'boolean') {
      if (body.archived) {
        await query("UPDATE conversations SET archived_at=now(), updated_at=now() WHERE id=$1", [id])
      } else {
        await query('UPDATE conversations SET archived_at=NULL, updated_at=now() WHERE id=$1', [id])
      }
      return Response.json({ ok: true, archived: body.archived })
    }

    // Move to folder or remove from folder
    if ('folder_id' in body) {
      if (body.folder_id === null || body.folder_id === undefined) {
        await query('DELETE FROM conversation_folder_members WHERE conversation_id=$1', [id])
      } else {
        // Upsert: one folder per conversation (PK is conversation_id)
        await query(
          `INSERT INTO conversation_folder_members (conversation_id, folder_id)
           VALUES ($1, $2)
           ON CONFLICT (conversation_id) DO UPDATE SET folder_id=EXCLUDED.folder_id, added_at=now()`,
          [id, body.folder_id]
        )
      }
      return Response.json({ ok: true, folder_id: body.folder_id ?? null })
    }

    return res.badRequest('no recognized field to update')
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
