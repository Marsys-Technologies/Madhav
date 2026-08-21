/**
 * RATE-07 — fleet-wide OAuth rate limiting (PARIŚEṢA-V4 GA-2 ruling).
 *
 * Covers the "minimum proof before PR" checklist from
 * `F06_RATE07_ARCHITECTURE_DECISION.md`:
 *
 *   1. trusted-header / proxy-spoofing and identity-source tests
 *   2. client/principal validation BEFORE subject charging
 *   3. 429 + Retry-After canary
 *   4. fail-closed store-failure behaviour
 *   5. route wiring for all five OAuth mutation endpoints
 *
 * Cross-instance atomicity and TTL/key cleanup are properties of the SQL, and
 * are proved in `platform/src/lib/__tests__/mcp/oauth_rate_limit.test.ts`
 * (structural + simulated concurrency) and
 * `platform/src/lib/__tests__/mcp/oauth_rate_limit.db.test.ts` (real Postgres,
 * opt-in). They cannot be proved from this side of the HTTP boundary and this
 * file does not pretend to.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import type { Request, Response } from 'express'

import {
  deriveClientIdentity,
  normaliseIp,
  consumeBucket,
  chargeValidatedSubject,
  oauthRateLimit,
  sendRateLimited,
  sendStoreUnavailable,
  RateLimitStoreUnavailable,
  ROUTE_LIMITS,
  rateLimitEnabled,
  trustedProxyHops,
} from '../lib/oauth_rate_limit.js'

// ── Test doubles ─────────────────────────────────────────────────────────────

function makeReq(headers: Record<string, string | string[]>, remoteAddress?: string): Request {
  return {
    headers,
    socket: remoteAddress ? { remoteAddress } : {},
  } as unknown as Request
}

interface FakeRes {
  statusCode: number | null
  headers: Record<string, string>
  body: unknown
  status(code: number): FakeRes
  json(payload: unknown): FakeRes
  setHeader(name: string, value: string): void
}

function makeRes(): FakeRes & Response {
  const res: FakeRes = {
    statusCode: null,
    headers: {},
    body: undefined,
    status(code: number) {
      this.statusCode = code
      return this
    },
    json(payload: unknown) {
      this.body = payload
      return this
    },
    setHeader(name: string, value: string) {
      this.headers[name] = value
    },
  }
  return res as FakeRes & Response
}

/** Build a fetch stub that returns a decision body. */
function decisionFetch(decision: Record<string, unknown>, status = 200) {
  return vi.fn(async () => ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => decision,
  })) as unknown as typeof fetch
}

const ORIGINAL_ENV = { ...process.env }

beforeEach(() => {
  process.env.PLATFORM_URL = 'http://platform.test'
  process.env.MCP_INTERNAL_TOKEN = 'internal-test-token'
  delete process.env.MCP_TRUSTED_PROXY_HOPS
  delete process.env.MCP_OAUTH_RATE_LIMIT_ENABLED
})

afterEach(() => {
  vi.restoreAllMocks()
  process.env = { ...ORIGINAL_ENV }
})

// ── 1. Identity derivation / spoofing ────────────────────────────────────────

