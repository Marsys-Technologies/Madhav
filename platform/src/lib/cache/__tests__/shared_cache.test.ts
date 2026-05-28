/**
 * MARSYS-JIS Stream C — shared_cache unit tests
 * Wave 4 unit 4.memorystore_caching.
 *
 * These tests mock ioredis so they run without a live Memorystore instance.
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'

// ────────────────────────────────────────────────────────────────────────
// Mock ioredis using vi.hoisted (factory + state must be hoisted together).
// ────────────────────────────────────────────────────────────────────────
const { fakeStore, FakeRedis } = vi.hoisted(() => {
  type StoredEntry = { value: string; expiresAt: number }
  const fakeStore = new Map<string, StoredEntry>()

  class FakeRedis {
    static lastInstance: FakeRedis | null = null
    isDown = false

    constructor() {
      FakeRedis.lastInstance = this
    }
    on() {}
    async get(key: string): Promise<string | null> {
      if (this.isDown) throw new Error('ECONNREFUSED')
      const e = fakeStore.get(key)
      if (!e) return null
      if (Date.now() > e.expiresAt) {
        fakeStore.delete(key)
        return null
      }
      return e.value
    }
    async set(key: string, value: string, _mode: 'EX', ttlSeconds: number): Promise<'OK'> {
      if (this.isDown) throw new Error('ECONNREFUSED')
      fakeStore.set(key, { value, expiresAt: Date.now() + ttlSeconds * 1000 })
      return 'OK'
    }
    async scan(
      cursor: string,
      _m: 'MATCH',
      pattern: string,
      _c: 'COUNT',
      _n: number,
    ): Promise<[string, string[]]> {
      if (this.isDown) throw new Error('ECONNREFUSED')
      if (cursor !== '0') return ['0', []]
      const re = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$')
      return ['0', [...fakeStore.keys()].filter((k) => re.test(k))]
    }
    async unlink(...keys: string[]): Promise<number> {
      if (this.isDown) throw new Error('ECONNREFUSED')
      let n = 0
      for (const k of keys) if (fakeStore.delete(k)) n++
      return n
    }
    async quit(): Promise<'OK'> {
      return 'OK'
    }
  }
  return { fakeStore, FakeRedis }
})

vi.mock('ioredis', () => ({ default: FakeRedis }))

// Force a known REDIS_HOST so redis_client.getRedis() returns the fake.
process.env.REDIS_HOST = '10.0.0.1'
process.env.REDIS_PORT = '6379'

// ────────────────────────────────────────────────────────────────────────
// Now safe to import the module under test.
// ────────────────────────────────────────────────────────────────────────
import {
  cacheGet,
  cacheSet,
  cacheGetOrCompute,
  buildKey,
  hashParams,
  invalidateNamespace,
  invalidateChart,
  setCacheMetricsSink,
  type CacheMetricsEvent,
} from '../shared_cache'
import { __resetRedisForTests } from '../redis_client'

describe('shared_cache (Memorystore adapter)', () => {
  beforeEach(async () => {
    fakeStore.clear()
    await __resetRedisForTests()
    if (FakeRedis.lastInstance) FakeRedis.lastInstance.isDown = false
    setCacheMetricsSink(() => {})
  })

  afterEach(async () => {
    await __resetRedisForTests()
  })

  describe('hashParams + buildKey', () => {
    it('is deterministic regardless of param key order', () => {
      expect(hashParams({ a: 1, b: 2 })).toBe(hashParams({ b: 2, a: 1 }))
    })

    it('differs when values differ', () => {
      expect(hashParams({ a: 1 })).not.toBe(hashParams({ a: 2 }))
    })

    it('namespaces keys with marsys:<surface>: prefix', () => {
      const k = buildKey('planner', { q: 'x' })
      expect(k.startsWith('marsys:planner:')).toBe(true)
    })

    it('hashes nested objects + arrays deterministically', () => {
      const a = hashParams({ x: { p: 1, q: 2 }, y: [3, 4] })
      const b = hashParams({ y: [3, 4], x: { q: 2, p: 1 } })
      expect(a).toBe(b)
    })
  })

  describe('cacheGet / cacheSet', () => {
    it('round-trips a JSON-able value', async () => {
      const key = buildKey('planner', { q: 'birth chart' })
      await cacheSet('planner', key, { plan: 'x' }, { ttlSeconds: 10 })
      const got = await cacheGet<{ plan: string }>('planner', key)
      expect(got).toEqual({ plan: 'x' })
    })

    it('returns undefined on miss', async () => {
      expect(await cacheGet('planner', 'marsys:planner:nope')).toBeUndefined()
    })

    it('returns undefined (never throws) when Redis is down', async () => {
      // Trigger client init then flip it down.
      await cacheSet('planner', buildKey('planner', { a: 1 }), 'init', { ttlSeconds: 10 })
      if (FakeRedis.lastInstance) FakeRedis.lastInstance.isDown = true
      const got = await cacheGet('planner', buildKey('planner', { a: 1 }))
      expect(got).toBeUndefined()
    })

    it('does not throw when set fails (compute path already succeeded)', async () => {
      await cacheSet('planner', buildKey('planner', { a: 1 }), 'x', { ttlSeconds: 10 })
      if (FakeRedis.lastInstance) FakeRedis.lastInstance.isDown = true
      await expect(
        cacheSet('planner', buildKey('planner', { b: 2 }), 'y', { ttlSeconds: 10 }),
      ).resolves.toBeUndefined()
    })

    it('respects TTL — expired entries return undefined', async () => {
      const key = buildKey('planner', { q: 'ttl-test' })
      await cacheSet('planner', key, 'fresh', { ttlSeconds: 1 })
      // Manually rewind expiresAt in the fake store.
      const entry = fakeStore.get(key)!
      entry.expiresAt = Date.now() - 1000
      expect(await cacheGet('planner', key)).toBeUndefined()
    })
  })

  describe('cacheGetOrCompute', () => {
    it('computes on miss + stores result', async () => {
      const compute = vi.fn().mockResolvedValue({ v: 42 })
      const key = buildKey('vertex-embed', { text: 'hello' })
      const r1 = await cacheGetOrCompute('vertex-embed', key, 60, compute)
      expect(r1).toEqual({ v: 42 })
      expect(compute).toHaveBeenCalledTimes(1)

      // give the fire-and-forget set time to land
      await new Promise((r) => setTimeout(r, 0))

      const r2 = await cacheGetOrCompute('vertex-embed', key, 60, compute)
      expect(r2).toEqual({ v: 42 })
      expect(compute).toHaveBeenCalledTimes(1) // hit, did NOT recompute
    })

    it('falls back to compute when Redis is down (chaos recovery)', async () => {
      // Prime the client then flip it down.
      await cacheSet('vertex-embed', buildKey('vertex-embed', { warm: 1 }), 'x', { ttlSeconds: 10 })
      if (FakeRedis.lastInstance) FakeRedis.lastInstance.isDown = true

      const compute = vi.fn().mockResolvedValue([0.1, 0.2, 0.3])
      const key = buildKey('vertex-embed', { text: 'chaos' })
      const r = await cacheGetOrCompute('vertex-embed', key, 60, compute)
      expect(r).toEqual([0.1, 0.2, 0.3])
      expect(compute).toHaveBeenCalledTimes(1)
    })
  })

  describe('invalidateNamespace + invalidateChart', () => {
    it('clears only the targeted namespace', async () => {
      await cacheSet('planner', buildKey('planner', { q: 'a' }), 'pa', { ttlSeconds: 60 })
      await cacheSet('planner', buildKey('planner', { q: 'b' }), 'pb', { ttlSeconds: 60 })
      await cacheSet('vertex-embed', buildKey('vertex-embed', { t: 'x' }), 'vx', { ttlSeconds: 60 })

      const n = await invalidateNamespace('planner')
      expect(n).toBe(2)

      expect(await cacheGet('planner', buildKey('planner', { q: 'a' }))).toBeUndefined()
      expect(await cacheGet('vertex-embed', buildKey('vertex-embed', { t: 'x' }))).toBe('vx')
    })

    it('invalidateChart wipes both retrieval-bundle + planner surfaces', async () => {
      await cacheSet('retrieval-bundle', buildKey('retrieval-bundle', { t: 'a' }), 'r', { ttlSeconds: 60 })
      await cacheSet('planner', buildKey('planner', { q: 'p' }), 'p', { ttlSeconds: 60 })
      await cacheSet('vertex-embed', buildKey('vertex-embed', { t: 'e' }), 'e', { ttlSeconds: 60 })

      await invalidateChart('chart-abc')

      expect(await cacheGet('retrieval-bundle', buildKey('retrieval-bundle', { t: 'a' }))).toBeUndefined()
      expect(await cacheGet('planner', buildKey('planner', { q: 'p' }))).toBeUndefined()
      expect(await cacheGet('vertex-embed', buildKey('vertex-embed', { t: 'e' }))).toBe('e')
    })

    it('returns 0 (does not throw) when Redis is down', async () => {
      await cacheSet('planner', buildKey('planner', { warm: 1 }), 'x', { ttlSeconds: 10 })
      if (FakeRedis.lastInstance) FakeRedis.lastInstance.isDown = true
      expect(await invalidateNamespace('planner')).toBe(0)
    })
  })

  describe('metrics sink', () => {
    it('fires hit/miss/set events with surface tags', async () => {
      const events: CacheMetricsEvent[] = []
      setCacheMetricsSink((ev) => events.push(ev))

      const key = buildKey('planner', { q: 'metrics' })
      await cacheGet('planner', key)                         // miss
      await cacheSet('planner', key, 'x', { ttlSeconds: 10 }) // set
      await cacheGet('planner', key)                         // hit

      const outcomes = events.map((e) => e.outcome)
      expect(outcomes).toContain('miss')
      expect(outcomes).toContain('set')
      expect(outcomes).toContain('hit')
      for (const e of events) expect(e.surface).toBe('planner')
    })

    it('emits error events when Redis fails', async () => {
      await cacheSet('planner', buildKey('planner', { warm: 1 }), 'x', { ttlSeconds: 10 })
      if (FakeRedis.lastInstance) FakeRedis.lastInstance.isDown = true

      const events: CacheMetricsEvent[] = []
      setCacheMetricsSink((ev) => events.push(ev))
      await cacheGet('planner', buildKey('planner', { q: 'fails' }))
      expect(events.some((e) => e.outcome === 'error')).toBe(true)
    })
  })
})
