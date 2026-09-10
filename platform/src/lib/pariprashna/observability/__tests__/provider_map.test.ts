/**
 * lane P2-E — provider_map.ts. Proves the ONE real hazard this module exists
 * to prevent: writing a `StackId` straight into `llm_usage_events.provider`
 * would violate the CHECK constraint for 'google' and 'nvidia'.
 */
import { describe, it, expect } from 'vitest'

import { mapStackIdToProviderName } from '../provider_map'

// The exact vocabulary `llm_usage_events_provider_check` (migration 001) allows.
const LLM_USAGE_EVENTS_PROVIDER_CHECK = new Set([
  'anthropic',
  'openai',
  'gemini',
  'deepseek',
  'nim',
])

describe('mapStackIdToProviderName', () => {
  it('maps every StackId to a value the llm_usage_events CHECK constraint accepts', () => {
    const stackIds = ['anthropic', 'google', 'openai', 'deepseek', 'nvidia'] as const
    for (const id of stackIds) {
      expect(LLM_USAGE_EVENTS_PROVIDER_CHECK.has(mapStackIdToProviderName(id))).toBe(true)
    }
  })

  it('translates the two names that actually disagree', () => {
    expect(mapStackIdToProviderName('google')).toBe('gemini')
    expect(mapStackIdToProviderName('nvidia')).toBe('nim')
  })

  it('leaves the three names that already agree untouched', () => {
    expect(mapStackIdToProviderName('anthropic')).toBe('anthropic')
    expect(mapStackIdToProviderName('openai')).toBe('openai')
    expect(mapStackIdToProviderName('deepseek')).toBe('deepseek')
  })
})
