/**
 * Reading-door parity (Jātaka Phase-A hardening, item 3).
 *
 * Legacy consult and Paripraśna admit or refuse a new reading from the same
 * shared readiness computation, with the same CHART_RECOMPUTE_REQUIRED code and
 * the same message. Only Ready — including Ready with a non-blocking refresh
 * warning — produces a reading; Building, Needs rebuild, Failed (a failed
 * correction or full rebuild), Partially built, Not built, or an unreadable
 * readiness never do.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const CHART = '482012f1-0000-4000-8000-0000000000cc'

const { readiness, mockInsert, mockPlanner } = vi.hoisted(() => ({
  readiness: { value: { state: 'ready', refreshWarning: null as string | null } as { state: string; refreshWarning: string | null } | 'throw' },
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
  getConversation: vi.fn(async () => null),
  insertConversationWithId: mockInsert,
  updateConversationTitle: vi.fn(),
}))
vi.mock('@/lib/charts/readiness', () => ({
  getChartReadinessMap: vi.fn(async (ids: string[]) => {
    if (readiness.value === 'throw') throw new Error('db down')
    return new Map(ids.map((id) => [id, readiness.value]))
  }),
  isDerivedChartReady: (r: { state: string }) => r.state === 'ready',
}))
vi.mock('@/lib/pipeline/pipeline_planner', () => ({
  PlannerFault: class PlannerFault extends Error {},
  callPipelinePlanner: mockPlanner,
}))

import { POST as consultPost } from '../route'
import { authorizeTurn } from '@/lib/pariprashna/pipeline/safety_gate'
import { readinessRefusalMessage } from '@/lib/charts/readinessCopy'

async function consultOutcome() {
  const res = await consultPost(
    new Request('http://localhost/api/chat/consult', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chartId: CHART, messages: [{ id: 'm1', role: 'user', parts: [{ type: 'text', text: 'Hello' }] }] }),
    }),
  ).catch(() => null)
  if (res?.status === 409) {
    const body = await res.json()
    return { refused: true, code: body.error.code as string, message: body.error.message as string }
  }
  return { refused: false }
}

async function pariprashnaOutcome() {
  const errors: Array<{ code: string; message: string }> = []
  const em = { error: (e: { code: string; message: string }) => errors.push(e) }
  await authorizeTurn({
    em: em as never,
    user: { uid: 'owner-uid' },
    identity: { chartId: CHART, conversationId: '6b0f4c2e-1111-4222-8333-4444555566cc', isFirstTurn: true } as never,
  })
  const refusal = errors.find((e) => e.code === 'CHART_RECOMPUTE_REQUIRED')
  return refusal ? { refused: true, code: refusal.code, message: refusal.message } : { refused: false }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockPlanner.mockRejectedValue(new Error('stop after gate'))
})

describe('legacy consult ↔ Paripraśna readiness parity', () => {
  it.each([
    ['building', true],
    ['needs-rebuild', true],
    ['failed', true],
    ['partially-built', true],
    ['not-built', true],
    ['ready', false],
  ])('a %s chart: refused=%s at both doors, with the same code and message', async (state, refused) => {
    readiness.value = { state, refreshWarning: null }
    const [consult, pariprashna] = [await consultOutcome(), await pariprashnaOutcome()]
    expect(consult.refused).toBe(refused)
    expect(pariprashna).toEqual(consult)
    if (refused) {
      expect(consult.code).toBe('CHART_RECOMPUTE_REQUIRED')
      expect(consult.message).toBe(readinessRefusalMessage(state))
    }
  })

  it('a Ready chart whose latest small refresh failed without harm still admits readings at both doors', async () => {
    readiness.value = { state: 'ready', refreshWarning: 'The latest refresh did not finish; the previously computed chart remains in use.' }
    expect((await consultOutcome()).refused).toBe(false)
    expect((await pariprashnaOutcome()).refused).toBe(false)
  })

  it('unreadable readiness fails closed at both doors, identically', async () => {
    readiness.value = 'throw'
    const [consult, pariprashna] = [await consultOutcome(), await pariprashnaOutcome()]
    expect(consult.refused).toBe(true)
    expect(pariprashna).toEqual(consult)
    expect(consult.message).toBe(readinessRefusalMessage('unavailable'))
  })
})
