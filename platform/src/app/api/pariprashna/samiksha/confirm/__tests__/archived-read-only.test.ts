/**
 * Samīkṣā confirm/dismiss — correction-history is read-only (Jātaka Phase-A
 * hardening, item 1). The referenced conversation is loaded and authorized
 * before any write, must belong to the supplied chart (non-enumerating 404
 * otherwise), and a correction-archived conversation refuses both confirm and
 * dismiss with 409 CONVERSATION_ARCHIVED_READ_ONLY before any stamp read,
 * lifecycle transition or ledger write. Manual archives keep existing semantics.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { NextRequest } from 'next/server'

vi.mock('server-only', () => ({}))

const CHART = '482012f1-0000-4000-8000-0000000000aa'
const OTHER_CHART = '482012f1-0000-4000-8000-0000000000bb'
const CONV = '6b0f4c2e-1111-4222-8333-4444555566aa'

const { mockQuery, mockGetConversation, mockConfirm, mockDismiss, mockAuthorize } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetConversation: vi.fn(),
  mockConfirm: vi.fn(),
  mockDismiss: vi.fn(),
  mockAuthorize: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'owner-uid' })) }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: mockAuthorize }))
vi.mock('@/lib/conversations', () => ({ getConversation: mockGetConversation }))
vi.mock('@/lib/pariprashna/samiksha/confirm', () => ({ confirmCandidate: mockConfirm, dismissCandidate: mockDismiss }))

import { POST } from '../route'

const CANDIDATE = {
  claim_text: 'A career change in 2027', domain: 'career', window_start: '2027-01-01', window_end: '2027-12-31',
  direction: 'positive', technique_refs: [], grounding_fact_ids: [], score: 0.8, horizon_text: null,
}

function req(action: 'confirm' | 'dismiss', chartId = CHART) {
  const body =
    action === 'confirm'
      ? { action, chartId, conversationId: CONV, candidate: CANDIDATE, confidence: { low: 0.4, high: 0.6 } }
      : { action, chartId, conversationId: CONV, candidate: CANDIDATE, reason: 'not relevant' }
  return new NextRequest('http://localhost/api/pariprashna/samiksha/confirm', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
}

const conversation = (archive_reason: string | null, chart_id = CHART) => ({
  id: CONV, chart_id, user_id: 'owner-uid', module: 'consume',
  archived_at: archive_reason || chart_id !== CHART ? '2026-09-27T10:00:00Z' : null,
  archive_reason, archived_chart_snapshot: null, archived_by_run_id: null,
})

const writes = () => mockQuery.mock.calls.filter(([sql]) => /^\s*(INSERT|UPDATE|DELETE)/i.test(sql))

beforeEach(() => {
  vi.clearAllMocks()
  mockQuery.mockImplementation(async (sql: string) => (/FROM profiles/.test(sql) ? { rows: [{ role: 'guest' }] } : { rows: [] }))
  mockAuthorize.mockResolvedValue('all')
  mockConfirm.mockResolvedValue({ id: 'ledger-1' })
  mockDismiss.mockResolvedValue({ id: 'ledger-2' })
})

describe('POST /api/pariprashna/samiksha/confirm — correction-history lock', () => {
  it.each(['confirm', 'dismiss'] as const)('refuses %s on a correction-archived conversation with the canonical 409', async (action) => {
    mockGetConversation.mockResolvedValue(conversation('chart_details_changed'))
    const res = await POST(req(action))
    expect(res.status).toBe(409)
    expect(await res.json()).toEqual({
      error: { code: 'CONVERSATION_ARCHIVED_READ_ONLY', message: 'This conversation is historical and read-only.', retry: false },
    })
    // No stamp read, lifecycle transition or ledger write happens after the lock.
    expect(mockConfirm).not.toHaveBeenCalled()
    expect(mockDismiss).not.toHaveBeenCalled()
    expect(writes()).toHaveLength(0)
  })

  it('loads the conversation with the caller identity before any write', async () => {
    mockGetConversation.mockResolvedValue(conversation(null))
    await POST(req('confirm'))
    expect(mockGetConversation).toHaveBeenCalledWith({ id: CONV, userId: 'owner-uid', isSuperAdmin: false })
    expect(mockGetConversation.mock.invocationCallOrder[0]).toBeLessThan(mockConfirm.mock.invocationCallOrder[0])
  })

  it.each([
    ['a missing or inaccessible conversation', null],
    ['a conversation from another chart', conversation(null, OTHER_CHART)],
  ])('answers %s with the same non-enumerating 404 and no write', async (_label, conv) => {
    mockGetConversation.mockResolvedValue(conv)
    const res = await POST(req('confirm'))
    expect(res.status).toBe(404)
    expect((await res.json()).error.code).toBe('DATA_NOT_FOUND')
    expect(mockConfirm).not.toHaveBeenCalled()
    expect(writes()).toHaveLength(0)
  })

  it('never consults the conversation when chart access is denied', async () => {
    mockAuthorize.mockResolvedValue('deny')
    const res = await POST(req('confirm'))
    expect(res.status).toBe(403)
    expect(mockGetConversation).not.toHaveBeenCalled()
  })

  it.each(['confirm', 'dismiss'] as const)('keeps %s working for an active conversation', async (action) => {
    mockGetConversation.mockResolvedValue(conversation(null))
    const res = await POST(req(action))
    expect(res.status).toBe(200)
    expect(action === 'confirm' ? mockConfirm : mockDismiss).toHaveBeenCalled()
  })

  it('keeps existing semantics for a manually archived conversation', async () => {
    mockGetConversation.mockResolvedValue({ ...conversation(null), archived_at: '2026-09-01T00:00:00Z' })
    const res = await POST(req('confirm'))
    expect(res.status).toBe(200)
    expect(mockConfirm).toHaveBeenCalled()
  })
})
