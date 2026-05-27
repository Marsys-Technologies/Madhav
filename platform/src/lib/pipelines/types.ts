/**
 * QueryPipeline — the public interface for the two consult pipelines.
 *
 * Unit 3.gateway_pipeline_isolation. Both pipelines (single_pass + agentic)
 * implement the same surface so route.ts can pick by a feature flag without
 * duplicating wiring.
 *
 * The interface is intentionally minimal at this commit. The route still
 * holds the runtime (Next.js streaming response, SSE writer, persistence
 * batching, tracing emit) — those move into pipelines/{shared,*}/ as later
 * waves land. What ships now is the structural shell so:
 *   • G5b lands the cutover atomically (one place to flip)
 *   • each pipeline owns its types + its tests
 *   • the route is a thin selector (no inline pipeline bodies)
 */

import type { ConsumeStyle } from '@/lib/claude/system-prompts'
import type { ModelStack } from '@/lib/models/registry'

/** Which pipeline strategy the route picks. */
export type PipelineKind = 'single_pass' | 'agentic'

/** What the route hands to the pipeline. */
export interface PipelineInput {
  /** UUID. Already validated by the shared resolver. */
  conversationId: string
  /** UUID. Already validated by the shared resolver. */
  chartId: string
  /** Authenticated user id (Firebase). */
  userUid: string
  /** Authenticated principal role. */
  isSuperAdmin: boolean
  /** Conversation history coming from the client. */
  messages: ReadonlyArray<{ role: string; parts?: ReadonlyArray<{ type: string; text?: string }> }>
  /** Selected stack (anthropic/google/openai/deepseek/nvidia). */
  stack: ModelStack
  /** Style (acharya | brief | client). */
  style: ConsumeStyle
  /** Effective synthesis model id resolved by the route. */
  modelId: string
  /** First-turn flag — drives title generation + initial insert. */
  isFirstTurn: boolean
  /** LEL informed/blind mode toggle. */
  lelContextEnabled: boolean
}

/**
 * What the pipeline returns. At this commit it is just a marker — the route
 * still owns the streaming Response object. When the streaming move lands
 * (G5b), this grows into a full Response | AsyncIterable<...>.
 */
export interface PipelineResult {
  kind: PipelineKind
  /** Echo of which strategy ran (for diagnostics + golden-transcript labelling). */
  selected: PipelineKind
}

/** The interface every pipeline implements. */
export interface QueryPipeline {
  readonly kind: PipelineKind
  /**
   * Diagnostic-grade plan label. Real `run()` is added when the streaming
   * extraction lands; until then route.ts continues to host the runtime.
   */
  describe(): { kind: PipelineKind; description: string }
}
