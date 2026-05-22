import 'server-only'

/**
 * prompt_assembler.ts — D-S1 R11.D
 *
 * Prompt assembly utilities for multi-provider cache-aware layout.
 *
 * The cache-aware layout follows NATIVE_RULINGS §4 canonical breakpoint positions
 * for Anthropic explicit_4bp caching. The assembler:
 *   1. Accepts a structured prompt layout (tools, system, RAG bundle, history turns)
 *   2. Injects `cache_control: { type: 'ephemeral' }` at the 4 canonical BP positions
 *      when caching is enabled
 *   3. Returns the assembled message array ready for the Anthropic API
 *
 * For other providers (Google cachedContent, OpenAI automatic, DeepSeek implicit),
 * the assembler passes messages through unchanged — those providers don't need
 * explicit cache markers.
 *
 * Used by D-S5 (cache-aware prompt layout) to optimize for highest-stable tokens
 * at each breakpoint.
 */

/** An assembled message with optional Anthropic cache_control. */
export interface AssembledMessage {
  role: 'system' | 'user' | 'assistant' | 'tool'
  content: string | unknown[]
  /** Injected by the assembler when caching is enabled. */
  cache_control?: { type: 'ephemeral' }
}

/**
 * Canonical breakpoint positions for Anthropic 4-BP cache layout.
 * These are logical positions, not message indices.
 */
export type CacheBreakpointPosition = 'end-of-tools' | 'end-of-system' | 'end-of-rag' | 'last-turn'

export const CANONICAL_BREAKPOINTS: CacheBreakpointPosition[] = [
  'end-of-tools',
  'end-of-system',
  'end-of-rag',
  'last-turn',
]

/**
 * Input structure for cache-aware prompt assembly.
 * Mirrors the logical sections of a Marsys chat turn.
 */
export interface PromptSections {
  /** Anthropic-style tool definitions block (injected as system or user content). */
  toolsBlock?: string
  /** Synthesis system prompt (static across turns — best cache candidate). */
  systemPrompt?: string
  /** RAG bundle from retrieval layer (changes per query). */
  ragBundle?: string
  /** Prior conversation turns (message history). */
  historyTurns: Array<{ role: 'user' | 'assistant'; content: string }>
  /** Current user turn (never cached — always changes). */
  currentUserTurn: string
}

/**
 * Assembles a flat message array from PromptSections, with optional cache_control
 * breakpoints injected at the 4 canonical positions.
 *
 * When cacheEnabled=false (flag off or provider doesn't use explicit_4bp),
 * returns messages without any cache_control markers.
 */
export function assembleWithCacheBreakpoints(
  sections: PromptSections,
  cacheEnabled: boolean,
): AssembledMessage[] {
  const messages: AssembledMessage[] = []

  // BP0: end-of-tools — tools block (static; ideal first cache anchor)
  if (sections.toolsBlock) {
    const msg: AssembledMessage = {
      role: 'system',
      content: sections.toolsBlock,
    }
    if (cacheEnabled) msg.cache_control = { type: 'ephemeral' }
    messages.push(msg)
  }

  // BP1: end-of-system — synthesis system prompt (static; large; second cache anchor)
  if (sections.systemPrompt) {
    const msg: AssembledMessage = {
      role: 'system',
      content: sections.systemPrompt,
    }
    if (cacheEnabled) msg.cache_control = { type: 'ephemeral' }
    messages.push(msg)
  }

  // History turns (no cache markers — changes per session)
  for (const turn of sections.historyTurns) {
    messages.push({ role: turn.role, content: turn.content })
  }

  // BP2: end-of-RAG — retrieval bundle (changes per query, but worth caching in
  // multi-turn sessions where the same documents re-appear)
  if (sections.ragBundle) {
    const msg: AssembledMessage = {
      role: 'user',
      content: sections.ragBundle,
    }
    if (cacheEnabled) msg.cache_control = { type: 'ephemeral' }
    messages.push(msg)
  }

  // BP3: last-assistant-turn — if history ends with an assistant turn, mark it
  // (Anthropic recommends caching the last assistant turn in multi-turn chats)
  if (cacheEnabled && messages.length > 0) {
    const lastAssistant = [...messages].reverse().find(m => m.role === 'assistant')
    if (lastAssistant) {
      lastAssistant.cache_control = { type: 'ephemeral' }
    }
  }

  // Current user turn (never cached)
  messages.push({ role: 'user', content: sections.currentUserTurn })

  return messages
}

