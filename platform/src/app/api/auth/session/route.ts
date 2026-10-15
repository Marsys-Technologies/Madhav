import { NextResponse } from 'next/server'
import { createSessionCookie, adminAuth, getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res, errorResponse } from '@/lib/errors'

// Sign-in refusals the login page must tell apart. Same envelope as every other
// route (`error.code` + `error.message`); the snake_case marker the login page
// branches on travels in `error.detail`.
function refuse(marker: 'email_not_verified' | 'account_pending' | 'account_inactive') {
  const spec = {
    email_not_verified: ['AUTH_EMAIL_NOT_VERIFIED', 'Please verify your email address first.'],
    account_pending: ['AUTH_ACCOUNT_PENDING', 'Your account is waiting for approval.'],
    account_inactive: ['AUTH_ACCOUNT_INACTIVE', 'Your account is not active.'],
  } as const
  const [code, message] = spec[marker]
  return errorResponse(code, message, 403, { detail: marker, retry: false })
}

const SESSION_DURATION_MS = 60 * 60 * 24 * 14 * 1000 // 14 days

export async function POST(request: Request) {
  let idToken: string | undefined
  try {
    const body = await request.json()
    idToken = body?.idToken
  } catch {
    return res.badRequest('invalid request body')
  }
  if (!idToken) return res.badRequest('idToken required')

  let decoded
  try {
    decoded = await adminAuth.verifyIdToken(idToken, true)
  } catch {
    return res.unauthenticated()
  }

  let profile: { id: string; role: 'super_admin' | 'guest'; status: 'pending' | 'active' | 'disabled'; username?: string | null } | null
  try {
    const { rows: existing } = await query<{ id: string; role: 'super_admin' | 'guest'; status: 'pending' | 'active' | 'disabled'; username?: string | null }>(
      'SELECT id, role, status, username FROM profiles WHERE id=$1',
      [decoded.uid]
    )
    profile = existing[0] ?? null
  } catch {
    return res.dbError()
  }

  if (profile) {
    if (profile.status !== 'active') {
      return refuse(profile.status === 'pending' ? 'account_pending' : 'account_inactive')
    }
  } else {
    // No profile yet. Nothing below may run for an unverified or email-less
    // identity: no row is created and no role is elevated.
    const tokenEmail = typeof decoded.email === 'string' ? decoded.email.trim() : ''
    if (decoded.email_verified !== true || !tokenEmail) {
      return refuse('email_not_verified')
    }
    // Disaster-recovery path only (the seeded super admin already has a
    // profile). An unset/blank SUPER_ADMIN_EMAIL never matches anything.
    const adminEmail = (process.env.SUPER_ADMIN_EMAIL ?? '').trim().toLowerCase()
    const isSuperAdmin = adminEmail !== '' && tokenEmail.toLowerCase() === adminEmail
    const role = isSuperAdmin ? 'super_admin' : 'guest'
    const status = isSuperAdmin ? 'active' : 'pending'
    try {
      await query(
        'INSERT INTO profiles (id, role, status, name, email) VALUES ($1,$2,$3,$4,$5) ON CONFLICT (id) DO NOTHING',
        [decoded.uid, role, status, decoded.name ?? null, tokenEmail]
      )
    } catch (insertErr) {
      // 23505: another profile already owns this email (lower(email) unique
      // index). The person is known but this sign-in is not approved.
      if ((insertErr as { code?: string } | null)?.code === '23505') {
        return refuse('account_pending')
      }
      console.error('[session] profile insert failed', insertErr)
      return res.internal('profile sync failed')
    }
    if (!isSuperAdmin) return refuse('account_pending')
  }

  let sessionCookie: string
  try {
    sessionCookie = await createSessionCookie(idToken, SESSION_DURATION_MS)
  } catch {
    return res.internal('session cookie creation failed')
  }

  const response = NextResponse.json({ ok: true, username_setup_required: !profile?.username })
  response.cookies.set('__session', sessionCookie, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: SESSION_DURATION_MS / 1000,
    path: '/',
  })
  return response
}

export async function DELETE() {
  // V3-E-017: revoke the session server-side (not just clear the cookie
  // client-side) so a captured `__session` cookie value can't outlive a
  // "logout" for the rest of its 14-day TTL. `getServerUser()` resolves the
  // uid via the same `__session` cookie + `verifySessionCookie()` path the
  // rest of the app uses; `verifySessionCookie()`'s `checkRevoked: true` flag
  // then rejects this exact cookie value on the very next request.
  try {
    const user = await getServerUser()
    if (user?.uid) {
      await adminAuth.revokeRefreshTokens(user.uid)
    }
  } catch (err) {
    // Logging out of a session that's already gone/invalid, or a transient
    // Firebase error, is not an error the caller should see — the cookie is
    // cleared below regardless.
    console.error('[session] revokeRefreshTokens failed', err)
  }

  const response = NextResponse.json({ ok: true })
  response.cookies.set('__session', '', {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 0,
    path: '/',
  })
  return response
}
