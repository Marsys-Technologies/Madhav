/**
 * proxy_session_gate.test.ts — the SESSION_GATE_MODE matrix through the real
 * `proxy()` with firebase-admin MOCKED.
 *
 *   scenarios: valid cookie | shape-valid but forged signature | expired |
 *              wrong issuer | verification infrastructure error
 *   modes:     shadow | enforce | off | unset | garbage value
 *
 * Asserts the decisions, the log lines (and that no secret ever reaches them),
 * that shadow never blocks, that enforce fails closed without throwing, the
 * bounded counters/log cap, and the verified-sub rate-limit key.
 *
 * The pre-existing proxy tests (src/lib/limits/__tests__/proxy.test.ts) run
 * unchanged against the default (shadow) mode and are the regression guard for
 * "nothing is blocked that is not blocked today".
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

import { configService } from '@/lib/config/index'
import { __resetRpmCountersForTest } from '@/lib/mcp/rate_limiter_core'
import {
  __resetSessionGateForTest,
  classifyHost,
  getSessionGateStats,
  SESSION_GATE_MAX_LOG_LINES_PER_MIN,
  XFF_COUNT_CAP,
  XFF_MAX_LINES_PER_MIN,
} from '@/lib/security/session_gate'
import { proxy } from '@/proxy'

const SECRET_UID = 'uid-SECRET-9f3a'
const SECRET_EMAIL = 'victim.person@example.com'

/** Shape-valid cookie (passes the proxy's non-crypto check) carrying PII-ish claims. */
function shapeValidCookie(sub = SECRET_UID): string {
  const payload = {
    sub,
    email: SECRET_EMAIL,
    exp: Math.floor(Date.now() / 1000) + 3600,
    iss: 'https://session.firebase.google.com/marsys',
  }
  return `hdr.${Buffer.from(JSON.stringify(payload)).toString('base64url')}.sigSECRET`
}

function req(path: string, opts?: { method?: string; cookie?: string | null; headers?: Record<string, string> }): NextRequest {
  const headers: Record<string, string> = { ...opts?.headers }
  const cookie = opts?.cookie === undefined ? shapeValidCookie() : opts.cookie
  if (cookie) headers.cookie = `__session=${cookie}`
  return new NextRequest(`http://localhost${path}`, { method: opts?.method ?? 'GET', headers })
}

function authErr(code: string, message: string) {
  return Object.assign(new Error(message), { code })
}

type Scenario = 'valid' | 'forged' | 'expired' | 'wrong_iss' | 'infra'
const SCENARIOS: Record<Scenario, { arrange: () => void; reason?: string }> = {
  valid: { arrange: () => verifyMock.mockResolvedValue({ sub: 'verified-uid', exp: Math.floor(Date.now() / 1000) + 3600 }) },
  forged: {
    arrange: () => verifyMock.mockRejectedValue(authErr('auth/argument-error', 'Firebase session cookie has invalid signature. See x')),
    reason: 'bad_signature',
  },
  expired: {
    arrange: () => verifyMock.mockRejectedValue(authErr('auth/session-cookie-expired', 'Firebase session cookie has expired.')),
    reason: 'expired',
  },
  wrong_iss: {
    arrange: () =>
      verifyMock.mockRejectedValue(
        authErr('auth/argument-error', 'Firebase session cookie has incorrect "iss" (issuer) claim. Expected "a" but got "b".'),
      ),
    reason: 'wrong_issuer',
  },
  infra: {
    arrange: () => verifyMock.mockRejectedValue(authErr('app/invalid-credential', 'Service account object must contain a string "project_id" property.')),
    reason: 'verify_error',
  },
}

/** mode label -> env value (undefined = unset). */
const MODES: Array<[string, string | undefined]> = [
  ['shadow', 'shadow'],
  ['enforce', 'enforce'],
  ['off', 'off'],
  ['unset', undefined],
  ['garbage', 'definitely-not-a-mode'],
]
const EFFECTIVE: Record<string, 'shadow' | 'enforce' | 'off'> = {
  shadow: 'shadow',
  enforce: 'enforce',
  off: 'off',
  unset: 'shadow',
  garbage: 'shadow',
}

