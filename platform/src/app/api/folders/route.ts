import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import type { ConversationFolder } from '@/types/folders'

export async function GET() {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  try {
    const { rows } = await query<{
      id: string
      user_id: string
      name: string
      color: string
      created_at: string
      updated_at: string
    }>(
      `SELECT id, user_id, name, color, created_at, updated_at
       FROM conversation_folders
       WHERE user_id = $1
       ORDER BY created_at DESC`,
      [user.uid]
    )

    const folders: ConversationFolder[] = rows.map(row => ({
      id: row.id,
      userId: row.user_id,
      name: row.name,
      color: row.color,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
    }))

    return Response.json({ folders })
  } catch {
    return res.dbError()
  }
}

export async function POST(req: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: { name?: string; color?: string }
  try {
    body = await req.json()
  } catch {
    return res.badRequest('invalid body')
  }

  const name = (body.name ?? '').trim()
  if (!name) return res.badRequest('name required')
  if (name.length > 80) return res.badRequest('name too long')

  const color = body.color ?? '#6366f1'

  try {
    const { rows } = await query<ConversationFolder>(
      `INSERT INTO conversation_folders (user_id, name, color)
       VALUES ($1, $2, $3)
       RETURNING id, user_id, name, color, created_at, updated_at`,
      [user.uid, name, color]
    )

    const folder = rows[0]
    if (!folder) return res.internal('insert failed')

    return Response.json({ folder }, { status: 201 })
  } catch {
    return res.dbError()
  }
}
