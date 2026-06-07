/**
 * adapters/agentic_loop/chain_of_thought.ts
 *
 * Thinking block pass-through and accumulation.
 * Captures extended thinking tokens from Claude/Gemini and maintains
 * a running chain-of-thought log for the duration of an agentic session.
 *
 * L0FR Stream A — authored 2026-06-07
 */

export interface ThinkingBlock {
  model: string
  iteration: number
  thinking_text: string
  tokens: number
  timestamp: string
}

export interface ChainOfThoughtState {
  blocks: ThinkingBlock[]
  total_thinking_tokens: number
}

export class ChainOfThought {
  private blocks: ThinkingBlock[] = []
  private totalTokens: number = 0

  /** Append a thinking block from an LLM response */
  append(model: string, iteration: number, thinkingText: string, tokens?: number): void {
    const block: ThinkingBlock = {
      model,
      iteration,
      thinking_text: thinkingText,
      tokens: tokens ?? Math.ceil(thinkingText.length / 4),  // rough estimate if not provided
      timestamp: new Date().toISOString(),
    }
    this.blocks.push(block)
    this.totalTokens += block.tokens
  }

  /** Extract thinking text from a model response (handles multiple formats) */
  static extractThinking(response: unknown): string | null {
    if (!response || typeof response !== 'object') return null
    const r = response as Record<string, unknown>

    // Anthropic format: content array with type='thinking' blocks
    if (Array.isArray(r['content'])) {
      const thinkingBlocks = (r['content'] as Array<{ type: string; thinking?: string }>)
        .filter(b => b.type === 'thinking' && b.thinking)
        .map(b => b.thinking!)
      if (thinkingBlocks.length > 0) return thinkingBlocks.join('\n\n')
    }

    // Gemini format: thoughtsTokenCount + thoughts field
    if (r['thoughts'] && typeof r['thoughts'] === 'string') {
      return r['thoughts']
    }

    // OpenAI reasoning: reasoning_content in some preview models
    if (r['reasoning_content'] && typeof r['reasoning_content'] === 'string') {
      return r['reasoning_content']
    }

    return null
  }

  /** Current state snapshot */
  get state(): ChainOfThoughtState {
    return {
      blocks: [...this.blocks],
      total_thinking_tokens: this.totalTokens,
    }
  }

  /** All thinking text concatenated (for context injection) */
  get fullText(): string {
    return this.blocks.map(b => `[Iteration ${b.iteration}]\n${b.thinking_text}`).join('\n\n---\n\n')
  }

  reset(): void {
    this.blocks = []
    this.totalTokens = 0
  }
}