describe('RATE-07 §1 — client identity is not caller-assertable', () => {
  it('NEVER uses the leftmost X-Forwarded-For entry (the spoofable one)', () => {
    // A client that sends `X-Forwarded-For: 1.2.3.4` gets its real peer APPENDED
    // by Cloud Run. Taking the left value would let it pick any bucket it likes.
    const id = deriveClientIdentity(makeReq({ 'x-forwarded-for': '1.2.3.4, 203.0.113.9' }))
    expect(id.ip).toBe('203.0.113.9')
    expect(id.ip).not.toBe('1.2.3.4')
    expect(id.source).toBe('xff')
  })

  it('two different spoofed prefixes from the same real peer land in the SAME bucket', () => {
    const a = deriveClientIdentity(makeReq({ 'x-forwarded-for': '10.0.0.1, 203.0.113.9' }))
    const b = deriveClientIdentity(makeReq({ 'x-forwarded-for': '8.8.8.8, 9.9.9.9, 203.0.113.9' }))
    expect(a.ip).toBe(b.ip)
  })

  it('a caller cannot escape its bucket by injecting a long forged chain', () => {
    const forged = Array.from({ length: 50 }, (_, i) => `10.0.0.${i}`).join(', ')
    const id = deriveClientIdentity(makeReq({ 'x-forwarded-for': `${forged}, 203.0.113.9` }))
    expect(id.ip).toBe('203.0.113.9')
  })

  it('ignores single-value client-assertable headers entirely', () => {
    // X-Real-IP / CF-Connecting-IP / True-Client-IP have no appending hop behind
    // Cloud Run — they are verbatim caller input.
    const id = deriveClientIdentity(
      makeReq(
        {
          'x-real-ip': '1.1.1.1',
          'cf-connecting-ip': '2.2.2.2',
          'true-client-ip': '3.3.3.3',
          'x-forwarded-for': '203.0.113.9',
        },
        '198.51.100.7',
      ),
    )
    expect(id.ip).toBe('203.0.113.9')
  })

  it('honours MCP_TRUSTED_PROXY_HOPS by counting from the RIGHT', () => {
    process.env.MCP_TRUSTED_PROXY_HOPS = '2'
    expect(trustedProxyHops()).toBe(2)
    // chain: client, lb, cloudrun-appended  →  with 2 trusted hops, the client is
    // the entry two in from the right.
    const id = deriveClientIdentity(makeReq({ 'x-forwarded-for': '203.0.113.9, 10.1.1.1, 10.2.2.2' }))
    expect(id.ip).toBe('10.1.1.1')
  })

  it('clamps to the leftmost entry when the chain is shorter than the hop count (never wraps)', () => {
    process.env.MCP_TRUSTED_PROXY_HOPS = '5'
    const id = deriveClientIdentity(makeReq({ 'x-forwarded-for': '203.0.113.9' }))
    expect(id.ip).toBe('203.0.113.9')
  })

  it('rejects an out-of-range or non-integer hop setting rather than trusting it', () => {
    for (const bad of ['0', '-1', '9', 'abc', '1.5', '']) {
      process.env.MCP_TRUSTED_PROXY_HOPS = bad
      expect(trustedProxyHops()).toBe(1)
    }
  })

  it('reports source=socket when no XFF is present, so a canary can notice', () => {
    const id = deriveClientIdentity(makeReq({}, '198.51.100.7'))
    expect(id).toEqual({ ip: '198.51.100.7', source: 'socket' })
  })

  it('reports source=unknown rather than inventing an address', () => {
    expect(deriveClientIdentity(makeReq({}))).toEqual({ ip: 'unknown', source: 'unknown' })
  })

  it('joins repeated X-Forwarded-For headers in order and still reads from the right', () => {
    const id = deriveClientIdentity(makeReq({ 'x-forwarded-for': ['1.2.3.4', '203.0.113.9'] }))
    expect(id.ip).toBe('203.0.113.9')
  })

  it('normalises equivalent spellings so one client cannot occupy two buckets', () => {
    expect(normaliseIp('::ffff:203.0.113.9')).toBe('203.0.113.9')
    expect(normaliseIp('203.0.113.9:44321')).toBe('203.0.113.9')
    expect(normaliseIp('[2001:db8::1]:443')).toBe('2001:db8::1')
    expect(normaliseIp('  203.0.113.9  ')).toBe('203.0.113.9')
    // A bare IPv6 must survive intact — it has many colons, not one.
    expect(normaliseIp('2001:db8::1')).toBe('2001:db8::1')
  })
})

// ── 2. Charging only validated subjects ──────────────────────────────────────

