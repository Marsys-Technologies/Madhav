/**
 * MARSYS-JIS Stream C — shared_cache chaos tests
 * Wave 4 unit 4.memorystore_caching commit 3/3.
 *
 * Satisfies brief AC.3 — "Redis flush / outage mid-request → cache miss →
 * falls back to compute cleanly → response correct."
 *
 * Each scenario simulates a different Redis failure mode and asserts:
 *   (a) cacheGetOrCompute returns the correct value
 *   (b) the compute closure ran (the path was NOT silently served stale)
 *   (c) no exception propagates to the caller
 *
 * Mocks ioredis at the module boundary so a chaotic ioredis is the only
 * thing the cache adapter sees.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

// ─────────────────────────────────────────────────────────────────────────────
// Hoisted ioredis fake — supports per-test failure-mode toggles:
//   • mode: 'healthy'         — normal operation
//   • mode: 'flushed'         — GET returns null (cache emptied mid-flight)
//   • mode: 'connection-down' — every op throws ECONNREFUSED
//   • mode: 'timeout'         — every op throws "Command timed out"
//   • mode: 'corrupted'       — GET returns non-JSON garbage
//   • mode: 'partial-failure' — first call OK, then breaks (flip mid-request)
// ─────────────────────────────────────────────────────────────────────────────

const { fakeStore, FakeRedis, chaos } = vi.hoisted(() => {
  type StoredEntry = { value: string; expiresAt: number }
  const fakeStore = new Map<string, StoredEntry>()
  const chaos = {
    mode: 'healthy' as
      | 'healthy'
      | 'flushed'
      | 'connection-down'
      | 'timeout'
      | 'corrupted'
      | 'partial-failure',
    callCount: 0,
    flipAfter: 1, // for partial-failure: how many successful ops before flipping
  }

  class FakeRedis {
    static lastInstance: FakeRedis | null = null
    constructor() {
      FakeRedis.lastInstance = this
    }
    on() {}

    private chaosCheck(op: string): { throwErr?: Error; forceNull?: boolean; corrupt?: boolean } {
      chaos.callCount++
      if (chaos.mode === 'connection-down') {
        return { throwErr: new Error(`ECONNREFUSED (${op})`) }
      }
      if (chaos.mode === 'timeout') {
        return { throwErr: new Error(`Command timed out (${op})`) }
      }
      if (chaos.mode === 'flushed' && op === 'get') {
        return { forceNull: true }
      }
      if (chaos.mode === 'corrupted' && op === 'get') {
        return { corrupt: true }
      }
      if (chaos.mode === 'partial-failure' && chaos.callCount > chaos.flipAfter) {
        return { throwErr: new Error('ECONNRESET (mid-request)') }
      }
      return {}
    }

    async get(key: string): Promise<string | null> {
      const c = this.chaosCheck('get')
      if (c.throwErr) throw c.throwErr
      if (c.forceNull) return null
      if (c.corrupt) return '{not-valid-json'
      const e = fakeStore.get(key)
      if (!e) return null
      if (Date.now() > e.expiresAt) {
        fakeStore.delete(key)
        return null
      }
      return e.value
    }
    async set(key: string, value: string, _mode: 'EX', ttlSeconds: number): Promise<'OK'> {
      const c = this.chaosCheck('set')
      if (c.throwErr) throw c.throwErr
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
      const c = this.chaosCheck('scan')
      if (c.throwErr) throw c.throwErr
      if (cursor !== '0') return ['0', []]
      const re = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$')
      return ['0', [...fakeStore.keys()].filter((k) => re.test(k))]
    }
    async unlink(...keys: string[]): Promise<number> {
      const c = this.chaosCheck('unlink')
      if (c.throwErr) throw c.throwErr
      let n = 0
      for (const k of keys) if (fakeStore.delete(k)) n++
      return n
    }
    async quit(): Promise<'OK'> {
      return 'OK'
    }
  }

  return { fakeStore, FakeRedis, chaos }
})

vi.mock('ioredis', () => ({ default: FakeRedis }))

// Force a known REDIS_HOST so getRedis() returns the fake.
process.env.REDIS_HOST = '10.0.0.1'
process.env.REDIS_PORT = '6379'

import {
  buildKey,
  cacheGet,
  cacheSet,
  cacheGetOrCompute,
  invalidateNamespace,
  setCacheMetricsSink,
  type CacheMetricsEvent,
} from '../shared_cache'
import { __resetRedisForTests } from '../redis_client'

describe('shared_cache CHAOS — brief AC.3: clean fall-back on Redis trouble', () => {
  beforeEach(async () => {
    fakeStore.clear()
    chaos.mode = 'healthy'
    chaos.callCount = 0
    chaos.flipAfter = 1
    await __resetRedisForTests()
    setCacheMetricsSink(() => {})
  })

  afterEach(async () => {
    await __resetRedisForTests()
  })

  // ──────────────────────────────────────────────────────────────────────────
  // AC.3 core path — Redis flushed mid-request
  // ──────────────────────────────────────────────────────────────────────────

  describe('Redis flushed (FLUSHALL between set and get)', () => {
    it('warm key → flushed → next read is a clean miss → compute runs again', async () => {
      const key = buildKey('retrieval-bundle', { chart: 'c-1', tool: 'msr' })

      // 1. Warm the cache normally.
      const compute = vi.fn().mockResolvedValueOnce({ answer: 'fresh-1' })
      const r1 = await cacheGetOrCompute('retrieval-bundle', key, 60, compute)
      expect(r1).toEqual({ answer: 'fresh-1' })
      expect(compute).toHaveBeenCalledTimes(1)
      // Give fire-and-forget set time to land.
      await new Promise((r) => setTimeout(r, 0))

      // 2. Simulate Redis FLUSHALL mid-request: GET now returns null.
      chaos.mode = 'flushed'

      // 3. Same key → cache miss → compute MUST run again, response correct.
      const compute2 = vi.fn().mockResolvedValueOnce({ answer: 'fresh-2' })
      const r2 = await cacheGetOrCompute('retrieval-bundle', key, 60, compute2)
      expect(r2).toEqual({ answer: 'fresh-2' })
      expect(compute2).toHaveBeenCalledTimes(1)
    })

    it('emits miss outcome (not error) when Redis legitimately returns null', async () => {
      chaos.mode = 'flushed'
      const events: CacheMetricsEvent[] = []
      setCacheMetricsSink((ev) => events.push(ev))

      const compute = vi.fn().mockResolvedValueOnce('ok')
      await cacheGetOrCompute('planner', buildKey('planner', { q: 'q' }), 30, compute)

      expect(events.some((e) => e.outcome === 'miss')).toBe(true)
      expect(events.every((e) => e.outcome !== 'error')).toBe(true)
    })
  })

  // ──────────────────────────────────────────────────────────────────────────
  // AC.3 connection chaos — Redis unreachable mid-request
  // ──────────────────────────────────────────────────────────────────────────

  describe('Redis connection-down (ECONNREFUSED)', () => {
    it('cacheGetOrCompute returns compute output even when GET throws', async () => {
      chaos.mode = 'connection-down'
      const compute = vi.fn().mockResolvedValueOnce({ data: 42 })
      const result = await cacheGetOrCompute(
        'vertex-embed',
        buildKey('vertex-embed', { text: 'hi' }),
        60,
        compute,
      )
      expect(result).toEqual({ data: 42 })
      expect(compute).toHaveBeenCalledTimes(1)
    })

    it('does NOT throw to caller — every Redis op is guarded', async () => {
      chaos.mode = 'connection-down'
      const compute = async () => 'computed-value'
      // No expect().rejects — just running this without try/catch verifies
      // the cache adapter swallows the ECONNREFUSED.
      const v = await cacheGetOrCompute('planner', buildKey('planner', { x: 1 }), 60, compute)
      expect(v).toBe('computed-value')
    })

    it('cacheSet failure does not abort the request (fire-and-forget)', async () => {
      // Warm the client, then drop the connection so set fails.
      await cacheSet('planner', buildKey('planner', { warm: 1 }), 'init', { ttlSeconds: 10 })
      chaos.mode = 'connection-down'

      const events: CacheMetricsEvent[] = []
      setCacheMetricsSink((ev) => events.push(ev))

      // This MUST resolve — even though the underlying SET will throw.
      await expect(
        cacheSet('planner', buildKey('planner', { q: 'x' }), 'fresh', { ttlSeconds: 10 }),
      ).resolves.toBeUndefined()
      expect(events.some((e) => e.outcome === 'error')).toBe(true)
    })

    it('invalidateNamespace returns 0 (not throws) when Redis is unreachable', async () => {
      await cacheSet('planner', buildKey('planner', { warm: 1 }), 'init', { ttlSeconds: 10 })
      chaos.mode = 'connection-down'
      const n = await invalidateNamespace('planner')
      expect(n).toBe(0)
    })
  })

  // ──────────────────────────────────────────────────────────────────────────
  // AC.3 timeout — commandTimeout fires
  // ──────────────────────────────────────────────────────────────────────────

  describe('Redis command timeout', () => {
    it('cacheGetOrCompute falls back to compute on GET timeout', async () => {
      chaos.mode = 'timeout'
      const compute = vi.fn().mockResolvedValueOnce(['signal-1', 'signal-2'])
      const result = await cacheGetOrCompute(
        'retrieval-bundle',
        buildKey('retrieval-bundle', { tool: 'msr' }),
        60,
        compute,
      )
      expect(result).toEqual(['signal-1', 'signal-2'])
      expect(compute).toHaveBeenCalledTimes(1)
    })
  })

  // ──────────────────────────────────────────────────────────────────────────
  // AC.3 corruption — malformed JSON in the cache slot
  // ──────────────────────────────────────────────────────────────────────────

  describe('Cache slot returns corrupted (non-JSON) payload', () => {
    it('parse error is swallowed → compute runs → caller gets fresh value', async () => {
      chaos.mode = 'corrupted'
      const compute = vi.fn().mockResolvedValueOnce({ valid: true })
      const r = await cacheGetOrCompute(
        'planner',
        buildKey('planner', { q: 'bad' }),
        60,
        compute,
      )
      expect(r).toEqual({ valid: true })
      expect(compute).toHaveBeenCalledTimes(1)
    })

    it('logs the JSON parse failure as an error metric', async () => {
      chaos.mode = 'corrupted'
      const events: CacheMetricsEvent[] = []
      setCacheMetricsSink((ev) => events.push(ev))
      await cacheGet('planner', buildKey('planner', { q: 'corrupt' }))
      expect(events.some((e) => e.outcome === 'error')).toBe(true)
    })
  })

  // ──────────────────────────────────────────────────────────────────────────
  // AC.3 mid-flight failure — Redis dies between set and read in same request
  // ──────────────────────────────────────────────────────────────────────────

  describe('Mid-request connection drop (ECONNRESET after first op)', () => {
    it('initial GET succeeds, subsequent SET fails — caller still receives compute result', async () => {
      // First op (the cacheGet inside cacheGetOrCompute) succeeds (miss → null),
      // then the fire-and-forget set blows up. Caller MUST still get the compute
      // value — it does not depend on the write succeeding.
      chaos.mode = 'partial-failure'
      chaos.flipAfter = 1
      const compute = vi.fn().mockResolvedValueOnce({ ok: true })
      const r = await cacheGetOrCompute(
        'active-charts',
        buildKey('active-charts', { variant: 'top50' }),
        60,
        compute,
      )
      expect(r).toEqual({ ok: true })
      expect(compute).toHaveBeenCalledTimes(1)
    })
  })

  // ──────────────────────────────────────────────────────────────────────────
  // AC.3 — system stays correct under sustained chaos (10 calls, mixed modes)
  // ──────────────────────────────────────────────────────────────────────────

  describe('Sustained chaos — 10 calls under rotating failure modes', () => {
    it('every call returns the correct compute output regardless of Redis state', async () => {
      const modes: Array<typeof chaos.mode> = [
        'healthy',
        'connection-down',
        'flushed',
        'timeout',
        'corrupted',
        'connection-down',
        'healthy',
        'flushed',
        'timeout',
        'healthy',
      ]
      const expected = Array.from({ length: 10 }, (_, i) => ({ call: i }))
      const results: unknown[] = []

      for (let i = 0; i < 10; i++) {
        chaos.mode = modes[i]
        const compute = vi.fn().mockResolvedValueOnce({ call: i })
        const r = await cacheGetOrCompute(
          'retrieval-bundle',
          // Distinct key each call so the cache layer can't accidentally
          // serve a stale value across iterations.
          buildKey('retrieval-bundle', { chart: 'c-1', call: i }),
          60,
          compute,
        )
        results.push(r)
      }

      expect(results).toEqual(expected)
    })
  })
})
