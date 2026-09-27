/**
 * Super-admin chat/build door — chart integrity (Jātaka Phase-A2 item 3 continued).
 *
 * Super-admin authority authenticates and authorizes the caller; it must not
 * bypass chart integrity. This door refuses a correction-archived conversation
 * and a chart that is not Ready, before any model call or persistence, exactly
 * like the other three reading doors.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockQuery, mockGetConversation, mockInsert, mockStreamText, mockReadiness } = vi.hoisted(() => ({
  mockQuery: vi.fn(),
  mockGetConversation: vi.fn(),
  mockInsert: vi.fn(async () => undefined),
  mockStreamText: vi.fn(),
  mockReadiness: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'admin-uid' })) }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/conversations', () => ({
  getConversation: mockGetConversation,
  insertConversationWithId: mockInsert,
}))
vi.mock('@/lib/charts/readingGate', () => ({ checkReadingReadiness: mockReadiness }))
vi.mock('ai', async (importOriginal) => ({
  ...(await importOriginal<typeof import('ai')>()),
  streamText: mockStreamText,
}))
vi.mock('@ai-sdk/anthropic', () => ({ anthropic: vi.fn(() => 'fake-model') }))
vi.mock('@/lib/claude/build-tools', () => ({ buildTools: {} }))
vi.mock('@/lib/claude/system-prompts', () => ({ buildSystemPrompt: vi.fn(() => 'sys') }))

import { POST } from '../route'

const CHART = 'c1'
const CONV = '6b0f4c2e-1111-4222-8333-4444555566cc'

function req(body: object) {
  return new Request('http://localhost/api/chat/build', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
}

function conversation(archive_reason: string | null, chart_id = CHART) {
  return { id: CONV, chart_id, user_id: 'admin-uid', archived_at: archive_reason ? '2026-09-27T10:00:00Z' : null, archive_reason }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockQuery.mockImplementation(async (sql: string) => {
    if (/FROM profiles/.test(sql)) return { rows: [{ role: 'super_admin' }] }
    if (/FROM charts/.test(sql)) return { rows: [{ id: CHART, name: 'N', birth_date: '1984-02-05', birth_time: '10:43', birth_place: 'P' }] }
    if (/FROM pyramid_layers/.test(sql)) return { rows: [] }
    return { rows: [] }
  })
  mockReadiness.mockResolvedValue({ ok: true })
  mockStreamText.mockReturnValue({
    consumeStream: vi.fn(),
    toUIMessageStreamResponse: vi.fn(() => new Response('stream', { status: 200 })),
  })
})

describe('POST /api/chat/build — correction-history lock', () => {
  it('refuses a correction-archived conversation with the canonical 409, before any model call', async () => {
    mockGetConversation.mockResolvedValue(conversation('chart_details_changed'))
    const res = await POST(req({ chartId: CHART, conversationId: CONV, messages: [] }))
    expect(res.status).toBe(409)
    const body = await res.json()
    expect(body.error.code).toBe('CONVERSATION_ARCHIVED_READ_ONLY')
    expect(mockStreamText).not.toHaveBeenCalled()
  })

  it('keeps working for an active conversation', async () => {
    mockGetConversation.mockResolvedValue(conversation(null))
    const res = await POST(req({ chartId: CHART, conversationId: CONV, messages: [] }))
    expect(res.status).toBe(200)
    expect(mockStreamText).toHaveBeenCalled()
  })
})

describe('POST /api/chat/build — shared readiness gate', () => {
  it.each([
    ['building', true],
    ['needs-rebuild', false],
    ['failed', false],
  ])('refuses a %s chart before any model call (retry=%s)', async (state, retry) => {
    mockGetConversation.mockResolvedValue(conversation(null))
    mockReadiness.mockResolvedValue({
      ok: false,
      code: 'CHART_RECOMPUTE_REQUIRED',
      state,
      message: `msg for ${state}`,
      retryable: retry,
    })
    const res = await POST(req({ chartId: CHART, conversationId: CONV, messages: [] }))
    expect(res.status).toBe(409)
    const body = await res.json()
    expect(body.error.code).toBe('CHART_RECOMPUTE_REQUIRED')
    expect(body.error.retry).toBe(retry)
    expect(mockStreamText).not.toHaveBeenCalled()
  })

  it('checks readiness even on a brand-new conversation (first turn)', async () => {
    mockReadiness.mockResolvedValue({ ok: false, code: 'CHART_RECOMPUTE_REQUIRED', state: 'failed', message: 'm', retryable: false })
    const res = await POST(req({ chartId: CHART, messages: [] }))
    expect(res.status).toBe(409)
    expect(mockInsert).not.toHaveBeenCalled()
    expect(mockStreamText).not.toHaveBeenCalled()
  })

  it('admits a Ready chart on a first turn', async () => {
    mockReadiness.mockResolvedValue({ ok: true })
    const res = await POST(req({ chartId: CHART, messages: [] }))
    expect(res.status).toBe(200)
    expect(mockStreamText).toHaveBeenCalled()
  })
})
