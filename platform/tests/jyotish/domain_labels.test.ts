import { describe, expect, it, beforeEach } from 'vitest'
import {
  ASSET_LABELS,
  QUERY_CLASS_LABELS,
  PIPELINE_STEP_NARRATION,
  formatTechnicalTag,
  labelFor,
  containsBannedToken,
  BANNED_INTERNAL_TOKENS,
  __resetMissCacheForTests,
} from '@/lib/jyotish/domain_labels'

describe('domain_labels — translation surface', () => {
  beforeEach(() => __resetMissCacheForTests())

  it('every ASSET_LABELS value is non-empty and free of internal jargon', () => {
    for (const [key, label] of Object.entries(ASSET_LABELS)) {
      expect(label.length).toBeGreaterThan(0)
      expect(containsBannedToken(label), `asset ${key} leaks: ${label}`).toBeNull()
    }
  })

  it('every QUERY_CLASS_LABELS value is non-empty', () => {
    for (const [k, v] of Object.entries(QUERY_CLASS_LABELS)) {
      expect(v.length, k).toBeGreaterThan(0)
    }
  })

  it('every PIPELINE_STEP_NARRATION value is jargon-free', () => {
    for (const [step, narration] of Object.entries(PIPELINE_STEP_NARRATION)) {
      expect(narration.length, step).toBeGreaterThan(0)
      expect(containsBannedToken(narration), `step ${step} leaks: ${narration}`).toBeNull()
    }
  })

  it('formatTechnicalTag produces compact strings', () => {
    expect(formatTechnicalTag('vector_score', 0.87)).toBe('≈0.87 cosine')
    expect(formatTechnicalTag('graph_depth', 2)).toBe('depth 2')
    expect(formatTechnicalTag('latency', 12345)).toBe('12.3s')
    expect(formatTechnicalTag('latency', 250)).toBe('250ms')
    expect(formatTechnicalTag('token_count', 1234)).toMatch(/1,?234 tokens/)
    expect(formatTechnicalTag('cache_hit', 1)).toBe('cache hit')
    expect(formatTechnicalTag('cost_usd', 0.0123)).toBe('$0.0123')
  })

  it('labelFor returns mapped value when key present', () => {
    expect(labelFor('asset', 'MSR')).toBe('Astrological Signals')
    expect(labelFor('class', 'predictive')).toBe('Predictive')
    expect(labelFor('step', 'vector_search')).toBe('Searching classical sources')
  })

  it('labelFor falls back gracefully on unknown keys', () => {
    expect(labelFor('asset', 'UNKNOWN_ASSET')).toBe('UNKNOWN_ASSET')
    expect(labelFor('step', 'new_step_name')).toBe('New Step Name')
  })

  it('BANNED_INTERNAL_TOKENS covers the core internal IDs', () => {
    expect(BANNED_INTERNAL_TOKENS).toContain('MSR')
    expect(BANNED_INTERNAL_TOKENS).toContain('FORENSIC')
    expect(BANNED_INTERNAL_TOKENS).toContain('CGM')
    expect(BANNED_INTERNAL_TOKENS).toContain('pgvector')
    expect(BANNED_INTERNAL_TOKENS).toContain('embedding')
  })
})
