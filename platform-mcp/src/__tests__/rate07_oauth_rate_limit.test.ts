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
  rateLimitSubjectForIp,
  consumeBuckets,
  chargeValidatedSubject,
  oauthRateLimit,
  sendRateLimited,
  sendStoreUnavailable,
  RateLimitStoreUnavailable,
  ROUTE_LIMITS,
  rateLimitEnabled,
  trustedProxyHops,
  shedRemaining,
  __resetDenyCacheForTests,
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

/** Build a fetch stub returning a raw body (used for malformed-body cases). */
function rawFetch(body: unknown, status = 200) {
  return vi.fn(async () => ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  })) as unknown as typeof fetch
}

/**
 * Build a fetch stub that models the store's BATCH contract, including its
 * server-side stop-on-deny: buckets are charged in order and evaluation halts
 * at the first denial, so `decisions` is shorter than `buckets` when denied.
 * `deny` decides, per subject_kind, whether that bucket rejects.
 */
function batchFetch(deny: (subjectKind: string) => boolean, retryAfter = 42) {
  return vi.fn(async (_url: string, init: { body: string }) => {
    const specs = JSON.parse(init.body).buckets as Array<Record<string, unknown>>
    const decisions: Array<Record<string, unknown>> = []
    let allowed = true
    for (const s of specs) {
      const kind = String(s['subject_kind'])
      const ok = !deny(kind)
      decisions.push({
        subject_kind: kind,
        allowed: ok,
        limit: s['limit'],
        hits: ok ? 1 : Number(s['limit']) + 1,
        remaining: ok ? Number(s['limit']) - 1 : 0,
        window_seconds: s['window_seconds'],
        retry_after_seconds: retryAfter,
      })
      if (!ok) { allowed = false; break }   // stop-on-deny
    }
    return { ok: true, status: 200, json: async () => ({ allowed, decisions }) }
  }) as unknown as typeof fetch
}

/** Every bucket allowed. */
const allowAll = () => batchFetch(() => false)

/** Parse the bucket specs sent on a given fetch call. */
function sentBuckets(spy: unknown, callIndex = 0): Array<Record<string, unknown>> {
  const calls = (spy as { mock: { calls: unknown[][] } }).mock.calls
  return JSON.parse((calls[callIndex]![1] as { body: string }).body).buckets
}

const ORIGINAL_ENV = { ...process.env }

beforeEach(() => {
  process.env.PLATFORM_URL = 'http://platform.test'
  process.env.MCP_INTERNAL_TOKEN = 'internal-test-token'
  delete process.env.MCP_TRUSTED_PROXY_HOPS
  delete process.env.MCP_OAUTH_RATE_LIMIT_ENABLED
  __resetDenyCacheForTests()
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
    // Both spellings of an IPv4-mapped address must collapse to one bucket.
    expect(normaliseIp('0:0:0:0:0:ffff:203.0.113.9')).toBe('203.0.113.9')
    expect(normaliseIp('::FFFF:203.0.113.9')).toBe('203.0.113.9')
  })
})

describe('RATE-07 §1b — bucket subject bounds key cardinality', () => {
  it('charges IPv6 per /64 — an attacker cannot mint free buckets from its own prefix', () => {
    // A routed /64 is the standard allocation for one VPS or one home line, so
    // per-exact-address keying gives one attacker 2^64 free rows. This is the
    // cardinality bound the migration's boundedness claim actually rests on.
    const a = rateLimitSubjectForIp('2001:db8:abcd:1234:0:0:0:1')
    const b = rateLimitSubjectForIp('2001:db8:abcd:1234:ffff:ffff:ffff:ffff')
    expect(a).toBe(b)
    expect(a).toMatch(/\/64$/)
  })

  it('still separates different /64s', () => {
    expect(rateLimitSubjectForIp('2001:db8:abcd:1234::1'))
      .not.toBe(rateLimitSubjectForIp('2001:db8:abcd:9999::1'))
  })

  it('handles compressed IPv6 without collapsing unrelated prefixes', () => {
    expect(rateLimitSubjectForIp('2001:db8::1')).toBe(rateLimitSubjectForIp('2001:db8:0:0::abcd'))
    expect(rateLimitSubjectForIp('2001:db8::1')).not.toBe(rateLimitSubjectForIp('2001:db9::1'))
    expect(rateLimitSubjectForIp('::1')).toMatch(/\/64$/)
  })

  it('leaves IPv4 EXACT — grouping /24 would punish unrelated ISP customers for no gain', () => {
    // IPv4 addresses are scarce and cost money, so the free-multiplication
    // threat that motivates prefix grouping does not exist there.
    expect(rateLimitSubjectForIp('203.0.113.9')).toBe('203.0.113.9')
    expect(rateLimitSubjectForIp('203.0.113.9')).not.toBe(rateLimitSubjectForIp('203.0.113.10'))
  })

  it('passes through the honest "unknown" sentinel unchanged', () => {
    expect(rateLimitSubjectForIp('unknown')).toBe('unknown')
  })

  it('the gate charges the PREFIX subject, not the raw address', async () => {
    const fetchSpy = allowAll()
    vi.stubGlobal('fetch', fetchSpy)
    await oauthRateLimit('oauth_authorize')(
      makeReq({ 'x-forwarded-for': '2001:db8:abcd:1234::5' }), makeRes(), vi.fn(),
    )
    expect(String(sentBuckets(fetchSpy)[0]!['subject'])).toMatch(/\/64$/)
  })
})

