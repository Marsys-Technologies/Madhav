import { getServerUser } from '@/lib/firebase/server'
import { listPersonas, createPersona } from '@/lib/personas'
import { res } from '@/lib/errors'
import type { PersonaCreate } from '@/types/personas'

export async function GET() {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  try {
    const personas = await listPersonas(user.uid)
    return Response.json({ personas })
  } catch {
    return res.dbError()
  }
}

export async function POST(request: Request) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  let body: PersonaCreate
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid body')
  }

  if (!body.name || typeof body.name !== 'string' || body.name.trim().length === 0)
    return res.validationFailed('name required')
  if (body.name.trim().length > 50)
    return res.validationFailed('name must be 50 chars or fewer')
  if (!body.system_prompt || typeof body.system_prompt !== 'string' || body.system_prompt.trim().length === 0)
    return res.validationFailed('system_prompt required')
  if (body.system_prompt.trim().length > 4000)
    return res.validationFailed('system_prompt must be 4000 chars or fewer')

  try {
    const persona = await createPersona({
      userId: user.uid,
      name: body.name.trim(),
      systemPrompt: body.system_prompt.trim(),
      defaultStyle: body.default_style ?? null,
      defaultStack: body.default_stack ?? null,
      isDefault: body.is_default ?? false,
    })
    return Response.json({ persona }, { status: 201 })
  } catch {
    return res.dbError()
  }
}