describe('RATE-07 §2 — no charging of unvalidated identifiers', () => {
  it('the pre-handler gate charges ONLY ip and route_global — never a body-supplied client_id', async () => {
    const fetchSpy = decisionFetch({ allowed: true, limit: 30, hits: 1, remaining: 29, window_seconds: 60, retry_after_seconds: 60 })
    vi.stubGlobal('fetch', fetchSpy)

    const req = makeReq({ 'x-forwarded-for': '203.0.113.9' })
    ;(req as unknown as { body: unknown }).body = { client_id: 'victim-client-id' }
    const res = makeRes()
    const next = vi.fn()

    await oauthRateLimit('oauth_authorize')(req, res, next)

    expect(next).toHaveBeenCalledOnce()
    const kinds = (fetchSpy as unknown as { mock: { calls: unknown[][] } }).mock.calls.map(
      (c) => JSON.parse((c[1] as { body: string }).body).subject_kind,
    )
    expect(new Set(kinds)).toEqual(new Set(['ip', 'route_global']))
    const subjects = (fetchSpy as unknown as { mock: { calls: unknown[][] } }).mock.calls.map(
      (c) => JSON.parse((c[1] as { body: string }).body).subject,
    )
    // The victim's client_id must appear NOWHERE in what was charged.
    expect(subjects).not.toContain('victim-client-id')
  })

  it('chargeValidatedSubject refuses an empty subject rather than merging callers into one bucket', async () => {
    const fetchSpy = decisionFetch({ allowed: true })
    vi.stubGlobal('fetch', fetchSpy)
    const res = makeRes()

    // Fails CLOSED rather than throwing: Express 4 does not catch rejections
    // from an async handler, so a throw would hang the request rather than
    // answer it. The refusal must still never reach the store.
    await expect(chargeValidatedSubject(res, 'oauth_token', 'client', '')).resolves.toBe(false)
    expect(res.statusCode).toBe(503)
    expect((fetchSpy as unknown as { mock: { calls: unknown[] } }).mock.calls).toHaveLength(0)
  })

  it('the gate answers with 503 rather than hanging if identity derivation itself throws', async () => {
    vi.stubGlobal('fetch', decisionFetch({ allowed: true }))
    // A request object whose header access explodes — stands in for any
    // unexpected throw inside the middleware.
    const hostile = {
      get headers(): never { throw new Error('boom') },
      socket: {},
    } as unknown as Request
    const res = makeRes()
    const next = vi.fn()

    await expect(oauthRateLimit('oauth_authorize')(hostile, res, next)).resolves.toBeUndefined()
    expect(next).not.toHaveBeenCalled()
    expect(res.statusCode).toBe(503)
  })

  it('chargeValidatedSubject charges the exact validated subject under the right kind', async () => {
    const fetchSpy = decisionFetch({ allowed: true, limit: 120, hits: 3, remaining: 117, window_seconds: 60, retry_after_seconds: 60 })
    vi.stubGlobal('fetch', fetchSpy)

    const res = makeRes()
    const ok = await chargeValidatedSubject(res, 'oauth_token', 'client', 'proven-client-id')
    expect(ok).toBe(true)

    const sent = JSON.parse(
      ((fetchSpy as unknown as { mock: { calls: unknown[][] } }).mock.calls[0]![1] as { body: string }).body,
    )
    expect(sent).toMatchObject({ route: 'oauth_token', subject_kind: 'client', subject: 'proven-client-id' })
  })
})

// ── 3. 429 + Retry-After canary ──────────────────────────────────────────────

