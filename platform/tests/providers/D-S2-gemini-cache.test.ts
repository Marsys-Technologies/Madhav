/**
 * D-S2: D-S2-gemini-cache.test.ts
 *
 * Tests for Google cachedContent API integration (R11.D).
 *
 * AC1: cache() returns cached_content_api mode.
 * AC2: cachedContent TTL and minTokens are in providerPayload.
 * AC3: buildCacheCreatePayload generates correct SDK payload shape.
 * AC4: extractGeminiCacheMetrics handles hit/miss/absent correctly.
 */

import { describe, it, expect } from 'vitest'
import { GOOGLE_MANIFEST } from '../../src/lib/providers/google/manifest'
import { GoogleAdapter } from '../../src/lib/providers/google/adapter'
import type { CacheRequest } from '../../src/lib/providers/types'
import {
  buildCacheCreatePayload,
  extractGeminiCacheMetrics,
  buildGeminiCacheMetricsRecord,
  GEMINI_CACHE_TTL_SECONDS,
  GEMINI_CACHE_MIN_TOKENS,
} from '../../src/lib/providers/google/cached_content'

// ---------------------------------------------------------------------------
// Manifest
// ---------------------------------------------------------------------------

describe('D-S2: Google manifest — cached_content_api', () => {
  it('manifest declares cached_content_api', () => {
    expect(GOOGLE_MANIFEST.promptCaching).toBe('cached_content_api')
  })
})

// ---------------------------------------------------------------------------
// GoogleAdapter.cache()
// ---------------------------------------------------------------------------

describe('D-S2: GoogleAdapter.cache()', () => {
  const adapter = new GoogleAdapter()

  it('returns cached_content_api mode', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.mode).toBe('cached_content_api')
  })

  it('providerPayload has ttlSeconds=600', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.providerPayload?.ttlSeconds).toBe(600)
  })

  it('providerPayload has minTokensForCache=32768', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.providerPayload?.minTokensForCache).toBe(32768)
  })

  it('providerPayload.usageField is cachedContentTokenCount', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.providerPayload?.usageField).toBe('cachedContentTokenCount')
  })

  it('providerPayload.sdkMethod references genai.caches.create', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.providerPayload?.sdkMethod).toBe('genai.caches.create')
  })
})

// ---------------------------------------------------------------------------
// buildCacheCreatePayload
// ---------------------------------------------------------------------------

describe('D-S2: buildCacheCreatePayload', () => {
  it('sets model on payload', () => {
    const payload = buildCacheCreatePayload({
      model: 'gemini-2.5-pro',
    })
    expect(payload.model).toBe('gemini-2.5-pro')
  })

  it('defaults ttl to 600s', () => {
    const payload = buildCacheCreatePayload({ model: 'gemini-2.5-pro' })
    expect(payload.ttl).toBe(`${GEMINI_CACHE_TTL_SECONDS}s`)
  })

  it('accepts custom ttl override', () => {
    const payload = buildCacheCreatePayload({ model: 'gemini-2.5-pro', ttl: '300s' })
    expect(payload.ttl).toBe('300s')
  })

  it('places systemPrompt in systemInstruction.parts', () => {
    const payload = buildCacheCreatePayload({
      model: 'gemini-2.5-pro',
      systemPrompt: 'You are a Jyotish instrument.',
    })
    expect(payload.systemInstruction?.parts[0].text).toBe('You are a Jyotish instrument.')
  })

  it('places ragBundle as user-role contents entry', () => {
    const payload = buildCacheCreatePayload({
      model: 'gemini-2.5-pro',
      ragBundle: 'Retrieved signals bundle.',
    })
    expect(payload.contents?.[0].role).toBe('user')
    expect(payload.contents?.[0].parts[0].text).toBe('Retrieved signals bundle.')
  })

  it('omits systemInstruction when systemPrompt is absent', () => {
    const payload = buildCacheCreatePayload({ model: 'gemini-2.5-pro', ragBundle: 'rag' })
    expect(payload.systemInstruction).toBeUndefined()
  })

  it('omits contents when ragBundle is absent', () => {
    const payload = buildCacheCreatePayload({ model: 'gemini-2.5-pro', systemPrompt: 'sys' })
    expect(payload.contents).toBeUndefined()
  })

  it('includes both systemInstruction + contents when both provided', () => {
    const payload = buildCacheCreatePayload({
      model: 'gemini-2.5-pro',
      systemPrompt: 'sys',
      ragBundle: 'rag',
    })
    expect(payload.systemInstruction).toBeDefined()
    expect(payload.contents).toHaveLength(1)
  })

  it('sets displayName to marsys-synthesis-cache', () => {
    const payload = buildCacheCreatePayload({ model: 'gemini-2.5-pro' })
    expect(payload.displayName).toBe('marsys-synthesis-cache')
  })
})

