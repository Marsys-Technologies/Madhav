import { getServerUser } from '@/lib/firebase/server'
import { listConversations, createConversation } from '@/lib/conversations'
import { res } from '@/lib/errors'
import type { ConversationModule } from '@/lib/db/types'

export async function GET(request: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const url = new URL(request.url)
  const chartId = url.searchParams.get('chartId')
  const moduleParam = url.searchParams.get('module') ?? 'consume'
  // archived=false by default — hide archived conversations
  const includeArchived = url.searchParams.get('archived') === 'true'
  if (!chartId) return res.badRequest('chartId required')

  let conversations
  try {
    conversations = await listConversations({
      chartId,
      userId: user.uid,
      module: moduleParam as ConversationModule,
      includeArchived,
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
