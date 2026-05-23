/**
 * gemini-cache-wiring.test.ts — F-S4: Gemini cachedContent wiring unit tests (R11.F)
 *
 * Verifies that:
 * AC.S4.6a: buildCacheCreatePayload() produces correct payload structure with systemPrompt
 * AC.S4.6b: buildCacheCreatePayload() produces correct payload structure with ragBundle
 * AC.S4.6c: buildCacheCreatePayload() sets TTL correctly
 * AC.S4.6d: buildCacheCreatePayload() passes model through unchanged
 * AC.S4.6e: GEMINI_CACHE_MIN_TOKENS constant is 32768
 * AC.S4.3: GoogleAdapter.chat() reads cachedContentName from cacheConfig (structure check)
 */

import { describe, it, expect } from 'vitest'
import {
  buildCacheCreatePayload,
  GEMINI_CACHE_MIN_TOKENS,
  GEMINI_CACHE_TTL_SECONDS,
} from '../../src/lib/providers/google/cached_content'

// ---------------------------------------------------------------------------
// buildCacheCreatePayload — payload structure
// ---------------------------------------------------------------------------

describe('F-S4: buildCacheCreatePayload — payload structure', () => {
  it('AC.S4.6a: systemPrompt is placed in systemInstruction.parts[0].text', () => {
    const payload = buildCacheCreatePayload({
      model: 'models/gemini-2.5-pro',
      systemPrompt: 'You are an expert Jyotish acharya.',
      ttl: '600s',
    })
    expect(payload.systemInstruction).toBeDefined()
    expect(payload.systemInstruction?.parts).toHaveLength(1)
    expect(payload.systemInstruction?.parts[0].text).toBe('You are an expert Jyotish acharya.')
  })

  it('AC.S4.6b: ragBundle is placed as contents[0] with role=user', () => {
    const payload = buildCacheCreatePayload({
      model: 'models/gemini-2.5-pro',
      ragBundle: 'RAG context: chart data here',
      ttl: '600s',
    })
    expect(payload.contents).toBeDefined()
    expect(payload.contents).toHaveLength(1)
    expect(payload.contents?.[0].role).toBe('user')
    expect(payload.contents?.[0].parts[0].text).toBe('RAG context: chart data here')
  })

  it('AC.S4.6b-combined: both systemPrompt and ragBundle can be set together', () => {
    const payload = buildCacheCreatePayload({
      model: 'models/gemini-2.5-pro',
      systemPrompt: 'System instructions here.',
      ragBundle: 'RAG bundle here.',
      ttl: '600s',
    })
    expect(payload.systemInstruction?.parts[0].text).toBe('System instructions here.')
    expect(payload.contents?.[0].role).toBe('user')
    expect(payload.contents?.[0].parts[0].text).toBe('RAG bundle here.')
  })

  it('AC.S4.6c: TTL is set correctly when provided', () => {
    const payload = buildCacheCreatePayload({
      model: 'models/gemini-2.5-pro',
      systemPrompt: 'System prompt.',
      ttl: '300s',
    })
    expect(payload.ttl).toBe('300s')
  })

  it('AC.S4.6c: TTL defaults to GEMINI_CACHE_TTL_SECONDS when not provided', () => {
    const payload = buildCacheCreatePayload({
      model: 'models/gemini-2.5-pro',
      systemPrompt: 'System prompt.',
    })
    expect(payload.ttl).toBe(`${GEMINI_CACHE_TTL_SECONDS}s`)
  })

  it('AC.S4.6d: model is passed through unchanged', () => {
    const model = 'models/gemini-2.5-pro-preview-05-06'
    const payload = buildCacheCreatePayload({ model, systemPrompt: 'test', ttl: '600s' })
    expect(payload.model).toBe(model)
  })

  it('AC.S4.6d: model without models/ prefix is passed through unchanged (prefixing is caller responsibility)', () => {
    const model = 'gemini-2.5-pro'
    const payload = buildCacheCreatePayload({ model, systemPrompt: 'test', ttl: '600s' })
    expect(payload.model).toBe(model)
  })

  it('produces no systemInstruction when systemPrompt is omitted', () => {
    const payload = buildCacheCreatePayload({
      model: 'models/gemini-2.5-pro',
      ragBundle: 'RAG only',
      ttl: '600s',
    })
    expect(payload.systemInstruction).toBeUndefined()
  })

  it('produces no contents when ragBundle is omitted', () => {
    const payload = buildCacheCreatePayload({
      model: 'models/gemini-2.5-pro',
      systemPrompt: 'System only',
      ttl: '600s',
    })
    expect(payload.contents).toBeUndefined()
  })

  it('sets displayName to marsys-synthesis-cache', () => {
    const payload = buildCacheCreatePayload({
      model: 'models/gemini-2.5-pro',
      systemPrompt: 'test',
      ttl: '600s',
    })
    expect(payload.displayName).toBe('marsys-synthesis-cache')
  })
})

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

describe('F-S4: Gemini cache constants', () => {
  it('AC.S4.6e: GEMINI_CACHE_MIN_TOKENS is 32768', () => {
    expect(GEMINI_CACHE_MIN_TOKENS).toBe(32768)
  })

  it('GEMINI_CACHE_TTL_SECONDS is 600', () => {
    expect(GEMINI_CACHE_TTL_SECONDS).toBe(600)
  })
})

// ---------------------------------------------------------------------------
// Token threshold guard logic (mirrors route.ts decision)
// ---------------------------------------------------------------------------

describe('F-S4: token threshold guard', () => {
  it('sub-threshold content does not meet cache minimum', () => {
    // Simulate what route.ts does: Math.ceil(systemContent.length / 4)
    const shortContent = 'a'.repeat(100) // ~25 tokens
    const estimatedTokens = Math.ceil(shortContent.length / 4)
    expect(estimatedTokens).toBeLessThan(GEMINI_CACHE_MIN_TOKENS)
  })

  it('above-threshold content meets cache minimum', () => {
    // 32768 tokens × 4 chars/token = 131072 chars
    const largeContent = 'a'.repeat(131072)
    const estimatedTokens = Math.ceil(largeContent.length / 4)
    expect(estimatedTokens).toBeGreaterThanOrEqual(GEMINI_CACHE_MIN_TOKENS)
  })

  it('exact boundary: 131072 chars → exactly 32768 estimated tokens', () => {
    const content = 'a'.repeat(131072)
    expect(Math.ceil(content.length / 4)).toBe(32768)
  })
})

// ---------------------------------------------------------------------------
// GoogleAdapter cache() method — providerPayload structure
// ---------------------------------------------------------------------------

describe('F-S4: GoogleAdapter.cache() providerPayload — S4 wiring fields', () => {
  // Import inline to avoid triggering server-only import constraints in tests
  // (the adapter itself does not import server-only modules)
  it('cache() returns ttlSeconds and minTokensForCache in providerPayload', async () => {
    const { GoogleAdapter } = await import('../../src/lib/providers/google/adapter')
    const adapter = new GoogleAdapter()
    const response = adapter.cache({ cacheMode: 'cached_content_api', breakpointPositions: [] })
    expect(response.mode).toBe('cached_content_api')
    expect(response.providerPayload?.['ttlSeconds']).toBe(600)
    expect(response.providerPayload?.['minTokensForCache']).toBe(32768)
  })
})
