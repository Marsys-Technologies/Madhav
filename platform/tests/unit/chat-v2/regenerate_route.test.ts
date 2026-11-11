/**
 * β1 — regenerate route unit tests.
 *
 * Tests the Consult regenerate handler behind the legacy redirect: access,
 * parent resolution, conversation_messages truncation, and error paths.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Hoisted mocks ──────────────────────────────────────────────────────────

const { conversationId, parentId, foreignConversationId, mockUser, mockConv } = vi.hoisted(() => {
  const conversationId = '00000000-0000-4000-8000-000000000001'
  return {
    conversationId,
    parentId: '00000000-0000-4000-8000-000000000002',
    foreignConversationId: '00000000-0000-4000-8000-000000000003',
    mockUser: { uid: 'user-abc' },
    mockConv: {
      id: conversationId,
      chart_id: '00000000-0000-4000-8000-000000000004',
      user_id: 'user-abc',
      module: 'consume',
      title: null,
      created_at: '2026-01-01',
      updated_at: null,
      archived_at: null,
    },
  }
})

vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(async () => mockUser as never),
}))

const queryMock = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('server-only', () => ({}))

vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(async () => mockConv),
}))

// Jātaka chart workspace: every reading door admits only a Ready chart (shared
// readiness gate) — this harness exercises a Ready chart.
vi.mock('@/lib/charts/readiness', () => ({
  getChartReadinessMap: vi.fn(async (ids: string[]) => new Map(ids.map((id) => [id, { state: 'ready' }]))),
  isDerivedChartReady: (r: { state: string }) => r.state === 'ready',
}))

vi.mock('@/lib/errors', () => ({
  errorResponse: (code: string, message: string, status: number) => Response.json({ error: { code, message } }, { status }),
  res: {
    unauthenticated: () => new Response('Unauthorized', { status: 401 }),
    badRequest: (msg: string) => new Response(msg, { status: 400 }),
    notFound: (entity: string) => new Response(`${entity} not found`, { status: 404 }),
    dbError: () => new Response('DB error', { status: 500 }),
  },
}))

import { POST } from '../../../src/app/api/chat/consult/regenerate/route'
import { getServerUser } from '@/lib/firebase/server'
import { getConversation } from '@/lib/conversations'

// ── Helpers ───────────────────────────────────────────────────────────────

function makeRequest(body: object) {
  return new Request('http://localhost/api/chat/consult/regenerate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

const cutoff = '2026-05-16T10:00:00.123456Z'
const later = '2026-05-16T10:00:00.123457Z'
const parent = { id: parentId, conversationId, createdAt: cutoff }
const peer = { id: '00000000-0000-4000-8000-000000000005', conversationId, createdAt: cutoff }
const descendant = { id: '00000000-0000-4000-8000-000000000006', conversationId, createdAt: later }
const foreign = {
  id: '00000000-0000-4000-8000-000000000007',
  conversationId: foreignConversationId,
  createdAt: later,
}
const missingParentId = '00000000-0000-4000-8000-000000000008'
const fixtureMessages = [parent, peer, descendant, foreign]
let messages = [...fixtureMessages]

describe('POST /api/chat/consult/regenerate', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    messages = [...fixtureMessages]
    vi.mocked(getServerUser).mockResolvedValue(mockUser as never)
    vi.mocked(getConversation).mockResolvedValue(mockConv as never)
    queryMock.mockReset()
      .mockResolvedValueOnce({ rows: [{ role: 'guest' }] })
      .mockImplementationOnce(async (sql: string, [messageId, scopeId]: [string, string]) => {
        expect(sql).toMatch(/WHERE id=\$1 AND conversation_id=\$2\s+FOR UPDATE/)
        expect(sql).toMatch(/DELETE FROM conversation_messages\s+USING parent/)
        expect(sql).toMatch(/conversation_messages\.conversation_id=\$2\s+AND conversation_messages\.created_at > parent\.created_at\s+AND NOT parent\.has_attachment/)

        const selected = messages.find(message => message.id === messageId && message.conversationId === scopeId)
        if (!selected) return { rows: [] }

        messages = messages.filter(message => message.conversationId !== scopeId || message.createdAt <= selected.createdAt)
        return { rows: [{ has_attachment: false }] }
      })
  })

  it('returns 200 and truncates only later messages in the same conversation', async () => {
    const res = await POST(makeRequest({ conversation_id: conversationId, parent_message_id: parentId }))

    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ ok: true, truncated_after: parentId })
    expect(queryMock).toHaveBeenCalledTimes(2)
    expect(queryMock).toHaveBeenNthCalledWith(2, expect.stringContaining('FOR UPDATE'), [parentId, conversationId])
    expect(messages).toEqual([parent, peer, foreign])
  })

  it('returns 401 when unauthenticated', async () => {
    vi.mocked(getServerUser).mockResolvedValueOnce(null)
    const res = await POST(makeRequest({ conversation_id: conversationId, parent_message_id: parentId }))
    expect(res.status).toBe(401)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('returns 400 when conversation_id missing', async () => {
    const res = await POST(makeRequest({ parent_message_id: parentId }))
    expect(res.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('returns 400 when parent_message_id missing', async () => {
    const res = await POST(makeRequest({ conversation_id: conversationId }))
    expect(res.status).toBe(400)
    expect(queryMock).not.toHaveBeenCalled()
  })

  it('returns 404 when conversation not found', async () => {
    const missingConversationId = '00000000-0000-4000-8000-000000000009'
    vi.mocked(getConversation).mockResolvedValueOnce(null)
    const res = await POST(makeRequest({ conversation_id: missingConversationId, parent_message_id: parentId }))
    expect(res.status).toBe(404)
    expect(await res.text()).toBe('conversation not found')
    expect(getConversation).toHaveBeenCalledWith({ id: missingConversationId, userId: mockUser.uid, isSuperAdmin: false })
    expect(queryMock).toHaveBeenCalledTimes(1)
    expect(messages).toEqual(fixtureMessages)
  })

  it.each([missingParentId, foreign.id])('returns the same 404 for an unknown or foreign parent (%s)', async requestedParentId => {
    const res = await POST(makeRequest({ conversation_id: conversationId, parent_message_id: requestedParentId }))
    expect(res.status).toBe(404)
    expect(await res.text()).toBe('parent_message not found')
    expect(queryMock).toHaveBeenCalledTimes(2)
    expect(queryMock).toHaveBeenNthCalledWith(2, expect.stringContaining('FOR UPDATE'), [requestedParentId, conversationId])
    expect(messages).toEqual(fixtureMessages)
  })
})
