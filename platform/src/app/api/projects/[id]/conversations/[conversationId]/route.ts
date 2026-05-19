import { getServerUser } from '@/lib/firebase/server'
import { removeConversationFromProject, verifyProjectOwnership } from '@/lib/projects'
import { res } from '@/lib/errors'

interface RouteParams { params: Promise<{ id: string; conversationId: string }> }

export async function DELETE(_req: Request, { params }: RouteParams) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const { id, conversationId } = await params

  try {
    const project = await verifyProjectOwnership(id, user.uid)
    if (!project) return res.notFound('project')
    await removeConversationFromProject(id, conversationId)
    return new Response(null, { status: 204 })
  } catch {
    return res.dbError()
  }
}
