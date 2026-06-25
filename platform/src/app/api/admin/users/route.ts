import { NextResponse } from 'next/server'
import { requireSuperAdmin } from '@/lib/auth/access-control'
import { adminAuth } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { validateUsername } from '@/lib/auth/username'
import { validatePassword } from '@/lib/auth/password'
import { res } from '@/lib/errors'
import { writeAuditLog } from '@/lib/admin/audit'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

interface CreateBody {
  full_name?: string
  email?: string
  username?: string
  role?: 'super_admin' | 'guest'
  password?: string
}

export async function GET() {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  try {
    const { rows } = await query<{
      id: string
      role: string
      status: string
      name: string | null
      username: string | null
      email: string | null
      created_at: string
      approved_at: string | null
    }>(
      'SELECT id, role, status, name, username, email, created_at, approved_at FROM profiles ORDER BY created_at DESC'
    )
    return NextResponse.json({ users: rows })
  } catch (err) {
    console.error('[admin/users] GET failed', err)
    return res.internal('Failed to load users.')
  }
}

export async function POST(request: Request) {
  const auth = await requireSuperAdmin()
  if (auth instanceof NextResponse) return auth

  let body: CreateBody
  try {
    body = await request.json()
  } catch {
    return res.badRequest('invalid request body')
  }

  const fullName = (body.full_name ?? '').trim()
  const email = (body.email ?? '').trim().toLowerCase()
  const username = (body.username ?? '').trim().toLowerCase()
  const role = body.role === 'super_admin' ? 'super_admin' : 'guest'
  const password = typeof body.password === 'string' && body.password.length > 0
    ? body.password
    : undefined

  if (!fullName || fullName.length > 100) {
    return res.badRequest('Full name is required.')
  }
  if (!email || !EMAIL_RE.test(email)) {
    return res.badRequest('A valid email is required.')
  }
  const usernameError = validateUsername(username)
  if (usernameError) return res.badRequest(usernameError)
  if (password !== undefined) {
    const pwError = validatePassword(password)
    if (pwError) return res.badRequest(pwError)
  }

  // Duplicate email/username check
  let dupRows: { id: string }[]
  try {
    const result = await query<{ id: string }>(
      'SELECT id FROM profiles WHERE lower(email)=lower($1) OR lower(username)=lower($2) LIMIT 1',
      [email, username]
    )
    dupRows = result.rows
  } catch (err) {
    console.error('[admin/users] POST dup-check failed', err)
    return res.dbError()
  }
  if (dupRows.length > 0) {
    return res.conflict('A user with that email or username already exists.')
  }

  let firebaseUser: Awaited<ReturnType<typeof adminAuth.createUser>>
  try {
    firebaseUser = await adminAuth.createUser({
      email,
      emailVerified: false,
      displayName: fullName,
      ...(password !== undefined ? { password } : {}),
    })
  } catch (err: unknown) {
    // Firebase "email already exists" can mean either a real duplicate or an
    // orphaned Firebase account (profile INSERT previously failed after createUser
    // succeeded, leaving Firebase holding the email with no profile row).
    // Detect the orphan case: if Firebase owns the email but profiles doesn't,
    // delete the dangling Firebase account and retry.
    const code = (err as Record<string, unknown>)?.code
    if (code === 'auth/email-already-exists') {
      try {
        const { rows: existing } = await query<{ id: string }>(
          'SELECT id FROM profiles WHERE lower(email)=lower($1) LIMIT 1',
          [email]
        )
        if (existing.length === 0) {
          // Orphaned Firebase account — delete it and retry
          const orphan = await adminAuth.getUserByEmail(email)
          await adminAuth.deleteUser(orphan.uid)
          firebaseUser = await adminAuth.createUser({
            email,
            emailVerified: false,
            displayName: fullName,
            ...(password !== undefined ? { password } : {}),
          })
        } else {
          return res.conflict('A user with that email already exists.')
        }
      } catch (retryErr: unknown) {
        const message = retryErr instanceof Error ? retryErr.message : 'Could not create user account.'
        console.error('[admin/users] POST Firebase retry failed', retryErr)
        return res.internal(message)
      }
    } else {
      const message = err instanceof Error ? err.message : 'Could not create user account.'
      return res.internal(message)
    }
  }

  const uid = firebaseUser.uid
  let insertedUser: Record<string, unknown> | undefined
  let resetLink: string | null = null
  try {
    const { rows: inserted } = await query(
      'INSERT INTO profiles (id, role, status, name, username, email, approved_at, approved_by) VALUES ($1,$2,$3,$4,$5,$6,now(),$7) RETURNING *',
      [uid, role, 'active', fullName, username, email, auth.user.uid]
    )
    insertedUser = inserted[0]
    resetLink = await adminAuth.generatePasswordResetLink(email).catch(() => null)
  } catch (err) {
    console.error('[admin/users] POST profile INSERT failed', err)
    await adminAuth.deleteUser(uid).catch(() => {})
    const message = err instanceof Error ? err.message : 'Could not create profile.'
    return res.internal(message)
  }

  // Audit write is outside the Firebase-cleanup try/catch so a missing
  // admin_audit_log table (migration not yet run) never causes a 500 or
  // triggers spurious Firebase user deletion.
  await writeAuditLog(auth.user.uid, 'create_user', uid, { name: fullName, email, role, password_set: Boolean(password) })
  return NextResponse.json({ ok: true, user_id: uid, reset_link: password ? null : resetLink, user: insertedUser })
}
