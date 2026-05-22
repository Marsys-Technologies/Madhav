/**
 * C-S2: smooth-stream-rate-target.test.ts
 *
 * Tests for the R11.C rate-target layer on top of Y-S3 word-aware flush.
 * Verifies:
 *   - TARGET_CPS constant is 40
 *   - computeFlushDelay() returns 0 below target
 *   - computeFlushDelay() throttles correctly above target
 *   - Delay is capped at MAX_WORD_BUFFER_MS (80ms)
 *   - Y-S3 word-boundary + 80ms MAX is preserved
 *   - isRateTargetEnabled() reflects flag state
 *   - No NEXT_PUBLIC prefix (server-side gate)
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  TARGET_CPS,
  MAX_WORD_BUFFER_MS,
  RATE_WINDOW_MS,
  createRateTargetState,
  computeFlushDelay,
  recordFlush,
  isRateTargetEnabled,
  getSmoothStreamTransform,
} from '../../src/lib/streaming/smooth_stream'

// ---------------------------------------------------------------------------
// Mock server-only + flag system
// ---------------------------------------------------------------------------
vi.mock('server-only', () => ({}))

vi.mock('../../src/lib/config/index', () => ({
  getFlag: vi.fn((flag: string) => {
    if (flag === 'R10_SMOOTH_STREAM_V2') return true
    if (flag === 'R11C_SMOOTH_STREAM_V3') return true
    return false
  }),
}))

vi.mock('ai', () => ({
  smoothStream: vi.fn(() => ({ _tag: 'smoothStreamTransform' })),
}))

import { getFlag } from '../../src/lib/config/index'

const mockGetFlag = vi.mocked(getFlag)

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

describe('C-S2: constants', () => {
  it('TARGET_CPS is 40', () => {
    expect(TARGET_CPS).toBe(40)
  })

  it('MAX_WORD_BUFFER_MS is 80 (Y-S3 preserved)', () => {
    expect(MAX_WORD_BUFFER_MS).toBe(80)
  })

  it('RATE_WINDOW_MS is 1000', () => {
    expect(RATE_WINDOW_MS).toBe(1000)
  })
})

// ---------------------------------------------------------------------------
// createRateTargetState
// ---------------------------------------------------------------------------

describe('C-S2: createRateTargetState()', () => {
  it('returns empty state', () => {
    const state = createRateTargetState()
    expect(state.flushTimestamps).toEqual([])
    expect(state.flushChars).toEqual([])
    expect(state.windowChars).toBe(0)
  })
})

// ---------------------------------------------------------------------------
// computeFlushDelay: no delay when history is insufficient
// ---------------------------------------------------------------------------

describe('C-S2: computeFlushDelay() — no history', () => {
  it('returns 0 with empty state (no history)', () => {
    const state = createRateTargetState()
    expect(computeFlushDelay(state, 20, Date.now())).toBe(0)
  })

  it('returns 0 when windowDuration < 50ms (not enough history)', () => {
    const state = createRateTargetState()
    const t0 = 1000
    recordFlush(state, 10, t0)
    // Only 30ms later — below the 50ms threshold
    expect(computeFlushDelay(state, 10, t0 + 30)).toBe(0)
  })
})

// ---------------------------------------------------------------------------
// computeFlushDelay: no delay when below target CPS
// ---------------------------------------------------------------------------

describe('C-S2: computeFlushDelay() — below target (flush immediately)', () => {
  it('returns 0 when current rate is well below TARGET_CPS', () => {
    const state = createRateTargetState()
    const t0 = 1000
    // 10 chars in 500ms = 20 cps (below TARGET_CPS=40)
    recordFlush(state, 10, t0)
    expect(computeFlushDelay(state, 5, t0 + 500)).toBe(0)
  })

  it('returns 0 when current rate equals TARGET_CPS exactly', () => {
    const state = createRateTargetState()
    const t0 = 1000
    // TARGET_CPS=40 chars in 1000ms = exactly 40 cps
    recordFlush(state, 40, t0)
    expect(computeFlushDelay(state, 5, t0 + 1000)).toBe(0)
  })
})

// ---------------------------------------------------------------------------
// computeFlushDelay: throttles above target
// ---------------------------------------------------------------------------

describe('C-S2: computeFlushDelay() — above target (throttle)', () => {
  it('returns positive delay when current rate exceeds TARGET_CPS', () => {
    const state = createRateTargetState()
    const t0 = 1000
    // 200 chars in 200ms = 1000 cps (way above TARGET_CPS=40)
    recordFlush(state, 200, t0)
    const delay = computeFlushDelay(state, 20, t0 + 200)
    expect(delay).toBeGreaterThan(0)
  })

  it('delay is capped at MAX_WORD_BUFFER_MS (80ms)', () => {
    const state = createRateTargetState()
    const t0 = 1000
    // Extremely bursty: 10000 chars in 100ms
    recordFlush(state, 10000, t0)
    const delay = computeFlushDelay(state, 100, t0 + 100)
    expect(delay).toBeLessThanOrEqual(MAX_WORD_BUFFER_MS)
  })

  it('delay is non-negative', () => {
    const state = createRateTargetState()
    const t0 = 1000
    recordFlush(state, 500, t0)
    const delay = computeFlushDelay(state, 10, t0 + 300)
    expect(delay).toBeGreaterThanOrEqual(0)
  })
})

// ---------------------------------------------------------------------------
// computeFlushDelay: window sliding (old entries pruned)
// ---------------------------------------------------------------------------

describe('C-S2: computeFlushDelay() — window pruning', () => {
  it('prunes entries older than RATE_WINDOW_MS', () => {
    const state = createRateTargetState()
    const t0 = 1000
    // Very bursty at t0
    recordFlush(state, 10000, t0)
    // Now 1500ms later — all entries from t0 should be pruned (1000ms window)
    // Provider is now slow: only 5 chars arrived
    recordFlush(state, 5, t0 + 1100)
    const delay = computeFlushDelay(state, 5, t0 + 1500)
    // Rate in current window is low → no delay
    expect(delay).toBe(0)
  })
})

// ---------------------------------------------------------------------------
// Rate simulation: computeFlushDelay throttles bursty input
// ---------------------------------------------------------------------------

describe('C-S2: rate simulation — bursty input throttling', () => {
  it('total accumulated delay is significant on bursty input', () => {
    const state = createRateTargetState()
    const targetCps = TARGET_CPS
    const windowMs = RATE_WINDOW_MS

    // Warm up window: deliver a fast burst to build up history over >50ms.
    // First, place 2 chunks at t=0 and t=60 to establish a 60ms window
    // with high rate, then measure further delay.
    let nowMs = 0
    recordFlush(state, 200, nowMs)  // 200 chars at t=0
    nowMs = 60
    recordFlush(state, 200, nowMs)  // 200 chars at t=60 → 400 chars in 60ms = 6666 cps

    let totalDelayMs = 0
    const iterations = 20  // further bursty chunks

    for (let i = 0; i < iterations; i++) {
      nowMs += 5  // 5ms between chunks = very bursty
      const delay = computeFlushDelay(state, 40, nowMs, targetCps, windowMs)
      totalDelayMs += delay
      nowMs += delay
      recordFlush(state, 40, nowMs)
    }

    // With a warm window at 6666 cps (way above TARGET_CPS=40),
    // rate-targeting should inject meaningful delays
    expect(totalDelayMs).toBeGreaterThan(0)
  })

  it('delay per chunk does not exceed MAX_WORD_BUFFER_MS on any chunk', () => {
    const state = createRateTargetState()
    const targetCps = TARGET_CPS
    const windowMs = RATE_WINDOW_MS

    let nowMs = 0
    for (let i = 0; i < 100; i++) {
      const chunkLen = 500  // extremely bursty
      const delay = computeFlushDelay(state, chunkLen, nowMs, targetCps, windowMs)
      expect(delay, `chunk ${i} delay`).toBeLessThanOrEqual(MAX_WORD_BUFFER_MS)
      recordFlush(state, chunkLen, nowMs + delay)
      nowMs += delay + 1
    }
  })

  it('no delay injected when provider delivers at exactly TARGET_CPS', () => {
    const state = createRateTargetState()
    const targetCps = TARGET_CPS

    // Deliver exactly TARGET_CPS=40 chars per second: 4 chars every 100ms
    let nowMs = 100
    let anyDelay = false
    recordFlush(state, 4, nowMs)

    for (let i = 0; i < 20; i++) {
      nowMs += 100
      const delay = computeFlushDelay(state, 4, nowMs)
      if (delay > 0) anyDelay = true
      recordFlush(state, 4, nowMs)
    }

    // At exactly target rate, no throttling
    expect(anyDelay).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// isRateTargetEnabled
// ---------------------------------------------------------------------------

describe('C-S2: isRateTargetEnabled()', () => {
  afterEach(() => {
    mockGetFlag.mockReset()
    mockGetFlag.mockImplementation((flag: string) => {
      if (flag === 'R10_SMOOTH_STREAM_V2') return true
      if (flag === 'R11C_SMOOTH_STREAM_V3') return true
      return false
    })
  })

  it('returns true when both flags are true', () => {
    expect(isRateTargetEnabled()).toBe(true)
  })

  it('returns false when R10_SMOOTH_STREAM_V2=false (Y-S3 disabled)', () => {
    mockGetFlag.mockImplementation((flag: string) => {
      if (flag === 'R10_SMOOTH_STREAM_V2') return false
      if (flag === 'R11C_SMOOTH_STREAM_V3') return true
      return false
    })
    expect(isRateTargetEnabled()).toBe(false)
  })

  it('returns false when R11C_SMOOTH_STREAM_V3=false (rate-target disabled)', () => {
    mockGetFlag.mockImplementation((flag: string) => {
      if (flag === 'R10_SMOOTH_STREAM_V2') return true
      if (flag === 'R11C_SMOOTH_STREAM_V3') return false
      return false
    })
    expect(isRateTargetEnabled()).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// getSmoothStreamTransform: Y-S3 layer unchanged
// ---------------------------------------------------------------------------

describe('C-S2: getSmoothStreamTransform() — Y-S3 layer', () => {
  it('returns smoothStream transform when R10_SMOOTH_STREAM_V2=true', () => {
    expect(getSmoothStreamTransform()).toBeDefined()
  })

  it('returns undefined when R10_SMOOTH_STREAM_V2=false', () => {
    mockGetFlag.mockImplementation((flag: string) => {
      if (flag === 'R10_SMOOTH_STREAM_V2') return false
      return false
    })
    expect(getSmoothStreamTransform()).toBeUndefined()
  })
})

// ---------------------------------------------------------------------------
// Server-side only — no NEXT_PUBLIC in source
// ---------------------------------------------------------------------------

describe('C-S2: no NEXT_PUBLIC flag in smooth_stream.ts', () => {
  it('smooth_stream.ts does not reference NEXT_PUBLIC', async () => {
    const src = await import('fs').then(fs =>
      fs.readFileSync('./src/lib/streaming/smooth_stream.ts', 'utf8')
    )
    expect(src).not.toContain('NEXT_PUBLIC')
  })
})