// ── 2. Charging only validated subjects ──────────────────────────────────────

describe('RATE-07 §2 — no charging of unvalidated identifiers', () => {
  it('the pre-handler gate charges ONLY ip and route_global — never a body-supplied client_id', async () => {
    const fetchSpy = allowAll()
    vi.stubGlobal('fetch', fetchSpy)

    const req = makeReq({ 'x-forwarded-for': '203.0.113.9' })
    ;(req as unknown as { body: unknown }).body = { client_id: 'victim-client-id' }
    const res = makeRes()
    const next = vi.fn()

    await oauthRateLimit('oauth_authorize')(req, res, next)

    expect(next).toHaveBeenCalledOnce()
    const buckets = sentBuckets(fetchSpy)
    expect(buckets.map((b) => b['subject_kind'])).toEqual(['ip', 'route_global'])
    expect(buckets.map((b) => b['subject'])).not.toContain('victim-client-id')
  })

  it('sends ONE batched call, not one call per bucket (flood amplification fix)', async () => {
    const fetchSpy = allowAll()
    vi.stubGlobal('fetch', fetchSpy)
    await oauthRateLimit('oauth_authorize')(makeReq({ 'x-forwarded-for': '203.0.113.9' }), makeRes(), vi.fn())
    expect((fetchSpy as unknown as { mock: { calls: unknown[] } }).mock.calls).toHaveLength(1)
    expect(sentBuckets(fetchSpy)).toHaveLength(2)
  })

  it('charges the per-IP bucket FIRST so stop-on-deny protects the shared global ceiling', async () => {
    const fetchSpy = allowAll()
    vi.stubGlobal('fetch', fetchSpy)
    await oauthRateLimit('oauth_register')(makeReq({ 'x-forwarded-for': '203.0.113.9' }), makeRes(), vi.fn())
    // Order is the contract that makes the route-wide ceiling non-weaponisable.
    expect(sentBuckets(fetchSpy)[0]!['subject_kind']).toBe('ip')
  })

  it('chargeValidatedSubject refuses an empty subject rather than merging callers into one bucket', async () => {
    const fetchSpy = allowAll()
    vi.stubGlobal('fetch', fetchSpy)
    const res = makeRes()

    // Fails CLOSED rather than throwing: Express 4 does not catch rejections
    // from an async handler, so a throw would hang the request.
    await expect(chargeValidatedSubject(res, 'oauth_token', 'client', '')).resolves.toBe(false)
    expect(res.statusCode).toBe(503)
    expect((fetchSpy as unknown as { mock: { calls: unknown[] } }).mock.calls).toHaveLength(0)
  })

  it('chargeValidatedSubject charges the exact validated subject under the right kind', async () => {
    const fetchSpy = allowAll()
    vi.stubGlobal('fetch', fetchSpy)

    const res = makeRes()
    expect(await chargeValidatedSubject(res, 'oauth_token', 'principal', 'proven-owner-uid')).toBe(true)
    expect(sentBuckets(fetchSpy)[0]).toMatchObject({
      route: 'oauth_token', subject_kind: 'principal', subject: 'proven-owner-uid',
    })
  })
})

// ── 3. 429 + Retry-After canary ──────────────────────────────────────────────

