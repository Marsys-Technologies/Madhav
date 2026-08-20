/**
 * lane P2-E — queries.ts. Each function is exercised against a scripted fake
 * `query()` so the assertion is on the REAL arithmetic (rates, coverage)
 * the function computes from rows, not on a mocked-out return value.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const queryMock = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: (...args: unknown[]) => queryMock(...args) }))

const getReconnectCountersMock = vi.fn()
vi.mock('../../protocol/ring_buffer', () => ({
  getReconnectCounters: () => getReconnectCountersMock(),
}))

import {
  getGateVerdictRates,
  getPredictionCaptureResolutionCoverage,
  getReconnectRates,
  getRegisterLintFiringRate,
} from '../queries'

describe('getGateVerdictRates', () => {
  beforeEach(() => queryMock.mockReset())

  it('computes rate = count / total across all returned actions', async () => {
    queryMock.mockResolvedValueOnce({
      rows: [
        { action: 'proceed', n: '90' },
        { action: 'reframe', n: '9' },
        { action: 'hard_stop', n: '1' },
      ],
    })
    const result = await getGateVerdictRates(14)
    expect(result.total).toBe(100)
    expect(result.rates).toEqual([
      { action: 'proceed', count: 90, rate: 0.9 },
      { action: 'reframe', count: 9, rate: 0.09 },
      { action: 'hard_stop', count: 1, rate: 0.01 },
    ])
  })

  it('reports total: 0 (not a division error) when the table is empty', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })
    const result = await getGateVerdictRates(14)
    expect(result.total).toBe(0)
    expect(result.rates).toEqual([])
  })
})

describe('getRegisterLintFiringRate', () => {
  beforeEach(() => queryMock.mockReset())

  it('computes firing_rate = fires / delta_calls', async () => {
    queryMock.mockResolvedValueOnce({
      rows: [{ turns: '5', delta_calls: '200', fires: '10', leaks_total: '14' }],
    })
    const result = await getRegisterLintFiringRate(14)
    expect(result.turns_measured).toBe(5)
    expect(result.firing_rate).toBeCloseTo(0.05)
    expect(result.leaks_total).toBe(14)
  })

  it('reports firing_rate: null (not 0) when nothing has been measured yet', async () => {
    queryMock.mockResolvedValueOnce({ rows: [{ turns: '0', delta_calls: null, fires: null, leaks_total: null }] })
    const result = await getRegisterLintFiringRate(14)
    expect(result.firing_rate).toBeNull()
  })
})

describe('getPredictionCaptureResolutionCoverage', () => {
  beforeEach(() => queryMock.mockReset())

  it('counts only outcome_recorded toward resolved_total, not every terminal state', async () => {
    queryMock.mockResolvedValueOnce({
      rows: [
        { lifecycle_status: 'outcome_recorded', n: '6' },
        { lifecycle_status: 'dismissed', n: '3' },
        { lifecycle_status: 'lapsed', n: '1' },
        { lifecycle_status: 'open', n: '2' },
      ],
    })
    const result = await getPredictionCaptureResolutionCoverage(14)
    expect(result.captured_total).toBe(12)
    expect(result.resolved_total).toBe(6)
    expect(result.resolution_coverage).toBeCloseTo(0.5)
    expect(result.by_lifecycle_status.dismissed).toBe(3)
  })

  it('reports resolution_coverage: null (not 0) when nothing was captured', async () => {
    queryMock.mockResolvedValueOnce({ rows: [] })
    const result = await getPredictionCaptureResolutionCoverage(14)
    expect(result.captured_total).toBe(0)
    expect(result.resolution_coverage).toBeNull()
  })
})

describe('getReconnectRates', () => {
  it('computes snapshot_fallback_rate from the ring_buffer counters', () => {
    getReconnectCountersMock.mockReturnValueOnce({ resumeAttempts: 40, evictedFallbacks: 4, unknownTurn: 1 })
    const result = getReconnectRates()
    expect(result.resume_attempts).toBe(40)
    expect(result.snapshot_fallback_rate).toBeCloseTo(0.1)
    expect(result.process_local).toBe(true)
  })

  it('reports snapshot_fallback_rate: null (not 0) with zero attempts observed', () => {
    getReconnectCountersMock.mockReturnValueOnce({ resumeAttempts: 0, evictedFallbacks: 0, unknownTurn: 0 })
    const result = getReconnectRates()
    expect(result.snapshot_fallback_rate).toBeNull()
  })
})
