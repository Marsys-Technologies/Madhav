/**
 * Agentic Loop Adapter — Chain of Thought
 * =========================================
 * Thinking block pass-through and accumulation.
 * Handles extended thinking from Gemini/Anthropic thinking tokens.
 */

export interface ThinkingBlock {
  type: 'thinking'
  thinking: string
  timestamp: number
  iteration?: number
}

export interface ThinkingAccumulator {
  blocks: ThinkingBlock[]
  total_thinking_tokens: number
}

/**
 * Parse thinking content from various LLM response formats.
 * Supports: Anthropic thinking blocks, Gemini's <think> tags, OpenAI reasoning tokens.
 */
export function parseThinkingBlocks(rawContent: string | object): ThinkingBlock[] {
  const blocks: ThinkingBlock[] = []

  if (typeof rawContent === 'string') {
    // Gemini-style <think>...</think> tags
    const thinkRegex = /<think>([\s\S]*?)<\/think>/g
    let match
    while ((match = thinkRegex.exec(rawContent)) !== null) {
      blocks.push({
        type: 'thinking',
        thinking: match[1].trim(),
        timestamp: Date.now(),
      })
    }
  } else if (Array.isArray(rawContent)) {
    // Anthropic-style content blocks
    for (const block of rawContent) {
      if (block?.type === 'thinking' && block?.thinking) {
        blocks.push({
          type: 'thinking',
          thinking: block.thinking,
          timestamp: Date.now(),
        })
      }
    }
  }

  return blocks
}

/**
 * Accumulate thinking blocks across loop iterations.
 */
export class ThinkingAccumulatorImpl implements ThinkingAccumulator {
  blocks: ThinkingBlock[] = []
  total_thinking_tokens = 0

  addBlock(block: ThinkingBlock, iteration?: number): void {
    this.blocks.push({ ...block, iteration })
    // Rough token estimate: ~1 token per 4 chars
    this.total_thinking_tokens += Math.ceil(block.thinking.length / 4)
  }

  addBlocks(blocks: ThinkingBlock[], iteration?: number): void {
    blocks.forEach((b) => this.addBlock(b, iteration))
  }

  /** Get thinking content up to the last N blocks */
  getRecent(n: number): ThinkingBlock[] {
    return this.blocks.slice(-n)
  }

  /** Summarize thinking across all iterations */
  getSummary(): string {
    if (this.blocks.length === 0) return ''
    return this.blocks
      .map((b, i) => `[Thinking block ${i + 1}${b.iteration !== undefined ? ` (iter ${b.iteration})` : ''}]: ${b.thinking.slice(0, 200)}...`)
      .join('\n')
  }

  /** Should the loop collapse thinking blocks? (cost optimization) */
  shouldCollapse(): boolean {
    return this.total_thinking_tokens > 10000
  }
}

/**
 * Format thinking blocks for display in Consume Chat.
 * Returns collapsed HTML for large blocks, inline for small.
 */
export function formatThinkingForDisplay(blocks: ThinkingBlock[]): string {
  if (blocks.length === 0) return ''

  const totalChars = blocks.reduce((sum, b) => sum + b.thinking.length, 0)

  if (totalChars > 1000) {
    // Collapse into accordion
    return `<details><summary>Extended thinking (${blocks.length} blocks)</summary>\n${blocks.map((b) => b.thinking).join('\n\n')}\n</details>`
  }

  return blocks.map((b) => `> ${b.thinking}`).join('\n\n')
}