let warn: ReturnType<typeof vi.spyOn>
const originalMode = process.env.SESSION_GATE_MODE

function setMode(value: string | undefined) {
  if (value === undefined) delete process.env.SESSION_GATE_MODE
  else process.env.SESSION_GATE_MODE = value
}

function logLines(): Array<Record<string, unknown>> {
  return warn.mock.calls.map((c: unknown[]) => JSON.parse(String(c[0])))
}

beforeEach(() => {
  __resetSessionGateForTest()
  __resetRpmCountersForTest()
  verifyMock.mockReset()
  warn = vi.spyOn(console, 'warn').mockImplementation(() => {})
})
afterEach(() => {
  warn.mockRestore()
  setMode(originalMode)
  configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', false)
  vi.useRealTimers()
})

describe.each(MODES)('SESSION_GATE_MODE = %s', (label, value) => {
  const effective = EFFECTIVE[label]

  describe.each(Object.keys(SCENARIOS) as Scenario[])('scenario: %s', (scenario) => {
    beforeEach(() => {
      setMode(value)
      SCENARIOS[scenario].arrange()
    })

    it('API path decision', async () => {
      const res = await proxy(req('/api/charts/abc'))
      const rejectsInEnforce = scenario !== 'valid'

      if (effective === 'enforce' && rejectsInEnforce) {
        expect(res.status).toBe(401)
        expect(await res.json()).toEqual({ error: 'unauthorized' })
      } else {
        // off and shadow (and unset/garbage) NEVER block a shape-valid cookie.
        expect(res.status).toBe(200)
      }
    })

    it('page path decision (redirect for a rejected session; plain 401 when the verifier itself is down)', async () => {
      const res = await proxy(req('/clients/abc'))
      if (effective === 'enforce' && scenario === 'infra') {
        expect(res.status).toBe(401)
        expect(res.headers.get('location')).toBeNull()
      } else if (effective === 'enforce' && scenario !== 'valid') {
        expect(res.status).toBe(307)
        expect(res.headers.get('location')).toContain('/login')
      } else {
        expect(res.status).toBe(200)
      }
    })

    it('log line + counter', async () => {
      await proxy(req('/api/charts/482012f1-710e-4a25-994a-93821f5871aa'))
      const lines = logLines()
      const reason = SCENARIOS[scenario].reason

      if (effective === 'off') {
        expect(verifyMock).not.toHaveBeenCalled()
        expect(lines).toEqual([])
        expect(getSessionGateStats().would_reject_total).toBe(0)
        return
      }
      expect(verifyMock).toHaveBeenCalledTimes(1)
      expect(verifyMock).toHaveBeenCalledWith(expect.any(String), false) // checkRevoked=false in the proxy

      if (scenario === 'valid') {
        expect(lines).toEqual([])
        expect(getSessionGateStats().verified_ok).toBe(1)
        return
      }
      if (effective === 'shadow') {
        expect(lines).toEqual([
          { event: 'session_gate_would_reject', path: '/api/charts/:id', reason, mode: 'shadow' },
        ])
        expect(getSessionGateStats().would_reject_total).toBe(1)
        expect(getSessionGateStats().would_reject_by_reason[reason as 'bad_signature']).toBe(1)
      } else {
        expect(lines).toEqual([{ event: 'session_gate_rejected', path: '/api/charts/:id', reason, mode: 'enforce' }])
        expect(getSessionGateStats().would_reject_total).toBe(0) // would-reject is shadow-only
      }
    })

    it('never leaks the cookie, uid, email or any cookie segment into the logs', async () => {
      const cookie = shapeValidCookie()
      await proxy(req('/api/charts/abc?token=querysecret', { cookie }))
      await proxy(req('/clients/abc', { cookie }))
      const blob = warn.mock.calls.map((c: unknown[]) => String(c[0])).join('\n')
      for (const secret of [cookie, ...cookie.split('.'), SECRET_UID, SECRET_EMAIL, 'querysecret', 'sigSECRET']) {
        expect(blob).not.toContain(secret)
      }
    })
  })
})