describe('RATE-07 §3 — 429 and Retry-After', () => {
  it('sendRateLimited emits 429 with an integer Retry-After header and a described body', () => {
    const res = makeRes()
    sendRateLimited(res, 17.2, 'oauth_authorize')
    expect(res.statusCode).toBe(429)
    expect(res.headers['Retry-After']).toBe('18')
    expect(res.body).toMatchObject({ error: 'rate_limit_exceeded', retry_after_seconds: 18 })
    expect(String((res.body as { error_description: string }).error_description)).toContain('oauth_authorize')
  })

  it('Retry-After is never 0 or negative even if the store reports a stale window', () => {
    const res = makeRes()
    sendRateLimited(res, -5, 'oauth_token')
    expect(Number(res.headers['Retry-After'])).toBeGreaterThanOrEqual(1)
  })

  it('the gate 429s when the per-IP bucket is exhausted, and does NOT call the handler', async () => {
    vi.stubGlobal('fetch', batchFetch((k) => k === 'ip', 42))
    const res = makeRes()
    const next = vi.fn()
    await oauthRateLimit('oauth_authorize')(makeReq({ 'x-forwarded-for': '203.0.113.9' }), res, next)

    expect(next).not.toHaveBeenCalled()
    expect(res.statusCode).toBe(429)
    expect(res.headers['Retry-After']).toBe('42')
  })

  it('the gate 429s on the route-wide global ceiling even when the per-IP bucket is fine', async () => {
    vi.stubGlobal('fetch', batchFetch((k) => k === 'route_global', 12))
    const res = makeRes()
    const next = vi.fn()
    await oauthRateLimit('oauth_authorize')(makeReq({ 'x-forwarded-for': '203.0.113.9' }), res, next)

    expect(next).not.toHaveBeenCalled()
    expect(res.statusCode).toBe(429)
    expect(res.headers['Retry-After']).toBe('12')
  })

  it('SECURITY: a per-IP denial does NOT charge the shared route_global bucket', async () => {
    // The fleet-wide DoS lever an adversarial review found in the first draft:
    // one address pouring its REJECTED traffic into the global ceiling could
    // 429 client registration for every user on earth. Stop-on-deny caps any
    // one address's contribution to the global bucket at its own per-IP limit.
    const fetchSpy = batchFetch((k) => k === 'ip')
    vi.stubGlobal('fetch', fetchSpy)

    await oauthRateLimit('oauth_register')(makeReq({ 'x-forwarded-for': '203.0.113.9' }), makeRes(), vi.fn())

    const body = await (await (fetchSpy as unknown as typeof fetch)(
      'x' as never, { body: JSON.stringify({ buckets: sentBuckets(fetchSpy) }) } as never,
    )).json() as { decisions: Array<{ subject_kind: string }> }
    // The store charged the ip bucket and STOPPED — route_global never charged.
    expect(body.decisions.map((d) => d.subject_kind)).toEqual(['ip'])
  })
})

// ── 3b. Deny-only load shed ──────────────────────────────────────────────────

