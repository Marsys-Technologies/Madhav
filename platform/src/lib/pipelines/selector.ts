/**
 * selector — picks the QueryPipeline implementation for a consult request.
 *
 * R11E loop flags permanently true (WS-0 2026-06-04): all 5 providers use
 * the agentic path unconditionally.
 */

import { agenticPipeline } from './agentic'
import { singlePassPipeline } from './single_pass'
import type { QueryPipeline, PipelineKind } from './types'

const AGENTIC_PROVIDERS = new Set(['anthropic', 'google', 'openai', 'deepseek', 'nvidia'])

/**
 * Pure selector — deterministic in its inputs. Tests use this.
 */
export function selectPipelineKind(opts: {
  adapterId: string
  agenticLoopEnabled: boolean
}): PipelineKind {
  if (!opts.agenticLoopEnabled) return 'single_pass'
  if (!AGENTIC_PROVIDERS.has(opts.adapterId)) return 'single_pass'
  return 'agentic'
}

/** Resolve the QueryPipeline instance for a kind. */
export function getPipeline(kind: PipelineKind): QueryPipeline {
  return kind === 'agentic' ? agenticPipeline : singlePassPipeline
}

export function selectPipelineForRequest(adapterId: string): {
  kind: PipelineKind
  pipeline: QueryPipeline
} {
  const agenticLoopEnabled = AGENTIC_PROVIDERS.has(adapterId)
  const kind = selectPipelineKind({ adapterId, agenticLoopEnabled })
  return { kind, pipeline: getPipeline(kind) }
}
