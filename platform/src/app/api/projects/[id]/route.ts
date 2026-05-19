import { getServerUser } from '@/lib/firebase/server'
import { getProject, updateProject, softDeleteProject, verifyProjectOwnership } from '@/lib/projects'
import { res } from '@/lib/errors'

interface RouteParams { params: Promise<{ id: string }> }

export async function GET(_req: Request, { params }: RouteParams) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const { id } = await params
  try {
    const project = await getProject(id, user.uid)
    if (!project) return res.notFound('project')
    return Response.json({ project })
  } catch {
    return res.dbError()
  }
}

export async function PATCH(request: Request, { params }: RouteParams) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const { id } = await params

  let body: Record<string, unknown>
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid body')
  }

  const ALLOWED = new Set(['name', 'system_prompt_addition', 'chart_id'])
  const unknown = Object.keys(body).filter(k => !ALLOWED.has(k))
  if (unknown.length > 0) return res.badRequest(`unknown fields: ${unknown.join(', ')}`)

  const updates: { name?: string; system_prompt_addition?: string | null; chart_id?: string | null } = {}
  if ('name' in body) {
    if (typeof body.name !== 'string' || body.name.trim().length === 0)
      return res.badRequest('name must be a non-empty string')
    updates.name = (body.name as string).trim()
  }
  if ('system_prompt_addition' in body) {
    updates.system_prompt_addition =
      body.system_prompt_addition === null ? null : String(body.system_prompt_addition)
  }
  if ('chart_id' in body) {
    updates.chart_id = body.chart_id === null ? null : String(body.chart_id)
  }

  try {
    const project = await updateProject(id, user.uid, updates)
    if (!project) return res.notFound('project')
    return Response.json({ project })
  } catch {
    return res.dbError()
  }
}

export async function DELETE(_req: Request, { params }: RouteParams) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const { id } = await params

  // Ownership check before delete
  try {
    const owned = await verifyProjectOwnership(id, user.uid)
    if (!owned) return res.notFound('project')
    await softDeleteProject(id, user.uid)
    return new Response(null, { status: 204 })
  } catch {
    return res.dbError()
  }
}
