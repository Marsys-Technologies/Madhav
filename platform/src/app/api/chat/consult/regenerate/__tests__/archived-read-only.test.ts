/**
 * Legacy consult regenerate door — correction-archived history is read-only
 * (Jātaka chart workspace, Task 8). Regenerate deletes messages after the
 * parent, so the lock must refuse before any read or DELETE.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockReadiness } = vi.hoisted(() => ({ mockReadiness: vi.fn() }))
vi.mock('@/lib/charts/readingGate', () => ({ checkReadingReadiness: mockReadiness }))
const NOT_READY = { ok: false, code: 'CHART_RECOMPUTE_REQUIRED', state: 'building', message: 'This chart is still being computed.', retryable: true }
const FAILED = { ok: false, code: 'CHART_RECOMPUTE_REQUIRED', state: 'failed', message: 'The latest build failed.', retryable: false }

const { mockGetConversation, mockQuery } = vi.hoisted(() => ({ mockGetConversation: vi.fn(), mockQuery: vi.fn() }))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'owner-uid' })) }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/conversations', () => ({ getConversation: mockGetConversation }))

import { POST } from '../route'

function req() {
  return new Request('http://localhost/api/chat/consult/regenerate', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ conversation_id: 'conv-1', parent_message_id: 'm1' }),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  mockReadiness.mockResolvedValue({ ok: true })
  mockQuery.mockImplementation(async (sql: string) => (/FROM profiles/.test(sql) ? { rows: [{ role: 'guest' }] } : { rows: [{ created_at: '2026-09-01' }] }))
})

describe('POST /api/chat/consult/regenerate — correction-archived conversation', () => {
  it('refuses with 409 CONVERSATION_ARCHIVED_READ_ONLY and never deletes a message', async () => {
    mockGetConversation.mockResolvedValue({ id: 'conv-1', archived_at: '2026-09-27T10:00:00Z', archive_reason: 'chart_details_changed' })
    const res = await POST(req())
    expect(res.status).toBe(409)
    expect((await res.json()).error.code).toBe('CONVERSATION_ARCHIVED_READ_ONLY')
    expect(mockQuery.mock.calls.some(([sql]) => /DELETE/i.test(sql))).toBe(false)
  })

  it('still truncates an active conversation', async () => {
    mockGetConversation.mockResolvedValue({ id: 'conv-1', archived_at: null, archive_reason: null })
    const res = await POST(req())
    expect(res.status).toBe(200)
    expect(mockQuery.mock.calls.some(([sql]) => /DELETE FROM conversation_messages/.test(sql))).toBe(true)
  })
})

describe('POST /api/chat/consult/regenerate — shared readiness gate', () => {
  it('refuses a chart that is not Ready before deleting anything, so the re-post cannot strand a truncated conversation', async () => {
    mockGetConversation.mockResolvedValue({ id: 'conv-1', chart_id: 'c', archived_at: null, archive_reason: null })
    mockReadiness.mockResolvedValue(NOT_READY)
    const res = await POST(req())
    expect(res.status).toBe(409)
    expect((await res.json()).error.code).toBe('CHART_RECOMPUTE_REQUIRED')
    expect(mockReadiness).toHaveBeenCalledWith('c')
    expect(mockQuery.mock.calls.some(([sql]) => /DELETE/i.test(sql))).toBe(false)
  })
})

describe('POST /api/chat/consult/regenerate — refusal retry flag follows the gate', () => {
  it.each([
    [NOT_READY, true],
    [FAILED, false],
  ])('%o → retry %s', async (gate, retry) => {
    mockGetConversation.mockResolvedValue({ id: 'conv-1', chart_id: 'c', archived_at: null, archive_reason: null })
    mockReadiness.mockResolvedValue(gate)
    const res = await POST(req())
    expect(res.status).toBe(409)
    expect((await res.json()).error.retry).toBe(retry)
  })
})
