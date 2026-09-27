/**
 * Legacy consult continue door — correction-archived history is read-only
 * (Jātaka chart workspace, Task 8). No message load or model stream starts.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockReadiness } = vi.hoisted(() => ({ mockReadiness: vi.fn() }))
vi.mock('@/lib/charts/readingGate', () => ({ checkReadingReadiness: mockReadiness }))
const NOT_READY = { ok: false, code: 'CHART_RECOMPUTE_REQUIRED', state: 'building', message: 'This chart is still being computed.' }

const { mockGetConversation, mockLoad, mockStreamText } = vi.hoisted(() => ({
  mockGetConversation: vi.fn(),
  mockLoad: vi.fn(),
  mockStreamText: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'owner-uid' })) }))
vi.mock('@/lib/db/client', () => ({ query: vi.fn(async () => ({ rows: [{ role: 'guest' }] })) }))
vi.mock('@/lib/conversations', () => ({ getConversation: mockGetConversation }))
vi.mock('@/lib/persistence/conversation_writer', () => ({ loadConversationMessagesV2: mockLoad }))
vi.mock('ai', async (importOriginal) => ({ ...(await importOriginal<typeof import('ai')>()), streamText: mockStreamText }))

import { POST } from '../route'

function req() {
  return new Request('http://localhost/api/chat/consult/continue', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ conversation_id: 'conv-1', last_message_id: 'm9' }),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  mockReadiness.mockResolvedValue({ ok: true })
})

describe('POST /api/chat/consult/continue — correction-archived conversation', () => {
  it('refuses with 409 CONVERSATION_ARCHIVED_READ_ONLY before loading messages or calling the model', async () => {
    mockGetConversation.mockResolvedValue({ id: 'conv-1', chart_id: 'c', archived_at: '2026-09-27T10:00:00Z', archive_reason: 'chart_details_changed' })
    const res = await POST(req())
    expect(res.status).toBe(409)
    expect((await res.json()).error.code).toBe('CONVERSATION_ARCHIVED_READ_ONLY')
    expect(mockLoad).not.toHaveBeenCalled()
    expect(mockStreamText).not.toHaveBeenCalled()
  })

  it('lets an active conversation continue past the gate', async () => {
    mockGetConversation.mockResolvedValue({ id: 'conv-1', chart_id: 'c', archived_at: null, archive_reason: null })
    mockLoad.mockRejectedValue(new Error('stop after gate'))
    const res = await POST(req())
    expect(res.status).not.toBe(409)
    expect(mockLoad).toHaveBeenCalled()
  })
})

describe('POST /api/chat/consult/continue — shared readiness gate', () => {
  it('refuses a chart that is not Ready before loading messages or calling the model', async () => {
    mockGetConversation.mockResolvedValue({ id: 'conv-1', chart_id: 'c', archived_at: null, archive_reason: null })
    mockReadiness.mockResolvedValue(NOT_READY)
    const res = await POST(req())
    expect(res.status).toBe(409)
    const body = await res.json()
    expect(body.error.code).toBe('CHART_RECOMPUTE_REQUIRED')
    expect(body.error.message).toBe('This chart is still being computed.')
    expect(mockReadiness).toHaveBeenCalledWith('c')
    expect(mockLoad).not.toHaveBeenCalled()
    expect(mockStreamText).not.toHaveBeenCalled()
  })
})
