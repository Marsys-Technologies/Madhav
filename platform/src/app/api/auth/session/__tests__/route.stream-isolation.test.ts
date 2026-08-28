/**
 * Proof for Pariprashna V3 A4 (distinct per-stream test principals).
 *
 * Root cause this guards against: during the Pariprashna Experience Assurance
 * campaign, every assurance stream (S1, S2, S5, ...) minted sessions for the
 * SAME shared Firebase UID (`hunQRYVJ5Ec2mQnJnutK7AoQnsO2`,
 * `A2_CREDENTIAL_LANE_OUTCOME_v1_0.md`). `DELETE /api/auth/session`'s logout
 * handler (V3-E-017 fix, see `route.revocation.test.ts`) calls Firebase
 * Admin's `revokeRefreshTokens(uid)`, which is UID-scoped: it invalidates
 * EVERY session cookie ever issued for that uid, not just the caller's own
 * cookie. When stream S5 ran its session-revocation security drill against
 * the shared uid, it silently revoked stream S2's still-active click-through
 * session too, because both were — unbeknownst to either — the same
 * principal.
 *
 * The fix (this session, `mint_stream_test_principal.ts`) is test-
 * infrastructure provisioning, not a change to production auth semantics:
 * give each stream its own distinct Firebase UID (its own `chart_grants` row
 * on the synthetic chart, same shape as the three pre-existing test
 * principals that already coexist on it). This test proves the isolation
 * property that capability rests on, using the same Firebase Admin
 * simulator pattern as `route.revocation.test.ts` (which proves the
 * single-principal revocation behavior this test's control case reuses),
 * extended to two independent principals:
 *
 *   1. Two distinct principals (representing two streams) each authenticate
 *      and can operate independently (their cookies resolve to their own,
 *      distinct uid).
 *   2. One principal's logout/revocation drill revokes ONLY that principal's
 *      uid — the other principal's cookie remains valid afterward.
 *   3. (Control, mirroring the existing V3-E-017 test) reusing the SAME uid
 *      for both "streams" reproduces the original collision — the second
 *      cookie for that shared uid is also revoked. This is what actually
 *      happened to S2, and is why distinct principals are the fix, not a
 *      change to revocation semantics.
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

// Two distinct per-stream test principals, exactly as
// `mint_stream_test_principal.ts` would derive them from STREAM_ID.
const UID_S2 = 'pariprashna-test-s2'
const UID_S5 = 'pariprashna-test-s5'
const COOKIE_S2 = 'fake-session-cookie-s2'
const COOKIE_S5 = 'fake-session-cookie-s5'

/**
 * Minimal Firebase Admin simulator, extended from `route.revocation.test.ts`
 * to track revocation PER UID (as the real Firebase Admin SDK does) rather
 * than a single global revoked flag — that generalization is exactly what
 * distinguishes "isolated" from "collided" in the tests below.
 */
const cookieToUid: Record<string, string> = {
  [COOKIE_S2]: UID_S2,
  [COOKIE_S5]: UID_S5,
}
let revokedUids: Set<string>
/** Which uid `getServerUser()` should currently resolve as ("logged in as"). */
let currentServerUid: string | null

function installSimulator() {
  revokedUids = new Set()
  currentServerUid = null

  mockVerifySessionCookie.mockImplementation(async (cookie: string) => {
    const uid = cookieToUid[cookie]
    if (!uid) throw new Error('invalid session cookie')
    if (revokedUids.has(uid)) throw new Error('Firebase ID token has been revoked')
    return { uid }
  })

  mockGetServerUser.mockImplementation(async () => {
    if (currentServerUid === null) return null
    if (revokedUids.has(currentServerUid)) return null
    return { uid: currentServerUid }
  })

  mockRevokeRefreshTokens.mockImplementation(async (uid: string) => {
    revokedUids.add(uid)
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  installSimulator()
})

describe('distinct per-stream test principals are isolated under revocation (Pariprashna V3 A4)', () => {
  it('two distinct stream principals each authenticate to their own uid', async () => {
    await expect(mockVerifySessionCookie(COOKIE_S2)).resolves.toEqual({ uid: UID_S2 })
    await expect(mockVerifySessionCookie(COOKIE_S5)).resolves.toEqual({ uid: UID_S5 })
  })

  it("stream S5's logout/security drill revokes ONLY S5's uid — S2's session survives", async () => {
    // S5 is "logged in" as its own distinct principal when it runs its
    // logout / session-revocation drill.
    currentServerUid = UID_S5
    const res = await DELETE()
    expect(res.status).toBe(200)
    expect(mockRevokeRefreshTokens).toHaveBeenCalledWith(UID_S5)
    expect(mockRevokeRefreshTokens).not.toHaveBeenCalledWith(UID_S2)

    // S5's own captured cookie is now correctly rejected...
    await expect(mockVerifySessionCookie(COOKIE_S5)).rejects.toThrow()

    // ...but S2's independent, still-active click-through session is
    // completely unaffected. This is the property the shared-principal
    // setup violated and that broke S2's mid-run test.
    await expect(mockVerifySessionCookie(COOKIE_S2)).resolves.toEqual({ uid: UID_S2 })
  })

  it("stream S2 can independently operate (mint, act, and later revoke its own session) with zero interference from S5's drill", async () => {
    // Run S5's drill first.
    currentServerUid = UID_S5
    await DELETE()
    expect(mockVerifySessionCookie(COOKIE_S2)).resolves.toEqual({ uid: UID_S2 })

    // S2 continues operating normally post-drill...
    await expect(mockVerifySessionCookie(COOKIE_S2)).resolves.toEqual({ uid: UID_S2 })

    // ...and can still run its OWN logout independently, which revokes only
    // its own uid.
    currentServerUid = UID_S2
    const res = await DELETE()
    expect(res.status).toBe(200)
    expect(mockRevokeRefreshTokens).toHaveBeenCalledWith(UID_S2)
    await expect(mockVerifySessionCookie(COOKIE_S2)).rejects.toThrow()
  })

  it('CONTROL — reproduces the original defect: reusing the SAME uid for two "streams" means one drill revokes both', async () => {
    // This mirrors the pre-fix reality: both "streams" mint against the one
    // shared uid `hunQRYVJ5Ec2mQnJnutK7AoQnsO2` documented in
    // A2_CREDENTIAL_LANE_OUTCOME_v1_0.md.
    const SHARED_UID = 'shared-legacy-test-principal'
    const cookieA = 'shared-cookie-stream-a'
    const cookieB = 'shared-cookie-stream-b'
    cookieToUid[cookieA] = SHARED_UID
    cookieToUid[cookieB] = SHARED_UID

    // Both cookies are valid and resolve to the same uid (they're really the
    // same underlying session identity, just captured at different times).
    await expect(mockVerifySessionCookie(cookieA)).resolves.toEqual({ uid: SHARED_UID })
    await expect(mockVerifySessionCookie(cookieB)).resolves.toEqual({ uid: SHARED_UID })

    // "Stream A" runs its security drill / logs out.
    currentServerUid = SHARED_UID
    await DELETE()

    // Both cookies are now dead — including "stream B"'s, which never asked
    // to be logged out. This is the exact collision that blocked S2.
    await expect(mockVerifySessionCookie(cookieA)).rejects.toThrow()
    await expect(mockVerifySessionCookie(cookieB)).rejects.toThrow()
  })
})
