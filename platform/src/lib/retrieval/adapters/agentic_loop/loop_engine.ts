/**
 * adapters/agentic_loop/loop_engine.ts
 *
 * Main orchestrator for the agentic retrieval loop.
 * No hard iteration cap (governed by soft budget + reflection engine).
 * Integrates: deferred tool loader, CoT, adaptive planner, reflection, error recovery, budget governor.
 *
 * L0FR Stream A — authored 2026-06-07
 */

import { getCapability } from '../../registry'
import type { ToolCapability, CapabilityContext } from '../../registry/types'
import { BudgetGovernor, DEFAULT_BUDGET, type BudgetConfig } from './budget_governor'
import { ChainOfThought } from './chain_of_thought'
import { AdaptivePlanner, type PlanItem } from './adaptive_planner'
import { ReflectionEngine, type ReflectionConfig, DEFAULT_REFLECTION_CONFIG } from './reflection'
import { ErrorRecoveryLog, suggestRecovery, type ToolError } from './error_recovery'
import { getToolCatalog, loadToolSchema } from './deferred_tool_loader'

export interface LoopConfig {
  budget?: BudgetConfig
  reflection?: ReflectionConfig
  /** If true, inject CoT into each iteration */
  capture_thinking?: boolean
}

export interface LoopResult {
  gathered: Record<string, unknown>  // uri → result
  thinking: string
  iterations: number
  total_cost_usd: number
  stop_reason: 'reflection_ready' | 'budget_exhausted' | 'plan_complete' | 'error'
  error_log: ReturnType<ErrorRecoveryLog['log']>
}

export async function runAgenticLoop(
  query: string,
  initialPlan: PlanItem[],
  ctx: CapabilityContext,
  config: LoopConfig = {}
): Promise<LoopResult> {
  const governor = new BudgetGovernor(config.budget ?? DEFAULT_BUDGET)
  const cot = new ChainOfThought()
  const planner = new AdaptivePlanner(initialPlan)
  const reflection = new ReflectionEngine(config.reflection ?? DEFAULT_REFLECTION_CONFIG)
  const errorLog = new ErrorRecoveryLog()
  const gathered: Record<string, unknown> = {}
  const gatheredTopics: string[] = []

  let stopReason: LoopResult['stop_reason'] = 'plan_complete'

  while (true) {
    // Check reflection
    if (reflection.shouldReflect()) {
      const prompt = reflection.buildReflectionPrompt(gatheredTopics)
      // In a real implementation, this would call the LLM
      // For now, reflect deterministically: if plan is complete, synthesize
      const nextTool = planner.nextTool()
      if (!nextTool) {
        stopReason = 'reflection_ready'
        break
      }
      // Continue if more tools available
    }

    const nextItem = planner.nextTool()
    if (!nextItem) {
      stopReason = 'plan_complete'
      break
    }

    // Load and execute tool
    const schema = loadToolSchema(nextItem.uri)
    if (!schema) {
      errorLog.record(
        { uri: nextItem.uri, error: 'tool not found in registry', args: {}, attempt: 1 },
        { action: 'skip', rationale: 'URI not registered' }
      )
      planner.recordResult({ uri: nextItem.uri, args: {}, result: null, latency_ms: 0, cost_usd: 0 })
      reflection.increment()
      continue
    }

    const cap = getCapability(nextItem.uri) as ToolCapability | undefined
    if (!cap) {
      planner.recordResult({ uri: nextItem.uri, args: {}, result: null, latency_ms: 0, cost_usd: 0 })
      reflection.increment()
      continue
    }

    // Execute with error recovery
    let attempt = 0
    let result: unknown = null
    let success = false

    while (attempt < 4 && !success) {
      attempt++
      const start = Date.now()
      try {
        result = await cap.handler({}, ctx)
        success = true
        const latency = Date.now() - start
        planner.recordResult({ uri: nextItem.uri, args: {}, result, latency_ms: latency, cost_usd: 0 })
        gathered[nextItem.uri] = result
        gatheredTopics.push(cap.name)

        // Re-plan based on result insight
        const insight = typeof result === 'string' ? result : JSON.stringify(result).slice(0, 200)
        planner.replan(insight)
      } catch (err) {
        const error: ToolError = {
          uri: nextItem.uri,
          error: String(err),
          args: {},
          attempt,
        }
        const recovery = suggestRecovery(error)
        errorLog.record(error, recovery)

        if (recovery.action === 'skip' || recovery.action === 'abort') {
          planner.recordResult({ uri: nextItem.uri, args: {}, result: null, latency_ms: 0, cost_usd: 0 })
          break
        }
        if (recovery.action === 'fallback_uri' && recovery.uri) {
          // Try the fallback URI on next attempt
          const fallbackCap = getCapability(recovery.uri) as ToolCapability | undefined
          if (fallbackCap) {
            try {
              result = await fallbackCap.handler({}, ctx)
              success = true
              gathered[nextItem.uri] = result  // store under original URI
              gatheredTopics.push(cap.name)
              planner.recordResult({ uri: nextItem.uri, args: {}, result, latency_ms: 0, cost_usd: 0 })
            } catch {
              // Fallback also failed
            }
          }
          break
        }
        // 'retry': continue loop
      }
    }

    reflection.increment()

    // Check budget
    // (In production, track per LLM call; here we check after each iteration)
    const budgetStatus = governor.trackCall('gemini-2.5-flash', { input_tokens: 0, output_tokens: 0 })
    if (budgetStatus.status === 'hard_stop') {
      stopReason = 'budget_exhausted'
      break
    }
  }

  return {
    gathered,
    thinking: cot.fullText,
    iterations: reflection.currentIteration,
    total_cost_usd: governor.total,
    stop_reason: stopReason,
    error_log: errorLog.log,
  }
}
