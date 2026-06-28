import { describe, it, expect, beforeEach } from 'vitest'
import { RequestScopedToolCache, createToolCache } from '../tool_cache'
import type { ToolBundle } from '../../retrieval/shared_types'

function makeBundle(overrides: Partial<ToolBundle> = {}): ToolBundle {
  return {
    tool_bundle_id: 'bundle-1',
    tool_name: 'test_tool',
    tool_version: '1.0',
    invocation_params: {},
    results: [{ content: 'test result' }],
    served_from_cache: false,
    cache_key: undefined,
    latency_ms: 5,
    result_hash: 'sha256:abc',
    schema_version: '1.0',
    ...overrides,
  }
}

describe('RequestScopedToolCache', () => {
  let cache: RequestScopedToolCache

  beforeEach(() => {
    cache = createToolCache()
  })

  describe('generateKey', () => {
    it('is deterministic for the same params in the same order', () => {
      const k1 = cache.generateKey('tool', { a: 1, b: 2 })
      const k2 = cache.generateKey('tool', { a: 1, b: 2 })
      expect(k1).toBe(k2)
    })

    it('produces the same key regardless of object key order', () => {
      const k1 = cache.generateKey('tool', { a: 1, b: 2 })
      const k2 = cache.generateKey('tool', { b: 2, a: 1 })
      expect(k1).toBe(k2)
    })

    it('produces different keys for different tool names', () => {
      const k1 = cache.generateKey('tool_a', { a: 1 })
      const k2 = cache.generateKey('tool_b', { a: 1 })
      expect(k1).not.toBe(k2)
    })

    it('produces different keys for different params', () => {
      const k1 = cache.generateKey('tool', { a: 1 })
      const k2 = cache.generateKey('tool', { a: 2 })
      expect(k1).not.toBe(k2)
    })

    it('key has format toolName:hexhash', () => {
      const key = cache.generateKey('msr_sql', { x: 1 })
      expect(key).toMatch(/^msr_sql:[0-9a-f]{64}$/)
    })
  })

  describe('get', () => {
    it('returns undefined when the cache is empty', async () => {
      const result = await cache.get('tool', { a: 1 })
      expect(result).toBeUndefined()
    })

    it('returns undefined for a key that was never put', async () => {
      cache.put('other_tool', { a: 1 }, Promise.resolve(makeBundle()))
      const result = await cache.get('tool', { a: 1 })
      expect(result).toBeUndefined()
    })
  })

  describe('put then get', () => {
    it('returns the resolved bundle after put', async () => {
      const bundle = makeBundle({ tool_bundle_id: 'bundle-xyz' })
      cache.put('tool', { x: 42 }, Promise.resolve(bundle))
      const result = await cache.get('tool', { x: 42 })
      expect(result).toEqual(bundle)
    })

    it('key order does not affect retrieval', async () => {
      const bundle = makeBundle()
      cache.put('tool', { a: 1, b: 2 }, Promise.resolve(bundle))
      const result = await cache.get('tool', { b: 2, a: 1 })
      expect(result).toEqual(bundle)
    })
  })

  describe('clear', () => {
    it('empties the map', async () => {
      cache.put('tool', { a: 1 }, Promise.resolve(makeBundle()))
      cache.put('tool', { b: 2 }, Promise.resolve(makeBundle()))
      expect(cache.size()).toBe(2)

      cache.clear()
      expect(cache.size()).toBe(0)
    })

    it('returns undefined for previously cached keys after clear', async () => {
      cache.put('tool', { a: 1 }, Promise.resolve(makeBundle()))
      cache.clear()
      const result = await cache.get('tool', { a: 1 })
      expect(result).toBeUndefined()
    })
  })

  describe('size', () => {
    it('starts at zero', () => {
      expect(cache.size()).toBe(0)
    })

    it('increments with each unique key put', () => {
      cache.put('tool', { a: 1 }, Promise.resolve(makeBundle()))
      expect(cache.size()).toBe(1)
      cache.put('tool', { a: 2 }, Promise.resolve(makeBundle()))
      expect(cache.size()).toBe(2)
    })

    it('does not increment when the same key is put twice', () => {
      cache.put('tool', { a: 1 }, Promise.resolve(makeBundle()))
      cache.put('tool', { a: 1 }, Promise.resolve(makeBundle()))
      expect(cache.size()).toBe(1)
    })
  })
})
