/**
 * D-S4: D-S4-deepseek-cache.test.ts
 *
 * Tests for DeepSeek implicit cache telemetry (R11.D).
 *
 * AC1: DeepSeek adapter's cache() returns 'implicit' mode (no markers).
 * AC2: providerPayload references prompt_cache_hit_tokens field path.
 * AC3: NVIDIA manifest declares null (confirmed no caching).
 */

import { describe, it, expect } from 'vitest'
import { DEEPSEEK_MANIFEST } from '../../src/lib/providers/deepseek/manifest'
import { NVIDIA_MANIFEST } from '../../src/lib/providers/nvidia/manifest'
import { DeepSeekAdapter } from '../../src/lib/providers/deepseek/adapter'
import type { CacheRequest } from '../../src/lib/providers/types'

describe('D-S4: DeepSeek manifest — implicit caching', () => {
  it('manifest declares implicit', () => {
    expect(DEEPSEEK_MANIFEST.promptCaching).toBe('implicit')
  })
})

describe('D-S4: NVIDIA manifest — null caching (AC3)', () => {
  it('NVIDIA manifest has null promptCaching', () => {
    expect(NVIDIA_MANIFEST.promptCaching).toBeNull()
  })
})

describe('D-S4: DeepSeekAdapter.cache()', () => {
  const adapter = new DeepSeekAdapter()

  it('returns implicit mode', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.mode).toBe('implicit')
  })

  it('breakpointPositions is empty (no explicit markers)', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.breakpointPositions).toHaveLength(0)
  })

  it('providerPayload references prompt_cache_hit_tokens', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.providerPayload?.prompt_cache_hit_tokens).toBe('usage.prompt_cache_hit_tokens')
  })

  it('providerPayload also references prompt_cache_miss_tokens', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.providerPayload?.prompt_cache_miss_tokens).toBe('usage.prompt_cache_miss_tokens')
  })

  it('cachedTokenCostFraction is a fraction < 1 (cheaper than standard)', () => {
    const result = adapter.cache({} as CacheRequest)
    const frac = result.providerPayload?.cachedTokenCostFraction as number
    expect(frac).toBeGreaterThan(0)
    expect(frac).toBeLessThan(1)
  })
})