describe('what the gate never touches', () => {
  beforeEach(() => {
    setMode('enforce')
    verifyMock.mockRejectedValue(authErr('auth/argument-error', 'Firebase session cookie has invalid signature.'))
  })

  it('a missing cookie is refused exactly as before and costs no verification', async () => {
    const res = await proxy(req('/api/charts/abc', { cookie: null }))
    expect(res.status).toBe(401)
    expect(verifyMock).not.toHaveBeenCalled()
  })

  it('a shape-INvalid cookie is refused exactly as before and costs no verification', async () => {
    const res = await proxy(req('/api/charts/abc', { cookie: 'not.a-jwt.at-all' }))
    expect(res.status).toBe(401)
    expect(verifyMock).not.toHaveBeenCalled()
  })

  it.each([
    '/',
    '/login',
    '/reset-password',
    '/api/health',
    '/api/access-requests',
    '/api/mcp/session',
    '/api/admin/internal/refresh-mv',
    '/api/admin/cron/reap-pending-streams',
    '/api/cockpit/watchdog',
    '/api/retrieval/capability',
  ])('public path %s is untouched even in enforce with a forged cookie', async (path) => {
    const res = await proxy(req(path))
    expect(res.status).toBe(200)
    expect(verifyMock).not.toHaveBeenCalled()
  })

  it('the matcher is unchanged', async () => {
    const { config } = await import('@/proxy')
    expect(config.matcher).toEqual([
      '/((?!_next/static|_next/image|favicon.ico|icon.png|apple-icon.png|brand/|api/auth/).*)',
    ])
  })
})

describe('enforce fails closed without throwing', () => {
  it('a throwing / hanging firebase-admin never produces an unhandled exception', async () => {
    setMode('enforce')
    verifyMock.mockImplementation(() => {
      throw new Error('kaboom (sync)')
    })
    await expect(proxy(req('/api/charts/abc'))).resolves.toMatchObject({ status: 401 })
    await expect(proxy(req('/clients/abc'))).resolves.toMatchObject({ status: 401 })
  })

  it('a key-fetch failure surfaced as an argument error is infra: 401 in enforce, 200 + verify_error in shadow', async () => {
    verifyMock.mockRejectedValue(authErr('auth/argument-error', 'Error fetching public keys for Google certs: getaddrinfo ENOTFOUND'))
    setMode('enforce')
    expect((await proxy(req('/api/charts/abc'))).status).toBe(401)
    __resetSessionGateForTest()
    setMode('shadow')
    expect((await proxy(req('/api/charts/abc'))).status).toBe(200)
    expect(logLines().at(-1)).toMatchObject({ event: 'session_gate_would_reject', reason: 'verify_error', mode: 'shadow' })
  })
})

describe('bounded observability', () => {
  it('shadow log lines are capped per minute and a suppression summary follows', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-10T00:00:00Z'))
    setMode('shadow')
    verifyMock.mockRejectedValue(authErr('auth/argument-error', 'Firebase session cookie has invalid signature.'))

    const total = SESSION_GATE_MAX_LOG_LINES_PER_MIN + 40
    for (let i = 0; i < total; i++) await proxy(req('/api/charts/abc'))

    expect(warn).toHaveBeenCalledTimes(SESSION_GATE_MAX_LOG_LINES_PER_MIN)
    // The counter is NOT capped by the log cap: every would-reject is counted.
    expect(getSessionGateStats().would_reject_total).toBe(total)

    vi.setSystemTime(Date.now() + 61_000)
    await proxy(req('/api/charts/abc'))
    const lines = logLines()
    expect(lines.some((l) => l.event === 'session_gate_log_suppressed' && l.suppressed === 40)).toBe(true)
  })
})

