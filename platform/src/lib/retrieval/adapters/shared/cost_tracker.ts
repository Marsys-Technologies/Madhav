/**
 * adapters/shared/cost_tracker.ts
 *
 * Per-call cost tracking and accumulator for all adapters.
 * Tracks token usage + estimated USD cost per Gemini/OpenAI pricing.
 *
 * L0FR Stream A — authored 2026-06-07
 */

export interface TokenUsage {
  input_tokens: number
  output_tokens: number
  cached_input_tokens?: number
}

export interface CallCost {
  model: string
  call_id: string
  timestamp: string
  input_tokens: number
  output_tokens: number
  cached_input_tokens: number
  estimated_usd: number
}

// ── Pricing table (USD per 1M tokens) ────────────────────────────────────────
// Gemini 2.5 Flash: $0.075 input, $0.30 output
// Gemini 2.5 Flash-Lite: $0.02 input, $0.08 output
// Gemini 2.5 Pro: $1.25 input, $10.00 output
// DeepSeek Chat: $0.07 input, $1.10 output

const PRICING: Record<string, { input: number; output: number }> = {
  'gemini-2.5-flash': { input: 0.075, output: 0.30 },
  'gemini-2.5-flash-lite': { input: 0.02, output: 0.08 },
  'gemini-2.5-flash-preview': { input: 0.075, output: 0.30 },
  'gemini-2.5-pro': { input: 1.25, output: 10.0 },
  'deepseek-chat': { input: 0.07, output: 1.10 },
  'deepseek-r1': { input: 0.14, output: 2.19 },
  'gpt-4o': { input: 2.50, output: 10.0 },
  'gpt-4o-mini': { input: 0.15, output: 0.60 },
  'default': { input: 0.075, output: 0.30 },  // Gemini Flash as default
}

function estimateCostUsd(model: string, usage: TokenUsage): number {
  const pricing = PRICING[model] ?? PRICING['default']!
  const billableInput = Math.max(0, usage.input_tokens - (usage.cached_input_tokens ?? 0))
  const inputCost = (billableInput / 1_000_000) * pricing.input
  const outputCost = (usage.output_tokens / 1_000_000) * pricing.output
  return inputCost + outputCost
}

// ── CostTracker class ─────────────────────────────────────────────────────────

export class CostTracker {
  private calls: CallCost[] = []
  private totalUsd: number = 0

  /** Record a single LLM call */
  track(model: string, usage: TokenUsage): CallCost {
    const cost: CallCost = {
      model,
      call_id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      timestamp: new Date().toISOString(),
      input_tokens: usage.input_tokens,
      output_tokens: usage.output_tokens,
      cached_input_tokens: usage.cached_input_tokens ?? 0,
      estimated_usd: estimateCostUsd(model, usage),
    }
    this.calls.push(cost)
    this.totalUsd += cost.estimated_usd
    return cost
  }

  /** Total estimated USD across all tracked calls */
  get total(): number {
    return this.totalUsd
  }

  /** All individual call records */
  get history(): CallCost[] {
    return [...this.calls]
  }

  /** Reset accumulator */
  reset(): void {
    this.calls = []
    this.totalUsd = 0
  }

  /** Serialize for budget header injection */
  toBudgetHeader(): string {
    return JSON.stringify({
      total_usd: this.totalUsd.toFixed(6),
      call_count: this.calls.length,
    })
  }
}

/** Module-level global tracker (for session-wide accounting) */
export const globalCostTracker = new CostTracker()
