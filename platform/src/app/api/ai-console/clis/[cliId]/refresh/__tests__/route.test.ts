import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AiConsoleError } from '@/lib/ai-console/errors'
import { __resetRpmCountersForTest } from '@/lib/mcp/rate_limiter_core'

const mocks = vi.hoisted(() => ({ auth: vi.fn(), flag: vi.fn(), refresh: vi.fn() }))
vi.mock('@/lib/auth/access-control', () => ({ getServerUserWithProfile: mocks.auth }))
vi.mock('@/lib/config', () => ({ getFlag: mocks.flag }))
vi.mock('@/lib/ai-console/cli/refresh', () => ({ refreshCliCatalog: mocks.refresh }))
vi.mock('@/lib/ai-console/repository', () => ({ listAiConsoleState: vi.fn(), previewChoiceDependencies: vi.fn() }))
import { POST } from '../route'

const context = (cliId = 'codex') => ({ params: Promise.resolve({ cliId }) })
const request = (body?: unknown) => new Request('https://test.invalid/api/ai-console/clis/codex/refresh', {
  method: 'POST', ...(body === undefined ? {} : { body: JSON.stringify(body) }),
})
beforeEach(() => {
  vi.resetAllMocks(); __resetRpmCountersForTest()
  mocks.auth.mockResolvedValue({ user: { uid: 'owner' }, profile: { status: 'active' } })
  mocks.flag.mockReturnValue(true)
  mocks.refresh.mockResolvedValue({ status: 'refreshed', cliId: 'codex', modelCount: 7 })
})

describe('CLI catalogue refresh route', () => {
  it('passes the authenticated user, force selection, and request cancellation signal', async () => {
    const req = request({ force: true })
    const response = await POST(req, context())
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ status: 'refreshed', cliId: 'codex', modelCount: 7 })
    expect(response.headers.get('Cache-Control')).toBe('no-store')
    expect(mocks.refresh).toHaveBeenCalledWith('owner', 'codex', { force: true, signal: req.signal })
  })

  it('accepts empty auto-refresh requests and returns skipped freshness', async () => {
    mocks.refresh.mockResolvedValue({ status: 'skipped' })
    const response = await POST(request(), context())
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ status: 'skipped' })
    expect(mocks.refresh).toHaveBeenCalledWith('owner', 'codex', { force: undefined, signal: expect.any(AbortSignal) })
  })

  it('rejects an unknown CLI ID with 400 before contacting a host', async () => {
    const response = await POST(request(), context('untrusted-cli'))
    expect(response.status).toBe(400)
    expect(await response.json()).toEqual({ error: 'invalid_request' })
    expect(mocks.refresh).not.toHaveBeenCalled()
  })

  it.each([{ force: 'true' }, { args: ['--unsafe'] }, { force: true, apiKey: 'private-input' }])(
    'rejects invalid or extra fields before any discovery', async body => {
      expect((await POST(request(body), context())).status).toBe(400)
      expect(mocks.refresh).not.toHaveBeenCalled()
    })

  it.each([[null, 401], [{ user: { uid: 'owner' }, profile: { status: 'inactive' } }, 403]] as const)(
    'requires an active authenticated user', async (auth, status) => {
      mocks.auth.mockResolvedValue(auth)
      expect((await POST(request(), context())).status).toBe(status)
      expect(mocks.refresh).not.toHaveBeenCalled()
    })

  it('hides the feature while disabled', async () => {
    mocks.flag.mockReturnValue(false)
    expect((await POST(request(), context())).status).toBe(404)
    expect(mocks.refresh).not.toHaveBeenCalled()
  })

  it('enforces the shared mutation throttle', async () => {
    for (let index = 0; index < 30; index++) expect((await POST(request(), context())).status).toBe(200)
    const response = await POST(request(), context())
    expect(response.status).toBe(429)
    expect(response.headers.get('Retry-After')).toBeTruthy()
    expect(mocks.refresh).toHaveBeenCalledTimes(30)
  })

  it.each([['AI_CLI_NOT_GRANTED', 403], ['AI_CLI_AUTH_UNAVAILABLE', 503], ['AI_CLI_TIMEOUT', 504]] as const)(
    'returns fixed safe CLI errors for %s', async (code, status) => {
      mocks.refresh.mockRejectedValue(new AiConsoleError(code))
      const response = await POST(request(), context())
      expect(response.status).toBe(status)
      expect((await response.json()).error.code).toBe(code)
    })

  it('does not return private host or account error text', async () => {
    mocks.refresh.mockRejectedValue(new Error('private-host-and-account-content'))
    const response = await POST(request(), context())
    expect(response.status).toBe(500)
    expect(JSON.stringify(await response.json())).not.toContain('private-host-and-account-content')
  })
})
