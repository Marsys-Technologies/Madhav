/**
 * β2 — Conversations API route integration tests.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Hoisted mocks ──────────────────────────────────────────────────────────

const { mockUser, mockConv, mockMessages } = vi.hoisted(() => ({
  mockUser: { uid: 'user-123' },
  mockConv: {
    id: 'c1',
    chart_id: 'chart-1',
    user_id: 'user-123',
    module: 'consume',
    title: 'Test',
    created_at: '2026-01-01',
    updated_at: null,
    archived_at: null,
  },
  mockMessages: [
    { id: 'msg-1', role: 'user', parts: [{ type: 'text', text: 'hi' }], metadata: {} },
    { id: 'msg-2', role: 'assistant', parts: [{ type: 'text', text: 'hello' }], metadata: {} },
  ],
}))

vi.mock('@/lib/firebase/server', () => ({
  getServerUser: vi.fn(async () => mockUser as never),
}))

vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async () => ({ rows: [{ role: 'user' }] })),
}))

vi.mock('server-only', () => ({}))

vi.mock('@/lib/conversations', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/conversations')>()
  return {
    ...actual,
    listConversations: vi.fn(async () => [mockConv]),
    createConversation: vi.fn(async () => ({ ...mockConv, id: 'new-conv-id' })),
    getConversation: vi.fn(async () => mockConv),
    updateConversationTitle: vi.fn(async () => {}),
  }
})

vi.mock('@/lib/persistence/conversation_writer', () => ({
  archiveConversation: vi.fn(async () => {}),
  loadConversationMessagesV2: vi.fn(async () => mockMessages),
}))

vi.mock('@/lib/errors', () => ({
  res: {
    unauthenticated: () => new Response('Unauthorized', { status: 401 }),
    badRequest: (msg: string) => new Response(msg, { status: 400 }),
    notFound: (entity: string) => new Response(`${entity} not found`, { status: 404 }),
    dbError: () => new Response('DB error', { status: 500 }),
  },
}))

// ── Import after mocks ─────────────────────────────────────────────────────

import { GET as ConversationsGET, POST as ConversationsPOST } from '../../../src/app/api/conversations/route'
import { GET as MessagesGET } from '../../../src/app/api/conversations/[id]/messages/route'
import { DELETE as ConversationDELETE } from '../../../src/app/api/conversations/[id]/route'
import { getServerUser } from '@/lib/firebase/server'
import { createConversation } from '@/lib/conversations'
import { archiveConversation } from '@/lib/persistence/conversation_writer'

// ── Tests ─────────────────────────────────────────────────────────────────

describe('POST /api/conversations', () => {
  beforeEach(() => vi.clearAllMocks())

  it('creates a conversation and returns 201', async () => {
    vi.mocked(getServerUser).mockResolvedValueOnce(mockUser as never)
    const req = new Request('http://localhost/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chartId: 'chart-1', module: 'consume' }),
    })
    const res = await ConversationsPOST(req)

    expect(res.status).toBe(201)
    const body = await res.json() as { conversation: { id: string } }
    expect(body.conversation.id).toBe('new-conv-id')
    expect(createConversation).toHaveBeenCalledWith({
      chartId: 'chart-1',
      userId: 'user-123',
      module: 'consume',
    })
  })

  it('returns 401 when unauthenticated', async () => {
    vi.mocked(getServerUser).mockResolvedValueOnce(null)
    const req = new Request('http://localhost/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ chartId: 'chart-1' }),
    })
    const res = await ConversationsPOST(req)
    expect(res.status).toBe(401)
  })

  it('returns 400 when chartId missing', async () => {
    vi.mocked(getServerUser).mockResolvedValueOnce(mockUser as never)
    const req = new Request('http://localhost/api/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    })
    const res = await ConversationsPOST(req)
    expect(res.status).toBe(400)
  })
})

describe('GET /api/conversations', () => {
  beforeEach(() => vi.clearAllMocks())

  it('returns conversation list', async () => {
    vi.mocked(getServerUser).mockResolvedValueOnce(mockUser as never)
    const req = new Request('http://localhost/api/conversations?chartId=chart-1')
    const res = await ConversationsGET(req)
    expect(res.status).toBe(200)
    const body = await res.json() as { conversations: unknown[] }
    expect(body.conversations).toHaveLength(1)
  })

  it('returns 400 without chartId', async () => {
    vi.mocked(getServerUser).mockResolvedValueOnce(mockUser as never)
    const req = new Request('http://localhost/api/conversations')
    const res = await ConversationsGET(req)
    expect(res.status).toBe(400)
  })
})

describe('GET /api/conversations/[id]/messages', () => {
  beforeEach(() => vi.clearAllMocks())

  it('returns v2 messages for a conversation', async () => {
    vi.mocked(getServerUser).mockResolvedValueOnce(mockUser as never)
    const ctx = { params: Promise.resolve({ id: 'c1' }) }
    const res = await MessagesGET(
      new Request('http://localhost/api/conversations/c1/messages'),
      ctx,
    )

    expect(res.status).toBe(200)
    const body = await res.json() as { messages: Array<{ id: string }> }
    expect(body.messages).toHaveLength(2)
    expect(body.messages[0]!.id).toBe('msg-1')
    expect(body.messages[1]!.id).toBe('msg-2')
  })

  it('returns 401 when unauthenticated', async () => {
    vi.mocked(getServerUser).mockResolvedValueOnce(null)
    const ctx = { params: Promise.resolve({ id: 'c1' }) }
    const res = await MessagesGET(
      new Request('http://localhost/api/conversations/c1/messages'),
      ctx,
    )
    expect(res.status).toBe(401)
  })
})

describe('DELETE /api/conversations/[id] — soft delete', () => {
  beforeEach(() => vi.clearAllMocks())

  it('archives (soft-deletes) the conversation', async () => {
    vi.mocked(getServerUser).mockResolvedValueOnce(mockUser as never)
    const ctx = { params: Promise.resolve({ id: 'c1' }) }
    const res = await ConversationDELETE(
      new Request('http://localhost/api/conversations/c1'),
      ctx,
    )

    expect(res.status).toBe(200)
    expect(archiveConversation).toHaveBeenCalledWith('c1')
  })
})
