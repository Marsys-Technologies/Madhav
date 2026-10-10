/**
 * proxy_login_next.test.ts — SS N-383 (a): the page redirect to /login carries
 * `?next=<pathname>` ONLY when `safeNextPath(pathname)` accepts it.
 *
 *   /share/AbC123xyz0       -> /login?next=%2Fshare%2FAbC123xyz0
 *   /clients/abc-123/edit   -> /login?next=%2Fclients%2Fabc-123%2Fedit
 *   /dashboard (anything else) -> /login (plain, exactly as before)
 *   /api/*                  -> 401 JSON, never a redirect
 *
 * Runs the real `proxy()` with firebase-admin MOCKED (no network, no Firebase).
 * Same behaviour in all three SESSION_GATE_MODE values.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'

const verifyMock = vi.hoisted(() => vi.fn())

vi.mock('firebase-admin/app', () => ({
  initializeApp: vi.fn(() => ({})),
  getApps: vi.fn(() => []),
  cert: vi.fn(() => ({})),
}))
vi.mock('firebase-admin/auth', () => ({
  getAuth: vi.fn(() => ({ verifySessionCookie: verifyMock })),
}))

import { safeNextPath } from '@/lib/auth/safe_next'
import { __resetRpmCountersForTest } from '@/lib/mcp/rate_limiter_core'
import { __resetSessionGateForTest } from '@/lib/security/session_gate'
import { proxy } from '@/proxy'

const ORIGIN = 'http://localhost'

function shapeValidCookie(): string {
  const payload = {
    sub: 'uid-next-test',
    exp: Math.floor(Date.now() / 1000) + 3600,
    iss: 'https://session.firebase.google.com/marsys',
  }
  return `hdr.${Buffer.from(JSON.stringify(payload)).toString('base64url')}.sig`
}

/** A request with NO cookie unless one is given. `rawPath` goes into the URL verbatim. */
function req(rawPath: string, cookie?: string): NextRequest {
  const headers: Record<string, string> = {}
  if (cookie) headers.cookie = `__session=${cookie}`
  return new NextRequest(`${ORIGIN}${rawPath}`, { headers })
}

function locationOf(res: Response): URL {
  const loc = res.headers.get('location')
  expect(loc, 'expected a redirect with a Location header').not.toBeNull()
  return new URL(loc as string)
}

const MODES: Array<[string, string | undefined]> = [
  ['off', 'off'],
  ['shadow', 'shadow'],
  ['enforce', 'enforce'],
]

const originalMode = process.env.SESSION_GATE_MODE
function setMode(value: string | undefined) {
  if (value === undefined) delete process.env.SESSION_GATE_MODE
  else process.env.SESSION_GATE_MODE = value
}

let warn: ReturnType<typeof vi.spyOn>
beforeEach(() => {
  __resetSessionGateForTest()
  __resetRpmCountersForTest()
  verifyMock.mockReset()
  warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
})
afterEach(() => {
  warn.mockRestore()
  setMode(originalMode)
})

describe.each(MODES)('unauthenticated page redirect, SESSION_GATE_MODE = %s', (_label, value) => {
  beforeEach(() => setMode(value))

  it('/share/<slug> -> /login?next=%2Fshare%2F<slug>', async () => {
    const res = await proxy(req('/share/AbC123xyz0'))
    expect(res.status).toBe(307)
    expect(res.headers.get('location')).toBe(`${ORIGIN}/login?next=%2Fshare%2FAbC123xyz0`)
  })

  it('/clients/<id>/edit -> /login?next=%2Fclients%2F<id>%2Fedit', async () => {
    const res = await proxy(req('/clients/abc-123/edit'))
    expect(res.status).toBe(307)
    expect(res.headers.get('location')).toBe(`${ORIGIN}/login?next=%2Fclients%2Fabc-123%2Fedit`)
  })

  it.each(['/dashboard', '/cockpit', '/clients', '/clients/', '/share', '/share/', '/panchang', '/setup-account'])(
    'non-allowlisted or bare-directory path %s -> plain /login (exactly as before)',
    async (path) => {
      const res = await proxy(req(path))
      expect(res.status).toBe(307)
      expect(res.headers.get('location')).toBe(`${ORIGIN}/login`)
    },
  )

  it('a query string is dropped: next carries the pathname only', async () => {
    const res = await proxy(req('/share/AbC123xyz0?utm=1&next=//evil.com#frag'))
    const loc = locationOf(res)
    expect(loc.pathname).toBe('/login')
    expect(loc.origin).toBe(ORIGIN)
    expect(loc.searchParams.get('next')).toBe('/share/AbC123xyz0')
    expect([...loc.searchParams.keys()]).toEqual(['next'])
    expect(res.headers.get('location')).toBe(`${ORIGIN}/login?next=%2Fshare%2FAbC123xyz0`)
  })

  it('a query string on a non-allowlisted page does not turn into a next', async () => {
    const res = await proxy(req('/dashboard?next=/share/AbC123xyz0'))
    expect(res.headers.get('location')).toBe(`${ORIGIN}/login`)
  })

  it('/api/* stays a 401 JSON with no redirect', async () => {
    for (const path of ['/api/charts', '/api/clients/abc-123/edit', '/api/share/AbC123xyz0']) {
      const res = await proxy(req(path))
      expect(res.status).toBe(401)
      expect(res.headers.get('location')).toBeNull()
      expect(res.headers.get('content-type') ?? '').toContain('application/json')
      expect(await res.json()).toEqual({ error: 'unauthorized' })
    }
  })

  it('a shape-INvalid cookie is redirected the same way (with next)', async () => {
    const res = await proxy(req('/share/AbC123xyz0', 'not-a-jwt'))
    expect(res.headers.get('location')).toBe(`${ORIGIN}/login?next=%2Fshare%2FAbC123xyz0`)
  })
})

