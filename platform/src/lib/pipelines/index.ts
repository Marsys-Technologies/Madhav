/**
 * pipelines — unit 3.gateway_pipeline_isolation public surface.
 *
 * Two pipelines (single_pass + agentic) behind one QueryPipeline interface.
 * Shared stages live in `./shared/`. The consult route is a thin selector
 * (auth + chart resolution + planner-context + dispatch).
 */

export { singlePassPipeline } from './single_pass'
export { agenticPipeline } from './agentic'
export {
  selectPipelineKind,
  selectPipelineForRequest,
  getPipeline,
} from './selector'
export type {
  QueryPipeline,
  PipelineKind,
  PipelineInput,
  PipelineResult,
} from './types'
export * as shared from './shared'
