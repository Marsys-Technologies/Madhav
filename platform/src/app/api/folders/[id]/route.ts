import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'

async function resolveFolder(folderId: string, userId: string) {
  const { rows } = await query<{ id: string; user_id: string }>(
    'SELECT id, user_id FROM conversation_folders WHERE id=$1',
    [folderId]
  )
  const folder = rows[0]
  if (!folder) return null
  if (folder.user_id !== userId) return null
  return folder
}

export async function PATCH(
  req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: { name?: string; color?: string }
  try {
    body = await req.json()
  } catch {
    return res.badRequest('invalid body')
  }

  try {
    const folder = await resolveFolder(id, user.uid)
    if (!folder) return res.notFound('folder')

    const updates: string[] = []
    const values: unknown[] = []
    let idx = 1

    if (typeof body.name === 'string') {
      const name = body.name.trim()
      if (!name || name.length > 80) return res.badRequest('invalid name')
      updates.push(`name = $${idx++}`)
      values.push(name)
    }
    if (typeof body.color === 'string') {
      updates.push(`color = $${idx++}`)
      values.push(body.color)
    }

    if (updates.length === 0) return res.badRequest('no fields to update')

    updates.push(`updated_at = now()`)
    values.push(id)

    await query(
      `UPDATE conversation_folders SET ${updates.join(', ')} WHERE id = $${idx}`,
      values
    )

    return Response.json({ ok: true })
  } catch {
    return res.dbError()
  }
}

export async function DELETE(
  _req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  try {
    const folder = await resolveFolder(id, user.uid)
    if (!folder) return res.notFound('folder')

    // CASCADE removes conversation_folder_members automatically.
    await query('DELETE FROM conversation_folders WHERE id=$1', [id])
    return Response.json({ ok: true })
  } catch {
    return res.dbError()
  }
}