describe('rate-limit door keys on the VERIFIED sub', () => {
  beforeEach(() => configService.setFlag('PARIPRASHNA_LIMITS_ENABLED', true))

  async function flood(n: number, rotateSub: boolean) {
    let last = 200
    for (let i = 0; i < n; i++) {
      last = (
        await proxy(req('/api/pariprashna', { method: 'POST', cookie: shapeValidCookie(rotateSub ? `forged-${i}` : 'same') }))
      ).status
    }
    return last
  }

  it('shadow + verified: rotating the forged sub no longer evades the bucket', async () => {
    setMode('shadow')
    verifyMock.mockResolvedValue({ sub: 'the-real-uid', exp: Math.floor(Date.now() / 1000) + 3600 })
    expect(await flood(125, true)).toBe(429) // MARSYS_PROXY_RPM_LIMIT defaults to 120
  })

  it('enforce + verified: same', async () => {
    setMode('enforce')
    verifyMock.mockResolvedValue({ sub: 'the-real-uid', exp: Math.floor(Date.now() / 1000) + 3600 })
    expect(await flood(125, true)).toBe(429)
  })

  it('a spoofed x-mcp-key-id header cannot move a verified caller to a fresh bucket', async () => {
    setMode('shadow')
    verifyMock.mockResolvedValue({ sub: 'the-real-uid', exp: Math.floor(Date.now() / 1000) + 3600 })
    let last = 200
    for (let i = 0; i < 125; i++) {
      last = (await proxy(req('/api/pariprashna', { method: 'POST', headers: { 'x-mcp-key-id': `spoof-${i}` } }))).status
    }
    expect(last).toBe(429)
  })

  it('shadow + verification FAILED: keeps today\'s key (unverified sub), so the previous behaviour is unchanged', async () => {
    setMode('shadow')
    verifyMock.mockRejectedValue(authErr('auth/argument-error', 'Firebase session cookie has invalid signature.'))
    expect(await flood(125, true)).toBe(200) // rotating sub still evades, exactly as before
    expect(await flood(125, false)).toBe(429) // a stable sub is limited, exactly as before
  })

  it('off: exactly today\'s keying (unverified sub)', async () => {
    setMode('off')
    expect(await flood(125, true)).toBe(200)
    expect(verifyMock).not.toHaveBeenCalled()
  })
})

// ── SS N-375: X-Forwarded-For entry-count observation ─────────────────────────

