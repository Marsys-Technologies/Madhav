// @vitest-environment node
/**
 * SS N-376 / PR-S4 — share route:
 *   2. NEW shares expire (default 30 days); listing/reuse ignore expired rows.
 *   5. hide_* body fields are parsed through the repo flag helper, default ON.
 *   6. create (POST) and revoke (DELETE) are rate-limited per VERIFIED user.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const getServerUserMock = vi.fn()
vi.mock('@/lib/firebase/server', () => ({ getServerUser: () => getServerUserMock() }))

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (sql: string, params?: unknown[]) => queryMock(sql, params) }))

const getConversationMock = vi.fn()
vi.mock('@/lib/conversations', () => ({ getConversation: (a: unknown) => getConversationMock(a) }))

type Ctx = { params: Promise<{ id: string }> }
const ctx = (id = 'conv-1'): Ctx => ({ params: Promise.resolve({ id }) })

function post(body?: unknown) {
  return new Request('http://localhost/api/conversations/conv-1/share', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
}
const del = () => new Request('http://localhost/api/conversations/conv-1/share', { method: 'DELETE' })
const get = () => new Request('http://localhost/api/conversations/conv-1/share')

async function loadRoute() {
  vi.resetModules()
  return await import('../route')
}

function insertCall() {
  return queryMock.mock.calls.find(([sql]) => /INSERT INTO conversation_shares/i.test(String(sql)))
}

beforeEach(() => {
  for (const m of [getServerUserMock, queryMock, getConversationMock]) m.mockReset()
  delete process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE
  getServerUserMock.mockResolvedValue({ uid: 'user-1' })
  getConversationMock.mockResolvedValue({ id: 'conv-1' })
  queryMock.mockImplementation(async (sql: string) => {
    if (/FROM profiles/i.test(sql)) return { rows: [{ role: 'guest' }] }
    return { rows: [] }
  })
})

describe('new shares expire (item 2)', () => {
  it('the default TTL constant is exactly 30 days', async () => {
    const { SHARE_DEFAULT_TTL_DAYS } = await import('@/lib/share/constants')
    expect(SHARE_DEFAULT_TTL_DAYS).toBe(30)
  })

  it('INSERT sets expires_at = now() + the TTL constant', async () => {
    const { POST } = await loadRoute()
    const { SHARE_DEFAULT_TTL_DAYS } = await import('@/lib/share/constants')
    const r = await POST(post({}), ctx())
    expect(r.status).toBe(200)
    const call = insertCall()!
    expect(call).toBeDefined()
    const [sql, params] = call as [string, unknown[]]
    expect(sql).toMatch(/expires_at/)
    expect(sql).toMatch(/now\(\)\s*\+/i)
    expect(params).toContain(SHARE_DEFAULT_TTL_DAYS)
  })

  it('an expired, unrevoked share is NOT reused by POST (it would hand back a dead link)', async () => {
    const { POST } = await loadRoute()
    await POST(post({}), ctx())
    const reuse = queryMock.mock.calls.find(([sql]) => /SELECT slug FROM conversation_shares/i.test(String(sql)))!
    expect(String(reuse[0])).toMatch(/expires_at IS NULL OR expires_at > now\(\)/)
  })

  it('GET only reports a share that is still live', async () => {
    const { GET } = await loadRoute()
    await GET(get(), ctx())
    const listing = queryMock.mock.calls.find(([sql]) => /FROM conversation_shares/i.test(String(sql)))!
    expect(String(listing[0])).toMatch(/expires_at IS NULL OR expires_at > now\(\)/)
    expect(String(listing[0])).toMatch(/expires_at/)
  })
})

describe('hide_* options go through the repo flag helper, default ON (item 5)', () => {
  it('unset env: hide_reasoning / hide_methodology from the body are stored', async () => {
    const { POST } = await loadRoute()
    await POST(post({ hide_reasoning: true, hide_methodology: true }), ctx())
    const [, params] = insertCall() as [string, unknown[]]
    expect(params).toContain(true)
    expect(params.filter((p) => p === true)).toHaveLength(2)
  })

  it('MARSYS_FLAG_R10_SELECTIVE_SHARE=false switches it off (stored as false)', async () => {
    process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE = 'false'
    const { POST } = await loadRoute()
    await POST(post({ hide_reasoning: true, hide_methodology: true }), ctx())
    const [, params] = insertCall() as [string, unknown[]]
    expect(params.filter((p) => p === true)).toHaveLength(0)
  })
})

describe('share create/revoke rate limit per verified user (item 6)', () => {
  it('the 21st POST in the window is refused with the repo 429 shape; no DB work after the refusal', async () => {
    const { POST } = await loadRoute()
    for (let i = 0; i < 20; i++) {
      const r = await POST(post({}), ctx())
      expect(r.status).toBe(200)
    }
    queryMock.mockClear()
    getConversationMock.mockClear()
    const refused = await POST(post({}), ctx())
    expect(refused.status).toBe(429)
    const body = await refused.json()
    expect(body.error?.code ?? body.code).toBe('LIMIT_RATE_LIMIT_EXCEEDED')
    expect(Number(refused.headers.get('retry-after'))).toBeGreaterThan(0)
    expect(queryMock).not.toHaveBeenCalled()
    expect(getConversationMock).not.toHaveBeenCalled()
  })

  it('another user is unaffected by the first user being throttled', async () => {
    const { POST } = await loadRoute()
    for (let i = 0; i < 21; i++) await POST(post({}), ctx())
    expect((await POST(post({}), ctx())).status).toBe(429)
    getServerUserMock.mockResolvedValue({ uid: 'user-2' })
    expect((await POST(post({}), ctx())).status).toBe(200)
  })

  it('DELETE (revoke) is limited too, and shares the per-user budget with POST', async () => {
    const { POST, DELETE } = await loadRoute()
    for (let i = 0; i < 20; i++) await POST(post({}), ctx())
    const r = await DELETE(del(), ctx())
    expect(r.status).toBe(429)
    expect(queryMock.mock.calls.some(([sql]) => /UPDATE conversation_shares/i.test(String(sql)))).toBe(false)
  })

  it('an unauthenticated call is 401 and consumes no budget', async () => {
    const { POST } = await loadRoute()
    getServerUserMock.mockResolvedValue(null)
    for (let i = 0; i < 30; i++) expect((await POST(post({}), ctx())).status).toBe(401)
    getServerUserMock.mockResolvedValue({ uid: 'user-1' })
    expect((await POST(post({}), ctx())).status).toBe(200)
  })

  it('the limiter map is bounded: more distinct users than the cap never exceeds it', async () => {
    const { POST } = await loadRoute()
    const { SHARE_MUTATION_MAX_ENTRIES } = await import('@/lib/share/constants')
    const { shareMutationLimiter } = await import('@/lib/share/share_rate_limit')
    for (let i = 0; i < SHARE_MUTATION_MAX_ENTRIES + 50; i++) {
      getServerUserMock.mockResolvedValue({ uid: `bulk-${i}` })
      await POST(post({}), ctx())
    }
    expect(shareMutationLimiter.size).toBeLessThanOrEqual(SHARE_MUTATION_MAX_ENTRIES)
    expect(shareMutationLimiter.size).toBeGreaterThan(0)
  })
})
