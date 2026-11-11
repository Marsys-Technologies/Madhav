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

const { mockGetConversation, mockQuery, mockGetServerUser } = vi.hoisted(() => ({
  mockGetConversation: vi.fn(), mockQuery: vi.fn(), mockGetServerUser: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: mockGetServerUser }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/conversations', () => ({ getConversation: mockGetConversation }))

import { POST } from '../route'
import { POST as redirect } from '../../../consume/regenerate/route'

const CONVERSATION_ID = '00000000-0000-4000-8000-000000000001'
const PARENT_ID = '00000000-0000-4000-8000-000000000002'
const parentBinding = [PARENT_ID, CONVERSATION_ID]
const activeConversation = { id: CONVERSATION_ID, chart_id: 'c', archived_at: null, archive_reason: null }

function req(body: unknown = { conversation_id: CONVERSATION_ID, parent_message_id: PARENT_ID }, endpoint = '/api/chat/consult/regenerate') {
  return new Request('https://fixture.invalid' + endpoint, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  mockReadiness.mockResolvedValue({ ok: true })
  mockGetServerUser.mockResolvedValue({ uid: 'owner-uid' })
  mockGetConversation.mockResolvedValue(activeConversation)
  mockQuery.mockReset().mockResolvedValueOnce({ rows: [{ role: 'guest' }] })
    .mockResolvedValueOnce({ rows: [{ has_attachment: false }] })
})

describe('POST /api/chat/consult/regenerate — correction-archived conversation', () => {
  it('refuses with 409 CONVERSATION_ARCHIVED_READ_ONLY and never deletes a message', async () => {
    mockGetConversation.mockResolvedValue({ id: CONVERSATION_ID, archived_at: '2026-09-27T10:00:00Z', archive_reason: 'chart_details_changed' })
    const res = await POST(req())
    expect(res.status).toBe(409)
    expect((await res.json()).error.code).toBe('CONVERSATION_ARCHIVED_READ_ONLY')
    expect(mockQuery.mock.calls.some(([sql]) => /DELETE/i.test(sql))).toBe(false)
  })

  it('still truncates an active conversation', async () => {
    mockGetConversation.mockResolvedValue({ id: CONVERSATION_ID, archived_at: null, archive_reason: null })
    const res = await POST(req())
    expect(res.status).toBe(200)
    expect(await res.json()).toEqual({ ok: true, truncated_after: PARENT_ID })
    expect(mockQuery).toHaveBeenCalledTimes(2)
    const [sql, params] = mockQuery.mock.calls[1]
    expect(params).toEqual(parentBinding)
    expect(sql).toMatch(/WHERE id=\$1 AND conversation_id=\$2\s+FOR UPDATE/)
    expect(sql).toMatch(/DELETE FROM conversation_messages\s+USING parent/)
    expect(sql).toMatch(/conversation_messages\.created_at > parent\.created_at\s+AND NOT parent\.has_attachment/)
  })
})

describe('POST /api/chat/consult/regenerate — shared readiness gate', () => {
  it('refuses a chart that is not Ready before deleting anything, so the re-post cannot strand a truncated conversation', async () => {
    mockGetConversation.mockResolvedValue({ id: CONVERSATION_ID, chart_id: 'c', archived_at: null, archive_reason: null })
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
    mockGetConversation.mockResolvedValue({ id: CONVERSATION_ID, chart_id: 'c', archived_at: null, archive_reason: null })
    mockReadiness.mockResolvedValue(gate)
    const res = await POST(req())
    expect(res.status).toBe(409)
    expect((await res.json()).error.retry).toBe(retry)
  })
})


describe('POST /api/chat/consult/regenerate — stored attachment containment', () => {
  it('refuses a stored attachment through the 308 even when the stale client omits all attachment metadata', async () => {
    mockQuery.mockReset().mockResolvedValueOnce({ rows: [{ role: 'guest' }] })
      .mockResolvedValueOnce({ rows: [{ has_attachment: true, created_at: '2026-01-01T00:00:00Z' }] })
      .mockResolvedValue({ rows: [] })

    const stale = req(undefined, '/api/chat/consume/regenerate?fixture=1')
    const moved = await redirect(stale)
    expect(moved.status).toBe(308)
    const location = moved.headers.get('Location')
    expect(location).toBe('https://fixture.invalid/api/chat/consult/regenerate?fixture=1')
    const response = await POST(new Request(location!, { method: stale.method, body: await stale.text() }))
    expect(response.status).toBe(503)
    expect(response.headers.get('Cache-Control')).toBe('private, no-store')
    expect(await response.json()).toMatchObject({ error: { code: 'ATTACHMENT_UNAVAILABLE', retry: false } })
    expect(mockQuery).toHaveBeenCalledTimes(2)
    const [sql, params] = mockQuery.mock.calls[1]
    expect(params).toEqual(parentBinding)
    expect(sql).toMatch(/IN \('file', 'image', 'audio'\)/)
    expect(sql).toMatch(/SELECT has_attachment FROM parent/)
  })

  it('requires a session before malformed input or database work', async () => {
    mockGetServerUser.mockResolvedValue(null)
    expect((await POST(req(null))).status).toBe(401)
    expect(mockGetConversation).not.toHaveBeenCalled()
    expect(mockQuery).not.toHaveBeenCalled()
  })

  it('preserves owner scope and does not read a parent for a wrong actor', async () => {
    mockGetServerUser.mockResolvedValue({ uid: 'other-uid' })
    mockGetConversation.mockResolvedValue(null)
    const response = await POST(req())
    expect(response.status).toBe(404)
    expect(mockGetConversation).toHaveBeenCalledWith({ id: CONVERSATION_ID, userId: 'other-uid', isSuperAdmin: false })
    expect(mockQuery).toHaveBeenCalledTimes(1)
  })

  it.each([null, {}, { conversation_id: CONVERSATION_ID }, { conversation_id: CONVERSATION_ID, parent_message_id: 'bad' }])(
    'fails malformed parent input without database work (%o)', async body => {
      expect((await POST(req(body))).status).toBe(400)
      expect(mockGetConversation).not.toHaveBeenCalled()
      expect(mockQuery).not.toHaveBeenCalled()
    },
  )

  it('returns a single generic missing-parent outcome for unknown or foreign IDs', async () => {
    mockQuery.mockReset().mockResolvedValueOnce({ rows: [{ role: 'super_admin' }] })
      .mockResolvedValueOnce({ rows: [] })
    const response = await POST(req())
    expect(response.status).toBe(404)
    expect(mockGetConversation).toHaveBeenCalledWith({ id: CONVERSATION_ID, userId: 'owner-uid', isSuperAdmin: true })
    expect(mockQuery).toHaveBeenCalledTimes(2)
    expect(mockQuery.mock.calls[1][1]).toEqual(parentBinding)
    expect(await response.json()).toMatchObject({ error: { code: 'DATA_NOT_FOUND' } })
  })
})