describe('xff_entry_count observation', () => {
  let info: ReturnType<typeof vi.spyOn>
  const IPS = ['203.0.113.77', '198.51.100.9', '10.1.2.3']
  const PUBLIC_HOST = 'app.example-marsys.test'
  const RUN_APP_HOST = 'amjis-web-938361928218.asia-south1.run.app'

  function xreq(path: string, host: string | null, xff: string | null): NextRequest {
    const headers: Record<string, string> = {}
    if (host) headers.host = host
    if (xff) headers['x-forwarded-for'] = xff
    return new NextRequest(`http://localhost${path}`, { method: 'GET', headers })
  }
  function xffLines(): Array<Record<string, unknown>> {
    return info.mock.calls.map((c: unknown[]) => JSON.parse(String(c[0])))
  }

  beforeEach(() => {
    info = vi.spyOn(console, 'info').mockImplementation(() => {})
    verifyMock.mockResolvedValue({ sub: 'u', exp: Math.floor(Date.now() / 1000) + 3600 })
  })
  afterEach(() => {
    info.mockRestore()
    delete process.env.SESSION_GATE_PUBLIC_HOSTS
  })

  it.each(['shadow', 'enforce', undefined, 'garbage'])('mode %s logs the count and host class', async (mode) => {
    setMode(mode)
    await proxy(xreq('/api/charts/482012f1', PUBLIC_HOST, IPS.join(', ')))
    await proxy(xreq('/api/health', RUN_APP_HOST, IPS[0]))
    await proxy(xreq('/api/health', 'localhost:3000', null))
    const eff = mode === 'enforce' ? 'enforce' : 'shadow'
    expect(xffLines()).toEqual([
      { event: 'xff_entry_count', host_class: 'public', count: 3, path: '/api/charts/:id', mode: eff },
      { event: 'xff_entry_count', host_class: 'run_app', count: 1, path: '/api/health', mode: eff },
      { event: 'xff_entry_count', host_class: 'other', count: 0, path: '/api/health', mode: eff },
    ])
  })

  it('off mode logs nothing', async () => {
    setMode('off')
    await proxy(xreq('/api/health', PUBLIC_HOST, IPS.join(',')))
    await proxy(xreq('/api/charts/482012f1', PUBLIC_HOST, IPS.join(',')))
    expect(info).not.toHaveBeenCalled()
  })

  it('never logs an IP address, the raw header, or the host value', async () => {
    setMode('shadow')
    await proxy(xreq('/api/charts/482012f1', PUBLIC_HOST, IPS.join(', ')))
    await proxy(xreq('/api/health', RUN_APP_HOST, `${IPS[0]},${IPS[1]}`))
    const blob = [...info.mock.calls, ...warn.mock.calls].map((c: unknown[]) => String(c[0])).join('\n')
    for (const secret of [...IPS, IPS.join(', '), PUBLIC_HOST, RUN_APP_HOST, 'run.app', 'example-marsys']) {
      expect(blob).not.toContain(secret)
    }
  })

  it('does not observe non-API requests', async () => {
    setMode('shadow')
    await proxy(xreq('/login', PUBLIC_HOST, IPS[0]))
    await proxy(xreq('/clients/abc', PUBLIC_HOST, IPS[0]))
    expect(info).not.toHaveBeenCalled()
  })

  it('is bounded: one line per host_class+count+path per minute, a key cap, and a total cap', async () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-10-10T00:00:00Z'))
    setMode('shadow')
    for (let i = 0; i < 200; i++) await proxy(xreq('/api/health', PUBLIC_HOST, IPS[0]))
    expect(info).toHaveBeenCalledTimes(1)

    // distinct keys (distinct counts x classes x paths) are capped
    for (let p = 0; p < 400; p++) {
      for (const n of [1, 2, 3]) await proxy(xreq(`/api/r${'abcdefghij'[p % 10]}${'klmnopqrst'[(p / 10) | 0 % 10]}/x`, PUBLIC_HOST, IPS.slice(0, n).join(',')))
    }
    expect(info.mock.calls.length).toBeLessThanOrEqual(XFF_MAX_LINES_PER_MIN)

    // a new minute re-opens the window
    info.mockClear()
    vi.setSystemTime(Date.now() + 61_000)
    await proxy(xreq('/api/health', PUBLIC_HOST, IPS[0]))
    expect(info).toHaveBeenCalledTimes(1)
  })

  it('caps the entry count so a hostile header cannot create unbounded cardinality', async () => {
    setMode('shadow')
    await proxy(xreq('/api/health', PUBLIC_HOST, Array.from({ length: 500 }, (_, i) => `1.1.1.${i}`).join(',')))
    expect(xffLines()[0]).toMatchObject({ count: XFF_COUNT_CAP })
  })

  it('classifyHost: SESSION_GATE_PUBLIC_HOSTS pins the public class', () => {
    expect(classifyHost('x.example.org')).toBe('public')
    expect(classifyHost('amjis-web.run.app:443')).toBe('run_app')
    expect(classifyHost('127.0.0.1:3000')).toBe('other')
    expect(classifyHost('x.example.org', { SESSION_GATE_PUBLIC_HOSTS: 'a.example.org, b.example.org' })).toBe('other')
    expect(classifyHost('B.example.org', { SESSION_GATE_PUBLIC_HOSTS: 'a.example.org, b.example.org' })).toBe('public')
    expect(classifyHost(null)).toBe('other')
  })
})
