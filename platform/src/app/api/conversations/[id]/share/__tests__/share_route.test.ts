// @vitest-environment node
/**
 * SS N-376 / PR-S4 — share route:
 *   2. NEW shares expire (default 30 days); listing/reuse ignore expired rows.
 *   5. hide_* body fields are parsed through the repo flag helper, default ON.
 *   6. create (POST) and revoke (DELETE) are rate-limited per VERIFIED user.
 * SS N-379 (v): R10_SELECTIVE_SHARE only controls whether hide options are OFFERED
 *   on NEW shares (POST body parsing + the dialog control, fed by GET).
 * SS N-383: POST reuses an active share only when it has the SAME hide options;
 *   different options mint a new share and leave the old one untouched.
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
    const reuse = queryMock.mock.calls.find(([sql]) => /SELECT .* FROM conversation_shares/i.test(String(sql)))!
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

describe('R10_SELECTIVE_SHARE controls only what is OFFERED on NEW shares (SS N-379 v)', () => {
  it('flag off: a new share ignores hide fields in the POST body and does not even read the body', async () => {
    process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE = 'false'
    const { POST } = await loadRoute()
    const req = post({ hide_reasoning: true, hide_methodology: true })
    const jsonSpy = vi.spyOn(req, 'json')
    const r = await POST(req, ctx())
    expect(r.status).toBe(200)
    expect(jsonSpy).not.toHaveBeenCalled()
    const [, params] = insertCall() as [string, unknown[]]
    expect(params.filter((p) => p === true)).toHaveLength(0)
    expect(params.filter((p) => p === false)).toHaveLength(2)
  })

  it('GET tells the dialog whether the options are offered: true by default', async () => {
    const { GET } = await loadRoute()
    const body = await (await GET(get(), ctx())).json()
    expect(body.selective_share_enabled).toBe(true)
  })

  it('GET tells the dialog the options are NOT offered when the flag is off', async () => {
    process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE = 'false'
    const { GET } = await loadRoute()
    const body = await (await GET(get(), ctx())).json()
    expect(body.selective_share_enabled).toBe(false)
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


// ─────────────────────────────────────────────────────────────────────────────
// SS N-383: different hide options mint a NEW share; same options reuse.
// ─────────────────────────────────────────────────────────────────────────────

type FakeShare = {
  slug: string
  created_at: string
  expires_at: string | null
  revoked_at: string | null
  hide_reasoning: boolean
  hide_methodology: boolean
}

const DAY_MS = 86_400_000
const iso = (offsetMs: number) => new Date(Date.now() + offsetMs).toISOString()

/**
 * A small stateful fake of conversation_shares behind queryMock. SELECTs apply the
 * same "active" predicate as the SQL (so the stateful scenarios behave like the DB);
 * `rawSelect: true` returns every stored row UNFILTERED, to prove the route's own
 * defensive re-check never hands back an expired or revoked share.
 */
function fakeShares(seed: FakeShare[], opts: { rawSelect?: boolean } = {}) {
  const rows = [...seed]
  let tick = 0
  queryMock.mockImplementation(async (sql: string, params?: unknown[]) => {
    const text = String(sql)
    if (/FROM profiles/i.test(text)) return { rows: [{ role: 'guest' }] }
    if (/INSERT INTO conversation_shares/i.test(text)) {
      const [, slug, , hr, hm, ttlDays] = params as [string, string, string, boolean, boolean, number]
      rows.push({
        slug,
        created_at: iso(++tick),
        expires_at: iso(Number(ttlDays) * DAY_MS),
        revoked_at: null,
        hide_reasoning: hr,
        hide_methodology: hm,
      })
      return { rows: [] }
    }
    if (/UPDATE conversation_shares SET revoked_at/i.test(text)) {
      for (const r of rows) if (!r.revoked_at) r.revoked_at = iso(0)
      return { rows: [] }
    }
    if (/FROM conversation_shares/i.test(text)) {
      const visible = opts.rawSelect
        ? rows
        : rows.filter((r) => !r.revoked_at && (!r.expires_at || new Date(r.expires_at).getTime() > Date.now()))
      return { rows: [...visible].sort((a, b) => b.created_at.localeCompare(a.created_at)) }
    }
    return { rows: [] }
  })
  return rows
}

const share = (slug: string, hr: boolean, hm: boolean, extra: Partial<FakeShare> = {}): FakeShare => ({
  slug,
  created_at: iso(-DAY_MS),
  expires_at: iso(10 * DAY_MS),
  revoked_at: null,
  hide_reasoning: hr,
  hide_methodology: hm,
  ...extra,
})

const inserts = () => queryMock.mock.calls.filter(([sql]) => /INSERT INTO conversation_shares/i.test(String(sql)))
const updates = () => queryMock.mock.calls.filter(([sql]) => /UPDATE conversation_shares/i.test(String(sql)))
const slugOf = async (r: Response) => ((await r.json()) as { slug: string }).slug

