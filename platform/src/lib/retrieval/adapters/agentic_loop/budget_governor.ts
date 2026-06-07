/**
 * Agentic Loop Adapter — Budget Governor
 * ========================================
 * Per-call cost tracking + budget header injection.
 * Tracks spend in USD; emits budget headers to the LLM request.
 */

export interface BudgetState {
  /** Total budget in USD */
  total_budget_usd: number
  /** Spent so far in USD */
  spent_usd: number
  /** Per-call cost ledger */
  call_ledger: CallCost[]
}

export interface CallCost {
  tool_uri: string
  model?: string
  input_tokens: number
  output_tokens: number
  cost_usd: number
  timestamp: number
}

/** Approximate cost per 1M tokens by model (USD) */
const MODEL_COST_PER_1M: Record<string, { input: number; output: number }> = {
  'gemini-2.5-flash': { input: 0.075, output: 0.30 },
  'gemini-2.5-flash-lite': { input: 0.019, output: 0.075 },
  'gemini-2.5-pro': { input: 1.25, output: 10.0 },
  'deepseek-chat': { input: 0.27, output: 1.10 },
  'gpt-4o': { input: 2.50, output: 10.0 },
  'gpt-4o-mini': { input: 0.15, output: 0.60 },
  default: { input: 0.075, output: 0.30 },  // default to flash
}

export class BudgetGovernor {
  private state: BudgetState

  constructor(total_budget_usd: number) {
    this.state = {
      total_budget_usd,
      spent_usd: 0,
      call_ledger: [],
    }
  }

  /** Record a completed tool call's cost */
  recordCall(params: {
    tool_uri: string
    model?: string
    input_tokens: number
    output_tokens: number
  }): CallCost {
    const model = params.model || 'default'
    const rates = MODEL_COST_PER_1M[model] || MODEL_COST_PER_1M.default
    const cost_usd =
      (params.input_tokens / 1_000_000) * rates.input +
      (params.output_tokens / 1_000_000) * rates.output

    const call: CallCost = {
      tool_uri: params.tool_uri,
      model,
      input_tokens: params.input_tokens,
      output_tokens: params.output_tokens,
      cost_usd,
      timestamp: Date.now(),
    }

    this.state.spent_usd += cost_usd
    this.state.call_ledger.push(call)
    return call
  }

  /** Check if budget allows another call (estimated cost in USD) */
  canAfford(estimated_cost_usd: number): boolean {
    return this.state.spent_usd + estimated_cost_usd <= this.state.total_budget_usd
  }

  /** Get remaining budget */
  get remaining(): number {
    return this.state.total_budget_usd - this.state.spent_usd
  }

  /** Get spent amount */
  get spent(): number {
    return this.state.spent_usd
  }

  /** Get budget utilization (0-1) */
  get utilization(): number {
    return this.state.spent_usd / this.state.total_budget_usd
  }

  /** Is over 80% utilized? (soft warning threshold) */
  get isApproachingLimit(): boolean {
    return this.utilization >= 0.8
  }

  /** Is over budget? */
  get isOverBudget(): boolean {
    return this.state.spent_usd >= this.state.total_budget_usd
  }

  /** Get budget headers to inject into LLM request */
  getBudgetHeaders(): Record<string, string> {
    return {
      'X-Budget-Remaining-USD': this.remaining.toFixed(6),
      'X-Budget-Utilization': (this.utilization * 100).toFixed(1) + '%',
      'X-Budget-Call-Count': String(this.state.call_ledger.length),
    }
  }

  /** Snapshot of current state */
  getState(): Readonly<BudgetState> {
    return { ...this.state, call_ledger: [...this.state.call_ledger] }
  }
}
