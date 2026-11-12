// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { readFileSync } from 'node:fs'

vi.mock('server-only', () => ({}))
const queryMock = vi.fn()
const loadMessagesMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (sql: string, args: unknown[]) => queryMock(sql, args) }))
vi.mock('@/lib/persistence/conversation_writer', () => ({ loadConversationMessagesV2: (...args: unknown[]) => loadMessagesMock(...args) }))

const ROLE = 'SELECT role FROM profiles WHERE id=$1'
const ACTIVE = 'SELECT slug, created_at, expires_at, revoked_at, hide_reasoning, hide_methodology FROM conversation_shares WHERE conversation_id=$1 AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now()) ORDER BY created_at DESC'
const REVOKE = 'UPDATE conversation_shares SET revoked_at=now() WHERE conversation_id=$1 AND revoked_at IS NULL'
const INSERT = 'INSERT INTO conversation_shares (conversation_id, slug, created_by, hide_reasoning, hide_methodology, expires_at) VALUES ($1,$2,$3,$4,$5, now() + make_interval(days => $6::int)) RETURNING *'
const SLUG = 'SELECT conversation_id, revoked_at, expires_at, hide_reasoning, hide_methodology FROM conversation_shares WHERE slug=$1 AND revoked_at IS NULL AND (expires_at IS NULL OR expires_at > now())'
const TITLE = 'SELECT title, chart_id FROM conversations WHERE id=$1'
const CHART = 'SELECT name FROM charts WHERE id=$1'
const actor = { conversationId: 'conversation-fixture', verifiedUserId: 'owner-fixture' }
const args = { ...actor, hideReasoning: false, hideMethodology: false }
const methods = ['listConversationSharesForActor', 'createConversationShareForActor', 'revokeConversationSharesForActor'] as const
const rawConversation = { id: actor.conversationId, chart_id: null, user_id: actor.verifiedUserId, module: 'consume', title: null, created_at: '2030-01-01T00:00:00.000Z' }
const activeRow = (extra: Record<string, unknown> = {}) => ({ slug: 'a123456789', created_at: '2030-01-01T00:00:00.000Z', expires_at: null, revoked_at: null, hide_reasoning: false, hide_methodology: false, ...extra })

type SharedRow = { conversation_id: string; revoked_at: string | null; expires_at: string | null; hide_reasoning: boolean; hide_methodology: boolean }
function fixture({ role = 'guest', conversation = rawConversation, shares = [], shared = { conversation_id: actor.conversationId, revoked_at: null, expires_at: null, hide_reasoning: true, hide_methodology: true }, chart = [] }: {
  role?: string
  conversation?: typeof rawConversation | null
  shares?: unknown[]
  shared?: SharedRow | null
  chart?: unknown[]
} = {}) {
  queryMock.mockImplementation(async (sql: string) => {
    if (sql === ROLE) return { rows: role === 'missing' ? [] : [{ role }] }
    if (sql === SLUG) return { rows: shared ? [shared] : [] }
    if (sql === ACTIVE) return { rows: shares }
    if (sql === TITLE || /FROM conversations WHERE id=\$1/.test(sql)) return { rows: conversation ? [conversation] : [] }
    if (sql === CHART) return { rows: chart }
    if (sql === INSERT || sql === REVOKE) return { rows: [] }
    throw new Error('unexpected fixture SQL')
  })
  loadMessagesMock.mockResolvedValue([])
}
const lifecycle = () => import('@/lib/conversations/shareLifecycle')
const view = () => import('@/lib/share/sharedConversationView')

beforeEach(() => { vi.resetModules(); queryMock.mockReset(); loadMessagesMock.mockReset(); fixture() })
afterEach(() => vi.useRealTimers())

