import { NextResponse } from 'next/server'
import { createSessionCookie, adminAuth, getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'
import { res } from '@/lib/errors'

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
    decoded = await adminAuth.verifyIdToken(idToken)
  } catch {
    return res.unauthenticated()
  }

  let profile: { id: string; role: 'super_admin' | 'guest'; status: 'pending' | 'active' | 'disabled' } | null
  try {
    const { rows: existing } = await query<{ id: string; role: 'super_admin' | 'guest'; status: 'pending' | 'active' | 'disabled' }>(
      'SELECT id, role, status FROM profiles WHERE id=$1',
      [decoded.uid]
    )
    profile = existing[0] ?? null
  } catch {
    return res.dbError()
  }

  if (profile) {
    if (profile.status !== 'active') {
      return res.forbidden()
    }
  } else {
    const role =
      decoded.email && decoded.email === process.env.SUPER_ADMIN_EMAIL
        ? 'super_admin'
        : 'guest'
    try {
      await query(
        'INSERT INTO profiles (id, role, status, name, email) VALUES ($1,$2,$3,$4,$5) ON CONFLICT (id) DO NOTHING',
        [decoded.uid, role, 'active', decoded.name ?? null, decoded.email ?? null]
      )
    } catch (insertErr) {
      console.error('[session] profile insert failed', insertErr)
      return res.internal('profile sync failed')
    }
  }

  let sessionCookie: string
  try {
    sessionCookie = await createSessionCookie(idToken, SESSION_DURATION_MS)
  } catch {
    return res.internal('session cookie creation failed')
  }

  const response = NextResponse.json({ ok: true })
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
