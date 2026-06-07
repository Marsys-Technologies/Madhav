/**
 * Agentic Loop Adapter — Reflection
 * ===================================
 * Periodic "ready to synthesize?" prompts.
 * Runs after key iterations to check loop health.
 */

import type { LoopState } from './adaptive_planner'

export interface ReflectionResult {
  ready_to_synthesize: boolean
  confidence: number
  observations: string[]
  suggested_action: 'synthesize' | 'continue' | 'refine_query'
}

/**
 * Determine when to run a reflection pass.
 * Defaults: every 3 iterations, or when coverage looks sufficient.
 */
export function shouldReflect(state: LoopState, reflection_interval = 3): boolean {
  return state.iteration > 0 && state.iteration % reflection_interval === 0
}

/**
 * Run a reflection pass on the current loop state.
 * Returns an assessment of readiness and observations.
 */
export function reflect(state: LoopState): ReflectionResult {
  const observations: string[] = []
  let confidence = 0

  // Check: do we have diverse data?
  const unique_tools = new Set(state.tools_called).size
  if (unique_tools >= 3) {
    observations.push(`${unique_tools} distinct tools invoked — good coverage breadth`)
    confidence += 0.3
  } else if (unique_tools === 0) {
    observations.push('No tools invoked yet — low coverage')
  }

  // Check: are results non-empty?
  const non_empty_results = Array.from(state.results_gathered.values()).filter(
    (v) => v !== null && v !== undefined && (typeof v !== 'object' || Object.keys(v as object).length > 0)
  ).length

  if (non_empty_results >= 2) {
    observations.push(`${non_empty_results} non-empty results gathered`)
    confidence += 0.3
  }

  // Check: does any result match ontology grounding?
  const has_entity_resolution = state.tools_called.some((uri) =>
    uri.includes('resolve_entity')
  )
  if (has_entity_resolution) {
    observations.push('Ontology grounding confirmed via resolve_entity')
    confidence += 0.2
  }

  // Check: is the iteration count reasonable?
  if (state.iteration >= 5) {
    observations.push(`${state.iteration} iterations — consider synthesizing soon`)
    confidence += 0.1
  }

  const ready_to_synthesize = confidence >= 0.5

  return {
    ready_to_synthesize,
    confidence,
    observations,
    suggested_action:
      confidence >= 0.7 ? 'synthesize' : confidence >= 0.4 ? 'continue' : 'refine_query',
  }
}

/**
 * Format a reflection result as a system message for the LLM.
 */
export function formatReflectionForLLM(result: ReflectionResult): string {
  return [
    `[Reflection at current iteration]`,
    `Confidence: ${(result.confidence * 100).toFixed(0)}%`,
    `Observations: ${result.observations.join('; ')}`,
    `Suggested action: ${result.suggested_action}`,
    result.ready_to_synthesize
      ? 'You have sufficient data. Consider synthesizing your response now.'
      : 'Continue gathering data before synthesizing.',
  ].join('\n')
}