describe('RATE-07 §3 — 429 and Retry-After', () => {
  it('sendRateLimited emits 429 with an integer Retry-After header and a described body', () => {
    const res = makeRes()
    sendRateLimited(res, 17.2, 'oauth_authorize')
    expect(res.statusCode).toBe(429)
    expect(res.headers['Retry-After']).toBe('18')
    expect(Number.isInteger(Number(res.headers['Retry-After']))).toBe(true)
    expect(res.body).toMatchObject({ error: 'rate_limit_exceeded', retry_after_seconds: 18 })
    expect(String((res.body as { error_description: string }).error_description)).toContain('oauth_authorize')
  })

  it('Retry-After is never 0 or negative even if the store reports a stale window', () => {
    const res = makeRes()
    sendRateLimited(res, -5, 'oauth_token')
    expect(Number(res.headers['Retry-After'])).toBeGreaterThanOrEqual(1)
  })

  it('the gate 429s when the per-IP bucket is exhausted, and does NOT call the handler', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (_url: string, init: { body: string }) => {
        const kind = JSON.parse(init.body).subject_kind
        return {
          ok: true,
          status: 200,
          json: async () =>
            kind === 'ip'
              ? { allowed: false, limit: 30, hits: 31, remaining: 0, window_seconds: 60, retry_after_seconds: 42 }
              : { allowed: true, limit: 600, hits: 5, remaining: 595, window_seconds: 60, retry_after_seconds: 60 },
        }
      }) as unknown as typeof fetch,
    )

    const res = makeRes()
    const next = vi.fn()
    await oauthRateLimit('oauth_authorize')(makeReq({ 'x-forwarded-for': '203.0.113.9' }), res, next)

    expect(next).not.toHaveBeenCalled()
    expect(res.statusCode).toBe(429)
    expect(res.headers['Retry-After']).toBe('42')
  })

  it('the gate 429s on the route-wide global ceiling even when the per-IP bucket is fine', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async (_url: string, init: { body: string }) => {
        const kind = JSON.parse(init.body).subject_kind
        return {
          ok: true,
          status: 200,
          json: async () =>
            kind === 'route_global'
              ? { allowed: false, limit: 600, hits: 601, remaining: 0, window_seconds: 60, retry_after_seconds: 12 }
              : { allowed: true, limit: 30, hits: 1, remaining: 29, window_seconds: 60, retry_after_seconds: 60 },
        }
      }) as unknown as typeof fetch,
    )

    const res = makeRes()
    const next = vi.fn()
    await oauthRateLimit('oauth_authorize')(makeReq({ 'x-forwarded-for': '203.0.113.9' }), res, next)

    expect(next).not.toHaveBeenCalled()
    expect(res.statusCode).toBe(429)
  })

  it('charges BOTH buckets even when one already denies (no free rides off a global rejection)', async () => {
    const fetchSpy = vi.fn(async (_url: string, init: { body: string }) => {
      const kind = JSON.parse(init.body).subject_kind
      return {
        ok: true,
        status: 200,
        json: async () =>
          kind === 'route_global'
            ? { allowed: false, limit: 600, hits: 601, remaining: 0, window_seconds: 60, retry_after_seconds: 12 }
            : { allowed: true, limit: 30, hits: 1, remaining: 29, window_seconds: 60, retry_after_seconds: 60 },
      }
    }) as unknown as typeof fetch
    vi.stubGlobal('fetch', fetchSpy)

    await oauthRateLimit('oauth_authorize')(makeReq({ 'x-forwarded-for': '203.0.113.9' }), makeRes(), vi.fn())
    expect((fetchSpy as unknown as { mock: { calls: unknown[] } }).mock.calls).toHaveLength(2)
  })
})

// ── 4. Fail-closed ───────────────────────────────────────────────────────────

