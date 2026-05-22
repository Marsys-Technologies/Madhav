/**
 * auth_cache.test.ts — F.5 acceptance: in-memory Bearer validation cache.
 *
 * Asserts that 100 sequential validations with the same key produce ≥95 cache hits
 * (first call is a miss + platform roundtrip; subsequent 99 are cache hits).
 *
 * MCPT v3.1.0-S1 AC.S1.5
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// We mock the global fetch so no real network call is made
const mockFetchResponse = {
  ok: true,
  json: async () => ({
    valid: true,
    user_uid: 'test-uid-001',
    audience_tier: 'acharya_reviewer',
    key_id: 'key-test-001',
  }),
}

// Set up before importing the module so the mock is in place
const mockFetch = vi.fn().mockResolvedValue(mockFetchResponse)
vi.stubGlobal('fetch', mockFetch)

import { validateMcpKeyFromHeader, _testClearCache, _testGetCacheSize } from '../src/auth.js'

describe('F.5 — Bearer validation cache', () => {
  beforeEach(() => {
    _testClearCache()
    mockFetch.mockClear()
  })

  afterEach(() => {
    _testClearCache()
  })

  it('first call hits platform; subsequent calls are cache hits', async () => {
    const header = 'Bearer mcp_test_key_abc123'
    const N = 100

    let fetchCallCount = 0
    let principalCount = 0

    for (let i = 0; i < N; i++) {
      const principal = await validateMcpKeyFromHeader(header)
      if (principal) principalCount++
      fetchCallCount = mockFetch.mock.calls.length
    }

    // All 100 calls must return a valid principal
    expect(principalCount).toBe(N)

    // Platform should be called exactly once (first call is a miss)
    expect(fetchCallCount).toBe(1)

    // Cache hit rate = (N - 1) / N = 99% ≥ 95%
    const cacheHitRate = (N - fetchCallCount) / N
    expect(cacheHitRate).toBeGreaterThanOrEqual(0.95)
  })

  it('cache returns the same principal on repeated calls', async () => {
    const header = 'Bearer mcp_test_key_xyz789'
    const first = await validateMcpKeyFromHeader(header)
    const second = await validateMcpKeyFromHeader(header)
    const third = await validateMcpKeyFromHeader(header)

    expect(first).not.toBeNull()
    expect(second).toEqual(first)
    expect(third).toEqual(first)

    // Only one fetch
    expect(mockFetch.mock.calls.length).toBe(1)
  })

  it('different tokens get separate cache entries', async () => {
    const headerA = 'Bearer mcp_key_alpha'
    const headerB = 'Bearer mcp_key_beta'

    await validateMcpKeyFromHeader(headerA)
    await validateMcpKeyFromHeader(headerB)

    // Both should have gone to the platform
    expect(mockFetch.mock.calls.length).toBe(2)

    // Second call on each should be cached
    await validateMcpKeyFromHeader(headerA)
    await validateMcpKeyFromHeader(headerB)
    expect(mockFetch.mock.calls.length).toBe(2) // still 2, no new calls
  })

  it('null header does not populate cache', async () => {
    const result = await validateMcpKeyFromHeader(undefined)
    expect(result).toBeNull()
    expect(mockFetch.mock.calls.length).toBe(0)
    expect(_testGetCacheSize()).toBe(0)
  })

  it('failed validation does not populate cache', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ valid: false }),
    })

    const result = await validateMcpKeyFromHeader('Bearer mcp_bad_key')
    expect(result).toBeNull()
    expect(_testGetCacheSize()).toBe(0)

    // Second call with same header should hit platform again (not cached)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        valid: true,
        user_uid: 'uid-2',
        audience_tier: 'client',
        key_id: 'key-2',
      }),
    })
    const result2 = await validateMcpKeyFromHeader('Bearer mcp_bad_key')
    expect(result2).not.toBeNull()
    expect(mockFetch.mock.calls.length).toBe(2)
  })
})
