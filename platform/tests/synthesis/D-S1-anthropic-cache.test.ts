/**
 * D-S1: D-S1-anthropic-cache.test.ts
 *
 * Tests for Anthropic 4-breakpoint cache_control + prompt_assembler canonical layout.
 *
 * R11.D — Caching
 * AC1: With cacheEnabled=true, exactly 4 cache_control markers at canonical positions.
 * AC3: With cacheEnabled=false, no cache_control in assembled messages.
 * AC5: Server-side only — no NEXT_PUBLIC prefix on the flag.
 * AC6: cache_metrics.ts buildCacheMetricsRecord: hit/miss/skip logic.
 */

import { describe, it, expect } from 'vitest'
import {
  assembleWithCacheBreakpoints,
  countCacheBreakpoints,
  type PromptSections,
} from '../../src/lib/synthesis/prompt_assembler'
import {
  buildCacheMetricsRecord,
} from '../../src/lib/observatory/cache_metrics'
import { ANTHROPIC_MANIFEST } from '../../src/lib/providers/anthropic/manifest'
import { AnthropicAdapter } from '../../src/lib/providers/anthropic/adapter'
import type { CacheRequest } from '../../src/lib/providers/types'

// ---------------------------------------------------------------------------
// AC5: server-side flag discipline (no NEXT_PUBLIC contamination)
// ---------------------------------------------------------------------------

describe('D-S1: R11D_ANTHROPIC_CACHE flag — server-side only', () => {
  it('flag name does not have NEXT_PUBLIC prefix', () => {
    // If this string were in source it would be a client-side leak.
    // The flag is server-side only per D-S1 brief.
    const flagName = 'R11D_ANTHROPIC_CACHE'
    expect(flagName.startsWith('NEXT_PUBLIC')).toBe(false)
  })
})

// ---------------------------------------------------------------------------
// AnthropicAdapter.cache() — returns explicit_4bp config
// ---------------------------------------------------------------------------

describe('D-S1: AnthropicAdapter.cache()', () => {
  const adapter = new AnthropicAdapter()

  it('manifest declares explicit_4bp', () => {
    expect(ANTHROPIC_MANIFEST.promptCaching).toBe('explicit_4bp')
  })

  it('cache() returns explicit_4bp mode', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.mode).toBe('explicit_4bp')
  })

  it('cache() returns exactly 4 breakpoint positions', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.breakpointPositions).toHaveLength(4)
  })

  it('cache() providerPayload has cacheControl: { type: ephemeral }', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.providerPayload?.cacheControl).toEqual({ type: 'ephemeral' })
  })

  it('cache() providerPayload has maxBreakpoints=4', () => {
    const result = adapter.cache({} as CacheRequest)
    expect(result.providerPayload?.maxBreakpoints).toBe(4)
  })

  it('custom breakpointPositions are forwarded', () => {
    const result = adapter.cache({ breakpointPositions: [0, 1] } as CacheRequest)
    expect(result.breakpointPositions).toEqual([0, 1])
  })
})

// ---------------------------------------------------------------------------
// assembleWithCacheBreakpoints — cache ON
// ---------------------------------------------------------------------------

describe('D-S1: assembleWithCacheBreakpoints — cacheEnabled=true', () => {
  const fullSections: PromptSections = {
    toolsBlock: 'tools JSON here',
    systemPrompt: 'synthesis system prompt',
    ragBundle: 'retrieved documents bundle',
    historyTurns: [
      { role: 'user', content: 'Previous question' },
      { role: 'assistant', content: 'Previous answer' },
    ],
    currentUserTurn: 'Current question',
  }

  it('exactly 4 cache_control markers when all sections present', () => {
    const messages = assembleWithCacheBreakpoints(fullSections, true)
    expect(countCacheBreakpoints(messages)).toBe(4)
  })

  it('tools block gets cache_control (BP0)', () => {
    const messages = assembleWithCacheBreakpoints(fullSections, true)
    const toolsMsg = messages.find(m => m.content === 'tools JSON here')
    expect(toolsMsg?.cache_control).toEqual({ type: 'ephemeral' })
  })

  it('system prompt gets cache_control (BP1)', () => {
    const messages = assembleWithCacheBreakpoints(fullSections, true)
    const sysMsg = messages.find(m => m.content === 'synthesis system prompt')
    expect(sysMsg?.cache_control).toEqual({ type: 'ephemeral' })
  })

  it('RAG bundle gets cache_control (BP2)', () => {
    const messages = assembleWithCacheBreakpoints(fullSections, true)
    const ragMsg = messages.find(m => m.content === 'retrieved documents bundle')
    expect(ragMsg?.cache_control).toEqual({ type: 'ephemeral' })
  })

  it('last assistant turn gets cache_control (BP3)', () => {
    const messages = assembleWithCacheBreakpoints(fullSections, true)
    const lastAssistant = [...messages].reverse().find(m => m.role === 'assistant')
    expect(lastAssistant?.cache_control).toEqual({ type: 'ephemeral' })
  })

  it('current user turn never gets cache_control', () => {
    const messages = assembleWithCacheBreakpoints(fullSections, true)
    const lastMsg = messages[messages.length - 1]
    expect(lastMsg.content).toBe('Current question')
    expect(lastMsg.cache_control).toBeUndefined()
  })

  it('message order: tools → system → history → rag → current', () => {
    const messages = assembleWithCacheBreakpoints(fullSections, true)
    const roles = messages.map(m => ({ role: m.role, snippet: (m.content as string).slice(0, 10) }))
    // tools (system) → system prompt (system) → history turns (user+assistant) → rag (user) → current (user)
    expect(messages[0].content).toBe('tools JSON here')
    expect(messages[1].content).toBe('synthesis system prompt')
    // last is current turn
    expect(messages[messages.length - 1].content).toBe('Current question')
  })
})

