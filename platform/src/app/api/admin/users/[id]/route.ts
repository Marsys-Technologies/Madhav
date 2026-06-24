import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { adminAuth } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { validateUsername } from '@/lib/auth/username'
import { res } from '@/lib/errors'
import { writeAuditLog } from '@/lib/admin/audit'

interface PatchBody {
  username?: string
  status?: 'active' | 'disabled'
  role?: 'super_admin' | 'guest'
}

export async function PATCH(
  request: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  const { id } = await ctx.params
  if (id === auth.user.uid) {
    return res.badRequest("You can't modify your own account from the admin panel.")
  }

  // Verify the user exists and capture current role before attempting any update.
  let currentRole: string | undefined
  try {
    const { rows: existing } = await query<{ id: string; role: string }>(
      'SELECT id, role FROM profiles WHERE id=$1',
      [id]
    )
    if (existing.length === 0) return res.notFound('user')
    currentRole = existing[0].role
  } catch (err) {
    console.error('[admin/users/[id]] PATCH existence-check failed', err)
    return res.dbError()
  }

  let body: PatchBody
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid request body')
  }

  const setClauses: string[] = []
  const values: unknown[] = []
  let idx = 1

  if (typeof body.username === 'string') {
    const username = body.username.trim().toLowerCase()
    const error = validateUsername(username)
    if (error) return res.badRequest(error)
    setClauses.push(`username=$${idx++}`)
    values.push(username)
  }

  const statusChanged = body.status === 'active' || body.status === 'disabled'
  if (statusChanged) {
    setClauses.push(`status=$${idx++}`)
    values.push(body.status)
  }

  const newRole = body.role === 'super_admin' || body.role === 'guest' ? body.role : undefined
  if (newRole && newRole !== currentRole) {
    // Guard: never demote the last super_admin.
    if (currentRole === 'super_admin' && newRole === 'guest') {
      try {
        const { rows: admins } = await query<{ cnt: string }>(
          "SELECT count(*)::text AS cnt FROM profiles WHERE role='super_admin'"
        )
        if (parseInt(admins[0]?.cnt ?? '0', 10) <= 1) {
          return res.badRequest('Cannot demote the last super admin.')
        }
      } catch (err) {
        console.error('[admin/users/[id]] PATCH super-admin count check failed', err)
        return res.dbError()
      }
    }
    setClauses.push(`role=$${idx++}`)
    values.push(newRole)
  }

  if (setClauses.length === 0) {
    return res.badRequest('Nothing to update.')
  }

  setClauses.push(`updated_at=now()`)
  values.push(id)

  // DB write first — keeps the profiles table as the source of truth.
  // Firebase update follows only after the DB commit succeeds.
  try {
    await query(
      `UPDATE profiles SET ${setClauses.join(', ')} WHERE id=$${idx}`,
      values
    )
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Update failed.'
    return res.internal(message)
  }

  if (statusChanged) {
    try {
      await adminAuth.updateUser(id, { disabled: body.status === 'disabled' })
    } catch (err: unknown) {
      // DB is already committed; log the divergence but return success so the
      // UI reflects the correct profile state. Firebase sync can be recovered
      // manually or on next sign-in.
      console.error('[admin/users/[id]] PATCH: DB committed but Firebase sync failed', err)
    }
    const action = body.status === 'disabled' ? 'disable_user' : 'enable_user'
    await writeAuditLog(auth.user.uid, action, id)
  }

  if (typeof body.username === 'string') {
    await writeAuditLog(auth.user.uid, 'edit_username', id, {
      new_username: body.username.trim().toLowerCase(),
    })
  }

  if (newRole && newRole !== currentRole) {
    await writeAuditLog(auth.user.uid, 'role_change', id, {
      from_role: currentRole,
      to_role: newRole,
    })
  }

  return NextResponse.json({ ok: true })
}

export async function DELETE(
  _request: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  const { id } = await ctx.params
  if (id === auth.user.uid) {
    return res.badRequest("You can't delete your own account.")
  }

  // Firebase delete first; if it fails, we leave the profile row alone.
  try {
    await adminAuth.deleteUser(id)
  } catch (err: unknown) {
    const code = (err as { code?: string })?.code
    // user-not-found means Firebase already lost the row — proceed to clean up profile.
    if (code !== 'auth/user-not-found') {
      const message = err instanceof Error ? err.message : 'Firebase delete failed.'
      return res.internal(message)
    }
  }

  // Capture name/email before the row is gone.
  let deletedName: string | null = null
  let deletedEmail: string | null = null
  try {
    const { rows: profile } = await query<{ name: string | null; email: string | null }>(
      'SELECT name, email FROM profiles WHERE id=$1',
      [id],
    )
    if (profile[0]) { deletedName = profile[0].name; deletedEmail = profile[0].email }
  } catch { /* non-fatal */ }

  try {
    await query('DELETE FROM profiles WHERE id=$1', [id])
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Delete failed.'
    return res.internal(message)
  }

  await writeAuditLog(auth.user.uid, 'delete_user', null, {
    deleted_user_id: id,
    name: deletedName,
    email: deletedEmail,
  })

  return NextResponse.json({ ok: true })
}
