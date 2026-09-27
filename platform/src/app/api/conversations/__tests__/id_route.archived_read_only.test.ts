/**
 * /api/conversations/[id] — correction-archived history is read-only
 * (Jātaka chart workspace, Task 8). GET still reads it; every PATCH field
 * (title, pin, archive/unarchive, folder) and DELETE return 409
 * CONVERSATION_ARCHIVED_READ_ONLY without writing. Manual archives (reason
 * NULL) keep their existing behaviour, including unarchive.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockQuery, mockGetConversation, mockUpdateTitle, mockArchive, mockLoad } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetConversation: vi.fn(),
  mockUpdateTitle: vi.fn(),
  mockArchive: vi.fn(),
  mockLoad: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'owner-uid' })) }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/conversations', () => ({ getConversation: mockGetConversation, updateConversationTitle: mockUpdateTitle }))
vi.mock('@/lib/persistence/conversation_writer', () => ({ archiveConversation: mockArchive, loadConversationMessagesV2: mockLoad }))

import { DELETE, GET, PATCH } from '../[id]/route'

const ctx = { params: Promise.resolve({ id: 'conv-1' }) }
const HISTORICAL = { id: 'conv-1', chart_id: 'c1', archived_at: '2026-09-27T10:00:00Z', archive_reason: 'chart_details_changed' }
const MANUAL = { ...HISTORICAL, archive_reason: null }

function patch(body: object) {
  return new Request('http://localhost/api/conversations/conv-1', {
    method: 'PATCH',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
}

const wrote = () => mockQuery.mock.calls.some(([sql]) => /^\s*(UPDATE|INSERT|DELETE)/i.test(sql))

beforeEach(() => {
  vi.clearAllMocks()
  mockQuery.mockImplementation(async (sql: string) => (/FROM profiles/.test(sql) ? { rows: [{ role: 'guest' }] } : { rows: [] }))
  mockLoad.mockResolvedValue([])
})

describe('correction-archived conversation', () => {
  it('stays readable', async () => {
    mockGetConversation.mockResolvedValue(HISTORICAL)
    const res = await GET(new Request('http://localhost'), ctx)
    expect(res.status).toBe(200)
    expect((await res.json()).conversation.archive_reason).toBe('chart_details_changed')
  })

  it.each([
    ['title', { title: 'Renamed' }],
    ['pin', { pinned: true }],
    ['unarchive', { archived: false }],
    ['re-archive', { archived: true }],
    ['folder move', { folder_id: 'f1' }],
    ['folder removal', { folder_id: null }],
  ])('refuses a %s change with 409 and writes nothing', async (_label, body) => {
    mockGetConversation.mockResolvedValue(HISTORICAL)
    const res = await PATCH(patch(body), ctx)
    expect(res.status).toBe(409)
    expect(await res.json()).toEqual({
      error: { code: 'CONVERSATION_ARCHIVED_READ_ONLY', message: 'This conversation is historical and read-only.', retry: false },
    })
    expect(wrote()).toBe(false)
    expect(mockUpdateTitle).not.toHaveBeenCalled()
  })

  it('refuses DELETE with 409 and never re-archives', async () => {
    mockGetConversation.mockResolvedValue(HISTORICAL)
    const res = await DELETE(new Request('http://localhost'), ctx)
    expect(res.status).toBe(409)
    expect(mockArchive).not.toHaveBeenCalled()
  })
})

describe('manual archive keeps existing semantics', () => {
  it('can still be unarchived', async () => {
    mockGetConversation.mockResolvedValue(MANUAL)
    const res = await PATCH(patch({ archived: false }), ctx)
    expect(res.status).toBe(200)
    expect(mockQuery.mock.calls.some(([sql]) => /archived_at=NULL/.test(sql))).toBe(true)
  })

  it('can still be renamed', async () => {
    mockGetConversation.mockResolvedValue(MANUAL)
    expect((await PATCH(patch({ title: 'New' }), ctx)).status).toBe(200)
    expect(mockUpdateTitle).toHaveBeenCalledWith('conv-1', 'New')
  })
})
