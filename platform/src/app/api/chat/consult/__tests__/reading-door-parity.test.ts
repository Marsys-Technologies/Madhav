/**
 * Reading-door readiness policy (Jātaka chart workspace).
 *
 * Legacy consult remains readiness-gated. Paripraśna is intentionally adaptive:
 * its planner selects the relevant subset from whatever chart material exists,
 * so incomplete chart readiness does not prevent a reading. The entry surface
 * carries the separate completeness notice.
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
    return { refused: true, code: body.error.code as string, message: body.error.message as string, retry: body.error.retry as boolean }
  }
  return { refused: false }
}

async function pariprashnaOutcome() {
  const errors: Array<{ code: string; message: string; retryable: boolean }> = []
  const em = { error: (e: { code: string; message: string; retryable: boolean }) => errors.push(e) }
  await authorizeTurn({
    em: em as never,
    user: { uid: 'owner-uid' },
    identity: { chartId: CHART, conversationId: '6b0f4c2e-1111-4222-8333-4444555566cc', isFirstTurn: true } as never,
  })
  const refusal = errors.find((e) => e.code === 'CHART_RECOMPUTE_REQUIRED')
  return refusal
    ? { refused: true, code: refusal.code, message: refusal.message, retry: refusal.retryable }
    : { refused: false }
}

beforeEach(() => {
  vi.clearAllMocks()
  mockPlanner.mockRejectedValue(new Error('stop after gate'))
})

describe('legacy consult and adaptive Paripraśna readiness policy', () => {
  it.each([
    ['building', true, true],
    ['needs-rebuild', true, false],
    ['failed', true, false],
    ['partially-built', true, false],
    ['not-built', true, false],
    ['ready', false, undefined],
  ])('a %s chart: legacy refused=%s with retry=%s while Paripraśna remains available', async (state, refused, retry) => {
    readiness.value = { state, refreshWarning: null }
    const [consult, pariprashna] = [await consultOutcome(), await pariprashnaOutcome()]
    expect(consult.refused).toBe(refused)
    expect(pariprashna.refused).toBe(false)
    if (refused) {
      expect(consult.code).toBe('CHART_RECOMPUTE_REQUIRED')
      expect(consult.message).toBe(readinessRefusalMessage(state))
      expect(consult.retry).toBe(retry)
    }
  })

  it('a Ready chart whose latest small refresh failed without harm still admits readings at both doors', async () => {
    readiness.value = { state: 'ready', refreshWarning: 'The latest refresh did not finish; the previously computed chart remains in use.' }
    expect((await consultOutcome()).refused).toBe(false)
    expect((await pariprashnaOutcome()).refused).toBe(false)
  })

  it('unreadable readiness fails closed for legacy consult but does not block Paripraśna', async () => {
    readiness.value = 'throw'
    const [consult, pariprashna] = [await consultOutcome(), await pariprashnaOutcome()]
    expect(consult.refused).toBe(true)
    expect(pariprashna.refused).toBe(false)
    expect(consult.message).toBe(readinessRefusalMessage('unavailable'))
    expect(consult.retry).toBe(true)
  })
})
