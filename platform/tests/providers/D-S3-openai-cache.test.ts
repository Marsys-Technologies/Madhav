/**
 * D-S3: D-S3-openai-cache.test.ts
 *
 * Tests for OpenAI automatic caching — telemetry capture (R11.D).
 *
 * AC1: OpenAI adapter's cache() returns 'automatic' mode (no markers added).
 * AC2: providerPayload references cached_tokens field path.
 * AC3: Manifest declares 'automatic' promptCaching.
 */

import { describe, it, expect } from 'vitest'
import { OPENAI_MANIFEST } from '../../src/lib/providers/openai/manifest'
import { OpenAIAdapter } from '../../src/lib/providers/openai/adapter'
import type { CacheRequest } from '../../src/lib/providers/types'

describe('D-S3: OpenAI manifest — automatic caching', () => {
  it('manifest declares automatic', () => {
    expect(OPENAI_MANIFEST.promptCaching).toBe('automatic')
  })
})

describe('D-S3: OpenAIAdapter.cache()', () => {
  const adapter = new OpenAIAdapter()

  it('returns automatic mode', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.mode).toBe('automatic')
  })

  it('breakpointPositions is empty (no explicit markers)', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.breakpointPositions).toHaveLength(0)
  })

  it('providerPayload references cached_tokens field path', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.providerPayload?.cached_tokens).toBe('usage.prompt_tokens_details.cached_tokens')
  })

  it('providerPayload cachedTokenCostFraction is 0.25', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.providerPayload?.cachedTokenCostFraction).toBe(0.25)
  })

  it('providerPayload requires stream_options.include_usage', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.providerPayload?.requireStreamUsage).toBe(true)
  })

  it('providerPayload minContextTokens is 1024', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.providerPayload?.minContextTokens).toBe(1024)
  })
})
