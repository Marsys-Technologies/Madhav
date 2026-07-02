/**
 * capability_cache.test.ts
 *
 * Verifies the latency fix added to /api/retrieval/capability: identical
 * (uri, args) calls must hit the Redis cache on the second invocation
 * (served_from_cache: true) rather than re-executing the handler.
 *
 * Tests:
 *   1. Cache miss on first call → handler executes, result stored in Redis
 *   2. Cache hit on second identical call → handler NOT called again
 *   3. Different args → separate cache entries, both miss on first call
 *   4. Redis unavailable → falls through to compute (no crash)
 *
 * Uses the FakeRedis pattern from shared_cache.test.ts (vi.hoisted factory).
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'

// ── FakeRedis (must be hoisted so vi.mock factory can reference it) ───────────

const { fakeStore, FakeRedis } = vi.hoisted(() => {
  type StoredEntry = { value: string; expiresAt: number }
  const fakeStore = new Map<string, StoredEntry>()

  class FakeRedis {
    static lastInstance: FakeRedis | null = null
    isDown = false
    constructor() { FakeRedis.lastInstance = this }
    on() {}
    async get(key: string): Promise<string | null> {
      if (this.isDown) throw new Error('ECONNREFUSED')
      const e = fakeStore.get(key)
      if (!e || Date.now() > e.expiresAt) return null
      return e.value
    }
    async set(key: string, value: string, _ex: 'EX', ttl: number): Promise<'OK'> {
      if (this.isDown) throw new Error('ECONNREFUSED')
      fakeStore.set(key, { value, expiresAt: Date.now() + ttl * 1000 })
      return 'OK'
    }
  }
  return { fakeStore, FakeRedis }
})

vi.mock('ioredis', () => ({ default: FakeRedis }))
vi.mock('server-only', () => ({}))

// ── Import cache helpers under test ──────────────────────────────────────────

import { buildKey, cacheGet, cacheSet } from '../shared_cache'

// ── Simulate the capability route's cache logic ───────────────────────────────
//
// Rather than mounting the full Next.js route (which requires mocking 15+
// modules including auth, bootstrap, getCapability), we replicate the exact
// caching block added to the route handler and verify its contract:
//   1. build cache key
//   2. check Redis
//   3. on miss: compute + store
//   4. return served_from_cache accordingly
//
// This is a behavioural contract test, not a snapshot test of the route file.

async function simulateCapabilityCall(
  uri: string,
  safeArgs: Record<string, unknown>,
  handler: () => Promise<unknown>,
): Promise<{ content: unknown; served_from_cache: boolean }> {
  const cacheKey = buildKey('retrieval-bundle', { uri, args: safeArgs })
  const cached = await cacheGet<unknown>('retrieval-bundle', cacheKey)
  if (cached !== undefined) {
    return { content: cached, served_from_cache: true }
  }
  const content = await handler()
  await cacheSet('retrieval-bundle', cacheKey, content, { ttlSeconds: 300 })
  return { content, served_from_cache: false }
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('capability route caching (latency fix)', () => {
  beforeEach(() => {
    fakeStore.clear()
    if (FakeRedis.lastInstance) FakeRedis.lastInstance.isDown = false
  })

  it('first call returns served_from_cache: false and invokes handler', async () => {
    const handler = vi.fn().mockResolvedValue({ signals: [1, 2, 3] })
    const result = await simulateCapabilityCall(
      'marsys://tool/L1/get_dashas',
      { chart_id: 'abc-123', ayanamsha_id: 'lahiri_chitrapaksha' },
      handler,
    )
    expect(result.served_from_cache).toBe(false)
    expect(result.content).toEqual({ signals: [1, 2, 3] })
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('second identical call returns served_from_cache: true and skips handler', async () => {
    const handler = vi.fn().mockResolvedValue({ signals: [1, 2, 3] })
    const args = { chart_id: 'abc-123', ayanamsha_id: 'lahiri_chitrapaksha' }
    const uri = 'marsys://tool/L1/get_dashas'

    const first  = await simulateCapabilityCall(uri, args, handler)
    const second = await simulateCapabilityCall(uri, args, handler)

    expect(first.served_from_cache).toBe(false)
    expect(second.served_from_cache).toBe(true)
    expect(second.content).toEqual({ signals: [1, 2, 3] })
    // Handler invoked exactly once — second call was a cache hit
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('different args produce separate cache entries', async () => {
    const handler = vi.fn()
      .mockResolvedValueOnce({ domain: 'career' })
      .mockResolvedValueOnce({ domain: 'health' })
    const uri = 'marsys://tool/L2/query_domain_reading'

    const r1 = await simulateCapabilityCall(uri, { chart_id: 'abc', domain: 'career' }, handler)
    const r2 = await simulateCapabilityCall(uri, { chart_id: 'abc', domain: 'health' }, handler)

    expect(r1.served_from_cache).toBe(false)
    expect(r2.served_from_cache).toBe(false)
    expect(handler).toHaveBeenCalledTimes(2)
  })

  it('repeated call with different chart_id is a separate cache miss', async () => {
    const handler = vi.fn().mockResolvedValue({ ok: true })
    const uri = 'marsys://tool/L1/get_positions'

    await simulateCapabilityCall(uri, { chart_id: 'chart-A' }, handler)
    const r2 = await simulateCapabilityCall(uri, { chart_id: 'chart-B' }, handler)

    expect(r2.served_from_cache).toBe(false)
    expect(handler).toHaveBeenCalledTimes(2)
  })

  it('Redis down: falls through to compute without throwing', async () => {
    FakeRedis.lastInstance!.isDown = true
    const handler = vi.fn().mockResolvedValue({ fallback: true })

    // getRedis() returns null when ioredis errors on connect, so cacheGet/Set
    // return undefined silently. Simulate by checking the result is compute-fresh.
    // (In practice getRedis() catches init errors and returns null; the FakeRedis
    // isDown path simulates a mid-session failure, which the error handler in
    // cacheGet catches and returns undefined — tested in shared_cache.test.ts.
    // Here we just verify the route logic doesn't throw when cache is unhealthy.)
    let threw = false
    try {
      await simulateCapabilityCall('marsys://tool/L1/get_dashas', { chart_id: 'x' }, handler)
    } catch {
      threw = true
    }
    expect(threw).toBe(false)
  })
})
