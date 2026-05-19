import { getServerUser } from '@/lib/firebase/server'
import { listProjects, createProject } from '@/lib/projects'
import { res } from '@/lib/errors'

export async function GET() {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  try {
    const projects = await listProjects(user.uid)
    return Response.json({ projects })
  } catch {
    return res.dbError()
  }
}

export async function POST(request: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: { name?: string; system_prompt_addition?: string; chart_id?: string }
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid body')
  }

  if (!body.name || typeof body.name !== 'string' || body.name.trim().length === 0) {
    return res.badRequest('name required')
  }

  try {
    const project = await createProject({
      userId: user.uid,
      name: body.name.trim(),
      systemPromptAddition: body.system_prompt_addition ?? null,
      chartId: body.chart_id ?? null,
    })
    return Response.json({ project }, { status: 201 })
  } catch {
    return res.dbError()
  }
}
