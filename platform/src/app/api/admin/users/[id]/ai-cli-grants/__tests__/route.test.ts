import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextResponse } from 'next/server'
import { __resetRpmCountersForTest } from '@/lib/mcp/rate_limiter_core'

const mocks = vi.hoisted(() => ({ admin: vi.fn(), flag: vi.fn(), list: vi.fn(), set: vi.fn() }))
vi.mock('@/lib/auth/access-control', () => ({ requireSuperAdmin: mocks.admin }))
vi.mock('@/lib/config', () => ({ getFlag: mocks.flag }))
vi.mock('@/lib/ai-console/repository', () => ({ listAdminCliGrants: mocks.list, setCliGrant: mocks.set }))

import * as route from '../route'
const context = { params: Promise.resolve({ id: 'alice' }) }

beforeEach(() => {
  vi.resetAllMocks(); __resetRpmCountersForTest(); mocks.flag.mockReturnValue(true)
  mocks.admin.mockResolvedValue({ user: { uid: 'admin' }, profile: { role: 'super_admin', status: 'active' } })
  mocks.list.mockResolvedValue([{ cli_id: 'codex', granted_at: null, revoked_at: null, host_state: 'unavailable' }])
})

describe('admin CLI grants route', () => {
  it('requires super-admin and exposes only coarse host state', async () => {
    const response = await route.GET(new Request('http://localhost'), context)
    expect(await response.json()).toEqual({ grants: [{ cliId: 'codex', productName: 'Codex CLI', granted: false, hostState: 'unavailable' }] })
    expect(mocks.list).toHaveBeenCalledWith('admin', 'alice')
    mocks.admin.mockResolvedValueOnce(NextResponse.json({ error: 'forbidden' }, { status: 403 }))
    expect((await route.GET(new Request('http://localhost'), context)).status).toBe(403)
  })

  it('never reports a detect-only CLI as host-reachable from stale database state', async () => {
    mocks.list.mockResolvedValueOnce([{ cli_id: 'codex', granted_at: new Date(), revoked_at: null,
      host_state: 'reachable' }])
    expect(await (await route.GET(new Request('http://localhost'), context)).json()).toEqual({ grants: [{
      cliId: 'codex', productName: 'Codex CLI', granted: true, hostState: 'unavailable',
    }] })
  })

  it('grants and revokes only the exact closed CLI ID', async () => {
    const request = (body: unknown) => new Request('http://localhost', { method: 'PATCH', body: JSON.stringify(body) })
    expect((await route.PATCH(request({ cliId: 'codex', granted: true }), context)).status).toBe(200)
    expect(mocks.set).toHaveBeenCalledWith('admin', 'alice', 'codex', true)
    expect((await route.PATCH(request({ cliId: 'other', granted: true }), context)).status).toBe(400)
    expect(mocks.set).toHaveBeenCalledOnce()
  })

  it('fails closed while the feature is disabled', async () => {
    mocks.flag.mockReturnValue(false)
    expect((await route.GET(new Request('http://localhost'), context)).status).toBe(404)
    expect(mocks.admin).not.toHaveBeenCalled()
  })

  it('bounds and rate-limits grant mutations before persistence', async () => {
    const huge = new Request('http://localhost', { method: 'PATCH', body: 'x'.repeat(17_000) })
    expect((await route.PATCH(huge, context)).status).toBe(413)
    const request = () => new Request('http://localhost', { method: 'PATCH',
      body: JSON.stringify({ cliId: 'codex', granted: true }) })
    for (let index = 0; index < 29; index++) expect((await route.PATCH(request(), context)).status).toBe(200)
    const limited = await route.PATCH(request(), context)
    expect(limited.status).toBe(429)
    expect(limited.headers.get('Retry-After')).not.toBeNull()
  })
})