describe('RATE-07 §4 — fail CLOSED on store failure', () => {
  it('consumeBucket throws (never returns allowed) when the store is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('ECONNREFUSED') }) as unknown as typeof fetch)
    await expect(
      consumeBucket({ route: 'oauth_token', subjectKind: 'ip', subject: '1.1.1.1', limit: 10, windowSeconds: 60 }),
    ).rejects.toBeInstanceOf(RateLimitStoreUnavailable)
  })

  it('consumeBucket throws on a non-2xx store response', async () => {
    vi.stubGlobal('fetch', decisionFetch({ error: 'boom' }, 500))
    await expect(
      consumeBucket({ route: 'oauth_token', subjectKind: 'ip', subject: '1.1.1.1', limit: 10, windowSeconds: 60 }),
    ).rejects.toBeInstanceOf(RateLimitStoreUnavailable)
  })

  it('consumeBucket throws on a body with no explicit boolean decision (never coerces)', async () => {
    for (const body of [{}, { allowed: 'yes' }, { allowed: 1 }, { allowed: null }]) {
      vi.stubGlobal('fetch', decisionFetch(body))
      await expect(
        consumeBucket({ route: 'oauth_token', subjectKind: 'ip', subject: '1.1.1.1', limit: 10, windowSeconds: 60 }),
      ).rejects.toBeInstanceOf(RateLimitStoreUnavailable)
    }
  })

  it('consumeBucket throws on a non-JSON body', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({ ok: true, status: 200, json: async () => { throw new Error('not json') } })) as unknown as typeof fetch,
    )
    await expect(
      consumeBucket({ route: 'oauth_token', subjectKind: 'ip', subject: '1.1.1.1', limit: 10, windowSeconds: 60 }),
    ).rejects.toBeInstanceOf(RateLimitStoreUnavailable)
  })

  it('the gate 503s (does NOT pass through) when the store is down', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('down') }) as unknown as typeof fetch)
    const res = makeRes()
    const next = vi.fn()
    await oauthRateLimit('oauth_token')(makeReq({ 'x-forwarded-for': '203.0.113.9' }), res, next)

    expect(next).not.toHaveBeenCalled()
    expect(res.statusCode).toBe(503)
    expect(res.headers['Retry-After']).toBe('30')
    expect(res.body).toMatchObject({ error: 'temporarily_unavailable' })
  })

  it('503 is distinguishable from 429 — an outage is not reported as abuse', () => {
    const a = makeRes(); sendStoreUnavailable(a)
    const b = makeRes(); sendRateLimited(b, 5, 'oauth_token')
    expect(a.statusCode).toBe(503)
    expect(b.statusCode).toBe(429)
    expect((a.body as { error: string }).error).not.toBe((b.body as { error: string }).error)
  })

  it('chargeValidatedSubject fails closed too, returning false after writing 503', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('down') }) as unknown as typeof fetch)
    const res = makeRes()
    const ok = await chargeValidatedSubject(res, 'oauth_register', 'principal', 'uid-123')
    expect(ok).toBe(false)
    expect(res.statusCode).toBe(503)
  })

  it('the kill switch is DEFAULT ON, and only an explicit "false" disables it', () => {
    expect(rateLimitEnabled()).toBe(true)
    // Anything that is not literally "false" leaves the control ON — including
    // an empty string and the near-misses an operator might reach for ('0',
    // 'no', 'off'). A security control must not be switchable off by accident.
    for (const v of ['', 'true', 'TRUE', '0', 'no', 'off', 'yes', 'disabled']) {
      process.env.MCP_OAUTH_RATE_LIMIT_ENABLED = v
      expect(rateLimitEnabled(), `value ${JSON.stringify(v)} must NOT disable the limiter`).toBe(true)
    }
    process.env.MCP_OAUTH_RATE_LIMIT_ENABLED = 'false'
    expect(rateLimitEnabled()).toBe(false)
    process.env.MCP_OAUTH_RATE_LIMIT_ENABLED = 'FALSE'
    expect(rateLimitEnabled()).toBe(false)
  })

  it('when disabled, the gate passes through and makes NO store call', async () => {
    process.env.MCP_OAUTH_RATE_LIMIT_ENABLED = 'false'
    const fetchSpy = decisionFetch({ allowed: true })
    vi.stubGlobal('fetch', fetchSpy)
    const next = vi.fn()
    await oauthRateLimit('oauth_authorize')(makeReq({ 'x-forwarded-for': '1.1.1.1' }), makeRes(), next)
    expect(next).toHaveBeenCalledOnce()
    expect((fetchSpy as unknown as { mock: { calls: unknown[] } }).mock.calls).toHaveLength(0)
  })
})

// ── 5. Limit table sanity ────────────────────────────────────────────────────

describe('RATE-07 §5 — route limit table', () => {
  it('defines a limit for every one of the five OAuth mutation routes', () => {
    expect(Object.keys(ROUTE_LIMITS).sort()).toEqual(
      ['oauth_authorize', 'oauth_callback', 'oauth_refresh', 'oauth_register', 'oauth_token'].sort(),
    )
  })

  it('every route has a global ceiling strictly above its per-IP limit', () => {
    for (const [route, l] of Object.entries(ROUTE_LIMITS)) {
      expect(l.perIp, `${route}.perIp`).toBeGreaterThan(0)
      expect(l.global, `${route}.global`).toBeGreaterThan(l.perIp)
      expect(l.windowSeconds, `${route}.windowSeconds`).toBeGreaterThan(0)
    }
  })

  it('oauthRateLimit refuses an unknown route key rather than silently not limiting', () => {
    expect(() => oauthRateLimit('nope' as never)).toThrow(/unknown route key/)
  })
})
