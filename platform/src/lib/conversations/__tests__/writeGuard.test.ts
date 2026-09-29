/**
 * Persistence-boundary write guard (Jātaka Phase-A hardening, item 5). Re-checked
 * at the moment a reading is persisted — not only at admission — so a turn that
 * began before a chart correction cannot write after it.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const { mockQuery, mockGate } = vi.hoisted(() => ({ mockQuery: vi.fn(), mockGate: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('@/lib/charts/readingGate', () => ({ checkReadingReadiness: mockGate }))

import { checkConversationWritable } from '../writeGuard'

const ARGS = { conversationId: 'conv-1', chartId: 'c1' }

beforeEach(() => {
  mockQuery.mockReset()
  mockGate.mockReset()
  mockQuery.mockResolvedValue({ rows: [{ chart_id: 'c1', archive_reason: null }] })
  mockGate.mockResolvedValue({ ok: true })
})

describe('checkConversationWritable', () => {
  it('allows an active conversation on a Ready chart', async () => {
    expect(await checkConversationWritable(ARGS)).toEqual({ ok: true })
    const [sql, params] = mockQuery.mock.calls[0]
    expect(sql).toMatch(/archive_reason/)
    expect(params).toEqual(['conv-1'])
  })

  it('refuses a conversation archived by a chart correction', async () => {
    mockQuery.mockResolvedValue({ rows: [{ chart_id: 'c1', archive_reason: 'chart_details_changed' }] })
    expect(await checkConversationWritable(ARGS)).toMatchObject({ ok: false, code: 'CONVERSATION_ARCHIVED_READ_ONLY' })
  })

  it('refuses when the chart is no longer Ready', async () => {
    mockGate.mockResolvedValue({ ok: false, code: 'CHART_RECOMPUTE_REQUIRED', state: 'needs-rebuild', message: 'm' })
    expect(await checkConversationWritable(ARGS)).toMatchObject({ ok: false, code: 'CHART_RECOMPUTE_REQUIRED' })
  })

  it('allows Pariprashna to persist a turn while the chart is incomplete', async () => {
    mockGate.mockResolvedValue({ ok: false, code: 'CHART_RECOMPUTE_REQUIRED', state: 'partially-built', message: 'm' })

    expect(await checkConversationWritable({ ...ARGS, readinessPolicy: 'allow-incomplete' })).toEqual({ ok: true })
    expect(mockGate).not.toHaveBeenCalled()
  })

  it('refuses a conversation that belongs to another chart', async () => {
    mockQuery.mockResolvedValue({ rows: [{ chart_id: 'other', archive_reason: null }] })
    expect(await checkConversationWritable(ARGS)).toMatchObject({ ok: false, code: 'CONVERSATION_ARCHIVED_READ_ONLY' })
  })

  it('fails closed when the conversation cannot be read', async () => {
    mockQuery.mockRejectedValue(new Error('db down'))
    expect(await checkConversationWritable(ARGS)).toMatchObject({ ok: false })
  })
})
