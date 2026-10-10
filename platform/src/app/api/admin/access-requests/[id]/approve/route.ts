import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { adminAuth } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { validateUsername } from '@/lib/auth/username'
import { res } from '@/lib/errors'
import { writeAuditLog } from '@/lib/admin/audit'

interface ApproveBody {
  username?: string
  role?: 'super_admin' | 'guest'
}

interface RequestRow {
  id: string
  full_name: string
  email: string
  status: 'pending' | 'approved' | 'rejected'
}

async function insertApprovedProfile(
  uid: string,
  req: RequestRow,
  username: string | null,
  role: 'super_admin' | 'guest',
  approverUid: string,
) {
  await query(
    'INSERT INTO profiles (id, role, status, name, username, email, approved_at, approved_by) VALUES ($1,\'guest\',\'active\',$2,$3,$4,now(),$5) ON CONFLICT (id) DO NOTHING',
    [uid, req.full_name, username, req.email, approverUid]
  )
  // Override role if super_admin was requested
  if (role === 'super_admin') {
    await query('UPDATE profiles SET role=$1 WHERE id=$2', ['super_admin', uid])
  }
}

export async function POST(
  request: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  const { id } = await ctx.params
  let body: ApproveBody
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid request body')
  }

  if (!body || typeof body !== 'object' || Array.isArray(body)) return res.badRequest('invalid request body')
  if (body.username != null && typeof body.username !== 'string') return res.badRequest('Invalid username.')
  // No username is reserved during a request; the approved user chooses it after sign-in.
  // Retain compatibility for existing admin callers that explicitly assign one.
  const username = body.username?.trim().toLowerCase() || null
  if (username) { const error = validateUsername(username); if (error) return res.badRequest(error) }

  const role = body.role === 'super_admin' ? 'super_admin' : 'guest'

  // 1. Load the request row.
  let reqRows: RequestRow[]
  try {
    const result = await query<RequestRow>(
      'SELECT id, full_name, email, status FROM access_requests WHERE id=$1',
      [id]
    )
    reqRows = result.rows
  } catch {
    return res.dbError()
  }
  const req = reqRows[0] ?? null
  if (!req) return res.notFound('not_found')
  if (req.status !== 'pending') {
    return res.conflict('Request is not pending.')
  }

  // 2. Who already exists for this email? An approved request must work for
  //    someone who already signed in (Firebase account, possibly a PENDING
  //    profile), not only for a brand-new address.
  type FirebaseUser = Awaited<ReturnType<typeof adminAuth.createUser>>
  let existingFirebase: FirebaseUser | null = null
  try {
    existingFirebase = await adminAuth.getUserByEmail(req.email)
  } catch (err: unknown) {
    if ((err as { code?: string } | null)?.code !== 'auth/user-not-found') {
      const message = err instanceof Error ? err.message : 'Could not look up user account.'
      return res.internal(message)
    }
  }

  let profileRows: { id: string; status: string }[]
  try {
    const result = await query<{ id: string; status: string }>(
      'SELECT id, status FROM profiles WHERE lower(email)=lower($1) OR id=$2',
      [req.email, existingFirebase?.uid ?? null]
    )
    profileRows = result.rows
  } catch {
    return res.dbError()
  }
  if (profileRows.some((p) => p.status === 'active')) {
    return res.conflict('An active account already exists for this email.')
  }
  const pendingProfile =
    profileRows.find((p) => p.status === 'pending' && p.id === existingFirebase?.uid) ?? null
  if (profileRows.length > 0 && !pendingProfile) {
    // A disabled profile (re-enable it from the Users tab) or a profile that
    // does not belong to the Firebase account for this email: do not guess.
    return res.conflict('A profile for this email exists but cannot be approved from here.')
  }

  // 3. Username uniqueness pre-check (the unique index will enforce too).
  //    Skipped when no username was given; ignores the profile being approved.
  if (username) {
    let dupRows: { id: string }[]
    try {
      const result = await query<{ id: string }>(
        'SELECT id FROM profiles WHERE lower(username)=lower($1) AND id IS DISTINCT FROM $2 LIMIT 1',
        [username, pendingProfile?.id ?? null]
      )
      dupRows = result.rows
    } catch {
      return res.dbError()
    }
    if (dupRows.length > 0) {
      return res.conflict('Username is already taken.')
    }
  }

  let uid: string
  let approvalPath: 'pending_profile' | 'firebase_user_only' | 'new_user'
  let hasPasswordProvider = false

  if (pendingProfile && existingFirebase) {
    // (a) The person already signed in and is waiting: approve that profile.
    uid = pendingProfile.id
    approvalPath = 'pending_profile'
    hasPasswordProvider = existingFirebase.providerData.some((p) => p.providerId === 'password')
    try {
      const sets = ['status=\'active\'', 'approved_at=now()', 'approved_by=$1', 'updated_at=now()']
      const values: unknown[] = [auth.user.uid]
      if (username) {
        values.push(username)
        sets.push(`username=$${values.length}`)
      }
      if (role === 'super_admin') sets.push('role=\'super_admin\'')
      values.push(uid)
      await query(`UPDATE profiles SET ${sets.join(', ')} WHERE id=$${values.length}`, values)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Could not approve profile.'
      return res.internal(message)
    }
  } else if (existingFirebase) {
    // (b) A Firebase account without a profile: create the profile, already approved.
    uid = existingFirebase.uid
    approvalPath = 'firebase_user_only'
    hasPasswordProvider = existingFirebase.providerData.some((p) => p.providerId === 'password')
    try {
      await insertApprovedProfile(uid, req, username, role, auth.user.uid)
    } catch (err) {
      if ((err as { code?: string } | null)?.code === '23505') {
        return res.conflict('Username or email is already in use.')
      }
      const message = err instanceof Error ? err.message : 'Could not create profile.'
      return res.internal(message)
    }
  } else {
    // (c) Neither exists. Create the Firebase user. Random password — they set their own via the reset link.
    let firebaseUser: FirebaseUser
    try {
      firebaseUser = await adminAuth.createUser({
        email: req.email,
        emailVerified: false,
        displayName: req.full_name,
      })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Could not create user account.'
      return res.internal(message)
    }

    // 4. Insert profile row. On conflict, roll back the Firebase user.
    uid = firebaseUser.uid
    approvalPath = 'new_user'
    try {
      await insertApprovedProfile(uid, req, username, role, auth.user.uid)
    } catch (err) {
      await adminAuth.deleteUser(uid).catch(() => {})
      const message = err instanceof Error ? err.message : 'Could not create profile.'
      return res.internal(message)
    }
  }

  // 5. Mark the request approved.
  try {
    await query(
      'UPDATE access_requests SET status=\'approved\', reviewed_at=now(), reviewed_by=$1, approved_user_id=$2 WHERE id=$3',
      [auth.user.uid, uid, id]
    )
  } catch {
    return res.internal('failed to mark request approved')
  }

  await writeAuditLog(auth.user.uid, 'approve_user', uid, {
    access_request_id: id,
    path: approvalPath,
  })

  // 6. Generate a password-reset link — only for someone who has no password yet.
  const resetLink = hasPasswordProvider
    ? null
    : await adminAuth
        .generatePasswordResetLink(req.email, { url: new URL('/setup-account', request.url).href })
        .catch(() => null)

  return NextResponse.json({ ok: true, user_id: uid, reset_link: resetLink })
}
