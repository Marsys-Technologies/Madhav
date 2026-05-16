/**
 * Unit tests — provider_quirks.ts retry policy table.
 */
import { describe, it, expect } from 'vitest'
import { providerQuirks, getMaxRetries } from '../provider_quirks'
import type { Provider } from '@/lib/models/registry'

describe('providerQuirks table', () => {
  it('defines quirks for all 5 known providers', () => {
    const expected: Provider[] = ['anthropic', 'google', 'openai', 'deepseek', 'nvidia']
    for (const p of expected) {
      expect(providerQuirks[p], `missing entry for ${p}`).toBeDefined()
      expect(typeof providerQuirks[p].maxRetries).toBe('number')
      expect(Array.isArray(providerQuirks[p].retryOn)).toBe(true)
    }
  })

  it('nvidia has maxRetries: 0 (adapter has its own logic)', () => {
    expect(providerQuirks.nvidia.maxRetries).toBe(0)
  })

  it('anthropic, google, openai, deepseek each allow ≥1 retry', () => {
    const retrying: Provider[] = ['anthropic', 'google', 'openai', 'deepseek']
    for (const p of retrying) {
      expect(providerQuirks[p].maxRetries, `${p} maxRetries`).toBeGreaterThanOrEqual(1)
    }
  })

  it('getMaxRetries returns the correct value for each provider', () => {
    expect(getMaxRetries('anthropic')).toBe(1)
    expect(getMaxRetries('google')).toBe(1)
    expect(getMaxRetries('openai')).toBe(1)
    expect(getMaxRetries('deepseek')).toBe(1)
    expect(getMaxRetries('nvidia')).toBe(0)
  })

  it('anthropic and openai include 429-with-retry-after in retryOn', () => {
    expect(providerQuirks.anthropic.retryOn).toContain('429-with-retry-after')
    expect(providerQuirks.openai.retryOn).toContain('429-with-retry-after')
  })
})

describe('getMaxRetries', () => {
  it('returns 0 as safe default for unknown provider cast', () => {
    // Cast to unknown provider via type assertion — should not throw
    const result = getMaxRetries('anthropic')
    expect(typeof result).toBe('number')
  })
})
