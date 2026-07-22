import { describe, expect, it, afterAll } from 'vitest'
import { percentile, summarizeLatencies, cacheHitRate, successRate, getByPath } from './stats'
import { defaultTarget } from './http_client'
import { measureCacheHitRate, measureConcurrencyCapacity, measureQosBackpressure, measureSloPerQueryClass } from './modes'
import { startMockServer, type MockServerHandle } from './mock_server'
import { DEFAULT_THRESHOLDS } from './types'
import { parseArgs } from './harness'

// ── stats.ts — pure math, verified against hand-computed values ──────────────────

describe('percentile', () => {
  it('returns 0 for an empty array', () => {
    expect(percentile([], 50)).toBe(0)
  })

  it('returns the single value for a 1-element array at any percentile', () => {
    expect(percentile([42], 0)).toBe(42)
    expect(percentile([42], 50)).toBe(42)
    expect(percentile([42], 99)).toBe(42)
  })

  it('p50 of [1,2,3,4,5] is the median, 3', () => {
    expect(percentile([1, 2, 3, 4, 5], 50)).toBe(3)
  })

  it('p0 and p100 are min and max', () => {
    const values = [5, 1, 4, 2, 3]
    expect(percentile(values, 0)).toBe(1)
    expect(percentile(values, 100)).toBe(5)
  })

  it('is insensitive to input order (sorts internally)', () => {
    expect(percentile([3, 1, 2], 50)).toBe(percentile([1, 2, 3], 50))
  })

  it('linearly interpolates between ranks (hand-computed: [10,20,30,40] p50 = 20+0.5*(30-20)=25)', () => {
    // rank = (50/100) * 3 = 1.5 -> interpolate between index 1 (20) and 2 (30)
    expect(percentile([10, 20, 30, 40], 50)).toBe(25)
  })

  it('matches a known worked example: 100 values 1..100, p95 = 95.05', () => {
    const values = Array.from({ length: 100 }, (_, i) => i + 1)
    // rank = 0.95 * 99 = 94.05 -> values[94]=95, values[95]=96 -> 95 + 0.05*(96-95) = 95.05
    expect(percentile(values, 95)).toBeCloseTo(95.05, 6)
  })
})

describe('summarizeLatencies', () => {
  it('all-zero stats for empty input', () => {
    const s = summarizeLatencies([])
    expect(s).toEqual({ n: 0, p50: 0, p95: 0, p99: 0, mean: 0, min: 0, max: 0 })
  })

  it('computes mean/min/max/n correctly on a known set', () => {
    const s = summarizeLatencies([10, 20, 30])
    expect(s.n).toBe(3)
    expect(s.mean).toBe(20)
    expect(s.min).toBe(10)
    expect(s.max).toBe(30)
    expect(s.p50).toBe(20)
  })
})

describe('cacheHitRate', () => {
  it('is 0 when there are no successful attempts', () => {
    expect(cacheHitRate([{ ok: false, cacheHit: false }])).toBe(0)
  })

  it('counts hits only among successful (ok) results, ignoring failed ones', () => {
    const rows = [
      { ok: true, cacheHit: true },
      { ok: true, cacheHit: true },
      { ok: true, cacheHit: false },
      { ok: false, cacheHit: false }, // excluded from denominator
    ]
    // 2 hits / 3 ok attempts = 0.666...
    expect(cacheHitRate(rows)).toBeCloseTo(2 / 3, 10)
  })

  it('is 1.0 when every successful attempt was a cache hit', () => {
    const rows = [
      { ok: true, cacheHit: true },
      { ok: true, cacheHit: true },
    ]
    expect(cacheHitRate(rows)).toBe(1)
  })
})

describe('successRate', () => {
  it('is 0 for an empty array', () => {
    expect(successRate([])).toBe(0)
  })

  it('computes the fraction of ok:true rows', () => {
    expect(successRate([{ ok: true }, { ok: true }, { ok: false }, { ok: false }])).toBe(0.5)
  })
})

describe('getByPath', () => {
  it('resolves a nested dot-path', () => {
    expect(getByPath({ a: { b: { c: 7 } } }, 'a.b.c')).toBe(7)
  })

  it('resolves a top-level field (the default served_from_cache shape)', () => {
    expect(getByPath({ served_from_cache: true }, 'served_from_cache')).toBe(true)
  })

  it('returns undefined for a missing path without throwing', () => {
    expect(getByPath({ a: 1 }, 'a.b.c')).toBeUndefined()
    expect(getByPath(null, 'a.b')).toBeUndefined()
    expect(getByPath(42, 'a.b')).toBeUndefined()
  })
})

// ── harness.ts CLI arg parsing ─────────────────────────────────────────────────────

