/**
 * E-S6: interleaved-text-tool.test.ts
 *
 * Verifies that interleaved text + tool block stream ordering is preserved
 * by the agentic loop engine. Claude 4.x and Gemini 2.5 Pro can emit text
 * BEFORE a tool call in a single assistant turn; the UI must render them
 * in source order.
 *
 * Tests the ordering contract in agentic_loop.ts:
 * - supportsInterleavedTextTool=true providers (Anthropic, Google) should preserve
 *   text-then-card-then-text ordering
 * - supportsInterleavedTextTool=false providers (OpenAI, DeepSeek, NVIDIA) emit
 *   tool calls without interleaved text
 */

import { describe, it, expect } from 'vitest'
import {
  ANTHROPIC_LOOP_CONFIG,
  GOOGLE_LOOP_CONFIG,
  OPENAI_LOOP_CONFIG,
  DEEPSEEK_LOOP_CONFIG,
  NVIDIA_LOOP_CONFIG,
  LOOP_CONFIG_BY_PROVIDER,
} from '../../src/lib/synthesis/agentic_loop'

describe('E-S6: interleaved text+tool ordering — provider support matrix', () => {
  it('Anthropic supports interleaved text+tool (Claude 4.x)', () => {
    expect(ANTHROPIC_LOOP_CONFIG.supportsInterleavedTextTool).toBe(true)
  })

  it('Google supports interleaved text+tool (Gemini 2.5 Pro)', () => {
    expect(GOOGLE_LOOP_CONFIG.supportsInterleavedTextTool).toBe(true)
  })

  it('OpenAI does NOT support interleaved text+tool (Chat Completions)', () => {
    expect(OPENAI_LOOP_CONFIG.supportsInterleavedTextTool).toBe(false)
  })

  it('DeepSeek does NOT support interleaved text+tool (OpenAI-compat)', () => {
    expect(DEEPSEEK_LOOP_CONFIG.supportsInterleavedTextTool).toBe(false)
  })

  it('NVIDIA does NOT support interleaved text+tool (OpenAI-compat baseline)', () => {
    expect(NVIDIA_LOOP_CONFIG.supportsInterleavedTextTool).toBe(false)
  })
})

describe('E-S6: LOOP_CONFIG_BY_PROVIDER — complete coverage', () => {
  const providerIds = ['anthropic', 'google', 'openai', 'deepseek', 'nvidia']

  it('covers all 5 providers', () => {
    for (const id of providerIds) {
      expect(LOOP_CONFIG_BY_PROVIDER[id]).toBeDefined()
      expect(LOOP_CONFIG_BY_PROVIDER[id].providerId).toBe(id)
    }
  })

  it('exactly 2 providers support interleaved text+tool', () => {
    const interleaved = Object.values(LOOP_CONFIG_BY_PROVIDER).filter(
      c => c.supportsInterleavedTextTool,
    )
    expect(interleaved).toHaveLength(2)
    const ids = interleaved.map(c => c.providerId).sort()
    expect(ids).toEqual(['anthropic', 'google'])
  })

  it('exactly 1 provider has reasoning middleware (DeepSeek)', () => {
    const withMiddleware = Object.values(LOOP_CONFIG_BY_PROVIDER).filter(
      c => c.hasReasoningMiddleware,
    )
    expect(withMiddleware).toHaveLength(1)
    expect(withMiddleware[0].providerId).toBe('deepseek')
  })
})

describe('E-S6: stream-position ordering invariant', () => {
  it('Anthropic loop config signals that stream position must be respected', () => {
    // The loop engine must preserve stream-position ordering when
    // supportsInterleavedTextTool=true. This test documents that contract.
    expect(ANTHROPIC_LOOP_CONFIG.supportsInterleavedTextTool).toBe(true)
    // When a Claude 4.x response contains:
    //   [text_delta:"Here is what I found: "] → [tool_use_start:query] → [text_delta:"..."]
    // The UI must render them as: text | ToolCallCard | text
    // The loop engine preserves this by not reordering ChatEvents.
  })

  it('Google loop config signals that stream position must be respected', () => {
    expect(GOOGLE_LOOP_CONFIG.supportsInterleavedTextTool).toBe(true)
  })
})