// ---------------------------------------------------------------------------
// extractGeminiCacheMetrics
// ---------------------------------------------------------------------------

describe('D-S2: extractGeminiCacheMetrics', () => {
  it('returns null when usageMetadata is undefined', () => {
    expect(extractGeminiCacheMetrics(undefined)).toBeNull()
  })

  it('returns null when cachedContentTokenCount is 0', () => {
    expect(extractGeminiCacheMetrics({ cachedContentTokenCount: 0 })).toBeNull()
  })

  it('returns null when cachedContentTokenCount is absent', () => {
    expect(extractGeminiCacheMetrics({ promptTokenCount: 1000 })).toBeNull()
  })

  it('returns metrics when cachedContentTokenCount > 0', () => {
    const result = extractGeminiCacheMetrics({
      cachedContentTokenCount: 8000,
      promptTokenCount: 10000,
      candidatesTokenCount: 500,
    })
    expect(result).not.toBeNull()
    expect(result?.cachedContentTokenCount).toBe(8000)
    expect(result?.promptTokenCount).toBe(10000)
  })

  it('defaults promptTokenCount to 0 if absent', () => {
    const result = extractGeminiCacheMetrics({ cachedContentTokenCount: 100 })
    expect(result?.promptTokenCount).toBe(0)
  })
})

// ---------------------------------------------------------------------------
// buildGeminiCacheMetricsRecord
// ---------------------------------------------------------------------------

describe('D-S2: buildGeminiCacheMetricsRecord', () => {
  it('marsys_event_type is gemini_cache_metrics', () => {
    const record = buildGeminiCacheMetricsRecord({
      model: 'gemini-2.5-pro',
      cachedContentName: 'cachedContents/abc123',
      metrics: { cachedContentTokenCount: 8000, promptTokenCount: 10000, candidatesTokenCount: 500 },
    })
    expect(record.marsys_event_type).toBe('gemini_cache_metrics')
  })

  it('cacheHitRatio is 0.8 for 8000/10000', () => {
    const record = buildGeminiCacheMetricsRecord({
      model: 'gemini-2.5-pro',
      cachedContentName: 'cachedContents/abc123',
      metrics: { cachedContentTokenCount: 8000, promptTokenCount: 10000, candidatesTokenCount: 500 },
    })
    expect(record.cacheHitRatio).toBeCloseTo(0.8)
  })

  it('estimatedCostSavingsRatio is 0.75 × hitRatio', () => {
    const record = buildGeminiCacheMetricsRecord({
      model: 'gemini-2.5-pro',
      cachedContentName: 'cachedContents/abc123',
      metrics: { cachedContentTokenCount: 8000, promptTokenCount: 10000, candidatesTokenCount: 500 },
    })
    expect(record.estimatedCostSavingsRatio).toBeCloseTo(0.75 * 0.8)
  })

  it('cacheHitRatio is 0 when promptTokenCount is 0 (no division error)', () => {
    const record = buildGeminiCacheMetricsRecord({
      model: 'gemini-2.5-pro',
      cachedContentName: 'cachedContents/abc123',
      metrics: { cachedContentTokenCount: 100, promptTokenCount: 0, candidatesTokenCount: 50 },
    })
    expect(record.cacheHitRatio).toBe(0)
  })
})

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

describe('D-S2: constants', () => {
  it('GEMINI_CACHE_TTL_SECONDS is 600', () => {
    expect(GEMINI_CACHE_TTL_SECONDS).toBe(600)
  })

  it('GEMINI_CACHE_MIN_TOKENS is 32768', () => {
    expect(GEMINI_CACHE_MIN_TOKENS).toBe(32768)
  })
})
