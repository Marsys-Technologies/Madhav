/**
 * W5 L6 — capability_dispatch_cache unit tests.
 *
 * No REDIS_HOST is set in the test environment, so `getRedis()` returns null
 * and the L2 tier is a guaranteed no-op (`cacheGet`/`cacheSet` skip cleanly,
 * per shared_cache.ts's own contract) — these tests exercise the L1
 * in-process coalescing + FIFO cap behavior, which is this module's own
 * responsibility and does not depend on Redis being present.
 *
 * Note on timing: `getOrComputeCapability` synchronously inserts a new
 * in-flight entry into the process-global map BEFORE it ever awaits
 * anything (the L2 `cacheGet` lookup happens inside the async closure that
 * is merely STARTED, not awaited, by the outer function). This means two
 * calls issued back-to-back in the same synchronous tick for the same
 * (uri, args) key reliably coalesce — the second call's synchronous
 * `_inflight.get(key)` lookup always sees the first call's synchronously-set
 * entry. Tests below rely on this and do not need manual microtask-flushing.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  getOrComputeCapability,
  __resetCapabilityDispatchCacheForTests,
  __inflightSizeForTests,
  MAX_INFLIGHT_ENTRIES,
} from '../capability_dispatch_cache'

beforeEach(() => {
  __resetCapabilityDispatchCacheForTests()
  delete process.env.REDIS_HOST
})

describe('getOrComputeCapability — cacheable=false (opt-out, unchanged behavior)', () => {
  it('calls compute() every time, never coalescing', async () => {
    const compute = vi.fn(() => Promise.resolve({ v: 1 }))
    await getOrComputeCapability('marsys://tool/x', { a: 1 }, false, compute)
    await getOrComputeCapability('marsys://tool/x', { a: 1 }, false, compute)
    expect(compute).toHaveBeenCalledTimes(2)
  })

  it('leaves the in-flight map untouched', async () => {
    const compute = vi.fn(() => Promise.resolve('ok'))
    await getOrComputeCapability('marsys://tool/x', {}, false, compute)
    expect(__inflightSizeForTests()).toBe(0)
  })
})

describe('getOrComputeCapability — cacheable=true, concurrent identical calls', () => {
  it('coalesces N concurrent identical (uri, args) calls into exactly ONE compute()', async () => {
    const compute = vi.fn(() => Promise.resolve('fresh-result'))

    // All three issued in the same synchronous tick, before any await —
    // this is the real shape a synthesis/judgment fan-out produces (several
    // Promise.all-branches asking for the same chart's data concurrently).
    const p1 = getOrComputeCapability('marsys://tool/L0/query_planet_position', { chart_id: 'c1', date: '2026-07-21' }, true, compute)
    const p2 = getOrComputeCapability('marsys://tool/L0/query_planet_position', { chart_id: 'c1', date: '2026-07-21' }, true, compute)
    const p3 = getOrComputeCapability('marsys://tool/L0/query_planet_position', { chart_id: 'c1', date: '2026-07-21' }, true, compute)

    const [r1, r2, r3] = await Promise.all([p1, p2, p3])

    expect(compute).toHaveBeenCalledTimes(1)
    expect(r1).toBe('fresh-result')
    expect(r2).toBe('fresh-result')
    expect(r3).toBe('fresh-result')
  })

  it('argument key order does not matter — {a,b} and {b,a} hash to the same key and coalesce', async () => {
    const compute = vi.fn(() => Promise.resolve('v'))

    const p1 = getOrComputeCapability('marsys://tool/x', { a: 1, b: 2 }, true, compute)
    const p2 = getOrComputeCapability('marsys://tool/x', { b: 2, a: 1 }, true, compute)
    await Promise.all([p1, p2])

    // Only one compute fired even though the two calls' args objects were
    // built with keys in a different order — proves buildKey's stable
    // stringify is in effect for this cache's key derivation.
    expect(compute).toHaveBeenCalledTimes(1)
  })

  it('different args produce independent computations (no false-positive coalescing)', async () => {
    const compute = vi.fn((n: number) => Promise.resolve(n))
    const p1 = getOrComputeCapability('marsys://tool/x', { chart_id: 'c1' }, true, () => compute(1))
    const p2 = getOrComputeCapability('marsys://tool/x', { chart_id: 'c2' }, true, () => compute(2))
    await Promise.all([p1, p2])
    expect(compute).toHaveBeenCalledTimes(2)
  })

  it('different uri with identical args produces independent computations', async () => {
    const compute = vi.fn((n: number) => Promise.resolve(n))
    const p1 = getOrComputeCapability('marsys://tool/a', { chart_id: 'c1' }, true, () => compute(1))
    const p2 = getOrComputeCapability('marsys://tool/b', { chart_id: 'c1' }, true, () => compute(2))
    await Promise.all([p1, p2])
    expect(compute).toHaveBeenCalledTimes(2)
  })

  it('removes the entry from the in-flight map once settled (L1 coalesces CONCURRENCY, it is not an unbounded memoization tier — that is L2 + TTL\'s job)', async () => {
    const compute = vi.fn(() => Promise.resolve('a'))
    await getOrComputeCapability('marsys://tool/x', { k: 1 }, true, compute)
    expect(__inflightSizeForTests()).toBe(0)

    // A second, NON-concurrent call (issued only after the first fully
    // settled) finds no in-flight entry and no Redis (disabled in this
    // test env) — it must recompute rather than hang or silently miss.
    await getOrComputeCapability('marsys://tool/x', { k: 1 }, true, compute)
    expect(compute).toHaveBeenCalledTimes(2)
  })

  it('still removes the in-flight entry when compute() rejects (no permanently stuck entries)', async () => {
    const compute = vi.fn(() => Promise.reject(new Error('boom')))
    await expect(
      getOrComputeCapability('marsys://tool/x', { k: 1 }, true, compute),
    ).rejects.toThrow('boom')
    expect(__inflightSizeForTests()).toBe(0)
  })

  it('a second concurrent caller that arrives while the first is still rejecting also rejects, and the map is left clean', async () => {
    const compute = vi.fn(() => Promise.reject(new Error('boom')))
    const p1 = getOrComputeCapability('marsys://tool/x', { k: 1 }, true, compute)
    const p2 = getOrComputeCapability('marsys://tool/x', { k: 1 }, true, compute)

    await expect(p1).rejects.toThrow('boom')
    await expect(p2).rejects.toThrow('boom')
    expect(compute).toHaveBeenCalledTimes(1) // both callers shared the one failing compute
    expect(__inflightSizeForTests()).toBe(0)
  })
})

describe('getOrComputeCapability — FIFO cap (the "caps" requirement)', () => {
  it('never lets the in-flight map exceed MAX_INFLIGHT_ENTRIES, even under massive distinct-key fan-out', async () => {
    // Fire MAX_INFLIGHT_ENTRIES + 250 concurrent calls, each a DISTINCT key,
    // in one synchronous burst — the pathological case the FIFO cap exists
    // for. Insertion (and eviction) is synchronous, so the peak-size check
    // immediately after the loop observes the cap correctly regardless of
    // how fast `compute()` itself resolves.
    const totalKeys = MAX_INFLIGHT_ENTRIES + 250
    const promises: Promise<number>[] = []

    for (let i = 0; i < totalKeys; i++) {
      promises.push(
        getOrComputeCapability('marsys://tool/fanout', { i }, true, () => Promise.resolve(i)),
      )
    }

    expect(__inflightSizeForTests()).toBeLessThanOrEqual(MAX_INFLIGHT_ENTRIES)

    const results = await Promise.all(promises)
    expect(results).toEqual(Array.from({ length: totalKeys }, (_, i) => i))
    expect(__inflightSizeForTests()).toBe(0)
  })
})
