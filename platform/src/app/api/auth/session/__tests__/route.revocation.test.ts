/**
 * Regression test for V3-E-017 (Paripraśna assurance, security/privacy stream S5).
 *
 * Before the fix, `DELETE /api/auth/session` (the logout endpoint) only cleared
 * the `__session` cookie client-side (`maxAge: 0`) — it never called Firebase
 * Admin's `revokeRefreshTokens(uid)`. The session cookie carries a 14-day TTL
 * (`SESSION_DURATION_MS`), so if a `__session` cookie value were ever captured
 * (XSS, stolen device, log leak, etc.), "logging out" did NOT invalidate that
 * captured cookie server-side — it stayed valid for up to 14 days.
 *
 * The underlying verification path is already wired correctly to respect
 * revocation: `verifySessionCookie()` calls `getAdminAuth().verifySessionCookie(
 * cookie, true)` — the `true` is Firebase's `checkRevoked` flag. The gap was
 * purely that nothing ever triggered a revocation.
 *
 * This test proves the gap end-to-end using a Firebase Admin SDK simulator: a
 * session cookie is valid, DELETE is called to "log out", and the SAME cookie
 * value must then be rejected by `verifySessionCookie` — which only happens if
 * DELETE actually resolved the caller's uid and called `revokeRefreshTokens`.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const {
  mockGetServerUser,
  mockVerifySessionCookie,
  mockRevokeRefreshTokens,
} = vi.hoisted(() => ({
  mockGetServerUser: vi.fn(),
  mockVerifySessionCookie: vi.fn(),
  mockRevokeRefreshTokens: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({
  getServerUser: mockGetServerUser,
  verifySessionCookie: mockVerifySessionCookie,
  createSessionCookie: vi.fn(),
  adminAuth: {
    revokeRefreshTokens: mockRevokeRefreshTokens,
  },
}))

import { DELETE } from '../route'

const SESSION_COOKIE = 'fake-session-cookie-value'
const UID = 'user-123'

/**
 * Minimal Firebase Admin simulator: tracks whether `revokeRefreshTokens(uid)`
 * has been called and makes `verifySessionCookie` reject the same cookie
 * value afterward — exactly the `checkRevoked: true` semantics the real
 * Firebase Admin SDK implements.
 */
let revoked: boolean

beforeEach(() => {
  vi.clearAllMocks()
  revoked = false

  mockVerifySessionCookie.mockImplementation(async (cookie: string) => {
    if (cookie !== SESSION_COOKIE) throw new Error('invalid session cookie')
    if (revoked) throw new Error('Firebase ID token has been revoked')
    return { uid: UID }
  })

  mockGetServerUser.mockImplementation(async () => {
    if (revoked) return null
    return { uid: UID }
  })

  mockRevokeRefreshTokens.mockImplementation(async (uid: string) => {
    if (uid === UID) revoked = true
  })
})

describe('DELETE /api/auth/session — V3-E-017 server-side revocation on logout', () => {
  it('the session cookie is valid before logout', async () => {
    await expect(mockVerifySessionCookie(SESSION_COOKIE)).resolves.toEqual({ uid: UID })
  })

  it('logout revokes the resolved uid server-side via Firebase Admin', async () => {
    const res = await DELETE()
    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ ok: true })
    expect(mockRevokeRefreshTokens).toHaveBeenCalledWith(UID)
  })

  it('the SAME captured cookie value is rejected by verifySessionCookie after logout', async () => {
    await DELETE()
    await expect(mockVerifySessionCookie(SESSION_COOKIE)).rejects.toThrow()
  })

  it('the SAME captured cookie value is rejected by getServerUser after logout', async () => {
    await DELETE()
    await expect(mockGetServerUser()).resolves.toBeNull()
  })

  it('still clears the __session cookie client-side (additive, not a replacement)', async () => {
    const res = await DELETE()
    const setCookie = res.headers.get('set-cookie') ?? ''
    expect(setCookie).toContain('__session=')
    expect(setCookie).toMatch(/Max-Age=0/i)
  })

  it('gracefully no-ops when there is no session to revoke (already logged out)', async () => {
    mockGetServerUser.mockResolvedValueOnce(null)
    const res = await DELETE()
    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ ok: true })
    expect(mockRevokeRefreshTokens).not.toHaveBeenCalled()
  })

  it('still returns ok:true even if revokeRefreshTokens itself throws', async () => {
    mockGetServerUser.mockResolvedValueOnce({ uid: UID })
    mockRevokeRefreshTokens.mockRejectedValueOnce(new Error('firebase unavailable'))
    const res = await DELETE()
    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ ok: true })
  })
})
