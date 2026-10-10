/**
 * S8 (audit finding 7): a sign-in with no profile must never become an active
 * account by itself. Verified email + revocation check are required, a new
 * verified user lands PENDING (no cookie), and SUPER_ADMIN promotion needs a
 * non-empty configured email that matches a VERIFIED token email exactly.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  verifyIdToken: vi.fn(),
  createSessionCookie: vi.fn(),
  query: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(),
  createSessionCookie: mocks.createSessionCookie,
  adminAuth: { verifyIdToken: mocks.verifyIdToken, revokeRefreshTokens: vi.fn() },
}))
vi.mock('@/lib/db/client', () => ({ query: mocks.query }))

import { POST } from '../route'

const idCredential = 'id-credential-fixture'
const request = () =>
  new Request('http://localhost/api/auth/session', {
    method: 'POST',
    body: JSON.stringify({ idToken: idCredential }),
  })

type Profile = { id: string; role: string; status: string; username?: string | null }
let existingProfile: Profile | null
let insertError: unknown

const inserts = () => mocks.query.mock.calls.filter(([sql]) => String(sql).includes('INSERT INTO profiles'))
const savedAdminEmail = process.env.SUPER_ADMIN_EMAIL

beforeEach(() => {
  vi.resetAllMocks()
  existingProfile = null
  insertError = null
  process.env.SUPER_ADMIN_EMAIL = 'admin@x.com'
  mocks.createSessionCookie.mockResolvedValue('cookie-fixture')
  mocks.query.mockImplementation(async (sql: string) => {
    if (sql.includes('SELECT id, role, status')) return { rows: existingProfile ? [existingProfile] : [] }
    if (sql.includes('INSERT INTO profiles')) {
      if (insertError) throw insertError
      return { rows: [] }
    }
    throw new Error(`unexpected sql: ${sql}`)
  })
})

afterEach(() => {
  if (savedAdminEmail === undefined) delete process.env.SUPER_ADMIN_EMAIL
  else process.env.SUPER_ADMIN_EMAIL = savedAdminEmail
})

describe('POST /api/auth/session sign-up approval', () => {
  it('checks revocation: verifyIdToken is called with (credential, true)', async () => {
    mocks.verifyIdToken.mockResolvedValue({ uid: 'u1', email: 'a@b.com', email_verified: true })
    await POST(request())
    expect(mocks.verifyIdToken).toHaveBeenCalledWith(idCredential, true)
  })

  it('unverified email + no profile -> 403 email_not_verified, no INSERT, no cookie', async () => {
    mocks.verifyIdToken.mockResolvedValue({ uid: 'u1', email: 'a@b.com', email_verified: false })
    const response = await POST(request())
    expect(response.status).toBe(403)
    expect((await response.json()).error.detail).toBe('email_not_verified')
    expect(inserts()).toHaveLength(0)
    expect(mocks.createSessionCookie).not.toHaveBeenCalled()
    expect(response.headers.get('set-cookie')).toBeNull()
  })

  it('verified email + no profile -> INSERT as pending guest, 403 account_pending, no cookie', async () => {
    mocks.verifyIdToken.mockResolvedValue({ uid: 'u1', email: 'a@b.com', email_verified: true, name: 'A B' })
    const response = await POST(request())
    expect(response.status).toBe(403)
    expect((await response.json()).error.detail).toBe('account_pending')
    expect(inserts()).toHaveLength(1)
    expect(inserts()[0][1]).toEqual(['u1', 'guest', 'pending', 'A B', 'a@b.com'])
    expect(mocks.createSessionCookie).not.toHaveBeenCalled()
    expect(response.headers.get('set-cookie')).toBeNull()
  })

  it('verified admin email with stray case/space -> active super_admin and a cookie', async () => {
    mocks.verifyIdToken.mockResolvedValue({ uid: 'root', email: ' Admin@X.com ', email_verified: true })
    const response = await POST(request())
    expect(response.status).toBe(200)
    expect(inserts()).toHaveLength(1)
    expect(inserts()[0][1].slice(0, 3)).toEqual(['root', 'super_admin', 'active'])
    expect(response.headers.get('set-cookie')).toContain('__session=')
  })

  it('unverified admin email -> no promotion, no INSERT, no cookie', async () => {
    mocks.verifyIdToken.mockResolvedValue({ uid: 'root', email: 'admin@x.com', email_verified: false })
    const response = await POST(request())
    expect(response.status).toBe(403)
    expect(inserts()).toHaveLength(0)
    expect(mocks.createSessionCookie).not.toHaveBeenCalled()
  })

  it('SUPER_ADMIN_EMAIL unset and a credential without an email never promotes', async () => {
    delete process.env.SUPER_ADMIN_EMAIL
    mocks.verifyIdToken.mockResolvedValue({ uid: 'u2', email_verified: true })
    const response = await POST(request())
    expect(response.status).toBe(403)
    expect((await response.json()).error.detail).toBe('email_not_verified')
    expect(inserts()).toHaveLength(0)
    expect(mocks.createSessionCookie).not.toHaveBeenCalled()
  })

  it('SUPER_ADMIN_EMAIL blank never matches a verified user', async () => {
    process.env.SUPER_ADMIN_EMAIL = '   '
    mocks.verifyIdToken.mockResolvedValue({ uid: 'u3', email: 'a@b.com', email_verified: true })
    const response = await POST(request())
    expect(response.status).toBe(403)
    expect(inserts()[0][1].slice(0, 3)).toEqual(['u3', 'guest', 'pending'])
  })

  it('existing pending profile -> 403 account_pending, no INSERT, no cookie', async () => {
    existingProfile = { id: 'u1', role: 'guest', status: 'pending' }
    mocks.verifyIdToken.mockResolvedValue({ uid: 'u1', email: 'a@b.com', email_verified: true })
    const response = await POST(request())
    expect(response.status).toBe(403)
    expect((await response.json()).error.detail).toBe('account_pending')
    expect(inserts()).toHaveLength(0)
    expect(mocks.createSessionCookie).not.toHaveBeenCalled()
  })

  it('existing disabled profile -> 403 account_inactive', async () => {
    existingProfile = { id: 'u1', role: 'guest', status: 'disabled' }
    mocks.verifyIdToken.mockResolvedValue({ uid: 'u1', email: 'a@b.com', email_verified: true })
    const response = await POST(request())
    expect(response.status).toBe(403)
    expect((await response.json()).error.detail).toBe('account_inactive')
  })

  it('existing active profile keeps working even with an unverified email (admin-created accounts)', async () => {
    existingProfile = { id: 'u1', role: 'guest', status: 'active', username: 'alice' }
    mocks.verifyIdToken.mockResolvedValue({ uid: 'u1', email: 'a@b.com', email_verified: false })
    const response = await POST(request())
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ ok: true, username_setup_required: false })
    expect(response.headers.get('set-cookie')).toContain('__session=')
    expect(inserts()).toHaveLength(0)
  })

  it('active profile without a username still reports username_setup_required', async () => {
    existingProfile = { id: 'u1', role: 'guest', status: 'active', username: null }
    mocks.verifyIdToken.mockResolvedValue({ uid: 'u1', email: 'a@b.com', email_verified: true })
    const response = await POST(request())
    expect((await response.json()).username_setup_required).toBe(true)
  })

  it('duplicate-email unique violation (23505) -> 403 account_pending, not a 500, no cookie', async () => {
    insertError = Object.assign(new Error('duplicate key'), { code: '23505' })
    mocks.verifyIdToken.mockResolvedValue({ uid: 'u9', email: 'a@b.com', email_verified: true })
    const response = await POST(request())
    expect(response.status).toBe(403)
    expect((await response.json()).error.detail).toBe('account_pending')
    expect(mocks.createSessionCookie).not.toHaveBeenCalled()
  })

  it('other insert failures stay a 500', async () => {
    insertError = new Error('connection lost')
    mocks.verifyIdToken.mockResolvedValue({ uid: 'u9', email: 'a@b.com', email_verified: true })
    vi.spyOn(console, 'error').mockImplementation(() => {})
    expect((await POST(request())).status).toBe(500)
  })

  it('a revoked or invalid credential -> 401', async () => {
    mocks.verifyIdToken.mockRejectedValue(new Error('revoked'))
    expect((await POST(request())).status).toBe(401)
  })
})
