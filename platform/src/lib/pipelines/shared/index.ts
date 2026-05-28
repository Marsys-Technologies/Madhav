/**
 * Shared pipeline stages — unit 3.gateway_pipeline_isolation.
 *
 * Stages the two pipelines (single_pass + agentic) hold in common. Extracted
 * from consult/route.ts to keep behaviour byte-identical (AC.3 golden-transcript).
 * The route still hosts the streaming + persistence runtime; this seam grows
 * as G5b lands.
 */

export { resolveAuthAndChart } from './auth_and_chart'
export {
  injectB11Floor,
  L2_5_TOOLS,
  type FloorInjectionResult,
} from './b11_floor_inject'
export type {
  AuthContext,
  ChartContext,
  ResolvedRequestContext,
  ResolveContextInput,
  ResolveContextResult,
} from './types'
export {
  runOnFinishWriteThrough,
} from './onfinish_writethrough'
export type {
  OnFinishWriteThroughOpts,
  OnFinishWriteThroughDeps,
  CitationGateOutcome,
  WriteThroughWriter,
  PersistenceClient,
  PricingClient,
  ContextAssemblyLogWriter,
  MsrSnippetResolver,
  PendingStreamWriterLike,
  TitleClient,
  PredictionLedgerAppender,
  SynthUsage,
} from './onfinish_writethrough'
export {
  runAdapterDispatch,
  type RunAdapterDispatchCtx,
} from './run_adapter_dispatch'
