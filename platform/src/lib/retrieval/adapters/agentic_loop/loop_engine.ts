/**
 * Agentic Loop Adapter — Loop Engine
 * =====================================
 * Main orchestrator with soft budget governor (no hard iteration cap).
 * Coordinates chain_of_thought, deferred_tool_loader, adaptive_planner,
 * reflection, error_recovery, and budget_governor.
 */

import { getCapability, listCapabilities } from '@/lib/retrieval/registry'
import type { CapabilityUri, CapabilityContext } from '@/lib/retrieval/registry/types'
import { BudgetGovernor } from './budget_governor'
import { ThinkingAccumulatorImpl, parseThinkingBlocks } from './chain_of_thought'
import { getToolCatalog, loadToolSchema, prioritizeCatalog } from './deferred_tool_loader'
import { planNextAction, shouldStopEarly } from './adaptive_planner'
import { shouldReflect, reflect, formatReflectionForLLM } from './reflection'
import { classifyError, planRecovery } from './error_recovery'
import type { LoopState } from './adaptive_planner'

export interface AgenticLoopOptions {
  /** Budget in USD for this loop run */
  budget_usd?: number
  /** Soft iteration limit (advisory, not hard) */
  soft_iteration_limit?: number
  /** Chart context for chart-specific tools */
  context?: CapabilityContext
  /** Reflection interval (every N iterations) */
  reflection_interval?: number
}

export interface LoopResult {
  final_context: Record<CapabilityUri, unknown>
  thinking_summary: string
  iterations_used: number
  budget_spent_usd: number
  tools_invoked: CapabilityUri[]
  was_budget_limited: boolean
  was_iteration_limited: boolean
}

const DEFAULT_SOFT_LIMIT = 12
const DEFAULT_BUDGET_USD = 0.50

/**
 * Run the agentic retrieval loop.
 * Returns aggregated context from all successful tool calls.
 */
export async function runAgenticLoop(
  query: string,
  options: AgenticLoopOptions = {}
): Promise<LoopResult> {
  const {
    budget_usd = DEFAULT_BUDGET_USD,
    soft_iteration_limit = DEFAULT_SOFT_LIMIT,
    context,
    reflection_interval = 3,
  } = options

  const governor = new BudgetGovernor(budget_usd)
  const thinking = new ThinkingAccumulatorImpl()

  const loopState: LoopState = {
    iteration: 0,
    tools_called: [],
    results_gathered: new Map(),
    intent: '',
    original_query: query,
  }

  const errors: ReturnType<typeof classifyError>[] = []
  let was_budget_limited = false
  let was_iteration_limited = false

  // Get the initial tool catalog
  const catalog = prioritizeCatalog(getToolCatalog())

  // Main loop
  while (true) {
    loopState.iteration++

    // Budget check
    if (governor.isOverBudget) {
      was_budget_limited = true
      break
    }

    // Soft iteration limit
    if (loopState.iteration > soft_iteration_limit) {
      was_iteration_limited = true
      break
    }

    // Reflection check
    if (shouldReflect(loopState, reflection_interval)) {
      const reflection_result = reflect(loopState)
      if (reflection_result.ready_to_synthesize) break
    }

    // Plan next action
    const plan = planNextAction(loopState, soft_iteration_limit)
    if (plan.action === 'synthesize') break
    if (plan.action === 'continue' && shouldStopEarly(loopState)) break

    // Execute tools for this iteration
    const tools_to_call = plan.next_tools || catalog.slice(0, 3).map((c) => c.uri)

    for (const tool_uri of tools_to_call) {
      if (loopState.tools_called.includes(tool_uri)) continue  // Don't repeat

      const cap = getCapability(tool_uri)
      if (!cap) continue

      try {
        const result = await cap.handler({}, context)

        if (!result.is_error) {
          loopState.results_gathered.set(tool_uri, result.content)
          loopState.tools_called.push(tool_uri)

          // Track thinking blocks if any
          if (typeof result.content === 'object' && result.content !== null) {
            const blocks = parseThinkingBlocks(result.content as object)
            thinking.addBlocks(blocks, loopState.iteration)
          }

          // Approximate cost tracking
          governor.recordCall({
            tool_uri,
            model: 'gemini-2.5-flash',
            input_tokens: 100,
            output_tokens: 500,
          })
        }
      } catch (err) {
        const error = classifyError(tool_uri, err, loopState.iteration)
        errors.push(error)

        const recovery = planRecovery(error, errors, 2)
        if (recovery.strategy === 'substitute' && recovery.substitute_uri) {
          // Try substitute (will be picked up next iteration)
          tools_to_call.push(recovery.substitute_uri)
        }
      }
    }
  }

  return {
    final_context: Object.fromEntries(loopState.results_gathered),
    thinking_summary: thinking.getSummary(),
    iterations_used: loopState.iteration,
    budget_spent_usd: governor.spent,
    tools_invoked: loopState.tools_called,
    was_budget_limited,
    was_iteration_limited,
  }
}