describe('RATE-07 §3b — deny-only load shed (flood does not amplify into the DB pool)', () => {
  it('a repeat offender is refused WITHOUT a further store round trip', async () => {
    const fetchSpy = batchFetch((k) => k === 'ip', 30)
    vi.stubGlobal('fetch', fetchSpy)
    const gate = oauthRateLimit('oauth_authorize')

    const r1 = makeRes()
    await gate(makeReq({ 'x-forwarded-for': '203.0.113.9' }), r1, vi.fn())
    expect(r1.statusCode).toBe(429)
    const callsAfterFirst = (fetchSpy as unknown as { mock: { calls: unknown[] } }).mock.calls.length

    const r2 = makeRes()
    const next2 = vi.fn()
    await gate(makeReq({ 'x-forwarded-for': '203.0.113.9' }), r2, next2)
    expect(r2.statusCode).toBe(429)
    expect(next2).not.toHaveBeenCalled()
    // The whole point: no additional call to the platform / DB pool.
    expect((fetchSpy as unknown as { mock: { calls: unknown[] } }).mock.calls).toHaveLength(callsAfterFirst)
  })

  it('the shed can only DENY — it never lets a request through on its own', async () => {
    // A cold cache decides nothing; the store is still consulted.
    expect(shedRemaining('oauth_authorize', '203.0.113.9')).toBe(0)
    const fetchSpy = allowAll()
    vi.stubGlobal('fetch', fetchSpy)
    const next = vi.fn()
    await oauthRateLimit('oauth_authorize')(makeReq({ 'x-forwarded-for': '203.0.113.9' }), makeRes(), next)
    expect(next).toHaveBeenCalledOnce()
    expect((fetchSpy as unknown as { mock: { calls: unknown[] } }).mock.calls).toHaveLength(1)
  })

  it('a route_global denial is NOT cached per-subject (one global outage must not fan out)', async () => {
    const fetchSpy = batchFetch((k) => k === 'route_global', 30)
    vi.stubGlobal('fetch', fetchSpy)
    const gate = oauthRateLimit('oauth_authorize')

    await gate(makeReq({ 'x-forwarded-for': '203.0.113.9' }), makeRes(), vi.fn())
    expect(shedRemaining('oauth_authorize', '203.0.113.9')).toBe(0)
  })

  it('the shed does not leak across routes or subjects', async () => {
    vi.stubGlobal('fetch', batchFetch((k) => k === 'ip', 30))
    await oauthRateLimit('oauth_authorize')(makeReq({ 'x-forwarded-for': '203.0.113.9' }), makeRes(), vi.fn())
    expect(shedRemaining('oauth_authorize', '203.0.113.9')).toBeGreaterThan(0)
    expect(shedRemaining('oauth_token', '203.0.113.9')).toBe(0)
    expect(shedRemaining('oauth_authorize', '198.51.100.1')).toBe(0)
  })
})

// ── 4. Fail-closed ───────────────────────────────────────────────────────────

