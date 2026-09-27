/**
 * /api/conversations/[id]/branches — correction-history is read-only
 * (Jātaka Phase-A hardening, item 1). Branch creation on a correction-archived
 * conversation returns the canonical 409 before any INSERT; listing branches
 * (GET) stays available; manual archives keep existing semantics.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockQuery, mockGetConversation } = vi.hoisted(() => ({ mockQuery: vi.fn(), mockGetConversation: vi.fn() }))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'owner-uid' })) }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/conversations', () => ({ getConversation: mockGetConversation }))

import { GET, POST } from '../[id]/branches/route'

const ctx = { params: Promise.resolve({ id: 'conv-1' }) }
const HISTORICAL = { id: 'conv-1', chart_id: 'c1', archived_at: '2026-09-27T10:00:00Z', archive_reason: 'chart_details_changed' }

function post() {
  return new Request('http://localhost/api/conversations/conv-1/branches', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ edited_message_id: 'm2', snapshot_jsonb: { a: 1 } }),
  })
}

const inserts = () => mockQuery.mock.calls.filter(([sql]) => /^\s*(INSERT|UPDATE|DELETE)/i.test(sql))

beforeEach(() => {
  vi.clearAllMocks()
  mockQuery.mockImplementation(async (sql: string) => {
    if (/FROM profiles/.test(sql)) return { rows: [{ role: 'guest' }] }
    if (/INSERT INTO conversation_branches/.test(sql)) return { rows: [{ id: 'b1', created_at: '2026-09-27' }] }
    return { rows: [] }
  })
})

describe('branches on a correction-archived conversation', () => {
  it('refuses branch creation with the canonical 409 and inserts nothing', async () => {
    mockGetConversation.mockResolvedValue(HISTORICAL)
    const res = await POST(post(), ctx)
    expect(res.status).toBe(409)
    expect(await res.json()).toEqual({
      error: { code: 'CONVERSATION_ARCHIVED_READ_ONLY', message: 'This conversation is historical and read-only.', retry: false },
    })
    expect(inserts()).toHaveLength(0)
  })

  it('still lists existing branches', async () => {
    mockGetConversation.mockResolvedValue(HISTORICAL)
    const res = await GET(new Request('http://localhost'), ctx)
    expect(res.status).toBe(200)
  })
})

describe('branches on other conversations', () => {
  it('creates a branch on an active conversation', async () => {
    mockGetConversation.mockResolvedValue({ ...HISTORICAL, archived_at: null, archive_reason: null })
    expect((await POST(post(), ctx)).status).toBe(201)
    expect(inserts()).toHaveLength(1)
  })

  it('keeps existing semantics for a manual archive', async () => {
    mockGetConversation.mockResolvedValue({ ...HISTORICAL, archive_reason: null })
    expect((await POST(post(), ctx)).status).toBe(201)
  })
})
