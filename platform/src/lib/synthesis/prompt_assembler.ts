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