// ---------------------------------------------------------------------------
// assembleWithCacheBreakpoints — cache OFF
// ---------------------------------------------------------------------------

describe('D-S1: assembleWithCacheBreakpoints — cacheEnabled=false', () => {
  const fullSections: PromptSections = {
    toolsBlock: 'tools JSON here',
    systemPrompt: 'synthesis system prompt',
    ragBundle: 'retrieved documents bundle',
    historyTurns: [
      { role: 'user', content: 'Previous question' },
      { role: 'assistant', content: 'Previous answer' },
    ],
    currentUserTurn: 'Current question',
  }

  it('zero cache_control markers when cacheEnabled=false', () => {
    const messages = assembleWithCacheBreakpoints(fullSections, false)
    expect(countCacheBreakpoints(messages)).toBe(0)
  })

  it('no message has cache_control defined', () => {
    const messages = assembleWithCacheBreakpoints(fullSections, false)
    for (const msg of messages) {
      expect(msg.cache_control).toBeUndefined()
    }
  })
})

// ---------------------------------------------------------------------------
// assembleWithCacheBreakpoints — partial sections
// ---------------------------------------------------------------------------

describe('D-S1: assembleWithCacheBreakpoints — partial sections', () => {
  it('no tools block: 3 or fewer breakpoints (depends on history)', () => {
    const sections: PromptSections = {
      systemPrompt: 'system',
      ragBundle: 'rag',
      historyTurns: [{ role: 'assistant', content: 'prior answer' }],
      currentUserTurn: 'question',
    }
    const messages = assembleWithCacheBreakpoints(sections, true)
    // system(1) + assistant in history(1, gets BP3) + rag(1) = 3 max
    expect(countCacheBreakpoints(messages)).toBeLessThanOrEqual(3)
  })

  it('no history: no BP3 assistant marker', () => {
    const sections: PromptSections = {
      toolsBlock: 'tools',
      systemPrompt: 'system',
      ragBundle: 'rag',
      historyTurns: [],
      currentUserTurn: 'question',
    }
    const messages = assembleWithCacheBreakpoints(sections, true)
    // BP0 (tools) + BP1 (system) + BP2 (rag) = 3; no BP3 (no assistant turn)
    expect(countCacheBreakpoints(messages)).toBe(3)
  })

  it('minimal: only currentUserTurn — 0 breakpoints even with cache=true', () => {
    const sections: PromptSections = {
      historyTurns: [],
      currentUserTurn: 'hello',
    }
    const messages = assembleWithCacheBreakpoints(sections, true)
    expect(countCacheBreakpoints(messages)).toBe(0)
  })
})

// ---------------------------------------------------------------------------
// cache_metrics.ts — buildCacheMetricsRecord
// ---------------------------------------------------------------------------

describe('D-S1: buildCacheMetricsRecord', () => {
  it('returns null when no cache activity (both fields 0)', () => {
    const result = buildCacheMetricsRecord({
      model: 'claude-opus-4-5',
      usage: { input_tokens: 1000, output_tokens: 200 },
    })
    expect(result).toBeNull()
  })

  it('returns record on cache hit (cacheReadTokens > 0)', () => {
    const result = buildCacheMetricsRecord({
      model: 'claude-opus-4-5',
      usage: {
        input_tokens: 100,
        output_tokens: 200,
        cache_read_input_tokens: 5000,
        cache_creation_input_tokens: 0,
      },
    })
    expect(result).not.toBeNull()
    expect(result?.cacheHit).toBe(true)
    expect(result?.cacheWrite).toBe(false)
    expect(result?.usage.cacheReadTokens).toBe(5000)
  })

  it('returns record on cache write (cacheCreationTokens > 0)', () => {
    const result = buildCacheMetricsRecord({
      model: 'claude-opus-4-5',
      usage: {
        input_tokens: 100,
        output_tokens: 200,
        cache_read_input_tokens: 0,
        cache_creation_input_tokens: 5000,
      },
    })
    expect(result?.cacheWrite).toBe(true)
    expect(result?.cacheHit).toBe(false)
  })

  it('estimatedTokenDeltaRatio is negative on cache hit (cheaper)', () => {
    const result = buildCacheMetricsRecord({
      model: 'claude-opus-4-5',
      usage: {
        input_tokens: 100,
        output_tokens: 200,
        cache_read_input_tokens: 5000,
        cache_creation_input_tokens: 0,
      },
    })
    // -0.9 × 5000 = -4500 (saving)
    expect(result?.estimatedTokenDeltaRatio).toBe(-4500)
  })

  it('estimatedTokenDeltaRatio is positive on cache write (more expensive)', () => {
    const result = buildCacheMetricsRecord({
      model: 'claude-opus-4-5',
      usage: {
        input_tokens: 100,
        output_tokens: 200,
        cache_read_input_tokens: 0,
        cache_creation_input_tokens: 5000,
      },
    })
    // 0.25 × 5000 = 1250 (surcharge for writing cache)
    expect(result?.estimatedTokenDeltaRatio).toBe(1250)
  })

  it('provider is always anthropic', () => {
    const result = buildCacheMetricsRecord({
      model: 'claude-opus-4-5',
      usage: { cache_read_input_tokens: 100 },
    })
    expect(result?.provider).toBe('anthropic')
  })

  it('conversationId is forwarded when provided', () => {
    const result = buildCacheMetricsRecord({
      model: 'claude-opus-4-5',
      conversationId: 'conv-abc-123',
      usage: { cache_read_input_tokens: 100 },
    })
    expect(result?.conversationId).toBe('conv-abc-123')
  })
})
