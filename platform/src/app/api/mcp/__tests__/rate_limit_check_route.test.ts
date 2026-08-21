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

const GOOD = { route: 'oauth_authorize', subject_kind: 'ip', subject: '1.2.3.4', limit: 30, window_seconds: 60 }

beforeEach(() => {
  mockConsume.mockReset()
  mockPrune.mockReset()
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

describe('RATE-07 store route — decisions', () => {
  it('returns 200 + allowed:true under the limit', async () => {
    mockConsume.mockResolvedValue({
      allowed: true, limit: 30, hits: 4, remaining: 26, windowSeconds: 60, retryAfterSeconds: 47,
    })
    const res = await POST(makeReq(GOOD))
    expect(res.status).toBe(200)
    await expect(res.json()).resolves.toEqual({
      allowed: true, limit: 30, hits: 4, remaining: 26, window_seconds: 60, retry_after_seconds: 47,
    })
  })

  it('returns 200 (NOT 429) + allowed:false when over the limit', async () => {
    mockConsume.mockResolvedValue({
      allowed: false, limit: 30, hits: 31, remaining: 0, windowSeconds: 60, retryAfterSeconds: 13,
    })
    const res = await POST(makeReq(GOOD))
    // 429 here would be ambiguous with "you, the sidecar, are rate limited".
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body.allowed).toBe(false)
    expect(body.retry_after_seconds).toBe(13)
  })

  it('forwards the arguments through unchanged', async () => {
    mockConsume.mockResolvedValue({
      allowed: true, limit: 10, hits: 1, remaining: 9, windowSeconds: 3600, retryAfterSeconds: 3599,
    })
    await POST(makeReq({ route: 'oauth_register', subject_kind: 'principal', subject: 'uid-9', limit: 10, window_seconds: 3600 }))
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
    const res = await POST(makeReq({ ...GOOD, limit: 0 }))
    expect(res.status).toBe(400)
    expect((await res.json()).error).toMatch(/limit must be/)
  })

  it('400s on an unknown subject_kind before reaching the store', async () => {
    const res = await POST(makeReq({ ...GOOD, subject_kind: 'wishful' }))
    expect(res.status).toBe(400)
    expect(mockConsume).not.toHaveBeenCalled()
  })

  it('400s on a malformed JSON body', async () => {
    const res = await POST(makeReq('{not json'))
    expect(res.status).toBe(400)
    expect(mockConsume).not.toHaveBeenCalled()
  })

  it('a prune failure does not affect the decision', async () => {
    mockConsume.mockResolvedValue({
      allowed: true, limit: 30, hits: 1, remaining: 29, windowSeconds: 60, retryAfterSeconds: 59,
    })
    mockPrune.mockRejectedValue(new Error('deadlock'))
    const res = await POST(makeReq(GOOD))
    expect(res.status).toBe(200)
    expect((await res.json()).allowed).toBe(true)
  })
})
