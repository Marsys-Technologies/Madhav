/**
 * SS N-398 -- the /panchang PAGE verifies the login itself.
 *
 * panchang/layout.tsx already requires an active user, but a crafted RSC request
 * can skip a layout and proxy.ts only checks the cookie's shape, so the page
 * calls `requireActiveUserPage()` before it loads anything. The only server-side
 * data load on this page is the Python sidecar panchanga `fetch`; every refused
 * case below must reach NO fetch at all.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

class RedirectError extends Error {
  constructor(public readonly url: string) {
    super(`NEXT_REDIRECT:${url}`)
  }
}
const redirectMock = vi.fn((url: string) => {
  throw new RedirectError(url)
})
vi.mock('next/navigation', () => ({
  redirect: (url: string) => redirectMock(url),
}))

const getServerUserWithProfileMock = vi.fn()
vi.mock('@/lib/auth/access-control', () => ({
  getServerUserWithProfile: () => getServerUserWithProfileMock(),
}))

// The client view is irrelevant to the guard; keep the import light.
vi.mock('../components/PanchangClientView', () => ({
  PanchangClientView: () => null,
}))

const fetchMock = vi.fn()
const searchParams = Promise.resolve({})

async function renderPage() {
  vi.resetModules()
  const mod = await import('../page')
  return mod.default({ searchParams })
}

function ctx(status: string) {
  return {
    user: { uid: 'u1' },
    profile: { id: 'u1', role: 'guest', status },
  }
}

beforeEach(() => {
  for (const m of [redirectMock, getServerUserWithProfileMock, fetchMock]) m.mockReset()
  redirectMock.mockImplementation((url: string) => {
    throw new RedirectError(url)
  })
  fetchMock.mockResolvedValue({ ok: false, json: async () => ({}) })
  vi.stubGlobal('fetch', fetchMock)
  vi.stubEnv('PYTHON_SIDECAR_URL', 'http://sidecar.invalid')
  vi.stubEnv('PYTHON_SIDECAR_API_KEY', 'k')
})
afterEach(() => {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
})

describe('panchang page requires a verified, active session', () => {
  it('no verified session -> redirect to /login and the sidecar is NOT called', async () => {
    getServerUserWithProfileMock.mockResolvedValue(null)
    await expect(renderPage()).rejects.toThrow('NEXT_REDIRECT:/login')
    expect(redirectMock).toHaveBeenCalledWith('/login')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it.each(['pending', 'disabled', 'suspended'])(
    'profile status %s -> redirect to /login and the sidecar is NOT called',
    async (status) => {
      getServerUserWithProfileMock.mockResolvedValue(ctx(status))
      await expect(renderPage()).rejects.toThrow('NEXT_REDIRECT:/login')
      expect(redirectMock).toHaveBeenCalledWith('/login')
      expect(fetchMock).not.toHaveBeenCalled()
    },
  )

  it('active user -> page renders and the sidecar is called exactly once', async () => {
    getServerUserWithProfileMock.mockResolvedValue(ctx('active'))
    const el = await renderPage()
    expect(el).toBeTruthy()
    expect(redirectMock).not.toHaveBeenCalled()
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(String(fetchMock.mock.calls[0][0])).toBe('http://sidecar.invalid/api/compute/panchanga')
  })

  it('the refusal never carries ?next= (only /share/ and /clients/ are allowlisted)', async () => {
    getServerUserWithProfileMock.mockResolvedValue(null)
    await expect(renderPage()).rejects.toThrow()
    for (const [url] of redirectMock.mock.calls) expect(String(url)).not.toContain('next=')
  })
})