describe('actor owners keep current role and actual conversation ownership checks', () => {
  it.each(methods)('%s resolves role and real getConversation before share SQL', async (method) => {
    await (await lifecycle())[method](args)
    expect(queryMock.mock.calls[0]).toEqual([ROLE, ['owner-fixture']])
    expect(queryMock.mock.calls[1][0]).toMatch(/FROM conversations WHERE id=\$1/)
    expect(queryMock.mock.calls[1][1]).toEqual(['conversation-fixture'])
    expect(queryMock.mock.calls[2]).toEqual([method === 'revokeConversationSharesForActor' ? REVOKE : ACTIVE, ['conversation-fixture']])
  })
  it.each(methods)('%s refuses another actor even when its JS input claims admin', async (method) => {
    const result = await (await lifecycle())[method]({ ...args, verifiedUserId: 'stranger-fixture', isSuperAdmin: true } as typeof args)
    expect(result).toBeNull()
    expect(queryMock).toHaveBeenCalledTimes(2)
    expect(queryMock.mock.calls[0]).toEqual([ROLE, ['stranger-fixture']])
    expect(queryMock.mock.calls.some(([sql]) => /conversation_shares/.test(String(sql)))).toBe(false)
  })
  it.each(methods)('%s keeps the internally derived super_admin path', async (method) => {
    fixture({ role: 'super_admin' })
    expect(await (await lifecycle())[method]({ ...args, verifiedUserId: 'admin-fixture' })).not.toBeNull()
    expect(queryMock.mock.calls[0]).toEqual([ROLE, ['admin-fixture']])
  })
  it.each(methods)('%s handles missing conversation without share SQL', async (method) => {
    fixture({ conversation: null })
    expect(await (await lifecycle())[method](args)).toBeNull()
    expect(queryMock).toHaveBeenCalledTimes(2)
  })
  it('missing profile retains current non-admin owner behavior', async () => {
    fixture({ role: 'missing' })
    expect(await (await lifecycle()).listConversationSharesForActor(actor)).toEqual({ share: null, shares: [] })
    expect(await (await lifecycle()).listConversationSharesForActor({ ...actor, verifiedUserId: 'stranger-fixture' })).toBeNull()
  })
  it('a role change is checked afresh on the next call', async () => {
    fixture({ role: 'super_admin' }); const owner = await lifecycle()
    expect(await owner.listConversationSharesForActor({ ...actor, verifiedUserId: 'stranger-fixture' })).not.toBeNull()
    fixture({ role: 'guest' }); queryMock.mockClear()
    expect(await owner.listConversationSharesForActor({ ...actor, verifiedUserId: 'stranger-fixture' })).toBeNull()
    expect(queryMock).toHaveBeenCalledTimes(2)
  })
  it('overlapping actors keep separate role/owner decisions and cannot share a cached listing', async () => {
    const owner = await lifecycle()
    const results = await Promise.all([owner.listConversationSharesForActor(actor), owner.listConversationSharesForActor({ ...actor, verifiedUserId: 'stranger-fixture' })])
    expect(results).toEqual([{ share: null, shares: [] }, null])
    expect(queryMock.mock.calls.filter(([sql]) => sql === ROLE).map(([, params]) => params)).toEqual([['owner-fixture'], ['stranger-fixture']])
    expect(queryMock.mock.calls.filter(([sql]) => sql === ACTIVE)).toHaveLength(1)
  })
  it.each([0, 1, 2])('query failure at stage %s propagates and prevents later effects', async (stage) => {
    const failure = new Error('synthetic query failure'); const implementation = queryMock.getMockImplementation()!; let index = 0
    queryMock.mockImplementation((...a) => index++ === stage ? Promise.reject(failure) : implementation(...a))
    await expect((await lifecycle()).createConversationShareForActor(args)).rejects.toBe(failure)
    expect(queryMock).toHaveBeenCalledTimes(stage + 1)
  })
})

describe('exact lifecycle SQL and legacy option behavior', () => {
  it('list preserves ordered rows, nullable metadata, and the most recent share', async () => {
    const rows = [activeRow({ created_at: null }), activeRow({ slug: 'b123456789', hide_reasoning: true })]
    fixture({ shares: rows })
    expect(await (await lifecycle()).listConversationSharesForActor(actor)).toEqual({ share: rows[0], shares: rows })
    expect(queryMock).toHaveBeenCalledTimes(3)
    expect(queryMock.mock.calls[2]).toEqual([ACTIVE, [actor.conversationId]])
  })
  it.each(['2031-01-01T00:00:00.000Z', '2031-06-01T00:00:00.000Z'])('create rechecks expired/revoked rows at %s but reuses null expiry', async (now) => {
    vi.useFakeTimers(); vi.setSystemTime(new Date(now))
    fixture({ shares: [activeRow({ slug: 'expired000', expires_at: now }), activeRow({ slug: 'revoked000', revoked_at: now }), activeRow({ slug: 'legacy0000' })] })
    expect(await (await lifecycle()).createConversationShareForActor(args)).toEqual({ slug: 'legacy0000' })
    expect(queryMock).toHaveBeenCalledTimes(3)
  })
  it('different options mint once with exact binds, TTL and no transaction or revocation', async () => {
    fixture({ shares: [activeRow()] })
    const result = await (await lifecycle()).createConversationShareForActor({ ...args, hideReasoning: true })
    expect(result?.slug).toMatch(/^[A-Za-z0-9]{10}$/)
    expect(queryMock.mock.calls).toHaveLength(4)
    expect(queryMock.mock.calls[3]).toEqual([INSERT, [actor.conversationId, result!.slug, actor.verifiedUserId, true, false, 30]])
  })
  it('revoke includes expired non-revoked rows with exactly one bound UPDATE', async () => {
    expect(await (await lifecycle()).revokeConversationSharesForActor(actor)).toEqual({ ok: true })
    expect(queryMock).toHaveBeenCalledTimes(3)
    expect(queryMock.mock.calls[2]).toEqual([REVOKE, [actor.conversationId]])
    expect(REVOKE).not.toContain('expires_at')
  })
  it('retains the trusted old helper without an added actor gate', async () => {
    const { listActiveConversationShares } = await import('@/lib/share/list_active_conversation_shares')
    expect(await listActiveConversationShares('old-trusted-fixture')).toEqual([])
    expect(queryMock.mock.calls).toEqual([[ACTIVE, ['old-trusted-fixture']]])
  })
})

