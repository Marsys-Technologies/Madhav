/**
 * selector — picks the QueryPipeline implementation for a consult request.
 *
 * Unit 3.gateway_pipeline_isolation. Mirrors the inline decision inside
 * consult/route.ts: per-provider `R11E_<PROVIDER>_LOOP` flag decides
 * agentic-vs-single_pass at request time.
 *
 * The pipeline-selector flag was retired by 3.legacy_delete 2026-05-28; the
 * vestigial selector-enabled shim helper it left behind was deleted by
 * 4.refactor_pipeline_shim. The selector + per-kind QueryPipeline modules
 * remain as infrastructure now that pipeline.run() bodies live in
 * `shared/run_adapter_dispatch.ts`.
 */

import { configService } from '@/lib/config/index'
import { agenticPipeline } from './agentic'
import { singlePassPipeline } from './single_pass'
import type { QueryPipeline, PipelineKind } from './types'

/** Maps provider id → the R11.E per-provider loop flag. Mirrors the inline
 *  ADAPTER_TO_LOOP_FLAG in `shared/run_adapter_dispatch.ts`. */
export const ADAPTER_TO_LOOP_FLAG: Record<string, string> = {
  anthropic: 'R11E_ANTHROPIC_LOOP',
  google: 'R11E_GEMINI_LOOP',
  openai: 'R11E_OPENAI_LOOP',
  deepseek: 'R11E_DEEPSEEK_LOOP',
  nvidia: 'R11E_NVIDIA_LOOP',
} as const

/**
 * Pure selector — no flag reads, deterministic in its inputs. Tests use this.
 */
export function selectPipelineKind(opts: {
  /** Provider id (anthropic/google/openai/deepseek/nvidia). */
  adapterId: string
  /** Per-provider agentic-loop flag effective value. */
  agenticLoopEnabled: boolean
}): PipelineKind {
  // Even with the flag on, only providers in the loop-flag map use the agentic
  // path — that mirrors the dispatch body where unknown adapters fall to false.
  if (!opts.agenticLoopEnabled) return 'single_pass'
  if (!(opts.adapterId in ADAPTER_TO_LOOP_FLAG)) return 'single_pass'
  return 'agentic'
}

/** Resolve the QueryPipeline instance for a kind. */
export function getPipeline(kind: PipelineKind): QueryPipeline {
  return kind === 'agentic' ? agenticPipeline : singlePassPipeline
}

/**
 * Selector entry — reads the per-provider flag via configService just like
 * the inlined dispatch body does today. Returns both the resolved kind and
 * the pipeline instance.
 */
export function selectPipelineForRequest(adapterId: string): {
  kind: PipelineKind
  pipeline: QueryPipeline
} {
  const flagKey = ADAPTER_TO_LOOP_FLAG[adapterId]
  const agenticLoopEnabled = flagKey
    ? Boolean(
        configService.getFlag(
          flagKey as Parameters<typeof configService.getFlag>[0],
        ),
      )
    : false

  const kind = selectPipelineKind({ adapterId, agenticLoopEnabled })
  return { kind, pipeline: getPipeline(kind) }
}
