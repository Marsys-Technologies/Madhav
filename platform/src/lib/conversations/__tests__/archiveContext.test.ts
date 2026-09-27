/**
 * Conversation archive context (Jātaka chart workspace, Task 4 / migration 1120).
 *
 * `ConversationSummary` carries archive_reason / archived_chart_snapshot /
 * archived_by_run_id from both read paths, and `isCorrectionArchived` is the
 * single predicate every turn-writing or mutating door uses. Manual archives
 * (reason NULL) keep their existing semantics.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

const { mockQuery } = vi.hoisted(() => ({ mockQuery: vi.fn() }))
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))
vi.mock('server-only', () => ({}))

import { getConversation, isCorrectionArchived, listConversations } from '@/lib/conversations'
import type { ChartInputSnapshot } from '@/lib/charts/types'

const SNAPSHOT: ChartInputSnapshot = {
  name: 'Before Name',
  preferred_name: null,
  subject_name: null,
  birth_date: '1984-02-05',
  birth_time: '10:43:00',
  birth_place: 'Bhubaneswar',
  birth_lat: 20.2961,
  birth_lng: 85.8245,
  timezone_id: 'Asia/Kolkata',
  effective_tz_offset_minutes: 330,
  ayanamshas: ['lahiri'],
  captured_at: '2026-09-27T10:00:00Z',
}

const ROW = {
  id: 'conv-1',
  chart_id: 'c-1',
  user_id: 'u-1',
  module: 'consume',
  title: 'Reading',
  created_at: '2026-09-01T00:00:00Z',
  updated_at: null,
  archived_at: '2026-09-27T10:00:00Z',
  archive_reason: 'chart_details_changed',
  archived_chart_snapshot: SNAPSHOT,
  archived_by_run_id: 'run-1',
}

beforeEach(() => {
  mockQuery.mockReset()
  mockQuery.mockResolvedValue({ rows: [] })
})

describe('isCorrectionArchived', () => {
  it('is true only for an archived row whose reason is chart_details_changed', () => {
    expect(isCorrectionArchived({ archived_at: '2026-09-27T00:00:00Z', archive_reason: 'chart_details_changed' })).toBe(true)
  })

  it('keeps manual archives (reason NULL) outside the correction lock', () => {
    expect(isCorrectionArchived({ archived_at: '2026-09-27T00:00:00Z', archive_reason: null })).toBe(false)
  })

  it('is false for an active conversation', () => {
    expect(isCorrectionArchived({ archived_at: null, archive_reason: null })).toBe(false)
  })

  it('fails closed on a correction reason even if archived_at were somehow cleared', () => {
    expect(isCorrectionArchived({ archived_at: null, archive_reason: 'chart_details_changed' })).toBe(true)
  })
})

describe('conversation projections carry archive context', () => {
  it('getConversation selects and returns all three archive fields', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [ROW] })
    const c = await getConversation({ id: 'conv-1', userId: 'u-1', isSuperAdmin: false })
    const [sql] = mockQuery.mock.calls[0]
    expect(sql).toMatch(/archive_reason/)
    expect(sql).toMatch(/archived_chart_snapshot/)
    expect(sql).toMatch(/archived_by_run_id/)
    expect(c).toMatchObject({
      archive_reason: 'chart_details_changed',
      archived_chart_snapshot: SNAPSHOT,
      archived_by_run_id: 'run-1',
    })
  })

  it('getConversation normalises absent archive fields to null', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ ...ROW, archived_at: null, archive_reason: undefined, archived_chart_snapshot: undefined, archived_by_run_id: undefined }] })
    const c = await getConversation({ id: 'conv-1', userId: 'u-1', isSuperAdmin: false })
    expect(c).toMatchObject({ archive_reason: null, archived_chart_snapshot: null, archived_by_run_id: null })
  })

  it('listConversations selects and returns all three archive fields', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [{ ...ROW, first_message_snippet: null }] })
    const [c] = await listConversations({ chartId: 'c-1', userId: 'u-1', module: 'consume', includeArchived: true })
    const [sql] = mockQuery.mock.calls[0]
    expect(sql).toMatch(/c\.archive_reason/)
    expect(sql).toMatch(/c\.archived_chart_snapshot/)
    expect(sql).toMatch(/c\.archived_by_run_id/)
    expect(c).toMatchObject({ archive_reason: 'chart_details_changed', archived_by_run_id: 'run-1' })
  })
})
