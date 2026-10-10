import 'server-only'
import { cookies } from 'next/headers'
import type { Auth } from 'firebase-admin/auth'
import { query } from '@/lib/db/client'

// Lazily initialise the Admin SDK so that build-time page-data collection
// (which imports this module) doesn't fail when credentials aren't set.
let _auth: Auth | null = null

function getAdminAuth(): Auth {
  if (_auth) return _auth
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { initializeApp, getApps, cert } = require('firebase-admin/app')
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { getAuth } = require('firebase-admin/auth')

  let serviceAccount: object = {}
  try {
    serviceAccount = JSON.parse(process.env.FIREBASE_ADMIN_CREDENTIALS ?? '{}')
  } catch {
    // credentials not yet configured; auth calls will fail at runtime
  }

  const app =
    getApps().length > 0
      ? getApps()[0]
      : initializeApp({ credential: cert(serviceAccount) })

  _auth = getAuth(app)
  return _auth!
}

export const adminAuth = new Proxy({} as Auth, {
  get(_target, prop) {
    return (getAdminAuth() as unknown as Record<string, unknown>)[prop as string]
  },
})

export async function verifySessionCookie(cookie: string) {
  return getAdminAuth().verifySessionCookie(cookie, true)
}

export async function createSessionCookie(idToken: string, expiresIn: number) {
  return getAdminAuth().createSessionCookie(idToken, { expiresIn })
}

/**
 * The signed-in user for the current request, or null.
 *
 * Two checks, in order:
 *   1. the `__session` cookie verifies with revocation (`verifySessionCookie`);
 *   2. the user's `profiles` row, WHEN ONE EXISTS, has `status = 'active'`.
 *
 * Why (2): a Firebase session cookie lives for up to 14 days and stays valid until
 * Firebase itself refuses it. Disabling a user in the admin console writes
 * `profiles.status` first and only then asks Firebase to disable the account (a
 * Firebase failure there is logged, not surfaced), so the cookie alone is not
 * proof the account is still allowed in. Almost every route and page authenticates
 * through this function and none of them looks at the status, so the status check
 * lives here, once, instead of in ~150 call sites. A pending or disabled profile
 * yields null, which every caller already maps to its own 401 / redirect to login.
 *
 * A user with NO profile row is returned exactly as before (the row is created by
 * the session route / approval flow, and some callers legitimately run before it
 * exists). A failed status lookup fails CLOSED (null).
 *
 * No cache, on purpose: the lookup is one primary-key read on `profiles`, small
 * next to the Firebase revocation round trip `verifySessionCookie(..., true)`
 * already makes on every call, and a cache would only reintroduce the staleness
 * window this check exists to remove (a disabled user would keep working for the
 * cache TTL).
 */
export async function getServerUser() {
  const cookieStore = await cookies()
  const session = cookieStore.get('__session')?.value
  if (!session) return null
  let decoded: Awaited<ReturnType<typeof verifySessionCookie>>
  try {
    decoded = await verifySessionCookie(session)
  } catch {
    return null
  }
  try {
    const { rows } = await query<{ status: string | null }>(
      'SELECT status FROM profiles WHERE id=$1',
      [decoded.uid]
    )
    const row = rows[0]
    if (row && row.status !== 'active') return null
  } catch (err) {
    console.error('[auth] profile status lookup failed; refusing session', err)
    return null
  }
  return decoded
}
