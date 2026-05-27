/**
 * pipelines — unit 3.gateway_pipeline_isolation public surface.
 *
 * Two pipelines (single_pass + agentic) behind one QueryPipeline interface.
 * Shared stages live in `./shared/`. The route is a thin selector
 * (gated by MARSYS_FLAG_PIPELINE_SELECTOR until G5b lands).
 */

export { singlePassPipeline } from './single_pass'
export { agenticPipeline } from './agentic'
export {
  selectPipelineKind,
  selectPipelineForRequest,
  getPipeline,
  isPipelineSelectorEnabled,
  ADAPTER_TO_LOOP_FLAG,
} from './selector'
export type {
  QueryPipeline,
  PipelineKind,
  PipelineInput,
  PipelineResult,
} from './types'
export * as shared from './shared'
