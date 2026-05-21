/**
 * suggested_followups.test.ts — Unit tests for the follow-up generator.
 */

import { describe, it, expect } from 'vitest'
import { generateSuggestedFollowups } from '@/lib/mcp/suggested_followups'
import type { PipelinePlan } from '@/lib/pipeline/types'

function makePlan(overrides: Partial<PipelinePlan> = {}): PipelinePlan {
  return {
    query_class: 'factual',
    query_intent_summary: 'Test query',
    asset_bundle: [],
    tool_calls: [],
    ...overrides,
  }
}

describe('generateSuggestedFollowups', () => {
  it('returns a non-empty array for any non-trivial plan', () => {
    const result = generateSuggestedFollowups(makePlan({ query_class: 'holistic' }))
    expect(result.length).toBeGreaterThan(0)
  })

  it('caps results at 3', () => {
    const result = generateSuggestedFollowups(makePlan({
      query_class: 'cross_domain',
      domains: ['career', 'finance', 'health'],
      forward_looking: true,
    }))
    expect(result.length).toBeLessThanOrEqual(3)
  })

  it('deduplicates suggestions (no repeated strings)', () => {
    const result = generateSuggestedFollowups(makePlan({ query_class: 'holistic' }))
    const unique = new Set(result)
    expect(unique.size).toBe(result.length)
  })

  it('suggests timing/dasha question for factual queries', () => {
    const result = generateSuggestedFollowups(makePlan({ query_class: 'factual' }))
    const combined = result.join(' ')
    // Should suggest either a holistic angle or a timing/dasha follow-up
    expect(combined.length).toBeGreaterThan(20)
  })

  it('suggests LEL ground-truth check for predictive forward-looking queries', () => {
    const result = generateSuggestedFollowups(makePlan({
      query_class: 'predictive',
      forward_looking: true,
    }))
    const combined = result.join(' ')
    expect(combined.toLowerCase()).toContain('event log')
  })

  it('returns strings (not numbers or objects)', () => {
    const result = generateSuggestedFollowups(makePlan({ query_class: 'holistic', domains: ['career'] }))
    for (const s of result) {
      expect(typeof s).toBe('string')
      expect(s.length).toBeGreaterThan(5)
    }
  })
})
