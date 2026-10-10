/**
 * S8: approving an access request must work for someone who already signed in
 * (a Firebase account, usually with a PENDING profile). Before, the route called
 * createUser() unconditionally, which fails with auth/email-already-exists.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

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
    expect(await response.json()).toEqual({ ok: true, user_id: 'new-uid', reset_link: 'https://reset.example/link' })
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
