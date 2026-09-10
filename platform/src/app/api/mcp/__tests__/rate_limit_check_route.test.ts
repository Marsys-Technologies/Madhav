/**
 * RATE-07 — POST /api/mcp/rate-limit/check.
 *
 * The store endpoint the MCP sidecar calls to charge an OAuth bucket. What
 * matters at this boundary:
 *
 *   1. It is service-to-service only, fail-closed on the internal token.
 *   2. It returns 200 for BOTH allowed and denied — it reports a decision, it
 *      does not enforce one. (The 429 belongs on the OAuth endpoint, where the
 *      OAuth-shaped body and Retry-After header belong.)
 *   3. A store failure returns 500 with NO decision field, so a caller cannot
 *      accidentally read a permissive answer out of an error.
 *   4. Bad arguments are 400, never a silently-permissive 200.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockConsume = vi.fn()
const mockPrune = vi.fn()
const mockShouldPrune = vi.fn()
const mockValidateServiceToken = vi.fn()

vi.mock('@/lib/mcp/service_token', () => ({
  validateServiceToken: (req: Request) => mockValidateServiceToken(req) as boolean,
}))

vi.mock('@/lib/mcp/oauth_rate_limit', async () => {
  const actual = await vi.importActual<typeof import('@/lib/mcp/oauth_rate_limit')>(
    '@/lib/mcp/oauth_rate_limit'
  )
  return {
    ...actual,
    consumeRateBucket: (...a: unknown[]) => mockConsume(...a) as unknown,
    pruneExpiredRateBuckets: (...a: unknown[]) => mockPrune(...a) as unknown,
    // Forced, never random: shouldPrune() fires ~1 call in 64, so a prune test
    // that relied on the real function would pass vacuously ~98% of the time
    // without ever executing the path it claims to cover (CLAUDE.md §N.8).
    shouldPrune: (...a: unknown[]) => mockShouldPrune(...a) as boolean,
  }
})

import { POST } from '@/app/api/mcp/rate-limit/check/route'
import { RateBucketArgumentError } from '@/lib/mcp/oauth_rate_limit'

function makeReq(body: unknown, headers: Record<string, string> = {}): Request {
  return new Request('http://localhost/api/mcp/rate-limit/check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-mcp-internal-token': 'tok', ...headers },
    body: typeof body === 'string' ? body : JSON.stringify(body),
  })
}

const IP_BUCKET = { route: 'oauth_authorize', subject_kind: 'ip', subject: '1.2.3.4', limit: 30, window_seconds: 60 }
const GLOBAL_BUCKET = { route: 'oauth_authorize', subject_kind: 'route_global', subject: '', limit: 600, window_seconds: 60 }
const GOOD = { buckets: [IP_BUCKET, GLOBAL_BUCKET] }

const ok = (limit: number, hits = 1) => ({
  allowed: true, limit, hits, remaining: limit - hits, windowSeconds: 60, retryAfterSeconds: 47,
})
const denied = (limit: number, retry = 13) => ({
  allowed: false, limit, hits: limit + 1, remaining: 0, windowSeconds: 60, retryAfterSeconds: retry,
})

beforeEach(() => {
  mockConsume.mockReset()
  mockPrune.mockReset().mockResolvedValue(0)
  mockShouldPrune.mockReset().mockReturnValue(false)
  mockValidateServiceToken.mockReset().mockReturnValue(true)
})

describe('RATE-07 store route — authentication', () => {
  it('401s when the service token is rejected, and never touches the store', async () => {
    mockValidateServiceToken.mockReturnValue(false)
    const res = await POST(makeReq(GOOD))
    expect(res.status).toBe(401)
    expect(mockConsume).not.toHaveBeenCalled()
  })
})

describe('RATE-07 store route — batch decisions', () => {
  it('charges every bucket and returns 200 + allowed:true when all pass', async () => {
    mockConsume.mockResolvedValueOnce(ok(30)).mockResolvedValueOnce(ok(600))
    const res = await POST(makeReq(GOOD))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.allowed).toBe(true)
    expect(body.decisions).toHaveLength(2)
    expect(body.decisions.map((d: { subject_kind: string }) => d.subject_kind)).toEqual(['ip', 'route_global'])
    expect(mockConsume).toHaveBeenCalledTimes(2)
  })

  it('SECURITY: STOPS at the first denial — a denied per-IP bucket never charges route_global', async () => {
    // This is the fix for the fleet-wide DoS lever: one address pouring its
    // REJECTED traffic into the shared ceiling could 429 everyone else.
    mockConsume.mockResolvedValueOnce(denied(30))
    const res = await POST(makeReq(GOOD))
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.allowed).toBe(false)
    expect(body.decisions).toHaveLength(1)
    expect(body.decisions[0].subject_kind).toBe('ip')
    expect(mockConsume, 'route_global must NOT have been charged').toHaveBeenCalledTimes(1)
  })

  it('returns 200 (NOT 429) when over the limit', async () => {
    mockConsume.mockResolvedValueOnce(denied(30, 13))
    const res = await POST(makeReq(GOOD))
    // 429 here would be ambiguous with "you, the sidecar, are rate limited".
    expect(res.status).toBe(200)
    expect((await res.json()).decisions[0].retry_after_seconds).toBe(13)
  })

  it('forwards each bucket through unchanged, in order', async () => {
    mockConsume.mockResolvedValue(ok(10))
    await POST(makeReq({ buckets: [{ route: 'oauth_register', subject_kind: 'principal', subject: 'uid-9', limit: 10, window_seconds: 3600 }] }))
    expect(mockConsume).toHaveBeenCalledWith({
      route: 'oauth_register', subjectKind: 'principal', subject: 'uid-9', limit: 10, windowSeconds: 3600,
    })
  })
})

describe('RATE-07 store route — failures never read as permissive', () => {
  it('500s with NO decision field when the store throws', async () => {
    mockConsume.mockRejectedValue(new Error('connection terminated unexpectedly'))
    const res = await POST(makeReq(GOOD))
    expect(res.status).toBe(500)
    const body = await res.json()
    expect(body).toEqual({ error: 'rate_limit_store_unavailable' })
    expect(body).not.toHaveProperty('allowed')
  })

  it('400s on an argument error', async () => {
    mockConsume.mockRejectedValue(new RateBucketArgumentError('limit must be an integer in [1, 100000]'))
    const res = await POST(makeReq({ buckets: [{ ...IP_BUCKET, limit: 0 }] }))
    expect(res.status).toBe(400)
    expect((await res.json()).error).toMatch(/limit must be/)
  })

  it('validates the WHOLE batch before charging any of it', async () => {
    // A malformed trailing entry must not leave the earlier one charged against
    // a request that is then rejected as a 400.
    const res = await POST(makeReq({ buckets: [IP_BUCKET, { ...GLOBAL_BUCKET, subject_kind: 'wishful' }] }))
    expect(res.status).toBe(400)
    expect(mockConsume).not.toHaveBeenCalled()
  })

  it('400s on a missing/empty/oversized buckets array', async () => {
    for (const body of [{}, { buckets: [] }, { buckets: 'nope' }, { buckets: Array(5).fill(IP_BUCKET) }]) {
      const res = await POST(makeReq(body))
      expect(res.status).toBe(400)
    }
    expect(mockConsume).not.toHaveBeenCalled()
  })

  it('400s on a malformed JSON body', async () => {
    const res = await POST(makeReq('{not json'))
    expect(res.status).toBe(400)
    expect(mockConsume).not.toHaveBeenCalled()
  })

  it('a prune failure does not affect the decision', async () => {
    mockConsume.mockResolvedValue(ok(30))
    mockShouldPrune.mockReturnValue(true)          // force the path
    mockPrune.mockRejectedValue(new Error('deadlock'))
    const res = await POST(makeReq(GOOD))
    expect(mockPrune, 'the prune path must actually have run').toHaveBeenCalled()
    expect(res.status).toBe(200)
    expect((await res.json()).allowed).toBe(true)
  })

  it('the prune is AWAITED, not fired and forgotten', async () => {
    // amjis-web runs without --no-cpu-throttling, so CPU stops the instant the
    // response is sent: a floating promise is not guaranteed to run at all,
    // which would quietly falsify migration 580's "no cron job" claim.
    let settled = false
    mockConsume.mockResolvedValue(ok(30))
    mockShouldPrune.mockReturnValue(true)
    mockPrune.mockImplementation(async () => {
      await new Promise((r) => setTimeout(r, 10))
      settled = true
      return 3
    })
    await POST(makeReq(GOOD))
    expect(settled, 'the response resolved before the prune finished').toBe(true)
  })
})
