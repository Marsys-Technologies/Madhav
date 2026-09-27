/**
 * Legacy consult door — no new reading while a chart is being recomputed or
 * needs rebuilding (Jātaka chart workspace, review fix). With the Paripraśna
 * flag off, /clients/[id]/pariprashna redirects here, so this door must not
 * start readings on a chart whose corrected details are mid-recompute.
 * Other states keep the legacy behaviour.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const CHART = '482012f1-0000-4000-8000-00000000000d'

const { mockInsert, mockPlanner, readiness } = vi.hoisted(() => ({
  mockInsert: vi.fn(),
  mockPlanner: vi.fn(),
  readiness: { state: 'ready' as string, fail: false },
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
  getConversation: vi.fn(async () => null),
  insertConversationWithId: mockInsert,
  updateConversationTitle: vi.fn(),
}))
vi.mock('@/lib/charts/readiness', () => ({
  getChartReadinessMap: vi.fn(async (ids: string[]) => {
    if (readiness.fail) throw new Error('db down')
    return new Map(ids.map((id) => [id, { state: readiness.state }]))
  }),
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
    body: JSON.stringify({ chartId: CHART, messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text: 'Hello' }] }] }),
  })
}

beforeEach(() => {
  vi.clearAllMocks()
  readiness.state = 'ready'
  readiness.fail = false
  mockPlanner.mockRejectedValue(new Error('stop after gate'))
})

describe('POST /api/chat/consult — readiness gate', () => {
  it.each(['building', 'needs-rebuild'])('refuses a new reading while the chart is %s', async (state) => {
    readiness.state = state
    const res = await POST(req())
    expect(res.status).toBe(409)
    const body = await res.json()
    expect(body.error.code).toBe('CHART_RECOMPUTE_REQUIRED')
    expect(mockInsert).not.toHaveBeenCalled()
    expect(mockPlanner).not.toHaveBeenCalled()
  })

  it('fails closed when readiness cannot be read', async () => {
    readiness.fail = true
    const res = await POST(req())
    expect(res.status).toBe(409)
    expect(mockInsert).not.toHaveBeenCalled()
  })

  it.each(['ready', 'partially-built', 'not-built', 'failed'])('keeps the legacy behaviour for a %s chart', async (state) => {
    readiness.state = state
    const res = await POST(req()).catch(() => null)
    expect(res?.status).not.toBe(409)
    expect(mockInsert).toHaveBeenCalled()
  })
})
