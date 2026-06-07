/**
 * Agentic Loop Adapter — Adaptive Planner
 * =========================================
 * Mid-loop re-planning based on intermediate results.
 * Examines what's been gathered and decides what to fetch next.
 */

import type { CapabilityUri } from '@/lib/retrieval/registry/types'

export interface LoopState {
  iteration: number
  tools_called: CapabilityUri[]
  results_gathered: Map<CapabilityUri, unknown>
  intent: string
  original_query: string
}

export interface PlanAction {
  action: 'continue' | 'synthesize' | 'fetch' | 'refine'
  next_tools?: CapabilityUri[]
  reasoning?: string
}

/**
 * Analyze current loop state and decide next action.
 * This is the mid-loop re-planning logic.
 */
export function planNextAction(state: LoopState, max_iterations: number): PlanAction {
  const { iteration, tools_called, results_gathered } = state

  // If we're at the max, synthesize what we have
  if (iteration >= max_iterations) {
    return {
      action: 'synthesize',
      reasoning: `Max iterations (${max_iterations}) reached — synthesizing with gathered data`,
    }
  }

  // If no results yet, continue gathering
  if (results_gathered.size === 0) {
    return {
      action: 'continue',
      reasoning: 'No results gathered yet — continue fetching',
    }
  }

  // If we have sufficient coverage for the intent, synthesize
  const coverage = assessCoverage(state)
  if (coverage.is_sufficient) {
    return {
      action: 'synthesize',
      reasoning: `Coverage sufficient (${coverage.score.toFixed(2)}) — ready to synthesize`,
    }
  }

  // If there are gaps, fetch targeted data
  if (coverage.missing_aspects.length > 0) {
    return {
      action: 'fetch',
      next_tools: coverage.suggested_tools,
      reasoning: `Coverage gaps: ${coverage.missing_aspects.join(', ')}`,
    }
  }

  return {
    action: 'continue',
    reasoning: 'Continuing data gathering',
  }
}

interface CoverageAssessment {
  is_sufficient: boolean
  score: number
  missing_aspects: string[]
  suggested_tools: CapabilityUri[]
}

/**
 * Assess coverage completeness based on gathered results.
 */
function assessCoverage(state: LoopState): CoverageAssessment {
  const results = state.results_gathered
  const gathered_count = results.size

  // Simple heuristic: if we have 3+ distinct tool results, check for key domains
  const has_ontology = Array.from(results.keys()).some(
    (uri) => uri.includes('resolve_entity') || uri.includes('list_entities')
  )
  const has_classical_text = Array.from(results.keys()).some(
    (uri) => uri.includes('classical_text') || uri.includes('sutravali')
  )

  // Coverage score: 0-1 based on domain coverage + result count
  const domain_score = (has_ontology ? 0.3 : 0) + (has_classical_text ? 0.4 : 0)
  const volume_score = Math.min(gathered_count / 5, 0.3)
  const score = domain_score + volume_score

  return {
    is_sufficient: score >= 0.6,
    score,
    missing_aspects: [
      ...(!has_ontology ? ['entity_resolution'] : []),
      ...(!has_classical_text ? ['classical_text_grounding'] : []),
    ],
    suggested_tools: [
      ...(!has_ontology ? ['marsys://tool/L0/resolve_entity' as CapabilityUri] : []),
      ...(!has_classical_text ? ['marsys://tool/L0/list_entities' as CapabilityUri] : []),
    ],
  }
}

/**
 * Determine if the loop should stop early.
 * Returns true if we have enough data to answer confidently.
 */
export function shouldStopEarly(state: LoopState): boolean {
  if (state.results_gathered.size >= 8) return true  // Rich enough
  if (state.results_gathered.size === 0 && state.iteration >= 3) return true  // Nothing working
  return false
}
