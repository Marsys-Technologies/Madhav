import { getServerUser } from '@/lib/firebase/server'
import { addConversationToProject, verifyProjectOwnership } from '@/lib/projects'
import { res } from '@/lib/errors'

interface RouteParams { params: Promise<{ id: string }> }

export async function POST(request: Request, { params }: RouteParams) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const { id } = await params

  let body: { conversation_id?: string }
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid body')
  }

  if (!body.conversation_id || typeof body.conversation_id !== 'string') {
    return res.badRequest('conversation_id required')
  }

  try {
    const project = await verifyProjectOwnership(id, user.uid)
    if (!project) return res.notFound('project')
    await addConversationToProject(id, body.conversation_id)
    return new Response(null, { status: 204 })
  } catch {
    return res.dbError()
  }
}
