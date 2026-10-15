/** S8: moving a never-approved profile to active IS the approval and must be stamped. */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  admin: vi.fn(),
  query: vi.fn(),
  updateUser: vi.fn(),
  audit: vi.fn(),
}))

vi.mock('@/lib/auth/access-control', () => ({ requireSuperAdmin: mocks.admin }))
vi.mock('@/lib/firebase/server', () => ({ adminAuth: { updateUser: mocks.updateUser, deleteUser: vi.fn() } }))
vi.mock('@/lib/db/client', () => ({ query: mocks.query }))
vi.mock('@/lib/admin/audit', () => ({ writeAuditLog: mocks.audit }))

import { PATCH } from '../route'

const ctx = { params: Promise.resolve({ id: 'u-ann' }) }
const patch = (body: unknown) =>
  PATCH(new Request('http://localhost/api/admin/users/u-ann', { method: 'PATCH', body: JSON.stringify(body) }), ctx)

let row: { id: string; role: string; status: string; approved_at: string | null }
const updateCall = () => mocks.query.mock.calls.find(([sql]) => String(sql).startsWith('UPDATE profiles'))!

beforeEach(() => {
  vi.resetAllMocks()
  mocks.admin.mockResolvedValue({ user: { uid: 'admin-1' }, profile: { role: 'super_admin', status: 'active' } })
  mocks.query.mockImplementation(async (sql: string) =>
    sql.includes('SELECT id, role') ? { rows: [row] } : { rows: [] })
})

describe('PATCH /api/admin/users/[id] approval stamps', () => {
  it('pending -> active stamps approved_at and approved_by', async () => {
    row = { id: 'u-ann', role: 'guest', status: 'pending', approved_at: null }
    expect((await patch({ status: 'active' })).status).toBe(200)
    const [sql, values] = updateCall()
    expect(sql).toContain('approved_at=now()')
    expect(sql).toMatch(/approved_by=\$2/)
    expect(values).toEqual(['active', 'admin-1', 'u-ann'])
    expect(mocks.audit).toHaveBeenCalledWith('admin-1', 'enable_user', 'u-ann', { approved_from: 'pending' })
  })

  it('disabled -> active for a previously approved user keeps the original stamps', async () => {
    row = { id: 'u-ann', role: 'guest', status: 'disabled', approved_at: '2026-01-01T00:00:00Z' }
    expect((await patch({ status: 'active' })).status).toBe(200)
    const [sql, values] = updateCall()
    expect(sql).not.toContain('approved_at')
    expect(sql).not.toContain('approved_by')
    expect(values).toEqual(['active', 'u-ann'])
    expect(mocks.audit).toHaveBeenCalledWith('admin-1', 'enable_user', 'u-ann', undefined)
  })

  it('disabling never stamps', async () => {
    row = { id: 'u-ann', role: 'guest', status: 'active', approved_at: null }
    await patch({ status: 'disabled' })
    expect(updateCall()[0]).not.toContain('approved_at')
  })
})
