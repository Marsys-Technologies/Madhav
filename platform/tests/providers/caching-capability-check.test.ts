/**
 * D-S0: caching-capability-check.test.ts
 *
 * R11.D entry-point. Verifies all 5 provider manifests correctly declare
 * their prompt caching strategy per CAPABILITY_MATRIX §9.
 *
 * Expected manifest values:
 *   - Anthropic: 'explicit_4bp'    — up to 4 cache_control breakpoints (5-min/1-hour TTL)
 *   - Google:    'cached_content_api' — separate cachedContent API call (TTL configurable)
 *   - OpenAI:    'automatic'       — automatic caching (default on, 25% hit cost)
 *   - DeepSeek:  'implicit'        — prompt_cache_hit_tokens in usage response
 *   - NVIDIA:    null              — not supported in Marsys baseline NIM config
 */

import { describe, it, expect } from 'vitest'
import { ANTHROPIC_MANIFEST } from '../../src/lib/providers/anthropic/manifest'
import { GOOGLE_MANIFEST } from '../../src/lib/providers/google/manifest'
import { OPENAI_MANIFEST } from '../../src/lib/providers/openai/manifest'
import { DEEPSEEK_MANIFEST } from '../../src/lib/providers/deepseek/manifest'
import { NVIDIA_MANIFEST } from '../../src/lib/providers/nvidia/manifest'
import { getAllManifests } from '../../src/lib/providers/dispatcher'

// ---------------------------------------------------------------------------
// Per-provider promptCaching declarations
// ---------------------------------------------------------------------------

describe('D-S0: promptCaching — per-provider manifest values', () => {
  it('Anthropic uses explicit_4bp (up to 4 cache_control breakpoints)', () => {
    expect(ANTHROPIC_MANIFEST.promptCaching).toBe('explicit_4bp')
  })

  it('Google uses cached_content_api (separate cachedContent API call)', () => {
    expect(GOOGLE_MANIFEST.promptCaching).toBe('cached_content_api')
  })

  it('OpenAI uses automatic (no explicit breakpoints; 25% hit cost)', () => {
    expect(OPENAI_MANIFEST.promptCaching).toBe('automatic')
  })

  it('DeepSeek uses implicit (prompt_cache_hit_tokens in usage)', () => {
    expect(DEEPSEEK_MANIFEST.promptCaching).toBe('implicit')
  })

  it('NVIDIA has null promptCaching (not supported in Marsys NIM baseline)', () => {
    expect(NVIDIA_MANIFEST.promptCaching).toBeNull()
  })
})

// ---------------------------------------------------------------------------
// Coverage via getAllManifests()
// ---------------------------------------------------------------------------

describe('D-S0: getAllManifests() caching coverage', () => {
  const all = getAllManifests()

  it('all 5 manifests declare promptCaching (non-undefined)', () => {
    for (const [provider, manifest] of Object.entries(all)) {
      expect(manifest.promptCaching, `${provider}.promptCaching`).toBeDefined()
      // null is acceptable (NVIDIA) — undefined is not
      expect(typeof manifest.promptCaching !== 'undefined', `${provider}.promptCaching defined`).toBe(true)
    }
  })

  it('exactly 1 provider uses explicit_4bp (Anthropic only)', () => {
    const explicit4bp = Object.entries(all)
      .filter(([, m]) => m.promptCaching === 'explicit_4bp')
      .map(([id]) => id)
    expect(explicit4bp).toEqual(['anthropic'])
  })

  it('exactly 1 provider uses cached_content_api (Google only)', () => {
    const cachedContent = Object.entries(all)
      .filter(([, m]) => m.promptCaching === 'cached_content_api')
      .map(([id]) => id)
    expect(cachedContent).toEqual(['google'])
  })

  it('exactly 1 provider uses automatic (OpenAI only)', () => {
    const automatic = Object.entries(all)
      .filter(([, m]) => m.promptCaching === 'automatic')
      .map(([id]) => id)
    expect(automatic).toEqual(['openai'])
  })

  it('exactly 1 provider uses implicit (DeepSeek only)', () => {
    const implicit = Object.entries(all)
      .filter(([, m]) => m.promptCaching === 'implicit')
      .map(([id]) => id)
    expect(implicit).toEqual(['deepseek'])
  })

  it('NVIDIA is the only provider with null promptCaching', () => {
    const nullCaching = Object.entries(all)
      .filter(([, m]) => m.promptCaching === null)
      .map(([id]) => id)
    expect(nullCaching).toEqual(['nvidia'])
  })
})

// ---------------------------------------------------------------------------
// Cross-invariant: providers with native thinking support SHOULD have caching
// ---------------------------------------------------------------------------

describe('D-S0: thinking+caching co-occurrence invariant', () => {
  const all = getAllManifests()

  it('native thinking providers (Anthropic/Google) both have caching', () => {
    const nativeThinking = Object.entries(all)
      .filter(([, m]) => m.extendedThinking === 'native_effort' || m.extendedThinking === 'native_budget')
    for (const [provider, manifest] of nativeThinking) {
      expect(manifest.promptCaching, `${provider}: native thinking → has caching`).not.toBeNull()
    }
  })
})