describe('RATE-07 §4 — fail CLOSED on store failure', () => {
  const ONE = [{ route: 'oauth_token', subjectKind: 'ip' as const, subject: '1.1.1.1', limit: 10, windowSeconds: 60 }]

  it('consumeBuckets throws (never returns allowed) when the store is unreachable', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('ECONNREFUSED') }) as unknown as typeof fetch)
    await expect(consumeBuckets(ONE)).rejects.toBeInstanceOf(RateLimitStoreUnavailable)
  })

  it('consumeBuckets throws on a non-2xx store response', async () => {
    vi.stubGlobal('fetch', rawFetch({ error: 'boom' }, 500))
    await expect(consumeBuckets(ONE)).rejects.toBeInstanceOf(RateLimitStoreUnavailable)
  })

  it('consumeBuckets throws on a body with no explicit boolean decision (never coerces)', async () => {
    for (const body of [{}, { allowed: 'yes', decisions: [] }, { allowed: 1, decisions: [] }, { allowed: null }, { allowed: true }]) {
      vi.stubGlobal('fetch', rawFetch(body))
      await expect(consumeBuckets(ONE)).rejects.toBeInstanceOf(RateLimitStoreUnavailable)
    }
  })

  it('consumeBuckets throws on a non-JSON body', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({ ok: true, status: 200, json: async () => { throw new Error('not json') } })) as unknown as typeof fetch,
    )
    await expect(consumeBuckets(ONE)).rejects.toBeInstanceOf(RateLimitStoreUnavailable)
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
    expect(await chargeValidatedSubject(res, 'oauth_register', 'principal', 'uid-123')).toBe(false)
    expect(res.statusCode).toBe(503)
  })

  it('the gate answers with 503 rather than hanging if identity derivation itself throws', async () => {
    vi.stubGlobal('fetch', allowAll())
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

  it('the kill switch is DEFAULT ON, and only an explicit "false" disables it', () => {
    expect(rateLimitEnabled()).toBe(true)
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
    const fetchSpy = allowAll()
    vi.stubGlobal('fetch', fetchSpy)
    const next = vi.fn()
    await oauthRateLimit('oauth_authorize')(makeReq({ 'x-forwarded-for': '1.1.1.1' }), makeRes(), next)
    expect(next).toHaveBeenCalledOnce()
    expect((fetchSpy as unknown as { mock: { calls: unknown[] } }).mock.calls).toHaveLength(0)
  })

  // ── DISABLED PATH IS A TRUE NO-OP ──────────────────────────────────────────
  //
  // This PR SHIPS WITH `MCP_OAUTH_RATE_LIMIT_ENABLED=false` in deploy.yml (see
  // the deploy-mcp env_vars block and the PR body's FOLLOW-UP REQUIRED note).
  // The reason is an ordering window: `deploy-mcp` and `deploy-web` both depend
  // only on `migrate` and therefore run in PARALLEL, and deploy-mcp (a small TS
  // build) normally promotes traffic FIRST. In that window the fail-closed gate
  // would be calling `/api/mcp/rate-limit/check` — a route THIS PR creates on
  // amjis-web — against the OLD web revision, which 404s, which the gate
  // correctly reads as "store unavailable" and answers 503 on all five OAuth
  // mutation endpoints. Shipping disabled removes that window entirely.
  //
  // That promise is only worth anything if "disabled" means EXACTLY the
  // pre-PR behaviour: no store call, no response written, no throw, control
  // handed straight to the handler. The tests below assert that for BOTH
  // entrypoints, INCLUDING the inputs that would otherwise take a fail-closed
  // 503 branch. Do not delete them when the flag is flipped on: they are what
  // makes the flag a real rollback lever rather than a documented intention.
  it('when disabled, the gate writes NOTHING to the response even if the store is unreachable', async () => {
    process.env.MCP_OAUTH_RATE_LIMIT_ENABLED = 'false'
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('store down') }) as unknown as typeof fetch)
    const res = makeRes()
    const next = vi.fn()
    await oauthRateLimit('oauth_token')(makeReq({ 'x-forwarded-for': '1.1.1.1' }), res, next)
    expect(next).toHaveBeenCalledOnce()
    expect(res.statusCode).toBeNull()
    expect(res.body).toBeUndefined()
    expect(res.headers).toEqual({})
  })

  it('when disabled, chargeValidatedSubject allows, makes NO store call, and writes nothing', async () => {
    process.env.MCP_OAUTH_RATE_LIMIT_ENABLED = 'false'
    const fetchSpy = vi.fn(async () => { throw new Error('store down') }) as unknown as typeof fetch
    vi.stubGlobal('fetch', fetchSpy)
    const res = makeRes()
    expect(await chargeValidatedSubject(res, 'oauth_register', 'principal', 'uid-123')).toBe(true)
    expect((fetchSpy as unknown as { mock: { calls: unknown[] } }).mock.calls).toHaveLength(0)
    expect(res.statusCode).toBeNull()
    expect(res.body).toBeUndefined()
  })

  it('when disabled, even an EMPTY validated subject is a pass-through, not a 503', async () => {
    // Enabled, this input is the deliberate fail-closed BUG branch (proved
    // above at "an empty validated subject fails CLOSED"). Disabled, the kill
    // switch is checked FIRST, so the branch is unreachable and a caller that
    // resolved no identity behaves exactly as it did before this PR existed.
    process.env.MCP_OAUTH_RATE_LIMIT_ENABLED = 'false'
    vi.stubGlobal('fetch', allowAll())
    const res = makeRes()
    expect(await chargeValidatedSubject(res, 'oauth_token', 'principal', '')).toBe(true)
    expect(res.statusCode).toBeNull()
  })

  it('when disabled, a flood leaves the per-instance deny cache completely untouched', async () => {
    // The shed cache is the module's only mutable process state. If the gate
    // could still populate it while disabled, "disabled" would not be a true
    // no-op — flipping the flag back on would inherit stale denials.
    process.env.MCP_OAUTH_RATE_LIMIT_ENABLED = 'false'
    vi.stubGlobal('fetch', batchFetch((k) => k === 'ip'))
    const next = vi.fn()
    for (let i = 0; i < 25; i++) {
      await oauthRateLimit('oauth_authorize')(makeReq({ 'x-forwarded-for': '203.0.113.9' }), makeRes(), next)
    }
    expect(next).toHaveBeenCalledTimes(25)
    expect(shedRemaining('oauth_authorize', rateLimitSubjectForIp('203.0.113.9'))).toBe(0)
  })
})

// ── 5. Limit table sanity ────────────────────────────────────────────────────

describe('RATE-07 §5 — route limit table', () => {
  it('defines a limit profile for every distinct OAuth bucket', () => {
    // No 'oauth_refresh': /refresh shares the oauth_token bucket (see the
    // ROUTE_LIMITS comment) so one operation is not budgeted twice.
    expect(Object.keys(ROUTE_LIMITS).sort()).toEqual(
      ['oauth_authorize', 'oauth_callback', 'oauth_register', 'oauth_token'].sort(),
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
