/**
 * β1 — regenerate route unit tests.
 *
 * Tests POST /api/chat/consume/regenerate: access control, parent resolution,
 * truncation of conversation_messages, and error paths.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Hoisted mocks ──────────────────────────────────────────────────────────

const { mockUser, mockConv } = vi.hoisted(() => ({
  mockUser: { uid: 'user-abc' },
  mockConv: {
    id: 'conv-1',
    chart_id: 'chart-1',
    user_id: 'user-abc',
    module: 'consume',
    title: null,
    created_at: '2026-01-01',
    updated_at: null,
    archived_at: null,
  },
}))

vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(async () => mockUser as never),
}))

const queryMock = vi.hoisted(() => vi.fn())
vi.mock('@/lib/db/client', () => ({ query: queryMock }))
vi.mock('server-only', () => ({}))

vi.mock('@/lib/conversations', () => ({
  getConversation: vi.fn(async () => mockConv),
}))

vi.mock('@/lib/errors', () => ({
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
  return new Request('http://localhost/api/chat/consume/regenerate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

// ── Tests ─────────────────────────────────────────────────────────────────

describe('POST /api/chat/consume/regenerate', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(getServerUser).mockResolvedValue(mockUser as never)
    vi.mocked(getConversation).mockResolvedValue(mockConv as never)
    // Default query mock: profiles returns non-admin, parent row found, DELETE succeeds.
    queryMock
      .mockResolvedValueOnce({ rows: [{ role: 'user' }] })               // profiles
      .mockResolvedValueOnce({ rows: [{ created_at: '2026-05-16T10:00:00Z' }] }) // parent lookup
      .mockResolvedValueOnce({ rows: [] })                                 // DELETE
  })

  it('returns 200 and truncates messages after parent', async () => {
    const res = await POST(makeRequest({
      conversation_id: 'conv-1',
      parent_message_id: 'msg-parent',
    }))

    expect(res.status).toBe(200)
    const body = await res.json() as { ok: boolean; truncated_after: string }
    expect(body.ok).toBe(true)
    expect(body.truncated_after).toBe('msg-parent')

    // DELETE called with correct args.
    const deleteCalls = queryMock.mock.calls.filter((c) =>
      String(c[0]).includes('DELETE FROM conversation_messages'),
    )
    expect(deleteCalls).toHaveLength(1)
    expect(deleteCalls[0]![1]).toEqual(['conv-1', '2026-05-16T10:00:00Z'])
  })

  it('returns 401 when unauthenticated', async () => {
    vi.mocked(getServerUser).mockResolvedValueOnce(null)
    const res = await POST(makeRequest({ conversation_id: 'conv-1', parent_message_id: 'msg-p' }))
    expect(res.status).toBe(401)
  })

  it('returns 400 when conversation_id missing', async () => {
    const res = await POST(makeRequest({ parent_message_id: 'msg-p' }))
    expect(res.status).toBe(400)
  })

  it('returns 400 when parent_message_id missing', async () => {
    const res = await POST(makeRequest({ conversation_id: 'conv-1' }))
    expect(res.status).toBe(400)
  })

  it('returns 404 when conversation not found', async () => {
    vi.mocked(getConversation).mockResolvedValueOnce(null)
    queryMock.mockReset()
    queryMock.mockResolvedValueOnce({ rows: [{ role: 'user' }] }) // profiles
    const res = await POST(makeRequest({ conversation_id: 'conv-missing', parent_message_id: 'msg-p' }))
    expect(res.status).toBe(404)
  })

  it('returns 404 when parent_message_id not found in DB', async () => {
    queryMock.mockReset()
    queryMock
      .mockResolvedValueOnce({ rows: [{ role: 'user' }] }) // profiles
      .mockResolvedValueOnce({ rows: [] })                   // parent lookup: empty
    const res = await POST(makeRequest({ conversation_id: 'conv-1', parent_message_id: 'msg-gone' }))
    expect(res.status).toBe(404)
  })
})
