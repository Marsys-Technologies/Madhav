import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { adminAuth } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'
import { writeAuditLog } from '@/lib/admin/audit'

// Generates a Firebase password-reset link for the target user. Returns the
// link to the admin UI for copy-paste.
//
// TODO: wire SMTP so the link is automatically emailed instead of surfaced for
// manual copy. For v1, the admin shares the link directly with the user.
export async function POST(
  _request: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  const { id } = await ctx.params

  let rows: { email: string | null }[]
  try {
    const result = await query<{ email: string | null }>(
      'SELECT email FROM profiles WHERE id=$1',
      [id]
    )
    rows = result.rows
  } catch {
    return res.dbError()
  }
  const profile = rows[0] ?? null

  if (!profile?.email) {
    return res.notFound('User has no email on file.')
  }

  let link: string
  try {
    link = await adminAuth.generatePasswordResetLink(profile.email)
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Could not generate reset link.'
    return res.internal(message)
  }

  await writeAuditLog(auth.user.uid, 'reset_password', id, { email: profile.email })
  return NextResponse.json({ ok: true, reset_link: link })
}