describe('active-viewer read owner keeps SQL-only slug and server projection contracts', () => {
  const viewer = { slug: 'a123456789', verifiedViewerUid: 'any-active-viewer-fixture' }
  it.each([undefined, ''])('missing or empty verified viewer UID (%s) refuses before every read', async (verifiedViewerUid) => {
    const input = { slug: viewer.slug, verifiedViewerUid } as typeof viewer
    expect(await (await view()).readSharedConversationView(input)).toBeNull()
    expect(queryMock).not.toHaveBeenCalled()
    expect(loadMessagesMock).not.toHaveBeenCalled()
  })
  it('uses exactly slug, title, chart reads then one message owner, including null chart id', async () => {
    expect(await (await view()).readSharedConversationView(viewer)).toEqual({ title: null, optionalChartName: undefined, visibleMessages: [] })
    expect(queryMock.mock.calls).toEqual([[SLUG, [viewer.slug]], [TITLE, [actor.conversationId]], [CHART, [null]]])
    expect(loadMessagesMock.mock.calls).toEqual([[actor.conversationId, { includeCanonicalText: true }]])
  })
  it('missing/expired/revoked slug comes from SQL, without a JS time filter', async () => {
    fixture({ shared: null })
    expect(await (await view()).readSharedConversationView(viewer)).toBeNull()
    expect(queryMock.mock.calls).toEqual([[SLUG, [viewer.slug]]]); expect(loadMessagesMock).not.toHaveBeenCalled()
  })
  it('missing conversation stops before charts and messages', async () => {
    fixture({ conversation: null })
    expect(await (await view()).readSharedConversationView(viewer)).toBeNull()
    expect(queryMock.mock.calls).toHaveLength(2); expect(loadMessagesMock).not.toHaveBeenCalled()
  })
  it('retains the SQL-only check site even if a synthetic query violates its predicate', async () => {
    fixture({ shared: { conversation_id: actor.conversationId, revoked_at: '2030-01-01', expires_at: '2030-01-01', hide_reasoning: true, hide_methodology: true } })
    expect(await (await view()).readSharedConversationView(viewer)).not.toBeNull()
    expect(queryMock).toHaveBeenCalledTimes(3)
  })
  it('stored options redact before owner return and discard private metadata and IDs', async () => {
    loadMessagesMock.mockResolvedValue([{ id: 'private-stored-id', role: 'assistant', parts: [{ type: 'reasoning', text: 'hidden-reasoning-fixture' }, { type: 'text', text: 'safe answer\n```marsys_methodology_block\nhidden-method-fixture\n```' }, { type: 'tool-retrieval', input: 'private-tool-fixture' }], metadata: { role: 'super_admin', private: 'private-meta-fixture' } }])
    const result = await (await view()).readSharedConversationView(viewer)
    expect(result?.visibleMessages).toEqual([{ id: 'm0', role: 'assistant', parts: [{ type: 'text', text: 'safe answer' }] }])
    for (const token of ['private-', 'hidden-', 'super_admin', 'conversation-fixture', 'chart_id']) expect(JSON.stringify(result)).not.toContain(token)
  })
  it.each([0, 1, 2])('query error %s prevents later reads/messages', async (stage) => {
    const failure = new Error('synthetic read failure'); const implementation = queryMock.getMockImplementation()!; let index = 0
    queryMock.mockImplementation((...a) => index++ === stage ? Promise.reject(failure) : implementation(...a))
    await expect((await view()).readSharedConversationView(viewer)).rejects.toBe(failure)
    expect(queryMock).toHaveBeenCalledTimes(stage + 1); expect(loadMessagesMock).not.toHaveBeenCalled()
  })
  it('message failure propagates once after the same three reads', async () => {
    const failure = new Error('synthetic loader failure'); loadMessagesMock.mockRejectedValue(failure)
    await expect((await view()).readSharedConversationView(viewer)).rejects.toBe(failure)
    expect(queryMock).toHaveBeenCalledTimes(3); expect(loadMessagesMock).toHaveBeenCalledTimes(1)
  })
})

describe('delivered extraction boundary', () => {
  it('route/page avoid raw SQL and message-loader imports; owners are server-only', () => {
    const route = readFileSync(new URL('../../../app/api/conversations/[id]/share/route.ts', import.meta.url), 'utf8')
    const page = readFileSync(new URL('../../../app/share/[slug]/page.tsx', import.meta.url), 'utf8')
    expect(route).not.toMatch(/from ['"]@\/lib\/(?:db\/client|conversations['"])/)
    expect(route).not.toMatch(/\b(?:SELECT|INSERT|UPDATE|DELETE FROM)\b.*(?:profiles|conversation_shares)/)
    expect(page).not.toMatch(/from ['"]@\/lib\/(?:db\/client|persistence\/conversation_writer|share\/shareView)['"]/)
    for (const source of ['../../conversations/shareLifecycle.ts', '../sharedConversationView.ts']) {
      expect(readFileSync(new URL(source, import.meta.url), 'utf8')).toMatch(/^import 'server-only'/)
    }
  })
})
