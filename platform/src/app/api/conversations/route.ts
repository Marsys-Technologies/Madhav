import { getServerUser } from '@/lib/firebase/server'
import { listConversations, createConversation } from '@/lib/conversations'
import { authorizeChartAccess } from '@/lib/auth/authorizeChartAccess'
import type { DbLike } from '@/lib/auth/authorizeChartAccess'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import type { ConversationModule } from '@/lib/db/types'

/**
 * S1-F-001 (Paripraśna v3 assurance, stream S1): before this check existed,
 * neither GET nor POST verified the caller held any `chart_grants`/ownership
 * for the caller-supplied `chartId` — a user could create and list
 * conversation rows scoped to a chart they had zero entitlement to. Routes
 * through the same `authorizeChartAccess` brain already used by
 * `GET /api/charts/[id]` and the `cockpit`/`mcp` surface. A `view` grant is
 * sufficient (creating/listing a conversation shell is read-adjacent, not
 * destructive — unlike the cockpit `clear` routes, which require `all`).
 */
async function resolveChartPermission(userId: string, chartId: string) {
  const profileResult = await query<{ role: string }>('SELECT role FROM profiles WHERE id=$1', [userId])
  const isSuperAdmin = profileResult.rows[0]?.role === 'super_admin'
  return authorizeChartAccess({
    principal: { uid: userId, role: isSuperAdmin ? 'super_admin' : 'guest' },
    chartId,
    db: { query: (sql: string, params?: unknown[]) => query(sql, params).then((r) => ({ rows: r.rows })) } as DbLike,
  })
}

export async function GET(request: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const url = new URL(request.url)
  const chartId = url.searchParams.get('chartId')
  const moduleParam = url.searchParams.get('module') ?? 'consume'
  // archived=false by default — hide archived conversations
  const includeArchived = url.searchParams.get('archived') === 'true'
  // V3-E-012a: opt-in only — see listConversations' readingsOnly docblock.
  // The default (false) keeps every existing caller (e.g. the consume
  // module's own ArchivedView.tsx) byte-identical to before this existed.
  const readingsOnly = url.searchParams.get('readingsOnly') === 'true'
  if (!chartId) return res.badRequest('chartId required')

  let conversations
  try {
    const permission = await resolveChartPermission(user.uid, chartId)
    if (permission === 'deny') return res.forbidden()

    conversations = await listConversations({
      chartId,
      userId: user.uid,
      module: moduleParam as ConversationModule,
      includeArchived,
      readingsOnly,
    })
  } catch {
    return res.dbError()
  }

  return Response.json({ conversations })
}

export async function POST(request: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: { chartId?: string; module?: string }
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid body')
  }

  const { chartId, module: moduleParam = 'consume' } = body
  if (!chartId) return res.badRequest('chartId required')

  try {
    const permission = await resolveChartPermission(user.uid, chartId)
    if (permission === 'deny') return res.forbidden()

    const conversation = await createConversation({
      chartId,
      userId: user.uid,
      module: moduleParam as ConversationModule,
    })
    return Response.json({ conversation }, { status: 201 })
  } catch {
    return res.dbError()
  }
}