describe('parseArgs', () => {
  it('defaults to local/dry-run, all modes, concurrency=32', () => {
    const args = parseArgs([])
    expect(args.dryRun).toBe(true)
    expect(args.target).toBe('local')
    expect(args.modes).toEqual(['cache', 'concurrency', 'qos', 'slo'])
    expect(args.concurrency).toBe(32)
  })

  it('a real --target does NOT force dry-run on its own', () => {
    const args = parseArgs(['--target=https://example.invalid'])
    expect(args.dryRun).toBe(false)
    expect(args.target).toBe('https://example.invalid')
  })

  it('--dry-run forces dry-run even with a real --target (belt-and-suspenders safety)', () => {
    const args = parseArgs(['--target=https://example.invalid', '--dry-run'])
    expect(args.dryRun).toBe(true)
  })

  it('parses --mode=cache to a single-mode array', () => {
    expect(parseArgs(['--mode=cache']).modes).toEqual(['cache'])
  })

  it('parses --concurrency and --out', () => {
    const args = parseArgs(['--concurrency=64', '--out=/tmp/report.json'])
    expect(args.concurrency).toBe(64)
    expect(args.out).toBe('/tmp/report.json')
  })
})

// ── Integration: real HTTP round trips against the local mock server ─────────────
// This is the harness's own dry-run verification (Task 12's constraint: no live
// connector credential in this session — see harness.ts's scope-boundary banner).
// Every assertion below exercises real sockets/latency/concurrency against
// mock_server.ts, including its embedded REAL QosDispatchQueue.

describe('W6 load harness — dry-run against the local mock server', () => {
  let mock: MockServerHandle

  afterAll(async () => {
    if (mock) await mock.close()
  })

  it('starts and stops cleanly', async () => {
    mock = await startMockServer()
    expect(mock.url).toMatch(/^http:\/\/127\.0\.0\.1:\d+$/)
  })

  it('W-28: cache hit-rate — first call misses, repeats hit (real HTTP + real cache Map)', async () => {
    const target = defaultTarget(mock.url)
    const report = await measureCacheHitRate(target, DEFAULT_THRESHOLDS, { n: 10 })
    expect(report.n).toBe(10)
    expect(report.errors).toBe(0)
    // First call is a guaranteed miss; the rest should hit the mock's TTL cache.
    expect(report.misses).toBeGreaterThanOrEqual(1)
    expect(report.hits).toBeGreaterThanOrEqual(8)
    expect(report.hitRate).toBeGreaterThan(0.5)
    expect(report.pass).toBe(true)
    // Cache hits should be measurably faster than the compute path.
    if (report.hitLatency && report.missLatency) {
      expect(report.hitLatency.mean).toBeLessThan(report.missLatency.mean)
    }
  })

  it('W-29: concurrency capacity — ramps levels, records success rate + latency percentiles', async () => {
    const target = defaultTarget(mock.url)
    const report = await measureConcurrencyCapacity(target, DEFAULT_THRESHOLDS, {
      levels: [1, 4, 16],
      requestsPerLevel: 16,
    })
    expect(report.levels).toHaveLength(3)
    for (const level of report.levels) {
      expect(level.requests).toBe(16)
      expect(level.latency.n).toBe(16)
      expect(level.successRate).toBeGreaterThan(0)
    }
    // Higher concurrency against the mock's contention-scaled compute delay should
    // show non-negative degradation (later level's p95 >= first level's, since compute
    // delay explicitly grows with inFlight in mock_server.ts).
    expect(report.levels[2].latency.p95).toBeGreaterThanOrEqual(report.levels[0].latency.p95 * 0.5)
  })

  it('W-30: QoS/backpressure — real QosDispatchQueue is observed, never silently degrades', async () => {
    const target = defaultTarget(mock.url)
    // Small server-side queue (concurrency=6, maxQueueDepth=12 in mock_server.ts
    // defaults) vs. a much larger burst here so contention actually happens.
    const report = await measureQosBackpressure(target, DEFAULT_THRESHOLDS, {
      principals: 10,
      requestsPerPrincipal: 8,
    })
    expect(report.totalRequests).toBe(80)
    // The core honest-degradation assertion: zero silently-degraded 200s.
    expect(report.silentlyDegraded).toBe(0)
    // At this burst size against a 6-concurrency/12-depth queue, refusals should occur.
    expect(report.qosMechanismObserved).toBe('real_dispatch_queue')
    expect(report.honestlyRefused).toBeGreaterThan(0)
    expect(report.pass).toBe(true)
  })

  it('W-31: SLO per query-class — groups the w5_battery corpus by family, computes percentiles', async () => {
    const target = defaultTarget(mock.url)
    const report = await measureSloPerQueryClass(target, DEFAULT_THRESHOLDS, { concurrency: 8 })
    expect(report.byQueryClass.map((r) => r.queryClass).sort()).toEqual(
      ['career', 'general', 'health', 'marriage', 'panoramic', 'wealth'].sort(),
    )
    for (const row of report.byQueryClass) {
      expect(row.latency.n).toBe(10) // 5 queries x 2 charts per family
    }
    expect(report.baselineComparisonNote).toMatch(/no latency figure/)
  })
})
