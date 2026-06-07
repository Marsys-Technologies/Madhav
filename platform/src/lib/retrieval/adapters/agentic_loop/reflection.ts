/**
 * adapters/agentic_loop/reflection.ts
 *
 * Periodic "ready to synthesize?" prompts.
 * At configurable intervals, injects a reflection prompt asking the LLM
 * whether it has enough information to produce a synthesis, or should
 * continue gathering.
 *
 * L0FR Stream A — authored 2026-06-07
 */

export interface ReflectionConfig {
  /** Trigger reflection every N tool calls */
  interval_calls: number
  /** Always reflect at these specific iterations */
  checkpoint_iterations?: number[]
  /** Maximum iterations before forcing synthesis */
  max_iterations: number
}

export const DEFAULT_REFLECTION_CONFIG: ReflectionConfig = {
  interval_calls: 4,
  checkpoint_iterations: [3, 7, 12],
  max_iterations: 20,
}

export interface ReflectionDecision {
  should_synthesize: boolean
  reason: string
  confidence: number  // 0-1
  suggested_next_tools?: string[]
}

export class ReflectionEngine {
  private callCount: number = 0
  private config: ReflectionConfig

  constructor(config: ReflectionConfig = DEFAULT_REFLECTION_CONFIG) {
    this.config = config
  }

  increment(): void {
    this.callCount++
  }

  /** Whether this iteration should trigger a reflection */
  shouldReflect(): boolean {
    if (this.callCount >= this.config.max_iterations) return true
    if (this.callCount % this.config.interval_calls === 0) return true
    if (this.config.checkpoint_iterations?.includes(this.callCount)) return true
    return false
  }

  /**
   * Generate the reflection prompt to inject into the LLM conversation.
   * The LLM responds with a structured decision.
   */
  buildReflectionPrompt(gatheredTopics: string[]): string {
    const isForced = this.callCount >= this.config.max_iterations

    if (isForced) {
      return `[SYSTEM: Maximum iterations reached (${this.config.max_iterations}). You MUST now synthesize based on gathered information.]\n\nYou have gathered information on: ${gatheredTopics.join(', ')}. Please now synthesize a comprehensive response.`
    }

    return `[REFLECTION CHECK — iteration ${this.callCount}]\n\nYou have gathered information on: ${gatheredTopics.join(', ')}.\n\nAssess: Do you have sufficient depth to answer the query comprehensively? Respond with:\n- READY_TO_SYNTHESIZE if you have enough\n- NEED_MORE_TOOLS followed by which tools to call next\n\nRemember: Acharya-grade analysis requires cross-domain signals. Ensure you've covered relevant layers.`
  }

  /**
   * Parse an LLM reflection response into a structured decision.
   */
  static parseReflectionResponse(response: string): ReflectionDecision {
    const upper = response.toUpperCase()

    if (upper.includes('READY_TO_SYNTHESIZE')) {
      return {
        should_synthesize: true,
        reason: 'LLM declared ready to synthesize',
        confidence: 0.9,
      }
    }

    if (upper.includes('NEED_MORE_TOOLS')) {
      // Extract tool URIs from response if mentioned
      const uriMatches = response.match(/marsys:\/\/\S+/g) ?? []
      return {
        should_synthesize: false,
        reason: 'LLM requested more tools',
        confidence: 0.8,
        suggested_next_tools: uriMatches,
      }
    }

    // Default: continue
    return {
      should_synthesize: false,
      reason: 'Ambiguous reflection response — continuing',
      confidence: 0.5,
    }
  }

  get currentIteration(): number {
    return this.callCount
  }
}
