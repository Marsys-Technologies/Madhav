/**
 * adapters/agentic_loop/adaptive_planner.ts
 *
 * Mid-loop re-planning based on intermediate results.
 * After each tool call, assesses whether the current plan is still optimal
 * or whether priorities should be re-ordered based on what was learned.
 *
 * L0FR Stream A — authored 2026-06-07
 */

export interface ToolResult {
  uri: string
  args: Record<string, unknown>
  result: unknown
  latency_ms: number
  cost_usd: number
}

export interface PlanItem {
  uri: string
  rationale: string
  priority: number  // lower = higher priority
  completed?: boolean
}

export interface PlanState {
  items: PlanItem[]
  iteration: number
  last_replanned_at?: string
}

export class AdaptivePlanner {
  private plan: PlanItem[]
  private iteration: number = 0
  private results: ToolResult[] = []

  constructor(initialPlan: PlanItem[]) {
    this.plan = [...initialPlan].sort((a, b) => a.priority - b.priority)
  }

  /** Record a completed tool call result */
  recordResult(result: ToolResult): void {
    this.results.push(result)
    // Mark the corresponding plan item as completed
    const item = this.plan.find(p => p.uri === result.uri && !p.completed)
    if (item) {
      item.completed = true
    }
    this.iteration++
  }

  /** Get the next un-completed tool to call */
  nextTool(): PlanItem | null {
    return this.plan.find(p => !p.completed) ?? null
  }

  /**
   * Re-prioritize the plan based on what was learned from intermediate results.
   * Simple heuristic: if a result suggests a particular domain, boost related tools.
   */
  replan(insight: string): void {
    // Simple keyword-based re-prioritization
    // (a real implementation would use an LLM classifier)
    const lowerInsight = insight.toLowerCase()

    for (const item of this.plan) {
      if (item.completed) continue

      // Boost panchanga/temporal tools if temporal patterns found
      if (lowerInsight.includes('dasha') || lowerInsight.includes('transit')) {
        if (item.uri.includes('kala') || item.uri.includes('dasha')) {
          item.priority = Math.max(0, item.priority - 10)
        }
      }

      // Boost remedy tools if afflictions found
      if (lowerInsight.includes('afflict') || lowerInsight.includes('malefic')) {
        if (item.uri.includes('remedy') || item.uri.includes('upaya')) {
          item.priority = Math.max(0, item.priority - 10)
        }
      }
    }

    // Re-sort after priority changes
    this.plan.sort((a, b) => {
      if (a.completed && !b.completed) return 1
      if (!a.completed && b.completed) return -1
      return a.priority - b.priority
    })
  }

  get state(): PlanState {
    return {
      items: [...this.plan],
      iteration: this.iteration,
      last_replanned_at: new Date().toISOString(),
    }
  }

  get completedCount(): number {
    return this.plan.filter(p => p.completed).length
  }

  get totalCount(): number {
    return this.plan.length
  }
}