describe('enforce: a shape-valid but cryptographically rejected cookie gets the same redirect', () => {
  beforeEach(() => {
    setMode('enforce')
    verifyMock.mockRejectedValue(Object.assign(new Error('Firebase session cookie has invalid signature.'), { code: 'auth/argument-error' }))
  })

  it('page: redirect to /login?next=...', async () => {
    const res = await proxy(req('/clients/abc-123/edit', shapeValidCookie()))
    expect(res.status).toBe(307)
    expect(res.headers.get('location')).toBe(`${ORIGIN}/login?next=%2Fclients%2Fabc-123%2Fedit`)
  })

  it('page, non-allowlisted: plain /login', async () => {
    const res = await proxy(req('/dashboard', shapeValidCookie()))
    expect(res.headers.get('location')).toBe(`${ORIGIN}/login`)
  })

  it('API: 401 JSON, no redirect', async () => {
    const res = await proxy(req('/api/charts', shapeValidCookie()))
    expect(res.status).toBe(401)
    expect(res.headers.get('location')).toBeNull()
  })

  it('verifier infrastructure down: still a plain 401 (no redirect, so no loop), unchanged', async () => {
    verifyMock.mockReset()
    verifyMock.mockRejectedValue(Object.assign(new Error('Service account object must contain a string "project_id" property.'), { code: 'app/invalid-credential' }))
    const res = await proxy(req('/share/AbC123xyz0', shapeValidCookie()))
    expect(res.status).toBe(401)
    expect(res.headers.get('location')).toBeNull()
  })
})

describe('a valid session is not redirected at all', () => {
  it.each(MODES)('mode %s', async (_label, value) => {
    setMode(value)
    verifyMock.mockResolvedValue({ sub: 'uid-next-test', exp: Math.floor(Date.now() / 1000) + 3600 })
    const res = await proxy(req('/share/AbC123xyz0', shapeValidCookie()))
    expect(res.headers.get('location')).toBeNull()
  })
})

describe('open-redirect attempts through the path never produce a next that safeNextPath would reject', () => {
  // Raw request paths an attacker can put in a link. Whatever the URL parser
  // makes of them, the redirect must stay on /login, on the same origin, and any
  // `next` must be a value safeNextPath accepts verbatim.
  const HOSTILE = [
    '/share//evil.com',
    '/share//evil.com/x',
    '//evil.com/share/AbC123xyz0',
    '/share/%2f%2fevil.com',
    '/share/%2F%2Fevil.com',
    '/share/..%2f..%2fevil',
    '/share/%2e%2e/%2e%2e/evil',
    '/share/%2e%2e%2f%2e%2e%2fevil',
    '/share/%252e%252e%252fevil',
    '/share/.%2e/admin',
    '/share/../admin',
    '/share/./AbC123xyz0',
    '/share/%5Cevil.com',
    '/share/%5cevil.com',
    '/share/\\evil.com',
    '/share/a\\..\\..\\evil',
    '/clients/%2f%2fevil.com',
    '/clients/..%2f..%2fadmin',
    '/clients/abc/../../evil',
    '/clients/abc:evil',
    '/share/javascript:alert(1)',
    '/share/http:%2f%2fevil.com',
    '/share/%00',
    '/share/%0d%0aLocation:%20http://evil.com',
    '/share/a%09b',
    '/share/a%20b',
    '/share/%E0%A4%A',
    '/share/%',
    '/share/AbC123xyz0/',
    `/share/${'a'.repeat(600)}`,
  ]

  it.each(HOSTILE)('%s', async (raw) => {
    for (const [, value] of MODES) {
      setMode(value)
      const res = await proxy(req(raw))
      expect(res.status).toBe(307)
      const loc = locationOf(res)
      expect(loc.origin).toBe(ORIGIN)
      expect(loc.pathname).toBe('/login')
      const keys = [...loc.searchParams.keys()]
      expect(keys.every((k) => k === 'next')).toBe(true)
      expect(keys.length).toBeLessThanOrEqual(1)
      const next = loc.searchParams.get('next')
      if (next !== null) {
        // Whatever was emitted must be exactly what the login page will accept.
        expect(safeNextPath(next)).toBe(next)
        expect(next.startsWith('/share/') || next.startsWith('/clients/')).toBe(true)
        expect(next.startsWith('//')).toBe(false)
        expect(next).not.toMatch(/[\\:?#]/)
      }
    }
  })

  it('paths the validator rejects redirect to a plain /login (no next at all)', async () => {
    for (const raw of ['/share//evil.com', '/share/..%2f..%2fevil', '/share/%5Cevil.com', '/share/a%20b', '/share/%', '/clients/abc:evil']) {
      const res = await proxy(req(raw))
      expect(res.headers.get('location'), raw).toBe(`${ORIGIN}/login`)
    }
  })
})

describe('round trip with the login page validator', () => {
  it.each(['/share/AbC123xyz0', '/clients/abc-123/edit', '/clients/c_9.v~2/x'])('proxy next for %s survives safeNextPath on the decoded value', async (path) => {
    const res = await proxy(req(path))
    const loc = locationOf(res)
    // The login page does: new URLSearchParams(window.location.search).get('next')
    const decoded = new URLSearchParams(loc.search).get('next')
    expect(decoded).toBe(path)
    expect(safeNextPath(decoded)).toBe(path)
  })
})
