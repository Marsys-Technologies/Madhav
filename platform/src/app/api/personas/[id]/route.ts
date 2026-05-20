import { getServerUser } from '@/lib/firebase/server'
import { getPersona, updatePersona, deletePersona } from '@/lib/personas'
import { res } from '@/lib/errors'
import type { PersonaUpdate } from '@/types/personas'

interface RouteParams { params: Promise<{ id: string }> }

export async function PATCH(request: Request, { params }: RouteParams) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const { id } = await params

  // Ownership check
  const owned = await getPersona(id, user.uid)
  if (!owned) return res.forbidden()

  let body: PersonaUpdate
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid body')
  }

  const ALLOWED = new Set(['name', 'system_prompt', 'default_style', 'default_stack', 'is_default'])
  const unknown = Object.keys(body).filter(k => !ALLOWED.has(k))
  if (unknown.length > 0) return res.badRequest(`unknown fields: ${unknown.join(', ')}`)

  if (body.name !== undefined && (typeof body.name !== 'string' || body.name.trim().length === 0 || body.name.trim().length > 50))
    return res.validationFailed('name must be 1–50 chars')
  if (body.system_prompt !== undefined && (typeof body.system_prompt !== 'string' || body.system_prompt.trim().length === 0 || body.system_prompt.trim().length > 4000))
    return res.validationFailed('system_prompt must be 1–4000 chars')

  const updates: Parameters<typeof updatePersona>[2] = {}
  if (body.name !== undefined) updates.name = body.name.trim()
  if (body.system_prompt !== undefined) updates.system_prompt = body.system_prompt.trim()
  if ('default_style' in body) updates.default_style = body.default_style ?? null
  if ('default_stack' in body) updates.default_stack = body.default_stack ?? null
  if (body.is_default !== undefined) updates.is_default = body.is_default

  try {
    const persona = await updatePersona(id, user.uid, updates)
    if (!persona) return res.notFound('persona')
    return Response.json({ persona })
  } catch {
    return res.dbError()
  }
}

export async function DELETE(_req: Request, { params }: RouteParams) {
  const user = await getServerUser()
  if (!user) return res.unauthenticated()

  const { id } = await params

  const owned = await getPersona(id, user.uid)
  if (!owned) return res.forbidden()

  try {
    const result = await deletePersona(id, user.uid)
    if (result.lastPersona) {
      return Response.json({ error: 'cannot_delete_last_persona' }, { status: 409 })
    }
    if (!result.deleted) return res.notFound('persona')
    return new Response(null, { status: 204 })
  } catch {
    return res.dbError()
  }
}
