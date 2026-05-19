import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { getConversation } from '@/lib/conversations'
import { res } from '@/lib/errors/errors'
import type { ConversationBranch } from '@/types/branches'

async function resolveAccess(userId: string) {
  const result = await query<{ role: string }>(
    'SELECT role FROM profiles WHERE id=$1',
    [userId]
  )
  return result.rows[0]?.role === 'super_admin'
}

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  try {
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    if (!conv) return res.notFound('conversation')

    const { rows } = await query<{
      id: string
      conversation_id: string
      edited_message_id: string
      parent_branch_id: string | null
      snapshot_jsonb: Record<string, unknown>
      created_at: string
    }>(
      `SELECT id, conversation_id, edited_message_id, parent_branch_id, snapshot_jsonb, created_at
       FROM conversation_branches
       WHERE conversation_id = $1
       ORDER BY created_at DESC`,
      [id]
    )

    const branches: ConversationBranch[] = rows.map(row => ({
      id: row.id,
      conversationId: row.conversation_id,
      editedMessageId: row.edited_message_id,
      parentBranchId: row.parent_branch_id,
      snapshotJsonb: row.snapshot_jsonb ?? {},
      createdAt: row.created_at,
    }))

    return Response.json({ branches })
  } catch {
    return res.dbError()
  }
}

export async function POST(
  req: Request,
  ctx: { params: Promise<{ id: string }> }
) {
  const { id } = await ctx.params
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: {
    edited_message_id?: string
    snapshot_jsonb?: Record<string, unknown>
    parent_branch_id?: string | null
  }
  try {
    body = await req.json()
  } catch {
    return res.badRequest('invalid body')
  }

  if (typeof body.edited_message_id !== 'string' || !body.edited_message_id) {
    return res.badRequest('edited_message_id required')
  }

  try {
    const isSuperAdmin = await resolveAccess(user.uid)
    const conv = await getConversation({ id, userId: user.uid, isSuperAdmin })
    if (!conv) return res.notFound('conversation')

    const snapshotJsonb = body.snapshot_jsonb ?? {}
    const parentBranchId = body.parent_branch_id ?? null

    const { rows } = await query<{ id: string; created_at: string }>(
      `INSERT INTO conversation_branches
         (conversation_id, edited_message_id, parent_branch_id, snapshot_jsonb)
       VALUES ($1, $2, $3, $4)
       RETURNING id, created_at`,
      [id, body.edited_message_id, parentBranchId, JSON.stringify(snapshotJsonb)]
    )

    const created = rows[0]
    if (!created) return res.internal('insert failed')

    return Response.json({ id: created.id, created_at: created.created_at }, { status: 201 })
  } catch {
    return res.dbError()
  }
}
