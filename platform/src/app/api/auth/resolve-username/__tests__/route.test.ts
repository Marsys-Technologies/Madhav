// @vitest-environment node
/**
 * SS N-373 item 4 / SS N-403 — POST /api/auth/resolve-username is public (outside
 * the proxy matcher) and turns a username into an email address. It MUST keep
 * returning the email for username login (SS ruling), so the defence is:
 *   - TWO limits, both before the lookup: per trusted IP (60/min, keyed on the
 *     TRUSTED client IP, never the client-controlled leftmost X-Forwarded-For
 *     entry) and per REQUESTED username (5/min, global, keyed on the sha256 of
 *     the normalised name). Browser logins share the single Firebase Hosting
 *     address, so a tight per-IP limit used to throttle everyone together.
 *   - a uniform response time for found / not-found / lookup-error,
 *   - both checks run BEFORE the lookup, so a throttled response can never
 *     depend on whether the username exists.
 */
import { createHash } from 'node:crypto'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => queryMock(...a) }))

// Records every limiter the route constructs and every key it checks, so tests
// can assert the key derivation and the memory bound without touching the route.
interface RecordedLimiter {
  opts: { limit: number; windowMs: number; maxEntries: number }
  keys: string[]
  size: number
}
const rec = vi.hoisted(() => ({
  instances: [] as unknown[],
  forcedNow: undefined as undefined | (() => number),
}))
vi.mock('@/lib/security/bounded_rate_limiter', async (importOriginal) => {
  const orig = await importOriginal<typeof import('@/lib/security/bounded_rate_limiter')>()
  class Recording extends orig.BoundedRateLimiter {
    readonly keys: string[] = []
    readonly opts: { limit: number; windowMs: number; maxEntries: number }
    constructor(opts: ConstructorParameters<typeof orig.BoundedRateLimiter>[0]) {
      super({ ...opts, now: rec.forcedNow ?? opts.now })
      this.opts = { limit: opts.limit, windowMs: opts.windowMs, maxEntries: opts.maxEntries }
      rec.instances.push(this)
    }
    check(key: string) {
      this.keys.push(key)
      return super.check(key)
    }
  }
  return { ...orig, BoundedRateLimiter: Recording }
})
function limiters(): { ip: RecordedLimiter; username: RecordedLimiter } {
  const all = rec.instances as RecordedLimiter[]
  return {
    ip: all.find((l) => l.opts.limit === 60) as RecordedLimiter,
    username: all.find((l) => l.opts.limit === 5) as RecordedLimiter,
  }
}

// Documented route constants (kept in step with the route; see route.ts).
const MIN_MS = 400
const JITTER_MS = 75
const IP_RPM = 60
const USERNAME_RPM = 5
const MAX_TRACKED = 10_000
const SHARED_HOSTING = '203.0.113.9'

const sha = (s: string) => createHash('sha256').update(s).digest('hex')

function req(username: unknown, xff?: string): Request {
  const headers: Record<string, string> = { 'content-type': 'application/json' }
  if (xff !== undefined) headers['x-forwarded-for'] = xff
  return new Request('http://localhost/api/auth/resolve-username', {
    method: 'POST',
    headers,
    body: JSON.stringify({ username }),
  })
}

async function load() {
  return (await import('@/app/api/auth/resolve-username/route')) as { POST: (r: Request) => Promise<Response> }
}

beforeEach(() => {
  vi.resetModules()
  rec.instances.length = 0
  rec.forcedNow = undefined
  queryMock.mockReset()
  vi.useFakeTimers()
})
afterEach(() => {
  vi.useRealTimers()
  vi.restoreAllMocks()
})

/** Run a request to completion under fake timers; returns the response and the virtual ms it took. */
async function timed(route: { POST: (r: Request) => Promise<Response> }, r: Request) {
  const t0 = Date.now()
  let done = false
  const p = route.POST(r).then((x) => { done = true; return x })
  let elapsed = 0
  while (!done && elapsed < 5_000) {
    await vi.advanceTimersByTimeAsync(1)
    elapsed += 1
  }
  const res = await p
  return { res, ms: Date.now() - t0 }
}

/** Like `timed` but without measuring: one virtual jump past the 400ms floor + jitter. */
async function run(route: { POST: (r: Request) => Promise<Response> }, r: Request) {
  const p = route.POST(r)
  await vi.advanceTimersByTimeAsync(MIN_MS + JITTER_MS + 25)
  return p
}

/** Mocked DB: only `alice` and `abhi` exist. */
function dbWithAccounts() {
  queryMock.mockImplementation(async (_sql: string, params: string[]) => {
    const name = String(params[0]).toLowerCase()
    return name === 'alice' || name === 'abhi'
      ? { rows: [{ email: `${name}@b.test`, status: 'active' }] }
      : { rows: [] }
  })
}

