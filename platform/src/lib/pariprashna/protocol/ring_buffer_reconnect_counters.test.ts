/**
 * lane P2-E (PPR-33/GAP-14) — the reconnect/snapshot-fallback counters added
 * to `getBufferedEventsSince`. Exercises the REAL function (not a stub) via
 * its in-memory fallback (REDIS_HOST unset in test env), so a resume-attempt
 * count that didn't actually increment would fail this test.
 */
import { describe, it, expect, beforeEach } from 'vitest'

import {
  openTurnBuffer,
  appendBufferedEvent,
  getBufferedEventsSince,
  getReconnectCounters,
  RING_BUFFER_MAX_EVENTS,
  __resetReconnectCountersForTests,
  __resetRingBufferForTests,
} from './ring_buffer'
import type { PariprashnaEvent } from './events'

describe('ring_buffer reconnect counters', () => {
  beforeEach(async () => {
    __resetReconnectCountersForTests()
    await __resetRingBufferForTests()
  })

  it('counts every getBufferedEventsSince call as a resume attempt', async () => {
    await openTurnBuffer({ turnId: 't1', chartId: 'c1', conversationId: 'conv1' })
    await getBufferedEventsSince('t1', 0)
    await getBufferedEventsSince('t1', 0)
    await getBufferedEventsSince('t1', 0)
    expect(getReconnectCounters().resumeAttempts).toBe(3)
  })

  it('counts a never-opened turn as unknownTurn, not evicted', async () => {
    const result = await getBufferedEventsSince('never-opened', 0)
    expect(result).toBeNull()
    const counters = getReconnectCounters()
    expect(counters.unknownTurn).toBe(1)
    expect(counters.evictedFallbacks).toBe(0)
  })

  it('does not count a real, non-evicted resume as a fallback', async () => {
    await openTurnBuffer({ turnId: 't2', chartId: 'c1', conversationId: 'conv1' })
    const first = await getBufferedEventsSince('t2', -1)
    expect(first?.evicted).toBe(false)
    expect(getReconnectCounters().evictedFallbacks).toBe(0)
  })

  it('counts a genuine ring-trim eviction as an evicted fallback', async () => {
    await openTurnBuffer({ turnId: 't3', chartId: 'c1', conversationId: 'conv1' })
    // Push past RING_BUFFER_MAX_EVENTS so the oldest events actually trim out
    // of the ring — a REAL eviction, not a simulated flag.
    for (let seq = 0; seq < RING_BUFFER_MAX_EVENTS + 5; seq++) {
      const event: PariprashnaEvent = { type: 'flag', seq, t: seq, code: 'probe', level: 'info' }
      await appendBufferedEvent('t3', event)
    }
    const result = await getBufferedEventsSince('t3', 0) // seq 0 has been trimmed out
    expect(result?.evicted).toBe(true)
    expect(getReconnectCounters().evictedFallbacks).toBe(1)
  })

  it('getReconnectCounters returns a snapshot copy, not a live reference', () => {
    const a = getReconnectCounters()
    a.resumeAttempts = 999
    expect(getReconnectCounters().resumeAttempts).not.toBe(999)
  })
})