describe('different hide options mint a new share; same options reuse (SS N-383)', () => {
  it('1. the same options twice -> the same slug and exactly one INSERT', async () => {
    fakeShares([])
    const { POST } = await loadRoute()
    const first = await slugOf(await POST(post({ hide_reasoning: true, hide_methodology: false }), ctx()))
    const second = await slugOf(await POST(post({ hide_reasoning: true, hide_methodology: false }), ctx()))
    expect(second).toBe(first)
    expect(inserts()).toHaveLength(1)
  })

  it('1b. omitted options count as false/false and reuse an existing false/false share', async () => {
    fakeShares([share('plainSlug01', false, false)])
    const { POST } = await loadRoute()
    expect(await slugOf(await POST(post({}), ctx()))).toBe('plainSlug01')
    expect(await slugOf(await POST(post({ hide_reasoning: 'yes', hide_methodology: 1 }), ctx()))).toBe('plainSlug01')
    expect(inserts()).toHaveLength(0)
  })

  it('2. different hide_reasoning -> a NEW slug, a second INSERT with the new options and a 30-day expiry; the first share is untouched', async () => {
    const rows = fakeShares([])
    const { POST } = await loadRoute()
    const { SHARE_DEFAULT_TTL_DAYS } = await import('@/lib/share/constants')
    const first = await slugOf(await POST(post({ hide_reasoning: false, hide_methodology: false }), ctx()))
    const firstBefore = { ...rows[0] }
    const second = await slugOf(await POST(post({ hide_reasoning: true, hide_methodology: false }), ctx()))
    expect(second).not.toBe(first)
    expect(inserts()).toHaveLength(2)
    const [sql, params] = inserts()[1] as [string, unknown[]]
    expect(sql).toMatch(/now\(\)\s*\+/i)
    expect(params.slice(0, 5)).toEqual(['conv-1', second, 'user-1', true, false])
    expect(params[5]).toBe(SHARE_DEFAULT_TTL_DAYS)
    expect(SHARE_DEFAULT_TTL_DAYS).toBe(30)
    // The old link keeps its original options and stays active: no UPDATE at all.
    expect(updates()).toHaveLength(0)
    expect(rows[0]).toEqual(firstBefore)
    expect(rows[0].revoked_at).toBeNull()
    expect(rows).toHaveLength(2)
  })

  it('3. different hide_methodology -> a new slug carrying the new option', async () => {
    fakeShares([share('plainSlug01', false, false)])
    const { POST } = await loadRoute()
    const slug = await slugOf(await POST(post({ hide_reasoning: false, hide_methodology: true }), ctx()))
    expect(slug).not.toBe('plainSlug01')
    expect(inserts()).toHaveLength(1)
    const [, params] = inserts()[0] as [string, unknown[]]
    expect(params.slice(3, 5)).toEqual([false, true])
    expect(updates()).toHaveLength(0)
  })

  it('4. calls A, B, A -> the third returns the FIRST slug (the matching share is reused); only two INSERTs', async () => {
    fakeShares([])
    const { POST } = await loadRoute()
    const A = { hide_reasoning: true, hide_methodology: false }
    const B = { hide_reasoning: false, hide_methodology: true }
    const a1 = await slugOf(await POST(post(A), ctx()))
    const b = await slugOf(await POST(post(B), ctx()))
    const a2 = await slugOf(await POST(post(A), ctx()))
    expect(b).not.toBe(a1)
    expect(a2).toBe(a1)
    expect(inserts()).toHaveLength(2)
    expect(updates()).toHaveLength(0)
  })

  it('4b. with several matching active shares the most recent one is reused', async () => {
    fakeShares([
      share('olderSame01', true, true, { created_at: iso(-3 * DAY_MS) }),
      share('newerSame02', true, true, { created_at: iso(-1 * DAY_MS) }),
      share('otherOpts03', false, false, { created_at: iso(-DAY_MS / 2) }),
    ])
    const { POST } = await loadRoute()
    expect(await slugOf(await POST(post({ hide_reasoning: true, hide_methodology: true }), ctx()))).toBe('newerSame02')
    expect(inserts()).toHaveLength(0)
  })

  it('5. flag OFF: requested options are ignored (false/false); it reuses an existing false/false share and never stores hide options', async () => {
    process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE = 'false'
    fakeShares([share('hiddenOpt01', true, true, { created_at: iso(-2 * DAY_MS) }), share('plainSlug01', false, false)])
    const { POST } = await loadRoute()
    const slug = await slugOf(await POST(post({ hide_reasoning: true, hide_methodology: true }), ctx()))
    expect(slug).toBe('plainSlug01')
    expect(inserts()).toHaveLength(0)
  })

  it('5b. flag OFF with only a hide-option share present: mints a false/false share, never one with hide options', async () => {
    process.env.MARSYS_FLAG_R10_SELECTIVE_SHARE = 'false'
    fakeShares([share('hiddenOpt01', true, true)])
    const { POST } = await loadRoute()
    const slug = await slugOf(await POST(post({ hide_reasoning: true, hide_methodology: true }), ctx()))
    expect(slug).not.toBe('hiddenOpt01')
    expect(inserts()).toHaveLength(1)
    const [, params] = inserts()[0] as [string, unknown[]]
    expect(params.slice(3, 5)).toEqual([false, false])
    expect(updates()).toHaveLength(0)
  })

  it('6. expired and revoked shares are never reused, even if the DB handed them back', async () => {
    fakeShares(
      [
        share('expiredOne1', true, false, { expires_at: iso(-DAY_MS) }),
        share('revokedOne1', true, false, { revoked_at: iso(-DAY_MS / 2) }),
      ],
      { rawSelect: true },
    )
    const { POST } = await loadRoute()
    const slug = await slugOf(await POST(post({ hide_reasoning: true, hide_methodology: false }), ctx()))
    expect(['expiredOne1', 'revokedOne1']).not.toContain(slug)
    expect(inserts()).toHaveLength(1)
    expect(updates()).toHaveLength(0)
  })

  it('6b. a share with expires_at NULL (pre-TTL) and the same options is still reused', async () => {
    fakeShares([share('legacyNull1', true, false, { expires_at: null })])
    const { POST } = await loadRoute()
    expect(await slugOf(await POST(post({ hide_reasoning: true, hide_methodology: false }), ctx()))).toBe('legacyNull1')
    expect(inserts()).toHaveLength(0)
  })

  it('a reuse still consumes rate-limit budget (the limiter runs before any DB work, as before)', async () => {
    fakeShares([share('plainSlug01', false, false)])
    const { POST } = await loadRoute()
    for (let i = 0; i < 20; i++) expect((await POST(post({}), ctx())).status).toBe(200)
    expect(inserts()).toHaveLength(0)
    expect((await POST(post({}), ctx())).status).toBe(429)
  })

  it('7. DELETE revokes ALL active shares of the conversation in one statement', async () => {
    const rows = fakeShares([share('plainSlug01', false, false), share('hiddenOpt02', true, true)])
    const { DELETE } = await loadRoute()
    const r = await DELETE(del(), ctx())
    expect(r.status).toBe(200)
    expect(updates()).toHaveLength(1)
    const [sql, params] = updates()[0] as [string, unknown[]]
    expect(sql).toMatch(/WHERE conversation_id=\$1 AND revoked_at IS NULL/)
    expect(sql).not.toMatch(/slug\s*=/i)
    expect(sql).not.toMatch(/LIMIT/i)
    expect(params).toEqual(['conv-1'])
    expect(rows.every((x) => x.revoked_at)).toBe(true)
  })

  it('8. GET lists every active share with its options and expiry; `share` stays the most recent one', async () => {
    const newest = share('newestSlug1', true, true, { created_at: iso(-1000) })
    const older = share('olderSlug01', false, false, { created_at: iso(-DAY_MS) })
    fakeShares([older, share('expiredSlug', false, true, { expires_at: iso(-DAY_MS) }), newest])
    const { GET } = await loadRoute()
    const body = await (await GET(get(), ctx())).json()
    expect(body.shares).toHaveLength(2)
    expect(body.shares.map((x: FakeShare) => x.slug)).toEqual(['newestSlug1', 'olderSlug01'])
    for (const x of body.shares as FakeShare[]) {
      expect(typeof x.hide_reasoning).toBe('boolean')
      expect(typeof x.hide_methodology).toBe('boolean')
      expect(x.expires_at).toBeTruthy()
    }
    expect(body.shares[0]).toMatchObject({ hide_reasoning: true, hide_methodology: true, expires_at: newest.expires_at })
    expect(body.shares[1]).toMatchObject({ hide_reasoning: false, hide_methodology: false, expires_at: older.expires_at })
    // Old shape preserved for existing clients.
    expect(body.share.slug).toBe('newestSlug1')
    expect(typeof body.selective_share_enabled).toBe('boolean')
    const listing = queryMock.mock.calls.find(([sql]) => /FROM conversation_shares/i.test(String(sql)))!
    expect(String(listing[0])).toMatch(/revoked_at IS NULL AND \(expires_at IS NULL OR expires_at > now\(\)\)/)
    expect(String(listing[0])).not.toMatch(/LIMIT/i)
  })

  it('8b. GET with no active share -> share null and shares []', async () => {
    fakeShares([])
    const { GET } = await loadRoute()
    const body = await (await GET(get(), ctx())).json()
    expect(body.share).toBeNull()
    expect(body.shares).toEqual([])
  })
})
