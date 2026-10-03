import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AiConsoleError } from '@/lib/ai-console/errors'
import { __resetRpmCountersForTest } from '@/lib/mcp/rate_limiter_core'

const mocks = vi.hoisted(() => ({ auth: vi.fn(), flag: vi.fn(), refresh: vi.fn() }))
vi.mock('@/lib/auth/access-control', () => ({ getServerUserWithProfile: mocks.auth }))
vi.mock('@/lib/config', () => ({ getFlag: mocks.flag }))
vi.mock('@/lib/ai-console/catalog-refresh', () => ({ refreshProviderCatalog: mocks.refresh }))
vi.mock('@/lib/ai-console/repository', () => ({ listAiConsoleState: vi.fn(), previewChoiceDependencies: vi.fn() }))

import { POST } from '../route'

const id = '11111111-1111-4111-8111-111111111111'
const context = (value = id) => ({ params: Promise.resolve({ id: value }) })
const request = (body?: unknown) => new Request('https://test.invalid/api/ai-console/connections/' + id + '/refresh', {
  method: 'POST', ...(body === undefined ? {} : { body: JSON.stringify(body) }),
})
beforeEach(() => {
  vi.resetAllMocks(); __resetRpmCountersForTest()
  mocks.auth.mockResolvedValue({ user: { uid: 'owner' }, profile: { status: 'active' } })
  mocks.flag.mockReturnValue(true)
  mocks.refresh.mockResolvedValue({ status: 'refreshed', modelCount: 3 })
})

describe('provider refresh route', () => {
  it('refreshes metadata with the authenticated owner and caller signal', async () => {
    const req = request({ force: true })
    const response = await POST(req, context())
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ status: 'refreshed', modelCount: 3 })
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(mocks.refresh).toHaveBeenCalledWith('owner', id, { force: true, signal: req.signal })
  })
  it('accepts an empty auto-refresh request', async () => {
    expect((await POST(request(), context())).status).toBe(200)
    expect(mocks.refresh).toHaveBeenCalledWith('owner', id, { force: undefined, signal: expect.any(AbortSignal) })
  })
  it.each([{ force: 'true' }, { apiKey: 'private-input' }, { force: true, acknowledgeCharge: true }])('rejects invalid or extra body fields', async body => {
    expect((await POST(request(body), context())).status).toBe(400)
    expect(mocks.refresh).not.toHaveBeenCalled()
  })
  it('rejects invalid IDs before contacting the provider', async () => {
    expect((await POST(request(), context('bad-id'))).status).toBe(400)
    expect(mocks.refresh).not.toHaveBeenCalled()
  })
  it.each([[null, 401], [{ user: { uid: 'owner' }, profile: { status: 'inactive' } }, 403]] as const)('requires an active authenticated user', async (auth, status) => {
    mocks.auth.mockResolvedValue(auth)
    expect((await POST(request(), context())).status).toBe(status)
    expect(mocks.refresh).not.toHaveBeenCalled()
  })
  it('enforces the shared mutation throttle', async () => {
    for (let attempt = 0; attempt < 30; attempt++) expect((await POST(request(), context())).status).toBe(200)
    const response = await POST(request(), context())
    expect(response.status).toBe(429)
    expect(response.headers.get('Retry-After')).toBeTruthy()
    expect(mocks.refresh).toHaveBeenCalledTimes(30)
  })
  it('returns fixed safe provider errors', async () => {
    mocks.refresh.mockRejectedValue(new AiConsoleError('AI_PERMISSION_DENIED'))
    const response = await POST(request(), context())
    expect(response.status).toBe(403)
    expect((await response.json()).error.code).toBe('AI_PERMISSION_DENIED')
    mocks.refresh.mockRejectedValue(new Error('fixture-private-content'))
    expect(JSON.stringify(await (await POST(request(), context())).json())).not.toContain('fixture-private-content')
  })
})
