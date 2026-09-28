/**
 * Legacy consult door — correction-archived history is read-only
 * (Jātaka chart workspace, Task 8). A new turn on a conversation archived by a
 * chart-details correction is refused before any planning, model call,
 * persistence or insert; manual archives keep their existing behaviour.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const CHART = '482012f1-0000-4000-8000-00000000000c'
const CONV = '6b0f4c2e-1111-4222-8333-444455556666'

const { mockGetConversation, mockInsert, mockPlanner } = vi.hoisted(() => ({
  mockGetConversation: vi.fn(),
  mockInsert: vi.fn(),
  mockPlanner: vi.fn(),
}))

vi.mock('@/lib/firebase/server', () => ({ getServerUser: vi.fn(async () => ({ uid: 'owner-uid' })) }))
vi.mock('@/lib/db/client', () => ({
  query: vi.fn(async (sql: string, params?: unknown[]) => {
    if (/from charts/i.test(sql)) return { rows: [{ id: params?.[0], name: 'N', birth_date: '1984-02-05', birth_time: '10:43', birth_place: 'P', client_id: 'owner-uid' }] }
    if (/from profiles/i.test(sql)) return { rows: [{ role: 'guest' }] }
    return { rows: [] }
  }),
  getPool: vi.fn(),
}))
vi.mock('@/lib/auth/authorizeChartAccess', () => ({ authorizeChartAccess: vi.fn(async () => 'all') }))
vi.mock('@/lib/conversations', () => ({
  getConversation: mockGetConversation,
  insertConversationWithId: mockInsert,
  updateConversationTitle: vi.fn(),
}))
// These cases exercise the archive lock on a Ready chart.
vi.mock('@/lib/charts/readiness', () => ({
  getChartReadinessMap: vi.fn(async (ids: string[]) => new Map(ids.map((id) => [id, { state: 'ready' }]))),
  isDerivedChartReady: (r: { state: string }) => r.state === 'ready',
}))
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: mockPlanner,
}))

import { POST } from '../route'

function req() {
  return new Request('http://localhost/api/chat/consult', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ chartId: CHART, conversationId: CONV, messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text: 'More?' }] }] }),
  })
}

const conversation = (archive_reason: string | null) => ({
  id: CONV,
  chart_id: CHART,
  user_id: 'owner-uid',
  module: 'consume',
  archived_at: '2026-09-27T10:00:00Z',
  archive_reason,
  archived_chart_snapshot: archive_reason ? { birth_date: '1984-02-05', birth_time: '10:43:00' } : null,
  archived_by_run_id: null,
})

beforeEach(() => vi.clearAllMocks())

describe('POST /api/chat/consult — correction-archived conversation', () => {
  it('refuses the turn with 409 CONVERSATION_ARCHIVED_READ_ONLY and does no work', async () => {
    mockGetConversation.mockResolvedValue(conversation('chart_details_changed'))
    const res = await POST(req())
    expect(res.status).toBe(409)
    expect((await res.json()).error.code).toBe('CONVERSATION_ARCHIVED_READ_ONLY')
    expect(mockPlanner).not.toHaveBeenCalled()
    expect(mockInsert).not.toHaveBeenCalled()
  })

  it('does not apply the correction lock to a manual archive', async () => {
    mockGetConversation.mockResolvedValue(conversation(null))
    mockPlanner.mockRejectedValue(new Error('stop after gate'))
    const res = await POST(req()).catch(() => null)
    expect(res?.status).not.toBe(409)
  })
})