describe('POST /api/auth/resolve-username', () => {
  it('keeps the success contract: found -> 200 { email }', async () => {
    queryMock.mockResolvedValue({ rows: [{ email: 'a@b.test', status: 'active' }] })
    const { res } = await timed(await load(), req('abhi', '203.0.113.9'))
    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ email: 'a@b.test' })
  })

  it('not found -> 404 in the canonical error envelope', async () => {
    queryMock.mockResolvedValue({ rows: [] })
    const { res } = await timed(await load(), req('nobody', '203.0.113.9'))
    expect(res.status).toBe(404)
    const body = await res.json()
    expect(body.error?.code).toBe('DATA_NOT_FOUND')
  })

  it('bad input is rejected before any lookup', async () => {
    const route = await load()
    const { res } = await timed(route, req('   ', '203.0.113.9'))
    expect(res.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
  })

  describe('uniform response time', () => {
    it('found, not-found and lookup-error all take at least MIN_MS (constant-time padding)', async () => {
      vi.spyOn(Math, 'random').mockReturnValue(0)
      const route = await load()

      queryMock.mockResolvedValueOnce({ rows: [{ email: 'a@b.test', status: 'active' }] })
      const found = await timed(route, req('abhi', '203.0.113.1'))
      queryMock.mockResolvedValueOnce({ rows: [] })
      const missing = await timed(route, req('nobody', '203.0.113.2'))
      queryMock.mockRejectedValueOnce(new Error('db down'))
      const failed = await timed(route, req('abhi', '203.0.113.3'))

      expect(found.res.status).toBe(200)
      expect(missing.res.status).toBe(404)
      expect(failed.res.status).toBe(503)
      for (const r of [found, missing, failed]) expect(r.ms).toBeGreaterThanOrEqual(MIN_MS)
      // identical distribution: with jitter pinned, found / not-found are indistinguishable
      expect(found.ms).toBe(missing.ms)
    })

    it('a slow lookup does not make found distinguishable: padding is to a floor, jitter is bounded', async () => {
      vi.spyOn(Math, 'random').mockReturnValue(0.999999)
      const route = await load()
      queryMock.mockResolvedValueOnce({ rows: [{ email: 'a@b.test', status: 'active' }] })
      const found = await timed(route, req('abhi', '203.0.113.1'))
      queryMock.mockResolvedValueOnce({ rows: [] })
      const missing = await timed(route, req('nobody', '203.0.113.2'))
      for (const r of [found, missing]) {
        expect(r.ms).toBeGreaterThanOrEqual(MIN_MS)
        expect(r.ms).toBeLessThanOrEqual(MIN_MS + JITTER_MS + 2)
      }
    })
  })

  describe('per-IP limit on the TRUSTED client IP (60/min, checked first)', () => {
    it('the shared Hosting address is not a wall: 30 DIFFERENT usernames from one single-entry XFF all pass', async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      for (let i = 0; i < 30; i++) {
        const { res } = await timed(route, req(`user-${i}`, SHARED_HOSTING))
        expect(res.status).toBe(404) // old code answered 429 from the 11th
      }
    })

    it(`allows ${IP_RPM} per minute per trusted IP, then 429 with Retry-After, and stops querying`, async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      for (let i = 0; i < IP_RPM; i++) {
        expect((await run(route, req(`enum-${i}`, SHARED_HOSTING))).status).toBe(404)
      }
      const callsBefore = queryMock.mock.calls.length
      const res = await run(route, req('enum-next', SHARED_HOSTING)) // the 61st distinct username
      expect(res.status).toBe(429)
      expect(Number(res.headers.get('retry-after'))).toBeGreaterThan(0)
      expect((await res.json()).error?.code).toBe('LIMIT_RATE_LIMIT_EXCEEDED')
      expect(queryMock.mock.calls.length).toBe(callsBefore) // throttled BEFORE the lookup
    })

    it('a request refused by the IP limit does not spend the username budget', async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      for (let i = 0; i < IP_RPM; i++) await run(route, req(`fill-${i}`, SHARED_HOSTING))
      for (let i = 0; i < 3; i++) expect((await run(route, req('bob', SHARED_HOSTING))).status).toBe(429)
      // 'bob' still has its full 5/min from other addresses
      for (let i = 0; i < USERNAME_RPM; i++) {
        expect((await run(route, req('bob', `198.51.100.${i + 1}`))).status).toBe(404)
      }
    })

    it('a username-throttled request costs exactly one IP token (the one already spent)', async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      for (let i = 0; i < USERNAME_RPM; i++) await run(route, req('carol', SHARED_HOSTING)) // 5 tokens
      expect((await run(route, req('carol', SHARED_HOSTING))).status).toBe(429) // token 6, refused by (a)
      for (let i = 0; i < IP_RPM - USERNAME_RPM - 1; i++) { // tokens 7..60
        expect((await run(route, req(`other-${i}`, SHARED_HOSTING))).status).toBe(404)
      }
      expect((await run(route, req('other-last', SHARED_HOSTING))).status).toBe(429) // token 61, refused by (b)
    })

    it('rotating the client-controlled LEFTMOST X-Forwarded-For entry does not choose the bucket', async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      for (let i = 0; i < IP_RPM; i++) {
        // forged leftmost entries (one, then two spoofed hops) in front of the trusted rightmost one
        const xff = i % 2 === 0 ? `10.0.${i}.1, ${SHARED_HOSTING}` : `10.1.${i}.1, 10.2.${i}.1, ${SHARED_HOSTING}`
        expect((await run(route, req(`probe-${i}`, xff))).status).toBe(404)
      }
      expect((await run(route, req('probe-next', `10.9.9.9, ${SHARED_HOSTING}`))).status).toBe(429)
      const { ip } = limiters()
      expect(new Set(ip.keys)).toEqual(new Set([SHARED_HOSTING])) // every forged chain landed in the trusted bucket
    })

    it('a different trusted IP has its own allowance', async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      for (let i = 0; i < IP_RPM; i++) await run(route, req(`a-${i}`, SHARED_HOSTING))
      expect((await run(route, req('a-next', SHARED_HOSTING))).status).toBe(429)
      expect((await run(route, req('a-next', '198.51.100.7'))).status).toBe(404)
    })

    it('no X-Forwarded-For (or an unusable one) -> ONE shared bucket, never an unlimited path', async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      for (let i = 0; i < IP_RPM / 2; i++) expect((await run(route, req(`n-${i}`))).status).toBe(404)
      for (let i = 0; i < IP_RPM / 2; i++) expect((await run(route, req(`g-${i}`, 'not-an-ip'))).status).toBe(404)
      expect((await run(route, req('n-next'))).status).toBe(429)
      expect(new Set(limiters().ip.keys)).toEqual(new Set(['unknown']))
    })

    it('the window recovers after a minute', async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      for (let i = 0; i < IP_RPM; i++) await run(route, req(`w-${i}`, SHARED_HOSTING))
      expect((await run(route, req('w-next', SHARED_HOSTING))).status).toBe(429)
      await vi.advanceTimersByTimeAsync(61_000)
      expect((await run(route, req('w-after', SHARED_HOSTING))).status).toBe(404)
    })
  })

  describe('per-REQUESTED-username limit (5/min, global, case/whitespace-insensitive)', () => {
    it(`${USERNAME_RPM} requests for one username from DIFFERENT IPs pass, the next (new IP) is 429`, async () => {
      dbWithAccounts()
      const route = await load()
      for (let i = 0; i < USERNAME_RPM; i++) {
        expect((await run(route, req('alice', `198.51.100.${i + 1}`))).status).toBe(200)
      }
      const callsBefore = queryMock.mock.calls.length
      const res = await run(route, req('alice', '198.51.100.99'))
      expect(res.status).toBe(429)
      expect(Number(res.headers.get('retry-after'))).toBeGreaterThan(0)
      expect((await res.json()).error?.code).toBe('LIMIT_RATE_LIMIT_EXCEEDED')
      expect(queryMock.mock.calls.length).toBe(callsBefore) // the lookup was not consumed
    })

    it("case and whitespace variants share one bucket ('Alice', ' alice ')", async () => {
      dbWithAccounts()
      const route = await load()
      const variants = ['alice', 'Alice', ' alice ', 'ALICE', '\talice\n']
      for (let i = 0; i < variants.length; i++) {
        expect((await run(route, req(variants[i], `198.51.100.${i + 1}`))).status).toBe(200)
      }
      for (const [i, v] of ['Alice', ' alice ', 'aLiCe'].entries()) {
        expect((await run(route, req(v, `198.51.101.${i + 1}`))).status).toBe(429)
      }
      expect(new Set(limiters().username.keys).size).toBe(1)
    })

    it('the throttled envelope is identical whether or not the username exists, and never queries', async () => {
      dbWithAccounts()
      const route = await load()
      for (let i = 0; i < USERNAME_RPM; i++) {
        await run(route, req('alice', `198.51.100.${i + 1}`)) // exists
        await run(route, req('ghost', `198.51.101.${i + 1}`)) // does not exist
      }
      const callsBefore = queryMock.mock.calls.length
      const existing = await run(route, req('alice', '198.51.102.1'))
      const missing = await run(route, req('ghost', '198.51.102.2'))
      expect(existing.status).toBe(429)
      expect(missing.status).toBe(429)
      expect(await existing.json()).toEqual(await missing.json())
      expect(existing.headers.get('retry-after')).toBe(missing.headers.get('retry-after'))
      expect(queryMock.mock.calls.length).toBe(callsBefore)
    })

    it('different usernames do not share a bucket', async () => {
      dbWithAccounts()
      const route = await load()
      for (let i = 0; i < USERNAME_RPM; i++) await run(route, req('alice', `198.51.100.${i + 1}`))
      expect((await run(route, req('alice', '198.51.100.50'))).status).toBe(429)
      expect((await run(route, req('abhi', '198.51.100.50'))).status).toBe(200)
    })

    it('bad input (400) is rejected before the username limiter is consulted', async () => {
      const route = await load()
      expect((await run(route, req('   ', SHARED_HOSTING))).status).toBe(400)
      expect(limiters().username.keys).toEqual([])
      expect(queryMock).not.toHaveBeenCalled()
    })

    it('the username window recovers after a minute', async () => {
      dbWithAccounts()
      const route = await load()
      for (let i = 0; i < USERNAME_RPM; i++) await run(route, req('alice', `198.51.100.${i + 1}`))
      expect((await run(route, req('alice', '198.51.100.50'))).status).toBe(429)
      await vi.advanceTimersByTimeAsync(61_000)
      expect((await run(route, req('alice', '198.51.100.51'))).status).toBe(200)
    })
  })

  describe('memory bound', () => {
    it('both tracked maps stay within their cap when more distinct keys than the cap arrive', async () => {
      rec.forcedNow = () => 1_000_000 // frozen clock: nothing expires, so only the cap/eviction can bound the maps
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      const { ip, username } = limiters()
      expect(ip.opts.maxEntries).toBe(MAX_TRACKED)
      expect(username.opts.maxEntries).toBe(MAX_TRACKED)
      for (let i = 0; i < MAX_TRACKED + 50; i++) {
        const addr = `10.${i >> 16}.${(i >> 8) & 255}.${i & 255}`
        expect((await run(route, req(`flood-${i}`, addr))).status).toBe(404)
        expect(username.size).toBeLessThanOrEqual(MAX_TRACKED)
        expect(ip.size).toBeLessThanOrEqual(MAX_TRACKED)
      }
      expect(username.size).toBe(MAX_TRACKED)
      expect(ip.size).toBe(MAX_TRACKED)
      // eviction is oldest-first: 'flood-0' (used once, then evicted) has a fresh full allowance again
      for (let i = 0; i < USERNAME_RPM; i++) {
        expect((await run(route, req('flood-0', `172.16.0.${i + 1}`))).status).toBe(404)
      }
      expect((await run(route, req('flood-0', '172.16.0.99'))).status).toBe(429)
      expect(username.size).toBeLessThanOrEqual(MAX_TRACKED)
      expect(ip.size).toBeLessThanOrEqual(MAX_TRACKED)
    }, 120_000)
  })

  describe('privacy of the requested username', () => {
    it('the raw username is never logged and never used as a limiter key (only its sha256)', async () => {
      const rawName = '  Very.Needle.Name  '
      const spies = (['log', 'info', 'warn', 'error', 'debug'] as const).map((m) => vi.spyOn(console, m).mockImplementation(() => {}))
      queryMock.mockResolvedValueOnce({ rows: [{ email: 'a@b.test', status: 'active' }] })
      queryMock.mockRejectedValueOnce(new Error('db down'))
      const route = await load()
      await run(route, req(rawName, '198.51.100.1')) // found
      await run(route, req(rawName, '198.51.100.2')) // db error
      for (let i = 0; i < USERNAME_RPM; i++) await run(route, req(rawName, '198.51.100.3')) // reaches throttle
      const { ip, username } = limiters()
      const expected = sha('very.needle.name')
      expect(username.keys.length).toBeGreaterThanOrEqual(USERNAME_RPM + 1)
      expect(new Set(username.keys)).toEqual(new Set([expected]))
      expect(username.keys[0]).toMatch(/^[0-9a-f]{64}$/)
      for (const k of [...username.keys, ...ip.keys]) {
        expect(k.toLowerCase()).not.toContain('needle')
      }
      const logged = JSON.stringify(spies.flatMap((s) => s.mock.calls))
      expect(logged.toLowerCase()).not.toContain('needle')
    })
  })
})
