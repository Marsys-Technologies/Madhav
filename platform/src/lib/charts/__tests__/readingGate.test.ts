/**
 * The shared reading gate's retry contract (Jātaka Phase-A2). `retryable` is
 * true only for a genuinely transient refusal — an actively progressing build,
 * or a readiness lookup that failed — and false for every state that needs an
 * explicit rebuild, operator or user action.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))

const { readiness } = vi.hoisted(() => ({ readiness: { value: 'ready' as string | 'throw' } }))
vi.mock('@/lib/charts/readiness', () => ({
  getChartReadinessMap: vi.fn(async (ids: string[]) => {
    if (readiness.value === 'throw') throw new Error('db down')
    return new Map(ids.map((id) => [id, { state: readiness.value }]))
  }),
  isDerivedChartReady: (r: { state: string }) => r.state === 'ready',
}))

import { checkReadingReadiness } from '../readingGate'
import { readinessRefusalMessage } from '../readinessCopy'

beforeEach(() => {
  readiness.value = 'ready'
})

describe('checkReadingReadiness', () => {
  it('admits a Ready chart', async () => {
    expect(await checkReadingReadiness('c1')).toEqual({ ok: true })
  })

  it.each([
    ['building', true],
    ['needs-rebuild', false],
    ['failed', false],
    ['partially-built', false],
    ['not-built', false],
  ])('refuses %s with retryable=%s', async (state, retryable) => {
    readiness.value = state
    expect(await checkReadingReadiness('c1')).toEqual({
      ok: false,
      code: 'CHART_RECOMPUTE_REQUIRED',
      state,
      message: readinessRefusalMessage(state),
      retryable,
    })
  })

  it('refuses an unreadable readiness as transient (retryable)', async () => {
    readiness.value = 'throw'
    const result = await checkReadingReadiness('c1')
    expect(result).toMatchObject({ ok: false, state: 'unavailable', retryable: true })
  })
})
