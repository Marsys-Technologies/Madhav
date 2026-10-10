// @vitest-environment node
/**
 * SS N-373 item 4 — POST /api/auth/resolve-username is public (outside the proxy
 * matcher) and turns a username into an email address. It MUST keep returning
 * the email for username login (SS ruling), so the defence is:
 *   - a strict per-IP rate limit keyed on the TRUSTED client IP (never the
 *     client-controlled leftmost X-Forwarded-For entry),
 *   - a uniform response time for found / not-found / lookup-error,
 *   - the rate-limit check runs BEFORE the lookup, so a throttled response can
 *     never depend on whether the username exists.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...a: unknown[]) => queryMock(...a) }))

// Documented route constants (kept in step with the route; see route.ts).
const MIN_MS = 400
const JITTER_MS = 75
const RPM = 10

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

  describe('strict per-IP rate limit on the TRUSTED client IP', () => {
    it(`allows ${RPM} lookups per minute per IP, then 429 with Retry-After, and stops querying`, async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      for (let i = 0; i < RPM; i++) {
        const { res } = await timed(route, req(`u${i}`, '203.0.113.9'))
        expect(res.status).toBe(404)
      }
      const callsBefore = queryMock.mock.calls.length
      const { res } = await timed(route, req('u-next', '203.0.113.9'))
      expect(res.status).toBe(429)
      expect(Number(res.headers.get('retry-after'))).toBeGreaterThan(0)
      expect((await res.json()).error?.code).toBe('LIMIT_RATE_LIMIT_EXCEEDED')
      expect(queryMock.mock.calls.length).toBe(callsBefore) // throttled BEFORE the lookup
    })

    it('rotating the client-controlled LEFTMOST X-Forwarded-For entry does not evade the limit', async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      let limited = 0
      for (let i = 0; i < RPM + 5; i++) {
        const { res } = await timed(route, req('probe', `10.0.${i}.1, 203.0.113.9`))
        if (res.status === 429) limited++
      }
      expect(limited).toBe(5)
    })

    it('a throttled response is identical whether or not the username exists', async () => {
      const route = await load()
      queryMock.mockResolvedValue({ rows: [{ email: 'a@b.test', status: 'active' }] })
      for (let i = 0; i < RPM; i++) await timed(route, req('abhi', '203.0.113.9'))
      const existing = await timed(route, req('abhi', '203.0.113.9'))
      const missing = await timed(route, req('does-not-exist', '203.0.113.9'))
      expect(existing.res.status).toBe(429)
      expect(missing.res.status).toBe(429)
      expect(await existing.res.json()).toEqual(await missing.res.json())
    })

    it('a different trusted IP has its own allowance', async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      for (let i = 0; i < RPM; i++) await timed(route, req('x', '203.0.113.9'))
      expect((await timed(route, req('x', '203.0.113.9'))).res.status).toBe(429)
      expect((await timed(route, req('x', '198.51.100.7'))).res.status).toBe(404)
    })

    it('no usable XFF -> one shared strict bucket (never an unlimited path)', async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      for (let i = 0; i < RPM; i++) await timed(route, req('x'))
      expect((await timed(route, req('x'))).res.status).toBe(429)
    })

    it('the window recovers after a minute', async () => {
      queryMock.mockResolvedValue({ rows: [] })
      const route = await load()
      for (let i = 0; i < RPM; i++) await timed(route, req('x', '203.0.113.9'))
      expect((await timed(route, req('x', '203.0.113.9'))).res.status).toBe(429)
      await vi.advanceTimersByTimeAsync(61_000)
      expect((await timed(route, req('x', '203.0.113.9'))).res.status).toBe(404)
    })
  })
})