/**
 * Returns the count of cache_control markers in an assembled message array.
 * Used by tests + Observatory to verify breakpoint placement.
 */
export function countCacheBreakpoints(messages: AssembledMessage[]): number {
  return messages.filter(m => m.cache_control?.type === 'ephemeral').length
}

// ---------------------------------------------------------------------------
// D-S5 — Cache-Aware Prompt Layout
// ---------------------------------------------------------------------------

/**
 * Canonical cache-aware section ordering for multi-provider synthesis:
 *   tools → system → RAG bundle → history turns → current turn
 *
 * This ordering is optimal for all 4 provider cache strategies:
 *   - Anthropic (explicit_4bp): 4 breakpoints sit at exact section boundaries
 *   - Google (cached_content_api): system + RAG cached as a unit
 *   - OpenAI (automatic): stable prefix maximises cache hit probability
 *   - DeepSeek (implicit): same stable-prefix benefit as OpenAI
 *
 * When R11D_PROMPT_LAYOUT=true, the synthesis layer calls assembleWithCacheBreakpoints
 * via this function. When false, the caller uses its prior assembly order.
 */
export const CACHE_AWARE_SECTION_ORDER = [
  'tools',
  'system',
  'rag',
  'history',
  'current',
] as const

export type CacheSectionName = typeof CACHE_AWARE_SECTION_ORDER[number]

/**
 * Validates that a PromptSections object has the required sections for
 * cache-effective operation. Returns a list of warnings (empty = clean).
 *
 * Used by Observatory telemetry to flag requests that can't benefit from caching.
 */
export function validateCacheSections(sections: PromptSections): string[] {
  const warnings: string[] = []

  if (!sections.toolsBlock) {
    warnings.push('tools block absent — BP0 cache anchor missing')
  }
  if (!sections.systemPrompt) {
    warnings.push('system prompt absent — BP1 cache anchor missing')
  }
  if (!sections.ragBundle) {
    warnings.push('RAG bundle absent — BP2 cache anchor missing; caching only on tools+system')
  }
  if (!sections.historyTurns.some(t => t.role === 'assistant')) {
    warnings.push('no assistant turn in history — BP3 last-turn anchor missing')
  }

  return warnings
}

/**
 * Computes the estimated token coverage for the 4 Anthropic cache breakpoints.
 *
 * Returns a ratio of "tokens before last cache BP / total input tokens" — higher is
 * better (more tokens cached means higher cost savings).
 *
 * Note: this is a structural estimate only (character-based). Accurate token
 * counts require tokenizer integration (D-S6 Observatory tile adds the measured value).
 */
export function estimateCacheCoverage(sections: PromptSections): {
  bp0HasContent: boolean
  bp1HasContent: boolean
  bp2HasContent: boolean
  bp3HasContent: boolean
  bpCount: number
  structuralCoverageWarnings: string[]
} {
  const bp0HasContent = Boolean(sections.toolsBlock)
  const bp1HasContent = Boolean(sections.systemPrompt)
  const bp2HasContent = Boolean(sections.ragBundle)
  const bp3HasContent = sections.historyTurns.some(t => t.role === 'assistant')

  const bpCount = [bp0HasContent, bp1HasContent, bp2HasContent, bp3HasContent].filter(Boolean).length

  return {
    bp0HasContent,
    bp1HasContent,
    bp2HasContent,
    bp3HasContent,
    bpCount,
    structuralCoverageWarnings: validateCacheSections(sections),
  }
}
