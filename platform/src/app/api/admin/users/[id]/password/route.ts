import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { adminAuth } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { validatePassword } from '@/lib/auth/password'
import { res } from '@/lib/errors'
import { writeAuditLog } from '@/lib/admin/audit'

export async function POST(
  request: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  const { id } = await ctx.params

  if (id === auth.user.uid) {
    return res.badRequest("Use your account settings to change your own password.")
  }

  let body: { password?: string }
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid request body')
  }

  const pwError = validatePassword(body.password ?? '')
  if (pwError) return res.badRequest(pwError)

  let email: string | null = null
  try {
    const { rows } = await query<{ email: string | null }>(
      'SELECT email FROM profiles WHERE id=$1',
      [id],
    )
    if (rows.length === 0) return res.notFound('user')
    email = rows[0].email
  } catch {
    return res.dbError()
  }

  try {
    await adminAuth.updateUser(id, { password: body.password })
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Could not set password.'
    return res.internal(message)
  }

  await writeAuditLog(auth.user.uid, 'set_password', id, { email })
  return NextResponse.json({ ok: true })
}
