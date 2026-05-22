/**
 * C-S4: thinking-config.test.ts
 *
 * Tests for per-provider thinking configurations.
 * Verifies each adapter's thinking() method returns the right shape.
 */

import { describe, it, expect, vi } from 'vitest'
import { AnthropicAdapter } from '../../src/lib/providers/anthropic/adapter'
import { GoogleAdapter } from '../../src/lib/providers/google/adapter'
import { OpenAIAdapter } from '../../src/lib/providers/openai/adapter'
import { DeepSeekAdapter } from '../../src/lib/providers/deepseek/adapter'
import { NVIDIAAdapter } from '../../src/lib/providers/nvidia/adapter'

// ---------------------------------------------------------------------------
// Mock server-only + observatory + migration-adapter
// ---------------------------------------------------------------------------
vi.mock('server-only', () => ({}))
vi.mock('../../src/lib/observatory/capability_telemetry', () => ({
  logCapabilityPath: vi.fn(),
}))
vi.mock('../../src/lib/providers/migration-adapter', () => ({
  migrationAdapter: {
    stubChat: vi.fn(async function* () { yield { type: 'message_stop', stopReason: 'end_turn' } }),
  },
}))

// ---------------------------------------------------------------------------
// Anthropic — native_effort
// ---------------------------------------------------------------------------

describe('C-S4: AnthropicAdapter.thinking()', () => {
  const adapter = new AnthropicAdapter()

  it('returns mode=native_effort', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_effort' })
    expect(result.mode).toBe('native_effort')
  })

  it('defaults to effort=medium', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_effort' })
    expect(result.effort).toBe('medium')
  })

  it('passes through effort=low', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_effort', effort: 'low' })
    expect(result.effort).toBe('low')
  })

  it('passes through effort=high', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_effort', effort: 'high' })
    expect(result.effort).toBe('high')
  })

  it('providerPayload.thinking has type=enabled + effort', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_effort', effort: 'medium' })
    const payload = result.providerPayload?.thinking as Record<string, unknown>
    expect(payload?.type).toBe('enabled')
    expect(payload?.effort).toBe('medium')
  })

  it('budgetTokens default for medium is 8192', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_effort', effort: 'medium' })
    expect(result.budgetTokens).toBe(8192)
  })

  it('budgetTokens default for low is 1024', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_effort', effort: 'low' })
    expect(result.budgetTokens).toBe(1024)
  })

  it('budgetTokens default for high is 32768', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_effort', effort: 'high' })
    expect(result.budgetTokens).toBe(32768)
  })

  it('respects explicit budgetTokens override', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_effort', budgetTokens: 4096 })
    expect(result.budgetTokens).toBe(4096)
  })
})

// ---------------------------------------------------------------------------
// Google — native_budget
// ---------------------------------------------------------------------------

describe('C-S4: GoogleAdapter.thinking()', () => {
  const adapter = new GoogleAdapter()

  it('returns mode=native_budget', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_budget' })
    expect(result.mode).toBe('native_budget')
  })

  it('default budgetTokens is 24576 (registry value preserved)', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_budget' })
    expect(result.budgetTokens).toBe(24576)
  })

  it('providerPayload.thinkingConfig has thinkingBudget', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_budget' })
    const payload = result.providerPayload?.thinkingConfig as Record<string, unknown>
    expect(payload?.thinkingBudget).toBe(24576)
  })

  it('effort=high maps to budgetTokens=32768', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_budget', effort: 'high' })
    expect(result.budgetTokens).toBe(32768)
  })

  it('effort=low maps to budgetTokens=8192', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_budget', effort: 'low' })
    expect(result.budgetTokens).toBe(8192)
  })

  it('explicit budgetTokens override respected', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'native_budget', budgetTokens: 16384 })
    expect(result.budgetTokens).toBe(16384)
  })
})

// ---------------------------------------------------------------------------
// OpenAI — polyfill_cot
// ---------------------------------------------------------------------------

describe('C-S4: OpenAIAdapter.thinking()', () => {
  const adapter = new OpenAIAdapter()

  it('returns mode=polyfill_cot', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'polyfill_cot' })
    expect(result.mode).toBe('polyfill_cot')
  })

  it('providerPayload has systemPromptPrefix', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'polyfill_cot' })
    expect(typeof result.providerPayload?.systemPromptPrefix).toBe('string')
    expect((result.providerPayload?.systemPromptPrefix as string).length).toBeGreaterThan(5)
  })

  it('effort=high produces a longer CoT prefix', () => {
    const low = adapter.thinking({ extendedThinkingMode: 'polyfill_cot', effort: 'low' })
    const high = adapter.thinking({ extendedThinkingMode: 'polyfill_cot', effort: 'high' })
    expect(
      (high.providerPayload?.systemPromptPrefix as string).length
    ).toBeGreaterThanOrEqual(
      (low.providerPayload?.systemPromptPrefix as string).length
    )
  })
})

// ---------------------------------------------------------------------------
// DeepSeek — inline_blocks
// ---------------------------------------------------------------------------

describe('C-S4: DeepSeekAdapter.thinking()', () => {
  const adapter = new DeepSeekAdapter()

  it('returns mode=inline_blocks', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'inline_blocks' })
    expect(result.mode).toBe('inline_blocks')
  })

  it('providerPayload.extractReasoningMiddleware is true', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'inline_blocks' })
    expect(result.providerPayload?.extractReasoningMiddleware).toBe(true)
  })

  it('defaults to effort=medium', () => {
    const result = adapter.thinking({ extendedThinkingMode: 'inline_blocks' })
    expect(result.effort).toBe('medium')
  })
})

// ---------------------------------------------------------------------------
// NVIDIA — null (capability hint)
// ---------------------------------------------------------------------------

describe('C-S4: NVIDIAAdapter.thinking()', () => {
  const adapter = new NVIDIAAdapter()

  it('returns mode=null (no thinking support)', () => {
    const result = adapter.thinking({ extendedThinkingMode: null })
    expect(result.mode).toBeNull()
  })

  it('does NOT throw CapabilityUnsupportedError (returns graceful null mode)', () => {
    expect(() => {
      adapter.thinking({ extendedThinkingMode: null })
    }).not.toThrow()
  })

  it('providerPayload has capability hint', () => {
    const result = adapter.thinking({ extendedThinkingMode: null })
    expect(result.providerPayload?.hint).toBeDefined()
  })
})
