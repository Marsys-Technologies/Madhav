/**
 * adapters/agentic_loop/budget_governor.ts
 *
 * Per-call cost tracking + budget header injection for the agentic loop.
 * Enforces soft and hard budget limits; emits warnings before hard stop.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import { CostTracker, type TokenUsage } from '../shared/cost_tracker'

export interface BudgetConfig {
  /** Soft limit in USD — warn when reached */
  soft_usd: number
  /** Hard limit in USD — stop loop when reached */
  hard_usd: number
}

export const DEFAULT_BUDGET: BudgetConfig = {
  soft_usd: 0.10,   // 10 cents: warn
  hard_usd: 0.50,   // 50 cents: stop (per-session cap)
}

export class BudgetGovernor {
  private tracker: CostTracker
  private config: BudgetConfig
  private softWarned: boolean = false

  constructor(config: BudgetConfig = DEFAULT_BUDGET) {
    this.tracker = new CostTracker()
    this.config = config
  }

  /** Track a model call and check budget state */
  trackCall(model: string, usage: TokenUsage): {
    cost: number
    total: number
    status: 'ok' | 'soft_warn' | 'hard_stop'
  } {
    const call = this.tracker.track(model, usage)
    const total = this.tracker.total

    if (total >= this.config.hard_usd) {
      return { cost: call.estimated_usd, total, status: 'hard_stop' }
    }
    if (!this.softWarned && total >= this.config.soft_usd) {
      this.softWarned = true
      return { cost: call.estimated_usd, total, status: 'soft_warn' }
    }
    return { cost: call.estimated_usd, total, status: 'ok' }
  }

  /** Current total spend */
  get total(): number {
    return this.tracker.total
  }

  /** Budget header for injection into LLM system prompt */
  toBudgetHeader(): string {
    return `[BUDGET] spent=${this.tracker.total.toFixed(4)}USD soft=${this.config.soft_usd}USD hard=${this.config.hard_usd}USD`
  }

  /** Full cost history */
  get history() {
    return this.tracker.history
  }
}
