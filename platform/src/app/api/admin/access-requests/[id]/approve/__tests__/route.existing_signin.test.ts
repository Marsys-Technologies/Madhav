/**
 * S8: approving an access request must work for someone who already signed in
 * (a Firebase account, usually with a PENDING profile). Before, the route called
 * createUser() unconditionally, which fails with auth/email-already-exists.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  admin: vi.fn(),
  query: vi.fn(),
  getUserByEmail: vi.fn(),
  createUser: vi.fn(),
  deleteUser: vi.fn(),
  resetLink: vi.fn(),
  audit: vi.fn(),
}))

vi.mock('@/lib/auth/access-control', () => ({ requireSuperAdmin: mocks.admin }))
vi.mock('@/lib/firebase/server', () => ({
  adminAuth: {
    getUserByEmail: mocks.getUserByEmail,
    createUser: mocks.createUser,
    deleteUser: mocks.deleteUser,
    generatePasswordResetLink: mocks.resetLink,
  },
}))
vi.mock('@/lib/db/client', () => ({ query: mocks.query }))
vi.mock('@/lib/admin/audit', () => ({ writeAuditLog: mocks.audit }))

import { POST } from '../route'

const ctx = { params: Promise.resolve({ id: 'req-1' }) }
const call = (body: unknown = {}) =>
  POST(new Request('http://localhost/api/admin/access-requests/req-1/approve', { method: 'POST', body: JSON.stringify(body) }), ctx)

let profileRows: { id: string; status: string }[]
const sqlCalls = (needle: string) => mocks.query.mock.calls.filter(([sql]) => String(sql).includes(needle))
const notFound = () => Object.assign(new Error('no user'), { code: 'auth/user-not-found' })

beforeEach(() => {
  vi.resetAllMocks()
  profileRows = []
  mocks.admin.mockResolvedValue({ user: { uid: 'admin-1' }, profile: { role: 'super_admin', status: 'active' } })
  mocks.resetLink.mockResolvedValue('https://reset.example/link')
  mocks.query.mockImplementation(async (sql: string) => {
    if (sql.includes('FROM access_requests')) {
      return { rows: [{ id: 'req-1', full_name: 'Ann Lee', email: 'ann@x.com', status: 'pending' }] }
    }
    if (sql.includes('FROM profiles WHERE lower(email)')) return { rows: profileRows }
    return { rows: [] }
  })
})

describe('POST /api/admin/access-requests/[id]/approve', () => {
  it('existing Firebase user + PENDING profile -> profile activated with stamps, request linked, createUser NOT called', async () => {
    mocks.getUserByEmail.mockResolvedValue({ uid: 'u-ann', providerData: [{ providerId: 'password' }] })
    profileRows = [{ id: 'u-ann', status: 'pending' }]
    const response = await call()
    expect(response.status).toBe(200)
    expect(mocks.createUser).not.toHaveBeenCalled()
    const update = sqlCalls('UPDATE profiles SET')[0]
    expect(update[0]).toContain("status='active'")
    expect(update[0]).toContain('approved_at=now()')
    expect(update[0]).toContain('approved_by=$1')
    expect(update[1]).toEqual(['admin-1', 'u-ann'])
    expect(sqlCalls('INSERT INTO profiles')).toHaveLength(0)
    const link = sqlCalls('UPDATE access_requests')[0]
    expect(link[0]).toContain("status='approved'")
    expect(link[1]).toEqual(['admin-1', 'u-ann', 'req-1'])
    expect(mocks.audit).toHaveBeenCalledWith('admin-1', 'approve_user', 'u-ann', expect.objectContaining({ path: 'pending_profile' }))
    // already has a password sign-in -> no setup link
    expect((await response.json()).reset_link).toBeNull()
    expect(mocks.resetLink).not.toHaveBeenCalled()
  })

  it('PENDING profile: a given username is set; the requested role is applied; uniqueness check ignores that profile', async () => {
    mocks.getUserByEmail.mockResolvedValue({ uid: 'u-ann', providerData: [] })
    profileRows = [{ id: 'u-ann', status: 'pending' }]
    const response = await call({ username: 'Ann_Lee', role: 'super_admin' })
    expect(response.status).toBe(200)
    const update = sqlCalls('UPDATE profiles SET')[0]
    expect(update[0]).toContain('username=$2')
    expect(update[0]).toContain("role='super_admin'")
    expect(update[1]).toEqual(['admin-1', 'ann_lee', 'u-ann'])
    expect(sqlCalls('lower(username)')[0][1]).toEqual(['ann_lee', 'u-ann'])
    // no password provider -> setup link generated
    expect((await response.json()).reset_link).toBe('https://reset.example/link')
  })

  it('Firebase user without any profile -> active profile inserted with approval stamps, createUser NOT called', async () => {
    mocks.getUserByEmail.mockResolvedValue({ uid: 'u-ann', providerData: [] })
    const response = await call()
    expect(response.status).toBe(200)
    expect(mocks.createUser).not.toHaveBeenCalled()
    const insert = sqlCalls('INSERT INTO profiles')[0]
    expect(insert[0]).toContain("'active'")
    expect(insert[0]).toContain('approved_at')
    expect(insert[1]).toEqual(['u-ann', 'Ann Lee', null, 'ann@x.com', 'admin-1'])
    expect(sqlCalls('lower(username)')).toHaveLength(0)
    expect((await response.json()).user_id).toBe('u-ann')
  })

  it('neither a Firebase user nor a profile -> today\'s path (createUser, insert, reset link)', async () => {
    mocks.getUserByEmail.mockRejectedValue(notFound())
    mocks.createUser.mockResolvedValue({ uid: 'new-uid', providerData: [] })
    const response = await call()
    expect(response.status).toBe(200)
    expect(mocks.createUser).toHaveBeenCalledWith({ email: 'ann@x.com', emailVerified: false, displayName: 'Ann Lee' })
    expect(sqlCalls('INSERT INTO profiles')[0][1]).toEqual(['new-uid', 'Ann Lee', null, 'ann@x.com', 'admin-1'])
    expect(await response.json()).toEqual({ ok: true, user_id: 'new-uid', reset_link: 'https://reset.example/link', setup_link_status: 'available' })
  })

  it('an ACTIVE profile for the email -> 409, nothing changed', async () => {
    mocks.getUserByEmail.mockResolvedValue({ uid: 'u-ann', providerData: [] })
    profileRows = [{ id: 'u-ann', status: 'active' }]
    const response = await call()
    expect(response.status).toBe(409)
    expect(mocks.createUser).not.toHaveBeenCalled()
    expect(sqlCalls('UPDATE')).toHaveLength(0)
    expect(sqlCalls('INSERT')).toHaveLength(0)
    expect(mocks.audit).not.toHaveBeenCalled()
  })

  it('a profile for the email with no matching Firebase account -> 409, no orphan createUser', async () => {
    mocks.getUserByEmail.mockRejectedValue(notFound())
    profileRows = [{ id: 'stale', status: 'pending' }]
    expect((await call()).status).toBe(409)
    expect(mocks.createUser).not.toHaveBeenCalled()
  })

  it('a Firebase lookup failure other than not-found -> 500, nothing written', async () => {
    mocks.getUserByEmail.mockRejectedValue(new Error('upstream down'))
    expect((await call()).status).toBe(500)
    expect(sqlCalls('UPDATE')).toHaveLength(0)
    expect(sqlCalls('INSERT')).toHaveLength(0)
  })
})


describe('approval account setup availability metadata', () => {
  it('reports not_required for an already configured password provider, without generating a link', async () => {
    mocks.getUserByEmail.mockResolvedValue({ uid: 'synthetic-existing', providerData: [{ providerId: 'password' }] })
    profileRows = [{ id: 'synthetic-existing', status: 'pending' }]
    const response = await call()
    expect(response.status).toBe(200)
    expect(await response.json()).toMatchObject({ ok: true, reset_link: null, setup_link_status: 'not_required' })
    expect(mocks.resetLink).not.toHaveBeenCalled()
    expect(mocks.createUser).not.toHaveBeenCalled()
    expect(mocks.audit).toHaveBeenCalledTimes(1)
  })
  it('reports available while preserving the exact generated link', async () => {
    mocks.getUserByEmail.mockResolvedValue({ uid: 'synthetic-existing', providerData: [] })
    const response = await call()
    expect(response.status).toBe(200)
    expect(await response.json()).toMatchObject({ ok: true, reset_link: 'https://reset.example/link', setup_link_status: 'available' })
    expect(mocks.resetLink).toHaveBeenCalledTimes(1)
    expect(mocks.createUser).not.toHaveBeenCalled()
    expect(mocks.audit).toHaveBeenCalledTimes(1)
  })
  it('reports unavailable after link-generation failure, without undoing approval or exposing the error', async () => {
    mocks.getUserByEmail.mockResolvedValue({ uid: 'synthetic-existing', providerData: [] })
    mocks.resetLink.mockRejectedValue(new Error('SYNTHETIC_PRIVATE_LINK_ERROR'))
    const response = await call()
    expect(response.status).toBe(200)
    const body = await response.json()
    expect(body).toMatchObject({ ok: true, reset_link: null, setup_link_status: 'unavailable' })
    expect(JSON.stringify(body)).not.toContain('SYNTHETIC_PRIVATE_LINK_ERROR')
    expect(sqlCalls('UPDATE access_requests')).toHaveLength(1)
    expect(mocks.audit).toHaveBeenCalledTimes(1)
    expect(mocks.deleteUser).not.toHaveBeenCalled()
  })
})


it.each([401, 403])('refuses actor status %s before any account, profile, audit or link action', async status => {
  const { NextResponse } = await import('next/server')
  mocks.admin.mockResolvedValue(NextResponse.json({ error: 'Synthetic refusal' }, { status }))
  expect((await call()).status).toBe(status)
  expect(mocks.query).not.toHaveBeenCalled()
  expect(mocks.getUserByEmail).not.toHaveBeenCalled()
  expect(mocks.createUser).not.toHaveBeenCalled()
  expect(mocks.resetLink).not.toHaveBeenCalled()
  expect(mocks.audit).not.toHaveBeenCalled()
})


afterEach(() => vi.unstubAllEnvs())

describe('approval setup continuation behind the first-party gateway', () => {
  const proxyCall = () => POST(new Request('http://0.0.0.0:3000/api/admin/access-requests/req-1/approve', {
    method: 'POST', body: '{}', headers: { origin: 'http://localhost:3100', 'x-forwarded-host': 'untrusted.example' },
  }), ctx)

  it('C9 internal-request/new-user case uses configured browser origin and preserves approval/audit', async () => {
    vi.stubEnv('APP_URL', 'http://localhost:3100')
    mocks.getUserByEmail.mockRejectedValue(notFound())
    mocks.createUser.mockResolvedValue({ uid: 'new-uid', providerData: [] })
    const response = await proxyCall()
    expect(response.status).toBe(200)
    expect(await response.json()).toMatchObject({ ok: true, user_id: 'new-uid', setup_link_status: 'available' })
    expect(mocks.resetLink).toHaveBeenCalledWith('ann@x.com', { url: 'http://localhost:3100/setup-account' })
    expect(sqlCalls('INSERT INTO profiles')[0][1]).toEqual(['new-uid', 'Ann Lee', null, 'ann@x.com', 'admin-1'])
    expect(sqlCalls('UPDATE access_requests')[0][1]).toEqual(['admin-1', 'new-uid', 'req-1'])
    expect(mocks.audit).toHaveBeenCalledWith('admin-1', 'approve_user', 'new-uid', { access_request_id: 'req-1', path: 'new_user' })
  })

  it('uses a configured HTTPS origin and ignores forwarded-host input', async () => {
    vi.stubEnv('APP_URL', 'https://portal.example')
    mocks.getUserByEmail.mockResolvedValue({ uid: 'u-ann', providerData: [] })
    expect((await proxyCall()).status).toBe(200)
    expect(mocks.resetLink).toHaveBeenCalledWith('ann@x.com', { url: 'https://portal.example/setup-account' })
  })

  it.each(['', 'not-a-url', 'file:///fixture', 'ftp://portal.example', 'http://0.0.0.0:3000', 'http://[::]:3000', 'https://fixture-user:fixture-pass@portal.example'])(
    'invalid configured origin %s keeps approval honest and generates no link', async appUrl => {
      vi.stubEnv('APP_URL', appUrl)
      mocks.getUserByEmail.mockResolvedValue({ uid: 'u-ann', providerData: [] })
      const response = await proxyCall()
      expect(response.status).toBe(200)
      expect(await response.json()).toMatchObject({ ok: true, reset_link: null, setup_link_status: 'unavailable' })
      expect(mocks.resetLink).not.toHaveBeenCalled()
      expect(sqlCalls('UPDATE access_requests')).toHaveLength(1)
      expect(mocks.audit).toHaveBeenCalledTimes(1)
      expect(mocks.deleteUser).not.toHaveBeenCalled()
    },
  )

  it('an unconfigured internal bind address is unavailable rather than an apparently usable continuation', async () => {
    vi.stubEnv('APP_URL', undefined)
    mocks.getUserByEmail.mockResolvedValue({ uid: 'u-ann', providerData: [] })
    const response = await proxyCall()
    expect(await response.json()).toMatchObject({ ok: true, reset_link: null, setup_link_status: 'unavailable' })
    expect(mocks.resetLink).not.toHaveBeenCalled()
    expect(mocks.audit).toHaveBeenCalledTimes(1)
  })

  it.each(['http://localhost', 'https://portal.example'])('preserves direct-origin compatibility without APP_URL: %s', async origin => {
    vi.stubEnv('APP_URL', undefined)
    mocks.getUserByEmail.mockResolvedValue({ uid: 'u-ann', providerData: [] })
    const response = await POST(new Request(origin + '/api/admin/access-requests/req-1/approve', { method: 'POST', body: '{}' }), ctx)
    expect(response.status).toBe(200)
    expect(mocks.resetLink).toHaveBeenCalledWith('ann@x.com', { url: origin + '/setup-account' })
  })

  it('an existing password remains not_required even when the configured setup origin is invalid', async () => {
    vi.stubEnv('APP_URL', 'not-a-url')
    mocks.getUserByEmail.mockResolvedValue({ uid: 'u-ann', providerData: [{ providerId: 'password' }] })
    profileRows = [{ id: 'u-ann', status: 'pending' }]
    const response = await proxyCall()
    expect(await response.json()).toMatchObject({ ok: true, reset_link: null, setup_link_status: 'not_required' })
    expect(mocks.resetLink).not.toHaveBeenCalled()
    expect(mocks.audit).toHaveBeenCalledTimes(1)
    expect(sqlCalls('UPDATE access_requests')).toHaveLength(1)
  })
})
